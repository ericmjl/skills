---
name: coherent-writing
description: "Improve coherence in drafts through a four-pass sub-agent workflow: resolve argument conflicts, smooth section transitions, smooth paragraph transitions, and run a final coherence audit. Use when a user says things like 'make this coherent', 'tighten the flow', 'this feels choppy', 'can you smooth transitions', or asks to revise prose in Markdown, notes, essays, blog posts, emails, or docs so ideas connect cleanly without adding new points."
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

## Requirements

Require from the user when missing:

- Draft text to revise.
- Intended audience.
- Desired tone (formal, conversational, technical, persuasive).
- Non-negotiable constraints (length, keywords, claims that must remain).

## What It Does

Perform coherence-first editing in four passes with sub-agents:

1. **Global argument pass** — read the full draft and resolve conflicting arguments.
2. **Section transition pass** — smooth every consecutive section boundary.
3. **Paragraph transition pass** — smooth every consecutive paragraph boundary.
4. **Final coherence audit** — recheck the whole piece and remediate remaining issues.

All passes preserve draft length, author voice, facts, and claims. They may not introduce new points, examples, citations, or arguments.

## How It Works

Run the passes in order. Do not skip passes. Do not merge passes.

### Preparation (orchestrator only)

Before Pass 1:

1. Read the full draft once without editing.
2. Record baseline word count (target: stay within ±5%).
3. Parse structure:
   - **Sections**: blocks separated by Markdown headings (`#`, `##`, `###`, etc.). If no headings exist, treat the whole draft as one section.
   - **Paragraphs**: blocks separated by blank lines within each section.
4. Build work queues:
   - Section pairs: `(S1,S2), (S2,S3), ...`
   - Paragraph pairs: `(P1,P2), (P2,P3), ...` across the full draft in reading order.
5. Copy constraints into every sub-agent prompt (see [Global constraints](#global-constraints)).

For transition templates and anti-patterns, read `references/coherence-patterns.md`.
For sub-agent prompt templates, read `references/subagent-prompts.md`.

### Pass 1 — Global argument coherence (1 sub-agent)

**Goal:** Ensure the entire piece has no conflicting arguments.

**Dispatch:** Exactly **one** sub-agent via the Task tool.

**Scope:** Full draft.

**Allowed edits:**

- Resolve contradictions by aligning claims, reordering, or trimming conflicting statements.
- Clarify ambiguous claims so they no longer conflict.
- Remove duplicate arguments that fight each other.

**Forbidden edits:**

- Adding new arguments, examples, data, or citations.
- Expanding scope or changing the thesis unless required to resolve a direct contradiction.

**Output:** Revised full draft + short list of conflicts found and how each was resolved.

The orchestrator replaces the working draft with this output before Pass 2.

### Pass 2 — Section transitions (1 sub-agent per consecutive section pair)

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

**Output per agent:** Revised boundary text + one-line note on what changed.

The orchestrator merges boundary edits back into the working draft in document order, then proceeds to Pass 3.

### Pass 3 — Paragraph transitions (1 sub-agent per consecutive paragraph pair)

**Goal:** Every consecutive paragraph pair flows smoothly; no abrupt paragraph shifts.

**Dispatch:** Launch **one sub-agent per consecutive paragraph pair** in parallel.

Example: paragraphs `P1`–`P4` → agents for `(P1,P2)`, `(P2,P3)`, `(P3,P4)`.

**Scope per agent:** Only the transition between its assigned paragraph pair:

- The last 1–2 sentences of the earlier paragraph.
- The first 1–2 sentences of the later paragraph.
- At most one short bridge sentence between them if needed.

**Allowed edits:**

- Rewrite transition phrases.
- Replace vague referents (`this`, `it`) with concrete nouns already present in the draft.
- Reorder or tighten existing sentences at the boundary.

**Forbidden edits:**

- Rewriting full paragraphs unrelated to the boundary.
- Adding new points, examples, or claims.
- Changing paragraph order or splitting/merging paragraphs.

**Output per agent:** Revised boundary text + one-line note on what changed.

The orchestrator merges boundary edits back into the working draft in document order, then proceeds to Pass 4.

### Pass 4 — Final coherence audit (1 sub-agent)

**Goal:** Recheck the full revised draft for any remaining coherence issues and remediate them.

**Dispatch:** Exactly **one** sub-agent via the Task tool.

**Scope:** Full draft from Pass 3.

**Check:**

- No conflicting arguments remain.
- Section boundaries still flow.
- Paragraph boundaries still flow.
- Word count still within ±5% of baseline.
- No new points were introduced.

**If issues remain:** Apply minimal remedial edits (same constraints as earlier passes).

**Output:** Final draft + short audit report listing any issues found and fixes applied.

### Global constraints

Include these in every sub-agent prompt:

```
CONSTRAINTS (non-negotiable):
- Preserve author voice, facts, and intent.
- Preserve overall length (stay within ±5% of baseline word count).
- Do NOT introduce new points, examples, citations, arguments, or claims.
- Edit ONLY for coherence and transition smoothness.
- Do NOT change scope beyond what is needed to fix coherence.
```

### Orchestrator merge rules

When integrating sub-agent outputs:

1. Apply edits in document order (top to bottom).
2. Prefer the smallest edit that fixes the transition.
3. If two agents touched adjacent boundaries, keep the later merge and re-read the seam for smoothness.
4. After each pass, recompute word count before continuing.
5. If word count drifts beyond ±5%, trim redundant phrasing before the next pass — never by deleting substantive claims.

### Return to user

Deliver:

1. **Final revised text** (full draft).
2. **Pass summary** (brief):
   - Pass 1: conflicts resolved.
   - Pass 2: section boundaries edited (count).
   - Pass 3: paragraph boundaries edited (count).
   - Pass 4: audit outcome.
3. **Length check:** baseline vs final word count.

Use this checkpoint rubric during every pass:

- **Continuity:** Does each sentence naturally follow from the prior one?
- **Progression:** Does each paragraph add something new?
- **Signposting:** Are transitions explicit where needed?
- **Alignment:** Does every section support the core claim?
- **Constraint compliance:** No new points; length preserved.
