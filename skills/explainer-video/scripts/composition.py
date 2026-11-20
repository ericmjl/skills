"""Turn a timeline document into a HyperFrames ``index.html``.

The HTML is a timing scaffold plus a cumulative picture. A path-shaped
``delta`` grows a file tree. A sentence delta stays a labeled row, with the
visual note under it. Motion is a paused GSAP timeline: no timers, no
``Math.random``, no CSS animations.
"""

from __future__ import annotations

import html
import json
from typing import Any

from visuals import render_picture


class CompositionError(ValueError):
    """The timeline document cannot be rendered."""


def render_html(timeline: dict[str, Any]) -> str:
    """Render a seekable HyperFrames composition.

    :param timeline: Document from :func:`timeline.build_timeline`.
    :returns: A complete HTML document.
    :raises CompositionError: A required timeline field is missing.
    """
    required = (
        "width",
        "height",
        "duration",
        "music",
        "music_volume",
        "duck",
        "placements",
        "fps",
        "artifact",
        "voice",
    )
    missing = [key for key in required if key not in timeline]
    if missing:
        raise CompositionError(f"Timeline is missing: {', '.join(missing)}.")
    width = int(timeline["width"])
    height = int(timeline["height"])
    duration = float(timeline["duration"])
    placements = timeline["placements"]
    if not isinstance(placements, list) or not placements:
        raise CompositionError("Timeline placements must be a non-empty list.")
    style = _style(width, height)
    scenes = "\n".join(_scene(row) for row in placements)
    voices = "\n".join(_voice(row) for row in placements)
    warnings = "\n".join(_hold_warning(row) for row in placements if _hold_seconds(row) > 4.0)
    automation = json.dumps(
        {"version": 1, "lanes": [{"target": "volume", "points": timeline["duck"]}]},
        separators=(",", ":"),
    )
    music_src = html.escape(str(timeline["music"]), quote=True)
    artifact = html.escape(str(timeline["artifact"]))
    voice = html.escape(str(timeline["voice"]))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{artifact or "Explainer"}</title>
  <style>
{style}
  </style>
</head>
<body>
  <!-- Voice {voice}. Path deltas render as a file tree. A sentence delta stays
       a labeled row. Banned: centered title on a gradient, fade-only
       entrances, system-font body paragraphs, a shot with nothing new for 4s. -->
{warnings}
  <div
    id="stage"
    data-composition-id="explainer"
    data-start="0"
    data-width="{width}"
    data-height="{height}"
    data-duration="{duration:.3f}"
  >
{scenes}
{voices}
    <audio
      id="music"
      src="{music_src}"
      data-start="0"
      data-duration="{duration:.3f}"
      data-track-index="3"
      data-volume="{float(timeline["music_volume"]):.3f}"
      data-timeline-role="music"
      data-automation='{automation}'
    ></audio>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{_tweens(placements)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines.explainer = tl;
  </script>
</body>
</html>
"""


def _style(width: int, height: int) -> str:
    """CSS for one aspect.

    :param width: Composition width.
    :param height: Composition height.
    :returns: CSS rules.
    """
    vertical = height > width
    pad_top = 150 if vertical else 72
    pad_side = 70 if vertical else 96
    pad_bottom = 180 if vertical else 80
    kicker = 32 if vertical else 28
    line = 56 if vertical else 48
    return f"""    html, body {{
      margin: 0;
      background: #222225;
      color: #e8e9ed;
    }}
    #stage {{
      position: relative;
      width: {width}px;
      height: {height}px;
      overflow: hidden;
      background: #222225;
      font-family: "Berkeley Mono", "BerkeleyMono", "DejaVu Sans Mono", "Liberation Mono", "Nimbus Mono PS", "Noto Sans Mono", ui-monospace, monospace;
    }}
    .scene {{
      position: absolute;
      inset: 0;
      box-sizing: border-box;
      padding: {pad_top}px {pad_side}px {pad_bottom}px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      gap: 24px;
    }}
    .kicker {{
      color: #62c4ff;
      font-size: {kicker}px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .tree {{
      list-style: none;
      padding: 0;
      margin: 0;
      font-size: {kicker}px;
      line-height: 1.35;
      color: #9aa0a8;
    }}
    .tree .added {{
      color: #e8e9ed;
    }}
    .filetree {{
      list-style: none;
      padding: 0;
      margin: 0 0 12px;
      font-size: 30px;
      line-height: 1.3;
      color: #9aa0a8;
    }}
    .filetree ul {{
      list-style: none;
      margin: 0;
      padding-left: 36px;
    }}
    .filetree .added {{
      color: #e8e9ed;
    }}
    .forest {{
      display: flex;
      gap: 32px;
      align-items: flex-start;
    }}
    .forest .filetree {{
      margin: 0;
    }}
    .scene.diagram {{
      justify-content: center;
    }}
    .scene.diagram .line {{
      font-size: {max(28, line // 2)}px;
      font-weight: 500;
      color: #9aa0a8;
    }}
    .line {{
      font-size: {line}px;
      line-height: 1.15;
      font-weight: 700;
      max-width: {width - 2 * pad_side}px;
    }}"""


def _scene(row: dict[str, Any]) -> str:
    """One visual clip.

    :param row: A placement row from the timeline.
    :returns: HTML for the scene.
    """
    index = int(row["index"])
    start = float(row["start"])
    scene_duration = float(row["duration"]) + float(row["gap_after"])
    join = str(row["join"])
    kicker = {"none": "Start", "but": "But", "therefore": "Therefore", "caveat": "Caveat"}[join]
    visual = html.escape(str(row["visual"]))
    words = len(str(row["spoken"]).split())
    tree = _tree(row)
    kind = "clip scene diagram" if "filetree" in tree else "clip scene"
    return f"""    <!-- spoken-words: {words} -->
    <section
      id="beat-{index}"
      class="{kind}"
      data-start="{start:.3f}"
      data-duration="{scene_duration:.3f}"
      data-track-index="1"
    >
      <div class="kicker">{kicker}</div>
{tree}
      <div class="line" id="line-{index}">{visual}</div>
    </section>"""


def _tree(row: dict[str, Any]) -> str:
    """Persistent picture: a file tree when deltas are paths, otherwise rows.

    :param row: A placement row. ``picture`` is the cumulative delta list.
    :returns: HTML, or an empty string when nothing has been added yet.
    """
    picture = row.get("picture") or []
    if not isinstance(picture, list) or not picture:
        return ""
    delta = str(row.get("delta") or "none")
    added = delta if delta.strip().lower() != "none" else None
    rendered = render_picture([str(item) for item in picture], index=int(row["index"]), added=added)
    if rendered.startswith("<ul"):
        return "      " + rendered
    return rendered


def _voice(row: dict[str, Any]) -> str:
    """One narration clip.

    :param row: A placement row.
    :returns: An audio element whose duration is the speech, not the hold.
    """
    index = int(row["index"])
    src = html.escape(str(row["wav"]), quote=True)
    return f"""    <audio
      id="vo-{index}"
      src="{src}"
      data-start="{float(row["start"]):.3f}"
      data-duration="{float(row["duration"]):.3f}"
      data-track-index="2"
      data-volume="1"
    ></audio>"""


def _tweens(placements: list[dict[str, Any]]) -> str:
    """Entrance tweens, one per beat, at that beat's start time.

    :param placements: Timeline rows.
    :returns: JavaScript statements.
    """
    lines = []
    for row in placements:
        index = int(row["index"])
        start = float(row["start"])
        lines.append(
            "    "
            f'tl.from("#line-{index}", {{ y: 36, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {start:.3f});'
        )
        delta = str(row.get("delta") or "none")
        if delta.strip().lower() != "none" and row.get("picture"):
            lines.append(
                "    "
                f'tl.from("#beat-{index} .added", {{ y: 24, autoAlpha: 0, duration: 0.4, '
                f'ease: "power3.out" }}, {start:.3f});'
            )
    return "\n".join(lines)


def _hold_seconds(row: dict[str, Any]) -> float:
    """Return how long the visual holds.

    :param row: Timeline row.
    :returns: Speech plus the following gap.
    """
    return float(row["duration"]) + float(row["gap_after"])


def _hold_warning(row: dict[str, Any]) -> str:
    """Comment that flags a hold a single entrance cannot carry.

    :param row: Timeline row.
    :returns: An HTML comment.
    """
    index = int(row["index"])
    held = _hold_seconds(row)
    return (
        f"  <!-- WARN beat {index} holds {held:.1f}s on one entrance. "
        "Add a second visual change before the final render. -->"
    )
