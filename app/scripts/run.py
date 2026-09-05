#!/usr/bin/env python3
"""Execute locked cuts — local ComfyUI batch or imported web results.

Local path: reads the frozen package (out/packages/<CUT>/context.json), builds
the graph via export.export.render('local'), queues it on the local ComfyUI
(127.0.0.1:8188, unauthenticated — open weights on the box), waits, downloads
the clip, and records it in out/run_state.json WITH its context_hash and
platform tag. Web path: you generate the cut on a web platform from the package
block, then import the resulting file here with --import-web so the same
accounting is recorded.

Parity contract (decisions.md §9): every clip record carries the context_hash of
the exact package it was made from — local clips and web clips of the same cut
must and will show the same hash, making divergence attributable to platform
noise rather than missing context.

Usage:
    python app/scripts/run.py                    # default project = luna-comic-2, run pending
    python app/scripts/run.py --list
    python app/scripts/run.py --cuts S03                     # anchor first
    python app/scripts/run.py --pending                      # everything not done
    python app/scripts/run.py --cuts S04 --force             # re-roll
    python app/scripts/run.py --pending --dry-run            # print plans only
    python app/scripts/run.py --import-web S12 --file out/web/S12.mp4
"""
import argparse
import json
import mimetypes
import pathlib
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
APP = REPO / "app"
sys.path.insert(0, str(APP / "scripts"))
import build as B
import export as X

STATE = "out/run_state.json"
PACKAGES = "out/packages"
CLIPS = "out/clips"
DEFAULT_URL = "http://127.0.0.1:8188"
POLL_SECONDS = 10


def _request(url, data=None, headers=None, method=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def api_get(base, path, timeout=60):
    return json.loads(_request(f"{base}{path}", timeout=timeout))


def upload_image(base, path: pathlib.Path, subfolder="luna"):
    boundary = f"----luna{uuid.uuid4().hex}"
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts = []
    for field, value in (("subfolder", subfolder), ("overwrite", "true"), ("type", "input")):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{value}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{path.name}\"\r\n"
                 f"Content-Type: {ctype}\r\n\r\n".encode() + path.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    resp = json.loads(_request(f"{base}/api/upload/image", data=b"".join(parts),
                               headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                               method="POST", timeout=300))
    return f"{resp.get('subfolder','')}/{resp['name']}" if resp.get("subfolder") else resp["name"]


def submit(base, graph, client_id):
    return json.loads(_request(f"{base}/api/prompt",
                               data=json.dumps({"prompt": graph, "client_id": client_id}).encode(),
                               headers={"Content-Type": "application/json"},
                               method="POST", timeout=120))["prompt_id"]


def wait_for(base, prompt_id, label, timeout=60 * 60):
    started = time.time()
    while time.time() - started < timeout:
        entry = api_get(base, f"/api/history/{prompt_id}").get(prompt_id)
        if entry:
            st = entry.get("status", {})
            if st.get("completed") or st.get("status_str") == "success":
                return entry, int(time.time() - started)
            if st.get("status_str") == "error":
                raise RuntimeError(f"{label} failed: {json.dumps(st.get('messages', []), ensure_ascii=False)[:1500]}")
        print(f"\r  {label}: generating… {int(time.time() - started)}s", end="", flush=True)
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f"{label}: no result after {timeout}s")


def download_output(base, entry, dest: pathlib.Path):
    for node_output in entry.get("outputs", {}).values():
        for item in node_output.get("images", []):
            q = urllib.parse.urlencode({"filename": item["filename"],
                                        "subfolder": item.get("subfolder", ""),
                                        "type": item.get("type", "output")})
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(_request(f"{base}/api/view?{q}", timeout=600))
            return dest
    raise RuntimeError("job finished but produced no video output")


# ---------------------------------------------------------------- state

def load_state(project_dir):
    sp = project_dir / STATE
    return json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"shots": {}}


def save_state(project_dir, state):
    sp = project_dir / STATE
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_clip(project_dir, cut_id, context_hash, platform, file, extra=None):
    state = load_state(project_dir)
    rec = state["shots"].setdefault(cut_id, {})
    rec["status"] = "done"
    rec["context_hash"] = context_hash
    rec["last_platform"] = platform
    clips = rec.setdefault("clips", [])
    clips.append({"platform": platform, "file": file,
                  "context_hash": context_hash, "ts": int(time.time()), **(extra or {})})
    save_state(project_dir, state)
    return state


def mark_storyboard(project_dir, done_ids):
    p = project_dir / "storyboard" / "shots.json"
    book = json.loads(p.read_text(encoding="utf-8"))
    for shot in book["shots"]:
        if shot["id"] in done_ids:
            shot["status"] = "generated"
    p.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pending_cuts(project_dir, compiled):
    state = load_state(project_dir)
    out = []
    for c in compiled:
        rec = state["shots"].get(c["id"], {})
        current = any(cl.get("context_hash") == c["context_hash"] for cl in rec.get("clips", []))
        if not current:
            out.append(c)
    return out


# ---------------------------------------------------------------- commands

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="luna-comic-2")
    ap.add_argument("--cuts", help="comma-separated cut ids")
    ap.add_argument("--pending", action="store_true", help="all cuts without a current clip")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true", help="regenerate even if current clip exists")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--import-web", metavar="CUT_ID", help="record a web-generated clip")
    ap.add_argument("--file", help="path to the web-generated clip (with --import-web)")
    args = ap.parse_args()

    project_dir = REPO / args.project
    compiled = B.compile_shots(project_dir)["shots"]
    by_id = {c["id"]: c for c in compiled}

    if args.import_web:
        if not args.file:
            sys.exit("--import-web needs --file")
        cut = by_id.get(args.import_web.upper())
        if not cut:
            sys.exit(f"unknown cut {args.import_web}")
        src = pathlib.Path(args.file)
        if not src.exists():
            sys.exit(f"file not found: {src}")
        dest = project_dir / CLIPS / f"{cut['id']}__web.mp4"
        dest.write_bytes(src.read_bytes())
        record_clip(project_dir, cut["id"], cut["context_hash"], "web", str(dest.relative_to(project_dir)),
                    {"web_file": str(src)})
        print(f"imported {src} -> {dest.relative_to(project_dir)} as web clip of {cut['id']} "
              f"(hash {cut['context_hash'][:12]})")
        return

    if args.list:
        purl = args.url.rstrip("/")
        for c in compiled:
            frames = X.grid_length(c["dur"])
            print(f"{c['id']:5s} {c['start']:7.2f}-{c['end']:7.2f} {c['dur']:5.2f}s "
                  f"grid {frames:3d}f  {c['section']:18s} hash {c['context_hash'][:12]}")
        return

    # build the batch
    if args.cuts:
        wanted = [w.strip().upper() for w in args.cuts.split(",") if w.strip()]
        missing = [w for w in wanted if w not in by_id]
        if missing:
            sys.exit(f"unknown cuts: {', '.join(missing)}")
        batch = [by_id[w] for w in wanted]
    else:
        batch = pending_cuts(project_dir, compiled)
    if not args.force:
        done_now = [c["id"] for c in batch if not any(
            cl.get("context_hash") == c["context_hash"] for cl in
            load_state(project_dir)["shots"].get(c["id"], {}).get("clips", []))]
        batch = [c for c in batch if c["id"] in done_now or c["id"] not in
                 {x["id"] for x in []}]  # keep simple: pending already excludes current
    if args.limit:
        batch = batch[:args.limit]
    if not batch:
        print("nothing to generate.")
        return

    # every cut must be locked (hard gate passed → package exists)
    unlocks = []
    for c in batch:
        pkg = project_dir / PACKAGES / c["id"] / "context.json"
        if not pkg.exists():
            unlocks.append(c["id"])
    if unlocks:
        sys.exit(f"HARD GATE: these cuts are not locked — run lock.py first: {', '.join(unlocks)}")

    base = args.url.rstrip("/")
    print(f"local batch · {len(batch)} cuts · ComfyUI {base} · free open weights")
    print(f"cuts: {', '.join(c['id'] for c in batch)}")

    ref_path = project_dir / "assets" / "reference" / "luna_character_sheet.jpg"
    if not ref_path.exists():
        sys.exit(f"reference image missing: {ref_path}")
    if args.dry_run:
        for c in batch:
            seed = args.seed if args.seed is not None else random.Random(c["id"]).randrange(4294967295)
            frames = X.grid_length(c["dur"])
            print(f"  {c['id']}: {frames}f grid @ {X.dimensions(0.5)[0]}x{X.dimensions(0.5)[1]} "
                  f"seed {seed} hash {c['context_hash'][:12]}")
        print("dry run — nothing submitted.")
        return

    ref_name = upload_image(base, ref_path)
    print(f"uploaded reference as {ref_name}")

    for i, c in enumerate(batch, 1):
        seed = args.seed if args.seed is not None else random.Random(c["id"]).randrange(4294967295)
        label = f"[{i}/{len(batch)}] {c['id']}"
        try:
            graph = X.render(c, "local", project_dir, ref_name=ref_name, seed=seed,
                             width=960, height=544, steps=8, turbo=True)["graph"]
            pid = submit(base, graph, str(uuid.uuid4()))
            entry, elapsed = wait_for(base, pid, label)
            dest = download_output(base, entry, project_dir / CLIPS / f"{c['id']}.mp4")
        except (RuntimeError, TimeoutError, urllib.error.URLError) as e:
            print(f"\r{label} FAILED: {e}")
            state = load_state(project_dir)
            state["shots"].setdefault(c["id"], {})["status"] = "failed"
            save_state(project_dir, state)
            continue
        print(f"\r{label} -> {dest.relative_to(project_dir)} in {elapsed//60}m{elapsed%60:02d}s   ")
        record_clip(project_dir, c["id"], c["context_hash"], "local",
                    str(dest.relative_to(project_dir)),
                    {"seed": seed, "frames": X.grid_length(c["dur"]),
                     "resolution": "960x544", "steps": 8, "turbo": True})
    mark_storyboard(project_dir, [c["id"] for c in batch])
    print("next: python app/scripts/verify.py  then  python app/scripts/assemble.py")


if __name__ == "__main__":
    main()