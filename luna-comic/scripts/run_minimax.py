#!/usr/bin/env python3
"""Generate the MV shots on your own GPU with the local MiniMax H3 weights.

Reads the compiled prompts in out/shot_prompts.json (produced by build_shots.py),
builds one API-format graph per shot, queues it on the local ComfyUI, waits for
the result, and downloads the clip to out/clips/<SHOT_ID>.mp4.

TWO DIFFERENT "MiniMax H3" NODE SETS EXIST — this matters:

  * local  (default) — comfy_extras/nodes_minimax_h3.py, category model/*/minimax.
    Runs the open weights in models/ on your GPU. No account, no API key, no cost.
    ComfyUI's own HTTP API on 127.0.0.1:8188 has no authentication at all.
  * cloud  (--backend cloud) — comfy_api_nodes/nodes_minimax.py, category
    partner/video/MiniMax. Sends the job to comfy.org's proxy and bills credits.
    Only that path needs COMFY_API_KEY, from platform.comfy.org.

The local graph mirrors the workflow you already ran successfully (recovered from
the metadata embedded in output/video/MiniMax_H3_00002_.mp4), with one deliberate
change: it uses MiniMaxH3ReferenceToVideo rather than MiniMaxH3ImageToVideo. Image
-to-video makes the reference the literal first frame — every shot would open on
the character sheet. Reference-to-video conditions on LUNA's identity instead and
lets the shot start wherever the prompt says.

Consistency: every shot is conditioned on the same reference image, cited in the
prompt as <Picture 1> — the tag the H3 text encoder inserts for it. Generate the
anchor shot first, approve it, then pass its best frame back in with --ref;
regenerating each shot from the original character sheet independently is what
makes the character drift.

Usage:
    python scripts/run_minimax.py --list
    python scripts/run_minimax.py --shots S03 --megapixels 0.3     # cheapest real test
    python scripts/run_minimax.py --shots S12                      # anchor shot
    python scripts/run_minimax.py --pending                        # the rest
    python scripts/run_minimax.py --shots S04 --force              # re-roll one shot
    python scripts/run_minimax.py --pending --dry-run              # graphs only

Length: H3 counts frames at 24 fps on a 17k+5 grid (124 frames ~ 5.17s). Each
shot is generated at the smallest grid length that covers its slot, then trimmed
back to the bar line by assemble_mv.py — so no shot is ever cut short.
"""
import argparse
import json
import math
import mimetypes
import os
import pathlib
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "out" / "shot_prompts.json"
CLIPS = ROOT / "out" / "clips"
STATE = ROOT / "out" / "run_state.json"

DEFAULT_URL = os.environ.get("COMFYUI_API_URL", "http://127.0.0.1:8188")

# Local weights, as installed under ComfyUI/models/.
UNET = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
CLIP = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
VIDEO_VAE = "minimax_h3_video_vae_fp16.safetensors"
AUDIO_VAE = "minimax_h3_audio_vae_fp32.safetensors"
TURBO_LORA = "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"

FPS = 24
LENGTH_BASE, LENGTH_STEP = 5, 17     # frame count grid the model is trained on

# Cloud backend only (--backend cloud).
CLOUD_MIN_DURATION, CLOUD_MAX_DURATION = 4, 15
CLOUD_USD_PER_SECOND = {"768P": 0.1287, "2K": 0.1859}

POLL_SECONDS = 10
TIMEOUT_SECONDS = 60 * 60


# ---------------------------------------------------------------- HTTP helpers

def _request(url, data=None, headers=None, method=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def api_get(base, path, timeout=60):
    return json.loads(_request(f"{base}{path}", timeout=timeout))


def api_post_json(base, path, payload, timeout=120):
    body = json.dumps(payload).encode("utf-8")
    return json.loads(_request(f"{base}{path}", data=body,
                               headers={"Content-Type": "application/json"},
                               method="POST", timeout=timeout))


def upload_image(base, path: pathlib.Path, subfolder="luna"):
    """POST /api/upload/image -> the name LoadImage expects."""
    boundary = f"----luna{uuid.uuid4().hex}"
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts = []
    for field, value in (("subfolder", subfolder), ("overwrite", "true"), ("type", "input")):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{value}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
        f"filename=\"{path.name}\"\r\nContent-Type: {ctype}\r\n\r\n".encode()
        + path.read_bytes() + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    resp = json.loads(_request(
        f"{base}/api/upload/image", data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST", timeout=300,
    ))
    name, sub = resp["name"], resp.get("subfolder", "")
    return f"{sub}/{name}" if sub else name


# ------------------------------------------------------------- sizing helpers

def grid_length(seconds):
    """Smallest 17k+5 frame count at 24 fps that covers `seconds`."""
    frames = math.ceil(seconds * FPS)
    if frames <= LENGTH_BASE:
        return LENGTH_BASE
    k = math.ceil((frames - LENGTH_BASE) / LENGTH_STEP)
    return LENGTH_BASE + k * LENGTH_STEP


def dimensions(megapixels, ratio="16:9"):
    """Width/height at the requested pixel budget, both multiples of 32.

    H3 only accepts dimensions on a 32-pixel grid, and rounding each side
    independently distorts the frame — 0.5 MP at 16:9 lands on 928x512, which is
    1.813 rather than 1.778. So search the grid and pay a little pixel budget to
    keep the aspect exact: the same request lands on 1024x576 instead.
    """
    w_ratio, h_ratio = (int(x) for x in ratio.split(":"))
    target = ratio_value = w_ratio / h_ratio
    best, best_score = None, None
    for width in range(320, 2049, 32):
        height = max(32, round(width / ratio_value / 32) * 32)
        ratio_error = abs(width / height - target) / target
        mp_error = abs(width * height / 1_000_000 - megapixels) / megapixels
        score = ratio_error * 30 + mp_error
        if best_score is None or score < best_score:
            best, best_score = (width, height), score
    return best


def cloud_duration(shot):
    return max(CLOUD_MIN_DURATION, min(CLOUD_MAX_DURATION, math.ceil(shot["dur"])))


def shot_prompt(shot):
    prompt = ("LUNA is the character shown in <Picture 1> — keep her hair, outfit, "
              "accessories and proportions exactly as they appear there. " + shot["prompt"])
    if shot.get("negative"):
        # H3 has no negative-prompt input; fold it in as plain language.
        prompt += f". Avoid: {shot['negative']}"
    return prompt


# -------------------------------------------------------------- graph builders

def build_graph_local(shot, ref_name, width, height, seed, steps, turbo,
                      ref_image_size="match", with_audio=True):
    """LoadImage -> MiniMaxH3ReferenceToVideo -> SamplerCustomAdvanced -> SaveVideo.

    Autogrow inputs are flat dotted keys in the API format — see finalize_prefix()
    in comfy_api/latest/_io.py — which is why the reference image is passed as
    "ref_images.ref_image_0" rather than a nested dict. The prefix template names
    slots ref_image_0..ref_image_8, and <Picture 1> in the prompt is slot 0.
    """
    model_source = "lora" if turbo else "unet"
    graph = {
        "load_ref": {"class_type": "LoadImage", "inputs": {"image": ref_name}},
        "unet": {"class_type": "UNETLoader",
                 "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "clip": {"class_type": "CLIPLoader",
                 "inputs": {"clip_name": CLIP, "type": "minimax", "device": "default"}},
        "vae_video": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_VAE}},
        "cond": {
            "class_type": "MiniMaxH3ReferenceToVideo",
            "inputs": {
                "clip": ["clip", 0],
                "vae": ["vae_video", 0],
                "prompt": shot_prompt(shot),
                "width": width,
                "height": height,
                "length": grid_length(shot["dur"]),
                "ref_image_size": ref_image_size,
                "ref_images.ref_image_0": ["load_ref", 0],
            },
        },
        "noise": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "guider": {"class_type": "BasicGuider",
                   "inputs": {"model": [model_source, 0], "conditioning": ["cond", 0]}},
        "sampler": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "sigmas": {"class_type": "BasicScheduler",
                   "inputs": {"scheduler": "simple", "steps": steps, "denoise": 1.0,
                              "model": [model_source, 0]}},
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
                 "inputs": {"video": ["video", 0], "filename_prefix": f"luna/{shot['id']}",
                            "format": "mp4", "format.codec": "h264"}},
    }
    if turbo:
        graph["lora"] = {"class_type": "LoraLoaderModelOnly",
                         "inputs": {"lora_name": TURBO_LORA, "strength_model": 1.0,
                                    "model": ["unet", 0]}}
    if with_audio:
        # H3 generates picture and sound together. The song is muxed over the top
        # later, so this track is discarded — but decoding it keeps the graph
        # identical to the one already proven on this machine.
        graph["vae_audio"] = {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE}}
        graph["cond"]["inputs"]["audio_vae"] = ["vae_audio", 0]
        graph["decode_audio"] = {"class_type": "VAEDecodeAudio",
                                 "inputs": {"samples": ["sample", 0], "vae": ["vae_audio", 0]}}
        graph["video"]["inputs"]["audio"] = ["decode_audio", 0]
    return graph


def build_graph_cloud(shot, ref_name, resolution, seed):
    """The comfy.org API-node path — billed, needs COMFY_API_KEY."""
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": ref_name}},
        "2": {
            "class_type": "MinimaxHailuo03ReferenceNode",
            "inputs": {
                "model": "MiniMax H3",
                "model.prompt": shot_prompt(shot),
                "model.resolution": resolution,
                "model.ratio": shot.get("aspect_ratio", "16:9"),
                "model.duration": cloud_duration(shot),
                "model.reference_images.image_1": ["1", 0],
                "seed": seed,
                "watermark": False,
            },
        },
        "3": {"class_type": "SaveVideo",
              "inputs": {"video": ["2", 0], "filename_prefix": f"luna/{shot['id']}",
                         "format": "mp4", "format.codec": "h264"}},
    }


# ----------------------------------------------------------------- queue + wait

def submit(base, graph, api_key, client_id):
    payload = {"prompt": graph, "client_id": client_id}
    if api_key:
        payload["extra_data"] = {"api_key_comfy_org": api_key}
    try:
        resp = api_post_json(base, "/api/prompt", payload)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(f"ComfyUI rejected the graph ({e.code}):\n{detail}")
    return resp["prompt_id"]


def wait_for(base, prompt_id, label):
    started = time.time()
    while True:
        elapsed = int(time.time() - started)
        if elapsed > TIMEOUT_SECONDS:
            raise TimeoutError(f"{label}: no result after {elapsed}s")
        history = api_get(base, f"/api/history/{prompt_id}")
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status", {})
            if status.get("completed") or status.get("status_str") == "success":
                return entry, elapsed
            if status.get("status_str") == "error":
                messages = status.get("messages", [])
                raise RuntimeError(f"{label} failed: {json.dumps(messages, ensure_ascii=False)[:1500]}")
        sys.stdout.write(f"\r  {label}: generating… {elapsed // 60}m{elapsed % 60:02d}s")
        sys.stdout.flush()
        time.sleep(POLL_SECONDS)


def download_output(base, entry, dest: pathlib.Path):
    for node_output in entry.get("outputs", {}).values():
        for item in node_output.get("images", []):   # SaveVideo reports via PreviewVideo -> "images"
            q = urllib.parse.urlencode({
                "filename": item["filename"],
                "subfolder": item.get("subfolder", ""),
                "type": item.get("type", "output"),
            })
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(_request(f"{base}/api/view?{q}", timeout=600))
            return dest
    raise RuntimeError("job finished but produced no video output")


# ----------------------------------------------------------------------- state

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"shots": {}}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mark_storyboard(done_ids):
    """Mirror completion back into shots.json's status field."""
    path = ROOT / "storyboard" / "shots.json"
    book = json.loads(path.read_text(encoding="utf-8"))
    touched = False
    for shot in book["shots"]:
        if shot["id"] in done_ids and shot.get("status") != "generated":
            shot["status"] = "generated"
            touched = True
    if touched:
        path.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sel = ap.add_mutually_exclusive_group()
    sel.add_argument("--shots", help="comma-separated shot ids, e.g. S01,S04")
    sel.add_argument("--pending", action="store_true", help="every shot not yet generated (default)")
    sel.add_argument("--all", action="store_true", help="every shot, generated or not")
    sel.add_argument("--list", action="store_true", help="print the shot table and exit")
    ap.add_argument("--backend", choices=["local", "cloud"], default="local",
                    help="local GPU (default, free) or comfy.org API nodes (billed)")
    ap.add_argument("--ref", help="reference image (default: the project character sheet)")
    ap.add_argument("--megapixels", type=float, default=0.5,
                    help="local: pixel budget per frame (default 0.5 ≈ 960x544 at 16:9)")
    ap.add_argument("--steps", type=int, help="local: sampler steps (default 8 turbo / 20 plain)")
    ap.add_argument("--no-turbo", action="store_true",
                    help="local: skip the 8-step turbo LoRA and sample at full steps")
    ap.add_argument("--ref-size", choices=["match", "max"], default="match",
                    help="local: 'max' keeps 2048px reference detail — better identity, much slower")
    ap.add_argument("--no-audio", action="store_true",
                    help="local: skip the generated soundtrack (the song is muxed in later anyway)")
    ap.add_argument("--resolution", choices=["768P", "2K"], default="768P", help="cloud only")
    ap.add_argument("--seed", type=int, help="fixed seed (default: derived from the shot id)")
    ap.add_argument("--force", action="store_true", help="regenerate shots already marked done")
    ap.add_argument("--limit", type=int, help="stop after N shots")
    ap.add_argument("--dry-run", action="store_true", help="print graphs, submit nothing")
    ap.add_argument("--yes", action="store_true", help="skip the cost confirmation (cloud only)")
    ap.add_argument("--no-mark", action="store_true", help="do not write status back into shots.json")
    ap.add_argument("--url", default=DEFAULT_URL)
    args = ap.parse_args()

    base = args.url.rstrip("/")
    local = args.backend == "local"
    turbo = local and not args.no_turbo
    steps = args.steps if args.steps is not None else (8 if turbo else 20)
    width, height = dimensions(args.megapixels)

    book = json.loads(PROMPTS.read_text(encoding="utf-8"))
    shots = book["shots"]
    state = load_state()

    if args.list:
        for s in shots:
            st = state["shots"].get(s["id"], {})
            flag = "done" if st.get("status") == "done" and st.get("hash") == s["hash"] else \
                   "stale" if st.get("status") == "done" else "pending"
            frames = grid_length(s["dur"])
            print(f"{s['id']:5s} {s['start']:7.2f}-{s['end']:7.2f} slot {s['dur']:5.2f}s  "
                  f"{frames:3d}f = {frames / FPS:5.2f}s  {flag:8s} {s['section']}")
        return

    if args.shots:
        wanted = [w.strip().upper() for w in args.shots.split(",") if w.strip()]
        by_id = {s["id"]: s for s in shots}
        missing = [w for w in wanted if w not in by_id]
        if missing:
            sys.exit(f"unknown shot ids: {', '.join(missing)}. Known: {', '.join(by_id)}")
        batch = [by_id[w] for w in wanted]
    elif args.all:
        batch = list(shots)
    else:
        batch = [s for s in shots
                 if not (state["shots"].get(s["id"], {}).get("status") == "done"
                         and state["shots"][s["id"]].get("hash") == s["hash"])]

    if not args.force:
        skipped = [s["id"] for s in batch
                   if state["shots"].get(s["id"], {}).get("status") == "done"
                   and state["shots"][s["id"]].get("hash") == s["hash"]]
        if skipped:
            print(f"already generated, skipping: {', '.join(skipped)}  (--force to re-roll)")
            batch = [s for s in batch if s["id"] not in skipped]
    if args.limit:
        batch = batch[:args.limit]
    if not batch:
        print("nothing to generate.")
        return

    if local:
        frames = sum(grid_length(s["dur"]) for s in batch)
        print(f"local · {len(batch)} shots · {width}x{height} · {frames} frames "
              f"({frames / FPS:.1f}s of video) · {steps} steps"
              f"{' + turbo LoRA' if turbo else ''} · no API key, no cost")
    else:
        seconds = sum(cloud_duration(s) for s in batch)
        cost = seconds * CLOUD_USD_PER_SECOND[args.resolution]
        print(f"cloud · {len(batch)} shots · {seconds}s at {args.resolution} · ≈ US${cost:.2f}")
    print(f"shots: {', '.join(s['id'] for s in batch)}")

    ref_path = pathlib.Path(args.ref) if args.ref else ROOT / json.loads(
        (ROOT / "project.json").read_text(encoding="utf-8"))["character"]["reference_sheet"]
    if not ref_path.exists():
        sys.exit(f"reference image not found: {ref_path}")
    print(f"reference: {ref_path}")

    api_key = ""
    if not local:
        api_key = os.environ.get("COMFY_API_KEY", "").strip()
        if not api_key and not args.dry_run:
            sys.exit("--backend cloud needs COMFY_API_KEY from platform.comfy.org.\n"
                     "For local generation drop --backend cloud: no key is needed.")

    def graph_for(shot, ref_name, seed):
        if local:
            return build_graph_local(shot, ref_name, width, height, seed, steps, turbo,
                                     args.ref_size, not args.no_audio)
        return build_graph_cloud(shot, ref_name, args.resolution, seed)

    if args.dry_run:
        for s in batch:
            seed = args.seed if args.seed is not None else random.Random(s["id"]).randrange(4294967295)
            print(f"\n--- {s['id']} ---")
            print(json.dumps(graph_for(s, "luna/" + ref_path.name, seed), ensure_ascii=False, indent=2))
        print("\ndry run — nothing submitted.")
        return

    if not local and not args.yes:
        seconds = sum(cloud_duration(s) for s in batch)
        cost = seconds * CLOUD_USD_PER_SECOND[args.resolution]
        if input(f"Spend ≈ US${cost:.2f} of comfy.org credits? [y/N] ").strip().lower() not in ("y", "yes"):
            print("aborted.")
            return

    ref_name = upload_image(base, ref_path)
    print(f"uploaded reference as {ref_name}\n")

    client_id = str(uuid.uuid4())
    CLIPS.mkdir(parents=True, exist_ok=True)
    done, failed = [], []

    for i, shot in enumerate(batch, 1):
        seed = args.seed if args.seed is not None else random.Random(shot["id"]).randrange(4294967295)
        label = f"[{i}/{len(batch)}] {shot['id']}"
        if local:
            frames = grid_length(shot["dur"])
            print(f"{label}  slot {shot['dur']:.2f}s → {frames} frames ({frames / FPS:.2f}s)  seed {seed}")
        else:
            print(f"{label}  slot {shot['dur']:.2f}s → {cloud_duration(shot)}s  seed {seed}")
        try:
            prompt_id = submit(base, graph_for(shot, ref_name, seed), api_key, client_id)
            entry, elapsed = wait_for(base, prompt_id, label)
            dest = download_output(base, entry, CLIPS / f"{shot['id']}.mp4")
        except (RuntimeError, TimeoutError, urllib.error.URLError) as e:
            print(f"\r{label}  FAILED: {e}\n")
            failed.append(shot["id"])
            state["shots"][shot["id"]] = {"status": "failed", "hash": shot["hash"],
                                          "error": str(e)[:500], "ts": int(time.time())}
            save_state(state)
            continue
        print(f"\r{label}  -> {dest.relative_to(ROOT)}  in {elapsed // 60}m{elapsed % 60:02d}s   ")
        done.append(shot["id"])
        record = {"status": "done", "hash": shot["hash"], "prompt_id": prompt_id,
                  "file": str(dest.relative_to(ROOT)), "backend": args.backend,
                  "slot_seconds": shot["dur"], "seed": seed, "seconds_taken": elapsed,
                  "reference": str(ref_path), "ts": int(time.time())}
        if local:
            record |= {"width": width, "height": height, "frames": grid_length(shot["dur"]),
                       "steps": steps, "turbo": turbo}
        else:
            record |= {"resolution": args.resolution,
                       "cost_usd": round(cloud_duration(shot) * CLOUD_USD_PER_SECOND[args.resolution], 4)}
        state["shots"][shot["id"]] = record
        save_state(state)

    if done and not args.no_mark:
        mark_storyboard(set(done))
    print(f"\ngenerated {len(done)}/{len(batch)}")
    if not local and done:
        print(f"≈ US${sum(state['shots'][i]['cost_usd'] for i in done):.2f} spent")
    if failed:
        print(f"failed: {', '.join(failed)} — re-run with --shots {','.join(failed)} --force")
        sys.exit(1)
    print("next: python scripts/assemble_mv.py")


if __name__ == "__main__":
    main()
