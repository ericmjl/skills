# Problem-chain script

Folded from the closed draft `problem-chain-explainer` (ericmjl/skills pull request 58, branch later deleted, diff still readable as of 2026-11-20). This file is the scripting stage of `explainer-video`. Use this file for the chain, `video-script-writing` for spoken-register checks, and `writing` when the deliverable is prose rather than a Short.

The reference Short is <https://www.youtube.com/shorts/AvRjarGrmC8>. It is a shape: a person builds a thing, the obvious version fails, each real feature shows up as the rescue, and the last card congratulates the viewer. Do not transcribe it. The `youtube` skill is the right warning: Shorts often have captions disabled, and a guessed transcript is worse than a paraphrase. The house table at the bottom is an original paraphrase of that shape. The Data Science Bootstrap build-up at [examples/ds-bootstrap-build-up/script.md](../examples/ds-bootstrap-build-up/script.md) is the porch-swing long form.

## Formats

Two script formats. Put an optional `# Format` heading in `script.md` with `short` or `build-up`. Missing means `short`.

On 2026-11-20 Eric watched the 78 s render of the 12-beat Data Science Bootstrap short and loved the visual style. He said the earlier, longer 14-beat script was better, and that "So" beat "Therefore" as the spoken opener. That longer chain, rewritten as 30 beats and 533 spoken words (about 3.5 minutes), is the build-up example. Prefer build-up when the chain has more failures than a Short can hold, or when naming every piece is the point. Prefer short when the deliverable is a YouTube Short.

| | `short` | `build-up` |
| --- | --- | --- |
| Length | 10-12 beats, 150-216 spoken words, 60-90 s | No beat or word cap. Warn above about 650 words (about 4.5 min). |
| Failures | 4 or 5 `but` beats in the shipping script | As many as the chain needs. Keep the but/therefore alternation. |
| Therefore opener | **So** (recommended). Therefore allowed. Repeated Therefore warns. | Same. |
| Therefore close | No naming punchline required | Each therefore ends with "That's X." or "Those are X." Missing warns. |
| But opener | "But …" | "But …", or a short recap such as "Now X, but Y" or "Finally, …" |
| Caveat | Encouraged | Optional |
| Sign-off | `Congratulations, you built X.` with X matching the artifact | Free text |

The but/therefore alternation check is the same in both formats. Two `but`s in a row still need a caveat between them. Two `therefore`s in a row are still invalid.

## What the viewer feels

The viewer is the builder. Second person, present tense. "You dig", "you add", "you lose the water". The narrator is not a lecturer listing features of someone else's product.

The chain is a sequence of failures and fixes. A beat joins the previous beat with **but**, **therefore**, or **caveat**.

- **but** means the thing you just built has a new problem.
- **therefore** means the problem forces the next design feature. The spoken line opens with "So". "Therefore" is allowed; using it on every fix is a warning. The field stays `therefore`. In `build-up`, the line ends by naming the feature: "That's X." or "Those are X."
- **caveat** is a limit on the fix it follows, or the limit you name just before the sign-off. It does not take a turn in the but/therefore alternation. Two `but` beats in a row are allowed only when a caveat sits between them. Two `therefore` beats in a row are not.
- The first beat has no join. It is the naive version.
- The last beat has no join. It is the payoff and the sign-off.

"And then", "also", "next", and "another feature" are the failure mode this method exists to remove. If a sentence still works after you delete the join, the beat is a feature list. Rewrite it until the join is load-bearing. Open every fix with "So" unless a single Therefore earns its place. Repeated Therefore is the warning. All-So is the recommended pattern.

## Length

Speak at about 150 words per minute. Count the spoken fields only.

A shipping **short** is 60 to 90 seconds, which is 10 to 12 beats.

Each spoken line is 15 to 18 words. The arithmetic:

- 10 beats at 15 words is 150 words, which is 60 seconds.
- 12 beats at 16 words is 192 words, about 77 seconds. That is the top of the 150 to 190 word center.
- 12 beats at 18 words is 216 words, about 86 seconds, still inside 90 seconds.

The 150 to 190 word band is the center of that budget, not a second budget. `check_script.py` fails a script under 150 words or over 216. A total from 191 to 216 is long, and still legal.

A failure is a `but` beat. The opening naive failure is real, and it is not part of this count. A 10-beat Short with strict alternation has 4 `but` beats: 8 middle beats, half of them failures. A 12-beat Short has 5. Six `but` beats need six fixes, which is 14 beats once you add the opening and the sign-off, past the 12-beat cap. So the shipped script carries 4 or 5 failures. Fewer than 4 and the Short is a slogan.

The chain table you write before cutting can hold up to 7 `but` rows. Condensing, below, brings it back to 4 or 5. A caveat does not count as a failure or as a fix. It spends a beat, so a kept caveat means one fewer alternating pair.

A **build-up** script has no 10-12 beat cap and no 150-216 word cap. `check_script.py` warns above about 650 spoken words, which is about 4.5 minutes at 150 wpm. The DS Bootstrap build-up is 533 words, about 3.5 minutes.

The edit uses the WAV durations from TTS. A line that looks like 6 seconds on paper can be 8 seconds once the voice says it. The word budget is how you decide the script is short enough to synthesize.

## Order of work

1. Name the artifact in one line. On a short, this is the X in "Congratulations, you built X." On a build-up, it is what the last beat can point at in free text.
2. Choose `short` or `build-up`. Write `# Format` in `script.md` when the script is a build-up.
3. Write the chain table before any spoken line. One row per beat: join, what fails or what you add, the picture.
4. Draft spoken lines from the table. One or two sentences, 15 to 18 words. A `but` line opens with "But". On a build-up it may recap first ("Now X, but Y" or "Finally, …"). A `therefore` line opens with "So". Therefore is allowed; do not open every fix with it. On a build-up, the therefore line ends with "That's X." or "Those are X." A caveat does not open with But, Therefore, or So.
5. Attach a checked number only where you can cite it. Pair it with an everyday object. Put the citation in `source` as `path:line`.
6. On a short, add a caveat beat with join `caveat`. Put it immediately after the fix it qualifies, between two `but` beats, or immediately before the sign-off. On a build-up the caveat is optional.
7. Close with the payoff. A short uses the exact sign-off `Congratulations, you built X.` A build-up may close in free text.
8. Read it aloud. Cut any beat whose picture does not change, unless you are keeping the long chain on purpose.
9. Copy the spoken lines into `script.md` using [script-template.md](script-template.md). Leave the table in `docs/chain.md`.

## Chain table

Write this before prose.

```text
Artifact: <the thing the viewer builds>

| Beat | Join | What happens | Picture |
| --- | --- | --- | --- |
| 0 | none | Naive version, and the specific way it fails | ... |
| 1 | but | The failure the naive version just caused | ... |
| 2 | therefore | The feature that failure forces. Spoken line opens with So. | ... |
| 3 | caveat | A limit on that fix. It does not count as a but or a therefore. | ... |
| 4 | but | The next failure. It alternates with the therefore. The caveat did not take a turn. | ... |
| 5 | caveat | Between two buts. This is the only place two buts may sit in a row. | ... |
| 6 | but | Allowed, because the caveat is the only join between it and beat 4. | ... |
| N | none | Payoff. A short says Congratulations, you built X. A build-up may close in free text. | Title card |
```

Every middle row is a failure (`but`), the feature that answers the previous failure (`therefore`), or a `caveat`. A feature that does not answer the previous row is a list item. Drop it or find the failure that earns it. A caveat does not answer a failure and does not introduce one. It qualifies a fix, or it is the last word before the sign-off.

## Spoken line

- Second person. The viewer holds the tool.
- The join is the first word when the join is `but` or `therefore`, except a build-up `but` may open with a short recap ("Now X, but Y" or "Finally, …"). A `therefore` line opens with "So". "Therefore" is allowed; using it on every fix is a warning.
- One idea. If you need "and" in the middle, it is probably two beats.
- Numbers are digits in the spoken line when they are a count (`4 hours`, `200 liters`) so the lexicon and the voice treat them as numbers. Spell a number only when the voice misreads it, and record that in the lexicon note.
- A number without a source does not ship. Replace the slot with `none` and take the figure out of the sentence.
- An analogy is a kitchen, a street, or a workday object. It is not a second technical term.
- The caveat names who this design is wrong for, or the condition that breaks it. Its join field is `caveat`, not `but`.
- On a short, the last spoken line contains `Congratulations, you built X.` X matches the artifact heading word for word. On a build-up, the last line is free text.
- On a build-up, every `therefore` line ends with "That's X." or "Those are X."

## Visual note

The visual field is a shot description: what enters, what moves, what the viewer can point at. It is not a caption of the sentence.

Tie the picture to the failure. When the line says the tank gets dirty, the picture shows dirty water entering, not a title that says "contamination".

Draft renders may put the visual sentence on screen so the timing can be judged. That text is a placeholder. The final composition replaces it with the diagram. Follow [hyperframes.md](hyperframes.md) for palette, Berkeley Mono (DejaVu Sans Mono, Liberation Mono, Nimbus Mono PS, or Noto Sans Mono when Berkeley Mono is not installed), and vertical safe zones. Follow `motion-graphics-video` for the banned defaults: a centered title on a gradient, fade-only transitions, corner labels, glow, more than one accent color, and a shot that sits still for more than 4 seconds.

## Numbers

Before a number enters the table, write the source in the row (a paper, a datasheet, a measurement Eric made). The Short does not cite it out loud. The project keeps it in `docs/chain.md` so a later edit can check the figure.

Translate once:

```text
200 liters, about a bathtub
4 hours, a morning of work
2 meters of soil, about as tall as a door
```

If the analogy is the surprising part, the number can be the but: the textbook figure says one thing, the bathtub says why that is a problem.

## Worked example

This is a paraphrase of the earth-sheltered-house chain. It is not the reference Short's script. Count it as a shape to copy, then write a new artifact. It is shorter than the shipping short budget on purpose: a real short `script.md` is 10 to 12 beats at 15 to 18 words. `check_script.py` fails the beat count and the total. One short or long beat is only a warning. Spoken "So" is the recommended opener. "Therefore" is allowed. A caveat, if this house needed one, would be its own row after a therefore, between two buts, or just before the sign-off.

The porch-swing long form is the worked script at [examples/ds-bootstrap-build-up/script.md](../examples/ds-bootstrap-build-up/script.md): 30 beats, 533 spoken words, Format `build-up`. Use that when the short would drop load-bearing failures. Eric preferred it to the 78 s (about 80 s) Bootstrap short on 2026-11-20.

Artifact: an earth-sheltered house that stays dry

| Beat | Join | What happens | Picture |
| --- | --- | --- | --- |
| 0 | none | You pile soil on a flat roof to hold the heat. The roof holds water too. | Soil poured onto a flat slab. A puddle forms. |
| 1 | therefore | You pitch the roof so the water has somewhere to go. | A slanted slab. Arrows run downhill. |
| 2 | but | The soil wants to slide off the pitch. | Soil slipping toward the low edge. |
| 3 | therefore | You terrace the soil in short level steps. | Steps cut into the slope, soil sitting still. |
| 4 | but | Water still finds the wall and soaks the room. | A dark stain climbing an interior wall. |
| 5 | therefore | You set a drainage layer and a membrane behind the wall. | Cutaway: gravel, a sheet, then the wall. |
| 6 | none | The room stays dry and the soil stays put. Congratulations, you built an earth-sheltered house that stays dry. | Warm room, soil outside, title card. |

Spoken lines for the first two rows, so the voice is obvious:

```text
You pile soil on a flat roof to hold the day's heat. The roof holds the rain as well.
```

```text
So you pitch the roof, and the water has somewhere to go.
```

A failure and its fix can share a beat only when both fit in two short sentences and the picture can show both. When they cannot, split them, as the table does from beat 1 onward. Prefer the split.

A number that would earn a place here, if checked: the depth of soil that actually changes the temperature swing, stated as "about as deep as a door is tall" only after the figure is looked up. Leave `number: none` until then.

## Condensing a longer chain

An approved chain is often longer than 12 beats. The Data Science Bootstrap Notes short started there. For a YouTube Short, cut it before you synthesize. For a porch-swing video, keep the long chain, set Format to `build-up`, and skip this cut. Eric preferred that longer script to the 80 s short.

- Keep the opening naive failure and the sign-off.
- Rank the `but` beats by how much the picture changes. A new object in the `delta` (a file appearing in the tree, a pipe that was not there) outranks a tint of the same object. Keep the 4 or 5 whose picture changes the most.
- Drop the `therefore` whose `but` you dropped.
- Drop any fix that needs a second technical term to make sense. One new term per kept fix. If the line has to teach both pixi and pre-commit, it is two beats or it is gone.
- Keep a caveat only when the fix it qualifies survived. A caveat just before the sign-off can stay when the limit is still true of the cut.
- Re-count. 10 to 12 beats, 15 to 18 words, 4 or 5 `but` joins.

## Mining the docs

Before writing the chain from memory, grep the docs the Short is about. Problem headings and why headings are the candidate pairs.

```bash
uv run skills/explainer-video/scripts/check_script.py mine PATH/TO/DOCS
```

The command walks `*.md` under that directory. A heading that starts with "Why" is a why. Any other heading that says "problem" or "failure" is a problem. Each problem pairs with the next why in that file. The report is `path:line` plus the heading. Put that `path:line` in the beat's `source` field. A pair with no why is still a candidate failure. You still have to decide which four or five survive condensing.

## Checklist before synthesis

Run the checker. It encodes the budget, the join order, the sign-off, the banned joins, and the jargon scan.

```bash
uv run skills/explainer-video/scripts/check_script.py check PROJECT/script.md
```

- The artifact name is one line. A short's sign-off contains `Congratulations, you built X.` with that same X. A build-up sign-off is free text.
- Beat 0 is the naive version failing, not the finished object.
- Middle joins are `but`, `therefore`, or `caveat`, and `check_script.py` reports the order as valid.
- On a short: 4 or 5 `but` beats. Up to 7 in the chain table, then condense. On a build-up, keep the failures the chain needs.
- On a short: 10 to 12 beats, 15 to 18 words each, 150 to 216 spoken words. Prefer the 150 to 190 center. On a build-up, no beat or total cap; warn above about 650 words. Each therefore ends with "That's X." or "Those are X."
- Every number has a `source` of `path:line` and an everyday analogy in the line.
- Every beat's `delta` says what it adds to the persistent picture. The visual line does not restate earlier deltas. A path grows the file tree. A named kind (`number-counter`, `before-after-stat`, `cause-chain`, `checklist-pop`) is a picture template for that beat.
- Second person throughout. No "the user", no "we recommend".
- Nothing in the spoken lines was copied from the reference Short.
