"""Normalize narration and music loudness before HyperFrames muxes them.

Speech is brought to -16 LUFS and the music bed to -24 LUFS. The duck lane
still dips the bed under each line. The pass is the measured ffmpeg
``loudnorm`` filter, not the single-pass guess.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


class LoudnessError(RuntimeError):
    """ffmpeg could not measure or normalize a file."""


SPEECH_LUFS = -16.0
MUSIC_LUFS = -24.0
TRUE_PEAK = -1.5
LOUDNESS_RANGE = 11.0
_MEASURED = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")


def loudnorm_filter(
    stats: dict[str, str],
    *,
    target_i: float = SPEECH_LUFS,
    target_tp: float = TRUE_PEAK,
    target_lra: float = LOUDNESS_RANGE,
) -> str:
    """Build the second-pass ``loudnorm`` filter from a measurement.

    :param stats: Keys from ffmpeg's ``print_format=json`` block.
    :param target_i: Integrated loudness in LUFS.
    :param target_tp: True peak in dBTP.
    :param target_lra: Loudness range.
    :returns: An ``-af`` filter string. Linear mode, so a short clip is not
        dynamically recompressed.
    :raises LoudnessError: A measurement field is missing.
    """
    missing = [key for key in _MEASURED if key not in stats]
    if missing:
        raise LoudnessError(f"loudnorm measurement is missing: {', '.join(missing)}.")
    return (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
        f":measured_I={stats['input_i']}:measured_TP={stats['input_tp']}"
        f":measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}"
        f":offset={stats['target_offset']}:linear=true"
    )


def parse_loudnorm_json(stderr: str) -> dict[str, str]:
    """Pull the loudnorm JSON object out of ffmpeg's stderr.

    :param stderr: Full ffmpeg stderr from a measure pass.
    :returns: The measurement fields as strings.
    :raises LoudnessError: The JSON block is missing or incomplete.
    """
    start = stderr.rfind("{")
    end = stderr.rfind("}")
    if start < 0 or end < start:
        raise LoudnessError("ffmpeg loudnorm did not print a measurement.")
    try:
        payload = json.loads(stderr[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LoudnessError("ffmpeg loudnorm measurement was not JSON.") from exc
    if not isinstance(payload, dict):
        raise LoudnessError("ffmpeg loudnorm measurement was not an object.")
    missing = [key for key in _MEASURED if key not in payload]
    if missing:
        raise LoudnessError(f"loudnorm measurement is missing: {', '.join(missing)}.")
    return {key: str(payload[key]) for key in _MEASURED}


def normalize_wav(
    source: Path,
    destination: Path | None = None,
    *,
    target_i: float = SPEECH_LUFS,
    target_tp: float = TRUE_PEAK,
    target_lra: float = LOUDNESS_RANGE,
) -> Path:
    """Two-pass loudnorm. The source is replaced when ``destination`` is omitted.

    :param source: Audio ffmpeg can read.
    :param destination: Output WAV. Defaults to ``source``.
    :param target_i: Integrated loudness in LUFS.
    :param target_tp: True peak ceiling.
    :param target_lra: Loudness range.
    :returns: The file that was written.
    :raises LoudnessError: ffmpeg is missing or either pass fails.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise LoudnessError("ffmpeg is not on PATH. Install ffmpeg before the mux.")
    if not source.is_file():
        raise LoudnessError(f"Audio file not found: {source}")
    stats = parse_loudnorm_json(_measure(ffmpeg, source, target_i, target_tp, target_lra))
    audio_filter = loudnorm_filter(
        stats, target_i=target_i, target_tp=target_tp, target_lra=target_lra
    )
    target = destination or source
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="explainer-loudness-") as tmp:
        staged = Path(tmp) / "out.wav"
        _apply(ffmpeg, source, staged, audio_filter)
        target.write_bytes(staged.read_bytes())
    return target


def _measure(
    ffmpeg: str,
    source: Path,
    target_i: float,
    target_tp: float,
    target_lra: float,
) -> str:
    """Run the measure pass and return stderr.

    :param ffmpeg: ffmpeg binary.
    :param source: Input audio.
    :param target_i: Integrated loudness target, passed so the offset matches.
    :param target_tp: True peak target.
    :param target_lra: Loudness range target.
    :returns: ffmpeg stderr.
    :raises LoudnessError: The measure pass fails.
    """
    completed = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(source),
            "-af",
            f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise LoudnessError(f"ffmpeg could not measure {source}.")
    return completed.stderr


def _apply(ffmpeg: str, source: Path, destination: Path, audio_filter: str) -> None:
    """Run the apply pass.

    :param ffmpeg: ffmpeg binary.
    :param source: Input audio.
    :param destination: Output WAV.
    :param audio_filter: Filter from :func:`loudnorm_filter`.
    :raises LoudnessError: The apply pass fails.
    """
    completed = subprocess.run(
        [ffmpeg, "-y", "-hide_banner", "-i", str(source), "-af", audio_filter, str(destination)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not destination.is_file():
        raise LoudnessError(f"ffmpeg could not normalize {source}.")
