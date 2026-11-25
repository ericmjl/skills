# Third-party notices

This skill reimplements ideas from the following works. Nothing from those
trees is vendored here. Where a formula, layer name, or template kind is
adapted, the source is listed below.

## HyperFrames animation map (dead zones)

- Repository: <https://github.com/heygen-com/hyperframes>
- License: Apache License 2.0
- Copyright: Copyright 2026 HeyGen, Inc.

The dead-zone checker in `scripts/dead_zones.py` reimplements the idea of
enumerating GSAP tween intervals on a paused timeline and reporting idle
stretches of at least 1.0 s, asking whether each stretch is an intentional
hold or a missing entrance. The implementation here reads the HTML this
skill generates (tween comments, with a GSAP-statement fallback). It does
not copy HyperFrames' browser capture session, bbox sampling, or
animation-map JSON schema.

## Huashu Design camera language (seek-safe camera rig)

- Repository: <https://github.com/alchaincyf/huashu-design>
- File: `references/camera-language.md`
- License: MIT
- Copyright: Copyright (c) 2026 alchaincyf (花叔 · 花生)

The `#viewport` / `#camera` / `#world` / `#hud` layering, the logarithmic
zoom duration `0.55 * |ln(z2/z1)| / ln(2)` clamped to 0.30–0.94 s, the
preference for CSS `zoom` over `transform: scale` so type stays sharp, and
the rule that labels live in `#hud` or counter-scale with `scale(1/zoom)`,
are paraphrased into `references/hyperframes.md` and implemented in
`scripts/camera.py` and `scripts/composition.py`. The GSAP is generated
from this skill's paused timeline. No Huashu Design source files are
copied.

## hyperframes-motion-library (picture templates)

- Repository: <https://github.com/nutllwhy/hyperframes-motion-library>
- Author: nutllwhy / 栗噔噔
- License: MIT
- Copyright: Copyright (c) 2026 栗噔噔 (nutllwhy)

The four delta kinds `number-counter`, `before-after-stat`, `cause-chain`,
and `checklist-pop` adapt the information structure of those named
templates (a counting number, a before/after pair, a three-step cause
chain, a popping checklist). Markup, motion, and color are restyled to
this skill's `#222225` / Berkeley Mono / `#62c4ff` house palette and
driven from the paused GSAP timeline. The original compositions, presets,
and style packs are not copied.
