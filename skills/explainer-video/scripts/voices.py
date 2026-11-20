"""Load the named-voice registry.

Paths in the registry may start with ``~``. The audio files themselves stay
outside the repo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class VoiceError(ValueError):
    """The voice registry is missing a required field."""


def load_registry(path: Path) -> dict[str, Any]:
    """Load ``voices.yaml``.

    :param path: Registry file.
    :returns: The decoded mapping.
    :raises VoiceError: The file is missing or not a mapping.
    """
    if not path.is_file():
        raise VoiceError(f"Voice registry not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("voices"), dict):
        raise VoiceError(f"Voice registry needs a voices mapping: {path}")
    return raw


def get_voice(registry: dict[str, Any], name: str) -> dict[str, Any]:
    """Return one voice record.

    :param registry: Document from :func:`load_registry`.
    :param name: Voice id.
    :returns: The voice mapping, including its id under ``id``.
    :raises VoiceError: The id is not in the registry.
    """
    voices = registry["voices"]
    if name not in voices or not isinstance(voices[name], dict):
        known = ", ".join(sorted(voices))
        raise VoiceError(f"Unknown voice {name!r}. Registry has: {known}.")
    record = dict(voices[name])
    record["id"] = name
    return record


def expand_path(value: object) -> Path | None:
    """Expand a registry path.

    :param value: A path string, or empty.
    :returns: An expanded path, or None when the value is empty.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return Path(text).expanduser()


def target_for(model: str) -> str:
    """Map a registry model id onto a normalizer target.

    :param model: ``model`` field from the voice record.
    :returns: ``cosyvoice3`` or ``chatterbox``.
    :raises VoiceError: The model is not wired.
    """
    if model == "cosyvoice3":
        return "cosyvoice3"
    if model in {"chatterbox-turbo", "chatterbox-tts"}:
        return "chatterbox"
    raise VoiceError(
        f"Model {model!r} is not wired for synthesis. "
        "Kokoro is documented in references/tts-models.md and is not a clone."
    )
