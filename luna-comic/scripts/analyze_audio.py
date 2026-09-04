#!/usr/bin/env python3
"""Measure the track's tempo, bar grid, and section boundaries.

This is what produced storyboard/beatmap.json. It decodes the MP3 with the
ffmpeg binary bundled in imageio-ffmpeg (no system ffmpeg needed), then runs
STFT-based analysis:

  * tempo      -- onset-flux comb search over 95-125 BPM
  * boundaries -- checkerboard-kernel novelty over a self-similarity matrix
  * profile    -- per-section band energy, which is what tells a drop from a
                  breakdown (bass ratio) and a riser from a pad (air ratio)

Usage:
    pip install numpy imageio-ffmpeg
    python scripts/analyze_audio.py            # analyse the default track
    python scripts/analyze_audio.py other.mp3  # analyse a different file

Re-run this only if the track is ever re-exported; the shot grid in
storyboard/shots.json is keyed to the numbers it prints. A pure rename of the
same audio does not need a re-run — pass the new path instead.
"""
import argparse
import pathlib
import subprocess
import sys
import tempfile

import numpy as np

SR, HOP, NFFT = 22050, 512, 1024
ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_TRACK = ROOT / ".." / "歌曲.mp3"


def decode(path):
    """MP3 -> mono float32 PCM at SR, via the bundled ffmpeg."""
    import imageio_ffmpeg

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as td:
        raw = pathlib.Path(td) / "audio.pcm"
        subprocess.run(
            [ff, "-hide_banner", "-loglevel", "error", "-i", str(path),
             "-ac", "1", "-ar", str(SR), "-f", "s16le", "-acodec", "pcm_s16le",
             str(raw), "-y"],
            check=True,
        )
        return np.fromfile(raw, dtype=np.int16).astype(np.float32) / 32768.0


def stft(x):
    w = np.hanning(NFFT).astype(np.float32)
    n = 1 + (len(x) - NFFT) // HOP
    S = np.empty((n, NFFT // 2 + 1), np.float32)
    for i in range(n):
        S[i] = np.abs(np.fft.rfft(x[i * HOP:i * HOP + NFFT] * w))
    return S


def tempo_grid(S):
    """Comb-filter search: find the BPM+phase whose grid best hits onsets."""
    fps = SR / HOP
    flux = np.maximum(0, np.diff(np.log1p(S * 20), axis=0)).sum(1)
    flux = (flux - flux.mean()) / flux.std()
    best = None
    for bpm in np.arange(95, 125, 0.05):
        period = 60 / bpm * fps
        for phase in np.arange(0, period):
            pos = np.arange(phase, len(flux), period).astype(int)
            score = flux[pos[pos < len(flux)]].mean()
            if best is None or score > best[2]:
                best = (bpm, phase / fps, score)
    return best


def boundaries(S, kernel_sec=8.0):
    """Checkerboard novelty over a cosine self-similarity matrix."""
    fps = SR / HOP
    freqs = np.fft.rfftfreq(NFFT, 1 / SR)
    edges = np.logspace(np.log10(60), np.log10(10000), 21)
    cols = []
    for i in range(20):
        m = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if not m.any():
            m = np.zeros_like(freqs, bool)
            m[np.argmin(abs(freqs - (edges[i] + edges[i + 1]) / 2))] = True
        cols.append(np.log1p(S[:, m].mean(1) * 50))
    F = np.stack(cols, 1)

    win = int(0.5 * fps)
    c = np.cumsum(np.vstack([np.zeros((1, 20)), F]), 0)
    n = len(F)
    F = np.stack([(c[min(n, i + win + 1)] - c[max(0, i - win)])
                  / (min(n, i + win + 1) - max(0, i - win)) for i in range(n)])
    F = (F - F.mean(0)) / (F.std(0) + 1e-9)

    step = max(1, int(0.25 * fps))
    idx = np.arange(0, n, step)
    G = F[idx]
    G /= np.linalg.norm(G, axis=1, keepdims=True) + 1e-9
    SSM = G @ G.T

    L = int(kernel_sec / 0.25)
    k = np.zeros((2 * L, 2 * L))
    k[:L, :L] = k[L:, L:] = 1
    k[:L, L:] = k[L:, :L] = -1
    k *= np.outer(np.hanning(2 * L), np.hanning(2 * L))

    nov = np.zeros(len(idx))
    for i in range(L, len(idx) - L):
        nov[i] = (SSM[i - L:i + L, i - L:i + L] * k).sum()
    nov = np.maximum(nov, 0)
    nov /= nov.max() + 1e-9

    t = idx * HOP / SR
    peaks, guard = [], int(3 / 0.25)
    for i in range(1, len(nov) - 1):
        if nov[i] > 0.15 and nov[i] == nov[max(0, i - guard):i + guard + 1].max():
            peaks.append((t[i], nov[i]))
    merged = []
    for p in peaks:
        if not merged or p[0] - merged[-1][0] > 5:
            merged.append(p)
        elif p[1] > merged[-1][1]:
            merged[-1] = p
    return merged


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("track", nargs="?", default=str(DEFAULT_TRACK),
                    help="path to the track (default: ../歌曲.mp3)")
    args = ap.parse_args()

    track = pathlib.Path(args.track).resolve()
    if not track.exists():
        sys.exit(f"track not found: {track}")
    x = decode(track)
    dur = len(x) / SR
    print(f"duration     {dur:.2f}s  ({int(dur // 60)}:{dur % 60:05.2f})")

    S = stft(x)
    bpm, offset, score = tempo_grid(S)
    bar = 4 * 60 / bpm
    print(f"tempo        {bpm:.2f} BPM (score {score:.3f})")
    print(f"beat / bar   {60 / bpm:.4f}s / {bar:.4f}s")
    print(f"first beat   {offset:.3f}s")
    print(f"total bars   {int((dur - offset) / bar)}")

    print("\nsection boundaries (novelty peaks):")
    for t, v in boundaries(S):
        n = round((t - offset) / bar)
        snapped = offset + n * bar
        print(f"  {int(t // 60)}:{t % 60:05.2f}  strength {v:.2f}"
              f"   -> bar {n + 1} @ {int(snapped // 60)}:{snapped % 60:05.2f}")


if __name__ == "__main__":
    main()
