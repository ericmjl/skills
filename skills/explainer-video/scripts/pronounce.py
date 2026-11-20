#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12", "pyyaml>=6", "loguru>=0.7"]
# ///
"""Add, correct, and apply the explainer pronunciation lexicon.

Run from anywhere:

    uv run skills/explainer-video/scripts/pronounce.py --help

``resynth --text-only`` rewrites the spoken line for the beats a term hits.
Without ``--text-only`` it also synthesizes those beats. Synthesis needs the
voice's model on this machine; this script does not install it.
"""

from __future__ import annotations

import shutil
import sys
import wave
from datetime import date
from pathlib import Path

import typer
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from normalize import (
    Entry,
    LexiconError,
    dump_lexicon,
    load_lexicon,
    load_pronunciations,
)
from timeline import ScriptError, parse_script
from voices import VoiceError, get_voice, load_registry, target_for

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON = SKILL_ROOT / "lexicon.json"
DEFAULT_VOICES = SKILL_ROOT / "voices.yaml"

app = typer.Typer(add_completion=False, no_args_is_help=True)
logger.remove()
logger.add(sys.stderr, format="{message}")


def _lexicon_option() -> Path:
    """Default lexicon path.

    :returns: The skill lexicon.
    """
    return DEFAULT_LEXICON


@app.command("list")
def list_entries(
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon", help="Lexicon JSON path."),
) -> None:
    """Print every entry."""
    lex = _load(lexicon)
    typer.echo(f"version {lex.version}  updated {lex.updated}  entries {len(lex.entries)}")
    for entry in lex.entries:
        flag = "listened" if entry.verified else "unverified"
        typer.echo(
            f"{entry.term}\t{entry.match}\t{flag}\t{entry.cmu or '-'}\t{entry.respelling or '-'}"
        )


@app.command()
def apply(
    text: str = typer.Argument(..., help="Spoken line to normalize."),
    target: str = typer.Option("cosyvoice3", "--target", help="cosyvoice3 or chatterbox."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon", help="Lexicon JSON path."),
) -> None:
    """Print one line after the pronunciation pass."""
    lex = _load(lexicon)
    try:
        result = lex.apply(text, target)
    except LexiconError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    for warning in result.warnings:
        logger.warning("Warning: {}", warning)
    typer.echo(result.text)


@app.command()
def add(
    term: str = typer.Argument(..., help="Written form to match."),
    cmu: str = typer.Option("", "--cmu", help="CMU tokens, for example [JH] [AE1] [K] [S]."),
    respelling: str = typer.Option("", "--respelling", help="Plain words for Chatterbox."),
    ipa: str = typer.Option("", "--ipa", help="Reference IPA. Not sent to TTS."),
    misheard: str = typer.Option("", "--misheard", help="Wrong reading used as a forced-decoding competitor."),
    note: str = typer.Option("", "--note", help="Why this reading was chosen."),
    match: str = typer.Option("insensitive", "--match", help="insensitive or exact."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon", help="Lexicon JSON path."),
    updated: str = typer.Option("", "--updated", help="YYYY-MM-DD. Default is today."),
) -> None:
    """Add a term. Refuses when the term already exists."""
    lex = _load(lexicon)
    stamp = updated or date.today().isoformat()
    entry = Entry(
        term=term,
        cmu=cmu,
        respelling=respelling,
        ipa=ipa,
        note=note,
        match=match,
        misheard=misheard,
    )
    try:
        revised = lex.add(entry, updated=stamp)
    except LexiconError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    dump_lexicon(revised, lexicon)
    typer.echo(f"Added {term}. Lexicon version {revised.version}.")


@app.command("import")
def import_pronunciations(
    source: Path = typer.Argument(..., help="A previous project's pronunciations.json."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon", help="Lexicon JSON path."),
    updated: str = typer.Option("", "--updated", help="YYYY-MM-DD. Default is today."),
) -> None:
    """Merge pronunciations.json into the lexicon.

    New terms are added. A verified entry is left alone. An unverified entry
    keeps a respelling it already has.
    """
    lex = _load(lexicon)
    stamp = updated or date.today().isoformat()
    try:
        incoming = load_pronunciations(source)
        revised, messages = lex.merge(incoming, updated=stamp)
    except LexiconError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    if revised.version != lex.version:
        dump_lexicon(revised, lexicon)
    for message in messages:
        typer.echo(message)
    typer.echo(f"Lexicon version {revised.version}.")


@app.command()
def correct(
    term: str = typer.Argument(..., help="Existing term to change."),
    cmu: str | None = typer.Option(None, "--cmu", help="Replacement CMU tokens."),
    respelling: str | None = typer.Option(None, "--respelling", help="Replacement respelling."),
    ipa: str | None = typer.Option(None, "--ipa", help="Replacement IPA."),
    misheard: str | None = typer.Option(None, "--misheard", help="Replacement misheard competitor."),
    note: str | None = typer.Option(None, "--note", help="Replacement note."),
    match: str | None = typer.Option(None, "--match", help="insensitive or exact."),
    verified: bool | None = typer.Option(None, "--verified/--unverified", help="Set the listen flag."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon", help="Lexicon JSON path."),
    updated: str = typer.Option("", "--updated", help="YYYY-MM-DD. Default is today."),
) -> None:
    """Change one entry and bump the lexicon version."""
    lex = _load(lexicon)
    changes: dict[str, object] = {}
    for key, value in (
        ("cmu", cmu),
        ("respelling", respelling),
        ("ipa", ipa),
        ("misheard", misheard),
        ("note", note),
        ("match", match),
        ("verified", verified),
    ):
        if value is not None:
            changes[key] = value
    if not changes:
        logger.error("Error: pass at least one field to change.")
        raise typer.Exit(code=2)
    stamp = updated or date.today().isoformat()
    try:
        revised = lex.correct(term, updated=stamp, **changes)
    except LexiconError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    dump_lexicon(revised, lexicon)
    saved = revised.get(term)
    if saved is None:
        logger.error("Error: {} disappeared after correct.", term)
        raise typer.Exit(code=2)
    typer.echo(
        f"Corrected {term}. Lexicon version {revised.version}. verified={saved.verified}."
    )


@app.command()
def resynth(
    project: Path = typer.Argument(..., help="Explainer project that contains script.md."),
    beat: int | None = typer.Option(None, "--beat", help="Only this beat index."),
    term: str | None = typer.Option(None, "--term", help="Only beats whose spoken line hits this term."),
    voice: str = typer.Option("", "--voice", help="Voice id. Default is the script's Voice section."),
    text_only: bool = typer.Option(False, "--text-only", help="Rewrite the line and skip TTS."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon", help="Lexicon JSON path."),
    voices: Path = typer.Option(DEFAULT_VOICES, "--voices", help="Voice registry path."),
) -> None:
    """Re-normalize the affected beats and, unless --text-only, synthesize them.

    A previous spoken text file is kept beside the new one as ``NN.spoken.prev.txt``.
    A previous WAV is kept as ``NN.prev.wav`` when synthesis runs.
    """
    script_path = project / "script.md"
    if not script_path.is_file():
        logger.error("Error: missing {}", script_path)
        raise typer.Exit(code=2)
    try:
        script = parse_script(script_path.read_text(encoding="utf-8"))
        lex = _load(lexicon)
        registry = load_registry(voices)
    except (ScriptError, LexiconError, VoiceError) as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    voice_name = voice or script.voice
    try:
        record = get_voice(registry, voice_name)
        target = target_for(str(record["model"]))
    except VoiceError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    chosen = list(script.beats)
    if beat is not None:
        chosen = [item for item in chosen if item.index == beat]
    if term is not None:
        try:
            chosen = [item for item in chosen if lex.mentions(item.spoken, term)]
        except LexiconError as exc:
            logger.error("Error: {}", exc)
            raise typer.Exit(code=2) from exc
    if not chosen:
        logger.error("Error: no beats matched. Pass a beat that exists, or a term the line contains.")
        raise typer.Exit(code=1)
    out_dir = project / "audio" / "beats"
    out_dir.mkdir(parents=True, exist_ok=True)
    from synthesize_beat import synthesize_line

    for item in chosen:
        result = lex.apply(item.spoken, target)
        for warning in result.warnings:
            logger.warning("Beat {}: {}", item.index, warning)
        text_path = out_dir / f"{item.index:02d}.spoken.txt"
        _keep_previous(text_path, text_path.with_suffix(".prev.txt"))
        text_path.write_text(result.text + "\n", encoding="utf-8")
        typer.echo(f"beat {item.index} [{target}] {result.text}")
        if text_only:
            continue
        wav_path = out_dir / f"{item.index:02d}.wav"
        _keep_previous(wav_path, out_dir / f"{item.index:02d}.prev.wav")
        synthesize_line(result.text, record, wav_path)
        typer.echo(f"  wrote {wav_path}")
    if text_only:
        typer.echo("Text only. No audio was synthesized.")
        return
    typer.echo("A/B: uv run skills/explainer-video/scripts/pronounce.py listen A.wav B.wav")


@app.command()
def listen(
    first: Path = typer.Argument(..., help="First WAV, the A take."),
    second: Path = typer.Argument(..., help="Second WAV, the B take."),
) -> None:
    """Print durations, then play A and B with ffplay when it is installed."""
    for label, path in (("A", first), ("B", second)):
        if not path.is_file():
            logger.error("Error: {} not found: {}", label, path)
            raise typer.Exit(code=2)
        typer.echo(f"{label}  {_duration_label(path)}  {path}")
    player = shutil.which("ffplay")
    if player is None:
        typer.echo("ffplay is not on PATH. Play the two files in any audio player.")
        return
    import subprocess

    for path in (first, second):
        subprocess.run([player, "-autoexit", "-nodisp", str(path)], check=False)


def _load(path: Path):
    """Load a lexicon or exit.

    :param path: Lexicon path.
    :returns: The lexicon.
    """
    try:
        return load_lexicon(path)
    except LexiconError as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc


def _keep_previous(source: Path, destination: Path) -> None:
    """Copy ``source`` to ``destination`` when ``source`` exists.

    :param source: File about to be overwritten.
    :param destination: Backup path.
    """
    if source.is_file():
        shutil.copyfile(source, destination)


def _duration_label(path: Path) -> str:
    """Describe a WAV duration.

    :param path: Audio file.
    :returns: A short duration label.
    """
    if path.suffix.lower() != ".wav":
        return "not a wav"
    with wave.open(str(path), "rb") as handle:
        seconds = handle.getnframes() / float(handle.getframerate())
    return f"{seconds:.2f}s"


if __name__ == "__main__":
    app()
