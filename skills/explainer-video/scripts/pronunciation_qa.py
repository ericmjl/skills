#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12", "loguru>=0.7"]
# ///
"""Per-take pronunciation QA for explainer beats.

Whisper timestamps, a forced-decoding margin against a misheard competitor,
and a wav2vec2 phoneme check are signals. They are not proof. An ear check
is still required: in v1 a phoneme pass on "live" still sounded wrong to Eric.

torch, openai-whisper, and transformers are optional and imported only when a
real take is scored.

    uv run --with openai-whisper --with transformers --with torch \\
      skills/explainer-video/scripts/pronunciation_qa.py PROJECT --beat 0
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import wave
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from normalize import Lexicon, LexiconError, load_lexicon
from timeline import ScriptError, parse_script

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON = SKILL_ROOT / "lexicon.json"
DEFAULT_ATTEMPTS = 4
DEFAULT_MIN_RATIO = 0.9
SPAN_PAD = 0.08
WHISPER_NAME = "small.en"
WAV2VEC_ID = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
CTC_DROP = frozenset({"<pad>", "<s>", "<unk>"})
WORD_RE = re.compile(r"[a-z0-9']+")
_IPA_UNITS = (
    "aɪ",
    "eɪ",
    "oʊ",
    "aʊ",
    "ɔɪ",
    "ɪə",
    "ʊə",
    "tʃ",
    "dʒ",
    "ɪ",
    "ʊ",
    "ə",
    "æ",
    "ɑ",
    "ɔ",
    "ɛ",
    "ʌ",
    "ʃ",
    "ʒ",
    "θ",
    "ð",
    "ŋ",
    "ɡ",
)
_MODELS: dict[str, object] = {}

app = typer.Typer(add_completion=False, no_args_is_help=True)
logger.remove()
logger.add(sys.stderr, format="{message}")


class PronunciationQAError(RuntimeError):
    """A pronunciation check could not run."""


@dataclass(frozen=True)
class WordSpan:
    """One Whisper word and its timestamps.

    :param word: Surface token, punctuation allowed.
    :param start: Start time in seconds.
    :param end: End time in seconds.
    """

    word: str
    start: float
    end: float


@dataclass(frozen=True)
class Transcript:
    """A take's transcript.

    :param text: Full text Whisper returned.
    :param words: Word timestamps, when the decoder supplied them.
    """

    text: str
    words: tuple[WordSpan, ...] = ()


@dataclass(frozen=True)
class Alignment:
    """First word, last word, and whole-line agreement for one take.

    :param first_ok: True when the opening word matches spoken or respelled.
    :param last_ok: True when the closing word, or the last 2-3 words squashed,
        matches spoken or respelled.
    :param ratio: difflib ratio of the whole line, the better of the two targets.
    :param transcript: Text that was scored.
    """

    first_ok: bool
    last_ok: bool
    ratio: float
    transcript: str

    def passed(self, min_ratio: float) -> bool:
        """Return whether this take clears the retry bar.

        :param min_ratio: Minimum whole-line ratio.
        :returns: True when both edges match and the ratio is high enough.
        """
        return self.first_ok and self.last_ok and self.ratio >= min_ratio

    def rank(self) -> tuple[int, float]:
        """Return the sort key used to keep the best take.

        :returns: Intact-edge count, then ratio.
        """
        return take_rank(self.first_ok, self.last_ok, self.ratio)


def line_words(text: str) -> list[str]:
    """Lowercase a line and drop punctuation, sound codes, and apostrophes.

    :param text: Spoken line, respelling, or transcript.
    :returns: Words used for first/last/ratio checks.
    """
    without_codes = re.sub(r"\[[A-Za-z]{1,3}[0-2]?\]", " ", text)
    return [token.replace("'", "") for token in WORD_RE.findall(without_codes.lower())]


def take_rank(first_ok: bool, last_ok: bool, ratio: float) -> tuple[int, float]:
    """Rank a take by intact edges, then by whole-line ratio.

    :param first_ok: Opening word matched.
    :param last_ok: Closing word matched.
    :param ratio: Whole-line difflib ratio.
    :returns: Higher is better.
    """
    return (int(first_ok) + int(last_ok), ratio)


def take_decision(
    alignment: Alignment,
    *,
    attempt: int,
    attempts: int,
    min_ratio: float,
) -> str:
    """Decide what to do with one scored take.

    :param alignment: First/last/ratio for this take.
    :param attempt: 1-based attempt number.
    :param attempts: How many takes are allowed.
    :param min_ratio: Accept a take at or above this whole-line ratio.
    :returns: ``accept``, ``retry``, or ``keep-best``.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1.")
    if alignment.passed(min_ratio):
        return "accept"
    if attempt < attempts:
        return "retry"
    return "keep-best"


def score_alignment(transcript: str, *, spoken: str, respelled: str) -> Alignment:
    """Score a transcript against the spoken line and the respelled line.

    :param transcript: Whisper text.
    :param spoken: Script line.
    :param respelled: Lexicon respelling of that line.
    :returns: Edge flags and the better whole-line ratio.
    """
    got = line_words(transcript)
    spoken_words = line_words(spoken)
    respelled_words = line_words(respelled)
    first = _first_ok(got, spoken_words) or _first_ok(got, respelled_words)
    last = _last_ok(got, spoken_words) or _last_ok(got, respelled_words)
    ratio = max(_ratio(got, spoken_words), _ratio(got, respelled_words))
    return Alignment(first_ok=first, last_ok=last, ratio=ratio, transcript=transcript)


def _first_ok(got: list[str], want: list[str]) -> bool:
    """Return whether the first words match.

    :param got: Transcript words.
    :param want: Expected words.
    :returns: True when both are non-empty and the first tokens are equal.
    """
    return bool(got and want and got[0] == want[0])


def _last_ok(got: list[str], want: list[str]) -> bool:
    """Return whether the last word, or the last 2-3 words squashed, match.

    :param got: Transcript words.
    :param want: Expected words.
    :returns: True on a last-word hit or a squashed tail hit.
    """
    if not got or not want:
        return False
    if got[-1] == want[-1]:
        return True
    for count in (2, 3):
        if len(want) < count:
            continue
        squashed = "".join(want[-count:])
        if got[-1] == squashed:
            return True
        if len(got) >= count and "".join(got[-count:]) == squashed:
            return True
    return False


def _ratio(got: list[str], want: list[str]) -> float:
    """Return a difflib ratio on the joined word lists.

    :param got: Transcript words.
    :param want: Expected words.
    :returns: 0 when both are empty-safe via difflib; otherwise the ratio.
    """
    return difflib.SequenceMatcher(None, " ".join(got), " ".join(want)).ratio()


def competitor_line(text: str, lexicon: Lexicon) -> str | None:
    """Substitute lexicon ``misheard`` values into ``text``.

    :param text: Spoken line.
    :param lexicon: Pronunciation lexicon.
    :returns: The competitor line, or None when no misheard hit applied.
    """
    return lexicon.competitor_line(text)


def greedy_ctc_decode(ids: Sequence[int], vocab: dict[str, int]) -> tuple[str, ...]:
    """Greedy CTC decode, dropping pad, s, and unk.

    Repeats collapse before the drop, matching CTC blanking on ``<pad>``.

    :param ids: Argmax token ids.
    :param vocab: Token to id map from the model's ``vocab.json``.
    :returns: Remaining phone tokens, in order.
    """
    id_to_token = {int(value): key for key, value in vocab.items()}
    phones: list[str] = []
    previous: int | None = None
    for raw in ids:
        idx = int(raw)
        if previous is not None and idx == previous:
            continue
        previous = idx
        token = id_to_token.get(idx, "")
        if not token or token in CTC_DROP:
            continue
        phones.append(token)
    return tuple(phones)


def ipa_phones(ipa: str) -> tuple[str, ...]:
    """Split an IPA string into phones, dropping stress marks.

    :param ipa: Reference IPA, possibly with spaces between words.
    :returns: Phone tokens.
    """
    stripped = ipa.replace("ˈ", "").replace("ˌ", "").strip()
    phones: list[str] = []
    for chunk in stripped.split():
        phones.extend(_split_ipa_chunk(chunk))
    return tuple(phones)


def _split_ipa_chunk(chunk: str) -> list[str]:
    """Longest-match tokenize one IPA word.

    :param chunk: IPA without spaces.
    :returns: Phone tokens.
    """
    phones: list[str] = []
    index = 0
    while index < len(chunk):
        matched = ""
        for unit in _IPA_UNITS:
            if chunk.startswith(unit, index):
                matched = unit
                break
        if matched:
            phones.append(matched)
            index += len(matched)
            continue
        phones.append(chunk[index])
        index += 1
    return phones


def phones_match(decoded: tuple[str, ...], ipa: str) -> bool:
    """Return whether a CTC phone sequence matches reference IPA.

    :param decoded: Phones from greedy CTC.
    :param ipa: Lexicon IPA for that term.
    :returns: True when the sequences match, including a compacted form.
    """
    expected = ipa_phones(ipa)
    if decoded == expected:
        return True
    return "".join(decoded) == "".join(expected)


def clip_span(
    start: float,
    end: float,
    *,
    duration: float,
    pad: float = SPAN_PAD,
) -> tuple[float, float]:
    """Widen a word span by ``pad`` seconds and clamp it to the clip.

    :param start: Word start, seconds.
    :param end: Word end, seconds.
    :param duration: Clip length, seconds.
    :param pad: Seconds to add on each side. The GB10 QA used 0.08.
    :returns: Inclusive-enough ``(start, end)`` window.
    """
    return (max(0.0, start - pad), min(duration, end + pad))


def select_span(words: tuple[WordSpan, ...], term: str) -> tuple[float, float] | None:
    """Find the Whisper span that covers a lexicon term.

    Hyphenated and slashed terms match either as one token or as split tokens.

    :param words: Whisper word timestamps.
    :param term: Lexicon term.
    :returns: ``(start, end)`` in seconds, or None when the term is missing.
    """
    tokens = _term_tokens(term)
    if not tokens:
        return None
    flat: list[tuple[str, int]] = []
    for index, item in enumerate(words):
        for part in _term_tokens(item.word):
            flat.append((part, index))
    length = len(tokens)
    for start in range(len(flat) - length + 1):
        window = [flat[start + offset][0] for offset in range(length)]
        if window != tokens:
            continue
        first = flat[start][1]
        last = flat[start + length - 1][1]
        return words[first].start, words[last].end
    return None


def _term_tokens(term: str) -> list[str]:
    """Split a lexicon term into comparable word pieces.

    :param term: Written form, possibly hyphenated or a path.
    :returns: Lowercase alphanumeric pieces.
    """
    return line_words(re.sub(r"[^a-zA-Z0-9']+", " ", term))


def words_from_whisper(result: dict[str, Any]) -> tuple[WordSpan, ...]:
    """Flatten Whisper ``word_timestamps`` into spans.

    :param result: ``model.transcribe`` return value.
    :returns: Word spans in order.
    """
    words: list[WordSpan] = []
    for segment in result.get("segments") or []:
        if not isinstance(segment, dict):
            continue
        for item in segment.get("words") or []:
            if not isinstance(item, dict):
                continue
            token = str(item.get("word") or "").strip()
            if not token:
                continue
            try:
                start = float(item["start"])
                end = float(item["end"])
            except (KeyError, TypeError, ValueError):
                continue
            words.append(WordSpan(word=token, start=start, end=end))
    return tuple(words)


def whisper_force_tokens(
    tokenizer: Any, text: str
) -> tuple[list[int], int, int]:
    """Build the forced-decoding token sequence for ``text``.

    The sequence is ``sot_sequence_including_notimestamps`` plus
    ``encode(' ' + text)`` plus ``eot``.

    :param tokenizer: Whisper tokenizer (or a test double with those attrs).
    :param text: Target or competitor line.
    :returns: All token ids, the index of the first text token, and text length.
    """
    sot = [int(item) for item in tokenizer.sot_sequence_including_notimestamps]
    encoded = [int(item) for item in tokenizer.encode(" " + text)]
    eot = tokenizer.eot
    eot_id = int(eot[0] if isinstance(eot, (list, tuple)) else eot)
    tokens = sot + encoded + [eot_id]
    return tokens, len(sot), len(encoded)


def sum_forced_text_logprobs(
    log_probs: Sequence[Sequence[float]],
    tokens: Sequence[int],
    *,
    text_start: int,
    text_len: int,
) -> float:
    """Sum log-probs of the text tokens under teacher forcing.

    ``log_probs[i]`` predicts ``tokens[i + 1]``, because logits were computed
    on ``tokens[:-1]``.

    :param log_probs: Rows of vocabulary log-probabilities.
    :param tokens: Full forced sequence, including sot and eot.
    :param text_start: Index of the first text token in ``tokens``.
    :param text_len: Number of text tokens.
    :returns: Sum of those text-token log-probs.
    """
    total = 0.0
    for offset in range(text_len):
        token_index = text_start + offset
        row = token_index - 1
        token_id = int(tokens[token_index])
        total += float(log_probs[row][token_id])
    return total


def beat_report(
    *,
    spoken: str,
    respelled: str,
    competitor: str | None,
    attempts: Sequence[dict[str, Any]],
    accepted: bool,
    alignment: Alignment,
    index: int | None = None,
) -> dict[str, Any]:
    """Build the per-beat JSON record.

    :param spoken: Script line.
    :param respelled: Lexicon respelling.
    :param competitor: Misheard line, or None.
    :param attempts: One record per take.
    :param accepted: True when a take passed.
    :param alignment: Best take's alignment.
    :param index: Beat number, when known.
    :returns: JSON-ready dictionary. ``signal_not_proof`` is always true.
    """
    payload: dict[str, Any] = {
        "spoken": spoken,
        "respelled": respelled,
        "competitor": competitor,
        "attempts": list(attempts),
        "accepted": accepted,
        "transcript": alignment.transcript,
        "first_ok": alignment.first_ok,
        "last_ok": alignment.last_ok,
        "ratio": alignment.ratio,
        "signal_not_proof": True,
    }
    if index is not None:
        payload["index"] = index
    return payload


def write_beat_report(path: Path, report: dict[str, Any]) -> None:
    """Write one beat's QA JSON.

    :param path: Destination, usually ``audio/beats/NN.qa.json``.
    :param report: Record from :func:`beat_report`.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def review_pronunciation_takes(
    wav_path: Path,
    *,
    spoken: str,
    respelled: str,
    lexicon: Lexicon,
    synthesize: Callable[[], None],
    transcribe: Callable[[Path], Transcript | str] | None = None,
    score_forced: Callable[[Path, str, str | None], dict[str, Any]] | None = None,
    score_phonemes: Callable[[Path, Transcript, str, Lexicon], list[dict[str, Any]]]
    | None = None,
    attempts: int = DEFAULT_ATTEMPTS,
    min_ratio: float = DEFAULT_MIN_RATIO,
    index: int | None = None,
) -> dict[str, Any]:
    """Synthesize, score first/last/ratio, and retry. Keep the best WAV.

    Forced-decoding and phoneme checks are recorded on each take. They do not
    decide accept or retry. That bar is intact edges plus the whole-line ratio.

    :param wav_path: Where each take is written.
    :param spoken: Script line.
    :param respelled: Lexicon respelling of that line.
    :param lexicon: Used for misheard competitors and phoneme targets.
    :param synthesize: Writes ``wav_path``. Called once per attempt.
    :param transcribe: Returns a transcript. The real Whisper path is the default.
    :param score_forced: Forced-decoding scores. Skipped when omitted and deps miss.
    :param score_phonemes: Per-term phoneme checks. Skipped when omitted and deps miss.
    :param attempts: Maximum takes, including the first.
    :param min_ratio: Accept at or above this whole-line ratio.
    :param index: Beat number stored on the report.
    :returns: One beat record for ``NN.qa.json`` and ``voice_log.json``.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1.")
    transcribe_fn = transcribe or transcribe_take
    competitor = competitor_line(spoken, lexicon)
    log: list[dict[str, Any]] = []
    best_key = (-1, -1.0)
    best_bytes = b""
    best_alignment = Alignment(first_ok=False, last_ok=False, ratio=0.0, transcript="")
    accepted = False
    for attempt in range(1, attempts + 1):
        synthesize()
        transcript = _as_transcript(transcribe_fn(wav_path))
        alignment = score_alignment(
            transcript.text, spoken=spoken, respelled=respelled
        )
        decision = take_decision(
            alignment, attempt=attempt, attempts=attempts, min_ratio=min_ratio
        )
        forced = _run_forced(score_forced, wav_path, spoken, competitor)
        phonemes = _run_phonemes(
            score_phonemes, wav_path, transcript, spoken, lexicon
        )
        current = wav_path.read_bytes() if wav_path.is_file() else b""
        if alignment.rank() > best_key:
            best_key = alignment.rank()
            best_bytes = current
            best_alignment = alignment
        log.append(
            {
                "n": attempt,
                "transcript": transcript.text,
                "first_ok": alignment.first_ok,
                "last_ok": alignment.last_ok,
                "ratio": round(alignment.ratio, 4),
                "forced": forced,
                "phonemes": phonemes,
                "decision": decision,
            }
        )
        if decision == "accept":
            accepted = True
            best_alignment = alignment
            best_bytes = current
            break
        if decision == "keep-best":
            break
    if best_bytes and wav_path.is_file() and wav_path.read_bytes() != best_bytes:
        wav_path.write_bytes(best_bytes)
    return beat_report(
        spoken=spoken,
        respelled=respelled,
        competitor=competitor,
        attempts=log,
        accepted=accepted,
        alignment=best_alignment,
        index=index,
    )


def _as_transcript(raw: Transcript | str) -> Transcript:
    """Accept either a Transcript or a plain string from a test double.

    :param raw: Transcriber output.
    :returns: A transcript. String input has no word timestamps.
    """
    if isinstance(raw, Transcript):
        return raw
    return Transcript(text=str(raw).strip(), words=())


def _run_forced(
    score_forced: Callable[[Path, str, str | None], dict[str, Any]] | None,
    wav_path: Path,
    spoken: str,
    competitor: str | None,
) -> dict[str, Any]:
    """Run forced decoding, or skip with a reason.

    :param score_forced: Injected scorer, or None for the real path.
    :param wav_path: Take WAV.
    :param spoken: Target line.
    :param competitor: Misheard line, or None.
    :returns: Target, competitor, margin, and skipped flag.
    """
    scorer = score_forced if score_forced is not None else forced_scores
    try:
        return scorer(wav_path, spoken, competitor)
    except PronunciationQAError as exc:
        return {
            "target": None,
            "competitor": None,
            "margin": None,
            "skipped": True,
            "reason": str(exc),
        }


def _run_phonemes(
    score_phonemes: Callable[[Path, Transcript, str, Lexicon], list[dict[str, Any]]]
    | None,
    wav_path: Path,
    transcript: Transcript,
    spoken: str,
    lexicon: Lexicon,
) -> list[dict[str, Any]]:
    """Run the wav2vec2 phoneme check, or skip.

    :param score_phonemes: Injected scorer, or None for the real path.
    :param wav_path: Take WAV.
    :param transcript: Whisper output, for timestamps.
    :param spoken: Script line, for lexicon hits.
    :param lexicon: Pronunciation lexicon.
    :returns: Per-term records. Empty when the check is skipped or unused.
    """
    scorer = score_phonemes if score_phonemes is not None else phoneme_checks
    try:
        return scorer(wav_path, transcript, spoken, lexicon)
    except PronunciationQAError as exc:
        return [{"term": "", "ok": False, "skipped": True, "reason": str(exc)}]


def transcribe_take(path: Path) -> Transcript:
    """Transcribe one beat with Whisper ``small.en``.

    Uses ``word_timestamps=True`` and ``temperature=0``. openai-whisper is
    required. torch is optional and only used to pick CUDA.

    :param path: WAV to transcribe.
    :returns: Transcript text and word spans.
    :raises PronunciationQAError: Whisper is not installed.
    """
    whisper = _optional_import("whisper", "openai-whisper")
    device = "cpu"
    try:
        torch = _optional_import("torch", "torch")
        if torch.cuda.is_available():
            device = "cuda"
    except PronunciationQAError:
        device = "cpu"
    model = _cached(
        f"whisper:{WHISPER_NAME}:{device}",
        lambda: whisper.load_model(WHISPER_NAME, device=device),
    )
    result = model.transcribe(
        str(path),
        language="en",
        word_timestamps=True,
        temperature=0,
        fp16=device == "cuda",
    )
    text = str(result.get("text") or "").strip()
    return Transcript(text=text, words=words_from_whisper(result))


def forced_scores(path: Path, spoken: str, competitor: str | None) -> dict[str, Any]:
    """Score the target line and a misheard competitor with forced decoding.

    :param path: Take WAV.
    :param spoken: Target line.
    :param competitor: Misheard line, or None when the lexicon has no hit.
    :returns: Target score, competitor score, and margin (target minus competitor).
    :raises PronunciationQAError: Whisper or torch is missing.
    """
    whisper = _optional_import("whisper", "openai-whisper")
    torch = _optional_import("torch", "torch")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = _cached(
        f"whisper:{WHISPER_NAME}:{device}",
        lambda: whisper.load_model(WHISPER_NAME, device=device),
    )
    tokenizer = whisper.tokenizer.get_tokenizer(
        model.is_multilingual, language="en", task="transcribe"
    )
    audio = whisper.load_audio(str(path))
    audio = whisper.pad_or_trim(audio)
    n_mels = getattr(getattr(model, "dims", None), "n_mels", 80)
    mel = whisper.log_mel_spectrogram(audio, n_mels=n_mels).to(model.device)
    target = _forced_logprob(model, tokenizer, torch, mel, spoken)
    if competitor is None:
        return {
            "target": target,
            "competitor": None,
            "margin": None,
            "skipped": True,
            "reason": "no misheard competitor",
        }
    other = _forced_logprob(model, tokenizer, torch, mel, competitor)
    return {
        "target": target,
        "competitor": other,
        "margin": target - other,
        "skipped": False,
    }


def _forced_logprob(
    model: Any,
    tokenizer: Any,
    torch: Any,
    mel: Any,
    text: str,
) -> float:
    """Sum text-token log-probs of ``text`` under the audio.

    :param model: Loaded Whisper model.
    :param tokenizer: Whisper tokenizer.
    :param torch: The torch module.
    :param mel: Mel spectrogram on the model device.
    :param text: Line to score.
    :returns: Sum of text-token log-probs.
    """
    tokens, text_start, text_len = whisper_force_tokens(tokenizer, text)
    token_tensor = torch.tensor(tokens, dtype=torch.long, device=model.device)
    logits = model.logits(token_tensor[:-1], model.embed_audio(mel))
    log_probs = torch.log_softmax(logits, dim=-1)
    rows = log_probs.detach().cpu().tolist()
    if rows and isinstance(rows[0][0], list):
        rows = rows[0]
    return sum_forced_text_logprobs(
        rows, tokens, text_start=text_start, text_len=text_len
    )


def phoneme_checks(
    path: Path,
    transcript: Transcript,
    spoken: str,
    lexicon: Lexicon,
) -> list[dict[str, Any]]:
    """Run wav2vec2 CTC on each lexicon term that has IPA in ``spoken``.

    :param path: Take WAV.
    :param transcript: Whisper timestamps.
    :param spoken: Script line.
    :param lexicon: Pronunciation lexicon.
    :returns: One record per IPA-bearing lexicon hit.
    :raises PronunciationQAError: transformers or torch is missing.
    """
    duration = _wav_duration(path)
    records: list[dict[str, Any]] = []
    for entry in lexicon.entries:
        if not entry.ipa.strip() or not lexicon.mentions(spoken, entry.term):
            continue
        span = select_span(transcript.words, entry.term)
        if span is None:
            records.append(
                {
                    "term": entry.term,
                    "ipa": entry.ipa,
                    "decoded": None,
                    "ok": False,
                    "span": None,
                    "reason": "span missing",
                }
            )
            continue
        window = clip_span(span[0], span[1], duration=duration)
        decoded = decode_span_phones(path, window[0], window[1])
        records.append(
            {
                "term": entry.term,
                "ipa": entry.ipa,
                "decoded": " ".join(decoded),
                "ok": phones_match(decoded, entry.ipa),
                "span": [window[0], window[1]],
            }
        )
    return records


def decode_span_phones(path: Path, start: float, end: float) -> tuple[str, ...]:
    """Greedy-CTC phonemes for one audio span.

    :param path: Take WAV.
    :param start: Window start, seconds.
    :param end: Window end, seconds.
    :returns: Phone tokens.
    :raises PronunciationQAError: transformers or torch is missing.
    """
    torch = _optional_import("torch", "torch")
    transformers = _optional_import("transformers", "transformers")
    model = _cached(
        f"wav2vec2:{WAV2VEC_ID}",
        lambda: transformers.Wav2Vec2ForCTC.from_pretrained(WAV2VEC_ID),
    )
    extractor = _cached(
        f"wav2vec2-fe:{WAV2VEC_ID}",
        lambda: transformers.Wav2Vec2FeatureExtractor.from_pretrained(WAV2VEC_ID),
    )
    tokenizer = _cached(
        f"wav2vec2-tok:{WAV2VEC_ID}",
        lambda: transformers.Wav2Vec2CTCTokenizer.from_pretrained(WAV2VEC_ID),
    )
    vocab = tokenizer.get_vocab()
    samples = _read_mono_span(path, start, end, rate=16000)
    values = torch.tensor([samples], dtype=torch.float32)
    inputs = extractor(
        values.squeeze(0).tolist(),
        sampling_rate=16000,
        return_tensors="pt",
        padding=True,
    )
    with torch.no_grad():
        logits = model(inputs.input_values).logits
    ids = logits.argmax(dim=-1)[0].tolist()
    return greedy_ctc_decode(ids, vocab)


def _wav_duration(path: Path) -> float:
    """Return WAV duration in seconds.

    :param path: PCM WAV.
    :returns: Duration.
    :raises PronunciationQAError: The file is not a readable WAV.
    """
    try:
        with wave.open(str(path), "rb") as handle:
            rate = handle.getframerate()
            frames = handle.getnframes()
    except wave.Error as exc:
        raise PronunciationQAError(f"Cannot read WAV {path}: {exc}") from exc
    if rate <= 0:
        return 0.0
    return frames / rate


def _read_mono_span(
    path: Path, start: float, end: float, *, rate: int
) -> list[float]:
    """Load one span as mono float samples at ``rate``.

    :param path: PCM WAV.
    :param start: Window start, seconds.
    :param end: Window end, seconds.
    :param rate: Target sample rate. wav2vec2 wants 16 kHz.
    :returns: Float samples in roughly [-1, 1].
    :raises PronunciationQAError: The WAV cannot be read.
    """
    try:
        with wave.open(str(path), "rb") as handle:
            src_rate = handle.getframerate()
            channels = handle.getnchannels()
            width = handle.getsampwidth()
            start_frame = max(0, int(start * src_rate))
            end_frame = min(handle.getnframes(), int(end * src_rate))
            handle.setpos(start_frame)
            raw = handle.readframes(max(0, end_frame - start_frame))
    except wave.Error as exc:
        raise PronunciationQAError(f"Cannot read WAV {path}: {exc}") from exc
    samples = _pcm_to_mono(raw, width=width, channels=channels)
    return _resample_linear(samples, src_rate, rate)


def _pcm_to_mono(raw: bytes, *, width: int, channels: int) -> list[float]:
    """Convert PCM bytes to mono float samples.

    :param raw: Frame bytes.
    :param width: Sample width in bytes.
    :param channels: Channel count.
    :returns: Mono floats.
    """
    if width not in {1, 2, 4} or channels < 1:
        return []
    import array
    import struct

    if width == 2:
        values = array.array("h")
        values.frombytes(raw)
        samples = [item / 32768.0 for item in values]
    elif width == 1:
        samples = [(item - 128) / 128.0 for item in raw]
    else:
        count = len(raw) // 4
        samples = [
            struct.unpack_from("<f", raw, index * 4)[0] for index in range(count)
        ]
    if channels == 1:
        return samples
    mono: list[float] = []
    for index in range(0, len(samples) - channels + 1, channels):
        window = samples[index : index + channels]
        mono.append(sum(window) / channels)
    return mono


def _resample_linear(samples: list[float], src_rate: int, dst_rate: int) -> list[float]:
    """Linear-resample a mono clip.

    :param samples: Source samples.
    :param src_rate: Original rate.
    :param dst_rate: Target rate.
    :returns: Resampled samples. Empty in, empty out.
    """
    if not samples or src_rate <= 0 or dst_rate <= 0:
        return samples
    if src_rate == dst_rate:
        return samples
    ratio = dst_rate / src_rate
    length = max(1, int(len(samples) * ratio))
    out: list[float] = []
    last = len(samples) - 1
    for index in range(length):
        position = index / ratio
        left = min(last, int(position))
        frac = position - left
        right = min(last, left + 1)
        out.append(samples[left] * (1.0 - frac) + samples[right] * frac)
    return out


def _optional_import(module: str, package: str) -> Any:
    """Import ``module`` or explain how to install it with uv.

    :param module: Import name.
    :param package: PyPI name shown in the error.
    :returns: The module.
    :raises PronunciationQAError: The import failed.
    """
    try:
        return __import__(module)
    except ImportError as exc:
        raise PronunciationQAError(
            f"{package} is not installed. Run this check with "
            f"uv run --with {package} ... . Do not pip install it globally."
        ) from exc


def _cached(key: str, loader: Callable[[], object]) -> Any:
    """Return a process-wide cached model.

    :param key: Cache key.
    :param loader: Builds the object once.
    :returns: The loaded object.
    """
    if key not in _MODELS:
        _MODELS[key] = loader()
    return _MODELS[key]


@app.command()
def check(
    project: Path = typer.Argument(..., help="Explainer project that contains script.md."),
    beat_index: int | None = typer.Option(None, "--beat", help="Beat index. Omit to score every WAV."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon"),
) -> None:
    """Score existing beat WAVs. Does not synthesize."""
    script_path = project / "script.md"
    if not script_path.is_file():
        logger.error("Error: missing {}", script_path)
        raise typer.Exit(code=2)
    try:
        script = parse_script(script_path.read_text(encoding="utf-8"))
        lex = load_lexicon(lexicon)
    except (ScriptError, LexiconError) as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    chosen = list(script.beats) if beat_index is None else [
        item for item in script.beats if item.index == beat_index
    ]
    if not chosen:
        logger.error("Error: script has no beat {}.", beat_index)
        raise typer.Exit(code=2)
    out_dir = project / "audio" / "beats"
    for item in chosen:
        wav_path = out_dir / f"{item.index:02d}.wav"
        if not wav_path.is_file():
            logger.warning("Skipping beat {}: missing {}", item.index, wav_path)
            continue
        respelled = lex.apply(item.spoken, "chatterbox").text
        try:
            transcript = transcribe_take(wav_path)
        except PronunciationQAError as exc:
            logger.error("Error: {}", exc)
            raise typer.Exit(code=2) from exc
        alignment = score_alignment(
            transcript.text, spoken=item.spoken, respelled=respelled
        )
        competitor = competitor_line(item.spoken, lex)
        try:
            forced = forced_scores(wav_path, item.spoken, competitor)
        except PronunciationQAError as exc:
            forced = {
                "target": None,
                "competitor": None,
                "margin": None,
                "skipped": True,
                "reason": str(exc),
            }
        try:
            phonemes = phoneme_checks(wav_path, transcript, item.spoken, lex)
        except PronunciationQAError as exc:
            phonemes = [{"term": "", "ok": False, "skipped": True, "reason": str(exc)}]
        report = beat_report(
            spoken=item.spoken,
            respelled=respelled,
            competitor=competitor,
            attempts=(
                {
                    "n": 1,
                    "transcript": transcript.text,
                    "first_ok": alignment.first_ok,
                    "last_ok": alignment.last_ok,
                    "ratio": round(alignment.ratio, 4),
                    "forced": forced,
                    "phonemes": phonemes,
                    "decision": "accept" if alignment.passed(DEFAULT_MIN_RATIO) else "keep-best",
                },
            ),
            accepted=alignment.passed(DEFAULT_MIN_RATIO),
            alignment=alignment,
            index=item.index,
        )
        write_beat_report(out_dir / f"{item.index:02d}.qa.json", report)
        typer.echo(
            f"beat {item.index} first={alignment.first_ok} last={alignment.last_ok} "
            f"ratio={alignment.ratio:.3f} accepted={report['accepted']}"
        )


if __name__ == "__main__":
    app()
