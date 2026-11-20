"""Tests for script parsing, beat placement, ducking, and the HTML scaffold."""

from __future__ import annotations

import json
import wave
from pathlib import Path

import pytest
from composition import render_html
from timeline import (
    ScriptError,
    build_timeline,
    duck_points,
    parse_script,
    place_on_beats,
    wav_duration,
)
from visuals import render_picture

SCRIPT = """# Artifact

A tiny pump

# Voice

eric

# Beats

## Beat 0

- join: none
- spoken: You bolt a pipe to a tank.
- visual: A pipe lands on a tank.
- number: none
- source: none
- delta: A tank

## Beat 1

- join: but
- spoken: But the joint leaks.
- visual: Water sprays at the joint.
- number: none
- source: none
- delta: A leak at the joint
"""


def test_parse_script_reads_beats_in_order() -> None:
    """Headings become beats and the voice id is the first word."""
    script = parse_script(SCRIPT)
    assert script.artifact == "A tiny pump"
    assert script.voice == "eric"
    assert script.script_format == "short"
    assert [beat.join for beat in script.beats] == ["none", "but"]
    assert script.beats[1].spoken == "But the joint leaks."


def test_parse_defaults_format_to_short() -> None:
    """A script with no Format heading is a short. That keeps older files valid."""
    assert parse_script(SCRIPT).script_format == "short"


def test_parse_reads_build_up_format() -> None:
    """An optional Format heading selects the porch-swing long form."""
    text = SCRIPT.replace("# Beats", "# Format\n\nbuild-up\n\n# Beats")
    script = parse_script(text)
    assert script.script_format == "build-up"


def test_parse_rejects_unknown_format() -> None:
    """Format is short or build-up. Anything else is a parse error."""
    text = SCRIPT.replace("# Beats", "# Format\n\nlong\n\n# Beats")
    with pytest.raises(ScriptError, match="short or build-up"):
        parse_script(text)


def test_build_up_example_parses() -> None:
    """The DS Bootstrap porch-swing script is a 30-beat build-up."""
    path = Path(__file__).resolve().parents[1] / "examples" / "ds-bootstrap-build-up" / "script.md"
    script = parse_script(path.read_text(encoding="utf-8"))
    assert script.script_format == "build-up"
    assert script.artifact == "A bootstrapped data science machine"
    assert script.voice == "eric"
    assert len(script.beats) == 30
    assert script.beats[0].join == "none"
    assert script.beats[-1].join == "none"
    assert script.beats[2].join == "therefore"
    assert script.beats[28].delta.startswith("~/dotfiles/")


def test_parse_script_rejects_a_gap_in_beat_numbers() -> None:
    """Beat headings have to be 0, 1, 2, with no skipped index."""
    broken = SCRIPT.replace("## Beat 1", "## Beat 2")
    with pytest.raises(ScriptError, match="numbered"):
        parse_script(broken)


def test_place_on_beats_snaps_inside_the_gap_window() -> None:
    """A beat inside the allowed gap wins, and speech length stays put."""
    placed = place_on_beats(
        [1.0, 1.0],
        [0.2, 1.4, 2.6],
        min_gap=0.08,
        max_gap=0.55,
        lead_in=0.2,
        tail=0.5,
    )
    assert placed[0].start == pytest.approx(0.2)
    assert placed[0].duration == pytest.approx(1.0)
    assert placed[1].start == pytest.approx(1.4)
    assert placed[1].duration == pytest.approx(1.0)
    assert placed[1].start >= placed[0].end + 0.08


def test_place_on_beats_keeps_min_gap_when_no_beat_is_close() -> None:
    """An empty or distant beat list does not stretch or overlap speech."""
    placed = place_on_beats([2.0, 2.0, 2.0], [], min_gap=0.1, max_gap=0.4, lead_in=0.0, tail=0.5)
    assert placed[0].start == pytest.approx(0.0)
    assert placed[1].start == pytest.approx(2.1)
    assert placed[2].start == pytest.approx(4.2)
    for item in placed:
        assert item.duration == pytest.approx(2.0)


def test_duck_points_are_low_during_speech_and_never_go_backwards() -> None:
    """The music lane dips for the speech span and the times stay sorted."""
    placed = place_on_beats([1.0, 1.0], [0.2, 1.4], min_gap=0.08, max_gap=0.55, lead_in=0.2)
    points = duck_points(placed, bed=1.0, ducked=0.35, ramp=0.12)
    times = [point["t"] for point in points]
    assert times == sorted(times)
    assert _gain_at(points, placed[0].start + 0.5) == pytest.approx(0.35)
    assert _gain_at(points, 0.0) == pytest.approx(1.0)


def test_wav_duration_and_timeline_size(tmp_path: Path) -> None:
    """A known WAV duration flows into a 1080x1920 timeline."""
    path = tmp_path / "00.wav"
    _write_silence(path, seconds=1.5, rate=8000)
    assert wav_duration(path) == pytest.approx(1.5)
    one = parse_script(
        "# Artifact\n\nPump\n\n# Voice\n\neric\n\n# Beats\n\n## Beat 0\n\n"
        "- join: none\n- spoken: Hello pyjanitor.\n- visual: A pipe < a tank & more.\n"
        "- number: none\n- source: docs/pump.md:4\n- delta: A pipe < a tank\n"
    )
    document = build_timeline(
        one,
        [wav_duration(path)],
        [0.0],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=120.0,
        aspect="9:16",
    )
    assert document["width"] == 1080
    assert document["height"] == 1920
    assert document["placements"][0]["duration"] == pytest.approx(1.5)
    wide = build_timeline(
        one,
        [1.5],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
        aspect="16:9",
    )
    assert (wide["width"], wide["height"]) == (1920, 1080)
    html = render_html(document)
    assert 'data-width="1080"' in html
    assert 'data-height="1920"' in html
    assert '"target":"volume"' in html
    assert "A pipe &lt; a tank &amp; more." in html
    assert "Math.random" not in html
    assert "setTimeout" not in html
    assert "DejaVu Sans Mono" in html
    assert "Liberation Mono" in html
    json.dumps(document)


def test_parse_accepts_caveat_source_and_delta() -> None:
    """A caveat join, a path:line source, and a delta all survive the parse."""
    script = parse_script(
        SCRIPT.replace("- join: but", "- join: caveat").replace(
            "- source: none\n- delta: A leak at the joint",
            "- source: docs/tank.md:12\n- delta: A note on the leak",
        )
    )
    assert script.beats[1].join == "caveat"
    assert script.beats[1].source == "docs/tank.md:12"
    assert script.beats[1].delta == "A note on the leak"


def test_parse_accepts_an_older_script_shape() -> None:
    """Beats written before source and delta still parse. source is free text."""
    older = SCRIPT.replace("- source: none\n- delta: A tank\n", "").replace(
        "- source: none\n- delta: A leak at the joint\n",
        "- source: the tank notes, not a path\n",
    )
    script = parse_script(older)
    assert script.beats[0].source == "none"
    assert script.beats[0].delta == "none"
    assert script.beats[1].source == "the tank notes, not a path"
    assert script.beats[1].delta == "none"


def test_picture_accumulates_deltas_without_restating_them_in_visual() -> None:
    """Beat 1's frame still shows beat 0's delta, and the visual line does not have to."""
    script = parse_script(SCRIPT)
    document = build_timeline(
        script,
        [1.0, 1.0],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
    )
    assert document["placements"][0]["picture"] == ["A tank"]
    assert document["placements"][1]["picture"] == ["A tank", "A leak at the joint"]
    html = render_html(document)
    later = html.split('id="beat-1"', maxsplit=1)[1]
    earlier = html.split('id="beat-1"', maxsplit=1)[0]
    assert "A tank" in earlier
    assert "A leak at the joint" not in earlier
    assert "A tank" in later
    assert "A leak at the joint" in later
    assert 'class="added"' in later
    assert 'class="filetree"' not in html


def test_tilde_root_renders_as_a_second_tree() -> None:
    """A ~/ path is a second tree root, next to the project tree."""
    script = parse_script(
        SCRIPT.replace("- delta: A tank", "- delta: analysis.ipynb").replace(
            "- delta: A leak at the joint", "- delta: ~/dotfiles/install.sh"
        )
    )
    document = build_timeline(
        script,
        [1.0, 1.0],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
    )
    html = render_html(document)
    scene = html.split('id="beat-1"', maxsplit=1)[1].split("<audio", maxsplit=1)[0]
    assert scene.count('class="filetree"') == 2
    assert "~/" in scene
    assert "dotfiles/" in scene
    assert "install.sh" in scene
    assert "analysis.ipynb" in scene
    assert 'id="added-1"' in scene


def test_comma_separated_path_deltas_all_appear() -> None:
    """Comma-separated paths in one delta are separate tree entries."""
    script = parse_script(
        SCRIPT.replace("- delta: A tank", "- delta: .env, .gitignore")
    )
    document = build_timeline(
        script,
        [1.0, 1.0],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
    )
    assert document["placements"][0]["picture"] == [".env", ".gitignore"]
    html = render_html(document)
    assert ".env" in html
    assert ".gitignore" in html
    assert 'class="added"' in html.split('id="beat-0"', maxsplit=1)[1].split('id="beat-1"', maxsplit=1)[0]


def test_empty_directory_keeps_a_trailing_slash() -> None:
    """A delta that ends with / is a directory, even when it has no children."""
    html = render_picture([".git/", ".github/workflows/"], index=18, added=".git/")
    assert ">.git/</li>" in html
    assert "workflows/" in html
    assert 'class="added"' in html
    assert ">.git</li>" not in html


def test_path_deltas_render_a_cumulative_file_tree() -> None:
    """A path delta grows a diagram, and the newest file is the one that enters."""
    script = parse_script(
        SCRIPT.replace("- delta: A tank", "- delta: environment.yml").replace(
            "- delta: A leak at the joint", "- delta: data/raw.csv"
        )
    )
    document = build_timeline(
        script,
        [1.0, 1.0],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
    )
    html = render_html(document)
    assert 'class="filetree"' in html
    assert "environment.yml" in html
    assert "data/" in html
    assert "raw.csv" in html
    assert 'id="added-1"' in html
    assert "diagram" in html.split('id="beat-1"', maxsplit=1)[1][:400]


def _gain_at(points: list[dict[str, float]], when: float) -> float:
    """Hold the last lane value at or before ``when``.

    :param points: Duck points.
    :param when: Time in seconds.
    :returns: Linear gain.
    """
    current = points[0]["v"]
    for point in points:
        if point["t"] <= when + 1e-9:
            current = point["v"]
        else:
            break
    return current


def _write_silence(path: Path, *, seconds: float, rate: int) -> None:
    """Write a mono 16-bit silent WAV.

    :param path: Destination.
    :param seconds: Duration.
    :param rate: Sample rate.
    """
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * frames)
