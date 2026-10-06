# Brief and style

Planning documents for a motion graphics video. Write these before any
animation code. They are cheap to change; renders are not.

## The crew persona

Open the work (and the project's `AGENTS.md` / `CLAUDE.md`) with:

> You are the director, writer, animator, composer, sound designer, and render
> engineer for this video. You own quality end to end. You look at your own
> frames and grade them honestly.

A task ("make a video about our product") produces a demo. A crew plus a story
produces a video. If the user gives a topic, propose a story: who wants what,
what stands in the way, what changes. Pick an emotion and write it down
("2:00 AM, solo founder energy", "launch-day swagger", "quiet confidence").
Every later decision (palette, music, pacing) checks against that emotion.

## docs/brief.md template

```markdown
# Brief

## Story
<one paragraph: setup, tension, turn, payoff>

## Emotion
<two or three words, referenced by every later phase>

## Beat sheet
| # | Beat | On screen | Seconds |
|---|------|-----------|---------|
| 1 | Hook: the tension in under 10 words | huge kinetic type | 2-3 |
| 2 | The idea appears / assembles | ... | 3-4 |
| 3 | Build: features, moments, escalation | ... | ... |
| 4 | Proof: one number or one moment | ... | 2-3 |
| 5 | Payoff / logo lockup + CTA | ... | 2-3 |

## Audience, platform, format
<who, where it plays, 9:16 / 1:1 / 16:9, duration>

## References
<frames, videos, links, or style names the user provided>
```

Get explicit user approval of the story before moving to style.

## References beat descriptions

Naming a style beats describing one. "Bauhaus poster meets Swiss grid"
compresses a thousand decisions. "Clean and modern" compresses nothing.

With a reference file (image, video, or folder):

1. Extract frames: `ffmpeg -i ref.mp4 -vf fps=2 refs/frame_%03d.png`
2. Study them. Write `docs/style_guide.md` from evidence, not vibes.
3. Take the grammar, never the content: pacing, type treatment, palette
   structure, transition language. No logos, characters, or copy.

With no reference: pick a named look, then write the same guide.

## docs/style_guide.md template

```markdown
# Style guide

## Palette
- Background: #0A0A0D
- Ink: #F5F1E8
- Accent (one only): #FF4D00
- Support (max two): #2B2B33, #8C8578

## Type
- Display: <family, weights, tracking, case> - used for headline words only
- UI/body: <family, weights> - used for labels, captions, data
- Scale: display 120-200px at 1080p, body 28-40px, minimum 24px

## Motion grammar
- Entrances: eased, overlapping, from offscreen or masked; nothing linear
- Holds: elements keep breathing (float, counter, glow pulse) while on screen
- Exits: faster than entrances, directional
- Camera: one move per shot (push, drift, whip), never two at once

## Transitions
- Hard cuts on beats by default
- Shader/WebGL transition at 2-3 key moments only (hero reveal, CTA landing)

## Texture
- Film grain via CSS gradients, vignette, optional scanlines
- Noise seeded with a fixed seed for determinism

## Shot length
- Median shot 2-3s; no shot longer than 4s without an on-screen event
```

## Banned defaults

Paste this list into the project rules verbatim. Models regress to these
defaults on every revision pass unless they are forbidden by name:

```markdown
# Banned defaults

- Centered title on a gradient background
- Everything fading in; linear motion
- Corner labels and decorative frame borders
- Glow on UI chrome; generic particle bursts
- Default system fonts; blue/purple gradient palettes
- More than one accent color; more than two type families
- Static elements on static backgrounds
- Any shot where nothing new happens for more than 4 seconds
```

## Constraint rules that force taste

- One display face, one UI face, one accent color.
- Type is a visual element: scale, mask, stack, and cut it, but never set a
  paragraph of body text on screen. Under 10 words per shot.
- Every 2-4 seconds something new must happen.
- Layout for the format: design 9:16 first if the target is vertical, and
  reflow (never crop) for other formats.
- Logos and CTAs land on a beat, in the last fifth of the runtime, held long
  enough to read twice.
