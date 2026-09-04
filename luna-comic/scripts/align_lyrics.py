#!/usr/bin/env python3
"""Align 歌詞.srt to the measured bar grid in storyboard/beatmap.json.

歌詞.srt is a whisper large-v3 forced-alignment transcript — every line's
start/end is measured directly from the vocal audio, not estimated. This
reads it as-is (no section-guessing, no proportional-by-length placement)
and annotates each line with which measured beatmap.json section its start
time falls in, purely for documentation/readability downstream.

Previously this read 歌詞.txt (one unbroken paragraph, no timecodes) and
inferred per-line timing by hand-assigning lines to sections and splitting
each section's span proportionally by line length. That produced only
estimates, off by several seconds in places once checked against the actual
forced-aligned transcript. 歌詞.srt supersedes 歌詞.txt as the timing source;
歌詞.txt is no longer read by this script.

Writes:
    lyrics/lyrics.json   line ids, text, section, bar, start/end, confidence
    lyrics/lyrics.srt    same lines, re-serialized as subtitles
and updates storyboard/shots.json in place, filling each shot's `lyric_lines`
with the ids of the lines that overlap it.

Usage:
    python scripts/align_lyrics.py
    python scripts/align_lyrics.py --check   # validate only, write nothing
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LYRICS_SRT = ROOT / ".." / "歌詞.srt"

SRT_BLOCK_RE = re.compile(
    r"(\d+)\s*\n"
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*\n"
    r"(.+?)(?=\n\s*\n|\Z)",
    re.S,
)


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def parse_srt(text):
    """SRT -> [{start, end, text}], seconds as float."""

    def to_sec(h, m, s, ms):
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    out = []
    for m in SRT_BLOCK_RE.finditer(text.strip() + "\n\n"):
        start = to_sec(*m.group(2, 3, 4, 5))
        end = to_sec(*m.group(6, 7, 8, 9))
        line_text = " ".join(m.group(10).split())
        out.append({"start": start, "end": end, "text": line_text})
    return out


def snap(t, offset, bar_sec):
    """Nearest bar line to t — for the documentation `bar` field only; the
    measured start/end times themselves are never snapped or adjusted."""
    n = round((t - offset) / bar_sec)
    return n + 1


def section_for(t, sections):
    for sec in sections:
        if sec["start"] <= t < sec["end"]:
            return sec["name"]
    return sections[-1]["name"] if t >= sections[-1]["end"] else sections[0]["name"]


def assign(raw_lines, beatmap):
    sections = beatmap["sections"]
    offset = beatmap["tempo"]["first_beat_offset_sec"]
    bar_sec = beatmap["tempo"]["bar_sec"]

    out = []
    for i, line in enumerate(raw_lines, 1):
        out.append({
            "id": f"L{i:02d}",
            "text": line["text"],
            "section": section_for(line["start"], sections),
            "bar": snap(line["start"], offset, bar_sec),
            "start": round(line["start"], 2),
            "end": round(line["end"], 2),
            "confidence": "forced_aligned",
        })
    return out


def to_srt(lines):
    def stamp(t):
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")

    blocks = []
    for i, l in enumerate(lines, 1):
        blocks.append(f"{i}\n{stamp(l['start'])} --> {stamp(l['end'])}\n{l['text']}\n")
    return "\n".join(blocks)


def attach_to_shots(lines, shots_path):
    """Fill each shot's lyric_lines with the ids of lines overlapping it."""
    book = json.loads(shots_path.read_text(encoding="utf-8"))
    for shot in book["shots"]:
        shot["lyric_lines"] = [
            l["id"] for l in lines
            if l["start"] < shot["end"] and l["end"] > shot["start"]
        ]
    shots_path.write_text(
        json.dumps(book, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return book


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = ap.parse_args()

    beatmap = load("storyboard/beatmap.json")
    raw = LYRICS_SRT.resolve().read_text(encoding="utf-8")
    raw_lines = parse_srt(raw)
    if not raw_lines:
        sys.exit(f"no SRT blocks parsed from {LYRICS_SRT}")
    lines = assign(raw_lines, beatmap)

    if args.check:
        print(f"{len(lines)} lines, all forced_aligned — OK")
        return

    out_dir = ROOT / "lyrics"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "lyrics.json").write_text(
        json.dumps({
            "$comment": (
                "MEASURED timings — whisper large-v3 forced alignment against the "
                "actual vocal audio, read as-is from ../歌詞.srt. `section` and `bar` "
                "are computed against beatmap.json purely for readability; they do "
                "not affect start/end. Regenerate with scripts/align_lyrics.py."
            ),
            "source": "../歌詞.srt",
            "grid": {
                "bpm": beatmap["tempo"]["bpm"],
                "bar_sec": beatmap["tempo"]["bar_sec"],
                "first_beat_offset_sec": beatmap["tempo"]["first_beat_offset_sec"],
            },
            "lines": lines,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "lyrics.srt").write_text(to_srt(lines), encoding="utf-8")

    book = attach_to_shots(lines, ROOT / "storyboard" / "shots.json")
    covered = sum(1 for s in book["shots"] if s["lyric_lines"])

    print(f"aligned {len(lines)} lines -> lyrics/lyrics.json + lyrics.srt")
    print(f"forced-aligned: {len(lines)}/{len(lines)}")
    print(f"shots carrying lyrics: {covered}/{len(book['shots'])}")


if __name__ == "__main__":
    main()
