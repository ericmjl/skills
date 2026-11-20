"""Script parsing, beat placement, and the music duck envelope.

Speech clips keep the duration of the TTS file. A cut moves onto a music beat
only by lengthening the silence after a clip, and only when a beat falls inside
the allowed gap. Speech is never time-stretched and never overlapped.
"""

from __future__ import annotations

import re
import wave
from dataclasses import dataclass, replace
from pathlib import Path

from visuals import split_delta

FIELD_RE = re.compile(
    r"^(?:-\s*)?(join|spoken|visual|number|source|delta)\s*:\s*(.*)$",
    re.IGNORECASE,
)
JOINS: frozenset[str] = frozenset({"none", "but", "therefore", "caveat"})
FORMAT_SHORT = "short"
FORMAT_BUILD_UP = "build-up"
FORMATS: frozenset[str] = frozenset({FORMAT_SHORT, FORMAT_BUILD_UP})
class ScriptError(ValueError):
    """The explainer script markdown is missing a required piece."""


@dataclass(frozen=True)
class Beat:
    """One problem-chain beat.

    :param index: Beat number from the ``## Beat N`` heading.
    :param join: ``none``, ``but``, ``therefore``, or ``caveat``.
    :param spoken: Line that goes to TTS. Shot notes stay out of this field.
    :param visual: What changes in the frame on this beat.
    :param number: Checked figure, or ``none``.
    :param source: Free text, often ``path:line`` or ``none``. Omitted means ``none``.
    :param delta: What this beat adds to the persistent on-screen picture.
        Omitted means ``none``. A path such as ``data/raw.csv`` grows a file tree.
    """

    index: int
    join: str
    spoken: str
    visual: str
    number: str
    source: str
    delta: str

    def with_spoken(self, spoken: str) -> Beat:
        """Return a copy with a new spoken line.

        :param spoken: Replacement line. This beat is unchanged.
        :returns: A new beat.
        """
        return replace(self, spoken=spoken)

    def with_delta(self, delta: str) -> Beat:
        """Return a copy with a new picture delta.

        :param delta: What this beat adds to the persistent picture.
        :returns: A new beat.
        """
        return replace(self, delta=delta)


@dataclass(frozen=True)
class Script:
    """A parsed explainer script.

    :param artifact: The one designed thing the viewer builds.
    :param voice: Voice id from ``voices.yaml``.
    :param beats: Beats in heading order.
    :param script_format: ``short`` or ``build-up``. Missing heading means short.
    """

    artifact: str
    voice: str
    beats: tuple[Beat, ...]
    script_format: str = FORMAT_SHORT

    def with_beats(self, beats: tuple[Beat, ...]) -> Script:
        """Return a copy with a new beat list.

        :param beats: Replacement beats, in order.
        :returns: A new script. This script is unchanged.
        """
        return replace(self, beats=beats)


@dataclass(frozen=True)
class Placement:
    """Where one speech clip sits on the timeline.

    :param index: Beat index.
    :param start: Start time in seconds.
    :param duration: Speech duration in seconds. This is the WAV length.
    :param gap_after: Silence after the speech, before the next start or the tail.
    """

    index: int
    start: float
    duration: float
    gap_after: float

    @property
    def end(self) -> float:
        """Return the end of the speech, not including the gap.

        :returns: ``start + duration``.
        """
        return self.start + self.duration


def parse_script(text: str) -> Script:
    """Parse the explainer script markdown.

    :param text: Full ``script.md`` contents.
    :returns: Artifact, voice id, and beats.
    :raises ScriptError: A required heading, field, or join is missing.
    """
    artifact = _section_body(text, "Artifact").strip()
    voice_body = _section_body(text, "Voice").strip()
    voice = voice_body.split()[0] if voice_body else ""
    if not voice:
        raise ScriptError("The Voice section needs a voice id from voices.yaml.")
    script_format = _parse_format(text)
    beats_body = _section_body(text, "Beats")
    raw_beats = re.split(r"(?m)^##\s+Beat\s+(\d+)\s*$", beats_body)
    if len(raw_beats) < 3:
        raise ScriptError("The Beats section needs at least one '## Beat N' heading.")
    beats: list[Beat] = []
    # re.split keeps the leading preamble at [0], then (number, body) pairs.
    chunks = raw_beats[1:]
    for number, body in zip(chunks[0::2], chunks[1::2], strict=True):
        beats.append(_parse_beat(int(number), body))
    indexes = [beat.index for beat in beats]
    if indexes != list(range(len(beats))):
        raise ScriptError(
            "Beat headings must be numbered 0, 1, 2, ... with no gaps. "
            f"Found {indexes}."
        )
    return Script(
        artifact=artifact,
        voice=voice,
        beats=tuple(beats),
        script_format=script_format,
    )


def _parse_format(text: str) -> str:
    """Read the optional Format heading.

    :param text: Full markdown.
    :returns: ``short`` or ``build-up``. Missing or empty means short.
    :raises ScriptError: The heading names an unknown format.
    """
    body = _section_body(text, "Format").strip()
    if not body:
        return FORMAT_SHORT
    value = body.split()[0].lower()
    if value not in FORMATS:
        raise ScriptError(f"Format must be short or build-up. Got {value!r}.")
    return value


def _section_body(text: str, heading: str) -> str:
    """Return the body under one top-level heading.

    :param text: Full markdown.
    :param heading: Heading text without the hash.
    :returns: Body until the next ``# `` heading, or an empty string.
    """
    pattern = re.compile(rf"(?m)^#\s+{re.escape(heading)}\s*$")
    match = pattern.search(text)
    if match is None:
        return ""
    rest = text[match.end() :]
    nxt = re.search(r"(?m)^#\s+", rest)
    if nxt is None:
        return rest
    return rest[: nxt.start()]


def _parse_beat(index: int, body: str) -> Beat:
    """Parse one beat body.

    :param index: Heading number.
    :param body: Lines under the heading.
    :returns: The beat.
    :raises ScriptError: A field is missing or the join is unknown.
    """
    fields: dict[str, str] = {}
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = FIELD_RE.match(stripped)
        if match is None:
            raise ScriptError(f"Beat {index} has a line that is not a field: {stripped}")
        fields[match.group(1).lower()] = match.group(2).strip()
    missing = [name for name in ("join", "spoken", "visual") if not fields.get(name)]
    if missing:
        raise ScriptError(f"Beat {index} is missing: {', '.join(missing)}.")
    join = fields["join"].lower()
    if join not in JOINS:
        raise ScriptError(
            f"Beat {index} join must be none, but, therefore, or caveat. Got {join!r}."
        )
    return Beat(
        index=index,
        join=join,
        spoken=fields["spoken"],
        visual=fields["visual"],
        number=fields.get("number") or "none",
        source=fields.get("source") or "none",
        delta=fields.get("delta") or "none",
    )


def wav_duration(path: Path) -> float:
    """Measure a PCM WAV duration.

    :param path: WAV file.
    :returns: Duration in seconds.
    :raises ScriptError: The file is missing or has no frames.
    """
    if not path.is_file():
        raise ScriptError(f"Audio file not found: {path}")
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
    if frames <= 0 or rate <= 0:
        raise ScriptError(f"Audio file has no duration: {path}")
    return frames / float(rate)


def place_on_beats(
    durations: list[float] | tuple[float, ...],
    music_beats: list[float] | tuple[float, ...],
    *,
    min_gap: float = 0.08,
    max_gap: float = 0.55,
    lead_in: float = 0.15,
    tail: float = 0.5,
) -> tuple[Placement, ...]:
    """Place speech clips on a music beat grid without shortening them.

    :param durations: Speech duration of each beat, in seconds.
    :param music_beats: Music beat times, in seconds. Empty is allowed.
    :param min_gap: Shortest silence between clips.
    :param max_gap: Longest silence the placer may insert to reach a beat.
    :param lead_in: Earliest start of the first clip.
    :param tail: Silence held after the last clip.
    :returns: One placement per duration.
    :raises ScriptError: A duration or gap setting is not usable.
    """
    if min_gap < 0 or max_gap < min_gap:
        raise ScriptError("max_gap must be greater than or equal to min_gap, and both >= 0.")
    if lead_in < 0 or tail < 0:
        raise ScriptError("lead_in and tail must be >= 0.")
    if not durations:
        raise ScriptError("No speech durations to place.")
    for duration in durations:
        if duration <= 0:
            raise ScriptError(f"Speech duration must be positive, got {duration}.")
    beats = tuple(sorted(float(item) for item in music_beats))
    start = _earliest_beat(lead_in, lead_in + max_gap, beats, fallback=lead_in)
    placed: list[Placement] = []
    for index, duration in enumerate(durations):
        if index == 0:
            clip_start = start
        else:
            previous = placed[-1]
            earliest = previous.end + min_gap
            latest = previous.end + max_gap
            clip_start = _earliest_beat(earliest, latest, beats, fallback=earliest)
            if clip_start < earliest - 1e-9:
                raise ScriptError("Placer produced an overlapping clip.")
        placed.append(
            Placement(index=index, start=clip_start, duration=float(duration), gap_after=0.0)
        )
    with_gaps: list[Placement] = []
    for index, placement in enumerate(placed):
        if index + 1 < len(placed):
            gap = placed[index + 1].start - placement.end
        else:
            gap = tail
        with_gaps.append(
            Placement(
                index=placement.index,
                start=placement.start,
                duration=placement.duration,
                gap_after=gap,
            )
        )
    return tuple(with_gaps)


def _earliest_beat(earliest: float, latest: float, beats: tuple[float, ...], *, fallback: float) -> float:
    """Return the earliest beat inside ``[earliest, latest]``, or the fallback.

    :param earliest: Inclusive window start.
    :param latest: Inclusive window end.
    :param beats: Sorted beat times.
    :param fallback: Time to use when the window holds no beat.
    :returns: A time that is never earlier than ``earliest``.
    """
    for beat in beats:
        if beat < earliest - 1e-9:
            continue
        if beat > latest + 1e-9:
            break
        return beat
    return fallback


def duck_points(
    placements: tuple[Placement, ...] | list[Placement],
    *,
    bed: float = 1.0,
    ducked: float = 0.35,
    ramp: float = 0.12,
) -> list[dict[str, float]]:
    """Build a HyperFrames volume lane that dips under each speech clip.

    Times are clip-relative. Put the lane on a music element whose
    ``data-start`` is 0. ``data-fx-carve`` is not a substitute: HyperFrames
    does not read that attribute at playback.

    :param placements: Speech placements.
    :param bed: Linear gain between clips.
    :param ducked: Linear gain during speech.
    :param ramp: Desired ramp length. Shorter gaps use a shorter ramp.
    :returns: Points shaped ``{"t": seconds, "v": gain}``.
    :raises ScriptError: Points would run backwards.
    """
    if bed <= 0 or ducked <= 0 or ramp < 0:
        raise ScriptError("bed and ducked must be positive, and ramp must be >= 0.")
    points: list[tuple[float, float]] = []

    def add(when: float, gain: float) -> None:
        when = round(max(0.0, when), 3)
        gain = round(gain, 3)
        if points and when < points[-1][0] - 1e-9:
            raise ScriptError(f"Duck envelope went backwards at {when}.")
        if points and abs(points[-1][0] - when) < 1e-9:
            points[-1] = (when, gain)
            return
        points.append((when, gain))

    if not placements:
        add(0.0, bed)
        return [{"t": when, "v": gain} for when, gain in points]

    first = placements[0]
    add(0.0, ducked if first.start <= 0 else bed)
    for index, placement in enumerate(placements):
        if placement.start > 0:
            if index == 0:
                usable = min(ramp, placement.start)
            else:
                gap = placement.start - placements[index - 1].end
                usable = 0.0 if gap <= 0 else min(ramp, gap / 2.0)
            down_at = placement.start - usable
            if not points or points[-1][0] < down_at - 1e-9:
                add(down_at, bed)
        add(placement.start, ducked)
        add(placement.end, ducked)
        if index + 1 == len(placements):
            usable_up = min(ramp, placement.gap_after) if placement.gap_after > 0 else 0.0
        else:
            gap_after = placements[index + 1].start - placement.end
            usable_up = 0.0 if gap_after <= 0 else min(ramp, gap_after / 2.0)
        add(placement.end + usable_up, bed)
    return [{"t": when, "v": gain} for when, gain in points]


def beat_wav_name(index: int) -> str:
    """Return the project-relative WAV path for a beat.

    :param index: Beat index.
    :returns: Path such as ``audio/beats/00.wav``.
    """
    return f"audio/beats/{index:02d}.wav"


def build_timeline(
    script: Script,
    durations: list[float] | tuple[float, ...],
    music_beats: list[float] | tuple[float, ...],
    *,
    music_path: str,
    music_duration: float,
    bpm: float,
    aspect: str = "9:16",
    min_gap: float = 0.08,
    max_gap: float = 0.55,
    lead_in: float = 0.15,
    tail: float = 0.5,
    fps: int = 30,
    bed: float = 1.0,
    ducked: float = 0.35,
    ramp: float = 0.12,
    music_volume: float = 0.7,
) -> dict[str, object]:
    """Assemble the timeline document the composition builder reads.

    :param script: Parsed script.
    :param durations: WAV duration for each beat, same order as the script.
    :param music_beats: Detected music beats. May be empty.
    :param music_path: Project-relative music path.
    :param music_duration: Music file duration in seconds.
    :param bpm: Estimated tempo. Use 0 when unknown.
    :param aspect: ``9:16`` or ``16:9``.
    :returns: A JSON-ready dictionary.
    :raises ScriptError: Counts, aspect, or durations do not line up.
    """
    if len(durations) != len(script.beats):
        raise ScriptError(
            f"Expected {len(script.beats)} speech durations, got {len(durations)}."
        )
    width, height = _aspect_size(aspect)
    placements = place_on_beats(
        durations,
        music_beats,
        min_gap=min_gap,
        max_gap=max_gap,
        lead_in=lead_in,
        tail=tail,
    )
    last = placements[-1]
    total = round(last.end + last.gap_after, 3)
    rows = []
    picture: list[str] = []
    for beat, placement in zip(script.beats, placements, strict=True):
        picture.extend(split_delta(beat.delta))
        rows.append(
            {
                "index": beat.index,
                "join": beat.join,
                "spoken": beat.spoken,
                "visual": beat.visual,
                "number": beat.number,
                "source": beat.source,
                "delta": beat.delta,
                "picture": list(picture),
                "start": round(placement.start, 3),
                "duration": round(placement.duration, 3),
                "gap_after": round(placement.gap_after, 3),
                "wav": beat_wav_name(beat.index),
            }
        )
    return {
        "fps": fps,
        "aspect": aspect,
        "width": width,
        "height": height,
        "artifact": script.artifact,
        "voice": script.voice,
        "music": music_path,
        "music_duration": round(music_duration, 3),
        "music_volume": music_volume,
        "bpm": bpm,
        "music_beats": [round(float(item), 3) for item in music_beats],
        "duration": total,
        "duck": duck_points(placements, bed=bed, ducked=ducked, ramp=ramp),
        "placements": rows,
    }


def _aspect_size(aspect: str) -> tuple[int, int]:
    """Map an aspect name to pixels.

    :param aspect: ``9:16`` or ``16:9``.
    :returns: Width and height.
    :raises ScriptError: The aspect is unknown.
    """
    if aspect == "9:16":
        return 1080, 1920
    if aspect == "16:9":
        return 1920, 1080
    raise ScriptError(f"Aspect must be 9:16 or 16:9, got {aspect!r}.")
