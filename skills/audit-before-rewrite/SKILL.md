---
name: audit-before-rewrite
description: >-
  Guard against silent feature loss when REWRITING, RESTYLING, or REFACTORING an existing artifact via a wholesale file rewrite (HTML demo, marimo notebook, code file, design doc, ADR, SKILL.md). Use when: a restyling/refactoring subagent is about to rewrite a file that had features added in prior turns; you are converting an inline snippet to a standalone file or vice versa; a notebook is being re-saved/restructured; a design doc's decision is being revised to a previously-rejected alternative; you are about to paste a regenerated version over an existing file; or the user re-requests a feature that 'used to be there'. Procedure: BEFORE the rewrite enumerate every feature/section/behavior/anchor in the current artifact, carry each forward explicitly, and AFTER the rewrite diff before/after to confirm nothing was silently dropped. Root-cause note and sibling-skill distinctions in the body.
created_at: "2026-07-24"
---

# Audit Before Rewrite

Guard against silent feature loss when REWRITING, RESTYLING, or REFACTORING an existing artifact via a wholesale file rewrite (HTML demo, marimo notebook, code file, design doc, ADR, SKILL.md). Use when: a restyling/refactoring subagent is about to rewrite a file that had features added in prior turns; you are converting an inline snippet to a standalone file (or vice versa); a notebook is being re-saved/restructured; a design doc's decision is being revised to a previously-rejected alternative; you are about to paste a regenerated version over an existing file; the user re-requests a feature that 'used to be there' (smoking gun for silent loss); or any operation where the new content REPLACES the old wholesale rather than editing in place. The procedure: BEFORE the rewrite, read the current artifact and enumerate every present feature/section/behavior/anchor/metadata/__main__ block; carry each forward explicitly in the new version; AFTER the rewrite, diff before/after and confirm nothing was silently dropped. Restyling subagents that do a full-file rewrite are the #1 cause of silent feature regression because they regenerate from a template/spec without seeing prior-turn additions. Distinct from pre-move-reference-audit (file moves/renames, not content rewrites) and from verify-primary-action (checks a NEW action ran, not whether a rewrite preserved what existed).

## Instructions

## Procedure

BEFORE the rewrite (do these as tool calls, not narration):
1. READ the current artifact in full (read tool). Do not rewrite from memory of a prior turn.
2. ENUMERATE every present feature/section/behavior/anchor/metadata/__main__ block. Write the list down — in the rewrite reasoning or a scratchpad, not as a narrated preamble to the user.
3. For each enumerated item, decide explicitly: carry forward / intentionally drop / merge. Items marked 'carry forward' MUST appear in the new version.

DURING the rewrite:
4. WRITE the new version (write_file/Edit) in the SAME turn as the enumeration whenever possible. The feature list is the contract the new version must satisfy.

AFTER the rewrite:
5. DIFF before/after (git diff, or re-read both). Confirm every 'carry forward' item survived. If any is missing, that is a silent regression — restore it.

- After the diff, ALSO check for silent DUPLICATION, not just loss: the diff's added lines must be exactly the intended new content — regeneration can re-emit existing rows/sections a second time (2026-08-31: a restructured newsletter calendar table re-emitted rows 011 and 013 alongside the new schedule). Uniqueness-check any repeated row keys, headings, or anchors; if a line's occurrence count went UP without a matching intent, that is a silent regression too — deduplicate before reporting done.
## Critical failure mode: enumeration-as-narration

The most common failure of this skill is NOT skipping the audit — it is performing the audit as NARRATED PREAMBLE ('Let me think about what to keep vs change:', followed by a bulleted restatement of the file's sections) and then never issuing the rewrite tool call. The enumeration is correct thinking, but it must resolve into a write_file/Edit call in the same turn or the turn immediately after. A session that says 'Let me think about what to keep vs change:' and lists 9 sections and then says 'Actually, this is a large rewrite. Let me do it as a full write, being...' and trails off has FAILED this skill even though it appeared to follow the procedure.

Rules:
- If you have READ the file and ENUMERATED its features but have not yet issued the rewrite, your NEXT message MUST contain the write_file/Edit call — not more enumeration, not plan restatement, not 'Let me do it carefully.'
- The enumeration belongs INSIDE the rewrite tool call's reasoning (as the contract the new version satisfies), or as the final step before an immediate write. It does NOT belong as a standalone narrated list with no tool call following.
- 'This is a large rewrite' is not a reason to narrate more — it is a reason to write immediately, because large rewrites are where silent feature loss is most likely (more features to drop) and where narration-without-action is most tempting (the size feels like it justifies planning).

This is the rewrite-specific facet of the global execution-discipline rule (memory #84, #1741, #1742, #1765, #1769; AGENTS.md 'Execution Discipline'). The global rule says 'act in the same turn'; THIS skill says 'the feature-enumeration step of a rewrite is the #1 place that rule gets violated, because the enumeration feels like productive work.'

## When the skill does NOT apply

- Editing in place via a targeted Edit (oldString -> newString) rather than wholesale rewrite: no audit needed beyond the edit itself. The skill is about REPLACING the whole file.
- Creating a NEW file with no prior version to preserve: no audit needed (nothing to lose).
- The user explicitly asks to delete/replace without preservation: respect the request, skip the audit.

## widget-conversion-trigger

- Concrete trigger to add to the 'Use when' list: converting a markdown TABLE, PROSE BLOCK, or list into an INTERACTIVE WIDGET (.content-deck, .content-quiz, .content-panels, a tabbed/accordion component, an expandable details block). Widget conversion is a wholesale rewrite of that region and is a high-risk silent-loss site because the agent focuses on the widget markup and tends to replace FROM the converted block to the end of its containing section (or end of file), silently dropping every downstream feature that lived AFTER the widget boundary. Failure signature (sgbs-training Lesson 2, 2026-08-02): converting a message-types table into a .content-deck truncated the file at the widget — wiped 實作建議/思考信息, the ENTIRE 第二部分 (課堂實作活動), 功課, and 下週課程提醒; only caught because the user noticed Part 2 was gone. Mitigation: when converting any markdown block to a widget, read the file in full, enumerate every section AFTER the conversion point as 'carry forward', write the widget + trailing content together in one edit, then git-diff to confirm the diff spans only the converted region (not the whole file tail).

## edit-failed-write-file-fallback-trigger

- A SECOND truncation trigger distinct from widget conversion: when a targeted Edit (oldString/newString) FAILS on a large markdown/content file (mismatched oldString — often a curly-quote/whitespace codepoint issue per edit-tool-curly-quote-mismatch), the agent's instinct is to fall back to a wholesale write_file to 'just redo the change'. A write_file that pastes only PARTIAL content TRUNCATES the file and destroys every prior-turn addition after the paste boundary. Failure signature (sgbs-training Lesson 2, 2026-08-02, SECOND instance same day as the widget-conversion case above): editing quiz distractors (Q4 of content-quiz-lesson-2-review) — the Q4 Edit 'failed', the agent fell back to a write_file, and the file shrank 1706→1003 lines (~700 lines lost). This shows the audit-before-rewrite failure mode is NOT limited to deliberate rewrites — an Edit-FAILED → write_file-FALLBACK is an ACCIDENTAL wholesale rewrite and carries the same silent-loss risk. Mitigation: (1) when an Edit fails, do NOT abandon Edit for write_file — re-read the exact bytes and retry Edit with a corrected/smaller anchor (see edit-tool-curly-quote-mismatch for the shrink-the-anchor technique); (2) if a write_file is truly necessary, enumerate carry-forward features FIRST per the main procedure; (3) FAST GUARD — run 'wc -l <file>' before AND after any edit/write on a large content file and confirm the count is unchanged (targeted edit) or as-intended (rewrite); a line-count drop on a targeted edit is the smoking gun for truncation and is caught in <1s, faster than reading a git-diff; (4) keep content-rich markdown git-tracked so 'git restore <file>' recovers immediately (the agent correctly did this in the 2026-08-02 instance).

## yaml-enumerated-list-artifacts

- The rewrite-loss family extends to structured data files carrying ENUMERATED LISTS: rewriting a venue-research YAML's unresolved_questions list silently dropped the ONT group-transfer question (2026-08-18) — no error, plausible line count, caught only by manually re-reading the old list. Any YAML/markdown file with open-items / unresolved / probe-questions / checklists gets the same discipline: enumerate every list entry BEFORE the rewrite, carry each forward explicitly, diff entry-counts AFTER. Sibling to the list-head insertion clobber (an Edit oldString anchored on header+first-entry replaces that entry) — enumerate-then-diff catches both mechanisms.

## global-stylesheet-consumer-audit

- - Trigger to add to the 'Use when' list: rewriting a GLOBAL/SHARED stylesheet (or layout-level CSS) for a page-scoped redesign (new wrapper class, scoped design tokens). Scoping the new styles under a wrapper does NOT protect sibling pages if the rewrite also touches GLOBAL selectors — body font-family swaps, removal of global heading rules (h1-h6), base element styling. Failure signature (learn-anything Collection rewrite, 2026-08-23): interest.css rewritten with a .lp scope for the landing page; the rewrite switched body font-family to a new token AND dropped the global '.display, h1, h2, h3 { font-family: var(--font-display) }' rule; journey pages (/eric, /daniel) sharing the stylesheet silently lost their serif headings while the redesigned landing page verified clean — caught only because the post-rewrite QA happened to include the sibling pages. Variant failure: writing CSS for a wrapper class (.journey) that was never added to the sibling markup — a dangling selector that silently styles nothing. Mitigation: (1) BEFORE the rewrite, enumerate every GLOBAL selector that OTHER consumer pages depend on (body, h1-h6, a, shared component classes) and carry them forward OUTSIDE the scope (scoped rules override within the wrapper, so both can coexist); (2) confirm every class you style actually exists in the target markup before writing rules for it; (3) AFTER the rewrite, verify the SIBLING pages that share the stylesheet, not just the redesigned page. Generalization: for SHARED files, the audit unit is the file's CONSUMERS, not just the file's contents — enumerating features inside the file is insufficient when the loss lands on pages you never looked at.

## Execution ordering (the read is the first tool call)

- DISCIPLINE: when commissioned to APPLY a rewrite/restructure, the audit read of the current artifact is the FIRST tool call of the turn — announced plan and matching read must land in the same turn. Never skip ahead to drafting the replacement content as chat prose before the read has executed: an in-chat draft of new content (with zero tool calls) is narration-without-action, draws the 'Take action now' interrupt, and risks drafting against a stale mental copy of the file instead of its real current state (the very failure the audit exists to prevent). Drafting belongs inside the Edit/Write tool call, after the read. Instance 2026-08-28 (founder-video script): a 10-step restructure plan whose step 1 was 'read the current script' was followed by zero tool calls and an in-chat draft of the origin-story section; the session died at the interrupt with the restructure unapplied.