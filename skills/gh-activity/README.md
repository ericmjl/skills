# GitHub activity reporter

This skill reports your GitHub activity for a specific day using the `gh` CLI. It defaults to today's date if you don't specify one.

## What it does

The skill fetches your GitHub events and presents them in an organized format with three main sections:

**Commits summary**: Lists all commits you made with their actual commit messages, grouped by repository and branch.

**Issues summary**: Shows all issues you created, commented on, or interacted with, including issue titles and the type of interaction.

**Activity timeline**: A chronological view of all your GitHub events for the day (pushes, PRs, issue comments, etc.).

## Requirements

You'll need these tools installed:

- `gh` (GitHub CLI) - authenticated with your GitHub account
- `jq` - for JSON processing

## Usage

Get today's activity:

```bash
/gh-activity
```

Get activity for a specific date:

```bash
/gh-activity 2025-12-15
```

The date format must be `YYYY-MM-DD`.

## How it works

The skill performs these steps:

1. Verifies you're authenticated with GitHub CLI
2. Fetches your events using `gh api /users/{username}/events`
3. Filters events to the specified date
4. For each push event, fetches the actual commits using `gh api /repos/{repo}/compare/{before}...{head}`
5. Extracts and displays issue information from issue events
6. Formats everything into a clear, organized report

The beauty of this approach is that it uses the GitHub CLI directly without any Python dependencies. Just bash, `gh`, and `jq` working together to give you a complete picture of your day's work.

## Authentication check

The skill automatically checks which GitHub account you're authenticated as and confirms this before fetching activity. This helps prevent confusion if you have multiple GitHub accounts or need to verify you're looking at the right user's activity.
