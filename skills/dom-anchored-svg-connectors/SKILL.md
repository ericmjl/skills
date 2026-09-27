---
name: dom-anchored-svg-connectors
description: >-
  Anchor connector lines/arrows/edges between rendered DOM elements (gantt dependency arrows, org-chart parent-child lines, flowchart edges, annotation leader lines) on MEASURED element rects — NEVER compute connector coordinates de novo (percentage math, hardcoded px widths, or a second parallel layout math). Use when drawing connectors in vanilla JS/HTML, or when the user reports connectors 'misaligned', 'all over the place', or 'floating detached from the boxes'; trigger: any second, independent coordinate computation for lines that must touch rendered elements. FIX: (1) one absolutely-positioned SVG overlay inside the scrollable wrapper sized to scrollWidth/scrollHeight; (2) store id-to-element refs while building the DOM, measure with getBoundingClientRect() minus the container rect after render; (3) anchor on box edges (right-center of predecessor to left-center of successor); (4) elbow routing with an SVG marker arrowhead; (5) overlay pointer-events:none; (6) clear+redraw on resize.
created_at: "2026-08-14"
---

# Dom Anchored Svg Connectors

When drawing connector lines/arrows/edges between rendered DOM elements (gantt dependency arrows, org-chart parent-child lines, flowchart/node-graph edges, annotation leader lines) in vanilla JS/HTML — or when the user reports connectors 'misaligned', 'all over the place', or 'floating detached from the boxes' — NEVER compute connector coordinates de novo (percentage math, hardcoded px-width assumptions, or re-deriving the layout math in a second parallel code path). TRIGGER CONDITION: any second, independent coordinate computation for lines that must touch existing rendered elements. ROOT CAUSE: the parallel math drifts from actual layout (fonts, flex sizing, scrollbars, padding, responsive widths) so anchors land in the wrong place. FIX (anchor on measured rects): (1) ONE absolutely-positioned SVG overlay inside the scrollable wrapper, sized to the container's scrollWidth/scrollHeight so it scrolls with content; (2) store id→element refs while building the DOM, then AFTER all elements render measure each with getBoundingClientRect() minus the container's rect for pixel-true anchors; (3) anchor on box edges — right-center of predecessor → left-center of successor (center-bottom/top for milestone diamonds); (4) elbow routing 'M sx sy H midX V ty H tx' with an SVG marker arrowhead, routing backwards/overlap deps through a mid-Y detour; (5) overlay pointer-events:none so bar hover/tooltips still work; (6) clear+redraw on window resize. User correction (learn-anything gantt, 2026-08-14): 'don't draw them de novo, draw them anchored on the boxes.'

## Instructions

TODO: Add specific instructions based on observed patterns.
