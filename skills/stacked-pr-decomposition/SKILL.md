---
name: stacked-pr-decomposition
description: Break long-lived pull request branches into a mergeable stack of small PRs with clear dependency order and story flow. Use when a branch has grown too large, when the user asks to split a PR into stacked PRs, or when each PR must be reviewable in about 5 minutes while preserving logical narrative across the stack.
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
