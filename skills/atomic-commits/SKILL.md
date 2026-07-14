---
name: atomic-commits
description: "Break unstaged or mixed changes into small, atomic, logical git commits with Conventional Commit messages. Use when the user asks to commit, stage, or split changes — e.g. 'help me commit', 'commit my changes', 'break these into logical commits', 'what should I commit first', 'stage my changes', 'commit atomically', or 'make atomic commits'. Uses git diff, git add -p, and Conventional Commits (feat:/fix:/refactor:/chore:/docs:/test:/style:/perf:/build:/ci)."
license: MIT
---

# Atomic Commits

Guide the user from a dirty working tree to a clean commit history where each commit is one logical change with a clear Conventional Commit message.

## Workflow

### 1. Analyze changes

Run in parallel:

```
git status
git diff
git diff --cached
```

If there are too many files, also run `git diff --stat` for a summary.

### 2. Propose a commit plan

Group changes into atomic commits. Present the plan as an ordered table:

| # | Scope | Files | Commit message |
|---|-------|-------|----------------|
| 1 | ... | ... | `type(scope): description` |

**Grouping rules (priority order):**

1. **One concern per commit.** Separate refactorings from features from bug fixes. If a file has changes for two concerns, plan to use `git add -p` to split hunks within that file.
2. **Dependencies first.** If commit B depends on commit A, order A before B.
3. **Tests alongside or after.** Tests for a change go in the same commit or the immediately following one — never alone in a distant commit.
4. **Config/infra before features.** Build/config changes that features depend on come first.

**Commit message format** — Conventional Commits:

```
type(scope): imperative-mood summary

Optional body explaining why, not what.
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

Scope: optional but encouraged — the module, package, or area affected.

Rules:
- Imperative mood: "add feature" not "added feature"
- Lowercase summary, no period at end
- Under 72 characters for the summary line
- Body wraps at 72 characters

### 3. Execute — one commit at a time

For each proposed commit:

1. Stage exactly the right files/hunks: `git add <files>` or `git add -p <file>`
2. Show the user what will be committed: `git diff --cached --stat`
3. Create the commit: `git commit -m "type(scope): summary"`
4. If a pre-commit hook modifies files, handle the result (amend only if hook changes are expected and the user agrees)

**Within-file splitting (scripted `printf | git add -p` — proven reliable):** Scripted `git add -p` DOES work in this environment for within-file hunk splitting. Proven workflow (gym-coach 06-21: split an 8-hunk `mutations.ts` into a refactor commit + a feature commit cleanly):

1. **Pre-analyze hunk headers.** Run `git diff <file>` and read every `@@ -old,count +new,count @@ <context>` header. The `<context>` after `@@` names the function/region each hunk belongs to, so you can map each hunk to a concern (feature A, refactor B, etc.). Count the hunks. Adjacent hunks (close `@@` line numbers, e.g. @665 and @679) are still presented SEPARATELY by `git add -p` as long as they carry distinct `@@` headers.

2. **Determine the y/n sequence.** One `y`/`n` per hunk, in the order `git add -p` presents them (top-to-bottom = lowest `@@` line first). Worked example: 8 hunks, want all EXCEPT hunk 5 → `y y y y n y y y`.

3. **Script the split.** `printf 'y\ny\ny\ny\nn\ny\ny\ny\n' | git add -p <file>`. The `\n` newlines are required — `git add -p` reads one answer per line.

4. **Verify staged hunks BEFORE committing (mandatory).** Run `git diff --cached <file> | grep '^@@'` and confirm the staged hunk set EXACTLY matches your intent: correct count, correct `@@` line numbers, no extras. Also run `git diff --cached --stat` to confirm only the intended files are staged. This catches a wrong y/n sequence before it lands in a commit.

5. **Pre-split compile-safety check (the critical step).** BEFORE deciding to split, verify the INTERMEDIATE commit (staged set without the dependent commit's changes) still compiles and has no unused-symbol warnings. Trace each newly-added helper/function: is it still CALLED by code remaining in the staged set? Worked example: commit 1 (refactor) adds helpers `getOwnedSession` and `findSetByNormalizedName`; commit 2 (feature) adds `deleteSetForServer` which also uses them. Before splitting, confirm at least one mutation staged in commit 1 still calls each helper (here: `logSetForServer` calls `findSetByNormalizedName`, several mutations call `getOwnedSession`) — so commit 1 stands alone with no unused-symbol warning. Only split when every intermediate state is self-consistent. If any intermediate would not compile or would reference an undefined symbol, fall back to the "When NOT to split" rule below and keep that file's changes in ONE commit.


**When NOT to split hunks within a file:** When hunks are interleaved across multiple concerns (e.g. the same hunk touches both a new feature and an unrelated cleanup — an import for feature A alongside a deletion for concern B), do NOT attempt fragile manual hunk surgery. Cherry-picking line ranges or scripting `git add -p` responses often produces commits that don't compile or miss critical imports.

Instead, group that file's changes into ONE commit. A commit that reads as one coherent unit ("the page after wiring timer feedback, including the cleanup it enables") is better than three commits stitched from fragile partial edits. Narrative coherence beats strict per-concern atomicity when the cost of splitting is a broken intermediate state.

**Decision rule:** if splitting a file's hunks into separate commits would leave any intermediate commit non-compiling or referencing an undefined symbol, keep that file's changes in ONE commit. Move truly separable concerns (a deleted file, standalone doc changes, an isolated new file) into their own commits instead.

### 4. Verify

After all commits, run `git log --oneline -<N>` to show the resulting history and confirm with the user.

## Edge Cases

- **No changes to commit:** Say so. Do not create empty commits.
- **Only one logical change:** Skip the table; make a single commit directly.
- **Untracked files:** Include in the plan. Stage with `git add`.
- **Binary files:** Cannot split with `git add -p`. Assign to the most relevant commit.
- **Merge conflicts:** Do not attempt to resolve as part of this workflow. Alert the user.

## Pre-commit hook abort → staged-file leak (critical)

When a pre-commit hook MODIFIES a file (e.g. "fix end of files", ruff format), git aborts the commit. The index is unchanged, so any files staged for the NEXT planned commit (added earlier in the sequence) are still staged. Retrying with `git add <intended-file> && git commit` then commits the intended file PLUS all those leftover staged files — silently collapsing multiple atomic commits into one and destroying atomicity.

Root cause: `git commit` commits the ENTIRE index, not just the files from the most recent `git add`.

**Stash-conflict variant (distinct from a clean abort):** pre-commit stashes UNSTAGED changes before running hooks, then restores them after. If a hook (ruff format, end-of-file-fixer) MODIFIES a staged file, the stash restore can CONFLICT with the hook's fix — you see `[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...` + `[INFO] Restored changes from ...`. The commit then FAILS (no `[main <hash>]` line in the output) and leaves a messy index. This is a different signature from a clean hook abort: the commit silently does not land, and the staged set is now a jumble of files from multiple intended commits. Treat the absence of a commit-hash line as the signal that the commit did NOT land, regardless of the `[INFO] Restored changes` noise. Recovery is the same (unstage strays, re-stage intentionally) but the BEST fix is proactive — see defense 1 below.

**Stale-staged-blob variant (distinct from strays):** after a hook aborts on a file (e.g. pydoclint DOC101 missing `:param:`), fixing the violation in the WORKING TREE and retrying `git commit` WITHOUT re-staging FAILS AGAIN with the SAME error — the INDEX still holds the pre-fix blob, and hooks run on the STAGED content, not the working tree. Signature: you edited the exact line the hook complained about, `git diff` shows the fix present in the working tree, yet the hook re-reports the identical violation. Confirm with `git diff --cached <file>` (shows the old, unfixed version staged) vs `git diff <file>` (shows the fix unstaged). Recovery: `git reset HEAD -- <file>` (or `git reset` to clear the whole index) then `git add <file>` to stage the FIXED blob, then commit. ROOT RULE: any time you edit a file to satisfy a hook after an abort, re-stage it before committing — the index is a SEPARATE snapshot from the working tree, and a working-tree fix does NOT update the staged blob until you `git add` again. This is the mechanism behind defense 4 below: it is not only UNRELATED files from other commits that leak into the index — the SAME file's pre-fix blob lingers too. (Discovered build-deep-research-agent 07-09: pydoclint kept failing on `solutions/part3.py` + `tools/*` despite docstring fixes already in the working tree, until `git reset HEAD -- .` + re-stage resolved it.)

Defenses (apply to every commit in a sequence):

1. **PROACTIVE: pre-format / pre-fix BEFORE staging (prevents the conflict entirely).** Run the repo's formatter/linter on the changed files FIRST (e.g. `pixi run ruff format`, `ruff check --fix`, `npx prettier --write`), THEN `git add`. When the files are already formatted to the hook's spec, the hook finds NOTHING to modify → no stash/restore cycle → no conflict → clean commit. This is the single highest-leverage defense: it eliminates the failure mode at the source rather than recovering from it. Run `pixi run ruff format` (or the repo's equivalent task) over the full working tree once before starting an atomic-commit sequence; then every individual commit in the sequence is hook-clean by construction. (Discovered build-deep-research-agent 07-09: commits 2+3 failed with `Stashed changes conflicted with hook auto-fixes... Rolling back fixes` because ruff format wanted to reformat 2 files mid-commit; pre-formatting the tree first would have avoided 2 failed commits + a 48-file index leak.)

2. **Stage one commit at a time.** Do not pre-stage the next commit's files before the current commit succeeds.
3. **Verify before every commit.** Run `git diff --cached --name-only` (or `--stat`) and confirm the staged set EXACTLY matches the plan for the current commit. If extra files appear, they leaked from a prior failed attempt.
4. **After a hook abort, unstage strays first.** Run `git restore --staged <unrelated-files>` (or `git reset` to unstage everything and re-add intentionally) before retrying the commit.
5. **Re-stage the hook-modified file, then commit.** `git add <hook-modified-file>` only re-adds that file; it does NOT clear other staged files.

Recovery if a leak already landed in a tip commit (not pushed): `git reset --soft HEAD~1`, then `git restore --staged <files-that-do-not-belong>`, commit the intended subset, then stage and commit the rest.
