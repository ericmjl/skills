---
name: stacked-pr-decomposition
description: Break long-lived pull request branches into a mergeable stack of small PRs with clear dependency order and story flow. Use when a branch has grown too large, when the user asks to split a PR into stacked PRs, when a stacked PR shows no CI checks because workflows filter on main (fix: gh stack init), when a freshly gh-stack-registered stack shows no workflow runs (stack creation fires no pull_request event — fix: push one real commit to fire synchronize), when the user asks about GitHub's native stacked-PR feature or gh stack commands, when MERGING a registered/native stack (gh stack merge: atomic all-or-nothing, draft-PR gate — gh stack submit creates drafts by default, async enqueue-then-poll, branches not auto-deleted), or when each PR must be reviewable in about 5 minutes while preserving logical narrative across the stack.
license: MIT
---

# Stacked PR Decomposition

Use this skill to split a long-lived branch into a sequence of small, mergeable stacked PRs that are easy to review and follow.

## Usage

Use when:

- A branch is too large for practical review.
- The user asks to break work into stacked PRs.
- Review goals include very fast human review (about 5 minutes per PR).
- The changes must retain a clear narrative from foundation to feature.

## Requirements

- Clean understanding of the current base branch (usually `main`).
- `git` available locally.
- `gh` available if opening PRs from CLI.
- Ability to run minimal verification (tests/lint/build checks relevant to each slice).

## What It Does

1. Maps the large branch into logical change groups.
2. Designs a narrative order for those groups.
3. Enforces a strict reviewability budget per PR.
4. Creates a stacked branch chain where each PR targets the previous PR branch.
5. Produces consistent PR descriptions so reviewers can move quickly.

## How It Works

### 1) Establish safe baseline and scope

1. Identify:
   - Base branch (`main` or project default).
   - Long-lived source branch to split.
2. Confirm branch is up to date enough to split safely.
3. Inventory changed files and classify by concern:
   - Pure refactor or mechanical prep.
   - Data/model or contract changes.
   - Core behavior changes.
   - UI/integration follow-through.
   - Cleanup/docs/tests.

### 2) Build a narrative stack plan

Plan PRs in dependency order:

1. Foundation first (no behavior change when possible).
2. Contract and model evolution second.
3. Behavior implementation third.
4. Integration/UI adoption fourth.
5. Cleanup and documentation last.

Each PR should answer:

- Why does this PR exist independently?
- Why must it come before the next PR?
- What reviewer mental model does it establish for the next layer?

### 3) Enforce 5-minute reviewability

Target each PR to be digestible in about 5 minutes:

- Prefer one concern per PR.
- Keep diffs compact and high-signal.
- Avoid mixing refactors with behavior changes.
- Include only tests that validate the slice.
- If a PR exceeds review budget, split it again.

Practical heuristics:

- Single intent, single headline.
- Small file count when possible.
- Minimal cross-cutting edits unless mechanically generated.
- Reviewer should summarize the change in one sentence after one read.

### 4) Materialize the stack with git branches

Create branches in sequence from base to tip:

```bash
git switch main
git pull

# PR 1
git switch -c stack/01-foundation
# cherry-pick or edit commits for slice 1

# PR 2 based on PR 1
git switch -c stack/02-contracts
# add slice 2

# Continue similarly...
```

Rules:

- Branch `stack/0N-*` starts from previous stack branch.
- Keep commit history clean and focused per slice.
- Avoid hidden dependencies that skip layers.

### 5) Validate each layer before opening PRs

For each stack branch:

1. Run targeted checks required for that slice.
2. Confirm branch compiles/tests independently relative to its base.
3. Ensure next branch still rebases cleanly if needed.

Do not open the next PR until the current slice is coherent.

### 6) Open stacked PRs with explicit chain context

When opening PRs:

- PR 1 base: `main`.
- PR N base: `stack/0(N-1)-...`.

In each PR body include:

- **Role in stack**: "PR 2 of 5"
- **Depends on**: previous PR link
- **Unblocks**: next PR link (if already opened)
- **Scope**: exactly what is in/out
- **Review guidance**: where to start, expected review time

Template:

```markdown
## Role
PR 2 of 5 in the stacked series.

## Scope
- ...

## Out of Scope
- ...

## Dependencies
- Base PR: #123

## Review Guide (5 min)
1. Read `path/a`
2. Read `path/b`
3. Run/inspect `test_x`
```

### 7) Keep the stack mergeable

As reviews land:

1. Merge from the bottom of the stack upward.
2. Retarget child PR branches onto `main` after their parent merges (see the
   `rebase --onto` technique below).
3. Keep PR descriptions updated so chain state remains obvious.

If one PR becomes contentious, isolate and resolve without bloating adjacent PRs.

#### Retargeting a child PR after its base merges (`rebase --onto`)

When a base PR merges — especially via **squash-merge** or **rebase-merge** — two
things happen at once:

- GitHub **auto-retargets** each dependent stacked PR's base from the merged
  branch to `main`.
- The child branch still carries the base PR's commits as **ancestors with the
  OLD SHAs**, while the commits that landed on `main` now have **NEW SHAs**
  (squash/rebase-merge rewrites them).

Because the SHAs differ, a plain `git rebase origin/main` can **fail to
auto-skip** the already-applied ancestor commits via patch-id detection, so you
end up resolving conflicts on commits that are *logically already in main*. The
fix is to replay **only your new commits** and drop the merged ancestors
explicitly:

```bash
# 1. Fetch and survey the boundary
git fetch origin
git log --oneline origin/main..HEAD   # your NEW commits (to keep)

# 2. CUTOFF = parent of your FIRST new commit (= old tip of the merged base branch)
CUTOFF=$(git rev-parse <your-first-new-commit>^)

# 3. Replay ONLY commits after the cutoff, onto main
git rebase --onto origin/main "$CUTOFF"

# 4. Force-push the retargeted branch
git push --force-with-lease origin <child-branch>
```

`git rebase --onto <newbase> <upstream>` replays every commit reachable from
`HEAD` but NOT reachable from `<upstream>`, on top of `<newbase>`. Setting
`<upstream>` to the cutoff (old base tip) excludes the merged ancestors from the
replay set entirely — no patch-id guessing, no phantom conflicts on
already-landed commits.

Verify on GitHub: `gh pr view <N> --json mergeable` reports `MERGEABLE`, and the
diff against `main` shows **only your new commits** with no resurrected ancestor
commits.

### 8) Quality bar checklist

Before considering the stack ready:

- [ ] Every PR has one clear intent.
- [ ] Every PR can be reviewed in about 5 minutes.
- [ ] Dependency chain is explicit and correct.
- [ ] Narrative order moves from foundation to outcome.
- [ ] Tests/checks are proportionate and passing per layer.
- [ ] Reviewers can understand each PR without reading the entire future stack.

## CI gap on stacked PRs (branch-filtered workflows)

A workflow configured with `on: pull_request: branches: [main]` (or any branch
filter) evaluates the filter against the PR's **base branch**. Stacked PRs
target the previous stack branch, not `main`, so branch-filtered workflows —
CI, preview deploys, required checks — **do not run** on them. Symptom: the PR
shows "no checks reported" and no preview environment. This is the workflow
working as configured, not a broken workflow or a blocked PR.

Rules:

- Do not debug the workflow or the PR when a stacked PR shows no checks —
  first read the workflow's `pull_request` branch filter.
- Before pushing a stacked PR, run the CI-equivalent verification locally
  (the same build/test/lint commands the workflow runs — e.g. `next build`
  plus backend deploy checks separately) so the slice is validated without CI.
- State the gap in the PR body or wrap-up ("CI runs once this PR retargets to
  `main` after the base merges") so a check-less PR is not a surprise to
  reviewers.

Retargeting nuance: GitHub auto-retargets a dependent PR only when its base
branch is **deleted** after merge. If the base PR merges with the branch kept
(e.g. rebase-merge without auto-delete), the child PR stays based on a
merged/dead branch — retarget manually (`gh pr edit <N> --base main`) and
confirm CI then kicks off.

### Fix: register the stack natively with `gh stack init` (public preview 2026-07-30)

GitHub ships NATIVE stacked PRs (public preview 2026-07-30). A manually-chained
PR stack (base branch = previous PR's head) has the stacked *shape* but is NOT a
first-class stack until registered. Registering it FIXES the CI gap above and
should be offered BEFORE retargeting or local-only verification:

- Create: `gh stack init --base main <branch1> <branch2> ...` (built-in gh
  command; also creatable from the web UI). The stack becomes a first-class
  object; member PRs carry a `stack` field in the REST resource, and the merge
  box shows a stack map.
- CI semantics: workflows trigger AS IF each PR in the stack targets the
  stack's BASE — a workflow with `on: pull_request: branches: [main]` runs for
  EVERY PR in the stack, not just the bottom one. Preview deploys and required
  checks fire on upper layers without retargeting.
- Merge semantics: merging the TOP PR merges the whole stack; merging a lower
  layer auto-rebases and auto-retargets the PRs above (replacing the manual
  `rebase --onto` / `gh pr edit --base` dance for that boundary).

After init, verify with `gh pr checks <N>` / `gh run list` and RUN the check in
the same turn — do not narrate a wait-and-watch plan (execution-discipline).
Follow-up discovery 2026-08-16 on learn-anything: user asked to use GitHub's
native stacked-PR feature; Stack #46 created via `gh stack init` linking PR #44
(planning/board-sync-gantt) + PR #45 (planning/portal-gantt) precisely so
deploy-website.yml would fire for #45.

Discovered 2026-08-16 on learn-anything: PR #45 (base
`planning/board-sync-gantt`, stacked on PR #44) ran no `deploy-website.yml`
CI because that workflow filters `pull_request` to `branches: [main]`; the
build was verified locally instead (`next build` + `convex dev --once`).

### Gotcha: stack registration alone does NOT trigger workflows

Registering a stack with `gh stack init` + `gh stack submit` (submit also pushes
the branches) emits NO `pull_request` event — stack creation is not a PR
activity type. The as-if-base CI semantics apply only to SUBSEQUENT
pull_request events (synchronize, reopened, ...), so after registering
already-open PRs, branch-filtered workflows still look dead until the next
push. Confirmed 2026-08-16 (learn-anything Stack #46): zero new workflow runs
immediately after `gh stack submit`; one real push later, `deploy-website.yml`
ran for the upper-layer PR (base = another stack branch) exactly as if it
targeted `main` — the semantics WORK, they just need an event to evaluate. Do
not conclude the feature is broken or not-yet-rolled-out when a
freshly-registered stack shows no runs.

To fire the needed `synchronize` event without violating git rules:

- PREFERRED: push ONE REAL commit. Bundle a genuinely pending improvement (a
  review fix, an a11y patch, a docs nit) as the trigger commit — the 2026-08-16
  session used a CDO a11y fix (click-only spans → keyboard-focusable anchors +
  `text-decoration: none` on `.gbar`/`.gdiamond-lg`) as the CI trigger, so the
  event double-counted as real work.
- Do NOT create an empty commit just to fire the event (empty commits require
  an explicit request).
- Do NOT amend + force-push to fire it (force-push requires an explicit
  request).
- Do NOT close + reopen the PR: `reopened` IS a default `pull_request` event
  type and would mechanically work, but it violates the SPIRIT of any "don't
  close the PR" instruction — never spend a user-issued constraint to save a
  turn.

### Adding a layer to an existing stack (`gh stack add`)

When follow-up work must NOT pile onto an already-open top PR (e.g.
post-review operational updates discovered after submit), add a NEW layer to
the registered stack instead:

```bash
gh stack add <branch-name>   # new branch layered on the current stack tip,
                             # created in the CURRENT worktree
# ... commit the follow-up work on the new branch ...
gh stack submit              # pushes branches and opens/updates the stack PRs
```

- `gh stack add <name>` creates the new branch on top of the CURRENT branch
  (the stack tip) in the CURRENT worktree, so an existing stack worktree
  continues in place — no new worktree needed.
- Stack membership state is tracked in per-branch `.stack` files inside the
  worktree — check for the `.stack` file when unsure how a worktree stack is
  tracked locally.
- The new layer PR targets the previous tip branch; a brand-new PR fires
  `pull_request` (opened) on creation — unlike re-registering already-open
  PRs, which fires no event (see the gotcha above) — so branch-filtered
  workflows evaluate with as-if-base semantics immediately.

Discovered 2026-08-16 (learn-anything board migration: `gh stack add
board/org-project` on top of `planning/portal-gantt` in the portal-gantt
worktree, landing org-project reference updates as a separate layer under
PRs #44/#45).

### Merging a registered stack (`gh stack merge` — atomic, async, draft-gated)

Discovered 2026-08-16 merging learn-anything Stack #46 (PRs #44 ← #45 ← #47):

```bash
gh stack merge <pr-number>   # merges everything up to AND INCLUDING that PR
# or: gh stack merge <stack-number>; bare numbers resolve stack-first, then PR
# non-interactive shells: pass --yes (or it merges whole stack w/o prompting
# using your last-used merge method unless one is specified)
```

Semantics (from `gh stack merge --help`):

- **Atomic all-or-nothing**: all members of the stack up to and including the
  chosen PR merge into the base branch in ONE operation — if any PR cannot
  merge, NONE are. Merging the TOP PR lands the whole stack; merging a lower
  PR merges everything below it and auto-rebases/retargets the layers above.
- **Draft gate (the gotcha)**: only basic PR state is pre-checked — "open and
  not a draft". `gh stack submit` opens NEW PRs as **drafts by default**, so a
  freshly-submitted top PR blocks the whole stack merge. Fix: `gh pr ready
  <top-PR>` then retry. Nuance: PRs that pre-existed the stack registration
  (opened via `gh pr create`, then linked with `gh stack init`/`link`) keep
  their non-draft status — only the submit-created PR needs the ready flip.
- **Async enqueue**: the merge runs via GitHub's async merge path
  (`PUT .../merge-async`; with a merge queue the stack joins the queue) — the
  call returns immediately and the merge completes in the background. POLL
  until the PRs report MERGED; do not assume failure or success at enqueue
  time. Bypassing merge requirements is NOT supported for stacks.
- **Verification**: the stack lands LINEARLY on main as one commit range
  (Stack #46: 7 commits, `d239376..cd3313f`, rebase-style history preserved).
- **Post-merge leftovers (both verified 2026-08-16)**: member branches are NOT
  auto-deleted from origin (all three remained on `git ls-remote`) — delete
  them explicitly if wanted; and the local checkout's main is NOT auto-synced
  — `git fetch origin && git merge --ff-only origin/main` (preserves unrelated
  unstaged changes) to catch up. Stack worktrees hold the stack's `.stack`
  files — safe to remove after the merge lands.
