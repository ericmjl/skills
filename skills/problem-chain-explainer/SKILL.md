---
name: problem-chain-explainer
description: >-
  Write scripts and shot notes for short engineering or science explainer
  videos in the problem-chain style: the viewer is the builder, and each
  design feature arrives as the fix for a failure that just happened. Use
  when the user asks for a 45-90 second vertical Short, YouTube Short, Reel,
  or science explainer script; says "problem chain", "but/therefore",
  "design from first principles", or "productive failure"; or wants each
  spoken beat paired with a visual change. Also use when revising an
  explainer that lists features with "and then" instead of a chain of
  failures. For hooks, open loops, and speech-rate bands on other video
  types, use video-script-writing.
license: MIT
---

# Problem-chain explainer

Make the viewer the builder. Let the obvious version fail in a way they
can see, then earn each real feature as the fix. The chain is the script.

Four techniques, used together:

- **Problem–solution chaining.** Every feature is the answer to a failure
  the viewer just watched.
- **But/therefore structure.** Trey Parker and Matt Stone's rule: the next
  beat follows with "but" or "therefore", never "and then".
- **Design from first principles.** Start from the load, the water, the
  heat, the light, the air. A parts list is the wrong opening.
- **Productive failure.** The naive version fails in a concrete, visible
  way before the real design appears. Naming the feature first kills the
  chain.

## Usage

Use this skill for a spoken script, plus shot or visual notes, that
explains how one designed thing works. Typical asks:

- "Write a 60-second Short on why this bridge, house, or pump is built
  this way."
- "Turn these design features into a problem chain."
- "Make the viewer the builder."
- "Each feature should solve the failure before it."

Default shape: 45 to 90 seconds, vertical, one viewer, sound often off.
The narration is second person. "You" are building the thing.

Skip this skill for founder stories, ads, VSLs, testimonials, or a
generic retention pass. Those belong to `video-script-writing`. Skip it
for a finished MP4 (`motion-graphics-video`, `remotion-video`) and for
downloading a transcript (`youtube`). If the user hands you a source
video, paraphrase the chain. Leave the transcript's sentences behind.

After the chain exists, run `video-script-writing` for the hook tests,
the loop map, captions, and the cut spec. Keep the but/therefore joins.
That pass must leave them intact.

## Requirements

Ask only for what is missing:

- The artifact. One designed thing, not a survey of a field.
- Length. Default 60 to 75 seconds, inside the 45 to 90 second band.
- Audience. Default: a curious non-specialist on a phone.
- The real design features, or a source you may paraphrase. If a feature
  is unfamiliar, look it up. Do not invent a mechanism.
- Which numbers are already checked. Unchecked magnitudes stay out of
  the spoken script.

No special tools. Deliver markdown: a chain table, the spoken script, a
visual note on every beat, and the timing math.

## What It Does

Produces a script the viewer can follow with the sound off:

1. A naive version of the artifact, spoken as if it would work.
2. A chain of 4 to 7 failures, in the order a builder would hit them.
3. A checked number and an everyday comparison on the failures that need
   weight. No invented figures.
4. Each real feature introduced as the fix, with the mechanism in one
   plain sentence.
5. Joins of "but" (the fix leaves the next problem) or "therefore" (this
   beat is the direct consequence). Never "and then".
6. At most one honest caveat.
7. A payoff that cashes in the whole chain, then a second-person sign-off.

## How It Works

Do these steps in order. The chain table exists before any polished
spoken lines.

### 1. Pick the artifact

One thing the viewer could imagine building or operating. "A house inside
a hill" is one artifact. "Sustainable architecture" is a field, so it is
the wrong pick. Write the naive version in one or two spoken sentences:
the obvious thing a newcomer would try, stated as if it worked.

### 2. List the real design features

One line per feature the source actually uses. Keep the source's order
for this step. If you are not sure a feature is real, check it before it
enters the chain.

### 3. Reverse each feature into the failure it prevents

The failure is what the builder would see if that feature were missing.
Make it concrete and visible: mud on the floor, a dark room, water on
the wall. A label such as "structural inadequacy" is not a failure yet.

```text
Feature: arch
Naive state: a flat mud ceiling
Failure it prevents: the soaked ceiling drops on you
```

### 4. Order the chain

Sort by the moment the builder would hit the failure. For a building,
that order is structure, then water, then heat, then light, then air
quality. For another artifact, walk the build or the operating sequence
and place each failure at the first moment it would show up.

Keep 4 to 7 problems. Fold extra features into the beat they belong to,
or park them in a note under the table. Nine parts in a row is a list.
A chain is 4 to 7 problems.

### 5. Draft the beats

Fill the beat template for every problem. One idea per beat. The spoken
line fits in one breath. The visual note says what changes in the frame:
what appears, what breaks, what replaces it.

Link the beats before you polish sentences. Read the joins out loud.

- **But** links a beat whose fix holds and still leaves the next problem.
  "The arch carries the weight, but the hill is still pushing."
- **Therefore** links a beat that is the direct consequence of the beat
  before it. "You sealed the shell, therefore the air has nowhere to go."

If you can swap in "and then" and the line still works, the beat is a
new topic. Rewrite the join, or cut the beat.

### 6. Add numbers and analogies

Every failure beat has a number slot. Fill it with one checked figure
and one everyday comparison: "about two tonnes, like a small car on
every square meter." If you cannot check the figure, leave the slot
empty. Do not invent a magnitude, a percent, or a cost to fill it.

On a tight cut, keep a number on the first failure and one more near the
payoff. Middle beats may carry a comparison without a second statistic.

No jargon on first use without a one-clause gloss. "Compression, a
squeeze rather than a pull." "A membrane, a continuous waterproof sheet."
Gloss once, then use the word.

### 7. Write the payoff and the sign-off

The payoff cashes in the whole chain: what all those fixes were for.
The viewer should feel the point of surviving every failure.

Then stop on a second-person sign-off that names what they built.
"Congratulations, you built a house inside a hill." No subscribe line
and no recap of the parts.

Optional, once, after the feature it qualifies: one honest caveat a
real builder would still live with. "Tree roots can work through the
membrane over years." Pay the caveat off in the same breath. It does
not open a new problem unless runtime is left to finish that problem.

### 8. Read-aloud timing check

Count words in the spoken column only. Shot notes stay out of the count.
Divide by 150. That is the read-aloud length in minutes.

| Target | Spoken words at 150 per minute |
| --- | --- |
| 45 s | about 110 |
| 60 s | about 150 |
| 75 s | about 190 |
| 90 s | about 225 |

Read it aloud. If you run long, fold or park a beat. Speaking faster
will not save a long chain. If the piece is a feed Short and
`video-script-writing` calls for its faster short-form band, trim the
chain to that runtime. Keep the read clear.

Then hand the script to `video-script-writing` Steps 4 through 7: hook
(a reason, a number, and the promise inside the first seconds), loop
map, spoken-register pass, captions, and a visual change at least every
few seconds. The naive opening is the promise. A greeting is the wrong
opening for this genre.

## Beat template

Copy one block per problem. Beat 0 is the naive state and has no fix.

```markdown
### Beat N — FOUR-WORD FAILURE
- Join: but | therefore | none (opening only)
- Naive state:
- Failure:
- Number + analogy: CHECKED FIGURE, or "none — unchecked"
- Fix:
- Mechanism: ONE PLAIN SENTENCE
- Next problem: the but/therefore that hands off
- Visual change:
- Spoken:
```

## Checklist

- [ ] One artifact. The naive version is spoken before any real feature.
- [ ] 4 to 7 problems, ordered by the builder's first encounter.
- [ ] Every feature was reversed from a visible failure.
- [ ] Every join is "but" or "therefore". "And then" fails the read-aloud.
- [ ] One idea per beat. One mechanism sentence. One gloss for new jargon.
- [ ] Every spoken number is checked, and each one has an everyday
      comparison. Empty slots stay empty.
- [ ] At most one caveat, and it is specific.
- [ ] The payoff uses the whole chain. The sign-off is second person and
      names the thing built.
- [ ] Every beat has a visual change. The spoken line still makes sense
      as a caption with the sound off.
- [ ] Spoken word count / 150 is inside the target length.
- [ ] The chain is paraphrased. No source transcript was copied through.

## Worked example

Beat map, paraphrased, of an earth-sheltered house Short:
<https://www.youtube.com/shorts/AvRjarGrmC8>. This is the shape of that
chain, not its transcript. Reuse the shape. Do not paste these sentences
into a new script.

**Artifact.** A house inside a hill.

**Naive.** Dig a cave into a hill, hang a door, you've got a house.

**Builder order.** Structure, water, heat, light, air quality.

The table is the plan. A 90-second read is about 225 spoken words for
the whole piece, so each problem gets roughly 25 spoken words. Do not
read the mechanism cell aloud in full.

| # | Join | Failure | Fix | Mechanism | Visual change |
| --- | --- | --- | --- | --- | --- |
| 0 | — | The obvious cave seems finished. | — | — | A shovel opens a hillside. A door appears in the cut. |
| 1 | but | A storm soaks the flat ceiling and it drops. | An arch. | An arch turns the weight into compression, and concrete is good at compression. | The mud ceiling falls. An arch replaces it and the load runs around the curve. |
| 2 | but | The hill shoves the house downhill. | An uphill retaining wall tied into the slab. | The wall holds the hill back, and the slab locks the bottom of the wall so the hill cannot kick it out. | The hillside slides toward the arch. A wall grows out of the floor slab and stops the soil. |
| 3 | but | Rain runs down that wall and into the room. | A waterproof membrane, plus gravel and a drain. | The membrane blocks the water, the gravel gives it a path, and the drain carries it away. | Water sheets down the wall. A sheet, a gravel layer, and a pipe at the footing appear, and the water leaves. |
| 4 | but | The hill still pulls heat out through the concrete. | Rigid foam on the outside. | The foam keeps the concrete on the warm side, so the wall stores heat instead of leaking it. | The bare wall reads cold. Foam boards land on the outside face, and the inside face stays warm. |
| 5 | but | You buried the sun. | South glazing with an overhang. | Winter sun sits low and comes in under the overhang; summer sun sits high and the overhang shades it. | The room is dim. A south window and a brim appear. Low sun enters. High sun stops on the brim. |
| 6 | but | Rooms deeper in the hill still have no sky. | A light tube. | The tube pipes daylight in without opening a window onto the weather. | The back room stays black. A tube punches through the hill and a disk of daylight lands on the floor. |
| 7 | therefore | You sealed the shell, so moist air and soil gas have nowhere to go. | A radon membrane and vent, plus a ventilation unit. | The membrane blocks the gas and the vent gives it a way out; the ventilation unit, a fan that swaps the air, moves moist air out before it condenses on a cold surface. | Water beads on a cold spot. A sheet seals the slab, a vent pipe rises away, and two ducts trade air. |

**Number, on beat 1.** A meter of wet dirt weighs about two tonnes, like
a small car on every square meter of ceiling. Re-check the mass and the
comparison before you speak them in a new script. Later beats in this
outline leave the number slot empty on purpose.

**Caveat, once, on beat 3.** Tree roots can work through the membrane
over years.

**Payoff.** In winter the neighbors crank their heaters. Yours needs a
lot less, because the hill already did most of the work this chain just
built.

**Sign-off.** Congratulations, you built a house inside a hill.

**Payoff visual.** Cut from a neighbor's bright window to your door in
the hill. Their heat is working. Yours has less to do.

**Trim.** Rows 1 through 7 are the full chain, which is the top of the
4-to-7 range. It fits about 90 seconds only when each spoken beat stays
near 25 words. For 60 to 75 seconds, fold beat 2 into beat 1 (the arch,
and a wall tied into the slab so the hill cannot push back) and fold
beat 6 into beat 5 (south glass for the front, a light tube for the
rooms in the back). Keep the air beat. The winter payoff needs a shell
that is strong, dry, and warm.

**Spoken shape.** Paraphrase of the opening and the close. Shot notes
sit in brackets. The middle of the chain uses the same voice: one
failure, one fix, one picture, then the next problem.

```text
Dig a cave into a hill. Hang a door. You've got a house.
[A shovel opens the hillside. A door appears in the cut.]

But the first storm soaks the ceiling, and the mud comes down.
A meter of wet dirt weighs about two tonnes. That's a small car
on every square meter. So you build an arch. An arch turns that
weight into compression, a squeeze rather than a pull, and
concrete is good at compression.
[The ceiling falls. An arch replaces it.]

But an arch does not stop the hill pushing back.
[Beats 2 through 7, same shape, about 25 spoken words each.]

In winter your neighbors crank their heaters. Yours needs a lot
less.
[Their window burns bright. Your door sits quiet in the hill.]

Congratulations. You built a house inside a hill.
```

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Opening on the feature ("this house uses an arch") | Open on the naive version. The feature arrives as the rescue. |
| "And then" between beats | Rewrite the join. If "and then" still fits, the beat is a new topic. |
| A number you guessed | Cut it. An analogy without a fake figure is the honest line. |
| Jargon with no gloss | Add one clause on first use, or use the plain word. |
| Two mechanisms in one beat | Split the beat, or fold the lesser fix into one clause and say so in the trim note. |
| A caveat that starts a new chain | One caveat. Pay it off in the same breath, or cut it. |
| A payoff that lists the parts again | Say what the chain was for. The parts already had their beats. |
| Copying a source video line for line | Paraphrase the failures and the fixes. |
