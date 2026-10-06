# Render and critique

The build-and-grade loop. This is the phase that separates a viral-quality
video from a "mid" one: the model renders, looks at its own frames, grades
them honestly, and fixes the worst problems before the final pass.

## The Hyperframes loop

Hyperframes turns HTML into deterministic MP4: the renderer seeks each frame
in headless Chrome and encodes with FFmpeg. Same input, same frames, same
output.

```bash
npx hyperframes init <project>     # scaffold (pick a starter skeleton)
cd <project>
npx hyperframes lint               # validate composition structure
npx hyperframes check              # lint + WCAG contrast + layout overflow
npx hyperframes preview            # Studio on :3002, frame-accurate scrubbing
npx hyperframes render --quality draft -o out/draft.mp4
npx hyperframes render --quality high  --fps 30 -o out/final.mp4
npx hyperframes doctor             # diagnose environment problems
```

### Composition anatomy

- `index.html` is the whole video: HTML + CSS + a paused GSAP timeline (`tl`).
- Scenes are `.scene.clip` divs with `data-start`, `data-duration`,
  `data-track-index`. Timing lives on the DOM, animation lives in the
  timeline registered as `window.__timelines["main"]`.
- Animate with `tl.from()` tweens (from offscreen/masked INTO the CSS
  position) so the CSS layout is the source of truth.
- Shader transitions: anchor scenes use `style="opacity:0;"` and are managed
  by HyperShader; all other scenes use `visibility:hidden` and need explicit
  `autoAlpha` toggles in the timeline. `autoAlpha` (not bare `visibility`)
  because shader transitions blanket-reset scene opacity; bare `visibility`
  toggles get poisoned by that reset.
- Grain via CSS radial-gradient layers. NEVER SVG filter data-URI grain; it
  taints canvas capture and breaks transitions.

### Environment gotchas

- Needs Node 22+ and FFmpeg on PATH. Headless Chrome is downloaded on first
  run; system Chrome hangs renders. Install the right binary with
  `npx puppeteer browsers install chrome-headless-shell`, then run
  `npx hyperframes doctor`.
- On Chromium 147+ the old capture protocol was removed; use
  `hyperframes@>=0.4.2` (auto-falls back to screenshot mode). Escape hatch:
  `export PRODUCER_FORCE_SCREENSHOT=true`.
- Confirm exact render flags against the installed CLI
  (`npx hyperframes render --help`); flag names evolve between versions.

## Contact sheet critique

After every draft render:

```bash
scripts/contact_sheet.sh out/draft.mp4 <duration-seconds> 12 out/contact.png
```

One frame per beat lands in a grid. Then grade every shot 1-10, in writing:

| Axis | Ask |
| --- | --- |
| Story | Can a stranger say what this shot is for? |
| Composition | Does the eye land where the shot wants it? |
| Motion | Do entrances ease and overlap? Does anything merely fade? |
| Typography | Is type treated as a visual? Readable at a glance? |
| Sync | Does the cut land on the beat? Does the shot answer the music? |

Protocol:

1. Write the three worst problems across the whole video (not twenty).
2. Fix only those. Re-render draft. New contact sheet.
3. Minimum 3 rounds. No shot below 8 in the final. Every round re-checks the
   banned-defaults list; fixes regress toward defaults under pressure.

Animatic gate before polish: render at 960x540 with placeholder audio and
watch it end to end. Pacing problems found here cost minutes; found after the
polish pass they cost hours.

## Final render verification

```bash
scripts/verify_render.sh out/final.mp4 <expected-duration>
```

Checks duration against the composition, confirms video+audio streams, prints
measured LUFS, and extracts a poster frame. Then manually extract 3-4 frames
and look at them. Trust nothing you have not seen.

## Multi-format export

Design against a layout function (safe margins, type scale, anchor positions
per format) and render each format from the same composition by reflowing.
Never crop a 16:9 master to 9:16; reframe the type and focal elements.
Render formats in parallel; they are independent files.

## Ship

Deliver: `final.mp4` (+ formats), `contact.png`, `poster.png`, and three
concrete notes on what another iteration would improve.
