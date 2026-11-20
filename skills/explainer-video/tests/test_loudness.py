"""Tests for the loudness step that runs before HyperFrames muxes audio."""

from __future__ import annotations

import math
import shutil
import struct
import wave
from pathlib import Path

import pytest
from loudness import loudnorm_filter, normalize_wav, parse_loudnorm_json


def test_loudnorm_filter_uses_the_measurement() -> None:
    """The second pass quotes the measured values and stays linear."""
    stats = {
        "input_i": "-24.5",
        "input_tp": "-4.0",
        "input_lra": "3.0",
        "input_thresh": "-34.5",
        "target_offset": "0.5",
    }
    audio_filter = loudnorm_filter(stats, target_i=-16)
    assert "measured_I=-24.5" in audio_filter
    assert "offset=0.5" in audio_filter
    assert audio_filter.endswith("linear=true")
    stderr = 'noise\n{\n\t"input_i" : "-24.5",\n\t"input_tp" : "-4.0",\n\t"input_lra" : "3.0",\n\t"input_thresh" : "-34.5",\n\t"target_offset" : "0.5"\n}\n'
    assert parse_loudnorm_json(stderr)["input_i"] == "-24.5"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_normalize_wav_raises_a_quiet_tone(tmp_path: Path) -> None:
    """A quiet tone is brought up. This is the step before the mux."""
    source = tmp_path / "quiet.wav"
    _write_sine(source, amplitude=0.02)
    normalize_wav(source, target_i=-16)
    measured = _integrated(source)
    assert measured == pytest.approx(-16, abs=2.5)


def _write_sine(path: Path, *, amplitude: float) -> None:
    """Write one second of a sine.

    :param path: Destination WAV.
    :param amplitude: Peak amplitude from 0 to 1.
    """
    rate = 16000
    frames = rate
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        samples = [
            int(amplitude * 32767 * math.sin(2 * math.pi * 440 * n / rate)) for n in range(frames)
        ]
        handle.writeframes(struct.pack("<" + "h" * frames, *samples))


def _integrated(path: Path) -> float:
    """Measure integrated loudness with ffmpeg.

    :param path: WAV to measure.
    :returns: Integrated LUFS.
    """
    import subprocess

    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            "loudnorm=print_format=json",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return float(parse_loudnorm_json(completed.stderr)["input_i"])
