---
name: processing-friendly-prose
description: >-
  Use whenever drafting or revising any prose for the user: emails, blog
  posts, docs, READMEs, tutorials, notebook markdown, video scripts, handoffs,
  and PR descriptions. This skill revises sentences so they are easier for a
  human reader to process: unpack stacked nouns, keep optional "that" in
  relative clauses, keep subjects close to their verbs, avoid animate verbs on
  inanimate subjects, and prefer ordinary wording over dense coinages. Also
  use when a draft feels hard to read, dense, or "AI-sounding" even after a
  voice or slop pass; when the user says "unpack this", "this is cognitively
  hard", "too compressed", or "make this easier to read"; or as a final pass
  after coherent-writing or blog-explainer-prose-dedup. Distinct from
  coherent-writing (argument flow and transitions) and
  blog-explainer-prose-dedup (repeated facts): this skill covers the shape of
  sentences, not the shape of the argument.
license: MIT
---

# Processing-Friendly Prose

## Usage

Use this skill when the ideas are already in place, but the sentences make
the reader work too hard. Common requests:

- "This is hard to read."
- "This feels dense / compressed / AI-sounding."
- "Unpack this."
- "Make this easier to read, without changing the claims."
- A final pass after a coherence, voice, or dedup pass.

This skill does not fix a choppy argument or a fact that appears twice.
For argument flow, use `coherent-writing` first. For repeated explanations,
use `blog-explainer-prose-dedup` first. Then run this pass, because those
edits can pack the sentences that remain.

## Requirements

Require from the user when they are missing:

- The draft to revise.
- Any claims, terms, or wording that must stay (quotes, numbers, names).
- Audience and tone, if they have not already been set.

Do not add new claims, examples, or citations to the draft. The examples
in this skill are for the editor, not material to insert into the user's
text.

## What It Does

It audits and repairs sentence shapes that are legal English, yet costly
for a human reader. Clark, Martin, and Mahowald (2026; see
[references/sources.md](references/sources.md)) show that recent
AI-generated text overuses such shapes: rare word pairs, long gaps between
a subject and its verb, stacks of nouns, relative clauses that drop
"that" or "which", inanimate subjects with verbs that usually take a
person, and one-off verbs made from nouns. They argue that training
rewards being brief and correct, not being easy to understand. A shorter
sentence is not always an easier one. A related study found that rewritten
text can take less total time to read only because it has fewer words,
while each word takes longer (Cekini et al. 2026).

The effect is stronger in long back-and-forth writing, in coding
explanations, and in tutorials than in a single short essay. Take extra
care in those settings, and in handoffs.

## How It Works

Run one audit, then repair. Do not mix this pass into a coherence or
dedup pass. List issues first, then edit.

### 1. Read the draft once

Do not edit on the first read. Note audience, tone, and any wording that
the user locked.

### 2. List issues before you change anything

Each issue is one line: `location + type + short description`. Types:

- **False brevity** — a cut that saves words but makes each remaining word
  harder.
- **Noun stack** — three or more nouns in a row, used as modifiers.
- **Dropped relativizer** — a relative clause that omits a "that" or
  "which" the reader would likely need.
- **Distant verb** — the subject and its verb are far apart.
- **Inanimate actor** — an inanimate subject takes a verb that usually
  takes a person or animal.
- **Ad-hoc denominal verb** — a noun used as a verb in a way that is not
  already common ("footnote it", "calendar it").
- **Rare wording** — a coinage or word pair that ordinary prose would
  not use.

Show the list to the user before you apply fixes, unless they have already
asked you to edit directly.

### 3. Repair, then re-read

Fix one sentence at a time. Keep the author's voice, facts, and length
in a reasonable band: a slightly longer, clearer sentence is a success,
not a failure. After the repairs, read the draft again and confirm that
you did not add claims or re-introduce the same issues.

## Checklist

Use these tests on every sentence you touch. Each item includes a
before and after. The "before" lines are examples of the problem, not
models to copy.

### Brevity is not readability

If you shortened a sentence by dropping a useful word or by packing
modifiers together, check whether the result is harder per word. Prefer
a slightly longer phrasing that the reader can predict.

- Before: "Skip optional that; compress meaning into marked constructions."
- After: "Keep the optional 'that', and say the meaning in a plain clause
  instead of a packed phrase."

### Unpack noun stacks of three or more

A stack of three or more nouns is hard to parse, and it is often
ambiguous. Turn the stack into a short phrase with prepositions or a
clause.

- Before: "the reader-patience budget"
- After: "how much patience the reader has left"

- Before: "the unit test failure retry policy"
- After: "the policy for retrying a unit test that failed"

Hyphenated terms that already name one thing (for example,
"object-relative") can stay. The problem is a fresh stack of nouns, not
a familiar compound.

### Keep optional "that" or "which"

Do not drop a relativizer just to save a word. Keep "that" or "which"
when the clause is long, or when the next noun is not the subject the
reader expects.

- Before: "the house the contractors built"
- After: "the house that the contractors built"

- Before: "the change the config file made to the scheduler"
- After: "the change that the config file made to the scheduler"

### Keep subjects and their verbs close

If a subject has to wait through a long aside before the verb arrives,
split the sentence or move the aside.

- Before: "The script that, after three reviews and a late change to the
  config, failed on the first run needs a tighter test."
- After: "The script failed on the first run. After three reviews and a
  late change to the config, it still needs a tighter test."

### Do not give inanimate subjects verbs that usually take a person

Tools, files, papers, and results can "return", "contain", or "show" in
the ordinary sense of those verbs. Do not give them verbs of eating,
biting, swallowing, thinking, or wanting. Name the human actor, or pick
a verb that fits an object.

- Before: "`is_file()` swallows that and returns False."
- After: "`is_file()` returns False and hides the error."

- Before: "The diagram assumes a sorted input."
- After: "We assume that the input is sorted, as the diagram shows."

### Avoid ad-hoc denominal verbs

A verb that started as a noun is fine when it is already common ("email
me", "ship the build"). Do not invent a new one to save words.

- Before: "Footnote it, then calendar the follow-up."
- After: "Add a footnote, then put the follow-up on the calendar."

### Prefer ordinary wording over rare coinages

If a two-word pair would be strange in ordinary prose, rewrite it. Common
terms of art in the field can stay; rare coinages should not.

- Before: "We surface a monitorability gap in the harness output."
- After: "We point out that it is hard to tell, from the output, what the
  tool actually did."

### Take extra care in long threads, coding notes, tutorials, and handoffs

These settings are where dense sentence shapes show up most often. When
you tighten a handoff toward a line budget, or shrink a tutorial
paragraph, do not do it by stacking nouns or by dropping "that".

## Related skills

- `coherent-writing` — argument flow, transitions, and contradictions.
  Run it first when the draft is choppy. This skill comes after.
- `blog-explainer-prose-dedup` — the same fact said more than once. Run
  it first, then this pass, because cutting repeats can pack what remains.
- `video-script-writing` — spoken scripts need this check even more:
  noun stacks and dropped "that" fail a table read.
- `handoff` — when you compress a handoff, keep the sentences easy to
  parse. The next agent is also a reader.
