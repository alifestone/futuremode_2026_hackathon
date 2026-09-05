#!/usr/bin/env python3
"""Plan pass — turn missing detail into a work list the agent can fill.

Reads the same inputs as build.py and emits a GAP REPORT: item references that
do not resolve, shots missing contract fields, faceted checklist reminders per
item (the LLM-lint work order), and registry coverage. Machinable output for
the UI and for coding agents.

Usage:
    python app/scripts/plan.py [--project luna-comic]          # human table
    python app/scripts/plan.py --json                          # machine JSON
    python app/scripts/plan.py --check                         # exit code only
"""
import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
APP = REPO / "app"
sys.path.insert(0, str(APP / "scripts"))

import build as B


def gap_report(project_dir: pathlib.Path):
    manifest, items_by_id, book, lyrics_by_id, schema = B.load_project(project_dir)
    types_schema = schema["types"]
    facets_by_type = {t: v.get("facets", []) for t, v in types_schema.items()}
    min_len = {t: v.get("min_text_chars", 0) for t, v in types_schema.items()}

    gaps = {"registry": [], "shots": [], "items_facets": [], "summary": {}}

    # --- registry level
    types_used = {}
    for it in items_by_id.values():
        t = it["type"]
        types_used[t] = types_used.get(t, 0) + 1
        if t not in types_schema:
            gaps["registry"].append(f'item {it["id"]}: unknown type {t!r}')
            continue
        if len(it.get("text", "")) < min_len.get(t, 0):
            gaps["registry"].append(
                f'item {it["id"]} ({t}): text only {len(it["text"])} chars '
                f'(min {min_len.get(t)})')
        gaps["items_facets"].append({
            "id": it["id"], "type": t, "text": it["text"],
            "checklist": facets_by_type.get(t, []),
            "locked": it.get("locked", False),
        })
    for t in types_schema:
        if types_schema[t].get("required") and t not in types_used:
            gaps["registry"].append(f"no {t} item defined at all")

    # --- shot level
    for shot in book["shots"]:
        resolved = B.resolve_shot(shot, items_by_id, schema, project_dir, manifest)
        problems = B.shot_problems(shot, resolved, schema, lyrics_by_id, items_by_id)
        for p in problems:
            gaps["shots"].append(p)

    # --- summary
    gaps["summary"] = {
        "total_shots": len(book["shots"]),
        "total_items": len(items_by_id),
        "registry_problems": len(gaps["registry"]),
        "shot_problems": len(gaps["shots"]),
        "items_needing_llm_lint": len(gaps["items_facets"]),
        "types_present": types_used,
    }
    return gaps


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="luna-comic")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--check", action="store_true", help="exit 1 if structural gaps exist")
    args = ap.parse_args()

    project_dir = REPO / args.project
    report = gap_report(project_dir)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        s = report["summary"]
        print(f"plan report · {s['total_shots']} shots · {s['total_items']} items")
        print(f"  registry problems : {s['registry_problems']}")
        print(f"  shot problems     : {s['shot_problems']}")
        print(f"  items for LLM lint: {s['items_needing_llm_lint']}")
        for p in report["registry"]:
            print("  !", p)
        for p in report["shots"]:
            print("  !", p)

    if args.check and (report["summary"]["registry_problems"] or report["summary"]["shot_problems"]):
        sys.exit(1)


if __name__ == "__main__":
    main()