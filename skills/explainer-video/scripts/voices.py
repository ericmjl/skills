"""Load the named-voice registry.

Reference clips live in ``~/.voice/`` (``Path.home() / ".voice"``), not in
the repo. A relative ``reference`` name is looked up there. Paths that start
with ``~`` still expand at runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REFERENCE_STEM = "reference"
REFERENCE_EXTENSIONS = (".m4a", ".wav", ".mp3")
DEFAULT_REFERENCE_NAME = f"{REFERENCE_STEM}.m4a"


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


def voice_home() -> Path:
    """Return the canonical directory for clone clips.

    :returns: ``Path.home() / ".voice"``, which is ``~/.voice/`` on
        macOS, Linux, and Windows.
    """
    return Path.home() / ".voice"


def default_reference_path() -> Path:
    """Return the default clone-clip path.

    :returns: ``~/.voice/reference.m4a``.
    """
    return voice_home() / DEFAULT_REFERENCE_NAME


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


def resolve_reference(value: object) -> Path | None:
    """Resolve a clone clip under ``~/.voice/``.

    A relative name is joined onto :func:`voice_home`. ``~`` is expanded.
    An empty field uses :func:`default_reference_path`. When the named
    file is missing, the same stem is tried with ``.m4a``, then ``.wav``,
    then ``.mp3``.

    :param value: The ``reference`` field from a voice record.
    :returns: An existing clip, or None when nothing is on disk.
    """
    preferred = specified_reference_path(value)
    if preferred.is_file():
        return preferred
    return first_existing_reference(preferred)


def specified_reference_path(value: object) -> Path:
    """Return the path the registry asked for, even if it is missing.

    :param value: The ``reference`` field from a voice record.
    :returns: An absolute path. Empty input becomes the default clip.
    """
    expanded = expand_path(value)
    if expanded is None:
        return default_reference_path()
    if expanded.is_absolute():
        return expanded
    return voice_home() / expanded


def first_existing_reference(preferred: Path) -> Path | None:
    """Return the first existing clip for ``preferred``'s stem.

    Lookup order is ``.m4a``, then ``.wav``, then ``.mp3``.

    :param preferred: Path whose parent and stem define the search.
    :returns: An existing file, or None.
    """
    parent = preferred.parent
    stem = preferred.stem
    for extension in REFERENCE_EXTENSIONS:
        candidate = parent / f"{stem}{extension}"
        if candidate.is_file():
            return candidate
    return None


def missing_reference_message(value: object = None) -> str:
    """Return the error shown when no clone clip is on disk.

    :param value: The ``reference`` field from the voice record.
    :returns: A message that names ``~/.voice/`` and the lookup order.
    """
    expected = specified_reference_path(value)
    return (
        "Error: voice reference clip is missing. "
        f"Expected {expected}. Looked in ~/.voice/ for "
        f"{REFERENCE_STEM}.m4a, then {REFERENCE_STEM}.wav, then "
        f"{REFERENCE_STEM}.mp3. Put a short clean sample of your voice at "
        "~/.voice/reference.m4a (create ~/.voice/ if needed), or set the "
        "reference field in voices.yaml to a file under ~/.voice/."
    )


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
