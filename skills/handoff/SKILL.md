---
name: handoff
description: >-
  Produce a verified handoff prompt/file that lets a fresh agent with zero context
  resume in-progress work cleanly. Use when a session is ending with unfinished work,
  when context is running low (~50-60% used — write EARLY, before the model dulls),
  when the user says "hand off", "save session state", "pick up where we left off",
  "prepare a handoff", "I'm switching windows/models", or when a session shows
  degradation (contradicting earlier decisions, re-exploring settled ground,
  misremembering files). Covers both writing the handoff and resuming from one.
  By default it writes a `.handoffs/` file; on request it folds everything into
  one self-contained paste-ready prompt instead ("single prompt", "one prompt",
  "stuff it all into the prompt", "no file").
license: MIT
---

# Handoff

## Usage

**Write a handoff (DROP mode)** when:

- A session ends with work unfinished and a fresh agent/session/window will continue it.
- The user asks to "hand off", "save progress", "prepare for a fresh session", or "write a handoff".
- Context is running low — suggest it proactively at ~50-60% usage, not at 90%.
- The session shows degradation symptoms: contradicting earlier decisions, re-deriving
  settled facts, or misremembering file contents. Say one sentence ("This session may be
  degrading — want me to write a handoff so a fresh agent picks up cleanly?") and stop.
  Never write the file without confirmation.

- **Single-prompt mode (INLINE)** when the user says "just give me one prompt",
  "stuff it all into the prompt", "no file", or the next session cannot read this
  repo's files (different machine, sandbox, web chat, non-coding agent). Same
  verification discipline and content — only the delivery changes: the entire
  handoff goes inside one paste-ready prompt instead of a file.

**Resume from a handoff (GRAB mode)** when starting work where a handoff exists
(check for one first — see How It Works), or when the user pastes one in.

**Do not use** for a finished task (nothing to hand off) or durable architecture
rationale (that belongs in a design doc or the project's persistent memory, not a
handoff).

## Requirements

- No dependencies. Works in any git or non-git project.
- **File mode (default):** writes one markdown file (`.handoffs/<YYYY-MM-DD>-<slug>.md`
  at the repo root; add `.handoffs/` to `.gitignore` — it is local scratch, not
  committed — unless the user asks to commit it) plus a resume prompt pointing at it.
- **Single-prompt mode:** writes no file; the full handoff is embedded in one
  paste-ready prompt (see Emit the resume prompt). Ask the user if they also want a
  record copy saved.

## What It Does

Produces a verified handoff — as a file plus resume prompt (default), or folded into
a single paste-ready prompt on request — and on resume, re-verifies that content
against repo reality before continuing. The handoff captures what
the next agent **cannot reconstruct from the code or git history**: the intent, the dead
ends already ruled out, and the exact next step — grounded in verified repo state, not
the chat narrative.

## How It Works

### Core principle: verify before you write

This skill runs precisely when memory is least reliable. Nothing goes in the file from
memory alone. A claim may be tagged `[V]` (verified) only if confirmed by a command or
file read **during this handoff run**; anything merely remembered is tagged `[?]` and is
a lead, not a fact.

1. **Orient in reality.** Run `git status`, `git branch --show-current`,
   `git log --oneline -15`, `git diff --stat`. No git? Re-read the files you believe
   you touched and list what actually changed vs. what you believe changed.
2. **Re-read, don't recall.** Re-open every file the handoff will mention. Any quoted
   path, line number, or snippet must come from this run's fresh read.
3. **Re-run ground truth.** Run the project's test/build/lint command. "Tests pass" is
   written only from output produced in this run — otherwise it's `[?]`.
4. **No invention.** Can't verify it and don't clearly remember it? Omit it. An honest
   gap beats confident fiction. If many claims end up `[?]`, write at the top:
   "Low-confidence handoff — verify aggressively."
5. If an older handoff exists, read its dead-ends and open-questions sections, carry
   forward anything still relevant (re-tagged `[?]` unless re-verified), then **archive
   it** (move to `.handoffs/archive/`), never delete it — its dead-ends section may be
   the only record of what not to retry. Single-prompt mode still archives an older
   file handoff — it just doesn't write a new one.

### Mine the conversation

Work through this checklist before drafting; skim-reading is how handoffs lose their
value:

- [ ] Goal in the user's terms + definition of done (the exact command/test that must go green)
- [ ] Work completed (every file modified, with specifics)
- [ ] **Failed approaches + why they failed** (the most expensive thing to re-discover)
- [ ] Decisions made + rejected alternatives + the WHY
- [ ] Test results and measurements (raw numbers, pasted output tails)
- [ ] Discoveries, gotchas, non-obvious facts ("known traps")
- [ ] User preferences expressed
- [ ] Remaining open questions the next agent must not guess past

### Write the handoff file

Keep every section; if one is genuinely empty, write "none". Target ≤250 lines,
hard ceiling 400 (it must fit in a fresh context). Cut narrative prose before cutting
Dead Ends, Verified State, or Next Steps.

```markdown
# Handoff: <one-line title>

Generated: <ISO timestamp> · Git HEAD: <short SHA> · Branch: <branch>
Trust rule: [V] = verified during this handoff run. [?] = unverified memory — re-check before relying on it.

## Goal & Acceptance Criteria
Why this work exists, the desired end state, and the exact test/command that must pass.

## Verified State (as of <timestamp>)
- [V]/[?] claims about what is committed, in flight, working, and broken — each with evidence.
- Test/build output tail, pasted from this run (never from memory).

## Decisions & Rationale
Decision + why + rejected alternative. The WHY stops the next agent relitigating.

## Dead Ends — DO NOT RETRY
What was tried → exactly how it failed → the specific reason → what to do instead.

## Known Traps
Non-obvious facts that would bite a stranger (file:line references).

## Next Steps (ordered)
Concrete, immediate action first. Not "finish the feature" — the literal next move,
with file and entry point.

## Open Questions
Unresolved decisions + current lean, so the next agent can proceed if no one answers.
```

Quality gate for every entry: *"Would a stranger with only this line avoid the mistake
we made?"* If not, add the file, line, or reason — or delete the entry.

### Emit the resume prompt

Both modes end with ONE paste-ready prompt, emitted inside a single fenced code
block so markdown-rendering agent UIs show a copy button — one click grabs the
whole thing. Introduce it with one prose line ("Copy the block below into your
next session:") and keep all other commentary outside the fence. Use a
four-backtick outer fence with no language tag: handoff content often quotes
fenced code or terminal output, and a longer outer fence survives inner
triple-backtick fences. (If any inner fence is itself four backticks, make the
outer fence longer than the longest inner fence.) Everything the next agent
needs goes INSIDE the block; nothing the next agent needs stays outside it.

**File mode (default):** write the handoff file, then emit:

````
Read .handoffs/<YYYY-MM-DD>-<slug>.md fully before any work. It is a verified
handoff: re-check its state against `git status`/`git log` before acting, resolve
its Open Questions with me before guessing, and start at its Next Steps.
````

Report the exact file path written and a one-line summary of what's in it.

**Single-prompt mode (INLINE):** write no file. Fold the full handoff — header with
trust rule, Goal, Verified State, Decisions, Dead Ends, Known Traps, Next Steps,
Open Questions — into ONE paste-ready block, with the trust rule and resume
instructions INSIDE it (the next agent sees only what is pasted). Emit:

`````
--- HANDOFF START ---
# Handoff: <one-line title>
Generated: <ISO timestamp> · Git HEAD: <short SHA> · Branch: <branch>
Trust rule: [V] = verified during the handoff run. [?] = unverified memory —
re-check before relying on it. You have only this prompt: re-check state against
the repo's `git status`/`git log` before acting, resolve Open Questions with the
user before guessing, and start at Next Steps.

## Goal & Acceptance Criteria
... (all sections, same content rules as the file template)
--- HANDOFF END ---
`````

Verification steps and the quality gate are identical in both modes; only the
delivery vehicle differs. Keep the same ≤250-line target / 400 hard ceiling — a
prompt much past that risks truncation on paste. If it won't fit: tighten content
first; fall back to file mode only as a last resort, and say why.

### GRAB mode: resume from a handoff

1. **Find it:** the newest file in `.handoffs/` (or the one the user names). If the
   user pastes an inline handoff instead, treat the pasted block as the handoff and
   skip to step 3.
2. **Read only that file** — do not load old session history.
3. **Trust but verify:** re-check its state against real `git status`/`git log` and the
   HEAD SHA in its header; re-run tests if the file claims they passed. Report drift
   explicitly: "the handoff said X, the repo now shows Y."
4. **Surface Open Questions** to the user; do not guess past a blocked step.
5. **Confirm the plan:** restate next steps adjusted for drift, get a go-ahead, then
   proceed.
6. **Retire it** when the work lands: fold durable learnings into a canonical doc, then
   delete or archive — don't let stale handoffs pile up.

### Common mistakes

| Mistake | Fix |
|---------|-----|
| Handoff restates the diff | The diff is already in git. Capture intent, dead ends, next step. |
| Built from chat, not `git status` | Verify first — a confidently-wrong handoff poisons the next session too. |
| "Tests were passing earlier" | Earlier ≠ now. Re-run them or write `[?]`. |
| Vague next step ("continue the work") | Write the literal next action with file and entry point. |
| Dead ends omitted | Naming what didn't work is the highest-value content — it saves a full re-derivation. |
| Padding thin sections | Invention is worse than a gap; write "not started, no design chosen" honestly. |
| Overwriting the old handoff | Archive it; carry forward its unresolved dead ends. |
| Single prompt so long it gets cut off on paste | Respect the 250-line target; tighten content before falling back to file mode. |
| Inlining when the next session can read the repo | Prefer file mode — it keeps the dead-ends archive chain alive. |
| Handoff emitted as prose or split across blocks | Copy buttons in markdown UIs attach to fenced blocks only — emit one contiguous fence, long enough to contain any inner fences. |
| Saving only at 90% context | Write at ~50-60%, while recall is sharp. Finish the current micro-step first, then save. |
