"""Tests for the composition dead-zone (no-motion) checker."""

from __future__ import annotations

from pathlib import Path

from dead_zones import (
    BeatWindow,
    Tween,
    analyze_tweens,
    app,
    format_report,
    idle_spans,
    parse_gsap_tweens,
    parse_html,
    parse_tween_comments,
    tween_comment,
)
from typer.testing import CliRunner

RUNNER = CliRunner()


def test_idle_spans_report_gaps_of_at_least_one_second() -> None:
    """Coverage is the union of tweens; gaps under 1 s are ignored."""
    tweens = (
        Tween(selector="#a", start=0.0, duration=0.4),
        Tween(selector="#b", start=2.0, duration=0.4),
        Tween(selector="#c", start=2.1, duration=0.3),
    )
    spans = idle_spans(tweens, duration=5.0)
    assert spans == ((0.4, 2.0), (2.4, 5.0))
    assert idle_spans(tweens, duration=2.8) == ((0.4, 2.0),)


def test_idle_spans_include_a_leading_gap() -> None:
    """Lead-in with no tween is a dead zone when it lasts a second."""
    tweens = (Tween(selector="#a", start=1.2, duration=0.4),)
    assert idle_spans(tweens, duration=2.0) == ((0.0, 1.2),)


def test_short_beat_hold_is_intentional() -> None:
    """A 1.5 s idle inside a 2 s beat with one entrance is a hold, not a miss."""
    tweens = (Tween(selector="#line-0", start=0.15, duration=0.4),)
    beats = (BeatWindow(index=0, start=0.15, duration=2.0),)
    report = analyze_tweens(tweens, duration=2.15, beats=beats)
    assert len(report.zones) == 1
    assert report.zones[0].label == "intentional-hold"
    assert report.missing_entrances == ()


def test_long_hold_with_one_entrance_is_a_missing_entrance() -> None:
    """The 4 s single-entrance rule labels the idle span as a miss."""
    tweens = (Tween(selector="#line-0", start=0.0, duration=0.4),)
    beats = (BeatWindow(index=3, start=0.0, duration=5.2),)
    report = analyze_tweens(tweens, duration=5.2, beats=beats)
    assert report.zones[0].label == "missing-entrance"
    assert report.zones[0].beat == 3
    assert "second visual change" in report.zones[0].note
    assert report.missing_entrances == report.zones


def test_second_entrance_makes_a_long_hold_intentional() -> None:
    """Two tween starts in a 5 s beat satisfy the review rule."""
    tweens = (
        Tween(selector="#line-1", start=1.0, duration=0.4),
        Tween(selector=".added", start=1.0, duration=0.4),
        Tween(selector="cam", start=1.15, duration=0.3),
    )
    beats = (BeatWindow(index=1, start=1.0, duration=5.0),)
    report = analyze_tweens(tweens, duration=6.0, beats=beats)
    labels = {zone.label for zone in report.zones}
    assert labels == {"intentional-hold"}
    assert report.missing_entrances == ()


def test_parse_tween_comments_and_gsap_fallback() -> None:
    """Comments are preferred; GSAP statements fill in when comments are absent."""
    html = """
    <div id="stage" data-duration="4.000"></div>
    <section id="beat-0" class="clip" data-start="0.150" data-duration="2.000"></section>
    <!-- tween selector="#line-0" start="0.150" duration="0.400" -->
    <script>
      tl.from("#line-0", { y: 36, autoAlpha: 0, duration: 0.4, ease: "power3.out" }, 0.150);
    </script>
    """
    comments = parse_tween_comments(html)
    assert comments == (Tween(selector="#line-0", start=0.15, duration=0.4),)
    parsed = parse_html(html)
    assert parsed.tweens == comments
    js_only = html.replace("<!-- tween", "<!-- other")
    fallback = parse_gsap_tweens(js_only)
    assert fallback[0].selector == "#line-0"
    assert fallback[0].start == 0.15
    assert fallback[0].duration == 0.4


def test_parse_html_classifies_a_scaffold_hold(tmp_path: Path) -> None:
    """The CLI reads a project index.html and exits 1 on a missing entrance."""
    html = """<!DOCTYPE html>
<html><body>
  <div id="stage" data-composition-id="explainer" data-duration="5.200"></div>
  <section id="beat-0" class="clip scene" data-start="0.000" data-duration="5.200"></section>
  <!-- tween selector="#line-0" start="0.000" duration="0.400" -->
  <script>
    const tl = gsap.timeline({ paused: true });
    tl.from("#line-0", { y: 36, autoAlpha: 0, duration: 0.4, ease: "power3.out" }, 0.000);
  </script>
</body></html>
"""
    (tmp_path / "index.html").write_text(html, encoding="utf-8")
    result = RUNNER.invoke(app, [str(tmp_path)])
    assert result.exit_code == 1
    assert "missing-entrance" in result.stdout
    text = format_report(parse_html(html))
    assert "missing entrance" in text


def test_tween_comment_round_trips() -> None:
    """The comment emitter matches the parser."""
    tween = Tween(selector="#added-1", start=1.25, duration=0.3)
    assert parse_tween_comments(tween_comment(tween)) == (tween,)
