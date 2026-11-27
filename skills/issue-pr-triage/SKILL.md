---
name: issue-pr-triage
description: "GitHub issue/PR triage that ends in action: survey open issues and PRs, classify what is solved, in progress, or workable, apply the one-command verdicts (close, label, comment) on the spot, then pick exactly one item and deliver a new PR or an updated PR. Stops at the open PR: never merges unless a rule in the target repo lets the agent merge. Use when asked to triage, sweep the backlog, find what can be closed, or pick something to work on."
license: MIT
---

# Issue & PR triage → one fix

A repeatable triage sweep using the GitHub CLI. Survey is read-only; every run
ends with exactly one item selected and worked to an open PR (new or updated).
The run stops there. A human merges the PR unless a rule in the target repo
lets the agent merge (see *Repo rules that grant merge authority*).

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
to a PR**. Housekeeping is not a separate output. Every item on the backlog
gets a verdict, a verdict that costs one command is applied on the spot, and
anything larger competes for the single pick. No run ends with a pending list.

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
| `blocked`     | Needs something this run cannot supply: a maintainer decision, an upstream fix, access. Record what it waits on. |

Open PRs get their own classification:

- `ready` — passing CI, no unaddressed review comments → waits for a
  maintainer to merge; not a candidate
- `needs-work` — failing CI, or unaddressed review comments → **workable**
- `stale` — author gone, no activity, conflicts → comment with an update
  request and a close-by date

**Map dependencies between items.** Build a dependency graph of the open
pool before ranking anything, grounded in **strong reasoning over the
codebase** — not just issue titles and linked references. These references are
hypotheses; the code is the evidence.

Sources, cheapest first, escalating as needed:

- **Issue → issue:** "blocks", "depends on", "parent of" mentions in bodies
  and comments (`gh issue view <N> --json body,comments`), plus tracking-issue
  checklists (`- [ ] #123`). Hypotheses only.
- **Issue → PR:** PRs that fix an issue (`closedByPullRequestsReferences`).
- **PR → PR:** stacked PRs (`gh pr view <N> --json headRefName,body` — "based on
  #X", "requires #X"), shared branch bases, and review chains.
- **Codebase:** for each candidate cluster, study the affected paths
  (`git log`, `rg`, reading the modules involved) to verify whether two issues
  actually trace to the same root cause or the same code path. A "depends on #N"
  claim the code contradicts is dropped; a code-derived dependency nobody
  wrote down is added.

The deliverable is a graph you trust: issues sharing a root-cause path in code
form a cluster whose root is the prerequisite; explicit references confirm or
extend what the code shows.

Record for each workable item: what it blocks (its dependents) and what it is
blocked by (its prerequisites, whether open, closed, or external). A dependent
item is not `workable` until its prerequisites land — classify it as
`in-progress` or `workable` accordingly, but remember that finishing its
prerequisite unblocks it.

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
is `needs-info`, `in-progress`, `solved`, or `blocked`), say so instead of
inventing work, and report the blockers.

### Phase 4 — Execute the pick

**Issue selected → new PR:**

Phase 2's codebase study already grounded the pick. Now go deep on this one
item:

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

**Stop at the open PR.** Both paths end with a PR that is open and ready for
a maintainer. Do not merge it, approve it, or enable auto-merge (`gh pr merge
--auto`). An approval can trigger an auto-merge that the author already
enabled. This holds even when CI is green and every review comment is handled:
a green PR is still a human's call to merge. The only way a run goes further
is a rule in the target repo that grants merge authority (next section).

**Do not start a second item.** Everything else goes in the final report as
backlog. If the selected fix turns out to be too large for one session, post
the partial findings on the issue; that comment is the result of the run. A
later run picks again from the remaining pool.

### Repo rules that grant merge authority

Some repos give the agent limited merge authority, for example: "the agent may
merge docs-only PRs that touch no code". A rule like that overrides the
default, but only within the limits it states.

Look for one before assuming there is none. Search the places where a repo
states policy for agents and contributors:

```bash
rg -n -i --hidden -g '!.git' merge \
  -g 'AGENTS.md' -g 'CLAUDE.md' -g 'CONTRIBUTING.md' \
  -g '.cursorrules' -g '.github/**'
```

Also check project-level skills or rules the repo keeps under `.agents/` or
`.claude/`.

A rule counts only if, read plainly, it lets the agent merge a defined class
of PRs. None of these count:

- A merge method ("use rebase merges").
- A repo setting (auto-merge allowed, no branch protection).
- A relaxed requirement ("docs-only PRs need no review"). It removes a
  barrier; it does not give the agent permission.

Before acting on a rule:

1. Check the PR against the rule with a command, not by impression. For a
   docs-only rule, run `gh pr diff <N> --name-only` and confirm every file is
   documentation, as the repo defines it. A workflow, script, config, or
   dependency file is code.
2. If the PR matches fully, merge the way the rule says: at once, or through
   auto-merge. Wait for CI first unless the rule allows skipping it; if that
   wait is too long for the session, leave the PR open and report it. If the
   rule names no method, follow the `gh-cli` skill's merge policy. Never
   bypass branch protection (`--admin`).
3. If the PR matches only partly, or the rule is ambiguous, leave the PR open
   and report the rule as a possible match.

Quote the rule and the check in the final report.

### Verdicts are applied, not proposed

Housekeeping belongs inside triage. A run that defers it to a confirmation
list ends with a list that no one acts on, and the pile grows with every run.

Every disposition is a verdict. When the verdict's action is one `gh` command
whose content is fully determined by the evidence that Phase 2 already
gathered, apply it on the spot:

- `solved` → close, with a comment that cites the fixing PR or commit.
- `duplicate` → close, with a comment that links the canonical issue.
- `needs-info` → label, and comment with what is missing.
- A wrong or missing label → fix it, when the evidence supports the label and
  not just the title. Keep labels minimal: one type label is usually enough.
- `stale` PR → comment with an update request and a close-by date. A later run
  closes the PR once that date passes without a reply.

These do not count against "one and only one". The one is a deliverable that
needs investigation and judgment (a PR). Closing three solved issues is three
verdicts, not three picks.

**Bright line.** If you would have to decide *what* to say beyond restating
the evidence, it is not a verdict application. It is a work item: put it in
the `workable` pool and let it compete for the pick. Typical cases: a
commenter's question that needs a real answer, an unaddressed change request
on someone's PR, a duplicate claim you could not verify.

**Never leave a verdict half-made.** "Close as solved, or keep open?" and
"which of these two is the duplicate?" are Phase 2 work that was not
finished, not questions for the user. Verify and act. If you cannot verify,
do not act: leave the item open, mark the claim as unverified in the evidence
column, and say so. That is a complete outcome.

**What only the user can do** — merge, review as the maintainer, make a
product call — is `blocked`. Record what it waits on in the disposition
table. That is a state, not a request: the run is complete without a reply.

Ask before acting only when a step is destructive and hard to undo
(force-push, deleting a branch) or falls outside the target repo. `--dry-run`
applies nothing, verdicts included.

## Rules

- Phase 1 is read-only. From Phase 2 on, act: apply verdicts, open or update
  the PR. Ask first only for destructive steps (force-push, deleting a branch)
  or actions outside the target repo.
- Never close a bug report. Close only duplicates, questions, invalid items,
  and `solved` items with evidence.
- Never dismiss an issue without investigation; never relabel based on title.
- Be honest: cannot reproduce or cannot verify → say so, do not guess.
- One and only one pick per run. Two items "in progress" is a failure.
  Verdicts applied on the spot are not picks.
- Stop at the open PR. Merging is never a step in a run: not at the end of
  Phase 4, not as an applied verdict, not under blanket approval, and not on an
  instruction given before the PR existed. Inside a run, the only exception
  is a repo rule that grants merge authority. A later request from the user
  to merge a named PR is not triage: handle it with the `gh-cli` skill.
- Prefer finishing an existing PR over opening a new one when both are workable.

## Final report

End every run with:

1. **Disposition table** — every open issue/PR with its disposition and
   evidence. For each verdict, say whether it was applied (closed, commented,
   labeled) or why it was not. For each `blocked` item, say what it waits on.
2. **The pick** — one sentence: what was selected and why.
3. **The result** — the new/updated PR URL, left open for a maintainer to
   merge, or honest blockers if nothing qualified. If a repo rule authorized
   a merge: the merged PR URL, the rule quoted word for word, and the check
   you ran against it.

Nothing is left pending. The report has no "say which of these to apply" list:
every verdict is applied, or has a recorded reason that it could not be.
