"""Tests for CosyVoice input protection that do not load the model."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from synthesize_beat import (
    DEFAULT_CHATTERBOX_SCRIPT,
    cached_model,
    install_sound_code_shield,
    resolve_chatterbox_script,
    resolve_hf_home,
    with_lead_in,
)


def test_lead_in_is_a_sacrificial_first_word() -> None:
    """The default is no pad. An explicit prefix is opt-in."""
    assert with_lead_in("You dig a hole.") == "You dig a hole."
    assert with_lead_in("You dig a hole.", pad="") == "You dig a hole."
    assert with_lead_in("You dig a hole.", pad="Okay.") == "Okay. You dig a hole."
    assert with_lead_in("Hmm. Already padded.", pad="Hmm.") == "Hmm. Already padded."


def test_model_loads_once_per_directory() -> None:
    """A second beat in the same process does not construct the model again."""
    calls: list[str] = []

    def load() -> str:
        calls.append("load")
        return "model"

    store: dict[str, object] = {}
    assert cached_model("/weights", load, store) == "model"
    assert cached_model("/weights", load, store) == "model"
    assert calls == ["load"]
    assert cached_model("/other", load, store) == "model"
    assert calls == ["load", "load"]


def test_sound_code_shield_patches_both_modules() -> None:
    """The frontend's own copy of spell_out_number is replaced too."""

    def spell(text: str, parser: object) -> str:
        """Turn digits into words, which is what garbles [IH1]."""
        del parser
        return text.replace("1", "one").replace("2", "two")

    assert spell("[IH1] and 2", None) == "[IHone] and two"
    utils = SimpleNamespace(spell_out_number=spell)
    frontend = SimpleNamespace(spell_out_number=spell)
    install_sound_code_shield(utils, frontend)
    assert utils.spell_out_number("[IH1] and 2", None) == "[IH1] and two"
    assert frontend.spell_out_number("[IH1]", None) == "[IH1]"
    install_sound_code_shield(utils, frontend)
    assert utils.spell_out_number("[IH1]", None) == "[IH1]"


def test_hf_home_is_respected_and_a_root_cache_is_avoided(tmp_path: Path) -> None:
    """An existing HF_HOME wins. A missing default cache yields the fallback."""
    missing = tmp_path / "does-not-exist" / "huggingface"
    fallback = tmp_path / "mine"
    assert resolve_hf_home({}, missing, fallback) == str(fallback)
    assert resolve_hf_home({"HF_HOME": "/data/hf"}, missing, fallback) is None
    writable = tmp_path / "ok"
    writable.mkdir()
    assert resolve_hf_home({}, writable, fallback) is None


def test_chatterbox_helper_path_prefers_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CHATTERBOX_SCRIPT wins over the sibling-skill default."""
    helper = tmp_path / "generate_narration.py"
    helper.write_text("# dummy\n", encoding="utf-8")
    monkeypatch.setenv("CHATTERBOX_SCRIPT", str(helper))
    assert resolve_chatterbox_script() == helper


def test_chatterbox_helper_path_defaults_to_sibling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no env var, look next to this skill."""
    monkeypatch.delenv("CHATTERBOX_SCRIPT", raising=False)
    assert resolve_chatterbox_script() == DEFAULT_CHATTERBOX_SCRIPT
