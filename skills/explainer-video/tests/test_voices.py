"""Tests for ~/.voice/ clone-clip resolution. No TTS model is loaded."""

from __future__ import annotations

from pathlib import Path

import pytest
from synthesize_beat import _require_reference
from voices import (
    DEFAULT_REFERENCE_NAME,
    load_registry,
    missing_reference_message,
    resolve_reference,
    specified_reference_path,
    voice_home,
)

SKILL = Path(__file__).resolve().parents[1]


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``Path.home()`` and ``~`` at a temp directory."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    (tmp_path / ".voice").mkdir()
    return tmp_path


def test_voice_home_is_dot_voice_under_home(fake_home: Path) -> None:
    """The canonical directory is Path.home() / '.voice'."""
    assert voice_home() == fake_home / ".voice"


def test_relative_name_resolves_under_voice_home(fake_home: Path) -> None:
    """A registry name such as reference.m4a is looked up in ~/.voice/."""
    clip = fake_home / ".voice" / "reference.m4a"
    clip.write_bytes(b"clip")
    assert resolve_reference("reference.m4a") == clip
    assert specified_reference_path("reference.m4a") == clip


def test_tilde_path_under_dot_voice_resolves(fake_home: Path) -> None:
    """~/.voice/reference.m4a expands through the home directory."""
    clip = fake_home / ".voice" / "reference.m4a"
    clip.write_bytes(b"clip")
    assert resolve_reference("~/.voice/reference.m4a") == clip


def test_lookup_order_is_m4a_then_wav_then_mp3(fake_home: Path) -> None:
    """When the named file is missing, .m4a wins over .wav, then .mp3."""
    voice_dir = fake_home / ".voice"
    wav = voice_dir / "reference.wav"
    mp3 = voice_dir / "reference.mp3"
    wav.write_bytes(b"wav")
    mp3.write_bytes(b"mp3")
    assert resolve_reference("reference.m4a") == wav
    m4a = voice_dir / "reference.m4a"
    m4a.write_bytes(b"m4a")
    assert resolve_reference("reference.m4a") == m4a
    m4a.unlink()
    wav.unlink()
    assert resolve_reference("") == mp3


def test_absolute_existing_path_is_used(fake_home: Path) -> None:
    """A padded WAV or other absolute clip is used as-is when it exists."""
    clip = fake_home / "outside.wav"
    clip.write_bytes(b"clip")
    assert resolve_reference(str(clip)) == clip


def test_custom_stem_does_not_fall_back_to_reference(fake_home: Path) -> None:
    """A missing custom name does not silently pick reference.m4a."""
    (fake_home / ".voice" / "reference.m4a").write_bytes(b"default")
    assert resolve_reference("custom.m4a") is None


def test_require_reference_returns_existing_clip(fake_home: Path) -> None:
    """Synthesis proceeds when ~/.voice/reference.m4a is present."""
    clip = fake_home / ".voice" / "reference.m4a"
    clip.write_bytes(b"clip")
    assert _require_reference({"reference": "reference.m4a"}) == clip


def test_empty_reference_uses_default_name(fake_home: Path) -> None:
    """An empty field still looks for ~/.voice/reference.m4a."""
    assert specified_reference_path("") == fake_home / ".voice" / DEFAULT_REFERENCE_NAME
    assert specified_reference_path(None) == fake_home / ".voice" / DEFAULT_REFERENCE_NAME
    assert resolve_reference("") is None


def test_missing_reference_message_points_at_dot_voice(fake_home: Path) -> None:
    """The error names ~/.voice/ and does not mention a personal clip path."""
    message = missing_reference_message("reference.m4a")
    assert "Error: voice reference clip is missing" in message
    assert "~/.voice/" in message
    assert "reference.m4a" in message
    assert "reference.wav" in message
    assert "reference.mp3" in message
    assert str(fake_home / ".voice" / "reference.m4a") in message


def test_require_reference_exits_when_clip_is_missing(fake_home: Path) -> None:
    """Synthesis does not invent a clip. It exits and points at ~/.voice/."""
    with pytest.raises(SystemExit, match=r"~/\.voice/") as caught:
        _require_reference({"reference": "reference.m4a"})
    assert caught.value.code == missing_reference_message("reference.m4a")


def test_shipped_registry_uses_generic_reference() -> None:
    """voices.yaml must not hard-code a personal clip path."""
    path = SKILL / "voices.yaml"
    registry = load_registry(path)
    for record in registry["voices"].values():
        raw = str(record.get("reference") or "")
        if not raw:
            continue
        name = Path(raw).name.lower()
        assert "eric" not in name
        expanded = Path(raw).expanduser()
        if expanded.is_absolute() or raw.startswith("~"):
            assert raw.startswith("~/.voice/") or ".voice" in Path(raw).parts
        else:
            assert Path(raw).name.startswith("reference.")
