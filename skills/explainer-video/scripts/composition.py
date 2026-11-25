"""Turn a timeline document into a HyperFrames ``index.html``.

The HTML is a timing scaffold plus a cumulative picture. A path-shaped
``delta`` grows a file tree. A named template delta renders a number
counter, before/after stat, cause chain, or checklist. A sentence delta
stays a labeled row. Motion is a paused GSAP timeline: no timers, no
``Math.random``, no CSS animations. Camera push-ins live on a
``#viewport`` / ``#camera`` / ``#world`` / ``#hud`` rig.
"""

from __future__ import annotations

import html
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from camera import resolve_push_zoom, zoom_duration
from dead_zones import (
    BeatWindow,
    Tween,
    analyze_tweens,
    tween_comment,
)
from visuals import (
    is_file_path,
    parse_delta_kind,
    render_picture,
    split_delta,
    template_items,
)


class CompositionError(ValueError):
    """The timeline document cannot be rendered."""


@dataclass(frozen=True)
class Motion:
    """GSAP statements plus the tween map the dead-zone checker reads.

    :param prelude: Declarations that must run before the tweens.
    :param statements: ``tl.from`` / ``tl.to`` calls.
    :param tweens: Intervals recorded as HTML comments.
    :param needs_layout: True when a push-in measures an ``#added-N`` node.
    """

    prelude: str
    statements: tuple[str, ...]
    tweens: tuple[Tween, ...]
    needs_layout: bool


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
    orientation = "landscape" if width > height else "portrait"
    style = _style(width, height)
    scenes = "\n".join(_scene(row) for row in placements)
    hud = "\n".join(_hud_card(row) for row in placements)
    voices = "\n".join(_voice(row) for row in placements)
    motion = plan_motion(placements, width=width, height=height)
    warnings = _dead_zone_comments(motion.tweens, placements, duration)
    tween_map = "\n".join(f"  {tween_comment(item)}" for item in motion.tweens)
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
  <!-- Voice {voice}. Path deltas render as a file tree. Named template deltas
       render a number counter, before/after stat, cause chain, or checklist.
       A sentence delta stays a labeled row. Camera push-ins use CSS zoom on
       #world. Banned: centered title on a gradient, fade-only entrances,
       system-font body paragraphs, a shot with nothing new for 4s. -->
{warnings}
{tween_map}
  <div
    id="stage"
    class="{orientation}"
    data-composition-id="explainer"
    data-start="0"
    data-width="{width}"
    data-height="{height}"
    data-duration="{duration:.3f}"
  >
    <div id="viewport">
      <div id="camera">
        <div id="world">
{scenes}
        </div>
      </div>
      <div id="hud">
{hud}
      </div>
    </div>
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
{_camera_runtime(width, height, motion.needs_layout)}
{motion.prelude}
{chr(10).join(motion.statements)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines.explainer = tl;
    applyCam();
  </script>
</body>
</html>
"""


def plan_motion(
    placements: list[dict[str, Any]],
    *,
    width: int,
    height: int,
) -> Motion:
    """Build entrance, template, and camera tweens for every beat.

    :param placements: Timeline rows.
    :param width: Composition width in pixels.
    :param height: Composition height in pixels.
    :returns: JS plus the tween map.
    """
    prelude: list[str] = [
        "    function formatCount(n) {",
        "      const rounded = Math.round(n);",
        r'      return String(rounded).replace(/\B(?=(\d{3})+(?!\d))/g, ",");',
        "    }",
    ]
    statements: list[str] = []
    tweens: list[Tween] = []
    needs_layout = False
    zoom = 1.0
    center_x = width / 2.0
    center_y = height / 2.0

    def add(selector: str, start: float, duration: float, js: str) -> None:
        statements.append("    " + js)
        tweens.append(Tween(selector=selector, start=start, duration=duration))

    for row in placements:
        index = int(row["index"])
        start = float(row["start"])
        available = _hold_seconds(row)
        add(
            f"#line-{index}",
            start,
            0.4,
            f'tl.from("#line-{index}", {{ y: 36, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {start:.3f});',
        )
        delta = str(row.get("delta") or "none")
        kind = parse_delta_kind(delta)
        if kind is not None:
            name, payload = kind
            _plan_template(
                name,
                payload,
                index=index,
                start=start,
                available=available,
                prelude=prelude,
                add=add,
            )
        elif delta.strip().lower() != "none" and row.get("picture"):
            add(
                f"#beat-{index} .added",
                start,
                0.4,
                f'tl.from("#beat-{index} .added", {{ y: 24, autoAlpha: 0, duration: 0.4, '
                f'ease: "power3.out" }}, {start:.3f});',
            )
        has_file = any(is_file_path(piece) for piece in split_delta(delta))
        target_zoom = resolve_push_zoom(
            str(row.get("push") or "auto"),
            has_file_target=has_file,
        )
        if target_zoom is not None:
            duration = zoom_duration(zoom, target_zoom)
            selector = f"#added-{index}"
            add(
                "cam",
                start,
                duration,
                (
                    f'{{ const p = layoutCenter("{selector}"); '
                    f"tl.to(cam, {{ cx: p.x, cy: p.y, zoom: {target_zoom:.3f}, "
                    f'duration: {duration:.3f}, ease: "power3.inOut", '
                    f"onUpdate: applyCam }}, {start:.3f}); }}"
                ),
            )
            zoom = target_zoom
            needs_layout = True
        elif zoom != 1.0:
            duration = zoom_duration(zoom, 1.0)
            add(
                "cam",
                start,
                duration,
                (
                    f"tl.to(cam, {{ cx: {center_x:.1f}, cy: {center_y:.1f}, zoom: 1, "
                    f'duration: {duration:.3f}, ease: "power3.inOut", '
                    f"onUpdate: applyCam }}, {start:.3f});"
                ),
            )
            zoom = 1.0

    if zoom != 1.0:
        last = placements[-1]
        pull_at = float(last["start"]) + float(last["duration"])
        duration = zoom_duration(zoom, 1.0)
        add(
            "cam",
            pull_at,
            duration,
            (
                f"tl.to(cam, {{ cx: {center_x:.1f}, cy: {center_y:.1f}, zoom: 1, "
                f'duration: {duration:.3f}, ease: "power3.inOut", '
                f"onUpdate: applyCam }}, {pull_at:.3f});"
            ),
        )

    return Motion(
        prelude="\n".join(prelude),
        statements=tuple(statements),
        tweens=tuple(tweens),
        needs_layout=needs_layout,
    )


def _plan_template(
    kind: str,
    payload: dict[str, Any],
    *,
    index: int,
    start: float,
    available: float,
    prelude: list[str],
    add: Callable[[str, float, float, str], None],
) -> None:
    """Append seek-safe tweens for a named picture template.

    :param kind: Template id.
    :param payload: Parsed delta fields.
    :param index: Beat index.
    :param start: Beat start time.
    :param available: Speech plus gap, used to fit count durations.
    :param prelude: JS declarations to extend.
    :param add: Callable ``(selector, start, duration, js)``.
    """
    if kind == "number-counter":
        target = float(payload.get("value") or payload.get("target") or payload.get("targetValue") or 0)
        count_dur = min(2.2, max(0.6, available - 0.6))
        prelude.append(f"    const counter{index} = {{ val: 0 }};")
        prelude.append(
            f'    const counterValue{index} = document.querySelector("#counter-value-{index}");'
        )
        add(
            f"#counter-{index} .delta-kicker",
            start,
            0.4,
            f'tl.from("#counter-{index} .delta-kicker", {{ y: 24, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {start:.3f});',
        )
        count_at = start + 0.15
        add(
            f"counter{index}",
            count_at,
            count_dur,
            (
                f"tl.to(counter{index}, {{ val: {target:g}, duration: {count_dur:.3f}, "
                f'ease: "power3.out", onUpdate: () => {{ '
                f"if (counterValue{index}) counterValue{index}.textContent = "
                f"formatCount(counter{index}.val); }} }}, {count_at:.3f});"
            ),
        )
        add(
            f"#counter-suffix-{index}",
            start + 0.35,
            0.35,
            f'tl.from("#counter-suffix-{index}", {{ autoAlpha: 0, duration: 0.35, '
            f'ease: "power2.out" }}, {start + 0.35:.3f});',
        )
        return
    if kind == "before-after-stat":
        after = float(payload.get("after") or payload.get("afterValue") or 0)
        count_dur = min(1.4, max(0.5, available - 0.8))
        prelude.append(f"    const stat{index} = {{ val: 0 }};")
        prelude.append(
            f'    const statAfter{index} = document.querySelector("#stat-after-{index}");'
        )
        add(
            f"#stat-{index} .delta-before",
            start,
            0.4,
            f'tl.from("#stat-{index} .delta-before", {{ y: 24, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {start:.3f});',
        )
        after_at = start + 0.35
        add(
            f"#stat-{index} .delta-after",
            after_at,
            0.4,
            f'tl.from("#stat-{index} .delta-after", {{ y: 24, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {after_at:.3f});',
        )
        add(
            f"stat{index}",
            after_at,
            count_dur,
            (
                f"tl.to(stat{index}, {{ val: {after:g}, duration: {count_dur:.3f}, "
                f'ease: "power3.out", onUpdate: () => {{ '
                f"if (statAfter{index}) statAfter{index}.textContent = "
                f"formatCount(stat{index}.val); }} }}, {after_at:.3f});"
            ),
        )
        add(
            f"#stat-{index} .delta-note",
            start + 0.7,
            0.4,
            f'tl.from("#stat-{index} .delta-note", {{ y: 16, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {start + 0.7:.3f});',
        )
        return
    if kind == "cause-chain":
        add(
            f"#chain-{index} .delta-kicker",
            start,
            0.4,
            f'tl.from("#chain-{index} .delta-kicker", {{ y: 24, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {start:.3f});',
        )
        add(
            f"#chain-fill-{index}",
            start + 0.2,
            0.8,
            f'tl.from("#chain-fill-{index}", {{ scaleX: 0, duration: 0.8, '
            f'ease: "power2.inOut", transformOrigin: "left center" }}, {start + 0.2:.3f});',
        )
        for ordinal in range(3):
            step_at = start + 0.35 + ordinal * 0.45
            add(
                f"#chain-step-{index}-{ordinal}",
                step_at,
                0.4,
                f'tl.from("#chain-step-{index}-{ordinal}", {{ y: 20, autoAlpha: 0, duration: 0.4, '
                f'ease: "power3.out" }}, {step_at:.3f});',
            )
        return
    if kind == "checklist-pop":
        items = template_items(payload) or ("Item",)
        add(
            f"#checks-{index} .delta-kicker",
            start,
            0.4,
            f'tl.from("#checks-{index} .delta-kicker", {{ y: 24, autoAlpha: 0, duration: 0.4, '
            f'ease: "power3.out" }}, {start:.3f});',
        )
        for ordinal, _item in enumerate(items):
            item_at = start + 0.25 + ordinal * 0.32
            add(
                f"#check-{index}-{ordinal}",
                item_at,
                0.4,
                f'tl.from("#check-{index}-{ordinal}", {{ x: -24, autoAlpha: 0, duration: 0.4, '
                f'ease: "power3.out" }}, {item_at:.3f});',
            )
            mark_at = item_at + 0.28
            add(
                f"#check-mark-{index}-{ordinal}",
                mark_at,
                0.2,
                f'tl.from("#check-mark-{index}-{ordinal}", {{ autoAlpha: 0, duration: 0.2, '
                f'ease: "none" }}, {mark_at:.3f});',
            )


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
    counter = 120 if vertical else 160
    stat = 96 if vertical else 120
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
    #viewport {{
      position: absolute;
      inset: 0;
      overflow: hidden;
      perspective: {max(width, height)}px;
      perspective-origin: {width // 2}px {height // 2}px;
    }}
    #camera {{
      position: absolute;
      inset: 0;
      perspective-origin: {width // 2}px {height // 2}px;
    }}
    #world {{
      position: absolute;
      inset: 0;
      transform-origin: 0 0;
      will-change: transform;
    }}
    #hud {{
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: 5;
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
    .scene.diagram {{
      justify-content: center;
    }}
    .hud-card {{
      position: absolute;
      inset: 0;
      box-sizing: border-box;
      padding: {pad_top}px {pad_side}px {pad_bottom}px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      gap: 16px;
      pointer-events: none;
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
    }}
    .delta-kicker {{
      color: #62c4ff;
      font-size: {kicker}px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 16px;
    }}
    .delta-counter, .delta-stat, .delta-chain, .delta-checks {{
      display: flex;
      flex-direction: column;
      gap: 20px;
      width: 100%;
    }}
    .delta-num {{
      display: flex;
      align-items: baseline;
      gap: 12px;
      font-variant-numeric: tabular-nums;
    }}
    .delta-value, .delta-counter .delta-num {{
      color: #62c4ff;
      font-weight: 700;
    }}
    .delta-counter .delta-value {{
      font-size: {counter}px;
      line-height: 0.9;
      color: #62c4ff;
    }}
    .delta-suffix, .delta-prefix {{
      font-size: {max(36, counter // 3)}px;
      color: #62c4ff;
    }}
    .delta-note, .delta-tag, .delta-unit {{
      color: #9aa0a8;
      font-size: {max(24, kicker - 4)}px;
    }}
    .delta-pair {{
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    #stage.landscape .delta-pair, #stage.landscape .delta-chain-steps {{
      flex-direction: row;
      align-items: stretch;
    }}
    .delta-before .delta-num span:first-child {{
      font-size: {stat}px;
      color: #9aa0a8;
      font-weight: 700;
    }}
    .delta-after .delta-value {{
      font-size: {stat}px;
      color: #62c4ff;
    }}
    .delta-arrow {{
      color: #9aa0a8;
      font-size: {kicker + 8}px;
    }}
    .delta-chain-track {{
      position: relative;
      height: 3px;
      background: rgba(232, 233, 237, 0.16);
    }}
    .delta-chain-fill {{
      position: absolute;
      inset: 0;
      width: 100%;
      background: #62c4ff;
      transform-origin: left center;
    }}
    .delta-chain-steps {{
      display: flex;
      flex-direction: column;
      gap: 28px;
    }}
    .delta-step {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .delta-dot {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      border: 2px solid #9aa0a8;
      background: #222225;
    }}
    .delta-step.result .delta-dot {{
      border-color: #62c4ff;
      background: #62c4ff;
    }}
    .delta-step.result .delta-body {{
      color: #62c4ff;
    }}
    .delta-body {{
      font-size: {max(28, line // 2)}px;
      font-weight: 700;
      line-height: 1.25;
    }}
    .delta-check-list {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}
    .delta-check-item {{
      display: grid;
      grid-template-columns: 32px 1fr;
      gap: 16px;
      align-items: center;
      padding: 14px 0;
      border-top: 1px solid rgba(232, 233, 237, 0.12);
      font-size: {max(26, kicker)}px;
      font-weight: 600;
    }}
    .delta-box {{
      display: grid;
      place-items: center;
      width: 28px;
      height: 28px;
      border: 2px solid rgba(232, 233, 237, 0.32);
      color: #222225;
      background: #62c4ff;
      font-size: 18px;
      font-weight: 700;
    }}"""


def _scene(row: dict[str, Any]) -> str:
    """One visual clip in ``#world``.

    :param row: A placement row from the timeline.
    :returns: HTML for the scene.
    """
    index = int(row["index"])
    start = float(row["start"])
    scene_duration = float(row["duration"]) + float(row["gap_after"])
    words = len(str(row["spoken"]).split())
    tree = _tree(row)
    diagram = (
        "filetree" in tree
        or "delta-counter" in tree
        or "delta-stat" in tree
        or "delta-chain" in tree
        or "delta-checks" in tree
    )
    kind = "clip scene diagram" if diagram else "clip scene"
    body = f"\n{tree}\n" if tree else "\n"
    return f"""    <!-- spoken-words: {words} -->
    <section
      id="beat-{index}"
      class="{kind}"
      data-start="{start:.3f}"
      data-duration="{scene_duration:.3f}"
      data-track-index="1"
      data-push="{html.escape(str(row.get("push") or "auto"), quote=True)}"
    >{body}    </section>"""


def _hud_card(row: dict[str, Any]) -> str:
    """Kicker and visual line, parked in ``#hud`` so type stays readable.

    :param row: A placement row.
    :returns: HTML for the overlay clip.
    """
    index = int(row["index"])
    start = float(row["start"])
    scene_duration = float(row["duration"]) + float(row["gap_after"])
    join = str(row["join"])
    kicker = {"none": "Start", "but": "But", "therefore": "Therefore", "caveat": "Caveat"}[join]
    visual = html.escape(str(row["visual"]))
    return f"""    <div
      id="hud-{index}"
      class="clip hud-card"
      data-start="{start:.3f}"
      data-duration="{scene_duration:.3f}"
      data-track-index="4"
    >
      <div class="kicker">{kicker}</div>
      <div class="line" id="line-{index}">{visual}</div>
    </div>"""


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
    try:
        rendered = render_picture(
            [str(item) for item in picture], index=int(row["index"]), added=added
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise CompositionError(f"Beat {row.get('index')}: {exc}") from exc
    if not rendered:
        return ""
    if rendered.startswith(("<ul", "<div")):
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


def _camera_runtime(width: int, height: int, needs_layout: bool) -> str:
    """JS for the camera proxy. CSS ``zoom`` keeps type sharp.

    :param width: Composition width.
    :param height: Composition height.
    :param needs_layout: True when push-ins measure a node.
    :returns: JavaScript statements.
    """
    cx = width / 2.0
    cy = height / 2.0
    layout = ""
    if needs_layout:
        layout = f"""
    function layoutCenter(sel) {{
      const el = document.querySelector(sel);
      if (!el) return {{ x: {cx:.1f}, y: {cy:.1f} }};
      const z = parseFloat(world.style.zoom || "1") || 1;
      const wr = world.getBoundingClientRect();
      const er = el.getBoundingClientRect();
      return {{
        x: (er.left + er.width / 2 - wr.left) / z,
        y: (er.top + er.height / 2 - wr.top) / z
      }};
    }}"""
    return f"""    const cam = {{ cx: {cx:.1f}, cy: {cy:.1f}, zoom: 1 }};
    const world = document.querySelector("#world");
    function applyCam() {{
      const z = cam.zoom;
      world.style.zoom = z;
      world.style.transform =
        `translate(${{{cx:.1f} / z - cam.cx}}px, ${{{cy:.1f} / z - cam.cy}}px)`;
    }}{layout}"""


def _dead_zone_comments(
    tweens: tuple[Tween, ...],
    placements: list[dict[str, Any]],
    duration: float,
) -> str:
    """HTML comments for idle spans, labelled hold vs missing entrance.

    :param tweens: Planned tween intervals.
    :param placements: Timeline rows.
    :param duration: Composition length.
    :returns: Comment lines, or an empty string.
    """
    beats = tuple(
        BeatWindow(
            index=int(row["index"]),
            start=float(row["start"]),
            duration=_hold_seconds(row),
        )
        for row in placements
    )
    report = analyze_tweens(tweens, duration=duration, beats=beats)
    lines: list[str] = []
    for zone in report.zones:
        tag = "WARN" if zone.label == "missing-entrance" else "HOLD"
        beat = f" beat {zone.beat}" if zone.beat is not None else ""
        lines.append(
            f"  <!-- {tag}{beat} {zone.start:.1f}-{zone.end:.1f}s {zone.label}. {zone.note} -->"
        )
    return "\n".join(lines)


def _hold_seconds(row: dict[str, Any]) -> float:
    """Return how long the visual holds.

    :param row: Timeline row.
    :returns: Speech plus the following gap.
    """
    return float(row["duration"]) + float(row["gap_after"])
