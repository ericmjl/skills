# Script template

Copy this into the video project's `script.md`. Keep the chain table in `docs/chain.md`. The parser reads the headings and fields below.

The sample lines are short so the shape fits on a page. This sample is a `short`. A shipping short beat is 15 to 18 words, and a shipping short is 10 to 12 beats. `check_script.py` fails a short outside the beat count and the total word count. A single beat outside 15 to 18 words is a warning. A `therefore` beat opens with "So". "Therefore" is allowed; using it on every fix is a warning, not a failure.

For a porch-swing video, add `# Format` with `build-up` after `# Voice`. There is no 10-12 beat or 150-216 word cap. Warn above about 650 words. Each therefore ends with "That's X." or "Those are X." A but may recap ("Now X, but Y"). The caveat is optional. The sign-off is free text. See [examples/ds-bootstrap-build-up/script.md](../examples/ds-bootstrap-build-up/script.md).

```markdown
# Artifact

A rainwater cistern that stays drinkable

# Voice

eric

# Format

short

# Beats

## Beat 0

- join: none
- spoken: You dig a hole and drop in a tank.
- visual: A tank drops into a cutaway hill.
- number: none
- source: none
- delta: A tank in the hill

## Beat 1

- join: but
- spoken: But the first rain runs off the roof and brings the dirt with it.
- visual: Dirty water enters the tank. The tank is already on screen.
- number: none
- source: docs/cistern.md:12
- delta: Dirty water in the tank

## Beat 2

- join: therefore
- spoken: So you add a first-flush pipe that dumps the opening minute.
- visual: A diverter kicks the first flow aside. Do not redraw the tank.
- number: one minute of roof wash, about a bucket
- source: docs/cistern.md:40
- delta: A first-flush pipe

## Beat 3

- join: caveat
- spoken: The pipe only helps when the roof is the thing that gets dirty.
- visual: A label on the pipe, not a new object.
- number: none
- source: none
- delta: A limit noted on the pipe

## Beat 4

- join: but
- spoken: But a cracked tank still loses the clean water overnight.
- visual: A crack opens in the tank that has been on screen since beat 0.
- number: none
- source: none
- delta: A crack in the tank

## Beat 5

- join: none
- spoken: Congratulations, you built A rainwater cistern that stays drinkable.
- visual: Clear water reaches the tank. Title card with the artifact name.
- number: none
- source: none
- delta: Title card
```

Rules the parser enforces:

- Beat headings are `## Beat 0`, `## Beat 1`, and so on, with no skipped numbers.
- `# Format` is optional. `short` or `build-up`. Missing means `short`.
- `join` is `none`, `but`, `therefore`, or `caveat`. `none` is the opening and the sign-off.
- A `therefore` line starts with "So". "Therefore" is allowed. The field still says `therefore`. On a build-up, the line ends with "That's X." or "Those are X."
- A build-up `but` may open with "Now X, but Y" or "Finally, …". A short `but` still starts with But.
- A `caveat` sits immediately after the fix it qualifies, between two `but` beats, or immediately before the sign-off. In the sample, beat 3 qualifies beat 2. Beat 4 is the next failure, so it alternates with that therefore. The caveat does not take the turn. On a build-up the caveat is optional.
- `spoken` is what TTS receives, after the lexicon. So is the recommended opener. Repeated Therefore is a warning.
- `visual` is the new change, not a restatement of the whole picture.
- `delta` is optional. A path (`environment.yml`, `data/raw.csv`) grows the file tree. Comma-separated paths (`.env, .gitignore`) are separate files. A `~/` path (`~/dotfiles/install.sh`) is a second tree root. A sentence is a labeled row. Named kinds render as picture templates: `number-counter {"title": "Users", "value": 1285000, "suffix": "+"}`, `before-after-stat {"label": "Hours", "before": 12, "after": 3, "unit": "h"}`, `cause-chain {"title": "Why", "cause": "A", "mechanism": "B", "result": "C"}`, `checklist-pop {"title": "Ship", "items": ["Lint", "Tests"]}`. `key=value` pairs work too. The composition carries earlier deltas forward. Omitted, or `none`, means this beat adds nothing.
- `push` is optional. `auto` (default, and the value when the field is omitted) pushes the camera onto a new file-tree node. `none` skips. A number such as `1.8` is an explicit zoom. Duration follows the logarithmic formula in [hyperframes.md](hyperframes.md).
- `source` is optional free text. `path:line` is the useful form, and `none` means there is no citation. A script from before this field still parses. A beat with a number should still name a source.
- `number` is `none`, or a checked figure plus the everyday comparison. The number is also spoken inside `spoken`.

`check_script.py` also rejects spoken "and then", "also", and a line that opens with "next". It flags dotted filenames, ALLCAPS, CamelCase, and code-like tokens that are missing from `lexicon.json`.
