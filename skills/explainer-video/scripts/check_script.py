#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12", "loguru>=0.7"]
# ///
"""Check an explainer script.md against the problem-chain budget.

Run from the repo root:

    uv run skills/explainer-video/scripts/check_script.py check PROJECT/script.md
    uv run skills/explainer-video/scripts/check_script.py mine PROJECT/docs

``check`` exits 0 when the script is inside the shipping budget. ``mine``
lists problem and why headings in a docs tree so a beat's ``source`` field
can point at ``path:line``.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import typer
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from normalize import Lexicon, LexiconError, load_lexicon
from timeline import (
    FORMAT_BUILD_UP,
    FORMAT_SHORT,
    JOINS,
    Script,
    ScriptError,
    parse_script,
)
from visuals import is_file_path, split_delta

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON = SKILL_ROOT / "lexicon.json"

WORDS_MIN = 15
WORDS_MAX = 18
BEATS_MIN = 10
BEATS_MAX = 12
TOTAL_MIN = 150
TOTAL_CENTER_MAX = 190
TOTAL_MAX = BEATS_MAX * WORDS_MAX
FAILURES_MIN = 4
FAILURES_MAX = 5
BUILD_UP_WORDS_WARN = 650
WPM = 150
PUNCHLINE_RE = re.compile(r"(?:That's|Those are)\s+.+\.\s*$", re.IGNORECASE)

BANNED_PHRASES = ("and then", "and next")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TOKEN_RE = re.compile(r"`([^`]+)`|(?<![\w.-])[A-Za-z][A-Za-z0-9]*(?:[._-][A-Za-z0-9]+)*(?![\w.-])")

app = typer.Typer(add_completion=False, no_args_is_help=True)
logger.remove()
logger.add(sys.stderr, format="{message}")


@dataclass(frozen=True)
class BeatReport:
    """One beat's word count and the problems on that beat.

    :param index: Beat number.
    :param join: Join field.
    :param words: Words in the spoken line.
    :param issues: Problems that belong to this beat.
    :param warnings: Notes that do not fail the check.
    """

    index: int
    join: str
    words: int
    issues: tuple[str, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScriptReport:
    """The full check.

    :param beats: Per-beat reports, in order.
    :param total_words: Sum of spoken words.
    :param seconds: Estimated duration at 150 words per minute.
    :param failures: Count of ``but`` joins. The opening is not included.
    :param issues: Script-level problems.
    :param notes: Observations that do not fail the check.
    :param jargon: Candidate terms missing from the lexicon, in first-seen order.
    :param script_format: ``short`` or ``build-up``.
    """

    beats: tuple[BeatReport, ...]
    total_words: int
    seconds: float
    failures: int
    issues: tuple[str, ...]
    notes: tuple[str, ...]
    jargon: tuple[str, ...]
    script_format: str = FORMAT_SHORT

    @property
    def ok(self) -> bool:
        """Return whether the script is inside the shipping budget.

        :returns: True when no beat, script, or jargon issue was recorded.
        """
        return not self.issues and not self.jargon and all(not beat.issues for beat in self.beats)


@dataclass(frozen=True)
class DocHit:
    """One problem or why heading.

    :param path: Path relative to the docs directory that was mined.
    :param line: 1-based line number.
    :param kind: ``problem`` or ``why``.
    :param title: Heading text.
    """

    path: str
    line: int
    kind: str
    title: str


@dataclass(frozen=True)
class FailureFix:
    """A problem heading and the why heading that follows it, if one does.

    :param problem: The problem heading, or None when a why has no problem before it.
    :param fix: The why heading, or None when the problem has no later why.
    """

    problem: DocHit | None
    fix: DocHit | None


def word_count(text: str) -> int:
    """Count whitespace-separated words.

    :param text: Spoken line.
    :returns: The word count. An empty line is zero.
    """
    return len(text.split())


def estimated_seconds(words: int, *, wpm: int = WPM) -> float:
    """Convert a word count to seconds at a speaking rate.

    :param words: Spoken words.
    :param wpm: Words per minute.
    :returns: Seconds, rounded to one decimal.
    """
    if wpm <= 0:
        raise ScriptError("Speaking rate must be positive.")
    return round(words / wpm * 60.0, 1)


def review_joins(joins: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Check join order.

    A caveat sits immediately after a ``therefore``, between two ``but``
    joins, or immediately before the sign-off. It does not take a turn in the
    but/therefore alternation. Two ``but`` joins may occur in a row only when
    every beat between them is a caveat. Two ``therefore`` joins may not.

    :param joins: Join field of each beat, in order.
    :returns: Problem messages. Empty when the order is valid.
    """
    problems: list[str] = []
    if not joins:
        return ("The script has no beats.",)
    if joins[0] != "none":
        problems.append("Beat 0 join must be none. It is the naive version.")
    if len(joins) < 2:
        problems.append("A script needs an opening beat and a separate sign-off beat.")
    elif joins[-1] != "none":
        problems.append("The last beat join must be none. It is the sign-off.")
    last_structural: str | None = None
    last_structural_at: int | None = None
    for index, join in enumerate(joins):
        if join not in JOINS:
            problems.append(f"Beat {index} join {join!r} is not a known join.")
            continue
        if join == "none" and index not in {0, len(joins) - 1}:
            problems.append(f"Beat {index} join none is only valid on the opening and the sign-off.")
        if join == "caveat":
            previous = joins[index - 1] if index else ""
            before_signoff = index + 1 == len(joins) - 1 and joins[-1] == "none"
            after_fix = previous == "therefore"
            between_buts = _nearest_structural(joins, index, step=-1) == "but" and _nearest_structural(
                joins, index, step=1
            ) == "but"
            if not (after_fix or before_signoff or between_buts):
                problems.append(
                    f"Beat {index} caveat must follow a therefore, sit between two buts, "
                    "or sit immediately before the sign-off."
                )
        if join in {"but", "therefore"} and last_structural is not None and last_structural_at is not None:
            if join == last_structural:
                between = joins[last_structural_at + 1 : index]
                around_caveat = join == "but" and bool(between) and all(item == "caveat" for item in between)
                if not around_caveat:
                    problems.append(
                        f"Beat {index} repeats {join} after beat {last_structural_at}. "
                        "Two buts in a row are allowed only around a caveat."
                    )
            last_structural = join
            last_structural_at = index
        elif join in {"but", "therefore"}:
            last_structural = join
            last_structural_at = index
    return tuple(problems)


def _nearest_structural(joins: list[str] | tuple[str, ...], index: int, *, step: int) -> str | None:
    """Return the nearest but or therefore, walking away from ``index``.

    :param joins: Join of each beat.
    :param index: Beat to start beside, not on.
    :param step: ``-1`` searches earlier beats. ``1`` searches later beats.
    :returns: The join, or None when the walk ends first.
    """
    cursor = index + step
    while 0 <= cursor < len(joins):
        if joins[cursor] in {"but", "therefore"}:
            return joins[cursor]
        cursor += step
    return None


def review_script(script: Script, lexicon: Lexicon) -> ScriptReport:
    """Score a parsed script against the shipping budget.

    :param script: Parsed ``script.md``.
    :param lexicon: Pronunciations used to hide known jargon.
    :returns: Word counts, join order, the failure count, and missing jargon.
    """
    beat_reports: list[BeatReport] = []
    issues: list[str] = []
    notes: list[str] = []
    therefore_openers: list[str] = []
    script_format = script.script_format
    for beat in script.beats:
        local: list[str] = []
        words = word_count(beat.spoken)
        warnings: list[str] = []
        if words < WORDS_MIN or words > WORDS_MAX:
            warnings.append(f"{words} words; a beat is {WORDS_MIN}-{WORDS_MAX} words.")
        local.extend(_spoken_form_issues(beat.index, beat.join, beat.spoken, script_format))
        local.extend(_banned_issues(beat.spoken))
        if beat.number.strip().lower() != "none" and beat.source == "none":
            local.append("number is set and source is none. Point source at path:line.")
        if (
            script_format == FORMAT_SHORT
            and beat.delta.strip().lower() == "none"
            and beat.join != "none"
        ):
            local.append("delta is none, so the persistent picture does not change.")
        if beat.join == "therefore":
            therefore_openers.append(_first_word(beat.spoken).lower())
            if script_format == FORMAT_BUILD_UP and not _has_punchline(beat.spoken):
                warnings.append(
                    "therefore is missing a naming punchline (That's X. or Those are X.)."
                )
        beat_reports.append(
            BeatReport(beat.index, beat.join, words, tuple(local), tuple(warnings))
        )

    issues.extend(review_joins([beat.join for beat in script.beats]))
    if (
        len(therefore_openers) >= 2
        and all(opener == "therefore" for opener in therefore_openers)
    ):
        notes.append(
            "Every therefore line starts with 'therefore'. So is the recommended opener."
        )

    total = sum(item.words for item in beat_reports)
    failures = sum(1 for beat in script.beats if beat.join == "but")
    if script_format == FORMAT_SHORT:
        if not BEATS_MIN <= len(script.beats) <= BEATS_MAX:
            issues.append(
                f"{len(script.beats)} beats; a shipping Short is {BEATS_MIN}-{BEATS_MAX} beats."
            )
        if total < TOTAL_MIN or total > TOTAL_MAX:
            issues.append(
                f"{total} spoken words; the budget is {TOTAL_MIN}-{TOTAL_MAX} "
                f"({BEATS_MIN}x{WORDS_MIN} through {BEATS_MAX}x{WORDS_MAX})."
            )
        elif total > TOTAL_CENTER_MAX:
            notes.append(
                f"{total} spoken words is above the {TOTAL_MIN}-{TOTAL_CENTER_MAX} center "
                "and still inside 90 seconds."
            )
        if not FAILURES_MIN <= failures <= FAILURES_MAX:
            issues.append(
                f"{failures} but-joins. A shipping Short has {FAILURES_MIN} or {FAILURES_MAX}. "
                "The opening naive failure is not part of this count. "
                "A chain table may hold up to 7 before you condense."
            )
        signoff = _signoff_issue(script.artifact, script.beats[-1].spoken if script.beats else "")
        if signoff:
            issues.append(signoff)
    elif total > BUILD_UP_WORDS_WARN:
        notes.append(
            f"{total} spoken words is above about {BUILD_UP_WORDS_WARN} "
            "(about 4.5 minutes at 150 words per minute)."
        )
    jargon = missing_jargon(script, lexicon)
    if jargon:
        issues.append("Jargon is missing from lexicon.json: " + ", ".join(jargon))
    return ScriptReport(
        beats=tuple(beat_reports),
        total_words=total,
        seconds=estimated_seconds(total),
        failures=failures,
        issues=tuple(issues),
        notes=tuple(notes),
        jargon=jargon,
        script_format=script_format,
    )


def missing_jargon(script: Script, lexicon: Lexicon) -> tuple[str, ...]:
    """Find dotted, ALLCAPS, CamelCase, and code-like tokens with no lexicon entry.

    :param script: Parsed script. Spoken lines and deltas are scanned.
    :param lexicon: Terms that are already pronounced.
    :returns: Unique surface forms, in first-seen order.
    """
    found: list[str] = []
    seen: set[str] = set()
    for beat in script.beats:
        texts = [beat.spoken]
        for piece in split_delta(beat.delta):
            if not is_file_path(piece):
                texts.append(piece)
        for text in texts:
            for token in _jargon_tokens(text):
                key = token.casefold()
                if key in seen or lexicon.get(token) is not None:
                    continue
                seen.add(key)
                found.append(token)
    return tuple(found)


def mine_docs(root: Path) -> tuple[FailureFix, ...]:
    """Pair problem headings with the next why heading in each markdown file.

    :param root: Docs directory.
    :returns: Pairs in file order. A missing side is None.
    :raises ScriptError: ``root`` is not a directory.
    """
    if not root.is_dir():
        raise ScriptError(f"Docs directory not found: {root}")
    pairs: list[FailureFix] = []
    files = sorted(path for path in root.rglob("*.md") if ".git" not in path.parts)
    for path in files:
        hits = _heading_hits(path, root)
        pending: DocHit | None = None
        for hit in hits:
            if hit.kind == "problem":
                if pending is not None:
                    pairs.append(FailureFix(pending, None))
                pending = hit
                continue
            pairs.append(FailureFix(pending, hit))
            pending = None
        if pending is not None:
            pairs.append(FailureFix(pending, None))
    return tuple(pairs)


def format_report(report: ScriptReport) -> str:
    """Render a report as plain text.

    :param report: Result of :func:`review_script`.
    :returns: The text ``check`` prints.
    """
    warning_count = sum(len(beat.warnings) for beat in report.beats) + len(report.notes)
    lines = [
        f"format {report.script_format}",
        f"beats {len(report.beats)}",
        f"words {report.total_words}",
        f"seconds {report.seconds:.1f}",
        f"buts {report.failures}",
        f"warnings {warning_count}",
    ]
    for beat in report.beats:
        lines.append(f"beat {beat.index} {beat.join} {beat.words} words")
        for issue in beat.issues:
            lines.append(f"  - {issue}")
        for warning in beat.warnings:
            lines.append(f"  warn: {warning}")
    for issue in report.issues:
        lines.append(f"script: {issue}")
    for note in report.notes:
        lines.append(f"note: {note}")
    if report.jargon:
        lines.append("jargon: " + ", ".join(report.jargon))
    lines.append("OK" if report.ok else "FAIL")
    return "\n".join(lines)


def format_mine(pairs: tuple[FailureFix, ...]) -> str:
    """Render mined pairs as ``path:line`` lines.

    :param pairs: Result of :func:`mine_docs`.
    :returns: Plain text.
    """
    if not pairs:
        return "No problem or why headings."
    lines: list[str] = []
    for pair in pairs:
        problem = _format_hit(pair.problem) if pair.problem else "(no problem heading)"
        fix = _format_hit(pair.fix) if pair.fix else "(no why heading)"
        lines.append(f"pair {problem} -> {fix}")
    return "\n".join(lines)


def _format_hit(hit: DocHit) -> str:
    """Format one heading as path, line, and title.

    :param hit: A docs heading.
    :returns: ``path:line title``.
    """
    return f"{hit.path}:{hit.line} {hit.title}"


def _heading_hits(path: Path, root: Path) -> list[DocHit]:
    """Collect problem and why headings from one file.

    :param path: Markdown file.
    :param root: Directory the displayed path is relative to.
    :returns: Hits in line order.
    """
    hits: list[DocHit] = []
    displayed = str(path.relative_to(root))
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match is None:
            continue
        kind = _heading_kind(match.group(2))
        if kind is None:
            continue
        hits.append(DocHit(displayed, number, kind, match.group(2).strip()))
    return hits


def _heading_kind(title: str) -> str | None:
    """Classify a heading as a problem, a why, or neither.

    :param title: Heading text without the hashes.
    :returns: ``problem``, ``why``, or None. A heading that starts with "why" is a why.
    """
    lowered = title.strip().lower()
    if re.match(r"why\b", lowered):
        return "why"
    if re.search(r"\b(problem|failure)\b", lowered):
        return "problem"
    return None


def _spoken_form_issues(
    index: int,
    join: str,
    spoken: str,
    script_format: str = FORMAT_SHORT,
) -> list[str]:
    """Check the first word against the join.

    :param index: Beat number.
    :param join: Join field.
    :param spoken: Spoken line.
    :param script_format: ``short`` or ``build-up``.
    :returns: Problems for this line.
    """
    first = _first_word(spoken).lower()
    if join == "but":
        if first == "but":
            return []
        if script_format == FORMAT_BUILD_UP and _but_has_recap(spoken, first):
            return []
        return [f"but is spoken as {first!r}. Start the line with But."]
    if join == "therefore" and first not in {"therefore", "so"}:
        return [f"therefore is spoken as {first!r}. Start the line with So (recommended) or Therefore."]
    if join == "caveat" and first in {"but", "therefore", "so"}:
        return ["A caveat does not start with But, Therefore, or So."]
    return []


def _but_has_recap(spoken: str, first: str) -> bool:
    """Return whether a but line opens with a short recap, then but.

    :param spoken: Spoken line.
    :param first: First word, already lowercased.
    :returns: True for ``Now X, but Y`` or ``Finally, ... but Y``.
    """
    if first not in {"now", "finally"}:
        return False
    words = {part.strip(".,;:!?\"'").lower() for part in spoken.split()}
    return "but" in words


def _has_punchline(spoken: str) -> bool:
    """Return whether a therefore line names the feature at the end.

    :param spoken: Spoken line.
    :returns: True when the line ends with ``That's X.`` or ``Those are X.``.
    """
    return PUNCHLINE_RE.search(spoken.strip()) is not None


def _banned_issues(spoken: str) -> list[str]:
    """Flag feature-list joins hiding in the spoken line.

    :param spoken: Spoken line.
    :returns: One message per banned phrase that occurs.
    """
    lowered = spoken.lower()
    found: list[str] = []
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            found.append(f"banned join {phrase!r}.")
    if re.search(r"\balso\b", lowered):
        found.append("banned join 'also'.")
    if re.match(r"\s*next\b", lowered):
        found.append("banned join 'next'.")
    return found


def _signoff_issue(artifact: str, spoken: str) -> str:
    """Return a message when the congratulations line does not name the artifact.

    :param artifact: Artifact heading.
    :param spoken: Last spoken line.
    :returns: A problem message, or an empty string when the line matches.
    """
    expected = artifact.strip().rstrip(".").casefold()
    match = re.search(r"congratulations,\s+you built\s+(.+?)[.!]", spoken, flags=re.IGNORECASE)
    if match is None or not expected:
        return "The sign-off must contain 'Congratulations, you built X.' with X equal to the artifact."
    if match.group(1).strip().casefold() != expected:
        return (
            "The sign-off names "
            f"{match.group(1).strip()!r}, and the artifact is {artifact.strip()!r}."
        )
    return ""


def _first_word(text: str) -> str:
    """Return the first word, without punctuation.

    :param text: A line.
    :returns: The first word, or an empty string.
    """
    parts = text.split()
    if not parts:
        return ""
    return parts[0].strip(".,;:!?\"'")


def _jargon_tokens(text: str) -> list[str]:
    """Return tokens that look like jargon.

    :param text: Spoken line or delta.
    :returns: Surface forms, including duplicates. The caller de-duplicates.
    """
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(text):
        raw = match.group(1) if match.group(1) is not None else match.group(0)
        token = raw.strip()
        if not token or not _looks_like_jargon(token):
            continue
        tokens.append(token)
    return tokens


def _looks_like_jargon(token: str) -> bool:
    """Decide whether one token is a pronunciation candidate.

    :param token: The token without backticks.
    :returns: True when the checker should look for a lexicon entry.
    """
    body = token.strip("`")
    if not body:
        return False
    if "." in body and re.search(r"\.[A-Za-z0-9]{1,8}$", body):
        return True
    if "_" in body:
        return True
    if re.fullmatch(r"[A-Z]{2,}[0-9]*", body):
        return True
    if re.search(r"[A-Z]", body[1:]) and re.search(r"[a-z]", body):
        return True
    return bool(body.islower() and len(body) >= 8 and body.endswith(("file", "files")))


@app.command()
def check(
    script: Path = typer.Argument(..., help="Path to script.md."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon", help="Lexicon JSON path."),
) -> None:
    """Parse script.md and print the budget report. Exit 1 when it fails."""
    if not script.is_file():
        logger.error("Error: script not found: {}", script)
        raise typer.Exit(code=2)
    try:
        parsed = parse_script(script.read_text(encoding="utf-8"))
        words = load_lexicon(lexicon)
    except (ScriptError, LexiconError) as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    report = review_script(parsed, words)
    typer.echo(format_report(report))
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def mine(
    docs: Path = typer.Argument(..., help="Docs directory to scan for problem and why headings."),
) -> None:
    """List candidate failure/fix pairs as path:line."""
    try:
        pairs = mine_docs(docs)
    except ScriptError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    typer.echo(format_mine(pairs))


if __name__ == "__main__":
    app()
