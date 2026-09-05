#!/usr/bin/env python3
"""Hard gate + package builder (decisions.md §4.3, §7).

lock.py is the ONLY place a cut becomes shippable: structural contract checks
fail the run (no exceptions), then a frozen snapshot package is written to
out/packages/<CUT_ID>/ — context.json is the single authoritative payload, and
context_hash binds prompt + settings + reference hashes so local execution and
any web export can be reconciled later (decisions.md §9).

Usage:
    python app/scripts/lock.py              # default project = luna-comic-2, lock all cuts
    python app/scripts/lock.py --cuts S01,S04                         # lock a subset
    python app/scripts/lock.py --dry-run                               # validate only
"""
import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
APP = REPO / "app"
sys.path.insert(0, str(APP / "scripts"))
import build as B
import export as X

PACKAGES = "out/packages"


def package_dir(project_dir: pathlib.Path, cut_id: str) -> pathlib.Path:
    return project_dir / PACKAGES / cut_id


def build_package(project_dir: pathlib.Path, cut, manifest):
    """The frozen snapshot. Returns (package_dir, problems)."""
    problems = []
    d = package_dir(project_dir, cut["id"])

    # reference images (hashes computed by build.py already)
    refs = []
    for ref in cut.get("references", []):
        p = project_dir / ref
        if not p.exists():
            problems.append(f"{cut['id']}: reference missing {ref}")
            continue
        import hashlib as _h
        refs.append({"path": ref, "hash": cut.get("ref_hashes", [""])[0],
                     "sha256": _h.sha256(p.read_bytes()).hexdigest()})

    # settings card (env-agnostic — never platform specifics, decisions.md §9.1)
    settings = {
        "start": cut["start"], "end": cut["end"], "dur": cut["dur"],
        "bar": cut["bar"], "section": cut["section"],
        "expression": cut.get("expression_plain", ""),
        "ratio": cut["aspect_ratio"], "bpm": manifest.get("song", {}).get("bpm", 106),
        "item_ids": cut["items"],
    }

    context = {
        "schema": "cut_context",
        "schema_version": cut.get("_schema", "0.1.0"),
        "cut_id": cut["id"],
        "project": manifest.get("project", ""),
        "prompt": cut["prompt"],
        "model_prompt": X.shot_prompt(cut),          # what the model actually receives
        "item_snapshot": cut.get("item_snapshot", []),
        "refs": refs,
        "settings": settings,
        "continuity": cut.get("continuity", {}),
        "lyric_lines": cut.get("lyric_lines", []),
        "lyric_intent": cut.get("lyric_intent", ""),
        "caption": cut.get("caption", ""),
        "edit_intent": {
            "in": cut["start"], "out": cut["end"],
            "trim_to_bar": True,
            "transition": "hard cut",
            "caption_overrides_subtitle": bool(cut.get("caption")),
        },
        "negative": cut.get("negative", ""),
        "context_hash": cut["context_hash"],
        "locked_at": None,  # filled by record step
    }
    return d, context, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="luna-comic-2")
    ap.add_argument("--cuts", help="comma-separated cut ids; default all")
    ap.add_argument("--dry-run", action="store_true", help="validate, write nothing")
    args = ap.parse_args()

    project_dir = REPO / args.project
    manifest, items_by_id, book, lyrics_by_id, schema = B.load_project(project_dir)
    compiled = B.compile_shots(project_dir)
    shots = compiled["shots"]

    if args.cuts:
        wanted = [w.strip().upper() for w in args.cuts.split(",") if w.strip()]
        shots = [c for c in shots if c["id"] in wanted]
        missing = [w for w in wanted if w not in {c["id"] for c in shots}]
        if missing:
            sys.exit(f"unknown cuts: {', '.join(missing)}")

    hard_gate, done, failures = [], [], []
    for c in shots:
        problems = list(compiled["problems"]) \
            if not args.cuts else B.shot_problems(
                next(s for s in book["shots"] if s["id"] == c["id"]),
                B.resolve_shot(next(s for s in book["shots"] if s["id"] == c["id"]),
                               items_by_id, schema, project_dir, manifest),
                schema, lyrics_by_id)
        problems = [p for p in problems if p.startswith(c["id"] + ":")]
        # also fail on unresolved refs / empty items
        if not c["items"]:
            problems.append(f"{c['id']}: references no items")
        if problems:
            hard_gate.append({"id": c["id"], "problems": problems})
            continue

        if args.dry_run:
            done.append(c["id"])
            continue

        d, context, p2 = build_package(project_dir, c, manifest)
        if p2:
            hard_gate.append({"id": c["id"], "problems": p2})
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / "context.json").write_text(
            json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
        (d / "prompt.txt").write_text(context["model_prompt"] + "\n", encoding="utf-8")
        # platform render artifacts
        seed = 0
        try:
            local = X.render(c, "local", project_dir, ref_name="luna/luna_character_sheet.jpg",
                             width=960, height=544, seed=seed, steps=8, turbo=True)
            (d / "graph_local.json").write_text(
                json.dumps(local["graph"], ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:  # noqa
            print(f"  warn: local graph render failed for {c['id']}: {e}")
        web = X.render(c, "generic_web", project_dir)
        (d / "web_paste.md").write_text(web["text"], encoding="utf-8")
        # reference image copy
        for ref in c.get("references", []):
            rp = project_dir / ref
            if rp.exists():
                dest = d / "ref" / pathlib.Path(ref).name
                dest.parent.mkdir(exist_ok=True)
                dest.write_bytes(rp.read_bytes())
        done.append(c["id"])

    print(f"lock: {len(done)}/{len(shots)} passed")
    if hard_gate:
        print("HARD GATE — fix before these cut(s) can ship:")
        for h in hard_gate:
            print(f"  {h['id']}:")
            for p in h["problems"]:
                print(f"    - {p}")
        sys.exit(1)
    if done and not args.dry_run:
        print(f"packages written under {project_dir / PACKAGES}/")


if __name__ == "__main__":
    main()