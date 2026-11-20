"""Tests for reference-clip silence. Spoken filler is never injected."""

from __future__ import annotations

import wave
from pathlib import Path

from reference_pad import append_wav_silence, line_for_model, prepare_reference


def test_trailing_silence_is_about_point_eight_seconds(tmp_path: Path) -> None:
    """The pad that fixed dropped first words is silence after the clip."""
    source = tmp_path / "ref.wav"
    _write_tone(source, seconds=0.2)
    destination = tmp_path / "ref.padded.wav"
    append_wav_silence(source, destination, 0.8)
    with wave.open(str(source), "rb") as original, wave.open(str(destination), "rb") as padded:
        extra = padded.getnframes() - original.getnframes()
        assert extra == round(0.8 * original.getframerate())
        width = padded.getsampwidth()
        padded.setpos(original.getnframes())
        tail = padded.readframes(extra)
    assert tail == b"\x00" * (extra * width)
    reused = prepare_reference(source, seconds=0.8)
    assert reused == destination
    assert reused.stat().st_size == destination.stat().st_size


def test_lead_in_word_is_only_the_fallback() -> None:
    """A missing pad does not inject Hmm. Only an explicit lead-in prefixes."""
    assert line_for_model("You dig a hole.", reference_padded=True, lead_in=None) == "You dig a hole."
    assert line_for_model("You dig a hole.", reference_padded=False, lead_in=None) == "You dig a hole."
    assert line_for_model("You dig a hole.", reference_padded=True, lead_in="") == "You dig a hole."
    assert line_for_model("You dig a hole.", reference_padded=True, lead_in="Okay.") == "Okay. You dig a hole."


def test_missing_reference_padded_does_not_inject_hmm() -> None:
    """An already-padded clip, or a direct synthesize_line call, never says Hmm."""
    record: dict[str, object] = {}
    spoken = line_for_model(
        "So you add a pipe.",
        reference_padded=bool(record.get("_reference_padded")),
        lead_in=None,
    )
    assert spoken == "So you add a pipe."
    assert "Hmm" not in spoken


def _write_tone(path: Path, *, seconds: float) -> None:
    """Write a short PCM WAV.

    :param path: Destination.
    :param seconds: Duration.
    """
    rate = 16000
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x10\x00" * frames)
