#!/usr/bin/env python3
"""Compile storyboard/shots.json into per-shot video generation prompts.

The video counterpart of build_prompts.py. That script compiles the superseded
13-panel comic track (3:4 stills); this one compiles the authoritative 26-shot
video storyboard (16:9). They stay separate on purpose — the two tracks carry
different aspect ratios and different negative prompts, and merging them would
make an edit to one silently rewrite the other.

Prompts extend the comic's 4-element structure with what a video model needs and a
still does not: the state of the world being rendered around her, where the shot
opens, the line being sung over it, how long it runs, and how the motion sits on
the beat.

    character / expression / action+camera / world state / opening framing /
    sung line / motion+duration / style

Usage:
    python scripts/build_shots.py                    # write out/shot_prompts.{json,md}
    python scripts/build_shots.py --show S12         # print one shot
    python scripts/build_shots.py --model "ComfyUI MiniMax H3"  # print local batch
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BPM = 106


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


# Opening-composition vocabulary.
#
# Measured across two local batches. Naming a shot size and forbidding the
# alternative ("OPENS already framed as an extreme close-up — do not establish
# with a wider view first") does not work: S01 answered it by compositing BOTH
# readings into one frame, a full-body LUNA standing in front of a giant pair of
# closed eyes, and S03 ignored it entirely. Negations feed the model the very
# thing they forbid, and shot-size jargon is not what it was trained on.
#
# What the model does follow is a description of what is physically in the
# opening frame — the style of MiniMax's own reference prompts ("The scene opens
# exactly on image 1, the mouse resting on the dark surface"). So each framing
# token is translated into content, in the present tense, with no jargon and no
# prohibition.
FRAMINGS = [
    "extreme close-up", "tight close-up", "medium close-up", "close-up",
    "medium full shot", "full body", "hero shot", "hero pose",
    "over-the-shoulder", "back view", "side profile", "wide", "medium",
]
# A move that genuinely changes framing, e.g. "hero shot into crowd wide".
TRANSITIONS = [" into ", " then ", " to "]

FRAME_CONTENT = {
    "extreme close-up": "is filled edge to edge by {subject}, and nothing else is visible",
    "tight close-up": "is filled by her face alone, cropped at the chin and the hairline",
    "close-up": "holds her face and shoulders, her head filling most of the height",
    "medium close-up": "holds her from the shoulders up",
    "medium": "holds her from the waist up",
    "medium full shot": "holds her from the knees up",
    "full body": "shows her whole body head to toe, filling the height of the frame",
    "hero shot": "shows her whole body head to toe, filling the height of the frame",
    "hero pose": "shows her whole body head to toe, filling the height of the frame",
    "wide": "shows her small in a large space, with room visible on every side of her",
    "back view": "shows her from behind, her back to the lens",
    "side profile": "holds her profile from the side",
    "over-the-shoulder": "looks past her shoulder, which sits large in the foreground",
}
DEFAULT_SUBJECT = "her eyes"


def find_framing(text):
    """Longest framing phrase at the earliest position, or None."""
    hits = [(text.index(f), -len(f), f) for f in FRAMINGS if f in text]
    return min(hits)[2] if hits else None


def subject_after(text, framing):
    """The 'on ...' that a close-up names, e.g. 'extreme close-up on the hologram'."""
    tail = text.split(framing, 1)[1]
    match = re.match(r"\s+on\s+([^,;]+)", tail)
    if not match:
        return DEFAULT_SUBJECT
    subject = match.group(1).strip()
    return subject if subject.startswith(("her ", "the ", "his ")) else f"her {subject}"


def content_for(text, framing):
    template = FRAME_CONTENT[framing]
    if "{subject}" not in template:
        return template
    return template.format(subject=subject_after(text, framing))


def framing_instruction(camera):
    """Describe what is in the opening frame, in the model's own idiom."""
    text = camera.lower()

    for token in TRANSITIONS:
        if token not in text:
            continue
        before, after = text.split(token, 1)
        start, end = find_framing(before), find_framing(after)
        # Only a real framing on BOTH sides means the composition changes;
        # "rack focus to background" and "snap to black" do not.
        if start and end and start != end:
            return (f"The opening frame {content_for(before, start)}; by the last beat the "
                    f"camera has moved until the frame {content_for(after, end)}")

    framing = find_framing(text)
    if not framing:
        return ""
    return f"The opening frame {content_for(text, framing)}; the shot stays at that framing"


# The film's science-fiction grammar: one world-state per shot, so the sci-fi
# reads as a single progression rather than per-shot effects. The song is about
# generation ("一張空白的畫面等著第一束光出現", "從第一個 prompt 到最後一個鏡頭"),
# so the world is literally rendered around her as she sings — void to wireframe
# to material to full render, collapsed at the breakdown and rebuilt for the
# final chorus. A shot's `render_stage` in shots.json selects its clause.
RENDER_STAGES = {
    "void": "the world around her is unrendered black, with nothing in it but a single "
            "cold point of light",
    "wireframe": "the environment exists only as glowing wireframe edges on black — "
                 "no surfaces, no textures yet",
    "materializing": "a render pass is sweeping over the wireframe, skinning edges with "
                     "material as it goes; surfaces it has not reached are still flat "
                     "untextured grey",
    "prompt": "glowing prompt glyphs assemble in the air and collapse into finished solid "
              "objects as each one completes",
    "rendered": "the world is fully rendered — complete lighting, true reflections, "
                "volumetric haze in the air",
    "collapsing": "the rendered surfaces peel back to bare wireframe and drift apart into "
                  "latent noise",
    "regenerating": "the whole world snaps back into full render in one expanding pass, "
                    "faster and brighter than it built the first time",
    "collapse_to_point": "the rendered world folds inward and collapses down to one point "
                         "of cold light",
}


def render_clause(shot):
    stage = shot.get("render_stage")
    if not stage:
        return ""
    if stage not in RENDER_STAGES:
        raise SystemExit(f'{shot["id"]}: unknown render_stage {stage!r}. '
                         f'Known: {", ".join(RENDER_STAGES)}')
    return RENDER_STAGES[stage]


def lyric_clause(shot, lyrics_by_id):
    """The sung line, so the imagery can carry it.

    Without this the model never saw a word of the song: the compiled prompt
    listed character, expression, action, camera, duration and style, and the
    shot's `lyrics` were carried into out/shot_prompts.json for humans only.
    """
    lines = [lyrics_by_id[lid]["text"] for lid in shot.get("lyric_lines", [])
             if lid in lyrics_by_id]
    if not lines:
        return ""
    sung = " / ".join(lines)
    return (f"The line sung over this shot is 「{sung}」 — the imagery must carry that "
            f"meaning, never spell it out as on-screen text")


def build_prompt(shot, defaults, character, lyrics_by_id):
    """Assemble the video prompt.

        character / expression / action+camera / world state / opening framing /
        sung line / motion+duration / style
    """
    character_desc = ", ".join(character["locked_keywords"])
    parts = [
        f'{character["name"]}, a K-pop virtual idol: {character_desc}',
        f'expression: {shot["expression"]}',
        f'{shot["action"]}; camera: {shot["camera"]}',
    ]
    for clause in (render_clause(shot), framing_instruction(shot["camera"]),
                   lyric_clause(shot, lyrics_by_id)):
        if clause:
            parts.append(clause)
    parts += [
        f'duration {shot["dur"]:.2f}s, motion synced to {BPM} BPM; '
        f'{shot["sync"].rstrip(". ")}',
        defaults["style_suffix"],
    ]
    return ". ".join(parts)


def shot_hash(prompt, negative, ratio):
    """Same rule as build_prompts.py: only re-render what actually changed."""
    payload = json.dumps([prompt, negative, ratio], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def compile_shots(project, book, lyrics_by_id):
    defaults = book["defaults"]
    character = project["character"]

    compiled = []
    for shot in book["shots"]:
        prompt = build_prompt(shot, defaults, character, lyrics_by_id)
        compiled.append({
            "id": shot["id"],
            "section": shot["section"],
            "bar": shot["bar"],
            "start": shot["start"],
            "end": shot["end"],
            "dur": shot["dur"],
            "model": shot["model"],
            "status": shot.get("status", "pending"),
            "caption": shot.get("caption", ""),
            "lyrics": [
                {"id": lid, "text": lyrics_by_id[lid]["text"]}
                for lid in shot.get("lyric_lines", []) if lid in lyrics_by_id
            ],
            "prompt": prompt,
            "negative": defaults["negative"],
            "aspect_ratio": defaults["aspect_ratio"],
            "character_ref": defaults["character_ref"],
            "render_stage": shot.get("render_stage", ""),
            "hash": shot_hash(prompt, defaults["negative"], defaults["aspect_ratio"]),
        })
    return compiled


def to_markdown(project, compiled):
    """Group by model — the batches you actually paste, one interface at a time."""
    out = [
        f"# {project['project']} — shot prompts",
        "",
        f"{len(compiled)} shots · 16:9 · generated by `scripts/build_shots.py` — do not edit by hand.",
        "",
        "Generate **S12 first** and approve it, then use *its output* as the reference "
        "image for every other shot. Generating each shot from the original character "
        "sheet independently is what makes the character drift.",
        "",
    ]

    for model in sorted({c["model"] for c in compiled}):
        batch = [c for c in compiled if c["model"] == model]
        total = sum(c["dur"] for c in batch)
        out.append(f"## {model} — {len(batch)} shots, {total:.1f}s total")
        out.append("")
        for c in batch:
            out.append(f"### {c['id']} · {c['start']:.2f}–{c['end']:.2f}s "
                       f"({c['dur']:.2f}s) · bar {c['bar']} · {c['section']}")
            out.append("")
            out.append(f"- **hash** `{c['hash']}` · **status** {c['status']} "
                       f"· **ratio** {c['aspect_ratio']}")
            out.append(f"- **reference** `{c['character_ref']}`")
            if c["caption"]:
                out.append(f"- **caption card** 「{c['caption']}」 (overrides lyric subtitle)")
            if c["lyrics"]:
                for l in c["lyrics"]:
                    out.append(f"- **lyric** {l['id']} 「{l['text']}」")
            out.append("")
            out.append("```")
            out.append(c["prompt"])
            out.append("```")
            out.append("")
            out.append("Negative:")
            out.append("")
            out.append("```")
            out.append(c["negative"])
            out.append("```")
            out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", metavar="SHOT_ID", help="print one shot's prompt and exit")
    ap.add_argument("--model", help="print only the batch for one model and exit")
    args = ap.parse_args()

    project = load("project.json")
    book = load("storyboard/shots.json")

    lyrics_path = ROOT / "lyrics" / "lyrics.json"
    lyrics_by_id = {}
    if lyrics_path.exists():
        lyrics_by_id = {l["id"]: l for l in
                        json.loads(lyrics_path.read_text(encoding="utf-8"))["lines"]}
    else:
        print("note: lyrics/lyrics.json not found — run scripts/align_lyrics.py first",
              file=sys.stderr)

    compiled = compile_shots(project, book, lyrics_by_id)

    if args.show:
        match = next((c for c in compiled if c["id"] == args.show), None)
        if not match:
            sys.exit(f"no shot with id {args.show}")
        print(json.dumps(match, ensure_ascii=False, indent=2))
        return

    if args.model:
        batch = [c for c in compiled if c["model"] == args.model]
        if not batch:
            models = sorted({c["model"] for c in compiled})
            sys.exit(f"no shots for model {args.model!r}. Known: {', '.join(models)}")
        print(json.dumps(batch, ensure_ascii=False, indent=2))
        return

    out = ROOT / "out" / "shot_prompts.json"
    out.parent.mkdir(exist_ok=True)

    # Preserve prior hashes so we can report what actually changed.
    previous = {}
    if out.exists():
        previous = {s["id"]: s["hash"]
                    for s in json.loads(out.read_text(encoding="utf-8"))["shots"]}

    out.write_text(
        json.dumps({"project": project["project"], "shots": compiled},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (ROOT / "out" / "shot_prompts.md").write_text(
        to_markdown(project, compiled), encoding="utf-8")

    changed = [c["id"] for c in compiled if previous.get(c["id"]) != c["hash"]]
    print(f"compiled {len(compiled)} shots -> out/shot_prompts.json + shot_prompts.md")
    for model in sorted({c["model"] for c in compiled}):
        batch = [c for c in compiled if c["model"] == model]
        print(f"  {model:16s} {len(batch):2d} shots  {sum(c['dur'] for c in batch):6.1f}s")
    if previous:
        print(f"changed since last build: {', '.join(changed) if changed else '(none)'}")
    else:
        print("first build — all shots are new")


if __name__ == "__main__":
    main()
