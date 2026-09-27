---
name: large-file-edit-truncation-guardrail
description: >-
  Diagnose and prevent SILENT TRUNCATION when editing large files (1000+ lines, especially CJK/multibyte markdown) via Edit/StrReplace/write_file. Use when: an edit 'succeeds' but trailing content (entire sections, __main__ blocks) is silently dropped with no error; a full write_file rewrite produced a shorter file than expected; an Edit FAILED and you are considering a write_file fallback (do NOT — the #1 truncation trigger); the dedicated Grep tool finds nothing for content ripgrep finds in a CJK file; or the user says 'we keep truncating'. GUARDRAIL: check the line count (wc -l) before AND after every non-trivial edit on a large file — a drop larger than the intended delta = silent truncation. Root causes (write streaming cap; StrReplace over-match or stale-buffer flush; CJK search false-negative), tool preferences, git-restore recovery, the wrong-path-landing sibling failure, and lookalike-skill distinctions live in the body.
created_by: autolearn
created_at: "2026-08-02"
---

# Large File Edit Truncation Guardrail

Diagnose and prevent SILENT TRUNCATION when editing large files (1000+ lines, especially CJK/multibyte markdown like sgbs-training lesson files, marimo notebooks, long design docs) via Edit/StrReplace/write_file/Write. Use when: you are editing a 1000+ line file and the edit 'succeeds' but trailing content (entire sections — homework, next-week-reminder, Part 2, __main__ block) is silently dropped with NO error; a full write_file rewrite of a large file produced a shorter file than expected; an Edit/StrReplace FAILED and you are considering a write_file fallback (do NOT — this is the #1 truncation trigger); you are converting a markdown block to an interactive widget (.content-quiz/.content-panels/.content-deck) in a long file; you are running many sequential StrReplace calls on the same large file; the dedicated Grep/search tool returns no matches for content visibly present in a CJK file while ripgrep finds it; or the user says 'we keep truncating' / 'something went wrong, you have truncation' / 'why do we keep truncating?'. ROOT CAUSES (three distinct): (1) WRITE/WRITE_FILE STREAMING CAP — the tool streams new content and can cut off mid-file (output-length limit), so a full rewrite loses the tail with no error; (2) STRREPLACE OVER-MATCH OR STALE-BUFFER FLUSH — a malformed/ambiguous oldString consumes more than intended, OR the tool's in-memory buffer is shorter than disk (read-with-limit then edit) and the short buffer gets flushed, truncating to ~the first 1000 lines; (3) CJK SEARCH FALSE-NEGATIVE — the dedicated search/Grep tool returns no matches for multibyte content that ripgrep finds, so you wrongly conclude content is absent and overwrite it. GUARDRAIL (the skill's load-bearing discipline): CHECK THE LINE COUNT (wc -l) BEFORE AND AFTER every non-trivial edit on a large file — a drop larger than your intended delta = silent truncation, full stop. PREFERENCES in order: (a) targeted Edit/StrReplace over full write_file rewrite (only the matched region round-trips); (b) for multi-section scattered replacements, a Python script (read full file into memory, apply all subs on the string, assert len(lines) sane, write once) over many sequential StrReplace calls that each re-read a possibly-stale view; (c) for a single large contiguous deletion, sed -i 'N1,N2d' (see edit-tool-large-block-deletion-use-sed) over a giant oldString; (d) SMALL unique oldStrings (one span at a time) over one big multi-hunk edit. RECOVERY: if truncation already happened, restore from git ('git restore <file>' / 'git checkout HEAD -- <file>') BEFORE re-editing — NEVER hand-reconstruct lost content from memory; keep these files git-tracked precisely so this failure mode is recoverable. SMOKING GUN: you just ran an Edit/Write and the file line count dropped far more than your intended change accounts for (e.g. 1706 -> 1003), or a section header like '## 第二部分' that should be present returns no grep hit. Distinct from audit-before-rewrite (SEMANTIC feature loss during a planned wholesale rewrite — forgetting to carry features forward; THIS is MECHANICAL byte-loss where the tool itself drops the tail), recover-overwritten-source (forensic reconstruction AFTER the fact via typecheck/build specs; THIS is the PREVENTIVE line-count discipline that catches it the instant it happens, and applies to prose/markdown with no test spec), edit-tool-large-block-deletion-use-sed (DELETING a known contiguous range via sed; THIS is ACCIDENTAL content loss during an in-place edit that should have preserved length), and edit-tool-curly-quote-mismatch (WHY an oldString fails to MATCH; HERE the match may SUCCEED but still discard trailing content). Consolidates 12+ prior memory entries (#1234/#1237/#1238/#1241/#1246/#1247/#1248/#1250/#1252/#1254/#1255/#1256) that all describe the same failure family across sgbs-training, marimo notebooks, and agentindex Astro builds.

## Instructions

## Procedure

### 0. Pre-flight (before ANY non-trivial edit on a 1000+ line file)

1. Record the pre-edit state:
   ```bash
   wc -l <file>                       # expected line count
   rg -n "^## " <file> | tail -5      # tail section headers that must survive
   ```
2. Confirm the file is git-tracked: `git ls-files --error-unmatch <file>`.
   If it is not, `cp <file> <file>.bak` NOW. Truncation recovery requires
   a clean restore source.
3. Decide the edit shape (below) and pick the matching tool.

### 1. Pick the right tool for the edit shape

| Edit shape | Use | Do NOT use |
|---|---|---|
| Single small unique region (one span, ASCII-safe anchor) | Edit / StrReplace | write_file |
| Full-file rewrite / restyle / regenerate from template | audit-before-rewrite skill FIRST, then write_file | (only after the audit) |
| Many scattered single-line subs across the file | Python script: read full file, apply all subs on the string, `assert` sane, write once | many sequential StrReplace calls (each re-reads a possibly-stale view) |
| One large contiguous block delete (50+ lines) | `sed -i "" "N1,N2d" <file>` (macOS) — see edit-tool-large-block-deletion-use-sed | a giant oldString transcribed by hand |
| Edit FAILED with "oldString not found" | re-read the EXACT bytes around the target; shrink to a smaller no-quote anchor (see edit-tool-curly-quote-mismatch) | **write_file fallback** — this is the #1 truncation trigger |

### 2. The load-bearing guardrail

After EVERY non-trivial edit on a large file, before declaring done:

```bash
wc -l <file>                                # must match expected (pre +/- intended delta)
rg -c "^## (第二部分|Part 2|課堂實作活動|功課|下週)" <file>   # tail markers still present
```

A line-count drop larger than your intended delta = **silent truncation**.
Stop. Do not iterate on top of the truncated file.

### 3. CJK search false-negative check

If a Grep/search tool returns no matches for content you can SEE in the file
(common in CJK/multibyte markdown), do NOT conclude the content is absent:

```bash
rg <pattern> <file>     # bash ripgrep — the reliable path for CJK
```

Only after ripgrep confirms absence may you treat the content as missing.

### 4. Recovery (truncation already happened)

In priority order:
1. `git restore <file>` / `git checkout HEAD -- <file>` (cleanest — file is tracked).
2. `git show <hash>:<file> > <file>` for a specific known-good commit.
3. `git reflog` / `git stash list` for older good states.
4. Editor local-history (Cursor: `~/Library/Application Support/Cursor/User/History/`).
5. Built/rendered artifacts (e.g. `site/<slug>/index.html` for markdown content).
6. Verbatim chunks captured earlier in the conversation tool outputs.

**NEVER hand-reconstruct lost content from memory.** Restore from a source.

### 5. Root causes (for diagnosis)

Three distinct failure modes, all silent:

1. **WRITE / WRITE_FILE streaming cap** — the tool streams new content and can
   cut off mid-file (output-length limit). A full rewrite loses the tail with
   no error. Symptom: file shrinks to roughly the first ~1000 lines.
2. **STRREPLACE over-match or stale-buffer flush** — a malformed/ambiguous
   oldString consumes more than intended, OR the tool flushed a stale
   in-memory buffer (e.g. read-with-limit then edit) that was shorter than
   disk. Symptom: edit "succeeds" but trailing sections vanish.
3. **Concurrent editor + agent race** — an external editor (Cursor, VS Code)
   AND the agent both dirty on the same file; the agent read-then-writes a
   stale version that omits unsaved editor changes, or the editor flush
   clobbers the agent edit. Fix: only ONE party edits a given file at a time.

## When NOT to apply

- File is SMALL (< ~300 lines) or NEW (truncation loses nothing) — full write
  is fine.
- The drop in line count EXACTLY matches your intended deletion — that is
  success, not truncation.
- A real test/typecheck/build gates the file (code) — let the spec catch loss;
  this skill is for PROSE/MARKDOWN where no spec exists.

## Related skills

- audit-before-rewrite — SEMANTIC feature loss during a planned wholesale
  rewrite (forgetting to carry features forward). THIS skill is MECHANICAL
  byte-loss.
- recover-overwritten-source — forensic reconstruction AFTER the fact via
  typecheck/build specs. THIS is the PREVENTIVE line-count discipline.
- edit-tool-large-block-deletion-use-sed — DELETING a known contiguous range.
  THIS is ACCIDENTAL loss during an in-place edit.
- edit-tool-curly-quote-mismatch — WHY an oldString fails to MATCH. HERE the
  match may SUCCEED but still discard trailing content.
- markdownlint-rule-gotchas — unrelated lint failures (MD012/MD029/MD060).

## RECOVERY execution discipline

- Once truncation is confirmed and you have chosen git restore as the recovery (priority #1), EXECUTE the restore command in the SAME turn — do NOT narrate the recovery plan ('Restoring the file from HEAD comes first. Then I'll check...'). A recovery that is announced but not run leaves the file truncated and forces a 'Take action now' interrupt, exactly the narration-without-action anti-pattern (memory #54) recurring inside a truncation-recovery context. The recovery command is a single deterministic shell call (git restore <file> / git checkout HEAD -- <file>) — there is nothing to deliberate; run it, then verify with wc -l, then proceed. Discovered 2026-08-02 sgbs-training: assistant correctly diagnosed a 1994->997 line truncation and correctly chose git restore, but narrated the plan across a paragraph instead of running the command, forcing the user's 'Take action now' interrupt.

## same-day-recurrence-post-mortem

- POST-MORTEM (2026-08-02): this skill was created 2026-08-02 to consolidate 12+ truncation memory entries (#1234/#1237/#1238/#1241/#1246/#1247), and truncation RECURRED MULTIPLE TIMES IN THE SAME DAY — including the session that authored the skill. lesson-2-narrative.md (~1994 lines) was truncated to ~997-1003 lines by a full-file Write, recovered via 'git checkout HEAD'. The skill's EXISTENCE did not prevent recurrence because a skill is a PASSIVE surface; the agent loaded the rule, intended to follow it, then proceeded to narrate plans and run a full Write WITHOUT executing the guardrail bash command. HARD RULE: loading this skill is INSUFFICIENT. The FIRST tool call after loading must be the pre-flight 'wc -l <file>' and 'git ls-files --error-unmatch <file>'. If you load this skill and your next action is prose narration or a full Write, you have not actually loaded the discipline — re-read section 0 and execute the bash commands. This generalizes to ALL guardrail skills: existence-in-context != execution-in-bash. Same-day recurrence is the smoking gun that the skill was read but not run.

## DUPLICATED-RESIDUE variant (Edit oldString ending mid-block)

- The line-count discipline is BIDIRECTIONAL: an unexpected GROWTH in wc -l is as diagnostic as a drop. MECHANISM: an Edit/StrReplace whose oldString ends MID-BLOCK (inside a multi-step script region, rollback ladder, heredoc, or repeated-tail structure) replaces only the matched prefix; the un-matched tail of the original block survives AFTER the new content, leaving a DUPLICATED tail — syntactically valid (so bash -n / YAML parse still pass) but semantically wrong (steps run twice, duplicate echo blocks). Observed 2026-08-16 llamabot release-workflow YAML: an edit to the rollback step left a duplicated PyPI-critical + 'Rollback complete' tail at lines 452-457; caught ONLY by re-reading the final full file. GUARDRAIL: (1) prefer oldStrings spanning COMPLETE blocks (block-start anchor to block-end anchor) over mid-block prefixes; (2) after multi-hunk edits on workflow YAML / long files, re-read the full affected REGION, not just the edit site; (3) check wc -l before/after in BOTH directions — drop = silent truncation, growth = duplicated residue; either means the edit boundary was wrong.

## WRONG-PATH landing (write reports success, file lands in a different directory)

- Sibling of truncation in the verify-after-write family: the tool reports success but the artifact is NOT at the target path. Observed 2026-08-27 brain42: a vault write intended for `work/Newsletter/Opportunities/` landed in `work/Blog Draft/` under the same filename; the only signal was a downstream markdownlint glob counting 3 files when 4 had been written.
- GUARDRAIL: verify-after-write means verify EXISTENCE AND LOCATION — ls/glob the target directory after writing a file whose path matters, and cross-check any downstream glob/lint file count against the number of files written (a short count = a missing or misplaced file, not a clean pass).
- RECOVERY: search the workspace for the filename (`find <root> -iname "*fragment*"`), mv the found file to the intended path, re-verify. Do NOT reconstruct content from memory — the bytes were intact at the wrong path.

## ASCII-diagram anchor edit dropped adjacent line (2026-08-29 v2probe)

- Instance: fixing whitespace in an ASCII README diagram via minimal-unique-anchor edits dropped an ADJACENT content line (the user-profile.md line) — caught only on self re-read, then restored. Minimal unique anchors on whitespace-sensitive ASCII art are fragile: over-match or a stale buffer can consume a NEIGHBORING line even when the anchor itself matched correctly, and the edit still reports success. The line-count guardrail applies at diagram-edit granularity: after each ASCII-diagram edit, wc -l the file AND grep for the specific neighboring lines expected to survive (e.g. rg 'user-profile.md' <file>); a missing neighbor line = silent drop — restore it immediately rather than moving on to the next announced fix.
