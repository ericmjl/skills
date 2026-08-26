---
name: gh-cli
description: Use GitHub CLI (gh) for common operations like creating PRs, viewing GitHub Actions logs, managing issues, GitHub Projects boards (gh project field/item automation), reviewing PRs, and more. When merging PRs via gh, use rebase merge only (--rebase) — standing user rule (Eric, 2026-08-26: "in general i want to do rebases only, never any type of merge"): never merge commits, never squash-merge, unless Eric explicitly requests otherwise for a specific PR.
license: MIT
---

# GitHub CLI Operations

This skill provides quick access to common GitHub CLI operations for managing repositories, pull requests, issues, and GitHub Actions.

## Requirements

- `gh` (GitHub CLI) - must be authenticated with your GitHub account
- Run `gh auth login` if not already authenticated

## Common operations

### Merge policy (PRs)

When merging with `gh pr merge`, **always use rebase merge** (`--rebase`): it reapplies the PR commits on top of the base branch for a linear history. Standing user rule (Eric, 2026-08-26: "rebases only, never any type of merge"): never squash (`--squash`), never a merge commit (`--merge` / plain merge), unless Eric explicitly asks for that style on a specific PR.

### Pull requests

**Create a new PR**:
```bash
gh pr create --title "Your PR title" --body "Description of changes"
```

**Create a PR with auto-fill (from commit messages)**:
```bash
gh pr create --fill
```

**Create a draft PR**:
```bash
gh pr create --draft --title "WIP: Feature X"
```

**Create a PR with a rich markdown body (shell-escaping workaround)**:
PR bodies with backticks, parentheses (), dollar signs, or other shell-special
characters fail when passed inline via `--body "..."` because zsh/bash
interprets them. This is the most common failure when creating PRs with code
blocks, markdown links like `[text](url)`, or any non-trivial formatting.

Use `--body-file` instead — write the body to a temp file first:
```bash
cat > /tmp/pr-body.md <<'EOF'
## Summary
Rich markdown with `backticks` and [links](https://example.com) here.
EOF
gh pr create --title "Title" --body-file /tmp/pr-body.md
```

The `--body-file` flag is supported by `gh pr create`, `gh pr edit`,
`gh issue create`, `gh issue comment`, and `gh pr review`. Use it as the
DEFAULT whenever the body is more than a simple one-liner — it avoids all
shell-escaping surprises.

**List PRs**:
```bash
# List open PRs
gh pr list

# List all PRs (including closed)
gh pr list --state all

# List your PRs
gh pr list --author @me
```

**View a PR**:
```bash
# View PR in terminal
gh pr view 123

# Open PR in browser
gh pr view 123 --web
```

**Check out a PR locally**:
```bash
gh pr checkout 123
```

**Review a PR**:
```bash
# Approve
gh pr review 123 --approve

# Request changes
gh pr review 123 --request-changes --body "Please fix the typo"

# Comment
gh pr review 123 --comment --body "Looks good overall"
```

**Merge a PR** (default to rebase; see [Merge policy](#merge-policy-prs)):
```bash
# Preferred: rebase and merge (linear history)
gh pr merge 123 --rebase

# Auto-merge when checks pass (still use rebase)
gh pr merge 123 --auto --rebase

# Only when explicitly desired: merge commit
gh pr merge 123 --merge

# Only when explicitly desired: squash and merge
gh pr merge 123 --squash
```

### `gh pr merge --auto` requires BOTH repo settings: auto-merge enabled AND an allowed merge method

`gh pr merge --auto --<method>` fails permanently when the repo does not permit
it. TWO independent repo settings gate it:

1. **Auto-merge must be enabled** on the repo (`allow_auto_merge: true` — this
   is OFF by default).
2. **The flag's merge method must be allowed** (`allow_rebase_merge` /
   `allow_squash_merge` / `allow_merge_commit`). A rebase-only repo rejects
   `--squash` no matter what.

**Diagnose before writing merge flags into a workflow:**

```bash
gh api repos/{owner}/{repo} \
  --jq '{allow_auto_merge, allow_squash_merge, allow_rebase_merge, allow_merge_commit}'
```

**In GitHub Actions**, make the auto-merge step degrade gracefully instead of
failing the job:

```yaml
- name: Enable auto-merge
  env:
    GH_TOKEN: ${{ github.token }}   # GH_TOKEN is gh's canonical env var
  run: |
    if ! gh pr merge --auto --rebase; then
      echo "::warning::Auto-merge unavailable (disabled on repo or method not allowed) — leaving PR open."
    fi
```

Keep the PR body honest too: do not promise auto-merge if the repo may not
allow it.

**To enable true hands-off auto-merge** (one-time repo setting):

```bash
gh api -X PATCH repos/{owner}/{repo} -f allow_auto_merge=true
```

Discovered llamabot PR #392 (2026-08-16): a workflow step ran
`gh pr merge --auto --squash` on a repo with `allow_auto_merge: false` AND
`allow_squash_merge: false` (rebase-only) — the step could never succeed.

### Local cleanup failure after `gh pr merge` does NOT mean the merge failed

`gh pr merge` (especially with `--delete-branch`) runs in TWO phases: it performs the **server-side merge FIRST**, then **local cleanup SECOND** (checkout the base branch, `git pull`, delete the local branch). When the local-cleanup phase errors, the merge on GitHub has **already succeeded** — the remote branch is deleted and the PR is merged. **Do NOT retry the merge** (it errors "already merged"). Verify the real state first, then fix only the local side.

**Step 1 — always verify the merge landed before doing anything else:**
```bash
gh pr view <N> --json state,mergedAt   # expect state: MERGED + a mergedAt timestamp
```

**Step 2 — diagnose which local-cleanup variant failed and recover:**

- **Dirty working tree** (`error: cannot pull with rebase: You have unstaged changes`): the local sync aborted because the tree has uncommitted WIP. Recover:
  ```bash
  git stash -u && git checkout main && git pull --ff-only && git stash pop
  git branch -d <pr-branch>   # now safe; tree is clean
  ```
- **Branch checked out in a git worktree** (local branch deletion fails; git refuses to delete a branch that is checked out in a worktree): common on repos that use a **worktree-per-PR** convention (e.g. the website's worktree-per-blog-post workflow). The remote branch is already deleted and the PR is merged on GitHub. Recover by removing the worktree, which releases the local branch:
  ```bash
  git worktree list                      # find the worktree path for this PR
  git worktree remove <worktree-path>    # releases the checked-out branch
  git branch -d <pr-branch>              # optional; now deletable
  ```

**Root principle (both variants):** a local-cleanup error is a LOCAL-side problem; the server-side merge is done. Confirm `MERGED` via `gh pr view`, then clean up the local checkout/worktree. Never re-run `gh pr merge` in response to a local-cleanup error. Consolidates the dirty-tree case (memory #463/#680) and the worktree case (website PR #241, 2026-08-07).

### 503/5xx on `gh pr create` — the PR may exist anyway (verify before retrying)

A 5xx (e.g. 503) from `gh pr create` does **not** prove creation failed: the
mutation can commit server-side before the error response is returned. Blindly
retrying creates a **duplicate PR** from the same branch.

**Verify before retrying:**

```bash
gh pr list --head <branch>           # does a PR already exist for this branch?
gh pr view <branch> --json number    # if yes, use it — do not re-create
```

Only re-run `gh pr create` if no PR exists for the branch.

**Root principle:** a client-side error from a GitHub create-mutation is not
proof of server-side failure — check server state before re-mutating. This is
the create-side sibling of the merge-side section above ("local cleanup failure
after `gh pr merge` does NOT mean the merge failed").

Discovered llamabot PR #392 (2026-08-16): the GitHub API returned 503 on
`gh pr create`; the PR had actually been created on the first attempt.

### Post-merge follow-through (verify landing, sync main, return to main)

After `gh pr merge <N> --rebase --delete-branch` succeeds, the job is NOT done
until the local side is synced and the user is back on main (Eric's default
ritual, website PR #288, 2026-08-14: "merge using rebase and pull latest changes
back to main on that PR, and then switch me back to main branch"):

1. **Verify the commits landed**: `git fetch origin main`, then confirm the PR's
   commits appear on `origin/main` (single-commit PR:
   `git log origin/main --oneline | head`). `gh pr view <N> --json state` must
   report `MERGED`.
2. **Switch the main checkout/worktree to main**: `git checkout main`.
   Unrelated uncommitted changes (e.g. the user's local `opencode.json` edits)
   carry over safely — do NOT stash or discard them.
3. **Fast-forward local main WITHOUT `git pull`**: `git merge --ff-only origin/main`.

**Why not `git pull`:** with `pull.rebase = true` (this machine's config),
`git pull` on a tree with unstaged changes ABORTS with
`error: cannot pull with rebase: You have unstaged changes`.
`git merge --ff-only origin/main` after a fetch (a) ignores the `pull.rebase`
config entirely, and (b) only refuses if an incoming commit would *overwrite*
a locally-modified file — unrelated unstaged changes ride along untouched and
stay unstaged on the new main. This is the **no-stash sibling** of the
stash-based recovery in the "Local cleanup failure" section above (that variant
is for when gh's own cleanup phase failed mid-way, or the dirty file *would*
conflict); for a plain post-merge sync, ff-only needs no stash. It also fails
loudly (non-fast-forward) if local main diverged — which is exactly what you
want to know.

4. **Close the loop on planned cleanup**: `git branch -d <pr-branch>` once no
   worktree holds it. Report every step from your announced plan as
   done-or-skipped in the wrap-up — silently dropping an announced cleanup step
   reads as a stall.

Discovered website PR #288 (2026-08-14): post-merge `git pull` balked at the
user's unstaged `opencode.json`; `git merge --ff-only origin/main` synced main
without touching it.

### Dependabot PRs — resolving lockfile conflicts via `@dependabot rebase`

Dependabot PRs frequently develop **merge conflicts in lockfiles** (`package-lock.json`, `pnpm-lock.yaml`, `uv.lock`, `pixi.lock`) when another dependabot PR lands first and shifts the base. You CANNOT resolve these by editing the lockfile yourself — dependabot owns the branch and must rebase it.

**Workflow:**
1. Confirm the conflict: `gh pr view <n> --json mergeable` → `CONFLICTING`.
2. Trigger a dependabot rebase by commenting `@dependabot rebase`:
   ```bash
   gh pr comment <n> --body "@dependabot rebase"
   ```
3. Poll for completion (~1-2 min). Status transitions:
   - `CONFLICTING` → `MERGEABLE` + checks `UNSTABLE` (rebased; CI re-running)
   - → `MERGEABLE` + checks green (ready to merge)
   ```bash
   gh pr view <n> --json mergeable
   gh pr checks <n>
   ```
4. Once green + `MERGEABLE`, merge via rebase (per [Merge policy](#merge-policy-prs)):
   ```bash
   gh pr merge <n> --rebase
   ```

**Do NOT** check out the dependabot branch and resolve the lockfile manually — dependabot will overwrite manual fixes on its next rebase. `@dependabot rebase` is the only correct trigger.

**Batching multiple dependabot PRs:** merge oldest→newest one at a time; each merge can re-conflict the next PR's lockfile, requiring a fresh `@dependabot rebase`. Poll/rebase each in turn rather than merging several then discovering cascading conflicts.

Discovered gym-coach (2026-07-28): 5 dependabot PRs merged; #19 (next 16.2.6→16.2.12) needed `@dependabot rebase` to clear a `package-lock.json` conflict left by #16's merge.

**Second use case — propagating a merged CI/workflow fix to open dependabot PRs:**
when a fix to a workflow (e.g. a permissions block that repairs a failing comment
step) lands on main, open dependabot PRs are still running CI against the OLD base.
Trigger a rebase onto the new main the same way:

1. Merge the fix PR to main.
2. Comment `@dependabot rebase` on each affected dependabot PR
   (`gh pr comment <n> --body "@dependabot rebase"`).
3. Confirm the rebase happened: the PR's head SHA CHANGES
   (`gh pr view <n> --json headRefOid`). Takes ~1–2 min.
4. THEN watch checks (see the `--watch` timing gotcha above — sleep first).

**Validation tip:** a same-repo PR that touches the workflow file is a live
validation of the fix — the repaired step runs with a proper token on same-repo
branches before any dependabot PR re-runs. (Note: yaml counts as code for
path-filter/"changes" gates, so the workflow job will run on such a PR.)
Discovered llamabot (2026-08-16): permissions fix merged as PR #393, propagated
to dependabot PRs #389/#391 via `@dependabot rebase`.

### Markdown bodies with backticks — use `--body-file`, not `--body`

PR and issue bodies are Markdown, full of backtick code spans (`` `import` ``,
`` `notebooks/03.py` ``, etc.). When you pass such a body via
`gh pr create --body "..."` or `gh pr edit --body "..."`, **backticks inside the
double-quoted string are interpreted as command substitution by zsh/bash** — they
get *executed*, not passed literally. The result is a silently mangled body:

- `--body "contained \`import\` and \`from ... import\` statements"` → the
  shell tries to *execute* `` `import` `` and `` `from ... import ...` ``.
  producing `command not found` errors on stderr and a body with the code spans
  **deleted** (e.g. "contained  and  statements").
- Filename spans like `` `03_tools_mcp_zotero.py` `` are executed as a command →
  `command not found: 03_tools_mcp_zotero.py`.
- The PR/issue is still **created** (the command succeeds overall), so you only
  discover the mangled body *afterward*, wasting a round-trip to inspect + fix it.

**The fix: write the body to a temp file and use `--body-file` (`-F`).**

```bash
# Create a PR with a Markdown body containing backticks
cat > /tmp/pr-body.md <<'EOF'
This PR cleans up `notebooks/03_tools_mcp_zotero.py`.

Removed `import` and `from llamabot import tool` lines from the
skeleton blocks. The `exN_header` cells no longer carry boilerplate.
EOF

gh pr create --title "Clean up notebook scaffolds" --body-file /tmp/pr-body.md
```

`--body-file` (`-F`) also works with `gh pr edit`, `gh issue create`, and
`gh issue comment` — any command that accepts `--body`.

**When to use `--body-file` vs `--body`:**
- Body contains **any** backtick, dollar-paren `$(...)`, or other shell
  metacharacter → `--body-file` (always safe).
- Body is plain prose with no backticks/special chars → `--body` is fine.
- In doubt → `--body-file`. It is never wrong.

**Default-first (recurrence 2026-08-26, learn-anything PR #81):** for ANY
multi-sentence PR body, go STRAIGHT to temp file + `--body-file` — do not
attempt inline `--body` with escaped quotes first. That session tried an
inline body with escaped quotes, the shell choked on the escapes, and the
temp-file route worked on the retry. Multi-sentence bodies essentially always
carry a quote, apostrophe, backtick, or paren, so the inline attempt is a
wasted failing turn, not a shortcut.

**Alternative (single quotes):** wrapping the body in single quotes
(`--body 'text with \`backticks\`'`) also prevents substitution, but breaks if
the body itself contains apostrophes/contractions ("don't", "it's") or single
quotes. The heredoc-to-file + `--body-file` pattern avoids this entirely and
handles arbitrarily complex Markdown.

Discovered build-deep-research-agent PR #41 (2026-07-12): the PR was created
successfully but the body's code spans were eaten by zsh command substitution,
requiring a follow-up `gh pr edit` to restore them.

### Creating a PR from a fork against the upstream repo (fork-and-contribute)

When you are working in a **fork** of an upstream project (e.g. `~/github/explainer` is a fork of `ramithuh/explainer`, `~/github/youtube-upload` is a fork of `tokland/youtube-upload`) and want to contribute a branch back to **upstream**, the naive `gh pr create --base main` **fails** with:

```
No commits between main and <your-branch>
```

because `main` resolves to **your fork's** `main` (the default remote), not upstream's. Your branch's commits are *ahead of upstream*, but your fork's `main` is already at or ahead of where your branch forks from, so there is nothing to diff against the fork's main.

**Workflow (fork-and-contribute):**

1. **Verify remotes first** — `git remote -v`. `origin` = your fork, `upstream` = the parent project.
   If `upstream` is missing:
   ```bash
   git remote add upstream https://github.com/<upstream-owner>/<upstream-repo>.git
   ```

2. **Push your branch to YOUR fork**:
   ```bash
   git push -u origin <branch>
   ```

3. **Open the PR against UPSTREAM**, explicitly:
   ```bash
   gh pr create \
     --base main \
     --head <your-github-user>:<branch> \
     --repo <upstream-owner>/<upstream-repo> \
     --title "..." \
     --body-file /tmp/body.md
   ```
   - `--repo <upstream-owner>/<upstream-repo>` is the key flag — it tells `gh` which repo the PR is filed against (the parent), disambiguating from your fork.
   - `--head <your-github-user>:<branch>` uses the cross-repo head syntax (`<user>:<branch>`) to name the source branch on your fork.

4. **Verify the PR is MERGEABLE against `upstream/main`** before declaring done:
   ```bash
   gh pr view <n> --json mergeable
   ```
   Must report `MERGEABLE` (not `CONFLICTING`). If it reports `CONFLICTING`, rebase onto `upstream/main` and force-push:
   ```bash
   git fetch upstream
   git rebase upstream/main
   git push --force-with-lease origin <branch>
   ```

**Diagnostic shortcut:** the error signature `No commits between main and <branch>` from `gh pr create` while inside a fork = the base resolved to the fork's own main, not upstream's. Reach for `--repo` + `--head <user>:<branch>` immediately; do **not** theorize about the branch being empty or the push having failed.

Recurring: first seen 2026-06-18 (`youtube-upload` modernization → `tokland/youtube-upload`), recurred 2026-07-19 (`explainer` keyboard-navigation PR #5 → `ramithuh/explainer`). Both sessions spent a turn diagnosing the wrong-base resolution before applying the explicit `--repo`/`--head` fix.

### GitHub Actions

**List workflow runs**:
```bash
# List recent runs
gh run list

# List runs for a specific workflow
gh run list --workflow "CI"

# List failed runs
gh run list --status failure
```

**View run details**:
```bash
gh run view 1234567890
```

**View run logs**:
```bash
# View all logs for a run
gh run view 1234567890 --log

# View logs for a specific job
gh run view 1234567890 --log --job "build"
```

**Download run logs**:
```bash
gh run download 1234567890
```

**Re-run a workflow**:
```bash
# Re-run failed jobs
gh run rerun 1234567890 --failed

# Re-run all jobs
gh run rerun 1234567890
```

**Watch a running workflow**:
```bash
gh run watch 1234567890
```


**Trigger a workflow manually**:
```bash
gh workflow run workflow-name.yml
```

### Bridging `gh workflow run` → `gh run watch` (the missing run-ID)

`gh workflow run <workflow>` dispatches a run and returns immediately — it does
**not** print the new run ID. `gh run watch <run-id>` **requires** a run ID
argument (or it prompts interactively, which fails in a non-interactive agent
CLI context). So the naive sequence:

```bash
gh workflow run deploy.yml -f app_dir=apps/foo
gh run watch --exit-status          # FAILS in non-interactive mode
```

will error out or hang waiting for interactive selection. **Always capture the
run ID after dispatching, then watch by ID:**

```bash
gh workflow run deploy.yml -f app_dir=apps/foo
sleep 3   # brief propagation delay before the run appears in `gh run list`
RUN_ID=$(gh run list --workflow deploy.yml --limit 1 \
  --json databaseId --jq ".[0].databaseId")
gh run watch "$RUN_ID" --exit-status
```

This applies to **any** `gh workflow run` → `gh run watch` sequence (deploy
workflows, release workflows, manual re-triggers). The run ID is the bridge —
without it the two commands cannot be chained non-interactively.

Discovered 2026-07-24 reviewing the ormoni-omni deploy-slackbot SKILL.md Phase C,
which documented the bare `gh run watch --exit-status` without a run ID.

### Issues

**Create an issue**:
```bash
gh issue create --title "Bug: Something broken" --body "Description here"
```

**List issues**:
```bash
# List open issues
gh issue list

# List your issues
gh issue list --assignee @me

# List issues with a label
gh issue list --label bug
```

**View an issue**:
```bash
gh issue view 456
```

**Comment on an issue**:
```bash
gh issue comment 456 --body "Thanks for reporting this!"
```

**Close/reopen an issue**:
```bash
gh issue close 456
gh issue reopen 456
```

### GitHub Projects (`gh project`) — board fields and item automation

Working with GitHub Projects v2 boards (e.g. the learn-anything CoS board
sync). All value-setting goes through `item-edit` and needs THREE ids:
project id, item id, field id.

**Discover ids:**

- Project id: `gh project list --owner <owner> --format json` (`PVT_...`)
- Item id: `gh project item-add <num> --owner <owner> --url <issue-url> --format json | jq -r .id` (returns the new item id directly)
- Field/option ids: `gh project field-list <num> --owner <owner> --format json`

**Create a single-select field — the flag is PLURAL and comma-separated:**

```bash
gh project field-create <num> --owner <owner> --name "Section" \
  --data-type SINGLE_SELECT \
  --single-select-options "Venue,Legal,Insurance,Planning"
```

A non-plural form of the flag fails. Bonus: `field-create --format json`
returns the field id AND every option id in one shot, so a separate
`field-list` is unneeded right after creation.

**Set field values on an item (`gh project item-edit`):**

- Date field: `gh project item-edit --project-id <PVT_id> --id <item-id> --field-id <field-id> --date "2026-08-15"`
- Single-select field: same shape but `--single-select-option-id <option-id>`
- Text/number fields: `--text` / `--number`

**Verify board state — `item-list` flattens Status to a top-level key:**

```bash
gh project item-list <num> --owner <owner> --limit 100 --format json \
  | jq -r '[.items[] | .status] | group_by(.) | map({status: .[0], n: length})'
```

Status is NOT under `fieldValues`/`fieldValuesByName`; when jq prints `?`/null
for a status, suspect the **jq path**, not the edit.

**Batching:** `item-edit` calls chained in a sequential bash loop are fine
(~1s each; 48 calls fits a 120s timeout). Batch issue **creation** in small
sequential groups (~4) instead of parallel `gh issue create` calls — GitHub
secondary rate limits trigger on rapid issue creation.

Discovered during the learn-anything CoS board sync (2026-08-15, board
`ericmjl/projects/3`): `field-create` flag trial-and-error plus option-id
plumbing cost several probing turns.

**Archive/close a whole board — no `gh project archive` exists; use `updateProjectV2` with `closed: true`:**

Projects v2 have NO separate archive command or mutation — the GraphQL archive
mechanism is a Boolean field on the update input:

```bash
gh api graphql -f query='mutation($id: ID!) { updateProjectV2(input: {projectId: $id, closed: true}) { projectV2 { id closed } } }' -f id='PVT_...'
```

The board then moves to the **Closed projects** filter
(`github.com/users/<owner>/projects?query=is%3Aclosed`, or
`/orgs/<owner>/projects?...`). Reopen with `closed: false`. Discoverable by
introspecting `UpdateProjectV2Input` (its fields include `closed: Boolean`).

Do NOT label board archiving a "manual human step" in a wrap-up — one mutation
does it. Discovered 2026-08-16 archiving `ericmjl/projects/3` after the
learn-anything board migration to `nll-ai/projects/1`; the prior session's
wrap-up had mislabeled it manual.

### `gh api graphql`: `-F` reads `@file` values, `-f` does not

Passing a GraphQL query from a file with `-f query=@query.graphql` **fails**:
`-f/--raw-field` adds the value as a **literal string with no `@` expansion**, so
GitHub receives the literal text `@query.graphql` as the query and returns the
parse error:

```
Expected one of SCHEMA, SCALAR, TYPE, ENUM, INPUT, UNION, INTERFACE, actual: DIR_SIGN ("@") at [1, 1]
```

The error names a GraphQL parse location, which misleads you into debating
GraphQL syntax or flag semantics — it is purely the un-expanded `@`.

**Fix (verified live 2026-08-16 against `gh api graphql` on this machine):**

```bash
gh api graphql -F query=@query.graphql          # -F/--field reads @-prefixed values from a file ("-" = stdin)
gh api graphql -f query="$(cat query.graphql)"  # alternative without -F
```

**Rule:** `@`-file expansion exists ONLY on `-F` (typed fields — `gh api --help`
documents `@<path>` on the `-F` line and nothing on the `-f` line). Applies to
ANY `gh api` value loaded from a file, not just GraphQL queries.

### Verifying a GitHub Projects board copy (read-only diff)

When a Projects v2 board is cloned/migrated (old project id → new `PVT_...` id),
verify with a **read-only diff script** instead of eyeballing `item-list` output.
Procedure (learn-anything CoS board migration, 2026-08-16):

1. Fetch BOTH boards via `gh api graphql -F query=@query.graphql` (see the `-F`
   section above): items with issue number/title/state + `fieldValues` nodes
   (single-select option name, dates, text), plus project `fields` with
   name/dataType and single-select options incl. option ids.
2. Run 7 checks: (a) item sets by issue number, (b) word-for-word titles,
   (c) item state, (d) field values per item (Status/Start/End/Section),
   (e) field definitions — names, dataTypes, option names+colors, option ids,
   (f) non-Issue items (drafts), (g) ops-doc recorded ids vs the live new board.
3. Parse the ops-doc id table (regex over the markdown rows) **inside** the
   comparison script — never transcribe ids by hand.

Two diff-script gotchas from that session:

- A reported MISMATCH where one side shows `doc=None` is almost always **your
  lookup-key bug**, not missing data: doc rows were labeled `Start field id
  (DATE)` while the lookup key was `Start field id`, so `dict.get` silently
  returned `None`. Use **prefix matching** for doc row labels. `None` on either
  side of a comparison = the comparison itself is broken; diagnose the parse
  before reporting a data mismatch.
- An old==new equivalence check can pass when BOTH boards are identically
  wrong; also pin the expected option sets (doc option names mapped to live
  option ids) so a doubly-wrong copy still fails.


### Repository operations

**Clone a repository**:
```bash
gh repo clone owner/repo
```

**Create a repository**:
```bash
# Create public repo
gh repo create my-repo --public

# Create private repo with README
gh repo create my-repo --private --add-readme
```

**View repository info**:
```bash
gh repo view owner/repo
```

**Fork a repository**:
```bash
gh repo fork owner/repo --clone
```

**Set default branch**:
```bash
gh repo set-default owner/repo
```

### Status and monitoring

**Check CI status**:
```bash
# View checks for current branch
gh pr checks

# View checks for a specific PR
gh pr checks 123
```

#### `gh pr checks --watch` fails when no checks exist yet — sleep before watching

**Trigger:** running `gh pr checks <n> --watch` immediately after an event that hasn't
produced check runs yet — right after `gh pr create`, or right after commenting
`@dependabot rebase` (the rebase + CI re-run takes 1–2 min to start). `--watch`
**errors out** ("no checks reported yet" / non-zero exit) instead of waiting when
zero checks exist, which looks like a PR failure rather than a timing gap.

**Fix:** sleep 60–90s first, then watch; or poll the precondition before watching:

```bash
sleep 90
gh pr checks 389 --watch --fail-fast   # checks now exist; watch works
```

For dependabot rebases specifically, the rebase is confirmed when the PR's head
SHA CHANGES (`gh pr view <n> --json headRefOid`) — poll that first, then watch.
Discovered llamabot PRs #389/#391 (2026-08-16).

**Programmatically check "is CI green?"** — `gh pr checks` DOES support `--json`
(verify with `gh pr checks --help` before assuming otherwise). Crucially, the JSON
output adds a **`bucket`** field that categorizes each check's `state` into one of
`pass`, `fail`, `pending`, `skipping`, or `cancel`. This is the canonical way to
determine CI-green status in a script/agent — do NOT parse the text table, which
**truncates at ~40 lines** and hides checks beyond the cutoff.

```bash
# List any check that is NOT pass/skipping. Empty output = CI is green.
gh pr checks --json name,bucket \
  --jq '.[] | select(.bucket != "pass" and .bucket != "skipping") | .name'
```

- **`skipping`** is EXPECTED and benign: it means a job gated on a specific event
  (e.g. `Upload to PyPI on release`, `Upload wheel to GitHub Release`) correctly
  skipped because this is a PR/push, not a release. Treat `pass` + `skipping` as
  green; only `fail`, `pending`, or `cancel` blocks a merge.
- **Exit code 8** = checks still pending (useful in a `gh pr merge --auto` gate).
- The full set of JSON fields: `bucket, completedAt, description, event, link,
  name, startedAt, state, workflow`.

**Pitfall:** a prior session asserted "`gh pr checks` doesn't support `--json`"
without checking `--help`, then spent several turns parsing truncated text output.
Always run `<cmd> --help` to verify a flag is genuinely unsupported before falling
back to an inferior text-parsing path.

**View your notifications**:
```bash
gh notify
```

### Advanced usage

**Use with specific repository**:
```bash
gh pr list --repo owner/repo
```

**Output as JSON for scripting**:
```bash
gh pr list --json number,title,author,state
```

**Use custom queries**:
```bash
# Search for PRs with label
gh pr list --label "needs-review"

# Search for issues assigned to you
gh issue list --assignee @me --state open
```

## Tips

**Check command help**: Add `--help` to any command to see all options:
```bash
gh pr create --help
```

**Interactive mode**: Many commands support interactive prompts when you don't provide required flags:
```bash
gh pr create  # Will prompt for title, body, etc.
```

**Aliases**: Create custom aliases for frequently used commands:
```bash
gh alias set prc 'pr create --fill'
```

**Default repository**: Run `gh repo set-default` in a repo to avoid specifying `--repo` flag.

## Common workflows

**Creating a PR from current branch**:
```bash
git push -u origin feature-branch
gh pr create --fill
```

**Checking why a PR failed**:
```bash
gh pr checks 123
gh run view <run-id> --log
```

**Quick PR review workflow**:
```bash
gh pr list
gh pr view 123
gh pr checkout 123
# Make local tests/review
gh pr review 123 --approve
```

**Monitoring a deployment**:
```bash
gh run list --workflow "Deploy"
gh run watch <latest-run-id>
```
