---
name: coherent-writing
description: "Improve coherence in drafts by diagnosing broken flow, rewriting transitions, aligning paragraph purpose, and preserving author voice. Use when a user says things like 'make this coherent', 'tighten the flow', 'this feels choppy', 'can you smooth transitions', or asks to revise prose in Markdown, notes, essays, blog posts, emails, or docs so ideas connect cleanly from sentence to sentence and section to section."
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

Perform coherence-first editing:

- Diagnose where flow breaks (topic jumps, missing bridge sentences, abrupt section shifts).
- Enforce one clear job per paragraph (claim, support, implication).
- Add or rewrite transitions so each paragraph answers "why this next?"
- Remove duplicates and reorder sentences for progressive logic.
- Preserve facts, intent, and voice unless user asks for deeper rewriting.

## How It Works

Follow this workflow in order:

1. Read the full draft once without editing. Identify the thesis, section goals, and expected logical path.
2. Mark coherence breaks:
   - abrupt shift in subject
   - unsupported assertion
   - repeated point without added value
   - pronoun/reference ambiguity
3. Perform structural edits before sentence polish:
   - reorder paragraphs or sentences for cause -> evidence -> implication flow
   - add one bridging sentence where a reader would otherwise ask "why now?"
4. Perform local edits:
   - tighten topic sentences
   - strengthen transition phrases
   - remove redundant qualifiers and repeated claims
5. Run a final coherence pass:
   - each paragraph links back to the section goal
   - each section links back to the thesis
   - no paragraph starts from unexplained context
6. Return the revised text plus short notes on major structural changes.

Use this checkpoint rubric during revision:

- **Continuity:** Does each sentence naturally follow from the prior one?
- **Progression:** Does each paragraph add something new?
- **Signposting:** Are transitions explicit where needed?
- **Alignment:** Does every section support the core claim?

For additional transition templates and anti-patterns, read `references/coherence-patterns.md`.

