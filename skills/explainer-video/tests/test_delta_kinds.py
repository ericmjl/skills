"""Tests for named picture-template delta kinds."""

from __future__ import annotations

from html.parser import HTMLParser

import pytest
from composition import render_html
from timeline import build_timeline, parse_script
from visuals import parse_delta_kind, render_picture, split_delta, template_items

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
- delta: number-counter {"title": "Leaks plugged", "value": 1285000, "suffix": "+", "note": "Still climbing"}

## Beat 1

- join: but
- spoken: But the joint leaks.
- visual: Water sprays at the joint.
- number: none
- source: none
- delta: before-after-stat {"label": "Hours per cut", "before": 12, "after": 3, "unit": "h", "before_label": "Past", "after_label": "Now", "conclusion": "A quarter of the wait"}

## Beat 2

- join: therefore
- spoken: So you add a first flush pipe.
- visual: A diverter kicks the first flow aside.
- number: none
- source: none
- delta: cause-chain {"title": "Why it holds", "cause": "The joint leaked", "mechanism": "A gasket seats", "result": "The pipe stays dry"}

## Beat 3

- join: none
- spoken: Congratulations, you built A tiny pump.
- visual: Title card with the artifact name.
- number: none
- source: none
- delta: checklist-pop {"title": "Ship check", "items": ["Gasket seated", "Pressure held", "Sign-off"]}
"""


def test_parse_delta_kind_reads_json_and_key_values() -> None:
    """JSON objects and key=value pairs both become a payload."""
    kind, payload = parse_delta_kind(
        'number-counter {"title": "Users", "value": 1285000, "suffix": "+"}'
    )
    assert kind == "number-counter"
    assert payload["value"] == 1285000
    assert payload["suffix"] == "+"
    kind, payload = parse_delta_kind("before-after-stat label=Build before=12 after=3 unit=h")
    assert kind == "before-after-stat"
    assert payload["before"] == 12
    assert payload["after"] == 3
    assert parse_delta_kind("A tank") is None
    assert parse_delta_kind("data/raw.csv") is None
    assert split_delta('cause-chain {"cause": "a, b", "result": "c"}') == (
        'cause-chain {"cause": "a, b", "result": "c"}',
    )


def test_template_items_accept_a_list_or_numbered_keys() -> None:
    """Checklist rows come from items or item1 / item2 / item3."""
    assert template_items({"items": ["Lint", "Tests"]}) == ("Lint", "Tests")
    assert template_items({"item1": "A", "item2": "B", "item3": "C"}) == ("A", "B", "C")
    assert template_items({"items": "Lint|Tests|Review"}) == ("Lint", "Tests", "Review")


def test_render_picture_emits_house_style_markup() -> None:
    """Each kind renders ids the tweens can target, in the house palette's HTML."""
    counter = render_picture(
        ['number-counter {"title": "Users", "value": 42, "suffix": "+"}'],
        index=0,
        added='number-counter {"title": "Users", "value": 42, "suffix": "+"}',
    )
    assert 'id="counter-0"' in counter
    assert 'id="counter-value-0"' in counter
    assert 'data-target="42"' in counter
    assert "Users" in counter
    stat = render_picture(
        ['before-after-stat {"label": "Hours", "before": 12, "after": 3, "unit": "h"}'],
        index=1,
        added='before-after-stat {"label": "Hours", "before": 12, "after": 3, "unit": "h"}',
    )
    assert 'id="stat-1"' in stat
    assert 'id="stat-after-1"' in stat
    assert "Hours" in stat
    chain = render_picture(
        ['cause-chain {"title": "Why", "cause": "A", "mechanism": "B", "result": "C"}'],
        index=2,
        added='cause-chain {"title": "Why", "cause": "A", "mechanism": "B", "result": "C"}',
    )
    assert 'id="chain-2"' in chain
    assert 'id="chain-step-2-0"' in chain
    assert "Cause" in chain
    assert "Mechanism" in chain
    assert "Result" in chain
    checks = render_picture(
        ['checklist-pop {"title": "Ship", "items": ["Lint", "Tests"]}'],
        index=3,
        added='checklist-pop {"title": "Ship", "items": ["Lint", "Tests"]}',
    )
    assert 'id="checks-3"' in checks
    assert 'id="check-3-0"' in checks
    assert "Lint" in checks


def test_composition_wires_seek_safe_template_tweens() -> None:
    """Template beats emit GSAP proxy counts, not CSS loops or timers."""
    script = parse_script(SCRIPT)
    document = build_timeline(
        script,
        [2.0, 2.0, 2.0, 2.0],
        [],
        music_path="audio/music.wav",
        music_duration=20.0,
        bpm=0.0,
    )
    html = render_html(document)
    assert 'id="counter-0"' in html
    assert 'id="stat-1"' in html
    assert 'id="chain-2"' in html
    assert 'id="checks-3"' in html
    assert "const counter0 = { val: 0 };" in html
    assert "tl.to(counter0" in html
    assert "tl.to(stat1" in html
    assert 'tl.from("#chain-step-2-0"' in html
    assert 'tl.from("#check-3-0"' in html
    assert "setTimeout" not in html
    assert "setInterval" not in html
    assert "animation-iteration-count" not in html
    assert "@keyframes" not in html
    assert "Math.random" not in html
    assert "paused: true" in html
    HTMLParser().feed(html)
    assert document["placements"][0]["delta"].startswith("number-counter")


def test_bad_template_json_is_a_composition_error() -> None:
    """A broken payload fails at render with a beat number, not a traceback."""
    from composition import CompositionError

    script = parse_script(
        SCRIPT.replace(
            '- delta: number-counter {"title": "Leaks plugged", "value": 1285000, "suffix": "+", "note": "Still climbing"}',
            "- delta: number-counter {not json}",
        )
    )
    document = build_timeline(
        script,
        [1.0, 1.0, 1.0, 1.0],
        [],
        music_path="audio/music.wav",
        music_duration=10.0,
        bpm=0.0,
    )
    with pytest.raises(CompositionError, match="Beat 0"):
        render_html(document)
