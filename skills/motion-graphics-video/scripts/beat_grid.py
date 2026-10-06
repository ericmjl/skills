#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Measure a music track's beat grid so scene cuts land on beats.

Reads a WAV/FLAC/MP3 (non-WAV inputs are converted via ffmpeg), detects
onsets with spectral flux, estimates BPM, and writes JSON:

    {"duration": s, "bpm": n, "onsets": [t, ...], "strong_beats": [t, ...]}

Usage:
    uv run beat_grid.py audio/track.wav -o docs/beats.json
"""

import argparse
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

TARGET_SR = 22050
FRAME_SIZE = 1024
HOP_SIZE = 512
MIN_ONSET_GAP_S = 0.12


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Load audio as mono float64 in [-1, 1] at TARGET_SR."""
    if path.suffix.lower() != ".wav":
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(path), "-ac", "1", "-ar", str(TARGET_SR), tmp.name],
            check=True,
        )
        path = Path(tmp.name)
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n_frames)
    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        raise SystemExit(f"Error: unsupported WAV sample width: {sampwidth * 8} bits")
    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)
    if sr != TARGET_SR:
        t_old = np.arange(len(data)) / sr
        t_new = np.arange(int(len(data) * TARGET_SR / sr)) / TARGET_SR
        data = np.interp(t_new, t_old, data)
    return data, TARGET_SR


def spectral_flux_onsets(samples: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (onset_times, onset_strengths) via half-wave rectified spectral flux."""
    n_frames = 1 + max(0, (len(samples) - FRAME_SIZE) // HOP_SIZE)
    if n_frames < 8:
        raise SystemExit("Error: audio too short to analyze")
    window = np.hanning(FRAME_SIZE)
    frames = np.lib.stride_tricks.sliding_window_view(samples, FRAME_SIZE)[::HOP_SIZE][:n_frames]
    mag = np.abs(np.fft.rfft(frames * window, axis=1))
    log_mag = np.log1p(10.0 * mag)
    flux = np.maximum(0.0, np.diff(log_mag, axis=0)).sum(axis=1)
    flux = np.concatenate([[0.0], flux])
    flux /= flux.max() if flux.max() > 0 else 1.0

    # Adaptive threshold: local mean over ~0.7s plus a global k * std margin.
    win = max(3, int(0.7 * sr / HOP_SIZE))
    kernel = np.ones(win) / win
    local_mean = np.convolve(flux, kernel, mode="same")
    threshold = local_mean + 0.6 * flux.std()

    candidates = np.where(flux > threshold)[0]
    onsets: list[int] = []
    min_gap = int(MIN_ONSET_GAP_S * sr / HOP_SIZE)
    for idx in candidates:
        if onsets and idx - onsets[-1] < min_gap:
            if flux[idx] > flux[onsets[-1]]:
                onsets[-1] = idx
            continue
        onsets.append(idx)
    times = np.array(onsets, dtype=np.float64) * HOP_SIZE / sr
    strengths = flux[onsets] if onsets else np.array([])
    return times, strengths


def estimate_bpm(onsets: np.ndarray) -> float:
    """Median inter-onset interval folded into a 70-180 BPM range."""
    if len(onsets) < 3:
        return 0.0
    intervals = np.diff(onsets)
    intervals = intervals[(intervals > 0.25) & (intervals < 1.2)]
    if len(intervals) == 0:
        return 0.0
    bpm = 60.0 / float(np.median(intervals))
    while bpm < 70:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return round(bpm, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure a beat grid from music")
    parser.add_argument("audio", type=Path, help="music file (wav preferred)")
    parser.add_argument("-o", "--output", type=Path, default=Path("docs/beats.json"))
    parser.add_argument("--n-strong", type=int, default=12, help="strong beats to keep")
    args = parser.parse_args()

    samples, sr = load_audio(args.audio)
    onsets, strengths = spectral_flux_onsets(samples, sr)
    bpm = estimate_bpm(onsets)
    duration = round(len(samples) / sr, 3)

    strong: list[float] = []
    if len(onsets):
        order = np.argsort(strengths)[::-1][: args.n_strong]
        strong = sorted(round(float(onsets[i]), 3) for i in order)

    result = {
        "source": str(args.audio),
        "duration": duration,
        "bpm": bpm,
        "n_onsets": len(onsets),
        "onsets": [round(float(t), 3) for t in onsets],
        "strong_beats": strong,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Beat grid written: {args.output}")
    print(f"  duration {duration}s, bpm {bpm}, {len(onsets)} onsets")


if __name__ == "__main__":
    sys.exit(main())
