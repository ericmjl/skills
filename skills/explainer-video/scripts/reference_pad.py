"""Add trailing silence to a voice reference clip.

CosyVoice drops the first word of a line when the reference ends on speech.
About 0.8 seconds of silence at the end of the clip fixed that on the GB10
render. Never inject a spoken filler. Trailing silence is the whole fix.
"""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path


class ReferencePadError(RuntimeError):
    """The reference clip could not be given trailing silence."""


PAD_SECONDS = 0.8


def line_for_model(text: str, *, reference_padded: bool, lead_in: str | None) -> str:
    """Choose the text CosyVoice should see.

    Trailing silence on the reference clip is what stops a dropped first word.
    This function never injects a spoken filler. ``lead_in`` prefixes only when
    the caller passes a non-empty string on purpose.

    :param text: Normalized line, without a sacrificial word.
    :param reference_padded: True when the reference clip has trailing silence.
        Kept so call sites stay the same. It does not change the text.
    :param lead_in: Explicit prefix. ``None`` or empty means none.
    :returns: The line to send to the model.
    """
    _ = reference_padded
    if lead_in is None:
        return text
    return _prefix(text, lead_in)


def prepare_reference(reference: Path, *, seconds: float = PAD_SECONDS) -> Path:
    """Write a WAV copy of ``reference`` with trailing silence.

    The original clip is left in place. A newer ``.padded.wav`` beside it is
    reused. PCM WAV is padded in-process. Anything else goes through ffmpeg.

    :param reference: Voice clip, WAV or a format ffmpeg can read.
    :param seconds: Silence to append. The GB10 render used about 0.8.
    :returns: Path to the padded WAV.
    :raises ReferencePadError: The clip cannot be padded.
    """
    if seconds < 0:
        raise ReferencePadError(f"Silence must be >= 0, got {seconds}.")
    if not reference.is_file():
        raise ReferencePadError(f"Reference clip not found: {reference}")
    destination = reference.with_name(reference.stem + ".padded.wav")
    if (
        destination.is_file()
        and destination.stat().st_mtime >= reference.stat().st_mtime
        and seconds > 0
    ):
        return destination
    if _is_pcm_wav(reference):
        append_wav_silence(reference, destination, seconds)
        return destination
    _pad_with_ffmpeg(reference, destination, seconds)
    return destination


def append_wav_silence(source: Path, destination: Path, seconds: float) -> None:
    """Append silence to a PCM WAV.

    :param source: Readable PCM WAV.
    :param destination: Where the padded WAV is written. May not be ``source``.
    :param seconds: Length of the silence.
    :raises ReferencePadError: The WAV cannot be read or written.
    """
    if destination.resolve() == source.resolve():
        raise ReferencePadError("Refusing to overwrite the original reference clip.")
    try:
        with wave.open(str(source), "rb") as handle:
            params = handle.getparams()
            frames = handle.readframes(handle.getnframes())
            rate = handle.getframerate()
            channels = handle.getnchannels()
            width = handle.getsampwidth()
    except wave.Error as exc:
        raise ReferencePadError(f"Cannot read WAV {source}: {exc}") from exc
    extra = round(seconds * rate) * channels * width
    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), "wb") as handle:
        handle.setparams(params)
        handle.writeframes(frames + (b"\x00" * extra))


def _prefix(text: str, pad: str) -> str:
    """Prefix ``pad`` unless it is empty or already there.

    :param text: Line.
    :param pad: Sacrificial first word.
    :returns: The line, possibly prefixed.
    """
    chosen = pad.strip()
    if not chosen or text.lower().startswith(chosen.lower()):
        return text
    return f"{chosen} {text}"


def _is_pcm_wav(path: Path) -> bool:
    """Return whether ``path`` opens as a PCM WAV.

    :param path: Candidate file.
    :returns: True when the stdlib wave module can read it.
    """
    if path.suffix.lower() != ".wav":
        return False
    try:
        with wave.open(str(path), "rb"):
            return True
    except (wave.Error, EOFError):
        return False


def _pad_with_ffmpeg(source: Path, destination: Path, seconds: float) -> None:
    """Append silence with ffmpeg's ``apad`` filter.

    :param source: Audio ffmpeg can decode.
    :param destination: Padded WAV.
    :param seconds: Silence to append.
    :raises ReferencePadError: ffmpeg is missing or the command fails.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise ReferencePadError(
            "ffmpeg is not on PATH, and the reference is not a PCM WAV. "
            "Install ffmpeg, or export the clip as WAV."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-af",
            f"apad=pad_dur={seconds}",
            str(destination),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not destination.is_file():
        detail = (completed.stderr or "").strip().splitlines()
        tail = detail[-1] if detail else "no stderr"
        raise ReferencePadError(f"ffmpeg could not pad {source}: {tail}")
