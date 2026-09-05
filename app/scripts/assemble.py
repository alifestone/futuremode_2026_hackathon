#!/usr/bin/env python3
"""Cut the generated clips to the bar grid and assemble the finished MV.

Same behaviour as the original luna-comic/scripts/assemble_mv.py, adapted to
consume out/compiled.json (produced by app/scripts/build.py) and the clip
records in out/run_state.json. Every clip was generated at the grid length
covering its slot; this trims to the exact measured bar-line slot, normalises to
one resolution/framerate, concatenates in order and muxes the song over the top.

The audio is the master clock: a short clip is held on its last frame rather
than sliding later shots off the beat.

Usage:
    python app/scripts/assemble.py --project luna-comic            # -> out/LUNA_MV.mp4
    python app/scripts/assemble.py --subs                          # burn lyrics/lyrics.srt
    python app/scripts/assemble.py --check                         # report what is missing
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
FPS = 30


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ffmpeg failed:\n  {' '.join(map(str, cmd[:6]))} …\n{proc.stderr[-2000:]}")
    return proc


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="luna-comic")
    ap.add_argument("--subs", action="store_true")
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=pathlib.Path)
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")

    project_dir = REPO / args.project
    shots = json.loads((project_dir / "out" / "compiled.json").read_text(encoding="utf-8"))["shots"]
    state = json.loads((project_dir / "out" / "run_state.json").read_text(encoding="utf-8")) \
        if (project_dir / "out" / "run_state.json").exists() else {"shots": {}}
    clips_dir = project_dir / "out" / "clips"
    audio = project_dir / ".." / "歌曲.mp3"
    subs = project_dir / "lyrics" / "lyrics.srt"
    output = args.out or (project_dir / "out" / "LUNA_MV.mp4")
    width = args.height * 16 // 9

    missing, short = [], []
    for s in shots:
        clip = clips_dir / f"{s['id']}.mp4"
        if not clip.exists():
            missing.append(s["id"])
            continue
        have = probe_duration(clip)
        if have < s["dur"] - 0.05:
            short.append((s["id"], round(have, 2), s["dur"]))

    if missing:
        print(f"missing {len(missing)}/{len(shots)} clips: {', '.join(missing)}")
    if short:
        for sid, have, need in short:
            print(f"short clip {sid}: {have}s for a {need}s slot — last frame will be held")
    if args.check:
        print(f"all {len(shots)} clips present and long enough. Ready to assemble." if not (missing or short)
              else "incomplete.")
        return
    if missing:
        sys.exit("refusing to assemble an incomplete timeline.")

    work = project_dir / "out" / "_assemble"
    work.mkdir(parents=True, exist_ok=True)
    segments = []
    for s in shots:
        clip = clips_dir / f"{s['id']}.mp4"
        seg = work / f"{s['id']}.mp4"
        vf = (f"scale={width}:{args.height}:force_original_aspect_ratio=decrease,"
              f"pad={width}:{args.height}:(ow-iw)/2:(oh-ih)/2,"
              f"fps={FPS},tpad=stop_mode=clone:stop_duration=2,setsar=1")
        run(["ffmpeg", "-y", "-i", str(clip), "-t", f"{s['dur']:.3f}",
             "-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-pix_fmt", "yuv420p", str(seg)])
        segments.append(seg)
        print(f"  cut {s['id']} -> {s['dur']:.2f}s")

    listfile = work / "concat.txt"
    listfile.write_text("".join(f"file '{p.name}'\n" for p in segments), encoding="utf-8")
    silent = work / "picture.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(silent)])

    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(audio.resolve())]
    if args.subs:
        if not subs.exists():
            sys.exit(f"{subs} not found")
        style = ("FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00301040,"
                 "BorderStyle=1,Outline=2,Shadow=1,MarginV=48")
        cmd += ["-vf", f"subtitles={subs.resolve()}:force_style='{style}'",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", str(output)]
    run(cmd)

    print(f"\n{output} · {probe_duration(output):.2f}s · {width}x{args.height} · {len(shots)} shots")


if __name__ == "__main__":
    main()