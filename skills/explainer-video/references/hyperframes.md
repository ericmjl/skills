# HyperFrames render

HyperFrames is HeyGen's open-source HTML-to-video framework. Repository: <https://github.com/heygen-com/hyperframes> (Apache-2.0, created 2026-03-10). Docs: <https://hyperframes.heygen.com>. This note was checked against those pages and the CLI skill in that repo on 2026-11-20. Confirm the installed CLI with `npx hyperframes render --help` before trusting a flag.

The sibling skill `motion-graphics-video` is the house style guide (banned defaults, contact sheet, ACE-Step). This skill renders with the same framework and does not vendor that skill's scripts.

## What the player reads

A composition is HTML plus a GSAP timeline created paused and stored on `window.__timelines`. The draft `index.html` from `build_composition.py` does this. Keep those rules if you replace the scaffold with a designed composition:

- No `Date.now`, `setTimeout`, `requestAnimationFrame`, CSS animations, or `Math.random`. The frame must depend on the timeline time only.
- Animate with `autoAlpha`, which sets visibility and opacity together. A bare `visibility` tween leaves a fade that pops.
- Grain, if you add it, is a CSS layer. An SVG filter is expensive and unstable across the capture path.
- Scenes are elements with class `clip`, plus `data-start`, `data-duration`, and `data-track-index`.
- Audio elements use the same three attributes. `data-volume` is a linear gain, from 0 to 1.

## Ducking

Narration ducks the music through a volume lane on the music element. `t` is relative to that element. The music clip starts at 0, so `t` is composition time.

```html
<audio
  id="music"
  class="clip"
  src="audio/music.wav"
  data-start="0"
  data-duration="62.4"
  data-track-index="0"
  data-volume="0.7"
  data-automation='{"version":1,"lanes":[{"target":"volume","points":[{"t":0,"v":1},{"t":1.2,"v":0.35}]}]}'
></audio>
```

The lane multiplies `data-volume`. A point at `v: 1` is the bed (gain 0.7). A point at `v: 0.35` is the ducked bed. `build_composition.py` ramps across 0.12 s at each narration edge. That ramp is a guess until a mix is listened to. Change the constants in `scripts/timeline.py` (`duck_points`) if a real render needs a deeper dip, then rebuild the HTML.

`data-fx-carve` is not read at playback. It stores the settings a carve was made from, so Studio can recompute `data-fx-chain` and the lanes. Writing a carve attribute and expecting the music to dip will produce a full-volume bed. The volume lane is the contract. Source: <https://hyperframes.heygen.com/reference/audio-effects>, accessed 2026-11-20.

Narration clips sit on a higher `data-track-index` than the music. They do not overlap each other. Overlap would be two voices. The aligner never places a clip so that it starts before the previous clip has ended.

## Beat alignment

`npx hyperframes beats` writes a Studio beat file for a music-led edit. It does not know where the narration WAVs end. This pipeline does the snap in `align_music.py`:

- Measure each narration WAV.
- Detect tempo and beat times with `librosa.beat.beat_track`, or accept `--beats-json`.
- Place clip N to start on the earliest music beat that lands in `[end + min_gap, end + max_gap]`.
- If no beat falls in that window, start at `end + min_gap`.
- Never change the WAV's duration. Never overlap speech.

Visual changes inside a beat, once you replace the scaffold, should land on those same music beats. The scaffold fades the line in at the clip start, which is already a snapped time. Finer hits (a number counting up, a pipe connecting) belong on the beat list inside `timeline.json` under `music_beats`.

Music shorter than the timeline is a warning, not a loop. Looping a short bed makes the seam obvious. Bring a longer track or cut the script.

## Scaffold versus the final picture

`build_composition.py` is the timing document plus the picture. A path-shaped `delta` (`environment.yml`, `data/raw.csv`) grows a file tree, and the newest file is the one that enters. A sentence delta stays a labeled row under the visual note. The palette is `#222225` background, `#e8e9ed` text, `#62c4ff` accent, and `#9aa0a8` dim. The type stack is Berkeley Mono, then DejaVu Sans Mono, Liberation Mono, Nimbus Mono PS, and Noto Sans Mono, then `ui-monospace` and `monospace`. Berkeley Mono is licensed and is not bundled here. On a machine that does not have it, the browser uses the first of those monospace faces that is installed. Tree labels are 30px so a phone can still read them.

Narration is normalized to -16 LUFS when it is synthesized. Align writes the music bed to -24 LUFS as `audio/music.norm.wav` and the timeline points at that file. Both happen before HyperFrames muxes the stems. `--no-loudness` on the synthesizer skips the narration pass.

The scaffold wraps the picture in a seek-safe camera rig: `#viewport` (fixed frame, `overflow: hidden`) holds `#camera` (lens only) which holds `#world` (the file tree, templates, and other picture). `#hud` sits beside `#camera`, not inside it, so kickers and visual lines do not scale with the lens. File-tree beats push in on the newest node (`#added-N`) unless the beat sets `push: none`. Zoom duration is `0.55 * |ln(z2/z1)| / ln(2)`, clamped to 0.30–0.94 s, so a doubling always takes 0.55 s. The move is a GSAP tween of a `{cx, cy, zoom}` proxy with `onUpdate` writing CSS `zoom` onto `#world` (layout-level scale, so type stays sharp). Labels that must ride along in `#world` counter-scale with `scale(1/zoom)`; this scaffold keeps type in `#hud` instead. Everything is derived from the paused timeline. Seeking is deterministic.

The scaffold records each tween as an HTML comment and runs a dead-zone pass: any stretch of at least 1.0 s with no active tween is labelled `intentional-hold` or `missing-entrance`. A missing entrance is a hold over 4 s with only one tween start — the same review rule as before, now measured from the GSAP map rather than speech length alone. `WARN … missing-entrance` comments are the flag. The final composition needs a second and third entrance inside a long beat (a diagram completing, a number landing, the failure showing, a camera push-in). Pull extra shot design from `motion-graphics-video` and keep the audio elements this scaffold already timed.

Named `delta` kinds `number-counter`, `before-after-stat`, `cause-chain`, and `checklist-pop` render as picture templates in this palette. They tween on the same paused timeline (a counting proxy, staggered autoAlpha). No CSS loops, no `setTimeout`.

Sources for the camera rig and the dead-zone idea, and for the four templates, are listed in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## CLI

From the project directory, after `index.html` exists:

```bash
npx hyperframes --version
npx hyperframes render --help
npx hyperframes lint
npx hyperframes check .
npx hyperframes preview
npx hyperframes render --quality draft -o out/draft.mp4
```

The public skill also documents `doctor`. Use it when the install is unhappy. Treat any flag that `--help` does not list as retired.

Draft quality is for the critique loop. The last export is the high-quality setting the installed CLI documents. Then:

```bash
skills/explainer-video/scripts/verify_render.sh out/draft.mp4 DURATION 1080 1920
```

`DURATION` is `timeline.json`'s `duration` field. The checker allows 0.5 s of slop, demands 1080x1920 unless you pass another size, and demands at least one audio stream.

## Where to render

Synthesis of voice `eric` wants the GB10 (aarch64, CUDA, a large unified memory). The render wants Node 22, Chrome, and ffmpeg, which the Mac already has. Generating WAVs on the Spark and rendering HTML on the Mac is a normal split. Copy `audio/` and `index.html`, and keep the relative paths (`audio/music.wav`, `audio/beats/00.wav`) intact.

## ARM64 browser

Chrome for Testing publishes no linux-arm64 build, so `hyperframes browser ensure` finds nothing on the GB10. Playwright's Chromium headless shell does have an arm64 build. The binary is named `headless_shell`.

```bash
npx playwright install chromium-headless-shell
export HYPERFRAMES_BROWSER_PATH="$(find "$HOME/.cache/ms-playwright" -type f -name headless_shell | head -1)"
export PRODUCER_HEADLESS_SHELL_PATH="$HYPERFRAMES_BROWSER_PATH"
```

HyperFrames reads `HYPERFRAMES_BROWSER_PATH` first and `PRODUCER_HEADLESS_SHELL_PATH` when the first is unset (`packages/cli/src/browser/manager.ts` and `packages/engine/src/services/browserManager.ts`, read 2026-11-20). Set both to the same file so `render`, `check`, and `preview` launch the shell you named. Confirm the flags with `npx hyperframes render --help`. This path was not executed on the machine that wrote this note.

## Music credit

When the track is CC BY, including CC-BY-SA and the other CC BY licenses, put `audio/credit.json` in the project before `build_composition.py`:

```json
{"title": "Glass Beats", "author": "Ada", "source": "https://example.com/glass", "license": "CC BY 4.0"}
```

The build writes that attribution to `credits.txt`. CC0 and a missing file do not. Put `credits.txt` in the description of the upload. The scaffold does not burn the credit into the picture.
