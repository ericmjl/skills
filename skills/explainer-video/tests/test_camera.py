"""Tests for logarithmic zoom duration and the camera-rig markup."""

from __future__ import annotations

import math

import pytest
from camera import (
    DEFAULT_PUSH_ZOOM,
    parse_push,
    resolve_push_zoom,
    zoom_duration,
)
from composition import render_html
from timeline import build_timeline, parse_script

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
- delta: environment.yml
- push: auto

## Beat 1

- join: but
- spoken: But the joint leaks.
- visual: Water sprays at the joint.
- number: none
- source: none
- delta: data/raw.csv
- push: 1.8
"""


def test_zoom_duration_doubling_is_point_five_five() -> None:
    """1x to 2x is exactly 0.55 s, the constant the formula is built on."""
    assert zoom_duration(1.0, 2.0) == pytest.approx(0.55)
    assert zoom_duration(2.0, 1.0) == pytest.approx(0.55)


def test_zoom_duration_clamps_small_and_large_jumps() -> None:
    """1 -> 1.3x hits the 0.30 s floor; 0.78 -> 2.6x hits the 0.94 s ceiling."""
    raw_small = 0.55 * abs(math.log(1.3 / 1.0)) / math.log(2.0)
    assert raw_small < 0.30
    assert zoom_duration(1.0, 1.3) == pytest.approx(0.30)
    raw_large = 0.55 * abs(math.log(2.6 / 0.78)) / math.log(2.0)
    assert raw_large > 0.94
    assert zoom_duration(0.78, 2.6) == pytest.approx(0.94)


def test_equal_zoom_still_takes_the_minimum() -> None:
    """A pan at constant magnification is not a zero-duration snap."""
    assert zoom_duration(1.45, 1.45) == pytest.approx(0.30)


def test_parse_and_resolve_push() -> None:
    """auto pushes a file-tree node; none skips; tiny zooms are ignored."""
    assert parse_push(None) == "auto"
    assert parse_push("off") == "none"
    assert parse_push("1.8") == "1.8"
    assert resolve_push_zoom("auto", has_file_target=True) == DEFAULT_PUSH_ZOOM
    assert resolve_push_zoom("auto", has_file_target=False) is None
    assert resolve_push_zoom("none", has_file_target=True) is None
    assert resolve_push_zoom("1.8", has_file_target=False) == pytest.approx(1.8)
    assert resolve_push_zoom("1.1", has_file_target=True) is None
    with pytest.raises(ValueError, match="push"):
        parse_push("huge")


def test_composition_wraps_a_seek_safe_camera_rig() -> None:
    """The scaffold is viewport / camera / world / hud, driven from the timeline."""
    script = parse_script(SCRIPT)
    document = build_timeline(
        script,
        [1.0, 5.0],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
    )
    html = render_html(document)
    assert 'id="viewport"' in html
    assert 'id="camera"' in html
    assert 'id="world"' in html
    assert 'id="hud"' in html
    assert "world.style.zoom" in html
    assert "onUpdate: applyCam" in html
    assert "transform: scale" not in html.split("applyCam")[1].split("function layoutCenter")[0]
    assert "setTimeout" not in html
    assert "Math.random" not in html
    assert "requestAnimationFrame" not in html
    duration_1_45 = zoom_duration(1.0, DEFAULT_PUSH_ZOOM)
    duration_1_8 = zoom_duration(DEFAULT_PUSH_ZOOM, 1.8)
    assert f"{duration_1_45:.3f}" in html
    assert f"{duration_1_8:.3f}" in html
    assert 'id="added-1"' in html
    assert "layoutCenter(\"#added-0\")" in html
    assert "layoutCenter(\"#added-1\")" in html
    assert 'id="hud-0"' in html
    assert 'id="line-0"' in html.split('id="hud-0"', maxsplit=1)[1]


def test_push_none_skips_the_camera_move() -> None:
    """An explicit none leaves the camera at 1x."""
    text = SCRIPT.replace("- push: auto", "- push: none").replace("- push: 1.8", "- push: none")
    script = parse_script(text)
    document = build_timeline(
        script,
        [1.0, 1.0],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
    )
    html = render_html(document)
    assert "layoutCenter" not in html
    assert "zoom: 1.45" not in html
    assert "zoom: 1.8" not in html
    assert 'id="viewport"' in html
