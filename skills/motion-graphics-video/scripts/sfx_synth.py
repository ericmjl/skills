#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Synthesize motion graphics sound effects as WAV files. Math, not downloads.

Deterministic: same type, duration, and seed always produce the same file.

Types:
    whoosh   filtered noise sweep that swells then releases (motivates a cut)
    impact   pitch-dropping sine + noise burst, fast decay (lands a reveal)
    riser    accelerating pitch + noise swell ending in a cut (pre-drop)
    sparkle  scattered high-frequency pings (magic, assembly, success)
    tick     tiny click for beat accents and UI moments

Usage:
    uv run sfx_synth.py whoosh  -o audio/sfx/whoosh_01.wav
    uv run sfx_synth.py impact  -d 1.2 -o audio/sfx/impact_01.wav
"""

import argparse
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
PEAK = 10 ** (-3 / 20)  # normalize to -3 dBFS


def _env_ad(n: int, attack: float, release: float) -> np.ndarray:
    """Attack-decay envelope over n samples; attack/release are fractions of n."""
    t = np.linspace(0.0, 1.0, n)
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    r = np.clip((1 - t) / max(release, 1e-6), 0, 1)
    return np.minimum(a, r) ** 1.5


def _lowpass_noise(n: int, cutoffs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One-pole lowpass over noise with a per-sample cutoff curve (0..1)."""
    noise = rng.standard_normal(n)
    out = np.empty(n)
    state = 0.0
    for i in range(n):
        alpha = float(np.clip(cutoffs[i], 0.001, 0.95))
        state += alpha * (noise[i] - state)
        out[i] = state
    return out


def make_whoosh(dur: float, rng: np.random.Generator) -> np.ndarray:
    n = int(dur * SR)
    t = np.linspace(0.0, 1.0, n)
    cutoff = 0.08 + 0.6 * np.sin(np.pi * np.clip(t * 0.85, 0, 1)) ** 2
    body = _lowpass_noise(n, cutoff, rng)
    swell = np.sin(np.pi * t) ** 2.5  # slow swell, quick release
    return body * swell


def make_impact(dur: float, rng: np.random.Generator) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    # Sub thump: pitch drops 130 -> 38 Hz within the first 120 ms.
    f0, f1, drop_t = 130.0, 38.0, 0.12
    freq = np.where(t < drop_t, f0 * (f1 / f0) ** (t / drop_t), f1)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    thump = np.sin(phase) * np.exp(-t / (dur * 0.22))
    # Transient noise burst in the first 40 ms.
    burst_n = int(0.04 * SR)
    burst = np.zeros(n)
    burst[:burst_n] = rng.standard_normal(burst_n) * np.exp(-np.arange(burst_n) / (0.008 * SR))
    return thump * 0.9 + burst * 0.5


def make_riser(dur: float, rng: np.random.Generator) -> np.ndarray:
    n = int(dur * SR)
    t = np.linspace(0.0, 1.0, n)
    f0, f1 = 160.0, 1400.0
    freq = f0 * (f1 / f0) ** (t ** 1.6)  # accelerating exponential sweep
    phase = 2 * np.pi * np.cumsum(freq) * (dur / n)
    tone = np.sin(phase) * 0.6
    cutoff = 0.02 + 0.7 * t ** 2
    noise = _lowpass_noise(n, cutoff, rng) * (t ** 2) * 0.5
    body = tone + noise
    tail = int(0.03 * SR)  # hard cut at the end (the drop follows)
    body[-tail:] = 0.0
    return body


def make_sparkle(dur: float, rng: np.random.Generator) -> np.ndarray:
    n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(int(rng.integers(8, 15))):
        start = int(rng.uniform(0, max(dur - 0.15, 0.01)) * SR)
        ping_n = int(0.09 * SR)
        ping_n = min(ping_n, n - start)
        if ping_n <= 0:
            continue
        f = rng.uniform(2200, 7200)
        t = np.arange(ping_n) / SR
        ping = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.025)
        out[start:start + ping_n] += ping * rng.uniform(0.5, 1.0)
    return out


def make_tick(dur: float, rng: np.random.Generator) -> np.ndarray:
    n = max(int(dur * SR), int(0.02 * SR))
    n = min(n, int(0.1 * SR))
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.006)
    click = rng.standard_normal(n) * np.exp(-t / 0.002) * 0.3
    return body + click


MAKERS = {
    "whoosh": make_whoosh,
    "impact": make_impact,
    "riser": make_riser,
    "sparkle": make_sparkle,
    "tick": make_tick,
}
DEFAULT_DUR = {"whoosh": 0.6, "impact": 1.2, "riser": 2.0, "sparkle": 1.0, "tick": 0.1}


def write_wav(path: Path, samples: np.ndarray) -> None:
    peak = np.abs(samples).max()
    if peak > 0:
        samples = samples / peak * PEAK
    pcm = (samples * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize a sound effect WAV")
    parser.add_argument("type", choices=sorted(MAKERS), help="effect type")
    parser.add_argument("-d", "--duration", type=float, default=None, help="seconds")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output wav path")
    parser.add_argument("--seed", type=int, default=42, help="seed for determinism")
    args = parser.parse_args()

    dur = args.duration if args.duration is not None else DEFAULT_DUR[args.type]
    if not 0.02 <= dur <= 10:
        parser.error("duration must be between 0.02 and 10 seconds")

    rng = np.random.default_rng(args.seed)
    samples = MAKERS[args.type](dur, rng)
    write_wav(args.output, samples)
    print(f"Wrote {args.output} ({args.type}, {dur:.2f}s, seed {args.seed}, {SR}Hz mono)")


if __name__ == "__main__":
    sys.exit(main())
