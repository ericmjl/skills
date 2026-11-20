"""Versioned pronunciation lexicon and the text pass that runs before TTS.

CosyVoice 3 accepts CMU ARPAbet tokens such as ``[JH][AE1][K][S]`` inline.
Chatterbox accepts plain text only, so the same entry carries a respelling.
Neither path is applied inside a span that is already a phoneme run.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path

VOWELS: frozenset[str] = frozenset(
    {
        "AA",
        "AE",
        "AH",
        "AO",
        "AW",
        "AY",
        "EH",
        "ER",
        "EY",
        "IH",
        "IY",
        "OW",
        "OY",
        "UH",
        "UW",
    }
)
CONSONANTS: frozenset[str] = frozenset(
    {
        "B",
        "CH",
        "D",
        "DH",
        "F",
        "G",
        "HH",
        "JH",
        "K",
        "L",
        "M",
        "N",
        "NG",
        "P",
        "R",
        "S",
        "SH",
        "T",
        "TH",
        "V",
        "W",
        "Y",
        "Z",
        "ZH",
    }
)
TOKEN_RE = re.compile(r"\[([A-Z]{1,2})([0-2])?\]")
PROTECTED_RE = re.compile(r"(?:\[[A-Za-z]+[0-2]?\]){2,}")
SOUND_CODE_RE = re.compile(r"\[[A-Za-z]{1,3}[0-2]?\]")
WORD_BREAK = "|"
TARGETS: frozenset[str] = frozenset({"cosyvoice3", "chatterbox"})


class LexiconError(ValueError):
    """A lexicon entry or file is not usable."""


def validate_cmu(cmu: str) -> str:
    """Check a CMU pronunciation string.

    :param cmu: Bracketed ARPAbet tokens, spaces allowed. Empty is allowed.
    :returns: The same string, stripped.
    :raises LexiconError: A token is not CMU, or a consonant carries stress.
    """
    stripped = cmu.strip()
    if not stripped:
        return ""
    pieces = stripped.split()
    if not pieces:
        return ""
    for piece in pieces:
        if piece == WORD_BREAK:
            continue
        match = TOKEN_RE.fullmatch(piece)
        if match is None:
            raise LexiconError(f"Not a CMU token: {piece}")
        phoneme, stress = match.group(1), match.group(2)
        if phoneme in VOWELS:
            continue
        if phoneme in CONSONANTS and stress is None:
            continue
        if phoneme in CONSONANTS and stress is not None:
            raise LexiconError(f"Consonant cannot carry stress: {piece}")
        raise LexiconError(f"Unknown CMU phoneme: {piece}")
    return stripped


def emit_cmu(cmu: str) -> str:
    """Join CMU tokens inside each word, and keep a space between words.

    A ``|`` in the lexicon string is the word break. Tokens inside one word
    are concatenated, matching CosyVoice's pinyin example ``[j][ǐ]``. Without
    the break, a multi-word reading such as "agents dot em dee" is one long
    token and the model runs the words together.

    :param cmu: A string that :func:`validate_cmu` accepts.
    :returns: One bracket-run per word, separated by spaces, or an empty string.
    """
    checked = validate_cmu(cmu)
    if not checked:
        return ""
    words: list[str] = []
    current: list[str] = []
    for piece in checked.split():
        if piece == WORD_BREAK:
            if current:
                words.append("".join(current))
                current = []
            continue
        current.extend(re.findall(r"\[[A-Z]{1,2}[0-2]?\]", piece))
    if current:
        words.append("".join(current))
    return " ".join(words)


def preserve_sound_codes(text: str, spell: object) -> str:
    """Run a text cleanup on everything except CMU sound codes.

    CosyVoice's English ``spell_out_number`` walks every digit. The stress
    digit in ``[IH1]`` becomes the word "one", so the token the model sees is
    ``[IHone]``. Spans that match a sound code are copied through unchanged.

    :param text: A line that may contain sound codes and ordinary numbers.
    :param spell: Callable used on each plain span. CosyVoice passes
        ``(span, inflect_parser)``; this helper calls it with the span only
        when the caller has already bound the parser.
    :returns: The line with sound codes intact.
    """
    if not callable(spell):
        raise LexiconError("spell must be callable.")
    parts: list[str] = []
    cursor = 0
    for match in SOUND_CODE_RE.finditer(text):
        if match.start() > cursor:
            parts.append(str(spell(text[cursor : match.start()])))
        parts.append(match.group(0))
        cursor = match.end()
    if cursor < len(text):
        parts.append(str(spell(text[cursor:])))
    return "".join(parts)


@dataclass(frozen=True)
class Entry:
    """One term and the pronunciations that may replace it.

    :param term: The written form to find.
    :param cmu: CMU tokens for CosyVoice 3. Empty if unknown.
    :param respelling: Plain words for models with no phoneme input.
    :param ipa: Reference IPA. Used by pronunciation QA, not sent to TTS.
    :param note: Why this reading was chosen.
    :param match: ``insensitive`` or ``exact``.
    :param verified: True only after someone has listened to a render.
    :param misheard: A wrong reading to score against, for forced decoding.
    """

    term: str
    cmu: str = ""
    respelling: str = ""
    ipa: str = ""
    note: str = ""
    match: str = "insensitive"
    verified: bool = False
    misheard: str = ""

    def with_changes(self, **changes: object) -> Entry:
        """Return a copy with the given fields replaced.

        :param changes: Entry field names and new values.
        :returns: A new entry. This instance is unchanged.
        """
        return replace(self, **changes)


@dataclass(frozen=True)
class Replacement:
    """One substitution a normalization pass made.

    :param term: Lexicon term that matched.
    :param start: Start index in the original text.
    :param end: End index in the original text.
    :param original: The matched surface text.
    :param spoken: The text that replaced it.
    """

    term: str
    start: int
    end: int
    original: str
    spoken: str


@dataclass(frozen=True)
class ApplyResult:
    """Normalized text plus what changed.

    :param text: Text safe to send to the named target.
    :param replacements: Substitutions, in left-to-right order.
    :param warnings: Problems that did not abort the pass.
    """

    text: str
    replacements: tuple[Replacement, ...]
    warnings: tuple[str, ...]


def _pattern(entry: Entry) -> re.Pattern[str]:
    """Build the search pattern for one entry.

    :param entry: Lexicon entry. ``match`` must already be valid.
    :returns: A compiled pattern that does not match inside a longer token.
    """
    flags = re.IGNORECASE if entry.match == "insensitive" else 0
    body = re.escape(entry.term)
    # Hyphen is a boundary, so pre-mRNA still corrects mRNA. A longer entry
    # such as scikit-learn wins when both could match the same span.
    return re.compile(rf"(?<!\w){body}(?!\w)", flags)


def _check_entry(entry: Entry) -> Entry:
    """Validate an entry and return it with a normalized CMU string.

    :param entry: Candidate entry.
    :returns: The same data, with ``cmu`` stripped.
    :raises LexiconError: The term, match mode, or CMU string is unusable.
    """
    if not entry.term.strip():
        raise LexiconError("Term is empty.")
    if entry.match not in {"insensitive", "exact"}:
        raise LexiconError(f"match must be insensitive or exact, got {entry.match!r}.")
    if any(ch in entry.term for ch in "\n\r\t"):
        raise LexiconError(f"Term must be one line, got {entry.term!r}.")
    return entry.with_changes(term=entry.term.strip(), cmu=validate_cmu(entry.cmu))


@dataclass(frozen=True)
class Lexicon:
    """An immutable, versioned list of pronunciation entries.

    Methods that change the list return a new lexicon. The version increments
    by one on every change so a project can see which file produced an audio take.
    """

    version: int
    updated: str
    entries: tuple[Entry, ...]

    def get(self, term: str) -> Entry | None:
        """Find an entry by term, ignoring case.

        :param term: Written form to look up.
        :returns: The entry, or None.
        """
        key = term.strip().lower()
        for entry in self.entries:
            if entry.term.lower() == key:
                return entry
        return None

    def add(self, entry: Entry, *, updated: str) -> Lexicon:
        """Return a lexicon that includes ``entry``.

        :param entry: New entry. The term must not already exist.
        :param updated: Date stamp for the new version, ``YYYY-MM-DD``.
        :returns: A new lexicon with ``version + 1``.
        :raises LexiconError: The entry is invalid or the term is already present.
        """
        checked = _check_entry(entry)
        if self.get(checked.term) is not None:
            raise LexiconError(
                f"{checked.term!r} is already in the lexicon. Use correct to change it."
            )
        merged = tuple(sorted((*self.entries, checked), key=lambda item: item.term.lower()))
        return Lexicon(version=self.version + 1, updated=updated, entries=merged)

    def correct(self, term: str, *, updated: str, **changes: object) -> Lexicon:
        """Return a lexicon with one entry's fields replaced.

        :param term: Existing term, case-insensitive.
        :param updated: Date stamp for the new version.
        :param changes: Entry fields to replace. Omitted fields stay.
        :returns: A new lexicon with ``version + 1``.
        :raises LexiconError: The term is missing or the new entry is invalid.
        """
        current = self.get(term)
        if current is None:
            raise LexiconError(f"{term!r} is not in the lexicon. Use add first.")
        updated_entry = _check_entry(current.with_changes(**changes))
        if updated_entry.term.lower() != current.term.lower():
            other = self.get(updated_entry.term)
            if other is not None and other.term.lower() != current.term.lower():
                raise LexiconError(f"{updated_entry.term!r} is already in the lexicon.")
        replaced = tuple(
            updated_entry if item.term.lower() == current.term.lower() else item
            for item in self.entries
        )
        ordered = tuple(sorted(replaced, key=lambda item: item.term.lower()))
        return Lexicon(version=self.version + 1, updated=updated, entries=ordered)

    def merge(
        self,
        incoming: tuple[Entry, ...],
        *,
        updated: str,
    ) -> tuple[Lexicon, tuple[str, ...]]:
        """Fold imported pronunciations into this lexicon.

        A missing term is added. An unverified entry keeps its own respelling
        and CMU when those fields are already filled, and takes the import's
        value when its own field is empty. A verified entry is not changed.
        The version increments by one when any entry changes.

        :param incoming: Entries from a ``pronunciations.json`` file.
        :param updated: Date stamp for the new version, ``YYYY-MM-DD``.
        :returns: The lexicon to keep, and one message per imported term.
        :raises LexiconError: An imported entry is not usable.
        """
        current = {entry.term.lower(): entry for entry in self.entries}
        messages: list[str] = []
        changed = False
        for raw in incoming:
            entry = _check_entry(raw)
            key = entry.term.lower()
            existing = current.get(key)
            if existing is None:
                current[key] = entry
                messages.append(f"added {entry.term}")
                changed = True
                continue
            if existing.verified:
                messages.append(f"kept verified {existing.term}")
                continue
            merged_entry, note = _merge_unverified(existing, entry)
            if merged_entry != existing:
                current[key] = merged_entry
                changed = True
            if note:
                messages.append(note)
        if not changed:
            return self, tuple(messages)
        entries = tuple(sorted(current.values(), key=lambda item: item.term.lower()))
        revised = Lexicon(version=self.version + 1, updated=updated, entries=entries)
        return revised, tuple(messages)

    def mentions(self, text: str, term: str) -> bool:
        """Report whether ``text`` contains a match for ``term``.

        :param text: Spoken line.
        :param term: Lexicon term.
        :returns: True when the entry's match rule hits.
        :raises LexiconError: The term is not in the lexicon.
        """
        entry = self.get(term)
        if entry is None:
            raise LexiconError(f"{term!r} is not in the lexicon.")
        return _pattern(entry).search(text) is not None

    def hits(self, text: str) -> tuple[tuple[int, int, Entry], ...]:
        """Find non-overlapping lexicon matches in ``text``.

        Protected phoneme runs are skipped. Longer overlapping terms win.

        :param text: Spoken line.
        :returns: ``(start, end, entry)`` triples, left to right.
        """
        protected = [match.span() for match in PROTECTED_RE.finditer(text)]
        found: list[tuple[int, int, Entry]] = []
        for entry in self.entries:
            for match in _pattern(entry).finditer(text):
                span = match.span()
                if any(span[0] < end and start < span[1] for start, end in protected):
                    continue
                found.append((span[0], span[1], entry))
        found.sort(key=lambda item: (item[0], -(item[1] - item[0])))
        chosen: list[tuple[int, int, Entry]] = []
        cursor = -1
        for start, end, entry in found:
            if start < cursor:
                continue
            if chosen and start < chosen[-1][1]:
                continue
            chosen.append((start, end, entry))
            cursor = end
        return tuple(chosen)

    def competitor_line(self, text: str) -> str | None:
        """Replace lexicon hits with their ``misheard`` readings.

        :param text: Spoken line.
        :returns: The competitor line, or None when no misheard hit applied.
        """
        parts: list[str] = []
        position = 0
        changed = False
        for start, end, entry in self.hits(text):
            parts.append(text[position:start])
            wrong = entry.misheard.strip()
            if wrong:
                parts.append(wrong)
                changed = True
            else:
                parts.append(text[start:end])
            position = end
        parts.append(text[position:])
        if not changed:
            return None
        return "".join(parts)

    def apply(self, text: str, target: str) -> ApplyResult:
        """Replace lexicon hits with the pronunciation ``target`` can speak.

        :param text: Spoken line, before TTS.
        :param target: ``cosyvoice3`` or ``chatterbox``.
        :returns: The rewritten line, the hits, and any fallback warnings.
        :raises LexiconError: ``target`` is not a known model family.
        """
        if target not in TARGETS:
            raise LexiconError(
                f"Unknown target {target!r}. Use one of: {', '.join(sorted(TARGETS))}."
            )
        chosen = self.hits(text)
        parts: list[str] = []
        replacements: list[Replacement] = []
        warnings: list[str] = []
        position = 0
        for start, end, entry in chosen:
            parts.append(text[position:start])
            spoken, warning = _spoken_for(entry, target)
            if warning:
                warnings.append(warning)
            parts.append(spoken)
            replacements.append(
                Replacement(
                    term=entry.term,
                    start=start,
                    end=end,
                    original=text[start:end],
                    spoken=spoken,
                )
            )
            position = end
        parts.append(text[position:])
        return ApplyResult(
            text="".join(parts),
            replacements=tuple(replacements),
            warnings=tuple(warnings),
        )


def _spoken_for(entry: Entry, target: str) -> tuple[str, str | None]:
    """Pick the replacement string for one entry.

    :param entry: Validated entry.
    :param target: ``cosyvoice3`` or ``chatterbox``.
    :returns: The spoken replacement and an optional warning.
    """
    if target == "cosyvoice3" and entry.cmu:
        return emit_cmu(entry.cmu), None
    if entry.respelling.strip():
        warning = None
        if target == "cosyvoice3":
            warning = f"{entry.term} has no CMU pronunciation; used the respelling."
        return entry.respelling.strip(), warning
    return (
        entry.term,
        f"{entry.term} has no pronunciation for {target}; left the spelling unchanged.",
    )


def _entry_from_obj(raw: object) -> Entry:
    """Build an entry from one JSON object.

    :param raw: Decoded JSON value.
    :returns: A validated entry.
    :raises LexiconError: The object is not an entry.
    """
    if not isinstance(raw, dict):
        raise LexiconError("Each lexicon entry must be an object.")
    known = {"term", "cmu", "respelling", "ipa", "note", "match", "verified", "misheard"}
    extra = set(raw) - known
    if extra:
        raise LexiconError(f"Unknown lexicon fields: {', '.join(sorted(extra))}.")
    term = raw.get("term")
    if not isinstance(term, str):
        raise LexiconError("Entry term must be a string.")
    verified = raw.get("verified", False)
    if not isinstance(verified, bool):
        raise LexiconError(f"verified must be true or false for {term}.")
    strings = {}
    for key in ("cmu", "respelling", "ipa", "note", "match", "misheard"):
        value = raw.get(key, "" if key != "match" else "insensitive")
        if not isinstance(value, str):
            raise LexiconError(f"{key} must be a string for {term}.")
        strings[key] = value
    return _check_entry(
        Entry(
            term=term,
            cmu=strings["cmu"],
            respelling=strings["respelling"],
            ipa=strings["ipa"],
            note=strings["note"],
            match=strings["match"],
            verified=verified,
            misheard=strings["misheard"],
        )
    )


def _merge_unverified(existing: Entry, incoming: Entry) -> tuple[Entry, str]:
    """Fill empty fields on an unverified entry. Never replace a filled reading.

    :param existing: The lexicon entry already on disk.
    :param incoming: The imported entry for the same term.
    :returns: The entry to store, and a message. The message may be empty.
    """
    changes: dict[str, object] = {}
    notes: list[str] = []
    if not existing.cmu and incoming.cmu:
        changes["cmu"] = incoming.cmu
        notes.append(f"filled cmu for {existing.term}")
    if not existing.respelling and incoming.respelling:
        changes["respelling"] = incoming.respelling
        notes.append(f"filled respelling for {existing.term}")
    elif (
        existing.respelling
        and incoming.respelling
        and existing.respelling != incoming.respelling
    ):
        notes.append(
            f"conflict {existing.term}: kept {existing.respelling!r}, "
            f"import has {incoming.respelling!r}"
        )
    if not existing.ipa and incoming.ipa:
        changes["ipa"] = incoming.ipa
    if not existing.misheard and incoming.misheard:
        changes["misheard"] = incoming.misheard
    conflict = any(note.startswith("conflict ") for note in notes)
    if incoming.verified and not conflict:
        changes["verified"] = True
        notes.append(f"marked {existing.term} verified from import")
    if not changes:
        return existing, "; ".join(notes)
    return existing.with_changes(**changes), "; ".join(notes)


def load_pronunciations(path: Path) -> tuple[Entry, ...]:
    """Load a previous project's ``pronunciations.json``.

    Three shapes are accepted. A list of lexicon entry objects. An object
    with an ``entries`` list, which is how this skill writes ``lexicon.json``.
    A map of term to respelling, or of term to an entry object.

    :param path: JSON file.
    :returns: Entries in file order. They are not yet merged.
    :raises LexiconError: The file is missing or not one of those shapes.
    """
    if not path.is_file():
        raise LexiconError(f"Pronunciations not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LexiconError(f"Pronunciations are not valid JSON: {path}") from exc
    if isinstance(raw, list):
        return tuple(_entry_from_obj(item) for item in raw)
    if isinstance(raw, dict) and isinstance(raw.get("entries"), list):
        return tuple(_entry_from_obj(item) for item in raw["entries"])
    if isinstance(raw, dict):
        items: list[Entry] = []
        for key, value in raw.items():
            if key in {"version", "updated"}:
                continue
            if isinstance(value, str):
                items.append(
                    _entry_from_obj(
                        {
                            "term": key,
                            "respelling": value,
                            "note": "Imported from pronunciations.json.",
                        }
                    )
                )
                continue
            if isinstance(value, dict):
                payload = dict(value)
                payload.setdefault("term", key)
                items.append(_entry_from_obj(payload))
                continue
            raise LexiconError(f"Pronunciation for {key!r} must be a string or an object.")
        if not items:
            raise LexiconError(f"No pronunciations in {path}.")
        return tuple(items)
    raise LexiconError("pronunciations.json must be a list or an object.")


def load_lexicon(path: Path) -> Lexicon:
    """Load a lexicon file.

    :param path: JSON file written by :func:`dump_lexicon`.
    :returns: The lexicon.
    :raises LexiconError: The file is missing or invalid.
    """
    if not path.is_file():
        raise LexiconError(f"Lexicon not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LexiconError(f"Lexicon is not valid JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise LexiconError("Lexicon root must be an object.")
    version = raw.get("version")
    updated = raw.get("updated")
    entries = raw.get("entries")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise LexiconError("Lexicon version must be an integer >= 1.")
    if not isinstance(updated, str) or not updated:
        raise LexiconError("Lexicon updated must be a non-empty string.")
    if not isinstance(entries, list):
        raise LexiconError("Lexicon entries must be a list.")
    parsed = tuple(_entry_from_obj(item) for item in entries)
    terms = [item.term.lower() for item in parsed]
    if len(terms) != len(set(terms)):
        raise LexiconError("Lexicon contains two entries for the same term.")
    return Lexicon(version=version, updated=updated, entries=parsed)


def dump_lexicon(lexicon: Lexicon, path: Path) -> None:
    """Write a lexicon as JSON.

    :param lexicon: Lexicon to store.
    :param path: Destination. Parent directories are created.
    """
    payload = {
        "version": lexicon.version,
        "updated": lexicon.updated,
        "entries": [
            _dump_entry(entry)
            for entry in sorted(lexicon.entries, key=lambda item: item.term.lower())
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _dump_entry(entry: Entry) -> dict[str, object]:
    """Serialize one lexicon entry.

    Empty ``misheard`` is omitted so older files stay compact.

    :param entry: Entry to write.
    :returns: JSON object.
    """
    payload: dict[str, object] = {
        "term": entry.term,
        "cmu": entry.cmu,
        "respelling": entry.respelling,
        "ipa": entry.ipa,
        "note": entry.note,
        "match": entry.match,
        "verified": entry.verified,
    }
    if entry.misheard:
        payload["misheard"] = entry.misheard
    return payload
