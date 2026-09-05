#!/usr/bin/env python3
"""Platform adapters — render a canonical cut into each platform's exact format.

decisions.md §8: canonical `context.json` -> platform renders. Local execution,
comfy.org cloud and the generic web paste-block all derive from the SAME
resolved prompt string, so a cut carries one context_hash everywhere.

Platforms v1 (decisions.md §8.2):
  local        — ComfyUI MiniMax H3 graph (free open weights on the box)
  comfy_cloud  — comfy.org API-node graph (billed, asks before spending)
  generic_web  — human-paste block for any web video platform (Hailuo-style)

Usage:
    python app/scripts/export.py --project luna-comic --cut S12 [--platform local|comfy_cloud|generic_web]
    python app/scripts/export.py --list
    python app/scripts/export.py --probe                   # print cost model info
"""
import argparse
import json
import math
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
APP = REPO / "app"
sys.path.insert(0, str(APP / "scripts"))
import build as B

FPS = 24
LENGTH_BASE, LENGTH_STEP = 5, 17       # H3 frame grid (17k+5), decisions.md §7
CLOUD_MIN_DURATION, CLOUD_MAX_DURATION = 4, 15
CLOUD_USD_PER_SECOND = {"768P": 0.1287, "2K": 0.1859}


def grid_length(seconds):
    """Smallest H3 frame count at 24 fps covering `seconds`."""
    frames = math.ceil(seconds * FPS)
    if frames <= LENGTH_BASE:
        return LENGTH_BASE
    return LENGTH_BASE + math.ceil((frames - LENGTH_BASE) / LENGTH_STEP) * LENGTH_STEP


def dimensions(megapixels, ratio="16:9"):
    w_ratio, h_ratio = (int(x) for x in ratio.split(":"))
    width = max(32, round(math.sqrt(megapixels * 1_000_000 * w_ratio / h_ratio) / 32) * 32)
    height = max(32, round(width * h_ratio / w_ratio / 32) * 32)
    return width, height


def shot_prompt(compiled_cut):
    """The model-facing text: <Picture 1> citation + negatives folded in.

    H3 has no negative-prompt input; negatives become plain language. This is
    part of the parity contract — local, cloud and generic_web all use it.
    """
    from textwrap import dedent
    prompt = (
        "LUNA is the character shown in <Picture 1> — keep her hair, outfit, "
        "accessories and proportions exactly as they appear there. "
        + compiled_cut["prompt"]
    )
    if compiled_cut.get("negative"):
        prompt += f". Avoid: {compiled_cut['negative']}"
    return prompt


# ---------------------------------------------------------------- local graph

def build_graph_local(cut, ref_name, width, height, seed, steps, turbo=False,
                      with_audio=True):
    """Mirror of the proven MiniMax H3 workflow (reference-to-video, not image)."""
    UNET = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    CLIP = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
    VIDEO_VAE = "minimax_h3_video_vae_fp16.safetensors"
    AUDIO_VAE = "minimax_h3_audio_vae_fp32.safetensors"
    TURBO_LORA = "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"
    graph = {
        "load_ref": {"class_type": "LoadImage", "inputs": {"image": ref_name}},
        "unet": {"class_type": "UNETLoader",
                 "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "clip": {"class_type": "CLIPLoader",
                 "inputs": {"clip_name": CLIP, "type": "minimax", "device": "default"}},
        "vae_video": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_VAE}},
        "cond": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {
            "clip": ["clip", 0], "vae": ["vae_video", 0],
            "prompt": shot_prompt(cut),
            "width": width, "height": height,
            "length": grid_length(cut["dur"]),
            "ref_image_size": "match",
            "ref_images.ref_image_0": ["load_ref", 0],
        }},
        "noise": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "guider": {"class_type": "BasicGuider",
                   "inputs": {"model": [("lora" if turbo else "unet"), 0],
                              "conditioning": ["cond", 0]}},
        "sampler": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "sigmas": {"class_type": "BasicScheduler",
                   "inputs": {"scheduler": "simple", "steps": steps, "denoise": 1.0,
                              "model": [("lora" if turbo else "unet"), 0]}},
        "sample": {"class_type": "SamplerCustomAdvanced",
                   "inputs": {"noise": ["noise", 0], "guider": ["guider", 0],
                              "sampler": ["sampler", 0], "sigmas": ["sigmas", 0],
                              "latent_image": ["cond", 1]}},
        "decode_video": {"class_type": "VAEDecode",
                         "inputs": {"samples": ["sample", 0], "vae": ["vae_video", 0]}},
        "video": {"class_type": "CreateVideo",
                  "inputs": {"images": ["decode_video", 0], "fps": float(FPS),
                             "bit_depth": 8, "color_space": "sRGB"}},
        "save": {"class_type": "SaveVideo",
                 "inputs": {"video": ["video", 0], "filename_prefix": f"luna/{cut['id']}",
                            "format": "mp4", "format.codec": "h264"}},
    }
    if turbo:
        graph["lora"] = {"class_type": "LoraLoaderModelOnly",
                         "inputs": {"lora_name": TURBO_LORA, "strength_model": 1.0,
                                    "model": ["unet", 0]}}
    if with_audio:
        graph["vae_audio"] = {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE}}
        graph["cond"]["inputs"]["audio_vae"] = ["vae_audio", 0]
        graph["decode_audio"] = {"class_type": "VAEDecodeAudio",
                                 "inputs": {"samples": ["sample", 0], "vae": ["vae_audio", 0]}}
        graph["video"]["inputs"]["audio"] = ["decode_audio", 0]
    return graph


def cloud_duration(cut):
    return max(CLOUD_MIN_DURATION, min(CLOUD_MAX_DURATION, math.ceil(cut["dur"])))


def cloud_cost(cut, resolution="768P"):
    return cloud_duration(cut) * CLOUD_USD_PER_SECOND[resolution]


# ------------------------------------------------------------ render dispatch

def render(cut, platform, project_dir: pathlib.Path, ref_name="luna/reference.jpg",
           width=960, height=544, seed=0, steps=8, turbo=True):
    if platform == "local":
        return {
            "platform": "local",
            "graph": build_graph_local(cut, ref_name, width, height, seed, steps, turbo),
            "usage": f"local GPU — no API key, no cost",
            "seed": seed, "steps": steps, "turbo": turbo,
            "frames": grid_length(cut["dur"]),
            "resolution": f"{width}x{height}",
        }
    if platform == "comfy_cloud":
        res = "768P"
        return {
            "platform": "comfy_cloud",
            "graph": {
                "1": {"class_type": "LoadImage", "inputs": {"image": ref_name}},
                "2": {"class_type": "MinimaxHailuo03ReferenceNode", "inputs": {
                    "model": "MiniMax H3",
                    "model.prompt": shot_prompt(cut),
                    "model.resolution": res,
                    "model.ratio": cut["aspect_ratio"],
                    "model.duration": cloud_duration(cut),
                    "model.reference_images.image_1": ["1", 0],
                    "seed": seed,
                    "watermark": False,
                }},
                "3": {"class_type": "SaveVideo",
                      "inputs": {"video": ["2", 0], "filename_prefix": f"luna/{cut['id']}",
                                 "format": "mp4", "format.codec": "h264"}},
            },
            "usage": f"comfy.org — billed ≈ US${cloud_cost(cut, res):.2f} at {res}",
            "cost_usd": round(cloud_cost(cut, res), 4),
            "duration_s": cloud_duration(cut),
            "seed": seed,
        }
    if platform == "generic_web":
        return {
            "platform": "generic_web",
            "text": generic_web_block(cut),
            "usage": "paste-block for any web video platform",
        }
    raise SystemExit(f"unknown platform {platform!r} — known: local, comfy_cloud, generic_web")


def generic_web_block(cut):
    """One self-contained block an operator pastes into a web platform."""
    lines = [
        "# " + cut["id"] + " — paste this exact prompt block",
        "",
        "## Prompt (copy everything in the code block)",
        "```",
        shot_prompt(cut),
        "```",
        "",
        "## Reference image",
        "Upload the project character sheet as the reference image. It is the only image.",
        "",
        "## Settings",
        f"- duration: {cut['dur']:.2f}s in the timeline (generate the grid length above it)",
        f"- aspect ratio: {cut['aspect_ratio']}",
        f"- context_hash: {cut['context_hash']}",
        "",
        "## Edit intent (assembler, not the model)",
        "- trim to bar line: keep the generated clip and cut to "
        f"{cut['start']:.2f}s–{cut['end']:.2f}s",
        "- transition: hard cut (all cuts in this edit are hard cuts on the bar grid)",
    ]
    if cut.get("caption"):
        lines.append(f"- caption card 「{cut['caption']}」 overrides the lyric subtitle here")
    if cut.get("lyric_intent"):
        lines.append(f"- lyric intent: {cut['lyric_intent']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="luna-comic")
    ap.add_argument("--cut", help="cut id (required unless --list)")
    ap.add_argument("--platform", choices=["local", "comfy_cloud", "generic_web"], default="generic_web")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--probe", action="store_true", help="print cost model + frame grid and exit")
    ap.add_argument("--json", action="store_true", help="machine output (default for local/cloud)")
    args = ap.parse_args()

    if args.probe:
        print(f"H3 frame grid: base {LENGTH_BASE}f, step {LENGTH_STEP}f @ {FPS}fps")
        print(f"cloud pricing: {json.dumps(CLOUD_USD_PER_SECOND)}")
        return

    project_dir = REPO / args.project
    compiled = B.compile_shots(project_dir)
    shots = compiled["shots"]

    if args.list:
        for c in shots:
            print(f"{c['id']:5s} {c['start']:7.2f}-{c['end']:7.2f} {c['dur']:5.2f}s  "
                  f"grid {grid_length(c['dur'])}f  hash {c['context_hash'][:12]}  {c['section']}")
        return

    cut = next((c for c in shots if c["id"].upper() == args.cut.upper()), None)
    if not cut:
        sys.exit(f"no cut {args.cut}")
    out = render(cut, args.platform, project_dir)
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json or args.platform != "generic_web"
          else out["text"])


if __name__ == "__main__":
    main()