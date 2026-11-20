"""Tests for the CC BY music credit written at render time."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from build_composition import apply_music_credit, attribution_line
from composition import CompositionError


def test_cc_by_writes_credits_and_other_licenses_do_not(tmp_path: Path) -> None:
    """A CC BY track gets one attribution line. CC0 removes a stale file."""
    audio = tmp_path / "audio"
    audio.mkdir()
    credit = {
        "title": "Glass Beats",
        "author": "Ada",
        "source": "https://example.com/glass",
        "license": "CC BY 4.0",
    }
    (audio / "credit.json").write_text(json.dumps(credit), encoding="utf-8")
    written = apply_music_credit(tmp_path)
    assert written == tmp_path / "credits.txt"
    text = written.read_text(encoding="utf-8")
    assert text == '"Glass Beats" by Ada. License: CC BY 4.0. Source: https://example.com/glass.\n'
    assert attribution_line({"license": "CC-BY-SA 4.0", "title": "T", "author": "A"}) == (
        '"T" by A. License: CC-BY-SA 4.0.'
    )
    assert attribution_line({"license": "CC0", "title": "T", "author": "A"}) is None
    (audio / "credit.json").write_text(json.dumps({"license": "CC0", "title": "Free"}), encoding="utf-8")
    assert apply_music_credit(tmp_path) is None
    assert not (tmp_path / "credits.txt").exists()


def test_missing_credit_file_leaves_credits_alone(tmp_path: Path) -> None:
    """No sidecar means the render step does not invent an attribution."""
    existing = tmp_path / "credits.txt"
    existing.write_text("hand written\n", encoding="utf-8")
    assert apply_music_credit(tmp_path) is None
    assert existing.read_text(encoding="utf-8") == "hand written\n"


def test_credit_file_must_be_an_object(tmp_path: Path) -> None:
    """A list in credit.json is a mistake, not a silent skip."""
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "credit.json").write_text("[]", encoding="utf-8")
    with pytest.raises(CompositionError, match="object"):
        apply_music_credit(tmp_path)
