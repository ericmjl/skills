---
name: gh-activity-summary
description: >-
  Generate a plain-language activity report of your GitHub work for a date
  range or a single day, including commits, pull requests, reviews, issues,
  comments, and a chronological event timeline. Use this when you need to
  summarize what you've accomplished on GitHub for status updates,
  retrospectives, reviewing what happened on a specific date, or tracking
  your work.
license: MIT
---

# GitHub activity report

This skill generates a markdown-friendly report of your GitHub activity over a date range using the `gh` CLI.

## Usage

Run the bundled script with optional `START_DATE` and `END_DATE` (format: `YYYY-MM-DD`).

```bash
# Default: last 7 days
bash skills/gh-activity-summary/activity-report.sh

# Specific range
bash skills/gh-activity-summary/activity-report.sh 2026-01-01 2026-01-07
```

## Requirements

- `gh` (GitHub CLI) - must be authenticated (`gh auth login`)
- `jq` - used for JSON counting and formatting

## What It Does

- Lists commits you authored in the date range.
- Lists pull requests you created and merged.
- Lists pull requests you reviewed.
- Lists issues you created.
- Prints simple summary counts for quick status updates.

## How It Works

- Uses `gh search` to query commits, PRs, and issues scoped to `@me`.
- Uses platform-aware date defaults (macOS vs Linux) when you omit dates.
- Formats output as readable markdown so you can paste it into status updates or pipe it into an LLM for summarization.

To generate a short natural-language summary, you can pipe the report into your preferred model:

```bash
bash skills/gh-activity-summary/activity-report.sh 2026-01-01 2026-01-07 | claude "Summarize this in 2-3 sentences"
```

## Daily timeline view

For a single specific day (commits grouped by repo and branch, issue
interactions, and a chronological event timeline), use the timeline script:

```bash
# Today
bash skills/gh-activity-summary/gh-activity.sh

# A specific date (YYYY-MM-DD)
bash skills/gh-activity-summary/gh-activity.sh 2025-12-15
```

Where `activity-report.sh` aggregates a range via `gh search` (best
for "what did I do this week"), `gh-activity.sh` replays the GitHub
events API for one day (best for "what happened on the 15th",
including pushes, PR comments, and issue activity in order).

Consolidated 2026-09-27: absorbs gh-daily-timeline (deleted; its
script and docs live here).
