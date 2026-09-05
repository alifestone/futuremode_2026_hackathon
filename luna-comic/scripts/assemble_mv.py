#!/usr/bin/env python3
"""Cut the generated clips to the bar grid and assemble the finished MV.

Every clip in out/clips/ was generated at 4-15s (the MiniMax H3 node's bounds),
which is at or above its slot length. This trims each one back to its exact slot
from storyboard/shots.json — the whole point of the project, since those slots
are measured bar lines, not estimates — normalises them to one resolution and
frame rate, concatenates in shot order, and muxes 歌曲.mp3 over the top.

The audio is the master clock: the timeline is rebuilt from the shot slots, so a
clip that is short (a failed re-roll, a truncated download) is held on its last
frame rather than sliding every later shot off the beat.

Usage:
    python scripts/assemble_mv.py                     # -> out/LUNA_MV.mp4
    python scripts/assemble_mv.py --subs              # burn lyrics/lyrics.srt
    python scripts/assemble_mv.py --height 1080       # output height (default 1080)
    python scripts/assemble_mv.py --check             # report what is missing, build nothing
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "out" / "shot_prompts.json"
CLIPS = ROOT / "out" / "clips"
WORK = ROOT / "out" / "_assemble"
AUDIO = ROOT / ".." / "歌曲.mp3"
SUBS = ROOT / "lyrics" / "lyrics.srt"
OUTPUT = ROOT / "out" / "LUNA_MV.mp4"

FPS = 30


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ffmpeg failed:\n  {' '.join(cmd[:6])} …\n{proc.stderr[-2000:]}")
    return proc


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subs", action="store_true", help="burn lyrics/lyrics.srt into the picture")
    ap.add_argument("--height", type=int, default=1080, help="output height (default 1080)")
    ap.add_argument("--check", action="store_true", help="report missing/short clips and exit")
    ap.add_argument("--out", type=pathlib.Path, default=OUTPUT)
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")

    shots = json.loads(PROMPTS.read_text(encoding="utf-8"))["shots"]
    width = args.height * 16 // 9

    missing, short = [], []
    for s in shots:
        clip = CLIPS / f"{s['id']}.mp4"
        if not clip.exists():
            missing.append(s["id"])
            continue
        have = probe_duration(clip)
        if have < s["dur"] - 0.05:
            short.append((s["id"], round(have, 2), s["dur"]))

    if missing:
        print(f"missing {len(missing)}/{len(shots)} clips: {', '.join(missing)}")
        print("  generate them:  python scripts/run_minimax.py --pending --yes")
    if short:
        for sid, have, need in short:
            print(f"short clip {sid}: {have}s for a {need}s slot — last frame will be held")
    if args.check:
        if not missing and not short:
            print(f"all {len(shots)} clips present and long enough. Ready to assemble.")
        return
    if missing:
        sys.exit("refusing to assemble an incomplete timeline.")

    WORK.mkdir(parents=True, exist_ok=True)
    segments = []

    # Every cut is a measured bar line, so each segment's length is taken from the
    # timeline, not from its own duration: frames = round(end*fps) - round(start*fps).
    # Rounding each shot's duration independently instead lets the error accumulate —
    # measured on the first assembly, cuts drifted from -0.44s to +0.20s across the
    # film, a 0.64s swing, and at 106 BPM one beat is only 0.566s.
    lead_in = shots[0]["start"]
    if lead_in > 0.01:
        # The storyboard starts on bar 1 at 0.49s, not at 0. Without this the whole
        # film runs early against the song by exactly that much.
        black = WORK / "lead_in.mp4"
        run(["ffmpeg", "-y", "-f", "lavfi", "-i",
             f"color=c=black:s={width}x{args.height}:r={FPS}:d={lead_in:.3f}",
             "-frames:v", str(round(lead_in * FPS)), "-c:v", "libx264", "-preset", "medium",
             "-crf", "18", "-pix_fmt", "yuv420p", str(black)])
        segments.append(black)
        print(f"  lead-in {lead_in:.2f}s black to bar 1")

    for s in shots:
        clip = CLIPS / f"{s['id']}.mp4"
        seg = WORK / f"{s['id']}.mp4"
        frames = round(s["end"] * FPS) - round(s["start"] * FPS)
        # tpad holds the final frame if the clip is short of its slot.
        vf = (f"scale={width}:{args.height}:force_original_aspect_ratio=decrease,"
              f"pad={width}:{args.height}:(ow-iw)/2:(oh-ih)/2,"
              f"fps={FPS},tpad=stop_mode=clone:stop_duration=2,setsar=1")
        run(["ffmpeg", "-y", "-i", str(clip), "-vf", vf, "-frames:v", str(frames),
             "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-pix_fmt", "yuv420p", str(seg)])
        segments.append(seg)
        print(f"  cut {s['id']} -> {frames} frames ({frames / FPS:.3f}s for a {s['dur']:.2f}s slot)")

    listfile = WORK / "concat.txt"
    listfile.write_text("".join(f"file '{p.name}'\n" for p in segments), encoding="utf-8")

    silent = WORK / "picture.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c", "copy", str(silent)])

    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(AUDIO.resolve())]
    if args.subs:
        if not SUBS.exists():
            sys.exit(f"{SUBS} not found — run scripts/align_lyrics.py first")
        style = ("FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00301040,"
                 "BorderStyle=1,Outline=2,Shadow=1,MarginV=48")
        cmd += ["-vf", f"subtitles={SUBS.resolve()}:force_style='{style}'",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", str(args.out)]
    run(cmd)

    print(f"\n{args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out} "
          f"· {probe_duration(args.out):.2f}s · {width}x{args.height} · {len(shots)} shots")
    print(f"working files kept in {WORK.relative_to(ROOT)} — delete when happy")


if __name__ == "__main__":
    main()
