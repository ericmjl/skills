---
name: coherent-writing
description: "Improve coherence in drafts through a five-pass sub-agent workflow: resolve cross-draft argument conflicts, fix within-paragraph logic (self-contradictions, sudden topic jumps, disconnects, unsignaled pivots), smooth section transitions, smooth paragraph-boundary transitions, and run a final coherence audit. Use when a user says things like 'make this coherent', 'tighten the flow', 'this feels choppy', 'this paragraph contradicts itself', 'fix the logic jumps inside this paragraph', 'the sentences don't connect', 'can you smooth transitions', or asks to revise prose in Markdown, notes, essays, blog posts, emails, or docs so ideas connect cleanly without adding new points."
license: MIT
---

# Coherent Writing

## Usage

Use this skill whenever a user wants writing to read as one connected argument rather than disconnected points.

Target common requests such as:

- "Make this paragraph coherent."
- "Smooth the transitions."
- "This draft feels jumpy and repetitive."
- "Keep my voice, but make the logic flow."
- "This paragraph contradicts itself."
- "Fix the logic jumps inside this paragraph."
- "The sentences don't connect."

## Requirements

Require from the user when missing:

- Draft text to revise.
- Intended audience.
- Desired tone (formal, conversational, technical, persuasive).
- Non-negotiable constraints (length, keywords, claims that must remain).

Audience and tone are wired into every sub-agent prompt's CONSTRAINTS block (see [Global constraints](#global-constraints)) so sub-agents preserve them rather than over-rewriting.

## What It Does

Perform coherence-first editing in five passes with sub-agents:

1. **Global argument pass** — read the full draft and resolve cross-draft argument conflicts.
2. **Within-paragraph pass** — fix self-contradictions, sudden topic jumps, logical disconnects, and unsignaled pivots *inside* each paragraph.
3. **Section transition pass** — smooth every consecutive section boundary.
4. **Paragraph transition pass** — smooth every consecutive paragraph boundary.
5. **Final coherence audit** — recheck the whole piece and remediate remaining issues.

All passes preserve draft length, author voice, facts, and claims. They may not introduce new points, examples, citations, or arguments.

### Failure types this skill catches

Every pass is trained to detect and remediate these four failure types (plus pronoun fog as a fifth mechanical issue):

- **Self-contradiction** — two claims that cannot both be true.
- **Sudden topic jump** — a sentence introduces a different subject with no bridge.
- **Logical disconnect** — the sentence does not contradict the prior one, but the connection between them is never surfaced.
- **Unsignaled pivot** — a shift in mode (explanation → recommendation, claim → evidence, general → specific) with no warning to the reader.
- **Pronoun fog** — `this`, `it`, `they`, `which` with no clear referent.

Pass 1 hunts these at the cross-paragraph / whole-draft scale. Pass 2 hunts them *inside* each paragraph. Passes 3 and 4 hunt them at boundaries.

## How It Works

Run the passes in order. Do not skip passes. Do not merge passes.

### Diagnose-first discipline

Every sub-agent emits an **issue list FIRST**, then proposes fixes. Each issue entry is one line: `location + type + one-line description`. This lets the orchestrator surface the full issue list to the user before applying fixes (or apply automatically if the user has opted in), and it produces the consolidated "issues, one by one" deliverable the user asked for.

### Preparation (orchestrator only)

Before Pass 1:

1. Read the full draft once without editing.
2. Record baseline word count (target: stay within ±5%).
3. Parse structure:
   - **Sections**: blocks separated by Markdown headings (`#`, `##`, `###`, etc.). If no headings exist, treat the whole draft as one section.
   - **Paragraphs**: blocks separated by blank lines within each section.
4. **Extract a claim inventory** — one line per claim, anchored to its paragraph (e.g. `¶3: Bayesian methods handle small samples better than frequentist ones`). Pass 1 cross-references this inventory to catch contradictions systematically rather than eyeballing.
5. Build work queues:
   - Paragraphs (for Pass 2): each paragraph individually.
   - Section pairs: `(S1,S2), (S2,S3), ...`
   - Paragraph-boundary pairs: `(P1,P2), (P2,P3), ...` across the full draft in reading order.
6. Capture intended audience and desired tone.
7. Copy constraints into every sub-agent prompt (see [Global constraints](#global-constraints)).

For transition templates and anti-patterns, read `references/coherence-patterns.md`.
For sub-agent prompt templates, read `references/subagent-prompts.md`.

### Pass 1 — Global argument coherence (1 sub-agent)

**Goal:** Ensure the entire piece has no conflicting arguments at the cross-paragraph / whole-draft scale.

**Dispatch:** Exactly **one** sub-agent via the Task tool.

**Scope:** Full draft + the claim inventory from Preparation.

**Diagnose first, then fix:**

1. Cross-reference every pair of claims in the inventory; flag the pairs that conflict.
2. Emit an issue list (one line per conflict: `¶A vs ¶B: <one-line description>`).
3. Only then resolve each conflict.

**Allowed edits:**

- Resolve contradictions by aligning, clarifying, reordering, or trimming conflicting statements. Prefer trimming one of the two claims over bending both — bent claims rarely survive later passes.
- Clarify ambiguous claims so they no longer conflict.
- Remove duplicate arguments that fight each other.

**Forbidden edits:**

- Adding new arguments, examples, data, or citations.
- Expanding scope or changing the thesis unless required to resolve a direct contradiction.

**Output:**

1. Issue list (conflicts found, one per line).
2. Revised full draft.
3. Conflicts resolved (bulleted: conflict → resolution).
4. Final word count.

The orchestrator replaces the working draft with this output before Pass 2.

### Pass 2 — Within-paragraph coherence (1 sub-agent per paragraph)

**Goal:** Each paragraph is internally coherent — no self-contradictions, sudden topic jumps, logical disconnects, or unsignaled pivots *inside* the paragraph.

**Dispatch:** Launch **one sub-agent per paragraph** in parallel (Task tool, single message with multiple calls). For large drafts (>30 paragraphs), batch in groups of ~15 to keep dispatch manageable.

**Scope per agent:** The full interior of ONE assigned paragraph. No boundary work — that belongs to Passes 3 and 4.

**Diagnose first, then fix:**

1. Read the paragraph end-to-end.
2. Walk sentence-by-sentence and flag every failure instance (self-contradiction, sudden topic jump, logical disconnect, unsignaled pivot, pronoun fog).
3. Emit an issue list (one line per issue: `sentence N → N+1: <type>: <one-line description>`).
4. Only then revise.

**Allowed edits (interior of the paragraph):**

- Reorder sentences for logical progression.
- Replace vague referents (`this`, `it`, `they`, `which`) with concrete nouns already in the paragraph.
- Insert short connective phrases (NOT new claims) between sentences: `Because of this,`, `As a result,`, `The reason is that`, `In other words,`.
- Tighten or split compound sentences that bundle unrelated ideas.
- Delete redundant sentences that repeat the same claim.
- Add a topic sentence if the paragraph lacks one, drawn from claims already in the paragraph (never a new claim).

**Forbidden edits:**

- Adding new claims, examples, citations, or arguments.
- Editing outside the assigned paragraph.
- Merging with adjacent paragraphs or splitting the paragraph into multiple.
- Changing paragraph order.

**Edit budget:** Bounded by "no new claims," NOT by sentence count. May rewire multiple sentence-to-sentence transitions inside the paragraph. This is the key difference from Pass 4 (paragraph boundaries), which is tightly capped.

**Output per agent:**

1. Issue list (one line per issue).
2. Revised paragraph (full text).
3. One-line note: what changed and why.

The orchestrator merges revised paragraphs back into the working draft in document order, then proceeds to Pass 3.

### Pass 3 — Section transitions (1 sub-agent per consecutive section pair)

**Goal:** Every consecutive section pair flows smoothly; no abrupt section shifts.

**Dispatch:** Launch **one sub-agent per consecutive section pair** in parallel (Task tool, single message with multiple calls).

Example: sections `Intro`, `Methods`, `Results` → agents for `(Intro, Methods)` and `(Methods, Results)`.

**Scope per agent:** Only the boundary between its assigned section pair:

- The last paragraph(s) of the earlier section.
- Any heading or bridge between them.
- The first paragraph(s) of the later section.

**Allowed edits:**

- Add or rewrite bridge sentences at the section boundary.
- Tweak opening/closing sentences of adjacent sections for continuity.
- Adjust signposting so the reader knows why the next section follows.

**Forbidden edits:**

- Rewriting unrelated paragraphs inside either section.
- Adding new points, examples, or claims.
- Changing section order or merging/splitting sections.

**Output per agent:** Issue (if any) + revised boundary text + one-line note on what changed.

The orchestrator merges boundary edits back into the working draft in document order, then proceeds to Pass 4.

### Pass 4 — Paragraph-boundary transitions (1 sub-agent per consecutive paragraph pair)

**Goal:** Every consecutive paragraph pair flows smoothly; no abrupt paragraph shifts at the boundary.

**Dispatch:** Launch **one sub-agent per consecutive paragraph pair** in parallel.

Example: paragraphs `P1`–`P4` → agents for `(P1,P2)`, `(P2,P3)`, `(P3,P4)`.

**Scope per agent:** Only the boundary between its assigned paragraph pair:

- The last 1–2 sentences of the earlier paragraph.
- The first 1–2 sentences of the later paragraph.
- At most one short bridge sentence between them if needed.

**Allowed edits:**

- Rewrite transition phrases.
- Replace vague referents (`this`, `it`) with concrete nouns already present in the draft.
- Reorder or tighten existing sentences at the boundary.

**Forbidden edits:**

- Rewriting full paragraphs unrelated to the boundary. (The interiors were already handled in Pass 2 — do not redo that work here.)
- Adding new points, examples, or claims.
- Changing paragraph order or splitting/merging paragraphs.

**Output per agent:** Issue (if any) + revised boundary text + one-line note on what changed.

The orchestrator merges boundary edits back into the working draft in document order, then proceeds to Pass 5.

### Pass 5 — Final coherence audit (1 sub-agent)

**Goal:** Recheck the full revised draft for any remaining coherence issues and remediate them.

**Dispatch:** Exactly **one** sub-agent via the Task tool.

**Scope:** Full draft from Pass 4.

**Check:**

- No self-contradictions remain (within or across paragraphs).
- No sudden topic jumps, logical disconnects, or unsignaled pivots remain (within or across paragraphs).
- Section boundaries still flow.
- Paragraph boundaries still flow.
- Word count still within ±5% of baseline.
- No new points were introduced during earlier passes.

**If issues remain:** Apply minimal remedial edits (same constraints as earlier passes).

**Output:**

1. Audit-issue list (one line per remaining issue).
2. Final draft.
3. Audit report: issue → fix applied (or `No issues found`).
4. Final word count vs baseline.

### Between-pass verification (orchestrator discipline)

After applying each pass's output and BEFORE dispatching the next pass's
sub-agents, verify every reported change is actually present in the working
draft. A common failure mode: the orchestrator applies the SMALL edits a
pass produced (typo fixes, contraction normalisation) but skips or forgets
the SUBSTANTIVE edits (reworded claims, inserted bridge sentences, rewired
paragraph interiors), then dispatches the next pass against a stale draft.
The next pass then produces transitions against text that no longer matches
what the prior pass actually recommended, and the orchestrator loses track
of which edits are pending.

Verification step (run after every pass application):

1. Re-read the working draft in full.
2. For each change the pass reported, locate it in the draft and confirm the
   new wording is present (not just the old wording).
3. Only after every reported change is confirmed, dispatch the next pass.

This is especially important after Pass 1 (whose substantive conflict
resolutions are the foundation every later pass builds on) and after Pass 2
(whose interior rewires change the very sentences Pass 4 will edit at
boundaries).

### Bridge-at-section-start edit discipline

When applying a Pass 3 bridge edit that inserts a sentence at the START of a
section (i.e. between the section heading and the first paragraph), preserve
the heading. A common Edit-tool failure mode: the `oldString` anchor spans
both the heading and the first sentence, and the `newString` replaces that
span with the bridge + first sentence, silently DROPPING the heading.

Safe patterns:

- Anchor `oldString` to the first sentence ONLY (after the heading); insert
  the bridge before it. The heading is untouched because it is not in the
  edit span.
- OR anchor `oldString` to heading + first sentence and reproduce the
  heading unchanged in `newString`, with the bridge inserted between.

After every section-start bridge edit, re-read the boundary and confirm the
heading is still present.

### Global constraints

Include these in every sub-agent prompt, filling in the placeholders from Preparation:

```text
CONSTRAINTS (non-negotiable):
- Preserve author voice, facts, and intent.
- Intended audience: AUDIENCE.
- Desired tone: TONE.
- Preserve overall length (stay within ±5% of baseline word count).
- Do NOT introduce new points, examples, citations, arguments, or claims.
- Edit ONLY for coherence and transition smoothness.
- Do NOT change scope beyond what is needed to fix coherence.
```

### Orchestrator merge rules

When integrating sub-agent outputs:

1. Apply edits in document order (top to bottom).
2. Prefer the smallest edit that fixes the issue.
3. If two agents touched adjacent boundaries, keep the later merge and re-read the seam for smoothness.
4. After each pass, recompute word count before continuing.
5. If word count drifts beyond ±5%, trim redundant phrasing before the next pass — never by deleting substantive claims.
6. When a bridge edit touches the START of a section, preserve the heading (see [Bridge-at-section-start edit discipline](#bridge-at-section-start-edit-discipline)). Re-read the boundary after the edit and confirm the heading is still there.
7. After applying each pass's output, verify every reported change is present in the draft before the next pass (see [Between-pass verification](#between-pass-verification-orchestrator-discipline)). Do not dispatch the next pass against a stale draft.

### Return to user

Deliver:

1. **Final revised text** (full draft).
2. **Consolidated issue list** — all issues found across all passes, in reading order, one by one. Each entry: `pass · location · type · fix applied`. This is the deliverable that matches the "surface issues one by one" workflow.
3. **Pass summary** (brief):
   - Pass 1: cross-draft conflicts resolved (count).
   - Pass 2: paragraphs edited (count) + issues caught by failure type.
   - Pass 3: section boundaries edited (count).
   - Pass 4: paragraph-boundary transitions edited (count).
   - Pass 5: audit outcome (issues remaining: count).
4. **Length check:** baseline vs final word count.

Use this checkpoint rubric during every pass:

- **Continuity:** Does each sentence naturally follow from the prior one?
- **Progression:** Does each paragraph add something new?
- **Signposting:** Are transitions explicit where needed?
- **Alignment:** Does every section support the core claim?
- **No interior incoherence:** Is every paragraph free of self-contradiction, sudden jumps, disconnects, and unsignaled pivots?
- **Constraint compliance:** No new points; length preserved; audience and tone intact.
