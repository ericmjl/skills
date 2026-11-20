#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12", "loguru>=0.7"]
# ///
"""Write index.html from timeline.json.

    uv run skills/explainer-video/scripts/build_composition.py PROJECT
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import typer
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from composition import CompositionError, render_html

CC_BY = re.compile(r"^cc[\s-]*by\b", re.IGNORECASE)

app = typer.Typer(add_completion=False, no_args_is_help=True)
logger.remove()
logger.add(sys.stderr, format="{message}")


@app.command()
def build(
    project: Path = typer.Argument(..., help="Explainer project that contains timeline.json."),
    output: Path = typer.Option(Path("index.html"), "--output", help="HTML path, relative to the project unless absolute."),
) -> None:
    """Render the HyperFrames document."""
    timeline_path = project / "timeline.json"
    if not timeline_path.is_file():
        logger.error("Error: missing {}. Run align_music.py first.", timeline_path)
        raise typer.Exit(code=2)
    document = json.loads(timeline_path.read_text(encoding="utf-8"))
    try:
        html = render_html(document)
    except CompositionError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    destination = output if output.is_absolute() else project / output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
    typer.echo(f"Wrote {destination} ({document['width']}x{document['height']}, {document['duration']}s).")
    try:
        credit = apply_music_credit(project)
    except (OSError, json.JSONDecodeError, CompositionError) as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    if credit is not None:
        typer.echo(f"Wrote {credit}")
    held = [
        row["index"]
        for row in document["placements"]
        if float(row["duration"]) + float(row["gap_after"]) > 4.0
    ]
    if held:
        logger.warning("Beats {} hold longer than 4s. Add another visual change before final.", held)


def attribution_line(payload: dict[str, object]) -> str | None:
    """Build the credit line for a CC BY track.

    CC BY, CC-BY-SA, and the other CC BY-* licenses need the line. CC0 and
    an empty license do not.

    :param payload: Fields from ``audio/credit.json``.
    :returns: One attribution sentence, or ``None`` when the license is not CC BY.
    """
    license_name = str(payload.get("license") or "").strip()
    if CC_BY.match(license_name) is None:
        return None
    title = str(payload.get("title") or "Untitled").strip() or "Untitled"
    author = str(payload.get("author") or "Unknown").strip() or "Unknown"
    source = str(payload.get("source") or "").strip()
    line = f'"{title}" by {author}. License: {license_name}.'
    if source:
        line = f"{line} Source: {source}."
    return line


def apply_music_credit(project: Path) -> Path | None:
    """Write ``credits.txt`` when the project's music is CC BY.

    ``audio/credit.json`` holds ``title``, ``author``, ``source``, and
    ``license``. A missing file leaves any existing ``credits.txt`` alone.
    A license that is not CC BY removes a previous ``credits.txt`` so a
    track change cannot leave a stale attribution.

    :param project: Explainer project directory.
    :returns: The credits path, or ``None`` when nothing was written.
    :raises CompositionError: The credit file is not a JSON object.
    """
    path = project / "audio" / "credit.json"
    destination = project / "credits.txt"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CompositionError("audio/credit.json must be an object.")
    line = attribution_line(payload)
    if line is None:
        if destination.is_file():
            destination.unlink()
        return None
    destination.write_text(line + "\n", encoding="utf-8")
    return destination


if __name__ == "__main__":
    app()
