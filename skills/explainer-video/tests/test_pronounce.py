"""CLI tests for the pronunciation tool. No TTS model is loaded."""

from __future__ import annotations

from pathlib import Path

from normalize import Lexicon, dump_lexicon
from pronounce import app
from typer.testing import CliRunner

SKILL = Path(__file__).resolve().parents[1]
RUNNER = CliRunner()


def test_add_apply_and_reject_duplicate(tmp_path: Path) -> None:
    """add writes a versioned file, apply prints the spoken form, duplicates fail."""
    path = tmp_path / "lexicon.json"
    dump_lexicon(Lexicon(version=1, updated="2026-11-20", entries=()), path)
    added = RUNNER.invoke(
        app,
        [
            "add",
            "pyjanitor",
            "--cmu",
            "[P] [AY1]",
            "--respelling",
            "pie janitor",
            "--lexicon",
            str(path),
            "--updated",
            "2026-11-20",
        ],
    )
    assert added.exit_code == 0, added.output
    applied = RUNNER.invoke(
        app,
        ["apply", "Use pyjanitor.", "--target", "cosyvoice3", "--lexicon", str(path)],
    )
    assert applied.exit_code == 0, applied.output
    assert applied.output.strip() == "Use [P][AY1]."
    again = RUNNER.invoke(
        app,
        ["add", "pyjanitor", "--respelling", "other", "--lexicon", str(path), "--updated", "2026-11-20"],
    )
    assert again.exit_code == 2


def test_resynth_text_only_rewrites_the_matching_beat(tmp_path: Path) -> None:
    """text-only resynth writes the CosyVoice line and does not invent a wav."""
    project = tmp_path / "proj"
    project.mkdir()
    (project / "script.md").write_text(
        """# Artifact

A pump

# Voice

eric

# Beats

## Beat 0

- join: none
- spoken: You bolt a pipe to a tank.
- visual: A pipe lands.
- number: none
- source: none
- delta: A pipe on a tank

## Beat 1

- join: but
- spoken: But pyjanitor cannot seal it.
- visual: The joint leaks.
- number: none
- source: none
- delta: A leak
""",
        encoding="utf-8",
    )
    result = RUNNER.invoke(
        app,
        [
            "resynth",
            str(project),
            "--term",
            "pyjanitor",
            "--text-only",
            "--lexicon",
            str(SKILL / "lexicon.json"),
            "--voices",
            str(SKILL / "voices.yaml"),
        ],
    )
    assert result.exit_code == 0, result.output
    written = (project / "audio" / "beats" / "01.spoken.txt").read_text(encoding="utf-8")
    assert "[P][AY1]" in written
    assert "pyjanitor" not in written
    assert not (project / "audio" / "beats" / "00.spoken.txt").exists()
    assert not (project / "audio" / "beats" / "01.wav").exists()
    assert "No audio was synthesized" in result.output or "Text only" in result.output
