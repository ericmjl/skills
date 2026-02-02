---
name: gh-pr-code-review
description: PR code review workflow: pull diff, two-pass findings, draft and prioritize comments, then optionally post via gh api.
license: MIT
---

# PR code review (gh)

This skill guides a repeatable pull request review workflow using the GitHub CLI.

It emphasizes two-pass review (to find more issues), drafting comments before
posting, and posting only after explicit user confirmation.

## Usage

Use this skill when the user asks you to review a pull request and leave
actionable feedback.

Inputs you should accept:

- PR number, PR URL, or branch name accepted by `gh pr view` / `gh pr diff`
- Optional repo override via `-R owner/repo` if not in a git checkout

## Requirements

- `gh` authenticated (`gh auth status`)
- Permission to comment on the PR
- Optional but useful: `jq`

## What it does

A code review in two passes, then a drafting and posting phase:

A) Pull down the PR diff and identify issues

B) Repeat the review, finding only new issues

C) Draft review comments but do not post yet

D) Prioritize comments by criticality:

- `critical`: correctness/security/data loss/broken API/test failures
- `optional`: maintainability/performance/edge cases/docs/test gaps
- `trivial`: nits/style/micro-optimizations (do not show by default)

E) Show only critical and optional items to the user. Then, if (and only if)
   the user explicitly confirms, post:

- inline (line-level) review comments where anchoring is unambiguous
- a single summary timeline comment containing only critical + optional items

## How it works

### 0) Gather PR context

1. Identify the PR. Prefer a PR number or URL.
2. Fetch PR metadata (including the head commit SHA):

```bash
gh pr view <PR> --json number,title,url,baseRefName,headRefName,headRefOid,files,additions,deletions
```

1. Fetch the diff (the primary review artifact):

```bash
gh pr diff <PR> --color=never
```

Optional: check CI signal while reviewing:

```bash
gh pr checks <PR>
```

### 1) Stage A: first-pass review

Review the diff and record issues as structured items. For each issue capture:

- `severity`: `critical` | `optional` | `trivial`
- `path`: file path when applicable
- `side`: `RIGHT` (new code / additions / context) or `LEFT` (deletions)
- `line`: line number in the diff blob when you can anchor reliably
- `body`: the draft comment text (short, actionable)

Focus this pass primarily on:

- correctness and logic errors
- security risks
- API breaks
- data loss / irreversible behavior
- missing or failing tests

### 2) Stage B: second-pass review (new issues only)

Re-review the same diff from scratch with a different lens:

- edge cases
- performance and algorithmic complexity
- naming, clarity, ergonomics
- documentation and user-facing behavior
- consistency with project conventions

Critical rule: do not repeat issues from stage A. Only append genuinely new issues.

### 3) Stage C: draft comments (do not post)

Convert each issue into a comment draft that is ready to paste/post:

- one idea per comment
- include why it matters and a concrete suggestion
- avoid bikeshedding; keep tone constructive

### 4) Stage D: prioritize

Assign each comment a criticality:

- `critical`: must-fix
- `optional`: should-fix
- `trivial`: nice-to-fix

### 5) Stage E: show only critical + optional, then optionally post

1. Show the user only critical + optional comments.
2. Ask for explicit confirmation before posting:

"Post these to the PR now? (yes/no)"

1. If user says yes:

- Post inline comments for items with reliable `path` + `line` + `side`.
- Post one summary timeline comment that includes all critical + optional items.
- Do not post trivial items.

## Posting comments with gh

### Summary timeline comment (PR is an issue)

Use the Issues API to post one summary comment:

```bash
gh api -X POST "repos/{owner}/{repo}/issues/<PR_NUMBER>/comments" \
  -f body="<summary markdown>"
```

Endpoint reference: `POST /repos/{owner}/{repo}/issues/{issue_number}/comments`.

### Inline (line-level) review comments

Use the Pull Request Review Comments API:

```bash
SHA="$(gh pr view <PR> --json headRefOid -q .headRefOid)"

gh api -X POST "repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments" \
  -f body="<comment markdown>" \
  -f commit_id="$SHA" \
  -f path="path/to/file.py" \
  -F line=42 \
  -f side=RIGHT
```

Endpoint reference: `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments`.

### Mapping a unified diff to (path, line, side)

Inline comments require an exact file `path`, a `line` number, and a `side`.

Use this deterministic approach for unified diffs:

- Each hunk header looks like `@@ -old_start,old_count +new_start,new_count @@`.
- Initialize counters: `old_line = old_start`, `new_line = new_start`.
- Walk each subsequent hunk line:

  - If the line starts with `' '` (context): increment both `old_line` and `new_line`.
  - If the line starts with `'+'` (addition): increment `new_line` only.
  - If the line starts with `'-'` (deletion): increment `old_line` only.

- To comment on the new code, use `side=RIGHT` and set `line=new_line`.
- To comment on a deletion, use `side=LEFT` and set `line=old_line`.

If you cannot reliably determine `line`/`side` (for example, complex hunks or
uncertainty), do not post an inline comment. Include the item only in the
summary timeline comment.
