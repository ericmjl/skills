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

**Map dependencies between items.** Build a dependency graph of the open
pool before ranking anything — **from GitHub metadata only**. Do not open
files, diff code, or investigate the codebase for this step; that study is
reserved for the one selected item in Phase 4. Cheap sources:

- **Issue → issue:** "blocks", "depends on", "parent of" mentions in bodies
  and comments (`gh issue view <N> --json body,comments`), plus tracking-issue
  checklists (`- [ ] #123`).
- **Issue → PR:** PRs that fix an issue (`closedByPullRequestsReferences`).
- **PR → PR:** stacked PRs (`gh pr view <N> --json headRefName,body` — "based on
  #X", "requires #X"), shared branch bases, and review chains.

Record for each workable item: what it blocks (its dependents) and what it is
blocked by (its prerequisites, whether open, closed, or external). A dependent
item is not `workable` until its prerequisites land — classify it as
`in-progress` or `workable` accordingly, but remember that finishing its
prerequisite unblocks it.

If metadata is ambiguous, do not dig deeper — record the edge as "unclear"
and let the selection rules handle it. An approximate graph from metadata is
cheap and good enough; an exact one from code study defeats the purpose of
picking one item per run.

**Verify before believing.** Spot-check 1–3 of the reporter's testable claims
against the codebase: does the referenced setting/command/API exist, does the
error string appear in the code, does the described behavior match the
implementation? Record each as confirmed, disputed, or unverifiable. If no
claims can be verified, cap your confidence at low and prefer `needs-info`
over a verdict. For `solved`, actually confirm the fix landed in a merged PR
or commit — a merged PR that does not touch the reported symptom is not `solved`.

Cite evidence for every disposition, prefixed `[issue]`, `[shell]`, or `[code]`.

### Phase 3 — Select exactly one

Topologically sort the `workable` pool using the dependency graph from Phase 2,
then pick **one and only one** item.

**Default rule: work from the roots of the dependency graph.** Prefer an item
that others depend on (high dependent count) and whose own prerequisites are
resolved, over a leaf item. Unblocking dependents multiplies progress — a root
fix may close several downstream items or make their PRs mergeable. In
particular, a dependency edge from a PR that cannot merge until its base lands
makes the base the default pick.

**Depart from the default only for a stated reason**, which you must write
down. Valid reasons:

- A quick fix elsewhere is trivially small and the root is a multi-day effort —
  but even then, only if the quick fix has no dependents waiting.
- The root is blocked by something external (maintainer decision, upstream
  repo, missing access) — record the blocker, work the next available item.
- A PR with unaddressed review comments is a dependent whose prerequisite (the
  review) is already resolved — finishing it is often the cheapest action
  available, so it competes well with graph roots.

Within the same dependency tier, score candidates:

1. **Impact** — severity, dependents, maintainer-marked labels (`high
   priority`, `good first issue`, `help wanted`).
2. **Freshness** — recent activity beats stale.

State the pick in one or two sentences: the reason and, if you departed from
the topo default, the stated reason. E.g. "Working on #123 — three issues
depend on it and its prerequisite #100 is closed. Skipped #45 (the other
root): blocked on a maintainer decision." If nothing is workable (everything
is `needs-info`, `in-progress`, or `solved`), say so instead of inventing
work, and report the blockers.

### Phase 4 — Execute the pick

**Issue selected → new PR:**

Now, and only now, study the codebase — for this one item:

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
