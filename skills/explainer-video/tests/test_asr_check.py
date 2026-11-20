"""Tests for the per-beat Whisper check. No model is loaded."""

from __future__ import annotations

import json
from pathlib import Path

from asr_check import record_voice_log, review_takes, word_error_rate


def test_word_error_rate_ignores_case_and_sound_codes() -> None:
    """One substituted word in four is a quarter. A sound code is not a word."""
    assert word_error_rate("You dig a hole.", "you dig a hole") == 0
    assert word_error_rate("You dig a hole.", "you dig the hole") == 0.25
    assert word_error_rate("[IH1] costs two", "costs two") == 0


def test_retry_keeps_the_lowest_error_and_logs_it(tmp_path: Path) -> None:
    """A bad first take is replaced when a later take matches."""
    wav = tmp_path / "00.wav"
    transcripts = iter(["tim mate joined", "your teammate joined"])

    def synthesize() -> None:
        wav.write_bytes(f"take-{wav.exists()}".encode())

    def transcribe(_path: Path) -> str:
        return next(transcripts)

    record = review_takes(
        wav,
        "your teammate joined",
        synthesize=synthesize,
        transcribe=transcribe,
        attempts=3,
        threshold=0.25,
    )
    assert record["accepted"] is True
    assert record["wer"] == 0
    assert len(record["attempts"]) == 2
    assert record["attempts"][0]["decision"] == "retry"
    log = tmp_path / "voice_log.json"
    record_voice_log(log, 0, record)
    record_voice_log(log, 0, record)
    saved = json.loads(log.read_text(encoding="utf-8"))
    assert [row["index"] for row in saved["beats"]] == [0]
    assert saved["beats"][0]["accepted"] is True
