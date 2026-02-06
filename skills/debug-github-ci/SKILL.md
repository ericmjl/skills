---
name: debug-github-ci
description: Debug GitHub Actions and CI failures using gh CLI: watch PR checks, fetch run logs, analyze failures, reproduce locally, and suggest fixes. Use when CI fails, when the user wants to watch or verify CI, or when debugging workflow runs.
license: MIT
---

# Debug GitHub CI

This skill guides systematic debugging of GitHub Actions (and other CI) failures and gives a clear way to "pay attention to CI" using the GitHub CLI.

## Usage

Use this skill when:

- A GitHub Actions (or other CI) workflow has failed and the user wants to fix it
- The user says they want to "watch CI," "make sure CI passes," or "pay attention to checks"
- The user shares a workflow run URL or asks to debug a failed run

Inputs: the user may give **a link to a failing job/run** or **a link to the PR**. Also accepted: PR number, branch name, or run ID. Repo can be overridden with `-R owner/repo` when not in a git checkout.

## Requirements

- GitHub CLI (`gh`) installed and authenticated (`gh auth status`)
- Optional: `act` for running workflows locally (`brew install act`)

## What It Does

1. **Watch CI** — When the user wants to pay attention to CI, run `gh pr checks --watch` so status updates in the terminal.
2. **Inspect failures** — Fetch run metadata and logs for failed jobs.
3. **Analyze** — Identify failed job(s), step, and root cause (deps, permissions, timeouts, etc.).
4. **Reproduce** — Checkout the same commit, run the same commands (or use `act`), compare with CI.
5. **Fix** — Suggest concrete changes, commands, and preventive steps.

## How It Works

### 1. Watching CI (paying attention to checks)

When the user wants to ensure CI is working or to monitor checks (e.g. after pushing or opening a PR), run:

```bash
gh pr checks --watch --interval 5
```

Run from the repo root. If the current branch is not a PR branch, use:

```bash
gh pr checks <PR> --watch --interval 5
```

Tell the user you're watching CI so they know checks will be monitored. `--interval` is in seconds (default 10). Optional: `--fail-fast` to exit watch as soon as any check fails.

### 2. Handling the user's link

#### User gives a link to a failing job or run

- URLs look like: `.../actions/runs/<run-id>` or `.../actions/runs/<run-id>/jobs/<job-id>`
- Parse the URL to get `run-id` (and `job-id` if present)
- Use them directly:

```bash
gh run view <run-id> -R owner/repo
gh run view <run-id> --log-failed -R owner/repo
```

- To fetch logs for one specific job:

```bash
gh run view <run-id> --job <job-id> --log -R owner/repo
```

- Omit `-R owner/repo` when already in that repo.

#### User gives a link to the PR

- URL looks like: `.../pull/<number>` (e.g. `.../pull/42`)
- Get the PR's head commit, then list runs for that commit to find the failed run:

```bash
gh pr view <PR> -R owner/repo --json headRefOid -q .headRefOid
gh run list --commit <sha> -R owner/repo
```

- Optionally filter to failed runs only: `gh run list --commit <sha> --status failure -R owner/repo`. Note the run ID from the output (first column), then fetch logs as below.
- Then fetch logs as above: `gh run view <run-id> --log-failed`
- To watch checks for this PR: `gh pr checks <PR> --watch --interval 5`

### 3. Extracting workflow information

From the run (and URL), identify: repository owner/name, run ID, workflow name, branch or commit that triggered the run.

### 4. Fetching logs with GitHub CLI

```bash
gh run list --limit 20
gh run view <run-id>
gh run view <run-id> --log
gh run view <run-id> --log-failed
```

Use `--log-failed` to focus on failed job logs first.

### 5. Analyzing the failure

- Which job(s) failed and at which step
- Error messages, exit codes, stack traces
- Common causes: dependency/version issues, permissions, timeouts, resource limits, env differences
- Relevant workflow YAML (`.github/workflows/*.yaml`) and environment setup

### 6. Reproducing locally

- Checkout the same commit or branch: `git checkout <commit-sha>` or `git checkout <branch>`
- Read the workflow file to see exact commands and environment
- Run the same sequence locally (e.g. same install and test commands: `pixi install`, `pixi run test`, `npm ci && npm test`)
- Match environment versions (Python, Node, etc.) if specified in the workflow
- Optionally use `act` for closer parity:
  - `act -j <job-name>` or `act` to run jobs locally
  - Note: `act` may not support every action or secret
- Compare local vs CI output and note any environment differences

### 7. Providing fixes and follow-up

- Explain what went wrong in plain terms
- Suggest specific fixes: config changes, dependency updates, workflow edits
- Give exact commands or code snippets where helpful
- Recommend next steps (re-run, re-push, add checks) and how to avoid similar failures
- Tailor advice to the project (e.g. Python/pixi vs Node/npm)

## Quick reference

<!-- markdownlint-disable MD060 -->
| Goal                  | Command                                                               |
|-----------------------|-----------------------------------------------------------------------|
| User gave job/run URL | Parse run-id from URL → `gh run view <run-id> --log-failed`           |
| User gave PR URL      | `gh pr view <PR> --json headRefOid -q .headRefOid`<br>`gh run list -c <sha> -s failure` |
| Watch PR checks       | `gh pr checks --watch --interval 5`                                   |
| Run summary           | `gh run view <run-id>`                                                |
| Full logs             | `gh run view <run-id> --log`                                          |
| Failed job logs only  | `gh run view <run-id> --log-failed`                                   |
| Single job log        | `gh run view <run-id> --job <job-id> --log`                           |
<!-- markdownlint-enable MD060 -->

Focus on actionable, specific solutions. When the user wants to "pay attention to CI," start with `gh pr checks --watch --interval 5` and then continue with the rest of the workflow as needed.
