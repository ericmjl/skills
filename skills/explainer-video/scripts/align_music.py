#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12", "librosa>=0.10", "numpy>=1.26", "soundfile>=0.12", "loguru>=0.7"]
# ///
"""Measure speech WAVs, detect music beats, and write timeline.json.

Speech is not stretched. Gaps grow, up to --max-gap, so the next clip can
start on a beat. Pass --beats-json to skip librosa and reuse a beat list.

    uv run skills/explainer-video/scripts/align_music.py PROJECT
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loudness import MUSIC_LUFS, LoudnessError, normalize_wav
from timeline import (
    ScriptError,
    beat_wav_name,
    build_timeline,
    parse_script,
    wav_duration,
)

app = typer.Typer(add_completion=False, no_args_is_help=True)
logger.remove()
logger.add(sys.stderr, format="{message}")


@app.command()
def align(
    project: Path = typer.Argument(..., help="Explainer project directory."),
    music: Path = typer.Option(Path("audio/music.wav"), "--music", help="Music file, relative to the project unless absolute."),
    beats_json: Path | None = typer.Option(None, "--beats-json", help="Skip librosa. JSON with a beats array of seconds."),
    aspect: str = typer.Option("9:16", "--aspect", help="9:16 or 16:9."),
    min_gap: float = typer.Option(0.08, "--min-gap"),
    max_gap: float = typer.Option(0.55, "--max-gap"),
    lead_in: float = typer.Option(0.15, "--lead-in"),
) -> None:
    """Write ``timeline.json`` in the project."""
    script_path = project / "script.md"
    if not script_path.is_file():
        logger.error("Error: missing {}", script_path)
        raise typer.Exit(code=2)
    try:
        script = parse_script(script_path.read_text(encoding="utf-8"))
    except ScriptError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    durations: list[float] = []
    for beat in script.beats:
        wav = project / beat_wav_name(beat.index)
        try:
            durations.append(wav_duration(wav))
        except ScriptError as exc:
            logger.error("Error: {}", exc)
            raise typer.Exit(code=2) from exc
    music_path = music if music.is_absolute() else project / music
    if not music_path.is_file():
        logger.error("Error: music not found: {}", music_path)
        raise typer.Exit(code=2)
    if not music_path.stem.endswith(".norm"):
        normalized = music_path.with_name(music_path.stem + ".norm.wav")
        try:
            normalize_wav(music_path, normalized, target_i=MUSIC_LUFS)
        except LoudnessError as exc:
            logger.error("Error: {}", exc)
            raise typer.Exit(code=2) from exc
        logger.info("Normalized music to {} LUFS: {}", MUSIC_LUFS, normalized.name)
        music_path = normalized
    if beats_json is not None:
        bpm, beat_times = _beats_from_file(beats_json)
        music_duration = _duration_via_soundfile(music_path)
    else:
        bpm, beat_times, music_duration = detect_beats(music_path)
    relative_music = str(music_path.relative_to(project)) if music_path.is_relative_to(project) else str(music_path)
    try:
        document = build_timeline(
            script,
            durations,
            beat_times,
            music_path=relative_music,
            music_duration=music_duration,
            bpm=bpm,
            aspect=aspect,
            min_gap=min_gap,
            max_gap=max_gap,
            lead_in=lead_in,
        )
    except ScriptError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    if music_duration + 0.05 < float(document["duration"]):
        logger.warning(
            "Music is {:.1f}s and the timeline is {:.1f}s. "
            "Use a longer track. This script does not loop the bed.",
            music_duration,
            float(document["duration"]),
        )
    destination = project / "timeline.json"
    destination.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    typer.echo(
        f"Wrote {destination} ({document['duration']}s, bpm {bpm}, {len(beat_times)} beats)."
    )


def detect_beats(path: Path) -> tuple[float, list[float], float]:
    """Detect beat times with librosa.

    :param path: Music file librosa can open. WAV is the reliable input.
    :returns: BPM, beat times in seconds, and duration in seconds.
    """
    import librosa

    samples, rate = librosa.load(path, sr=22050, mono=True)
    if samples.size == 0:
        raise SystemExit(f"Error: music file is empty: {path}")
    tempo, frames = librosa.beat.beat_track(y=samples, sr=rate)
    bpm = float(tempo) if getattr(tempo, "ndim", 0) == 0 else float(tempo.reshape(-1)[0])
    times = [float(item) for item in librosa.frames_to_time(frames, sr=rate)]
    duration = float(len(samples) / rate)
    return round(bpm, 1), times, duration


def _beats_from_file(path: Path) -> tuple[float, list[float]]:
    """Read a precomputed beat list.

    :param path: JSON object with ``beats`` and optional ``bpm``.
    :returns: BPM and beat times.
    """
    if not path.is_file():
        raise SystemExit(f"Error: beats file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("beats"), list):
        raise SystemExit("Error: beats JSON needs an object with a beats array of seconds.")
    beats = [float(item) for item in raw["beats"]]
    bpm = float(raw.get("bpm", 0.0))
    return bpm, beats


def _duration_via_soundfile(path: Path) -> float:
    """Duration of a file soundfile can open.

    :param path: Audio file.
    :returns: Seconds.
    """
    import soundfile as sf

    info = sf.info(str(path))
    return float(info.duration)


if __name__ == "__main__":
    app()
