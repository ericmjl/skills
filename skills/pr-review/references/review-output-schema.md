# Review output schema

Fill this after both passes. Map every finding onto the existing
`critical` / `optional` / `trivial` grades. Show only critical and optional.
Default cap: about **six** shown findings. An empty findings list is fine.

Do not put line numbers in `issue_content`.

## Per finding

| Field | Required | Notes |
| --- | --- | --- |
| `relevant_file` | yes | Full path in the PR |
| `issue_header` | yes | Two-word title, e.g. `Possible Bug` |
| `issue_content` | yes | Why it matters, plus the realistic trigger |
| `start_line` / `end_line` | yes | In the new file for additions; old file for deletions |
| `existing_code` / `improved_code` | no | Together, and only when a fix is ≤10 lines. `existing_code` is the exact new-file text from `start_line`–`end_line` (no `+`/`-`, no line-number prefix). `improved_code` is the full replacement with the same indent |
| `confidence` | no | Integer 0–10 |

Confidence bands, when you include the field:

- **9–10**: visible in the diff; trigger is concrete
- **7–8**: very likely; only reasonable assumptions about code outside the hunk
- **5–6**: plausible, not verified from the diff
- **0–4**: guesswork — treat as `trivial` or drop

Also keep the posting anchors from SKILL.md: `severity`, `path`, `side`,
`line`, `body`.

### Severity mapping

- `critical`: bug, security issue, data loss, broken API, or a test that
  fails because of this PR. Use `changes_required` if any shown finding is
  critical.
- `optional`: a real maintainability, performance, edge-case, missing-test,
  or unmet-ticket issue that should be fixed but is not a merge blocker on
  its own.
- `trivial`: nits and style. Usually the flagging rules already forbid
  these; if one slips through, do not show or post it.

A finding with confidence 5–6 is `optional` at most, unless it is a
named security issue with a concrete trigger.

## Fields that describe the whole review

| Field | Values |
| --- | --- |
| `estimated_effort_to_review` | 1 (short) … 5 (long and hard) |
| `security_concerns` | the exact word `No`, or a short header then explanation (`Sensitive information exposure: …`, `SQL injection: …`) |
| `relevant_tests` | `Yes` or `No` — whether this PR added or updated tests that cover the change |
| `ticket_compliance` | `met` / `not met` / `needs human verification` (or skip if no ticket). Verification is for UI checks and anything the diff cannot prove |
| `risk_level` | `low` / `medium` / `high`. `high` only for a clear bug, security issue, or major logic risk |
| `merge_recommendation` | `no_concerns_found` / `needs_review` / `changes_required` |
| `failure_modes` | up to 3; omit if none are grounded in the visible code |
| `review_priority_files` | short list a human should open first; empty if the PR is tiny |
| `can_be_split` | up to 3 independent slices `{title, relevant_files}`, or empty. Independent means no code dependency between slices. **Flag only** — do not start a split skill |
| `todo_sections` | `No`, or `{relevant_file, line_number, content}` for real `TODO` comments in the diff (strip a leading `TODO`; cap content at ~10 words) |

Each failure mode: `what` (how it fails after merge), `where`
(`file:function`), `trigger`, `detection` (test, alert, or `nothing` — do
not claim a test ran), `covered_by_this_pr` (true only if this PR's tests
or checks cover the trigger).

Merge recommendation:

- `changes_required` — at least one critical finding
- `needs_review` — no critical finding, but optional issues, flags for
  sensitive paths, or CI failures deserve a closer look
- `no_concerns_found` — nothing important in the diff or the risk flags

## What to show the user

When you present the review (still not posted):

1. Since-last-review classes, if this is a repeat (addressed / reappeared /
   still open / new)
2. Flags for sensitive paths and deleted files, if any
3. Effort, risk, merge recommendation, tests, ticket compliance,
   security concerns
4. Priority files, `can_be_split` (flag only), TODOs, up to three failure
   modes
5. Critical and optional findings (≤6), each with header, path, lines,
   why + trigger, and the draft comment
6. What the packed diff omitted, if anything
