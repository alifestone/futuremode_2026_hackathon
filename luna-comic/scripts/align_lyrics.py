#!/usr/bin/env python3
"""Align 歌詞.txt to the measured bar grid in storyboard/beatmap.json.

歌詞.txt is one unbroken paragraph with no timecodes. This splits it into
singable lines, assigns each line to one of the 12 measured sections, and lays
the lines onto bar lines inside that section.

IMPORTANT — these timings are ESTIMATED, not measured. There is no vocal-onset
detection or forced alignment in this project, so unlike beatmap.json (which is
measured from the audio) the per-line times here are inferred from structure:
section assignment is by hand, and placement within a section is proportional to
line length. The six hard_cut_points from beatmap.json are the exception — lines
anchored to them are exact.

Writes:
    lyrics/lyrics.json   line ids, text, section, bar, start/end, confidence
    lyrics/lyrics.srt    same timings as subtitles, for the edit
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
LYRICS_TXT = ROOT / ".." / "歌詞.txt"

# Production markers that are not sung. Stripped before splitting.
MARKER_RE = re.compile(r"\[[^\]]*\]")

# Phrases that must survive as one line even though they contain split
# punctuation. The countdown and the two English hooks are single musical
# gestures; breaking them at every comma would produce unsingable fragments.
ATOMIC = [
    "3、2、1，Live AI！",
    "Li-Li-Live A-AI！",
    "Create it, make it, show me your world, world, w-w-w-world.",
    "Dream it, build it, let the future unfold, fold.",
    "CSF CCA Live AI。",
]

# Which section each lyric line belongs to, keyed by the line's index after
# splitting. Built by hand against the 12 measured sections in beatmap.json:
# the lyric's own structure (countdown -> verse -> pre-chorus -> chorus hook ->
# breakdown -> final chorus -> outro tag) maps onto them in order.
SECTION_PLAN = [
    ("Intro", 2),               # L01 訊息亮起… + L02 the 3、2、1 countdown
    ("Build / Pre-drop", 1),    # L03 Li-Li-Live A-AI! lands on the bass entry
    ("Verse 1A", 2),            # L04-L05 the blank-canvas image
    ("Verse 1B", 1),            # L06 from first prompt to last shot
    ("Pre-chorus", 1),          # L07 時間正在倒數 — the riser line
    ("Chorus 1", 2),            # L08 hook (anchored 45.77) + L09
    ("Chorus 1 ext.", 4),       # L10-L13 讓光影… + the English hooks
    ("Verse 2", 1),             # L14 3-2-1 tag
    ("Breakdown", 0),           # instrumental dropout — no vocal
    ("Final chorus", 3),        # L15 hook (anchored 93.32) + L16-L17
    ("Climax", 5),              # L18-L22 the Live AI call-and-response
    ("Outro", 1),               # L23 CSF CCA Live AI (anchored 132.90)
]

# Lines that must land exactly on a measured hard cut from beatmap.json.
# Keyed by (section, text prefix) — "CSF CCA Live AI" appears twice in the
# lyric, mid-song and as the closing tag, and only the closing one is anchored.
HARD_ANCHORS = {
    ("Chorus 1", "Live AI，現在就創造未來"): 45.77,
    ("Final chorus", "Live AI，現在就創造未來"): 93.32,
    ("Outro", "CSF CCA Live AI"): 132.90,
}


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def split_lines(raw):
    """Paragraph -> singable lines, keeping ATOMIC phrases intact."""
    text = MARKER_RE.sub("", raw).strip()

    # Protect atomic phrases behind placeholders so the splitter cannot cut them.
    holds = {}
    for i, phrase in enumerate(ATOMIC):
        if phrase in text:
            key = f"\x00{i}\x00"
            holds[key] = phrase
            text = text.replace(phrase, key)

    # Split on sentence-final punctuation, and also on either side of a held
    # phrase — a placeholder hides its own trailing punctuation from the
    # splitter, which would otherwise glue it to the neighbouring line.
    text = re.sub(r"(\x00\d+\x00)", r"\n\1\n", text)
    parts = re.split(r"(?<=[。！？])\s*|\n", text)

    lines = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        for key, phrase in holds.items():
            part = part.replace(key, phrase)
        lines.append(part)
    return lines


def snap(t, offset, bar_sec):
    """Snap a time to the nearest bar line, so every cue lands on the grid."""
    n = round((t - offset) / bar_sec)
    return round(offset + n * bar_sec, 2), n + 1


def anchor_for(section, text):
    for (sec_name, prefix), t in HARD_ANCHORS.items():
        if section == sec_name and text.startswith(prefix):
            return t
    return None


def assign(lines, beatmap):
    """Lay lines onto the bar grid, section by section."""
    sections = {s["name"]: s for s in beatmap["sections"]}
    offset = beatmap["tempo"]["first_beat_offset_sec"]
    bar_sec = beatmap["tempo"]["bar_sec"]

    planned = sum(n for _, n in SECTION_PLAN)
    if planned != len(lines):
        sys.exit(
            f"SECTION_PLAN covers {planned} lines but the lyrics split into "
            f"{len(lines)}. Adjust SECTION_PLAN so the counts match.\n"
            + "\n".join(f"  {i:2d}  {l}" for i, l in enumerate(lines))
        )

    out, cursor = [], 0
    for name, count in SECTION_PLAN:
        if not count:      # instrumental section — no vocal to place
            continue
        sec = sections[name]
        group = lines[cursor:cursor + count]
        cursor += count

        # Within a section, give each line a share of the span proportional to
        # its length — longer lines take longer to sing.
        weights = [len(l) for l in group]
        total = sum(weights) or 1
        span = sec["end"] - sec["start"]

        t = sec["start"]
        for i, (line, w) in enumerate(zip(group, weights)):
            forced = anchor_for(name, line)
            start = forced if forced is not None else t
            raw_end = sec["end"] if i == count - 1 else start + span * w / total

            # Anchored lines keep their measured time exactly — a hard cut like
            # the final transient at 132.90 is not on a bar line, and snapping
            # it would pull the cue off the hit it exists to land on.
            if forced is not None:
                start_snapped = forced
                bar = snap(forced, offset, bar_sec)[1]
            else:
                start_snapped, bar = snap(start, offset, bar_sec)
            end_snapped, _ = snap(raw_end, offset, bar_sec)
            if end_snapped <= start_snapped:          # never collapse a cue
                end_snapped = round(start_snapped + bar_sec, 2)

            out.append({
                "id": f"L{len(out) + 1:02d}",
                "text": line,
                "section": name,
                "bar": bar,
                "start": start_snapped,
                "end": end_snapped,
                "confidence": "anchored" if forced is not None else "estimated",
                "anchor": "hard_cut" if forced is not None else None,
            })
            t = end_snapped
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
    raw = LYRICS_TXT.resolve().read_text(encoding="utf-8")
    lines = assign(split_lines(raw), beatmap)

    # The three hard anchors are the only load-bearing timings here; if one
    # drifted, the section plan is wrong and everything downstream is too.
    for line in lines:
        if line["anchor"] == "hard_cut":
            expected = anchor_for(line["section"], line["text"])
            if abs(line["start"] - expected) > 0.01:
                sys.exit(f"{line['id']} should anchor at {expected}, got {line['start']}")

    if args.check:
        print(f"{len(lines)} lines, {sum(1 for l in lines if l['anchor'])} anchored — OK")
        return

    out_dir = ROOT / "lyrics"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "lyrics.json").write_text(
        json.dumps({
            "$comment": (
                "ESTIMATED timings, not measured. Section assignment is by hand "
                "against beatmap.json's 12 measured sections; placement inside a "
                "section is proportional to line length. Only lines with "
                "anchor=hard_cut are exact. Regenerate with scripts/align_lyrics.py."
            ),
            "source": "../歌詞.txt",
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
    print(f"anchored to hard cuts: {sum(1 for l in lines if l['anchor'])}")
    print(f"shots carrying lyrics: {covered}/{len(book['shots'])}")


if __name__ == "__main__":
    main()
