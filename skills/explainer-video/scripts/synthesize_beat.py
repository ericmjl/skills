#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer>=0.12",
#   "pyyaml>=6",
#   "loguru>=0.7",
#   "torch>=2.3",
#   "torchaudio>=2.3",
# ]
# # CosyVoice is not a PyPI distribution. Import it from the git clone named by
# # cosyvoice_repo in voices.yaml (https://github.com/FunAudioLLM/CosyVoice).
# # On aarch64, install torch and torchaudio from the cu130 index before this
# # script. The clone's requirements.txt pins cu121, which has no aarch64 wheel.
# # See references/tts-models.md.
# ///
"""Synthesize explainer beats with the voice registry's model.

The primary model is Fun-CosyVoice3. The import is local and optional: this
environment did not run the model. ``--dry-run`` writes the normalized line
and does not import torch. Omit ``--beat`` to synthesize every beat in one
process. The CosyVoice weights load once and stay cached for that process.

    uv run skills/explainer-video/scripts/synthesize_beat.py PROJECT --dry-run
    uv run skills/explainer-video/scripts/synthesize_beat.py PROJECT --beat 0 --dry-run
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import typer
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from asr_check import record_voice_log
from loudness import SPEECH_LUFS, LoudnessError, normalize_wav
from normalize import LexiconError, load_lexicon, preserve_sound_codes
from pronunciation_qa import (
    DEFAULT_ATTEMPTS,
    DEFAULT_MIN_RATIO,
    review_pronunciation_takes,
    write_beat_report,
)
from reference_pad import (
    PAD_SECONDS,
    ReferencePadError,
    line_for_model,
    prepare_reference,
)
from timeline import ScriptError, parse_script
from voices import VoiceError, expand_path, get_voice, load_registry, target_for

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON = SKILL_ROOT / "lexicon.json"
DEFAULT_VOICES = SKILL_ROOT / "voices.yaml"
DEFAULT_CHATTERBOX_SCRIPT = (
    SKILL_ROOT.parent / "chatterbox-voice-clone" / "scripts" / "generate_narration.py"
)

DEFAULT_LEAD_IN = ""
_MODELS: dict[str, object] = {}

app = typer.Typer(add_completion=False, no_args_is_help=True)
logger.remove()
logger.add(sys.stderr, format="{message}")


@app.command()
def beat(
    project: Path = typer.Argument(..., help="Explainer project that contains script.md."),
    beat_index: int | None = typer.Option(
        None, "--beat", help="Beat index. Omit to synthesize every beat in one process."
    ),
    voice: str = typer.Option("", "--voice", help="Voice id. Default is the script Voice."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Write the normalized line only."),
    lexicon: Path = typer.Option(DEFAULT_LEXICON, "--lexicon"),
    voices: Path = typer.Option(DEFAULT_VOICES, "--voices"),
    attempts: int = typer.Option(
        DEFAULT_ATTEMPTS, "--attempts", help="Pronunciation QA takes, including the first."
    ),
    min_ratio: float = typer.Option(
        DEFAULT_MIN_RATIO,
        "--min-ratio",
        help="Retry while the first/last-aware whole-line ratio is below this.",
    ),
    loudness: bool = typer.Option(True, "--loudness/--no-loudness", help="Normalize each WAV before the mux."),
) -> None:
    """Normalize and synthesize one beat, or every beat when ``--beat`` is omitted."""
    script_path = project / "script.md"
    if not script_path.is_file():
        logger.error("Error: missing {}", script_path)
        raise typer.Exit(code=2)
    try:
        script = parse_script(script_path.read_text(encoding="utf-8"))
        lex = load_lexicon(lexicon)
        record = get_voice(load_registry(voices), voice or script.voice)
        target = target_for(str(record["model"]))
    except (ScriptError, LexiconError, VoiceError) as exc:
        logger.error("Error: {}", exc)
        raise typer.Exit(code=2) from exc
    if beat_index is None:
        chosen = list(script.beats)
    else:
        chosen = [item for item in script.beats if item.index == beat_index]
    if not chosen:
        logger.error("Error: script has no beat {}.", beat_index)
        raise typer.Exit(code=2)
    out_dir = project / "audio" / "beats"
    out_dir.mkdir(parents=True, exist_ok=True)
    voice_record = _with_padded_reference(record)
    written: list[Path] = []
    for item in chosen:
        result = lex.apply(item.spoken, target)
        for warning in result.warnings:
            logger.warning("{}", warning)
        text_path = out_dir / f"{item.index:02d}.spoken.txt"
        text_path.write_text(result.text + "\n", encoding="utf-8")
        typer.echo(result.text)
        written.append(text_path)
        if dry_run:
            continue
        wav_path = out_dir / f"{item.index:02d}.wav"
        expected = lex.apply(item.spoken, "chatterbox").text
        produced = result.text
        try:
            checked = review_pronunciation_takes(
                wav_path,
                spoken=item.spoken,
                respelled=expected,
                lexicon=lex,
                synthesize=lambda line=produced, path=wav_path: _produce(
                    line, voice_record, path, loudness
                ),
                attempts=attempts,
                min_ratio=min_ratio,
                index=item.index,
            )
        except (OSError, LoudnessError) as exc:
            logger.error("Error: {}", exc)
            raise typer.Exit(code=2) from exc
        write_beat_report(out_dir / f"{item.index:02d}.qa.json", checked)
        record_voice_log(project / "voice_log.json", item.index, checked)
        if checked["accepted"]:
            typer.echo(f"Wrote {wav_path} (ratio {checked['ratio']:.2f})")
        else:
            logger.warning(
                "Beat {} stayed at first={} last={} ratio {} after {} takes. "
                "See audio/beats/{:02d}.qa.json. This is a signal, not proof.",
                item.index,
                checked["first_ok"],
                checked["last_ok"],
                checked["ratio"],
                len(checked["attempts"]),
                item.index,
            )
            typer.echo(f"Wrote {wav_path} (ratio {checked['ratio']:.2f}, not accepted)")
    if dry_run:
        names = ", ".join(path.name for path in written)
        typer.echo(f"Dry run. Wrote {names}. No model was loaded.")


def _produce(text: str, record: dict[str, object], wav_path: Path, loudness: bool) -> None:
    """Synthesize one take and, by default, normalize it before the mux.

    :param text: Normalized line.
    :param record: Voice record. May already point at a padded reference.
    :param wav_path: Destination WAV.
    :param loudness: When true, two-pass loudnorm runs on the new WAV.
    :raises LoudnessError: ffmpeg cannot normalize the take.
    """
    synthesize_line(text, record, wav_path)
    if loudness:
        normalize_wav(wav_path, target_i=SPEECH_LUFS)


def _with_padded_reference(record: dict[str, object]) -> dict[str, object]:
    """Point a CosyVoice record at a reference with trailing silence.

    The original clip is not modified. When the pad cannot be written, the
    record is returned unchanged. The line is still sent without a spoken filler.

    :param record: Voice record from the registry.
    :returns: A copy. ``_reference_padded`` says whether the pad is in use.
    """
    prepared = dict(record)
    if str(record.get("model")) != "cosyvoice3":
        prepared["_reference_padded"] = False
        return prepared
    seconds = _pad_seconds()
    reference = expand_path(record.get("reference"))
    if seconds <= 0 or reference is None:
        prepared["_reference_padded"] = False
        return prepared
    try:
        padded = prepare_reference(reference, seconds=seconds)
    except ReferencePadError as exc:
        logger.warning("{}. Sending the line without a spoken filler.", exc)
        prepared["_reference_padded"] = False
        return prepared
    prepared["reference"] = str(padded)
    prepared["_reference_padded"] = True
    logger.info("Using a reference with {:.1f}s of trailing silence: {}", seconds, padded)
    return prepared


def _pad_seconds() -> float:
    """Read the reference pad length from the environment.

    :returns: Seconds of trailing silence. ``0`` disables the pad.
    """
    raw = os.environ.get("COSYVOICE_REFERENCE_PAD", str(PAD_SECONDS))
    try:
        return float(raw)
    except ValueError:
        logger.warning("COSYVOICE_REFERENCE_PAD={!r} is not a number. Using {}.", raw, PAD_SECONDS)
        return PAD_SECONDS


def synthesize_line(text: str, record: dict[str, object], wav_path: Path) -> None:
    """Synthesize ``text`` with the voice record's model.

    :param text: Already normalized spoken line.
    :param record: One voice from the registry.
    :param wav_path: Destination WAV.
    :raises SystemExit: The model, the reference clip, or the device is missing.
    """
    model = str(record["model"])
    if model == "cosyvoice3":
        _synthesize_cosyvoice(text, record, wav_path)
        return
    if model in {"chatterbox-turbo", "chatterbox-tts"}:
        _synthesize_chatterbox(text, record, wav_path)
        return
    raise SystemExit(
        f"Error: model {model!r} is not wired. See references/tts-models.md."
    )


def _synthesize_cosyvoice(text: str, record: dict[str, object], wav_path: Path) -> None:
    """Call Fun-CosyVoice3 the way example.py does.

    Not executed in the environment that added this skill. The call shape
    follows FunAudioLLM/CosyVoice ``example.py`` as read on 2026-11-20.

    :param text: Normalized line. May contain CMU tokens.
    :param record: Voice record.
    :param wav_path: Destination WAV.
    """
    reference = expand_path(record.get("reference"))
    model_dir = expand_path(record.get("model_dir"))
    repo = expand_path(record.get("cosyvoice_repo"))
    if reference is None or not reference.is_file():
        raise SystemExit(
            "Error: voice reference clip is missing. "
            f"Expected {reference}. Put a clone clip at the path in voices.yaml "
            "(default ~/voice/eric-voice-ref.m4a), or edit that file."
        )
    if model_dir is None or not model_dir.is_dir():
        raise SystemExit(
            "Error: Fun-CosyVoice3 weights not found. Download "
            "FunAudioLLM/Fun-CosyVoice3-0.5B-2512 into "
            f"{model_dir}. On aarch64, do not pip install -r requirements.txt. "
            "That file pins cu121. Install torch from the cu130 index. "
            "See references/tts-models.md."
        )
    if repo is not None:
        sys.path.insert(0, str(repo))
        matcha = repo / "third_party" / "Matcha-TTS"
        if matcha.is_dir():
            sys.path.insert(0, str(matcha))
    ensure_hf_home()
    try:
        import torch
        import torchaudio
        from cosyvoice.cli.cosyvoice import AutoModel
    except ImportError as exc:
        raise SystemExit(
            "Error: cannot import CosyVoice. Clone https://github.com/FunAudioLLM/CosyVoice "
            "with --recursive, install its requirements, and set cosyvoice_repo in voices.yaml. "
            "On aarch64 use the cu130 torch index, not the cu121 pins. "
            f"Import error: {exc}"
        ) from exc
    try:
        from cosyvoice.cli import frontend
        from cosyvoice.utils import frontend_utils

        install_sound_code_shield(frontend_utils, frontend)
    except ImportError:
        logger.warning("Could not patch CosyVoice spell_out_number. Sound codes may be garbled.")
    settings = record.get("settings") if isinstance(record.get("settings"), dict) else {}
    device = str(settings.get("device", "cuda"))
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit(
            "Error: CUDA is not available, so Fun-CosyVoice3 was not run. "
            "Synthesize on a CUDA box (the GB10 notes are in references/tts-models.md). "
            "On a Mac, use voice eric-mac. This script did not fall back silently."
        )
    prompt = "You are a helpful assistant.<|endofprompt|>"
    transcript = str(record.get("reference_transcript") or "").strip()
    spoken = line_for_model(
        text,
        reference_padded=bool(record.get("_reference_padded")),
        lead_in=os.environ.get("COSYVOICE_LEAD_IN"),
    )
    model = cached_model(str(model_dir), lambda: _load_cosyvoice(AutoModel, model_dir, device))
    if transcript:
        chunks = model.inference_zero_shot(
            spoken, prompt + transcript, str(reference), stream=False
        )
    else:
        logger.warning(
            "reference_transcript is empty. Using inference_cross_lingual. "
            "Fill the transcript when you have it; zero-shot uses it."
        )
        chunks = model.inference_cross_lingual(prompt + spoken, str(reference), stream=False)
    pieces = []
    for item in chunks:
        speech = item["tts_speech"]
        pieces.append(speech if speech.dim() == 2 else speech.unsqueeze(0))
    if not pieces:
        raise SystemExit("Error: CosyVoice returned no audio.")
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(wav_path), torch.cat(pieces, dim=-1).cpu(), model.sample_rate)


def resolve_chatterbox_script() -> Path:
    """Return the Chatterbox helper script.

    ``CHATTERBOX_SCRIPT`` wins when set. Otherwise this looks for a sibling
    ``chatterbox-voice-clone`` skill, which is not shipped in this repository.
    """
    env = os.environ.get("CHATTERBOX_SCRIPT", "").strip()
    if env:
        return Path(env).expanduser()
    return DEFAULT_CHATTERBOX_SCRIPT


def _synthesize_chatterbox(text: str, record: dict[str, object], wav_path: Path) -> None:
    """Hand one line to an optional Chatterbox helper script.

    :param text: Respelling-normalized line.
    :param record: Voice record.
    :param wav_path: Destination WAV. Copied out of that helper's output directory.
    """
    reference = expand_path(record.get("reference"))
    if reference is None or not reference.is_file():
        raise SystemExit(f"Error: voice reference clip is missing: {reference}")
    helper = resolve_chatterbox_script()
    if not helper.is_file():
        raise SystemExit(
            "Error: Chatterbox helper script is missing at "
            f"{helper}. Install chatterbox-voice-clone as a sibling skill, "
            "or set CHATTERBOX_SCRIPT to its generate_narration.py."
        )
    settings = record.get("settings") if isinstance(record.get("settings"), dict) else {}
    model_name = str(settings.get("chatterbox_model", "turbo"))
    device = str(settings.get("device", "")).strip()
    uv_bin = _uv()
    with tempfile.TemporaryDirectory(prefix="explainer-chatterbox-") as tmp:
        work = Path(tmp)
        script_path = work / "line.txt"
        script_path.write_text(text + "\n", encoding="utf-8")
        out_dir = work / "out"
        command = [
            uv_bin,
            "run",
            str(helper),
            "--script",
            str(script_path),
            "--voice-ref",
            str(reference),
            "--out",
            str(out_dir),
            "--model",
            model_name,
        ]
        if device:
            command.extend(["--device", device])
        logger.info("Running Chatterbox helper for one beat.")
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            raise SystemExit(
                f"Error: Chatterbox helper exited {completed.returncode}. "
                "See that script's troubleshooting. Do not invent a second MPS patch."
            )
        produced = out_dir / "narration.wav"
        if not produced.is_file():
            raise SystemExit(f"Error: Chatterbox did not write {produced}.")
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        wav_path.write_bytes(produced.read_bytes())


def with_lead_in(text: str, pad: str | None = None) -> str:
    """Optionally prefix a word. The default is no prefix.

    CosyVoice sometimes swallows the first word. Trailing silence on the
    reference clip is the fix. Do not inject a spoken filler.

    :param text: Normalized line that will be sent to the model.
    :param pad: Explicit prefix. ``None`` or empty leaves the line alone.
    :returns: The line the model should speak.
    """
    chosen = DEFAULT_LEAD_IN if pad is None else pad.strip()
    if not chosen:
        return text
    if text.lower().startswith(chosen.lower()):
        return text
    return f"{chosen} {text}"


def cached_model(key: str, loader: Callable[[], object], cache: dict[str, object] | None = None) -> object:
    """Return the model for ``key``, loading it on the first call only.

    :param key: Cache key, usually the model directory.
    :param loader: Builds the model. Called once per key.
    :param cache: Store to use. The process-wide cache is the default.
    :returns: The loaded model.
    """
    store = _MODELS if cache is None else cache
    if key not in store:
        store[key] = loader()
    return store[key]


def install_sound_code_shield(utils_module: Any, frontend_module: Any | None = None) -> None:
    """Stop CosyVoice from spelling the digits inside sound codes.

    ``spell_out_number`` turns ``[IH1]`` into ``[IHone]``. The wrapper runs
    that function on the text outside the codes and copies each code through.
    Both the utils module and ``cosyvoice.cli.frontend`` are patched, because
    the frontend imports the function by name.

    :param utils_module: Module that defines ``spell_out_number``.
    :param frontend_module: Module that imported that function, if loaded.
    """
    original = utils_module.spell_out_number
    if getattr(original, "_explainer_shield", False):
        return

    def shielded(text: str, inflect_parser: object) -> str:
        return preserve_sound_codes(text, lambda span: original(span, inflect_parser))

    shielded._explainer_shield = True  # type: ignore[attr-defined]
    utils_module.spell_out_number = shielded  # type: ignore[attr-defined]
    if frontend_module is not None and hasattr(frontend_module, "spell_out_number"):
        frontend_module.spell_out_number = shielded  # type: ignore[attr-defined]


def resolve_hf_home(env: dict[str, str], default_cache: Path, fallback: Path) -> str | None:
    """Choose an HF_HOME when the default Hugging Face cache cannot be written.

    A root-owned ``~/.cache/huggingface`` makes the first synthesis hang.
    An ``HF_HOME`` that is already set is left alone.

    :param env: Environment mapping. Not mutated.
    :param default_cache: The cache Hugging Face would use with no HF_HOME.
    :param fallback: A directory the current user can create.
    :returns: The fallback path, or ``None`` when nothing should change.
    """
    if env.get("HF_HOME"):
        return None
    if _cache_writable(default_cache):
        return None
    return str(fallback)


def ensure_hf_home() -> None:
    """Set ``HF_HOME`` when the default cache is not writable by this user."""
    fallback = Path.cwd() / ".cache" / "huggingface"
    chosen = resolve_hf_home(dict(os.environ), Path.home() / ".cache" / "huggingface", fallback)
    if chosen is None:
        return
    Path(chosen).mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = chosen
    logger.warning(
        "HF_HOME was unset and the default Hugging Face cache is not writable. Using {}.",
        chosen,
    )


def _cache_writable(path: Path) -> bool:
    """Return whether ``path`` can be created or written by this user.

    :param path: Cache directory Hugging Face would use.
    :returns: True when this process can write there.
    """
    if path.exists():
        return os.access(path, os.W_OK)
    parent = path.parent
    return parent.exists() and os.access(parent, os.W_OK)


def _load_cosyvoice(auto_model: Callable[..., object], model_dir: Path, device: str) -> object:
    """Construct AutoModel once per directory.

    :param auto_model: CosyVoice ``AutoModel`` class.
    :param model_dir: Downloaded weights.
    :param device: Requested device, used only in the log line.
    :returns: The loaded model.
    """
    logger.info("Loading Fun-CosyVoice3 from {} on {}.", model_dir, device)
    return auto_model(model_dir=str(model_dir))


def _uv() -> str:
    """Find the uv binary.

    :returns: Absolute or PATH-resolved uv.
    :raises SystemExit: uv is not installed.
    """
    import shutil

    found = shutil.which("uv")
    if found is None:
        raise SystemExit("Error: uv is not on PATH. Install uv, then re-run this script with uv run.")
    return found


if __name__ == "__main__":
    app()
