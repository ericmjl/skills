"""Score a beat against Whisper and decide whether to synthesize it again.

The comparison is a word error rate against the line the listener should
hear. A take above the threshold is re-synthesized, up to a fixed number of
attempts. Every attempt is written to ``voice_log.json``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

WORD_RE = re.compile(r"[a-z0-9']+")
DEFAULT_ATTEMPTS = 3
DEFAULT_WER = 0.25


def normalize_words(text: str) -> list[str]:
    """Lowercase a line and drop punctuation and sound codes.

    :param text: Expected line or a transcript.
    :returns: Words used for the error rate.
    """
    without_codes = re.sub(r"\[[A-Za-z]{1,3}[0-2]?\]", " ", text)
    return WORD_RE.findall(without_codes.lower())


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Return the word error rate of ``hypothesis`` against ``reference``.

    :param reference: The line that should have been spoken.
    :param hypothesis: Whisper's transcript.
    :returns: Edit distance divided by the reference length. An empty
        reference is 0 when the hypothesis is also empty, and 1 otherwise.
    """
    ref = normalize_words(reference)
    hyp = normalize_words(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def take_decision(wer: float, *, attempt: int, attempts: int, threshold: float) -> str:
    """Decide what to do with one scored take.

    :param wer: Word error rate of this take.
    :param attempt: 1-based attempt number.
    :param attempts: How many takes are allowed.
    :param threshold: Takes at or under this rate are accepted.
    :returns: ``accept``, ``retry``, or ``keep-best``.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1.")
    if wer <= threshold:
        return "accept"
    if attempt < attempts:
        return "retry"
    return "keep-best"


def review_takes(
    wav_path: Path,
    expected: str,
    *,
    synthesize: Callable[[], None],
    transcribe: Callable[[Path], str],
    attempts: int = DEFAULT_ATTEMPTS,
    threshold: float = DEFAULT_WER,
) -> dict[str, object]:
    """Synthesize, score, and retry. Leave the lowest-error WAV on disk.

    :param wav_path: Where each take is written.
    :param expected: Text the transcript is compared to.
    :param synthesize: Writes ``wav_path``. Called once per attempt.
    :param transcribe: Returns the transcript of ``wav_path``.
    :param attempts: Maximum takes.
    :param threshold: Accept a take at or under this word error rate.
    :returns: One beat record for ``voice_log.json``.
    """
    log: list[dict[str, object]] = []
    best_wer = 1.0
    best_bytes = b""
    best_transcript = ""
    accepted = False
    for attempt in range(1, attempts + 1):
        synthesize()
        transcript = transcribe(wav_path).strip()
        wer = round(word_error_rate(expected, transcript), 4)
        decision = take_decision(wer, attempt=attempt, attempts=attempts, threshold=threshold)
        current = wav_path.read_bytes()
        if not best_bytes or wer < best_wer:
            best_wer = wer
            best_bytes = current
            best_transcript = transcript
        log.append(
            {
                "n": attempt,
                "wer": wer,
                "transcript": transcript,
                "decision": decision,
            }
        )
        if decision == "accept":
            accepted = True
            break
        if decision == "keep-best":
            break
    if best_bytes and wav_path.read_bytes() != best_bytes:
        wav_path.write_bytes(best_bytes)
    return {
        "expected": expected,
        "attempts": log,
        "wer": best_wer,
        "transcript": best_transcript,
        "accepted": accepted,
    }


def record_voice_log(path: Path, beat_index: int, entry: dict[str, object]) -> None:
    """Insert one beat's check into ``voice_log.json``.

    A later check of the same beat replaces the earlier record.

    :param path: ``voice_log.json`` in the project.
    :param beat_index: Beat number.
    :param entry: Record from :func:`review_takes`, without the index.
    """
    document: dict[str, object] = {"beats": []}
    if path.is_file():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and isinstance(loaded.get("beats"), list):
            document = loaded
    beats = [
        row
        for row in document.get("beats", [])
        if isinstance(row, dict) and row.get("index") != beat_index
    ]
    beats.append({"index": beat_index, **entry})
    beats.sort(key=lambda row: int(row["index"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"beats": beats}, indent=2) + "\n", encoding="utf-8")


def _edit_distance(left: list[str], right: list[str]) -> int:
    """Return the Levenshtein distance between two word lists.

    :param left: Reference words.
    :param right: Hypothesis words.
    :returns: The number of insertions, deletions, and substitutions.
    """
    previous = list(range(len(right) + 1))
    for i, token in enumerate(left, start=1):
        current = [i]
        for j, other in enumerate(right, start=1):
            cost = 0 if token == other else 1
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]
