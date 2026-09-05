#!/usr/bin/env python3
"""Zero-dependency local HTTP server for the workflow UI (decisions.md §1.4).

Thin shell: every mutation shells out to the same scripts the CLI and agents
use, and reads/writes the same JSON files — the UI never maintains its own
state. Run:  python app/server.py   ->  http://127.0.0.1:8080

API:
    GET  /                    ui/index.html
    GET  /api/summary         manifest + gap + lifecycle counts
    GET  /api/items           items.json
    POST /api/items           save items.json (JSON body = registry)
    GET  /api/shots           storyboard + compiled (out/compiled.json if present)
    POST /api/shots           save storyboard (JSON body = book)
    POST /api/plan            -> plan.py --json
    POST /api/build           -> build.py (writes out/compiled.json), returns problems
    POST /api/lock            body {cuts?: [...]} -> lock.py
    GET  /api/packages        list package dirs + context hashes + clips
    GET  /api/export          ?cut=&platform= -> export.py render
    GET  /api/download        ?path=<rel> (project-root-relative, whitelisted)
    POST /api/run             body {cuts?: [...]} -> background run.py batch
    GET  /api/state           run_state.json
"""
import json
import mimetypes
import pathlib
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = pathlib.Path(__file__).resolve().parent.parent
APP = REPO / "app"
PROJECT = REPO / (sys.argv[1] if len(sys.argv) > 2 and sys.argv[1] == "--project" else "luna-comic")
if len(sys.argv) > 2 and sys.argv[1] == "--project":
    PROJECT = REPO / sys.argv[2]

SCRIPTS = APP / "scripts"
RUNNING = {}  # cut-id -> subprocess handle


def sh(script, *args, timeout=600):
    cmd = [sys.executable, str(SCRIPTS / script), "--project", PROJECT.name, *args]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def read_json(path, default=None):
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def summary():
    manifest = read_json(PROJECT / "manifest.json", {})
    items = read_json(PROJECT / "items.json", {})
    book = read_json(PROJECT / "storyboard" / "shots.json", {})
    compiled = read_json(PROJECT / "out" / "compiled.json", {})
    problems = compiled.get("problems", [])
    state = read_json(PROJECT / "out" / "run_state.json", {})
    pkgs = {}
    pkg_root = PROJECT / "out" / "packages"
    if pkg_root.exists():
        for d in pkg_root.iterdir():
            ctx = read_json(d / "context.json")
            if ctx:
                pkgs[d.name] = ctx.get("context_hash", "")
    return {
        "project": manifest.get("project", PROJECT.name),
        "reference_sheet": manifest.get("character", {}).get("reference_sheet", ""),
        "song": manifest.get("song", {}),
        "items": len(items.get("items", [])),
        "shots": len(book.get("shots", [])),
        "problems": problems,
        "locked": len(pkgs),
        "clips": sum(len(s.get("clips", [])) for s in state.get("shots", {}).values()),
        "packages": pkgs,
        "state": state,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text, code=200):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def do_GET(self):
        path = self.path.split("?")[0]
        q = {}
        if "?" in self.path:
            for kv in self.path.split("?", 1)[1].split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    q[k] = v

        if path == "/" or path == "/index.html":
            body = (APP / "ui" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/summary":
            return self.send_json(summary())
        if path == "/api/items":
            return self.send_json(read_json(PROJECT / "items.json", {}))
        if path == "/api/shots":
            return self.send_json({
                "book": read_json(PROJECT / "storyboard" / "shots.json", {}),
                "compiled": read_json(PROJECT / "out" / "compiled.json", {}),
            })
        if path == "/api/state":
            return self.send_json(read_json(PROJECT / "out" / "run_state.json", {}))
        if path == "/api/packages":
            return self.send_json(summary().get("packages", {}))
        if path == "/api/export":
            cut, platform = q.get("cut", ""), q.get("platform", "generic_web")
            rc, out, err = sh("export.py", "--cut", cut, "--platform", platform, "--json")
            if rc != 0:
                return self.send_json({"error": err.strip()}, 400)
            return self.send_text(out)
        if path == "/api/image":
            # inline image (no attachment) — for displaying refs in the UI
            rel = urllib.parse.unquote(q.get("path", ""))
            p = (PROJECT / rel).resolve()
            if not str(p).startswith(str(PROJECT.resolve())):
                return self.send_json({"error": "not allowed"}, 400)
            if not p.exists() or not p.is_file():
                return self.send_json({"error": "not found"}, 404)
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            body = p.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/download":
            rel = urllib.parse.unquote(q.get("path", ""))
            p = (PROJECT / rel).resolve()
            if not str(p).startswith(str(PROJECT.resolve())):
                return self.send_json({"error": "not allowed"}, 400)
            if not p.exists() or not p.is_file():
                return self.send_json({"error": "not found"}, 404)
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            body = p.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Disposition", f'attachment; filename="{p.name}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        body = self.read_body()

        if path == "/api/items":
            try:
                data = json.loads(body)
                (PROJECT / "items.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except json.JSONDecodeError as e:
                return self.send_json({"error": f"invalid JSON: {e}"}, 400)
            return self.send_json({"ok": True})
        if path == "/api/shots":
            try:
                data = json.loads(body)
                (PROJECT / "storyboard" / "shots.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except json.JSONDecodeError as e:
                return self.send_json({"error": f"invalid JSON: {e}"}, 400)
            return self.send_json({"ok": True})
        if path == "/api/build":
            rc, out, err = sh("build.py", "--draft")
            return self.send_json({"rc": rc, "out": out, "err": err,
                                   "summary": summary()})
        if path == "/api/plan":
            rc, out, err = sh("plan.py", "--json")
            if rc != 0 and not out:
                return self.send_json({"error": err.strip()}, 400)
            try:
                return self.send_json(json.loads(out))
            except json.JSONDecodeError:
                return self.send_json({"error": out}, 400)
        if path == "/api/lock":
            data = json.loads(body) if body else {}
            cuts = data.get("cuts") or []
            args = ["--cuts", ",".join(cuts)] if cuts else []
            rc, out, err = sh("lock.py", *args)
            return self.send_json({"rc": rc, "out": out, "err": err})
        if path == "/api/run":
            data = json.loads(body) if body else {}
            cuts = data.get("cuts") or []
            args = ["--cuts", ",".join(cuts)] if cuts else ["--pending"]
            cmd = [sys.executable, str(SCRIPTS / "run.py"), "--project", PROJECT.name, *args]
            proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            RUNNING["batch"] = proc
            return self.send_json({"ok": True, "started": args})
        if path == "/api/accept":
            # decisions.md §10.2 — accepted is a HUMAN-only transition
            data = json.loads(body) if body else {}
            cut_id = (data.get("cut") or "").upper()
            state = read_json(PROJECT / "out" / "run_state.json", {})
            rec = state.setdefault("shots", {}).setdefault(cut_id, {})
            rec["accepted"] = bool(data.get("accepted"))
            rec["accepted_by"] = "human"
            rec["accepted_at"] = __import__("time").time()
            (PROJECT / "out" / "run_state.json").write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return self.send_json({"ok": True})
        self.send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])
    print(f"LUNA workflow UI  ->  http://127.0.0.1:{port}   (project: {PROJECT.name})")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()