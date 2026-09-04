#!/usr/bin/env python3
"""Compile panels.json into per-panel generation prompts.

Edit panels.json, re-run this, and only the panels whose prompt hash changed
need regenerating. Prompts follow the 4-element structure from the LUNA plan doc:
character / expression / action+camera / style.

Usage:
    python scripts/build_prompts.py            # write out/prompts.json, print summary
    python scripts/build_prompts.py --show P08 # print one panel's full prompt
"""
import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def build_prompt(panel, defaults, character):
    """Assemble the 4-element prompt: character, emotion, action/camera, style."""
    character_desc = ", ".join(character["locked_keywords"])
    parts = [
        f'{character["name"]}, a K-pop virtual idol: {character_desc}',
        f'expression: {panel["expression"]}',
        f'{panel["action"]}; camera: {panel["camera"]}',
        defaults["style_suffix"],
    ]
    return ". ".join(parts)


def panel_hash(prompt, negative, ratio):
    payload = json.dumps([prompt, negative, ratio], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", metavar="PANEL_ID", help="print one panel's prompt and exit")
    args = ap.parse_args()

    project = load("project.json")
    book = load("panels/panels.json")
    defaults = book["defaults"]
    character = project["character"]

    compiled = []
    for page in book["pages"]:
        for panel in page["panels"]:
            prompt = build_prompt(panel, defaults, character)
            compiled.append({
                "id": panel["id"],
                "page": page["page"],
                "page_title": page["title"],
                "time": panel["time"],
                "caption": panel.get("caption", ""),
                "status": panel.get("status", "pending"),
                "prompt": prompt,
                "negative": defaults["negative"],
                "aspect_ratio": defaults["aspect_ratio"],
                "character_ref": defaults["character_ref"],
                "hash": panel_hash(prompt, defaults["negative"], defaults["aspect_ratio"]),
            })

    if args.show:
        match = next((c for c in compiled if c["id"] == args.show), None)
        if not match:
            sys.exit(f"no panel with id {args.show}")
        print(json.dumps(match, ensure_ascii=False, indent=2))
        return

    out = ROOT / "out" / "prompts.json"
    out.parent.mkdir(exist_ok=True)

    # Preserve prior hashes so we can report what actually changed.
    previous = {}
    if out.exists():
        previous = {p["id"]: p["hash"] for p in json.loads(out.read_text(encoding="utf-8"))["panels"]}

    out.write_text(
        json.dumps({"project": project["project"], "panels": compiled}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    changed = [c["id"] for c in compiled if previous.get(c["id"]) != c["hash"]]
    print(f"compiled {len(compiled)} panels across {len(book['pages'])} pages -> out/prompts.json")
    if previous:
        print(f"changed since last build: {', '.join(changed) if changed else '(none)'}")
    else:
        print("first build — all panels are new")


if __name__ == "__main__":
    main()
