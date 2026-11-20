"""Tests for per-take pronunciation QA. Models are mocked or unused."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

from normalize import Entry, Lexicon
from pronunciation_qa import (
    Alignment,
    WordSpan,
    beat_report,
    clip_span,
    competitor_line,
    greedy_ctc_decode,
    ipa_phones,
    phones_match,
    review_pronunciation_takes,
    score_alignment,
    select_span,
    sum_forced_text_logprobs,
    take_decision,
    take_rank,
    whisper_force_tokens,
    words_from_whisper,
    write_beat_report,
)

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "pronunciation_qa.py"


def test_optional_models_are_not_imported_at_module_level() -> None:
    """torch, whisper, and transformers stay out of the module body."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".", maxsplit=1)[0])
    assert "torch" not in names
    assert "whisper" not in names
    assert "transformers" not in names


def test_greedy_ctc_drops_pad_s_unk_and_collapses_repeats() -> None:
    """Blank, start, and unk tokens leave the phone sequence. Repeats collapse."""
    vocab = {"<pad>": 0, "<s>": 1, "<unk>": 2, "l": 3, "ɪ": 4, "v": 5, "aɪ": 6}
    phones = greedy_ctc_decode([1, 0, 3, 3, 4, 5, 0, 2], vocab)
    assert phones == ("l", "ɪ", "v")
    diphthong = greedy_ctc_decode([3, 6, 5], vocab)
    assert diphthong == ("l", "aɪ", "v")
    assert phones_match(("l", "ɪ", "v"), "lɪv")
    assert not phones_match(("l", "aɪ", "v"), "lɪv")
    assert ipa_phones("lɪv ɪn") == ("l", "ɪ", "v", "ɪ", "n")


def test_first_and_last_word_matching_catches_dropped_edges() -> None:
    """A missing opening So or a cut-off That's X. fails even when the ratio is high."""
    spoken = "So GitHub Actions runs the same checks. That's continuous integration."
    dropped_so = score_alignment(
        "GitHub Actions runs the same checks. That's continuous integration.",
        spoken=spoken,
        respelled=spoken,
    )
    assert dropped_so.first_ok is False
    assert dropped_so.last_ok is True
    assert dropped_so.ratio >= 0.9
    assert dropped_so.passed(0.9) is False
    cut_off = score_alignment(
        "So GitHub Actions runs the same checks. That's",
        spoken=spoken,
        respelled=spoken,
    )
    assert cut_off.first_ok is True
    assert cut_off.last_ok is False
    assert cut_off.passed(0.9) is False
    squashed = score_alignment(
        "So GitHub Actions runs the same checks thatscontinuousintegration",
        spoken=spoken,
        respelled=spoken,
    )
    assert squashed.last_ok is True
    intact = score_alignment(spoken, spoken=spoken, respelled="So ghit hub Actions runs.")
    assert intact.first_ok is True
    assert intact.passed(0.9) is True


def test_span_selection_pads_whisper_timestamps() -> None:
    """A lexicon term maps onto Whisper words, then the clip grows by 0.08 s."""
    words = (
        WordSpan("settings", 0.10, 0.40),
        WordSpan("live", 0.40, 0.62),
        WordSpan("in", 0.62, 0.74),
        WordSpan("pyproject", 0.74, 1.20),
    )
    span = select_span(words, "live in")
    assert span == (0.40, 0.74)
    assert clip_span(0.40, 0.74, duration=2.0) == (0.32, 0.82)
    assert clip_span(0.02, 1.96, duration=2.0) == (0.0, 2.0)
    hyphen = (
        WordSpan("a", 0.0, 0.1),
        WordSpan("two-gigabyte", 0.1, 0.5),
        WordSpan("CSV", 0.5, 0.8),
    )
    assert select_span(hyphen, "two-gigabyte") == (0.1, 0.5)
    assert select_span(words, "missing term") is None


def test_misheard_substitution_builds_the_competitor_line() -> None:
    """A competitor line swaps in lexicon mishearings and is None when none apply."""
    lex = _lex(
        Entry("two-gigabyte", misheard="toe gigabyte", respelling="two gigabyte"),
        Entry("hard-codes", misheard="card codes", respelling="hard codes"),
        Entry("Diataxis", misheard="dee ataxis", respelling="dye uh tax iss"),
        Entry("pixi", respelling="pixie"),
    )
    line = "But git add dot committed a two-gigabyte CSV that hard-codes Diataxis."
    assert competitor_line(line, lex) == (
        "But git add dot committed a toe gigabyte CSV that card codes dee ataxis."
    )
    assert competitor_line("Install with pixi.", lex) is None


def test_forced_token_sequence_and_text_logprob_sum() -> None:
    """Tokens are sot + encode(' ' + text) + eot. The sum is over the text tokens."""
    tokenizer = SimpleNamespace(
        sot_sequence_including_notimestamps=[50258, 50259, 50363],
        eot=50257,
        encode=lambda text: [10, 11] if text.startswith(" ") else [0],
    )
    tokens, text_start, text_len = whisper_force_tokens(tokenizer, "hello there")
    assert tokens == [50258, 50259, 50363, 10, 11, 50257]
    assert text_start == 3
    assert text_len == 2
    log_probs = [[0.0] * 50300 for _ in range(5)]
    log_probs[2][10] = -1.0
    log_probs[3][11] = -2.5
    assert sum_forced_text_logprobs(log_probs, tokens, text_start=3, text_len=2) == -3.5


def test_whisper_word_extraction_and_report_shape(tmp_path: Path) -> None:
    """Whisper segments flatten to word spans, and the JSON report has a stable shape."""
    result = {
        "text": "So you add a pipe.",
        "segments": [
            {
                "words": [
                    {"word": " So", "start": 0.0, "end": 0.2},
                    {"word": " you", "start": 0.2, "end": 0.35},
                    {"word": " add", "start": 0.35, "end": 0.5},
                    {"word": " a", "start": 0.5, "end": 0.55},
                    {"word": " pipe.", "start": 0.55, "end": 0.9},
                ]
            }
        ],
    }
    words = words_from_whisper(result)
    assert [item.word for item in words] == ["So", "you", "add", "a", "pipe."]
    alignment = Alignment(first_ok=True, last_ok=True, ratio=1.0, transcript="So you add a pipe.")
    report = beat_report(
        spoken="So you add a pipe.",
        respelled="So you add a pipe.",
        competitor=None,
        attempts=(
            {
                "n": 1,
                "transcript": alignment.transcript,
                "first_ok": True,
                "last_ok": True,
                "ratio": 1.0,
                "forced": {
                    "target": -1.0,
                    "competitor": None,
                    "margin": None,
                    "skipped": True,
                },
                "phonemes": [],
                "decision": "accept",
            },
        ),
        accepted=True,
        alignment=alignment,
    )
    assert report["signal_not_proof"] is True
    assert report["spoken"] == "So you add a pipe."
    assert report["accepted"] is True
    assert "attempts" in report
    assert "ratio" in report
    path = tmp_path / "00.qa.json"
    write_beat_report(path, report)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["signal_not_proof"] is True
    assert saved["attempts"][0]["n"] == 1


def test_review_retries_until_edges_pass_and_keeps_the_best(tmp_path: Path) -> None:
    """A dropped So is retried. Ranking is (first_ok + last_ok, ratio), not WER."""
    wav = tmp_path / "18.wav"
    transcripts = iter(
        [
            "GitHub Actions runs the same checks. That's continuous integration.",
            "So GitHub Actions runs the same checks. That's continuous integration.",
        ]
    )

    def synthesize() -> None:
        wav.write_bytes(f"take-{wav.exists()}".encode())

    def transcribe(_path: Path) -> str:
        return next(transcripts)

    spoken = "So GitHub Actions runs the same checks. That's continuous integration."
    record = review_pronunciation_takes(
        wav,
        spoken=spoken,
        respelled=spoken,
        lexicon=_lex(),
        synthesize=synthesize,
        transcribe=transcribe,
        score_forced=lambda *_args, **_kwargs: {
            "target": -1.0,
            "competitor": -4.0,
            "margin": 3.0,
            "skipped": False,
        },
        score_phonemes=lambda *_args, **_kwargs: [],
        attempts=4,
        min_ratio=0.9,
    )
    assert record["accepted"] is True
    assert len(record["attempts"]) == 2
    assert record["attempts"][0]["decision"] == "retry"
    assert record["attempts"][0]["first_ok"] is False
    assert record["attempts"][1]["decision"] == "accept"
    assert record["ratio"] == record["attempts"][1]["ratio"]
    assert wav.read_bytes() == b"take-True"


def test_keep_best_ranks_by_edges_then_ratio(tmp_path: Path) -> None:
    """When tries run out, the take with more intact edges wins over a higher ratio."""
    wav = tmp_path / "00.wav"
    n = {"n": 0}

    def synthesize() -> None:
        n["n"] += 1
        wav.write_bytes(f"take-{n['n']}".encode())

    transcripts = iter(
        [
            "you add a pipe that's a first",
            "So you add a pipe that's",
        ]
    )

    def transcribe(_path: Path) -> str:
        return next(transcripts)

    spoken = "So you add a pipe. That's a first flush."
    record = review_pronunciation_takes(
        wav,
        spoken=spoken,
        respelled=spoken,
        lexicon=_lex(),
        synthesize=synthesize,
        transcribe=transcribe,
        score_forced=lambda *_args, **_kwargs: {
            "target": None,
            "competitor": None,
            "margin": None,
            "skipped": True,
        },
        score_phonemes=lambda *_args, **_kwargs: [],
        attempts=2,
        min_ratio=0.9,
    )
    assert record["accepted"] is False
    first = record["attempts"][0]
    second = record["attempts"][1]
    assert first["first_ok"] is False
    assert second["first_ok"] is True
    assert take_rank(second["first_ok"], second["last_ok"], second["ratio"]) > take_rank(
        first["first_ok"], first["last_ok"], first["ratio"]
    )
    assert record["first_ok"] is True
    assert wav.read_bytes() == b"take-2"
    assert take_decision(
        Alignment(first_ok=True, last_ok=True, ratio=0.95, transcript="x"),
        attempt=1,
        attempts=4,
        min_ratio=0.9,
    ) == "accept"
    assert take_decision(
        Alignment(first_ok=False, last_ok=True, ratio=0.99, transcript="x"),
        attempt=1,
        attempts=4,
        min_ratio=0.9,
    ) == "retry"
    assert take_decision(
        Alignment(first_ok=False, last_ok=True, ratio=0.99, transcript="x"),
        attempt=4,
        attempts=4,
        min_ratio=0.9,
    ) == "keep-best"


def _lex(*entries: Entry) -> Lexicon:
    """Build a lexicon from entries.

    :param entries: Entries to add, in order.
    :returns: A lexicon whose version equals one plus the number of entries.
    """
    lex = Lexicon(version=1, updated="2026-11-20", entries=())
    for entry in entries:
        lex = lex.add(entry, updated="2026-11-20")
    return lex
