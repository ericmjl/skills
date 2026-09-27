#!/usr/bin/env bash
set -euo pipefail

# GitHub Activity Reporter
# Reports your GitHub activity for a specified day using the gh CLI

# Get the date parameter (default to today)
DATE="${1:-$(date +%Y-%m-%d)}"

# Validate date format (YYYY-MM-DD)
if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Error: Date must be in YYYY-MM-DD format" >&2
    echo "Example: 2025-12-20" >&2
    exit 1
fi

# Get authenticated user
echo "Checking GitHub authentication..." >&2
USERNAME=$(gh api user --jq .login)

if [ -z "$USERNAME" ]; then
    echo "Error: Not authenticated with GitHub CLI" >&2
    echo "Run: gh auth login" >&2
    exit 1
fi

echo "Authenticated as: $USERNAME" >&2
echo "" >&2

# Fetch user events
echo "Fetching activity for $USERNAME on $DATE..." >&2
echo "" >&2

# Get events and filter by date
EVENTS_JSON=$(gh api "/users/$USERNAME/events" --paginate | jq --arg date "$DATE" '
  map(select(.created_at | startswith($date)))
')

# Print header
echo "=== GitHub Activity Report ==="
echo "User: $USERNAME"
echo "Date: $DATE"
echo ""

# Get summary stats
TOTAL_EVENTS=$(echo "$EVENTS_JSON" | jq 'length')
TOTAL_REPOS=$(echo "$EVENTS_JSON" | jq '[.[] | .repo.name] | unique | length')

echo "Total events: $TOTAL_EVENTS"
echo "Repositories: $TOTAL_REPOS"
echo ""

# Extract and display commits
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "COMMITS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PUSH_EVENTS=$(echo "$EVENTS_JSON" | jq -c '.[] | select(.type == "PushEvent")')

if [ -z "$PUSH_EVENTS" ]; then
    echo "No commits found for this date."
else
    COMMIT_COUNT=0
    while IFS= read -r event; do
        REPO=$(echo "$event" | jq -r '.repo.name')
        BEFORE=$(echo "$event" | jq -r '.payload.before')
        HEAD=$(echo "$event" | jq -r '.payload.head')
        REF=$(echo "$event" | jq -r '.payload.ref' | sed 's|refs/heads/||')

        # Fetch commits for this push
        COMMITS=$(gh api "/repos/$REPO/compare/$BEFORE...$HEAD" --jq '.commits[] | "  • \(.commit.message | split("\n")[0])"' 2>/dev/null || echo "")

        if [ -n "$COMMITS" ]; then
            echo "[$REPO] ($REF)"
            echo "$COMMITS"
            COMMIT_COUNT=$((COMMIT_COUNT + $(echo "$COMMITS" | wc -l | tr -d ' ')))
            echo ""
        fi
    done <<< "$PUSH_EVENTS"

    echo "Total commits: $COMMIT_COUNT"
fi

echo ""

# Extract and display issues
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ISSUES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ISSUE_EVENTS=$(echo "$EVENTS_JSON" | jq -c '.[] | select(.type == "IssuesEvent" or .type == "IssueCommentEvent")')

if [ -z "$ISSUE_EVENTS" ]; then
    echo "No issue activity found for this date."
else
    # Group by issue number and display
    echo "$ISSUE_EVENTS" | jq -r '
        .payload.issue.number as $num |
        .payload.issue.title as $title |
        .repo.name as $repo |
        .type as $type |
        .payload.action as $action |
        "\($num)|\($title)|\($repo)|\($type)|\($action)"
    ' | sort -t'|' -k1 -u | while IFS='|' read -r num title repo type action; do
        echo "Issue #$num: $title"
        echo "  Repository: $repo"

        # Get all actions for this issue
        echo "$ISSUE_EVENTS" | jq -r --arg num "$num" '
            select(.payload.issue.number == ($num | tonumber)) |
            if .type == "IssuesEvent" then
                "  • \(.payload.action | ascii_upcase) the issue"
            elif .type == "IssueCommentEvent" then
                "  • Added comment"
            else
                empty
            end
        '
        echo ""
    done
fi

echo ""

# Detailed activity timeline
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ACTIVITY TIMELINE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "$EVENTS_JSON" | jq -r '
  group_by(.repo.name) |
  .[] |
  "[\(.[0].repo.name)]",
  (
    .[] |
    "  [\(.created_at | sub("^.*T"; "") | sub("Z$"; ""))] \(.type | sub("Event$"; "")): \(
      if .type == "PushEvent" then
        (.payload.ref | sub("refs/heads/"; "")) + " branch"
      elif .type == "PullRequestEvent" then
        "\(.payload.action) PR #\(.payload.pull_request.number): \(.payload.pull_request.title)"
      elif .type == "IssueCommentEvent" then
        "\(.payload.action) comment on #\(.payload.issue.number)"
      elif .type == "IssuesEvent" then
        "\(.payload.action) issue #\(.payload.issue.number)"
      elif .type == "CreateEvent" then
        "created \(.payload.ref_type)"
      elif .type == "DeleteEvent" then
        "deleted \(.payload.ref_type)"
      elif .type == "WatchEvent" then
        "starred repository"
      elif .type == "ForkEvent" then
        "forked repository"
      elif .type == "PullRequestReviewEvent" then
        "\(.payload.action) review on PR #\(.payload.pull_request.number)"
      else
        ""
      end
    )"
  ),
  ""
'
