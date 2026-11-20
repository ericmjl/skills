"""Tests for the pronunciation lexicon and normalizer."""

from __future__ import annotations

from pathlib import Path

import pytest
from normalize import (
    Entry,
    Lexicon,
    LexiconError,
    emit_cmu,
    load_lexicon,
    load_pronunciations,
    preserve_sound_codes,
    validate_cmu,
)

SKILL = Path(__file__).resolve().parents[1]


def _lex(*entries: Entry) -> Lexicon:
    """Build a lexicon from entries.

    :param entries: Entries to add, in order.
    :returns: A lexicon whose version equals the number of entries.
    """
    lex = Lexicon(version=1, updated="2026-11-20", entries=())
    for entry in entries:
        lex = lex.add(entry, updated="2026-11-20")
    return lex


def test_validate_cmu_rejects_stress_on_a_consonant() -> None:
    """A consonant token cannot carry a stress digit."""
    with pytest.raises(LexiconError, match="Consonant"):
        validate_cmu("[B1]")


def test_validate_cmu_accepts_a_stressed_vowel() -> None:
    """Vowel stress 0, 1, or 2 is stored as written."""
    assert validate_cmu("[AY1] [K] [S]") == "[AY1] [K] [S]"


def test_emit_cmu_removes_spaces() -> None:
    """Tokens inside one word are concatenated, matching the pinyin example."""
    assert emit_cmu("[JH] [AE1] [K] [S]") == "[JH][AE1][K][S]"


def test_emit_cmu_keeps_a_space_between_words() -> None:
    """A bar in the lexicon is a word break, so a phrase is not one blob."""
    spoken = emit_cmu(
        "[EY1] [JH] [AH0] [N] [T] [S] | [D] [AA1] [T] | [EH1] [M] | [D] [IY1]"
    )
    assert spoken == "[EY1][JH][AH0][N][T][S] [D][AA1][T] [EH1][M] [D][IY1]"
    assert "detemd" not in spoken.lower()
    assert validate_cmu("[G] [IH1] [T] | [IH1]") == "[G] [IH1] [T] | [IH1]"


def test_sound_codes_survive_digit_spellout() -> None:
    """CosyVoice's number cleanup must not rewrite the digit inside [IH1]."""

    def spell_digits(span: str) -> str:
        """Spell digits the way CosyVoice's English cleanup does, with no space."""
        words = {"1": "one", "2": "two"}
        pieces: list[str] = []
        start: int | None = None
        for index, char in enumerate(span):
            if char.isdigit():
                if start is None:
                    start = index
                continue
            if start is not None:
                pieces.append(words[span[start:index]])
                start = None
            pieces.append(char)
        if start is not None:
            pieces.append(words[span[start:]])
        return "".join(pieces)

    raw = "[IH1] costs 2"
    assert spell_digits(raw) == "[IHone] costs two"
    assert preserve_sound_codes(raw, spell_digits) == "[IH1] costs two"


def test_apply_cosyvoice_uses_cmu_and_chatterbox_uses_respelling() -> None:
    """The same entry feeds each model's control."""
    lex = _lex(Entry("pyjanitor", cmu="[P] [AY1]", respelling="pie janitor"))
    spoken = lex.apply("Use pyjanitor today.", "cosyvoice3")
    plain = lex.apply("Use pyjanitor today.", "chatterbox")
    assert spoken.text == "Use [P][AY1] today."
    assert plain.text == "Use pie janitor today."
    assert spoken.warnings == ()


def test_missing_cmu_falls_back_to_respelling() -> None:
    """CosyVoice still speaks when only a respelling is known."""
    lex = _lex(Entry("pyjanitor", respelling="pie janitor"))
    result = lex.apply("pyjanitor", "cosyvoice3")
    assert result.text == "pie janitor"
    assert result.warnings == ("pyjanitor has no CMU pronunciation; used the respelling.",)


def test_exact_smiles_does_not_eat_the_verb() -> None:
    """SMILES is case-exact so ordinary 'smiles' stays a verb."""
    lex = _lex(
        Entry("SMILES", cmu="[S] [M] [AY1] [L] [Z]", respelling="smiles", match="exact")
    )
    assert lex.apply("She smiles at the SMILES string.", "chatterbox").text == (
        "She smiles at the smiles string."
    )


def test_hyphen_does_not_hide_mrna() -> None:
    """pre-mRNA still receives the mRNA pronunciation."""
    lex = _lex(Entry("mRNA", cmu="[EH1] [M]", respelling="em ar en ay"))
    result = lex.apply("Measure pre-mRNA.", "cosyvoice3")
    assert result.text == "Measure pre-[EH1][M]."


def test_longer_hyphenated_term_wins() -> None:
    """scikit-learn is one word, not the entry for learn."""
    lex = _lex(
        Entry("learn", cmu="[L] [ER1] [N]", respelling="learn-word"),
        Entry("scikit-learn", cmu="[S] [AY1]", respelling="sy kit learn"),
    )
    result = lex.apply("Use scikit-learn.", "chatterbox")
    assert result.text == "Use sy kit learn."
    assert result.replacements[0].term == "scikit-learn"


def test_existing_phoneme_run_is_left_alone() -> None:
    """A second pass does not rewrite tokens that are already phonemes."""
    lex = _lex(Entry("pyjanitor", cmu="[P] [AY1] [JH] [AE1]", respelling="pie janitor"))
    once = lex.apply("pyjanitor", "cosyvoice3").text
    twice = lex.apply(once, "cosyvoice3").text
    assert once == "[P][AY1][JH][AE1]"
    assert twice == once


def test_add_and_correct_return_new_lexicons() -> None:
    """Updates bump the version and do not mutate the previous lexicon."""
    original = Lexicon(version=1, updated="2026-11-20", entries=())
    added = original.add(
        Entry("JAX", cmu="[JH] [AE1] [K] [S]", respelling="jacks", match="exact"),
        updated="2026-11-21",
    )
    changed = added.correct("JAX", updated="2026-11-22", respelling="jacks again", verified=True)
    assert original.version == 1
    assert original.entries == ()
    assert added.version == 2
    assert added.get("JAX") is not None
    assert added.get("JAX").respelling == "jacks"
    assert changed.version == 3
    assert changed.get("jax").respelling == "jacks again"
    assert changed.get("JAX").verified is True


def test_add_refuses_a_duplicate_term() -> None:
    """A second add of the same term tells the caller to use correct."""
    lex = _lex(Entry("JAX", respelling="jacks"))
    with pytest.raises(LexiconError, match="already"):
        lex.add(Entry("jax", respelling="other"), updated="2026-11-20")


def test_unknown_target_is_rejected() -> None:
    """The normalizer does not guess a model family."""
    lex = _lex(Entry("JAX", respelling="jacks"))
    with pytest.raises(LexiconError, match="Unknown target"):
        lex.apply("JAX", "kokoro")


def test_fixture_lexicon_starts_unverified() -> None:
    """Version and verified flags are pinned on a fixture, not the live file.

    ``add`` and ``correct`` bump the shipped lexicon. A test that requires
    version 1, or a fixed verified set, fails the moment someone does that.
    """
    lex = load_lexicon(Path(__file__).parent / "fixtures" / "lexicon.json")
    assert lex.version == 1
    assert lex.entries
    assert [item.term for item in lex.entries if item.verified] == []
    assert lex.apply("Install with pixi.", "chatterbox").text == "Install with pixie."


def test_shipped_lexicon_rewrites_every_seed_term() -> None:
    """The shipped file loads, and each seed term has a CosyVoice reading."""
    lex = load_lexicon(SKILL / "lexicon.json")
    assert lex.entries
    for entry in lex.entries:
        result = lex.apply(f"See {entry.term} now.", "cosyvoice3")
        assert result.replacements, entry.term
        assert "[" in result.text
    agents = lex.apply("See AGENTS.md now.", "cosyvoice3")
    assert "[EY1][JH][AH0][N][T][S] [D][AA1][T] [EH1][M] [D][IY1]" in agents.text
    assert lex.get("pixi") is not None
    assert lex.get("pixi").respelling == "pixie"
    assert lex.get("Git").respelling == "ghit"
    assert lex.get("CI").respelling == "see eye"
    assert lex.get("AGENTS.md").respelling == "agents dot em dee"
    assert lex.get("pre-commit").respelling == "pree commit"
    assert lex.get("dotfiles").respelling == "dot files"
    assert lex.get("lockfile").respelling == "lock file"
    assert lex.get("AI") is not None
    assert lex.get("AI").respelling == "ay eye"
    assert lex.get("AI").verified is False
    assert lex.get("teammate") is not None
    assert lex.get("teammate").respelling == "team mate"
    assert lex.get("teammate").verified is False
    assert lex.get("pixi") is not None
    assert lex.get("pixi").verified is True
    assert lex.get("git add dot") is not None
    assert lex.get("git add dot").respelling == "git add dot"
    assert lex.get("git add dot").verified is False
    assert lex.apply("But git add dot just committed a file.", "chatterbox").text == (
        "But git add dot just committed a file."
    )
    seeds = {
        "Diataxis": "dye uh tax iss",
        ".env": "dot E N V",
        "pyproject.toml": "pie project dot toml",
        "pixi.lock": "pixie dot lock",
        "pytest": "pie test",
        "pyds-cli": "pie D S C L I",
        "cookiecutter": "cookie cutter",
        "SKILL.md": "skill dot em dee",
        ".gitignore": "dot git ignore",
    }
    for term, respelling in seeds.items():
        entry = lex.get(term)
        assert entry is not None, term
        assert entry.respelling == respelling, term
        assert entry.verified is False, term
    assert lex.get("two-gigabyte") is not None
    assert lex.get("two-gigabyte").misheard == "toe gigabyte"
    assert lex.get("hard-codes") is not None
    assert lex.get("hard-codes").misheard == "card codes"
    assert lex.get("Diataxis") is not None
    assert lex.get("Diataxis").misheard == "dee ataxis"
    assert lex.get("live in") is not None
    assert lex.get("live in").respelling == "liv in"
    assert lex.get("Skills") is not None
    assert lex.get("Skills").match == "exact"
    assert lex.get("integration runs") is not None
    assert lex.get("overwrite") is not None
    assert lex.get("overwrite").misheard == "overrate"
    assert lex.get("reusable") is not None
    assert lex.get("reusable").misheard == "reachable"
    assert lex.get("uv") is not None
    assert lex.get("uv").respelling == "you vee"
    assert lex.apply("Install with pixi.", "chatterbox").text == "Install with pixie."
    untouched = lex.apply("She smiles.", "chatterbox")
    assert untouched.text == "She smiles."
    modal = lex.apply("a modal verb and Modal the product", "chatterbox")
    assert modal.text == "a modal verb and Modul the product"


def test_merge_adds_a_term_and_keeps_a_verified_reading(tmp_path: Path) -> None:
    """An import fills gaps, records conflicts, and does not touch a verified entry."""
    lex = _lex(
        Entry("pixi", respelling="pixie", verified=True),
        Entry("Git", respelling="ghit"),
    )
    source = tmp_path / "pronunciations.json"
    source.write_text(
        '{"pixi": "pick see", "Git": "jit", "CI": "see eye"}',
        encoding="utf-8",
    )
    revised, messages = lex.merge(load_pronunciations(source), updated="2026-11-20")
    assert revised.version == lex.version + 1
    assert revised.get("pixi").respelling == "pixie"
    assert revised.get("Git").respelling == "ghit"
    assert revised.get("CI").respelling == "see eye"
    assert any(message.startswith("kept verified") for message in messages)
    assert any(message.startswith("conflict") for message in messages)
    assert any(message.startswith("added CI") for message in messages)
