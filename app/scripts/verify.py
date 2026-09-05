#!/usr/bin/env python3
"""Hash audit (decisions.md §13). Reconcile clips against packages.

For every cut, tells you whether a generated clip matches the CURRENT frozen
context: clip recorded context_hash == package context_hash. Anything else is
stale — the input context changed after that clip was generated.

Also reports local-vs-web parity: cuts that have both a local and a web clip
recorded, with their hashes side by side.

Usage:
    python app/scripts/verify.py            # default project = luna-comic-2
    python app/scripts/verify.py --json                        # machine JSON
    python app/scripts/verify.py --check                       # exit 1 if any stale
"""
import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
APP = REPO / "app"
sys.path.insert(0, str(APP / "scripts"))
import build as B

STATE = "out/run_state.json"


def audit(project_dir: pathlib.Path):
    compiled = B.compile_shots(project_dir)
    by_id = {c["id"]: c for c in compiled["shots"]}
    state = {}
    sp = project_dir / STATE
    if sp.exists():
        state = json.loads(sp.read_text(encoding="utf-8")).get("shots", {})

    report = []
    ok = stale = missing = 0
    for cid, cut in by_id.items():
        rec = state.get(cid, {})
        clips = rec.get("clips", [])
        pkg_dir = project_dir / "out" / "packages" / cid
        pkg = None
        if (pkg_dir / "context.json").exists():
            pkg = json.loads((pkg_dir / "context.json").read_text(encoding="utf-8"))
        current = pkg["context_hash"] if pkg else cut["context_hash"]
        entry = {"id": cid, "package": bool(pkg), "current_hash": current,
                 "clips": clips, "state": "missing"}
        if not clips:
            missing += 1
            report.append(entry)
            continue
        for cl in clips:
            cl_state = "ok" if cl.get("context_hash") == current else "stale"
            if cl_state == "ok":
                ok += 1
            else:
                stale += 1
        entry["state"] = "stale" if stale_flag(clips, current) else "ok"
        report.append(entry)
    return {"cuts": report, "summary": {"total": len(by_id), "ok": ok, "stale": stale,
                                        "un_generated": missing}}


def stale_flag(clips, current):
    return any(cl.get("context_hash") != current for cl in clips)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="luna-comic-2")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    report = audit(REPO / args.project)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        s = report["summary"]
        print(f"verify · {s['total']} cuts · {s['ok']} clips current · "
              f"{s['stale']} stale · {s['un_generated']} not generated")
        for c in report["cuts"]:
            for cl in c["clips"]:
                flag = "stale" if cl.get("context_hash") != c["current_hash"] else "ok"
                print(f"  {c['id']:5s} {cl.get('platform','?'):12s} {cl.get('file',''):28s} "
                      f"{flag}  {cl.get('context_hash','')[:12]}")
            if not c["clips"]:
                print(f"  {c['id']:5s} (no clip)")

    if args.check and report["summary"]["stale"]:
        sys.exit(1)


if __name__ == "__main__":
    main()