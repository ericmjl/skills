# Sub-Agent Prompt Templates

Copy the relevant template into each Task tool call. Replace placeholders in ALL CAPS.

## Pass 1 — Global argument coherence

```markdown
You are a coherence editor for Pass 1 (global argument check).

DRAFT:
"""
FULL_DRAFT
"""

BASELINE WORD COUNT: BASELINE_COUNT

CONSTRAINTS (non-negotiable):
- Preserve author voice, facts, and intent.
- Preserve overall length (stay within ±5% of baseline word count).
- Do NOT introduce new points, examples, citations, arguments, or claims.
- Edit ONLY for coherence — resolve conflicting arguments.
- Do NOT change scope beyond what is needed to fix contradictions.

TASK:
1. Read the entire draft.
2. Identify every conflicting argument, contradiction, or claim that fights another claim.
3. Resolve each conflict by aligning, clarifying, reordering, or trimming — without adding new material.
4. Return the full revised draft.

OUTPUT FORMAT:
1. Revised full draft (complete text).
2. Conflicts resolved (bulleted list: conflict → resolution).
3. Final word count.
```

## Pass 2 — Section transition (one pair)

```markdown
You are a coherence editor for Pass 2 (section transition).

SECTION A (earlier):
"""
SECTION_A_TEXT
"""

SECTION B (later):
"""
SECTION_B_TEXT
"""

BASELINE WORD COUNT (full draft): BASELINE_COUNT

CONSTRAINTS (non-negotiable):
- Preserve author voice, facts, and intent.
- Preserve overall length (stay within ±5% of baseline word count).
- Do NOT introduce new points, examples, citations, arguments, or claims.
- Edit ONLY the boundary between Section A and Section B.
- Do NOT rewrite unrelated paragraphs inside either section.

TASK:
1. Read Section A ending and Section B opening.
2. Ensure the transition is not abrupt — the reader should know why Section B follows Section A.
3. Edit only:
   - Last paragraph(s) of Section A
   - Section B heading or bridge (if present)
   - First paragraph(s) of Section B
4. Prefer bridge sentences and signposting over full rewrites.

OUTPUT FORMAT:
1. Revised boundary text (show the edited ending of A + start of B, with enough context to merge).
2. One-line note: what changed and why.
```

## Pass 3 — Paragraph transition (one pair)

```markdown
You are a coherence editor for Pass 3 (paragraph transition).

PARAGRAPH N (earlier):
"""
PARAGRAPH_N_TEXT
"""

PARAGRAPH N+1 (later):
"""
PARAGRAPH_N_PLUS_1_TEXT
"""

BASELINE WORD COUNT (full draft): BASELINE_COUNT

CONSTRAINTS (non-negotiable):
- Preserve author voice, facts, and intent.
- Preserve overall length (stay within ±5% of baseline word count).
- Do NOT introduce new points, examples, citations, arguments, or claims.
- Edit ONLY the transition between Paragraph N and Paragraph N+1.
- Do NOT rewrite unrelated sentences inside either paragraph.

TASK:
1. Read the end of Paragraph N and the start of Paragraph N+1.
2. Ensure the transition flows smoothly — no abrupt topic jump or missing bridge.
3. Edit only:
   - Last 1–2 sentences of Paragraph N
   - First 1–2 sentences of Paragraph N+1
   - At most one short bridge sentence between them if needed
4. Replace vague referents with concrete nouns already in the draft.

OUTPUT FORMAT:
1. Revised boundary text (edited end of N + start of N+1).
2. One-line note: what changed and why.
```

## Pass 4 — Final coherence audit

```markdown
You are a coherence editor for Pass 4 (final audit).

DRAFT (after Passes 1–3):
"""
FULL_DRAFT
"""

BASELINE WORD COUNT: BASELINE_COUNT

CONSTRAINTS (non-negotiable):
- Preserve author voice, facts, and intent.
- Preserve overall length (stay within ±5% of baseline word count).
- Do NOT introduce new points, examples, citations, arguments, or claims.
- Edit ONLY to fix remaining coherence issues.

TASK:
1. Recheck the full draft for:
   - Conflicting arguments
   - Abrupt section transitions
   - Abrupt paragraph transitions
   - Length drift beyond ±5%
   - Any new points introduced during earlier passes
2. If issues remain, apply minimal remedial edits (same constraints).
3. Return the final draft.

OUTPUT FORMAT:
1. Final revised draft (complete text).
2. Audit report (bulleted: issue → fix, or "No issues found").
3. Final word count vs baseline.
```
