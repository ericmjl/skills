"""Tests for the script budget checker and the docs miner."""

from __future__ import annotations

from pathlib import Path

from check_script import (
    app,
    format_report,
    mine_docs,
    missing_jargon,
    review_joins,
    review_script,
)
from normalize import Lexicon, dump_lexicon, load_lexicon
from timeline import Beat, Script, parse_script
from typer.testing import CliRunner

SKILL = Path(__file__).resolve().parents[1]
EXAMPLE = SKILL / "examples" / "ds-bootstrap-build-up" / "script.md"
RUNNER = CliRunner()


def test_caveat_does_not_break_alternation_and_two_buts_need_one() -> None:
    """A caveat is invisible to but/therefore, and but-but needs it in between."""
    assert review_joins(("none", "but", "therefore", "caveat", "but", "none")) == ()
    assert review_joins(("none", "but", "caveat", "but", "none")) == ()
    assert review_joins(("none", "therefore", "caveat", "none")) == ()
    repeated = review_joins(("none", "but", "but", "none"))
    assert any("around a caveat" in item for item in repeated)
    two_therefores = review_joins(("none", "therefore", "caveat", "therefore", "none"))
    assert any("repeats therefore" in item for item in two_therefores)
    loose = review_joins(("none", "but", "caveat", "therefore", "none"))
    assert any("must follow a therefore" in item for item in loose)


def test_so_is_the_recommended_therefore_opener() -> None:
    """So is the recommended therefore opener. Repeated Therefore still warns."""
    mixed = _shipping_script(openers=("Therefore", "So", "Therefore", "So"))
    report = review_script(mixed, _empty_lexicon())
    assert report.ok, report
    assert report.failures == 4
    assert report.total_words == 160
    assert report.seconds == 64.0
    all_so = _shipping_script(openers=("So", "So", "So", "So"))
    so_report = review_script(all_so, _empty_lexicon())
    assert so_report.ok, so_report
    assert so_report.notes == ()
    same = _shipping_script(openers=("Therefore", "Therefore", "Therefore", "Therefore"))
    same_report = review_script(same, _empty_lexicon())
    assert same_report.ok, same_report
    assert any("therefore" in item.lower() for item in same_report.notes)
    wrong = _shipping_script(openers=("Therefore", "Then", "Therefore", "So"))
    wrong_report = review_script(wrong, _empty_lexicon())
    assert any("spoken as 'then'" in item.issues[0] for item in wrong_report.beats if item.issues)


def test_beat_length_is_a_warning() -> None:
    """A beat outside 15 to 18 words does not fail a script that otherwise ships."""
    script = _shipping_script(openers=("Therefore", "So", "Therefore", "So"))
    long = script.beats[1].spoken + " extra words now"
    beats = list(script.beats)
    beats[1] = beats[1].with_spoken(long)
    report = review_script(script.with_beats(tuple(beats)), _empty_lexicon())
    assert report.ok, report
    assert any("words" in item for item in report.beats[1].warnings)
    assert report.beats[1].issues == ()


def test_banned_joins_and_missing_jargon() -> None:
    """Feature-list words and unknown code-like tokens are reported."""
    script = _shipping_script(openers=("Therefore", "So", "Therefore", "So"))
    spoken = script.beats[1].spoken.replace("the", "and then the", 1)
    # Keep the line inside the word budget after the insertion by dropping two words.
    words = spoken.split()
    spoken = " ".join(words[:16])
    beats = list(script.beats)
    beats[1] = beats[1].with_spoken(spoken + " also next")
    # The line above is deliberately long so the banned words are present.
    # Word-count failure is separate; this test only checks the banned phrases
    # and the jargon scan on a hand-built line.
    flagged = review_script(script.with_beats(tuple(beats)), _empty_lexicon())
    beat_issues = " ".join(flagged.beats[1].issues)
    assert "and then" in beat_issues
    assert "also" in beat_issues
    plain = "But the next rain finds the crack and soaks the room tonight."
    quiet = review_script(
        script.with_beats((script.beats[0],) + (beats[1].with_spoken(plain),) + script.beats[2:]),
        _empty_lexicon(),
    )
    assert all("banned join 'next'" not in item for item in quiet.beats[1].issues)
    jargon_script = script.with_beats(
        (
            script.beats[0].with_spoken("You edit AGENTS.md before the first rain can fill the tank."),
            *script.beats[1:],
        )
    )
    found = missing_jargon(jargon_script, _empty_lexicon())
    assert "AGENTS.md" in found
    known = missing_jargon(jargon_script, load_lexicon(SKILL / "lexicon.json"))
    assert "AGENTS.md" not in known
    assert "lockfile" in missing_jargon(
        script.with_beats(
            (
                script.beats[0],
                script.beats[1].with_delta("lockfile"),
                *script.beats[2:],
            )
        ),
        _empty_lexicon(),
    )


def test_signoff_must_name_the_artifact() -> None:
    """The congratulations sentence has to repeat the artifact heading."""
    script = _shipping_script(openers=("Therefore", "So", "Therefore", "So"))
    renamed = Script(artifact="a different pump", voice="eric", beats=script.beats)
    report = review_script(renamed, _empty_lexicon())
    assert any("sign-off" in item.lower() or "artifact" in item for item in report.issues)


def test_short_defaults_are_unchanged() -> None:
    """A short still needs 10-12 beats, 150-216 words, 4 or 5 buts, and the sign-off."""
    script = _shipping_script(openers=("So", "So", "So", "So"))
    assert script.script_format == "short"
    report = review_script(script, _empty_lexicon())
    assert report.ok, format_report(report)
    last = script.beats[-1].with_spoken("And with that, the tank holds water.")
    tiny = Script(
        artifact="a tiny pump",
        voice="eric",
        beats=(script.beats[0], last),
        script_format="short",
    )
    tiny_report = review_script(tiny, _empty_lexicon())
    assert tiny_report.ok is False
    blob = " ".join(tiny_report.issues).lower()
    assert "beats" in blob
    assert "sign-off" in blob or "congratulations" in blob


def test_build_up_example_passes_check_script() -> None:
    """The porch-swing DS Bootstrap script is inside the build-up rules."""
    script = parse_script(EXAMPLE.read_text(encoding="utf-8"))
    report = review_script(script, load_lexicon(SKILL / "lexicon.json"))
    assert report.ok, format_report(report)
    assert report.issues == ()
    assert report.jargon == ()
    assert all(beat.issues == () for beat in report.beats)
    assert script.script_format == "build-up"
    assert report.failures == 14
    text = format_report(report)
    summary = text.split("beat ", maxsplit=1)[0]
    assert f"buts {report.failures}" in summary
    assert "failures" not in summary
    assert "OK" in text


def test_check_cli_accepts_the_build_up_example() -> None:
    """The Typer command exits 0 on the worked build-up example."""
    result = RUNNER.invoke(app, ["check", str(EXAMPLE), "--lexicon", str(SKILL / "lexicon.json")])
    assert result.exit_code == 0, result.output
    assert "OK" in result.output
    assert "FAIL" not in result.output
    assert "failures 14" not in result.output
    assert "buts 14" in result.output


def test_missing_punchline_warns_on_build_up() -> None:
    """A build-up therefore without That's X. or Those are X. is a warning."""
    script = _build_up_miniscript(punchline=False)
    report = review_script(script, _empty_lexicon())
    assert report.ok, format_report(report)
    therefore = next(item for item in report.beats if item.join == "therefore")
    assert any("punchline" in item.lower() for item in therefore.warnings)
    named = review_script(_build_up_miniscript(punchline=True), _empty_lexicon())
    named_therefore = next(item for item in named.beats if item.join == "therefore")
    assert all("punchline" not in item.lower() for item in named_therefore.warnings)


def test_build_up_allows_now_and_finally_but_recap() -> None:
    """A build-up but may open with Now X, but Y or Finally, ..."""
    script = _build_up_miniscript(punchline=True)
    beats = list(script.beats)
    beats[1] = beats[1].with_spoken(
        "Finally, the tank holds water, but the dirt still washes in tonight."
    )
    report = review_script(script.with_beats(tuple(beats)), _empty_lexicon())
    assert report.beats[1].issues == (), report.beats[1].issues
    short = _shipping_script(openers=("So", "So", "So", "So"))
    short_beats = list(short.beats)
    short_beats[1] = short_beats[1].with_spoken(
        "Now the first rain runs off the roof, but the dirt comes into the tank"
    )
    short_report = review_script(short.with_beats(tuple(short_beats)), _empty_lexicon())
    assert any("Start the line with But" in item for item in short_report.beats[1].issues)


def test_mine_pairs_problem_headings_with_the_next_why(tmp_path: Path) -> None:
    """Each problem heading pairs with the following why, with path:line."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text(
        "# The problem with pip\n\nBody.\n\n## Why pixi\n\nBody.\n\n# Another failure\n",
        encoding="utf-8",
    )
    pairs = mine_docs(docs)
    assert len(pairs) == 2
    assert pairs[0].problem is not None and pairs[0].fix is not None
    assert pairs[0].problem.path == "guide.md"
    assert pairs[0].problem.line == 1
    assert pairs[0].fix.line == 5
    assert pairs[0].fix.title == "Why pixi"
    assert pairs[1].problem is not None and pairs[1].fix is None
    assert pairs[1].problem.line == 9


def test_check_cli_exits_nonzero_on_a_short_script(tmp_path: Path) -> None:
    """The Typer command prints the report and fails a script under the budget."""
    script = tmp_path / "script.md"
    script.write_text(
        """# Artifact

a tiny pump

# Voice

eric

# Beats

## Beat 0

- join: none
- spoken: You dig a hole.
- visual: A tank.
- number: none
- source: none
- delta: A tank

## Beat 1

- join: none
- spoken: Congratulations, you built a tiny pump.
- visual: Title.
- number: none
- source: none
- delta: Title card
""",
        encoding="utf-8",
    )
    result = RUNNER.invoke(app, ["check", str(script), "--lexicon", str(SKILL / "lexicon.json")])
    assert result.exit_code == 1, result.output
    assert "FAIL" in result.output
    assert "words" in result.output


def test_import_command_merges_a_term_map(tmp_path: Path) -> None:
    """pronounce.py import adds a map entry and bumps the lexicon version."""
    from pronounce import app as pronounce_app

    lexicon = tmp_path / "lexicon.json"
    dump_lexicon(Lexicon(version=1, updated="2026-11-20", entries=()), lexicon)
    source = tmp_path / "pronunciations.json"
    source.write_text('{"widget": "wih jit"}', encoding="utf-8")
    result = RUNNER.invoke(
        pronounce_app,
        ["import", str(source), "--lexicon", str(lexicon), "--updated", "2026-11-20"],
    )
    assert result.exit_code == 0, result.output
    loaded = load_lexicon(lexicon)
    assert loaded.version == 2
    assert loaded.get("widget") is not None
    assert loaded.get("widget").respelling == "wih jit"


def _empty_lexicon() -> Lexicon:
    """Return a lexicon with no entries.

    :returns: Version 1, empty.
    """
    return Lexicon(version=1, updated="2026-11-20", entries=())


def _build_up_miniscript(*, punchline: bool) -> Script:
    """Build a four-beat porch-swing script.

    :param punchline: Whether the therefore line names the feature at the end.
    :returns: A build-up script the checker should accept, with a warning when
        the punchline is missing.
    """
    therefore = (
        "So you add a first flush pipe. That's a first flush."
        if punchline
        else "So you add a first flush pipe that dumps the opening wash."
    )
    beats = (
        Beat(
            index=0,
            join="none",
            spoken="You dig a hole and drop in a tank today.",
            visual="A tank.",
            number="none",
            source="none",
            delta="A tank",
        ),
        Beat(
            index=1,
            join="but",
            spoken="Now the tank holds water, but the dirt still washes in tonight.",
            visual="Dirty water.",
            number="none",
            source="none",
            delta="none",
        ),
        Beat(
            index=2,
            join="therefore",
            spoken=therefore,
            visual="A pipe.",
            number="none",
            source="none",
            delta="A pipe",
        ),
        Beat(
            index=3,
            join="none",
            spoken="And with that, the water stays drinkable.",
            visual="Title.",
            number="none",
            source="none",
            delta="none",
        ),
    )
    return Script(
        artifact="a drinkable tank",
        voice="eric",
        beats=beats,
        script_format="build-up",
    )


def _shipping_script(*, openers: tuple[str, str, str, str]) -> Script:
    """Build a 10-beat script inside the word, failure, and sign-off budget.

    :param openers: First word of each therefore beat, in order.
    :returns: A script review_script should accept when the openers vary.
    """
    joins = (
        "none",
        "but",
        "therefore",
        "but",
        "therefore",
        "but",
        "therefore",
        "but",
        "therefore",
        "none",
    )
    lines = [
        _words("You dig a hole and set a tank before the first rain can fill it now"),
        _words("But the first rain runs off the roof and brings the dirt into the tank"),
        _words(f"{openers[0]} you add a first flush pipe that dumps the opening minute of wash"),
        _words("But the soil wants to slide off the pitch and bury the pipe you just set"),
        _words(f"{openers[1]} you terrace the slope in short steps and the loose dirt stays put"),
        _words("But water still finds the wall and soaks the room behind the new terrace"),
        _words(f"{openers[2]} you set a drain and a sheet so the wall stays dry after rain"),
        _words("But the sheet fails when a root lifts it and opens a seam at the corner"),
        _words(f"{openers[3]} you pin the sheet at the seam and the root can no longer lift it"),
        _words("Clear water now still reaches the tank after rain today. Congratulations, you built a tiny pump."),
    ]
    beats = tuple(
        Beat(
            index=index,
            join=join,
            spoken=line,
            visual=f"Picture {index}.",
            number="none",
            source="none",
            delta=f"piece {index}",
        )
        for index, (join, line) in enumerate(zip(joins, lines, strict=True))
    )
    return Script(artifact="a tiny pump", voice="eric", beats=beats)


def _words(text: str) -> str:
    """Pad or trim a line to 16 words.

    :param text: A line that is already close to 16 words.
    :returns: Exactly 16 words.
    """
    parts = text.split()
    if len(parts) < 16:
        parts = parts + ["now"] * (16 - len(parts))
    return " ".join(parts[:16])
