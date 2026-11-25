"""Seek-safe camera timing for a HyperFrames composition.

Push-in duration follows a logarithmic zoom curve so a doubling of
magnification always takes the same time. The composition applies the
result on a paused GSAP timeline; nothing here uses wall-clock timers.
"""

from __future__ import annotations

import math

# 1x -> 2x takes 0.55 s. Smaller jumps clamp to 0.30 s, larger to 0.94 s.
ZOOM_SECONDS_PER_DOUBLE: float = 0.55
ZOOM_DURATION_MIN: float = 0.30
ZOOM_DURATION_MAX: float = 0.94
DEFAULT_PUSH_ZOOM: float = 1.45
MIN_PUSH_ZOOM: float = 1.25


def zoom_duration(start_zoom: float, end_zoom: float) -> float:
    """Return the push-in or pull-out duration in seconds.

    ``0.55 * |ln(z2 / z1)| / ln(2)``, clamped to ``[0.30, 0.94]``.
    A doubling of zoom is 0.55 s. Equal zooms still take the minimum so a
    pan between two nodes at the same magnification is not instantaneous.

    :param start_zoom: Magnification at the start of the move. Must be > 0.
    :param end_zoom: Magnification at the end of the move. Must be > 0.
    :returns: Duration in seconds, already clamped.
    :raises ValueError: A zoom is not positive.
    """
    if start_zoom <= 0 or end_zoom <= 0:
        raise ValueError(
            f"Zoom levels must be positive, got {start_zoom} -> {end_zoom}."
        )
    if math.isclose(start_zoom, end_zoom, rel_tol=0.0, abs_tol=1e-12):
        return ZOOM_DURATION_MIN
    raw = ZOOM_SECONDS_PER_DOUBLE * abs(math.log(end_zoom / start_zoom)) / math.log(2.0)
    return min(ZOOM_DURATION_MAX, max(ZOOM_DURATION_MIN, raw))


def parse_push(value: str | None) -> str:
    """Normalize a beat's ``push`` field.

    :param value: Raw field, or None when omitted.
    :returns: ``auto``, ``none``, or a decimal zoom string.
    :raises ValueError: The value is not a recognized push setting.
    """
    text = (value or "auto").strip()
    if not text:
        return "auto"
    lowered = text.lower()
    if lowered in {"auto", "none", "off"}:
        return "none" if lowered == "off" else lowered
    try:
        zoom = float(text)
    except ValueError as exc:
        raise ValueError(
            f"push must be auto, none, or a zoom number, got {text!r}."
        ) from exc
    if zoom <= 0:
        raise ValueError("push zoom must be positive.")
    return text.strip()


def resolve_push_zoom(push: str, *, has_file_target: bool) -> float | None:
    """Return the zoom to use for this beat, or None to skip the camera.

    ``auto`` pushes to :data:`DEFAULT_PUSH_ZOOM` when the beat added a
    file-tree node. An explicit number below :data:`MIN_PUSH_ZOOM` is
    skipped (it reads as a wobble, not a push-in).

    :param push: Normalized ``auto`` / ``none`` / zoom string.
    :param has_file_target: True when this beat introduced a file-tree node.
    :returns: Zoom level, or None when the camera should hold.
    """
    lowered = push.strip().lower()
    if lowered in {"none", "off", "0", "false"}:
        return None
    if lowered in {"", "auto"}:
        return DEFAULT_PUSH_ZOOM if has_file_target else None
    zoom = float(push)
    if zoom < MIN_PUSH_ZOOM:
        return None
    return zoom
