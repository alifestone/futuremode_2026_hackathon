#!/usr/bin/env python3
"""Determine the FINAL prompt for every cut. Single source of truth.

This is the render engine behind decisions.md §3/§5/§9 — the ONE function that
produces the exact prompt string a model receives, so that local execution and
every web export consume byte-identical text. Also the ONE place where the
canonical compile order is enforced.

    compile order (fixed, decisions.md §3.4):
      character → state → scene → set_piece → look → action/camera/sync → style

    variation discipline (decisions.md §3.5):
      fact changes  -> new item in items.json (the registry keeps ONE copy)
      emphasis only -> shot.overrides[item_id] = "appended text" (never replaces)

Usage:
    python app/scripts/build.py [--project luna-comic]            # write out/compiled.{json,md}
    python app/scripts/build.py --show S12                         # print one resolved shot
    python app/scripts/build.py --model "ComfyUI MiniMax H3"       # print a model batch
    python app/scripts/build.py --draft                            # don't hard-fail on contract
"""
import argparse
import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
APP = REPO / "app"


# ---------------------------------------------------------------- loading

def load_project(project_dir: pathlib.Path):
    """Return (manifest, items_by_id, shots, lyrics_by_id, schema)."""
    manifest = json.loads((project_dir / "manifest.json").read_text(encoding="utf-8"))
    items = json.loads((project_dir / "items.json").read_text(encoding="utf-8"))
    items_by_id = {it["id"]: it for it in items["items"]}
    book = json.loads((project_dir / "storyboard" / "shots.json").read_text(encoding="utf-8"))
    lyrics_by_id = {}
    lyrics_path = project_dir / "lyrics" / "lyrics.json"
    if lyrics_path.exists():
        lyrics_data = json.loads(lyrics_path.read_text(encoding="utf-8"))
        lyrics_by_id = {l["id"]: l for l in lyrics_data["lines"]}
    schema = json.loads((APP / "items.schema.json").read_text(encoding="utf-8"))
    return manifest, items_by_id, book, lyrics_by_id, schema


# ------------------------------------------------------------- render core

def ordered_type(type_, schema):
    order = schema["compile_order"]
    return order.index(type_) if type_ in order else len(order)


def resolve_shot(shot, items_by_id, schema, project_dir: pathlib.Path, manifest):
    """Resolve a shot's item references into an ordered, override-merged list.

    Returns dict with:
      parts      : list of (kind, text) in canonical compile order (already merged)
      item_snapshot : [{id, type, text}] as-of-now, for lock.py freezing
      missing    : item ids referenced but absent from registry
    """
    missing = [i for i in shot.get("items", []) if i not in items_by_id]
    overrides = shot.get("overrides", {})
    missing += [i for i in overrides if i not in items_by_id]

    refs = shot.get("items", [])
    unique = []
    for i in refs:
        if i not in unique:
            unique.append(i)

    item_snapshot = []
    parts = []
    # character block
    for i in sorted([i for i in unique if items_by_id.get(i, {}).get("type") == "character"],
                    key=lambda i: items_by_id[i]["id"]):
        text = merge_item(items_by_id[i], overrides.get(i))
        parts.append(("character", text))
        item_snapshot.append({"id": i, "type": "character", "text": items_by_id[i]["text"]})
    parts.append(("expression", f'expression: {shot["expression"]}'))
    # state / scene / set_piece / look in canonical order
    for t in ["state", "scene", "set_piece", "look"]:
        for i in [i for i in unique if items_by_id.get(i, {}).get("type") == t]:
            text = merge_item(items_by_id[i], overrides.get(i))
            parts.append((t, text))
            item_snapshot.append({"id": i, "type": t, "text": items_by_id[i]["text"]})
    # camera_grammar items, if any
    for i in [i for i in unique if items_by_id.get(i, {}).get("type") == "camera_grammar"]:
        text = merge_item(items_by_id[i], overrides.get(i))
        parts.append(("camera_grammar", text))
        item_snapshot.append({"id": i, "type": "camera_grammar", "text": items_by_id[i]["text"]})
    # the editable action/camera middle — sits after world, before style
    parts.append(("action_camera", f'{shot["action"]}; camera: {shot["camera"]}'))
    # style lock always ends the item block (canonical order)
    for i in [i for i in unique if items_by_id.get(i, {}).get("type") == "style"]:
        text = merge_item(items_by_id[i], overrides.get(i))
        parts.append(("style", text))
        item_snapshot.append({"id": i, "type": "style", "text": items_by_id[i]["text"]})
    return {"parts": parts, "item_snapshot": item_snapshot, "missing": missing}


def merge_item(item, override):
    text = item["text"]
    if override:
        text += ". " + override  # append-only, never replace (decisions.md §3.5)
    return text


def render_prompt(shot, resolved, manifest, lyrics_by_id, schema):
    """Assemble the FINAL prompt string. Byte-for-byte the parity contract."""
    seg = []
    for kind, text in resolved["parts"]:
        if kind == "action_camera":
            seg.append(text)
        else:
            seg.append(text)

    # continuity hooks (decisions.md §6.1)
    cin, cout = shot.get("continuity_in", ""), shot.get("continuity_out", "")
    if cin or cout:
        hook = "continuity: opens continuing " + (cin or "the previous cut") + \
               "; leaves " + (cout or "handing to the next cut")
        seg.append(hook)

    # vocal: lyric original text + intent (decisions.md §5.1/§5.2)
    lines = [lyrics_by_id[l]["text"] for l in shot.get("lyric_lines", []) if l in lyrics_by_id]
    intent = shot.get("lyric_intent", "").strip()
    if lines or intent:
        lyric_txt = " / ".join(lines) if lines else "(no lyric this beat)"
        seg.append(f'vocal: 「{lyric_txt}」 — {intent or "beat of silence, let the music carry"}')

    # duration + sync
    sync = shot.get("sync", "").rstrip(". ")
    bpm = manifest.get("song", {}).get("bpm", 106)
    seg.append(f'duration {shot["dur"]:.2f}s, motion synced to {bpm} BPM; {sync}')

    return ". ".join(s for s in seg if s)


def context_hash(prompt, settings_payload, ref_hashes):
    """Deterministic fingerprint binding prompt + env-agnostic settings + refs.

    decisions.md §9.1: local and web must show THE SAME hash for the same input
    context — platform-specific renderings never enter this.
    """
    payload = json.dumps({
        "prompt": prompt,
        "settings": settings_payload,
        "refs": sorted(ref_hashes),
    }, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ------------------------------------------------------------- compilation

def compile_shots(project_dir: pathlib.Path):
    manifest, items_by_id, book, lyrics_by_id, schema = load_project(project_dir)
    negative = manifest.get("style", {}).get("negative", "")
    ratio = manifest.get("style", {}).get("aspect_ratio", "16:9")
    refs = manifest.get("character", {}).get("reference_sheet", [])
    default_ref = refs if isinstance(refs, str) else (refs[0] if refs else "")
    ref_path = project_dir / default_ref if default_ref else None
    ref_hash = ""
    if ref_path and ref_path.exists():
        ref_hash = hashlib.sha256(ref_path.read_bytes()).hexdigest()[:16]

    compiled, problems = [], []
    for shot in book["shots"]:
        resolved = resolve_shot(shot, items_by_id, schema, project_dir, manifest)
        prompt = render_prompt(shot, resolved, manifest, lyrics_by_id, schema)
        settings = {"dur": shot["dur"], "start": shot["start"], "end": shot["end"],
                    "ratio": ratio, "expression": shot["expression"],
                    "bar": shot.get("bar"), "section": shot.get("section")}
        c_hash = context_hash(prompt, settings, [ref_hash] if ref_hash else [])
        problems += shot_problems(shot, resolved, schema, lyrics_by_id, items_by_id)
        compiled.append({
            "id": shot["id"],
            "section": shot.get("section"),
            "bar": shot.get("bar"),
            "start": shot["start"], "end": shot["end"], "dur": shot["dur"],
            "model": shot.get("model", ""),
            "status": shot.get("status", "pending"),
            "aspect_ratio": ratio,
            "negative": negative,
            "references": [default_ref] if default_ref else [],
            "ref_hashes": [ref_hash] if ref_hash else [],
            "items": shot.get("items", []),
            "overrides": shot.get("overrides", {}),
            "continuity": {"in": shot.get("continuity_in", ""), "out": shot.get("continuity_out", "")},
            "lyric_lines": shot.get("lyric_lines", []),
            "lyric_intent": shot.get("lyric_intent", ""),
            "caption": shot.get("caption", ""),
            "expression": shot.get("expression", ""),
            "item_snapshot": resolved["item_snapshot"],
            "prompt": prompt,
            "hash": c_hash,
            "context_hash": c_hash,
        })
    return {"project": manifest.get("project", ""), "schema": schema["schema_version"],
            "shots": compiled, "problems": problems}


def shot_problems(shot, resolved, schema, lyrics_by_id, items_by_id):
    """Structural problems only (decisions.md §4.4). Semantic coverage = plan lint."""
    out = []
    if resolved["missing"]:
        out.append(f'{shot["id"]}: missing item refs {", ".join(resolved["missing"])}')
    if not shot.get("items"):
        out.append(f'{shot["id"]}: references no items at all')
    types = {items_by_id.get(i, {}).get("type") for i in shot.get("items", [])}
    for need in ("character", "scene"):
        if need not in types:
            out.append(f'{shot["id"]}: missing a {need} item')
    if shot.get("lyric_lines") and not shot.get("lyric_intent", "").strip():
        out.append(f'{shot["id"]}: has lyric_lines but no lyric_intent (contract §5.1)')
    for field in ("continuity_in", "continuity_out"):
        if not shot.get(field, "").strip():
            out.append(f'{shot["id"]}: missing {field}')
    return out


def to_markdown(project, compiled):
    out = [
        f"# {project['project']} — compiled cuts",
        "",
        f"{len(compiled)} cuts · schema {project['schema']} · generated by `app/scripts/build.py` — do not edit by hand.",
        "",
    ]
    for c in compiled:
        out.append(f"### {c['id']} · {c['start']:.2f}–{c['end']:.2f}s ({c['dur']:.2f}s) · "
                   f"bar {c['bar']} · {c['section']}")
        out.append("")
        out.append(f"- **context_hash** `{c['context_hash']}` · status {c['status']} · ratio {c['aspect_ratio']}")
        out.append(f"- **items** {', '.join(c['items'])}")
        if c["overrides"]:
            out.append(f"- **overrides** {json.dumps(c['overrides'], ensure_ascii=False)}")
        if c["continuity"]["in"]:
            out.append(f"- **in** {c['continuity']['in']}")
        if c["continuity"]["out"]:
            out.append(f"- **out** {c['continuity']['out']}")
        if c["caption"]:
            out.append(f"- **caption** 「{c['caption']}」 (overrides lyric subtitle)")
        if c["lyric_lines"]:
            out.append(f"- **vocal** {c['lyric_lines']} · intent: {c['lyric_intent']}")
        out.append("")
        out.append("```")
        out.append(c["prompt"])
        out.append("```")
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="luna-comic", help="project dir under the repo root")
    ap.add_argument("--show", metavar="CUT_ID", help="print one resolved cut and exit")
    ap.add_argument("--model", help="print only the batch for one model and exit")
    ap.add_argument("--draft", action="store_true", help="report problems only, never fail")
    args = ap.parse_args()

    project_dir = REPO / args.project
    if not (project_dir / "manifest.json").exists():
        sys.exit(f"no project manifest at {project_dir / 'manifest.json'}")

    compiled = compile_shots(project_dir)

    if args.show:
        m = next((c for c in compiled["shots"] if c["id"].upper() == args.show.upper()), None)
        if not m:
            sys.exit(f"no cut {args.show}")
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return

    if args.model:
        batch = [c for c in compiled["shots"] if c["model"] == args.model]
        if not batch:
            models = sorted({c["model"] for c in compiled["shots"]})
            sys.exit(f"no cuts for model {args.model!r}. Known: {', '.join(models)}")
        print(json.dumps(batch, ensure_ascii=False, indent=2))
        return

    out_dir = project_dir / "out"
    out_dir.mkdir(exist_ok=True)
    previous = {}
    prev_path = out_dir / "compiled.json"
    if prev_path.exists():
        previous = {s["id"]: s["context_hash"] for s in
                    json.loads(prev_path.read_text(encoding="utf-8"))["shots"]}

    (out_dir / "compiled.json").write_text(
        json.dumps(compiled, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "compiled.md").write_text(
        to_markdown(compiled, compiled["shots"]), encoding="utf-8")

    changed = [c["id"] for c in compiled["shots"] if previous.get(c["id"]) != c["context_hash"]]
    print(f"compiled {len(compiled['shots'])} cuts -> out/compiled.json + compiled.md")
    if compiled["problems"]:
        print(f"problems ({'draft, reported only' if args.draft else 'HARD GATE — fix these before lock'}):")
        for p in compiled["problems"]:
            print(f"  - {p}")
        if not args.draft:
            sys.exit(1)
    if previous:
        print(f"changed since last build: {', '.join(changed) if changed else '(none)'}")
    else:
        print("first build — all cuts new")


if __name__ == "__main__":
    main()