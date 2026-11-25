# Review

Two passes. The first is a checklist you can finish before a render. The second is a render, a critique, and another render. Three draft rounds before a high-quality export. In each round, fix the three worst problems and leave the rest.

The public `motion-graphics-video` skill owns the contact-sheet method and the grade (shots at 8 or better, mix near -14 LUFS). Use that skill's `contact_sheet.sh` and critique rubric when the picture is past the scaffold. This file does not copy those scripts.

## Before the first render

Script, from [problem-chain.md](problem-chain.md):

- Beat 0 is the naive failure.
- `check_script.py check` prints OK. That covers join order (`but`, `therefore`, `caveat`), 15 to 18 words a beat, 10 to 12 beats, 4 or 5 `but` failures, the sign-off, and missing jargon.
- The sign-off contains `Congratulations, you built X.` with X equal to the artifact heading.
- A longer approved chain was condensed: the kept failures are the ones whose picture changes the most, and no kept fix needs a second technical term.
- Every number is checked, analogized, and `source` is `path:line`.
- Each `delta` is the new piece of a persistent picture. The visual line does not redraw the earlier beats.
- Second person. No sentence was copied from the reference Short.

Voice:

- The `# Voice` section names a row in `voices.yaml`.
- The clone clip is in `~/.voice/` (`reference.m4a`, then `reference.wav`, then `reference.mp3`). If it is missing, stop and ask the user; do not invent a clip.
- `pronounce.py list` shows the terms this script uses. Any term with `verified: false` that you can hear in a beat gets a listen before the final export.
- `audio/beats/NN.spoken.txt` is the line the model received. It matches the lexicon, not a hand edit that bypassed it.
- Each WAV is one voice, with no clipped breath at the cut and no spoken bracket tags.

Picture, still on paper:

- Every beat's visual note can be pointed at. A title that repeats the sentence is not a picture.
- The sign-off is the only full-frame title.
- Palette and type come from [hyperframes.md](hyperframes.md). One accent.

## After each draft

```bash
npx hyperframes render --quality draft -o out/draft.mp4
skills/explainer-video/scripts/verify_render.sh out/draft.mp4 DURATION 1080 1920
uv run skills/explainer-video/scripts/dead_zones.py PROJECT
```

`dead_zones.py` reads the built `index.html` (tween comments, falling back to `tl.from` / `tl.to` statements) and lists every stretch of at least 1.0 s with no active tween. Each stretch is `intentional-hold` or `missing-entrance`. A missing entrance is a beat that holds longer than 4 s with only one tween start — the same rule as the old `WARN beat N holds` comment, now measured from the GSAP map. Exit code 1 means at least one missing entrance. `build_composition.py` prints the same report after it writes the HTML.

Watch the file once with the sound on, and once reading only the pictures.

| Check | What "done" means |
| --- | --- |
| Duration | Within half a second of `timeline.json`, and inside 45 to 90 seconds. |
| Frame | 1080x1920 for the vertical master. A 16:9 pass is a separate timeline, 1920x1080. |
| Audio present | `verify_render.sh` reports at least one audio stream. |
| Ducking | Music is audible between lines and drops while a line plays. A full-volume bed means the volume lane was lost. |
| Snap | Line starts sit on a music beat, or the gap is the short minimum because no beat fell in the window. No line starts late by a full bar. |
| Speech | No time-stretch artifacts, no two lines overlapping, no lexicon token spoken as the word "bracket". |
| Holds | No shot sits for more than 4 seconds with a single entrance. `dead_zones.py` must not print `missing-entrance`. HTML comments `WARN … missing-entrance` are the same miss; `HOLD … intentional-hold` is a labelled pause, not a failure. |
| Jargon | The words you added to the lexicon this session sound like the note says they should. Then `correct TERM --verified`. |
| Sign-off | The last words are the congratulations line, and the card shows the artifact name. |
| Loudness | The mixed file is in the neighborhood of -14 LUFS integrated. Measure with ffmpeg `loudnorm` or the public skill's checker when you have a render. The scaffold does not measure this. |

## Critique loop

1. Render a draft.
2. Write three sentences: the worst timing miss, the worst picture, the worst spoken word.
3. Fix those three. A spoken-word miss is a lexicon `correct` plus `resynth` of that beat, then `align_music.py` and `build_composition.py` again, because the WAV duration may have changed.
4. Render again.
5. Stop after the third round only if the table above is clean. Otherwise keep going and say which row is still open.

A picture fix that does not change audio can skip synthesis. Rebuild the HTML, or edit `index.html` by hand if you have already replaced the scaffold, and render. A picture fix that moves a cut relative to a word has to go back through the WAVs. Do not nudge `data-start` until the word is covered and the beat snap is abandoned. Change the gap in a new `align_music.py` run instead.

## What this loop does not prove

A clean checklist on a machine that never ran the model is a script review, not a mix review. Say which of the two you did.
