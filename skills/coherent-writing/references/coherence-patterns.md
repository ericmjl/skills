# Coherence Patterns

Use this file during rewriting when you need concrete transition language or fast diagnostics.

## Fast Diagnostics

Five failure types to look for at every scale (sentence-to-sentence inside a paragraph, paragraph-to-paragraph at boundaries, section-to-section, and cross-draft):

1. **Self-contradiction** — two claims that cannot both be true. The strongest failure; always flag these first.
2. **Sudden topic jump** — a sentence introduces a different subject with no bridge.
3. **Logical disconnect** — the sentence does not contradict the prior one, but the connection between them is never surfaced. The hardest to spot: each sentence looks fine in isolation, but the reader cannot say *why* sentence B follows sentence A.
4. **Unsignaled pivot** — a shift in mode (explanation → recommendation, claim → evidence, general → specific) with no warning to the reader.
5. **Pronoun fog** — `this`, `it`, `they`, `which` with no clear referent. Mechanical, common, easy to fix.

A sixth pattern, **orphan claim**, is a special case: an assertion appears without evidence or context. Treat as a logical disconnect on the claim-to-evidence axis.

### Where to hunt each type

- **Self-contradiction** — Pass 1 (cross-paragraph) and Pass 2 (within-paragraph).
- **Sudden topic jump** — Pass 2 (within) and Pass 4 (boundaries).
- **Logical disconnect** — Pass 2 (within). This is the within-paragraph pass's primary target.
- **Unsignaled pivot** — Pass 2 (within) and Pass 3 (section boundaries, where pivots are largest).
- **Pronoun fog** — Pass 2 (within) and Pass 4 (boundaries).

## Within-Paragraph Rewiring Patterns

Use when a paragraph's interior logic is broken (Pass 2 territory). All of these preserve the paragraph's claims; they only rewire how sentences connect.

### Expose a hidden link

Sentence B follows A for a reason the writer assumed but never stated. Insert the reason.

- Before: "The model overfits. We need more data."
- After: "The model overfits, *which means it has learned noise rather than signal*. We need more data."

### Reorder for cause-before-effect

If effect precedes cause in the sentence order, swap them so the reader sees the cause first.

- Before: "We need more data. The model overfits."
- After: "The model overfits. We need more data."

### Split a compound that bundles unrelated ideas

A single sentence carrying two unrelated claims reads as a disconnect.

- Before: "The model overfits and the UI is slow."
- After: "The model overfits. Separately, the UI is slow."

### Signal the pivot explicitly

Mark a mode shift so the reader expects it.

- Before: "The model overfits. Use regularization."
- After: "The model overfits. *To address this*, use regularization."

### Replace a vague referent

Pin down what `this`, `it`, `they` actually points to.

- Before: "This causes problems later."
- After: "This *overfitting* causes problems later."

### Delete the redundant sentence

If a sentence repeats the prior claim in different words, delete it. Don't tighten it — delete it. Repetition masquerades as emphasis but reads as a loop.

## Transition Templates

Use transitions sparingly and only when a link is unclear.

### Additive

- "Building on that,"
- "In the same vein,"
- "A related implication is"

### Contrastive

- "However, this breaks down when"
- "That said, the stronger interpretation is"
- "By contrast,"

### Causal

- "Because of this,"
- "As a result,"
- "This matters because"

### Sequence

- "First... Next... Finally..."
- "At this point,"
- "The next step is"

### Evidence-to-claim

- "Taken together, these details suggest"
- "This supports the broader claim that"
- "The practical takeaway is"

## Paragraph Frame

Use this frame when paragraphs feel loose:

1. Topic sentence with one claim.
2. Support sentence(s): evidence, example, or reasoning.
3. Link sentence: why this point matters for the thesis.

## Section Boundary Patterns

Use at section transitions when the shift feels abrupt:

### Preview the next section

- "With that foundation in place, the next question is..."
- "That sets up the part of the argument that follows:"
- "To see why this matters, consider..."

### Close the prior section

- "So far, this establishes..."
- "Taken together, these points show..."
- "That conclusion leads directly to..."

### Heading + bridge

When a heading alone is too abrupt, add one bridge sentence before or after it:

```markdown
## Methods

Building on the problem outlined above, the analysis proceeds as follows.
```

## Keep Voice While Improving Flow

Prefer these moves before rewriting tone:

- Reorder existing sentences.
- Add one bridge sentence.
- Delete duplicate sentences.
- Replace vague referents with concrete nouns.

Only change diction significantly when explicitly requested.

## Length Preservation

When smoothing transitions:

- Trim redundant qualifiers elsewhere if a bridge sentence adds words.
- Prefer tightening existing sentences over adding new ones.
- If a bridge is needed, keep it to one sentence.
- Target ±5% of baseline word count across all passes.
