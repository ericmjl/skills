#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12", "loguru>=0.7"]
# ///
"""Report stretches of a built composition with no active GSAP tween.

A dead zone is any idle span of at least 1.0 s. Each zone is labelled as
an intentional hold, or as a likely missing entrance when a beat holds
longer than 4 s with only one entrance.

    uv run skills/explainer-video/scripts/dead_zones.py PROJECT
    uv run skills/explainer-video/scripts/dead_zones.py PROJECT/index.html
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from loguru import logger

MIN_DEAD_ZONE: float = 1.0
MISSING_ENTRANCE_HOLD: float = 4.0
TWEEN_COMMENT_RE = re.compile(
    r'<!--\s*tween\s+selector="([^"]*)"\s+start="([\d.]+)"\s+duration="([\d.]+)"\s*-->'
)
STAGE_DURATION_RE = re.compile(
    r'id="stage"[^>]*data-duration="([\d.]+)"',
    re.IGNORECASE,
)
BEAT_RE = re.compile(
    r'id="beat-(\d+)"[^>]*data-start="([\d.]+)"[^>]*data-duration="([\d.]+)"',
    re.IGNORECASE,
)
# tl.from("#sel", { duration: 0.4, ... }, 1.250);
# tl.to(cam, { duration: 0.300, ... }, 1.250);
TWEEN_CALL_RE = re.compile(
    r"tl\.(?:fromTo|from|to)\s*\((.*?),\s*([\d.]+)\s*\)\s*;",
    re.DOTALL,
)
DURATION_RE = re.compile(r"duration:\s*([\d.]+)")
TARGET_RE = re.compile(r"^\s*([^,]+)")

app = typer.Typer(add_completion=False, no_args_is_help=True)
logger.remove()
logger.add(sys.stderr, format="{message}")


class DeadZoneError(ValueError):
    """The composition HTML cannot be analysed."""


@dataclass(frozen=True)
class Tween:
    """One GSAP tween interval.

    :param selector: Target hint (CSS selector, ``cam``, or a proxy name).
    :param start: Timeline time in seconds.
    :param duration: Tween length in seconds.
    """

    selector: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        """Return the exclusive end time.

        :returns: ``start + duration``.
        """
        return self.start + self.duration


@dataclass(frozen=True)
class BeatWindow:
    """Visual clip window for one beat.

    :param index: Beat number.
    :param start: Clip start in seconds.
    :param duration: Speech plus the following gap.
    """

    index: int
    start: float
    duration: float

    @property
    def end(self) -> float:
        """Return the exclusive end of the clip.

        :returns: ``start + duration``.
        """
        return self.start + self.duration


@dataclass(frozen=True)
class DeadZone:
    """An idle stretch of the timeline.

    :param start: Gap start in seconds.
    :param end: Gap end in seconds.
    :param label: ``intentional-hold`` or ``missing-entrance``.
    :param beat: Overlapping beat index, or None.
    :param note: One-line explanation.
    """

    start: float
    end: float
    label: str
    beat: int | None
    note: str

    @property
    def duration(self) -> float:
        """Return the idle length in seconds.

        :returns: ``end - start``.
        """
        return self.end - self.start


@dataclass(frozen=True)
class DeadZoneReport:
    """Full dead-zone audit of one composition.

    :param duration: Composition length in seconds.
    :param tweens: Parsed tween intervals.
    :param beats: Visual clip windows.
    :param zones: Idle stretches of at least 1.0 s.
    """

    duration: float
    tweens: tuple[Tween, ...]
    beats: tuple[BeatWindow, ...]
    zones: tuple[DeadZone, ...]

    @property
    def missing_entrances(self) -> tuple[DeadZone, ...]:
        """Return zones that violate the 4 s single-entrance rule.

        :returns: The ``missing-entrance`` subset, in time order.
        """
        return tuple(zone for zone in self.zones if zone.label == "missing-entrance")


def idle_spans(
    tweens: list[Tween] | tuple[Tween, ...],
    duration: float,
    *,
    min_length: float = MIN_DEAD_ZONE,
) -> tuple[tuple[float, float], ...]:
    """Return idle intervals of at least ``min_length`` seconds.

    Coverage is the union of tween ``[start, end)`` ranges. Gaps before
    the first tween, between merged ranges, and after the last tween are
    kept when they are long enough.

    :param tweens: Active motion intervals.
    :param duration: Composition length in seconds.
    :param min_length: Shortest gap to report.
    :returns: ``(start, end)`` pairs, in time order.
    :raises DeadZoneError: Duration is not positive.
    """
    if duration <= 0:
        raise DeadZoneError(f"Composition duration must be positive, got {duration}.")
    intervals = sorted(
        (float(item.start), float(item.end))
        for item in tweens
        if item.duration > 1e-9
    )
    merged: list[list[float]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1] + 1e-9:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    gaps: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in merged:
        if start - cursor >= min_length - 1e-9:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if duration - cursor >= min_length - 1e-9:
        gaps.append((cursor, duration))
    return tuple(gaps)


def classify_span(
    start: float,
    end: float,
    beats: list[BeatWindow] | tuple[BeatWindow, ...],
    tweens: list[Tween] | tuple[Tween, ...],
) -> DeadZone:
    """Label one idle span as a hold or a missing entrance.

    A span is a likely missing entrance when the overlapping beat holds
    longer than 4 s (or the span itself does) and that beat has fewer
    than two tween starts. Otherwise it is an intentional hold.

    :param start: Gap start in seconds.
    :param end: Gap end in seconds.
    :param beats: Visual clip windows.
    :param tweens: All tween intervals.
    :returns: A labelled dead zone.
    """
    span = end - start
    beat = _overlapping_beat(start, end, beats)
    starts = 0
    if beat is not None:
        starts = sum(
            1
            for tween in tweens
            if beat.start - 1e-9 <= tween.start < beat.end - 1e-9
        )
    long_hold = span > MISSING_ENTRANCE_HOLD + 1e-9 or (
        beat is not None and beat.duration > MISSING_ENTRANCE_HOLD + 1e-9
    )
    second_entrance = starts >= 2
    if long_hold and not second_entrance:
        label = "missing-entrance"
        if beat is None:
            note = (
                f"No animation for {span:.1f}s. "
                "A hold over 4s with no second entrance is a miss."
            )
        else:
            note = (
                f"Beat {beat.index} holds {beat.duration:.1f}s with {starts} entrance"
                f"{'' if starts == 1 else 's'}. "
                "Add a second visual change before the final render."
            )
        return DeadZone(start=start, end=end, label=label, beat=None if beat is None else beat.index, note=note)
    note = (
        f"No animation for {span:.1f}s. Intentional hold."
        if beat is None
        else (
            f"Beat {beat.index}: {span:.1f}s hold after "
            f"{starts} entrance{'' if starts == 1 else 's'}."
        )
    )
    return DeadZone(
        start=start,
        end=end,
        label="intentional-hold",
        beat=None if beat is None else beat.index,
        note=note,
    )


def analyze_tweens(
    tweens: list[Tween] | tuple[Tween, ...],
    *,
    duration: float,
    beats: list[BeatWindow] | tuple[BeatWindow, ...] = (),
) -> DeadZoneReport:
    """Build a dead-zone report from tween intervals.

    :param tweens: Active motion intervals.
    :param duration: Composition length in seconds.
    :param beats: Visual clip windows, used only for labelling.
    :returns: The labelled report.
    """
    spans = idle_spans(tweens, duration)
    zones = tuple(classify_span(start, end, beats, tweens) for start, end in spans)
    return DeadZoneReport(
        duration=duration,
        tweens=tuple(tweens),
        beats=tuple(beats),
        zones=zones,
    )


def parse_html(html: str) -> DeadZoneReport:
    """Read tween comments (or GSAP statements) and beat clips from HTML.

    Comments of the form ``<!-- tween selector="..." start="..." duration="..." -->``
    are the preferred map. When none are present, ``tl.from`` / ``tl.to`` /
    ``tl.fromTo`` statements are parsed instead.

    :param html: Built ``index.html``.
    :returns: The labelled report.
    :raises DeadZoneError: Duration is missing or not positive.
    """
    duration = _stage_duration(html)
    beats = parse_beats(html)
    tweens = parse_tween_comments(html) or parse_gsap_tweens(html)
    return analyze_tweens(tweens, duration=duration, beats=beats)


def parse_tween_comments(html: str) -> tuple[Tween, ...]:
    """Read machine-readable tween comments.

    :param html: Built ``index.html``.
    :returns: Tweens in document order, or empty when none are present.
    """
    found: list[Tween] = []
    for selector, start, duration in TWEEN_COMMENT_RE.findall(html):
        found.append(
            Tween(selector=selector, start=float(start), duration=float(duration))
        )
    return tuple(found)


def parse_gsap_tweens(html: str) -> tuple[Tween, ...]:
    """Read ``tl.from`` / ``tl.to`` / ``tl.fromTo`` statements.

    :param html: Built ``index.html``.
    :returns: Tweens in document order.
    """
    found: list[Tween] = []
    for args, start in TWEEN_CALL_RE.findall(html):
        target_match = TARGET_RE.match(args)
        duration_match = DURATION_RE.search(args)
        if target_match is None or duration_match is None:
            continue
        found.append(
            Tween(
                selector=target_match.group(1).strip().strip("\"'"),
                start=float(start),
                duration=float(duration_match.group(1)),
            )
        )
    return tuple(found)


def parse_beats(html: str) -> tuple[BeatWindow, ...]:
    """Read ``#beat-N`` clip windows.

    :param html: Built ``index.html``.
    :returns: Beat windows in document order.
    """
    found: list[BeatWindow] = []
    for index, start, duration in BEAT_RE.findall(html):
        found.append(
            BeatWindow(index=int(index), start=float(start), duration=float(duration))
        )
    return tuple(found)


def tween_comment(tween: Tween) -> str:
    """Format one tween as an HTML comment.

    :param tween: Interval to record.
    :returns: A comment line, without a trailing newline.
    """
    selector = tween.selector.replace('"', "'")
    return (
        f'<!-- tween selector="{selector}" start="{tween.start:.3f}" '
        f'duration="{tween.duration:.3f}" -->'
    )


def format_report(report: DeadZoneReport) -> str:
    """Render a human-readable dead-zone report.

    :param report: Audit result.
    :returns: Multi-line text ending in a newline.
    """
    lines = [
        (
            f"{len(report.tweens)} tweens across {report.duration:.1f}s; "
            f"{len(report.zones)} dead zone{'' if len(report.zones) == 1 else 's'} "
            f">= {MIN_DEAD_ZONE:.1f}s."
        )
    ]
    if not report.zones:
        lines.append("No dead zones.")
        return "\n".join(lines) + "\n"
    for zone in report.zones:
        lines.append(
            f"{zone.label} {zone.start:.1f}-{zone.end:.1f}s ({zone.duration:.1f}s): "
            f"{zone.note}"
        )
    missing = len(report.missing_entrances)
    if missing:
        lines.append(
            f"{missing} likely missing entrance{'' if missing == 1 else 's'}. "
            "Add a second visual change before the final render."
        )
    return "\n".join(lines) + "\n"


def report_to_dict(report: DeadZoneReport) -> dict[str, Any]:
    """JSON-ready form of a report.

    :param report: Audit result.
    :returns: A dictionary.
    """
    return {
        "duration": round(report.duration, 3),
        "tweens": [
            {
                "selector": tween.selector,
                "start": round(tween.start, 3),
                "duration": round(tween.duration, 3),
            }
            for tween in report.tweens
        ],
        "zones": [
            {
                "start": round(zone.start, 3),
                "end": round(zone.end, 3),
                "duration": round(zone.duration, 3),
                "label": zone.label,
                "beat": zone.beat,
                "note": zone.note,
            }
            for zone in report.zones
        ],
    }


def _stage_duration(html: str) -> float:
    """Read ``data-duration`` from ``#stage``.

    :param html: Built ``index.html``.
    :returns: Composition length in seconds.
    :raises DeadZoneError: The attribute is missing.
    """
    match = STAGE_DURATION_RE.search(html)
    if match is None:
        raise DeadZoneError("index.html is missing #stage data-duration.")
    duration = float(match.group(1))
    if duration <= 0:
        raise DeadZoneError(f"Composition duration must be positive, got {duration}.")
    return duration


def _overlapping_beat(
    start: float,
    end: float,
    beats: list[BeatWindow] | tuple[BeatWindow, ...],
) -> BeatWindow | None:
    """Return the beat that covers most of ``[start, end)``.

    :param start: Gap start.
    :param end: Gap end.
    :param beats: Visual clip windows.
    :returns: The best overlapping beat, or None.
    """
    best: BeatWindow | None = None
    best_overlap = 0.0
    for beat in beats:
        overlap = min(end, beat.end) - max(start, beat.start)
        if overlap > best_overlap:
            best_overlap = overlap
            best = beat
    return best


@app.command()
def check(
    source: Path = typer.Argument(
        ...,
        help="Project directory containing index.html, or the HTML file itself.",
    ),
    json_out: bool = typer.Option(False, "--json", help="Print the report as JSON."),
) -> None:
    """Audit a built composition for dead zones."""
    html_path = source / "index.html" if source.is_dir() else source
    if not html_path.is_file():
        logger.error("Error: missing {}.", html_path)
        raise typer.Exit(code=2)
    try:
        report = parse_html(html_path.read_text(encoding="utf-8"))
    except DeadZoneError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    if json_out:
        typer.echo(json.dumps(report_to_dict(report), indent=2))
    else:
        typer.echo(format_report(report), nl=False)
    if report.missing_entrances:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
