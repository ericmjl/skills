---
name: issue-pr-triage
description: "GitHub issue/PR triage that ends in action: survey open issues and PRs, classify what is solved, in progress, or workable, then pick exactly one item and deliver a new PR or an updated PR. Use when asked to triage, sweep the backlog, find what can be closed, or pick something to work on."
license: MIT
---

# Issue & PR triage → one fix

A repeatable triage sweep using the GitHub CLI. Survey is read-only; every run
ends with exactly one item selected and worked to a PR (new or updated).

## Usage

Use this skill when the user asks to triage issues or PRs, or asks variants of:

- "Triage issues for me. What's been solved and can be closed? What's still
  open? What is already being addressed by an open PR?"
- "Pick one issue to work on."
- "Update my open PRs."

Inputs you should accept: repo (default: current checkout's `origin`), optional
issue/PR numbers, optional label filter, optional `--dry-run` for survey only.

## Requirements

- `gh` authenticated (`gh auth status`)
- A git checkout of the target repo (for claim verification and fixes)
- Optional: `jq`

## What it does

Four phases: **survey** (read-only) → **classify** → **select one** → **execute
to a PR**. Plus optional housekeeping (close/comment/label) that always requires
user confirmation.

## How it works

### Phase 1 — Survey (strictly read-only)

Gather the full picture before judging anything:

```bash
# Open issues and PRs
gh issue list --state open --limit 100 --json number,title,labels,updatedAt,author
gh pr list --state open --limit 100 --json number,title,updatedAt,headRefName,statusCheckRollup

# What each open issue is linked to (cross-references, closing PRs)
gh issue view <N> --json closedByPullRequestsReferences,body,comments

# PRs that reference an issue ("Fixes #N" in body)
gh pr list --state open --search "linked:issue"

# Was it already fixed by a recently merged PR or commit?
gh pr list --state merged --search "fixes #<N>" --limit 10
git log --oneline --since="<issue createdAt>" -- <affected paths>
```

Do not judge an item by its title alone. Read the body, the comments, any logs
or stack traces, and for PRs run `gh pr diff <N>`.

### Phase 2 — Classify

Assign exactly one disposition to each open issue:

| Disposition   | Criteria                                                                 |
| ------------- | ------------------------------------------------------------------------ |
| `solved`      | A merged PR or commit fixes it since the report. Verify before claiming. |
| `in-progress` | An open PR references it (`closedByPullRequestsReferences`, "Fixes #N"). |
| `needs-info`  | Bug report missing repro steps, versions, or environment.                |
| `duplicate`   | An open or closed canonical issue covers it. Verify the similarity.      |
| `workable`    | Actionable, unblocked work. This is the candidate pool for Phase 3.      |

Open PRs get their own classification:

- `ready` — passing CI, no unaddressed review comments
- `needs-work` — failing CI, or unaddressed review comments → **workable**
- `stale` — author gone, no activity, conflicts → candidate for housekeeping

**Verify before believing.** Spot-check 1–3 of the reporter's testable claims
against the codebase: does the referenced setting/command/API exist, does the
error string appear in the code, does the described behavior match the
implementation? Record each as confirmed, disputed, or unverifiable. If no
claims can be verified, cap your confidence at low and prefer `needs-info`
over a verdict. For `solved`, actually confirm the fix landed in a merged PR
or commit — a merged PR that does not touch the reported symptom is not `solved`.

Cite evidence for every disposition, prefixed `[issue]`, `[shell]`, or `[code]`.

### Phase 3 — Select exactly one

Pick **one and only one** item from the `workable` pool (an issue to fix, or a
PR to update). Score candidates:

1. **Quick fix first** — obviously small, well-understood fix wins.
2. **Then impact** — severity of the bug, maintainer-marked labels
   (`high priority`, `good first issue`, `help wanted`).
3. **Then freshness** — recent activity beats stale.

PRs with unaddressed review comments rank high: finishing existing work is
cheaper than starting new work.

State the pick in one sentence with the reason, e.g. "Working on #123 — small
repro, confirmed claim in `src/foo.ts`, no open PR covers it." If nothing is
workable (everything is `needs-info`, `in-progress`, or `solved`), say so
instead of inventing work, and report the blockers.

### Phase 4 — Execute the pick

**Issue selected → new PR:**

1. Reproduce the bug (or verify the feature gap). If you cannot reproduce, say
   so honestly — do not guess at causes; report and stop.
2. Create a branch from the default branch; implement the fix; add or adjust a
   test when practical.
3. Open the PR with body starting `Fixes #<N>` and a short evidence summary
   (symptom → root cause → fix).
4. Run relevant checks/linters before pushing.

**PR selected → updated PR:**

1. Fetch its branch (`gh pr checkout <N>` or fetch `headRefName`).
2. Address failing CI and each open review comment; rebase if conflicts.
3. Push updates; note what changed in a PR comment if the change is substantive.

**Do not start a second item.** Everything else goes in the final report as
backlog. If the selected fix turns out to be too large for one session, report
partial findings on the issue (with confirmation) and pick again from the
remaining pool.

### Housekeeping (optional, confirmation required)

After the survey, you may propose bulk actions — close `solved`/`duplicate`
issues, post `needs-info` comments, link duplicates to their canonical issue.
Propose them as a list and apply only after explicit user confirmation.
Applicable labels go on the selected issue/PR only, and keep them minimal —
one type label is usually enough.

## Rules

- Survey is read-only. Any state change (comment, close, label, push) requires
  explicit confirmation unless the user already granted blanket approval.
- Never close a bug report. Close only duplicates, questions, invalid items,
  and `solved` items with evidence.
- Never dismiss an issue without investigation; never relabel based on title.
- Be honest: cannot reproduce or cannot verify → say so, do not guess.
- One and only one selection per run. Two items "in progress" is a failure.
- Prefer finishing an existing PR over opening a new one when both are workable.

## Final report

End every run with:

1. **Disposition table** — every open issue/PR with its disposition, evidence,
   and (where applicable) the covering PR or canonical issue.
2. **The pick** — one sentence: what was selected and why.
3. **The result** — new/updated PR URL, or honest blockers if nothing qualified.
4. **Proposed housekeeping** — pending confirmation list, if any.
