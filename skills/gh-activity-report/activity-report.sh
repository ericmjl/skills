#!/usr/bin/env bash

set -euo pipefail

OSTYPE_VALUE="${OSTYPE:-}"

if [[ "$OSTYPE_VALUE" == darwin* ]]; then
    DEFAULT_START_DATE="$(date -v-7d +%Y-%m-%d)"
    DEFAULT_END_DATE="$(date +%Y-%m-%d)"
else
    DEFAULT_START_DATE="$(date -d "7 days ago" +%Y-%m-%d)"
    DEFAULT_END_DATE="$(date +%Y-%m-%d)"
fi

START_DATE="${1:-$DEFAULT_START_DATE}"
END_DATE="${2:-$DEFAULT_END_DATE}"

DATE_REGEX='^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
if [[ ! "$START_DATE" =~ $DATE_REGEX ]]; then
    echo "Error: START_DATE must be YYYY-MM-DD (got '$START_DATE')" >&2
    exit 1
fi
if [[ ! "$END_DATE" =~ $DATE_REGEX ]]; then
    echo "Error: END_DATE must be YYYY-MM-DD (got '$END_DATE')" >&2
    exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
    echo "Error: gh CLI is not installed or not in PATH" >&2
    echo "Install from: https://cli.github.com/" >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is not installed or not in PATH" >&2
    echo "Install jq to use this skill." >&2
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "Error: Not authenticated with GitHub CLI" >&2
    echo "Run: gh auth login" >&2
    exit 1
fi

echo "GitHub Activity Report"
echo "======================"
echo "Date Range: $START_DATE to $END_DATE"
echo ""

echo "## Commits"
echo "----------"
gh search commits \
    --author=@me \
    --committer-date="$START_DATE..$END_DATE" \
    --limit 100 \
    --json repository,commit \
    --jq '.[] | "- [\(.repository.nameWithOwner)] \(.commit.message | split("\n")[0])"' \
    2>/dev/null || echo "No commits found"

echo ""
echo "## Pull Requests Created"
echo "------------------------"
gh search prs \
    --author=@me \
    --created="$START_DATE..$END_DATE" \
    --limit 100 \
    --json title,repository,state,url \
    --jq '.[] | "- [\(.state)] \(.title) (\(.repository.nameWithOwner))\n  \(.url)"' \
    2>/dev/null || echo "No PRs created"

echo ""
echo "## Pull Requests Merged"
echo "-----------------------"
gh search prs \
    --author=@me \
    --merged="$START_DATE..$END_DATE" \
    --limit 100 \
    --json title,repository,url \
    --jq '.[] | "- \(.title) (\(.repository.nameWithOwner))\n  \(.url)"' \
    2>/dev/null || echo "No PRs merged"

echo ""
echo "## Code Reviews"
echo "---------------"
gh search prs \
    --reviewed-by=@me \
    --created="$START_DATE..$END_DATE" \
    --limit 100 \
    --json title,repository,url \
    --jq '.[] | "- Reviewed: \(.title) (\(.repository.nameWithOwner))\n  \(.url)"' \
    2>/dev/null || echo "No reviews performed"

echo ""
echo "## Issues Created"
echo "-----------------"
gh search issues \
    --author=@me \
    --created="$START_DATE..$END_DATE" \
    --limit 100 \
    --json title,repository,state,url \
    --jq '.[] | "- [\(.state)] \(.title) (\(.repository.nameWithOwner))\n  \(.url)"' \
    2>/dev/null || echo "No issues created"

echo ""
echo "## Summary Statistics"
echo "---------------------"

COMMITS_COUNT="$(gh search commits --author=@me --committer-date="$START_DATE..$END_DATE" --limit 100 --json sha 2>/dev/null | jq 'length' || echo 0)"
PRS_CREATED_COUNT="$(gh search prs --author=@me --created="$START_DATE..$END_DATE" --limit 100 --json number 2>/dev/null | jq 'length' || echo 0)"
PRS_MERGED_COUNT="$(gh search prs --author=@me --merged="$START_DATE..$END_DATE" --limit 100 --json number 2>/dev/null | jq 'length' || echo 0)"
REVIEWS_COUNT="$(gh search prs --reviewed-by=@me --created="$START_DATE..$END_DATE" --limit 100 --json number 2>/dev/null | jq 'length' || echo 0)"
ISSUES_COUNT="$(gh search issues --author=@me --created="$START_DATE..$END_DATE" --limit 100 --json number 2>/dev/null | jq 'length' || echo 0)"

echo "- $COMMITS_COUNT commits"
echo "- $PRS_CREATED_COUNT PRs created"
echo "- $PRS_MERGED_COUNT PRs merged"
echo "- $REVIEWS_COUNT PRs reviewed"
echo "- $ISSUES_COUNT issues created"

echo ""
echo "---"
echo "Report generated: $(date)"
