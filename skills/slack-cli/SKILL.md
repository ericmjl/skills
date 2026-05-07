---
name: slack-cli
description: Use Slack CLI (`slack`) for app lifecycle and workspace operations including login/logout, create/init, run/deploy, manifest validation, trigger management, app install/uninstall, environment management, and diagnostics. Use when users ask to run or troubleshoot commands like `slack create`, `slack run`, `slack deploy`, `slack trigger`, `slack manifest`, `slack auth`, `slack activity`, `slack datastore`, `slack env`, or request help-first progressive discovery with `slack help` and `slack SUBCOMMAND --help`, plus version/documentation alignment and stale-skill refresh.
license: MIT
---

# Slack CLI

Use this skill when working with the Slack command-line tool (`slack`) for local development, app lifecycle, deployment, and command troubleshooting.

Default mindset: discover progressively with `--help`, verify against official docs, and keep both local CLI and this skill content current.

## Requirements

- Slack CLI installed and available as `slack`
- Slack account/team authorization for operations that require workspace access

## What This Skill Covers

- Command discovery and flag lookup via help output
- Local project setup (`create`, `init`, `run`)
- Deployment and lifecycle operations (`deploy`, `install`, `uninstall`, `delete`)
- App metadata and configuration (`manifest`, `env`, `function`, `external-auth`)
- Operational support (`activity`, `doctor`, `version`, `upgrade`)
- Version and documentation alignment (installed CLI vs official docs)
- Self-maintenance when skill guidance is stale

## Official Documentation

- Main docs: `https://docs.slack.dev/tools/slack-cli/`
- Command guide: `https://docs.slack.dev/tools/slack-cli/guides/running-slack-cli-commands`
- Command reference root: `https://docs.slack.dev/tools/slack-cli/reference/commands/slack`

## Default Workflow

1. Clarify intent (discover command syntax, debug, or execute lifecycle action).
2. Start from help and progressively narrow:
   - `slack help`
   - `slack SUBCOMMAND --help`
   - `slack SUBCOMMAND SUBCOMMAND --help` (when nested commands exist)
3. Cross-check syntax/flags with official docs before recommending final commands.
4. Identify whether the task is read-only/help-only or state-changing.
5. For state-changing commands, confirm target workspace/app context (`--team`, `--app`) before execution.
6. Prefer explicit flags over interactive prompts for reproducibility.

## Help-Only Study Mode

If a user asks to "study the CLI" or "do not run real operations":

1. Restrict work to help output and documentation.
2. Do not execute commands that create, modify, deploy, install, uninstall, or delete resources.
3. Build a command map from help pages and global flags.
4. Cross-check discovered commands against official docs links.
5. Return recommended command templates and safe next steps.

## Version and Documentation Alignment

Before making strong command recommendations:

1. Determine the installed CLI version (`slack version`) when command execution is allowed.
2. Compare installed behavior/help output with the current official docs.
3. If docs and local help conflict, prefer local `--help` as runtime truth and explicitly report the mismatch.
4. If the installed CLI appears older than docs, recommend that the user upgrade the local Slack CLI before continuing.

If command execution is not allowed, state that version validation was not performed and recommend the user run `slack version`.

## Self-Improving Maintenance Rules

If this skill appears stale relative to current `--help` output or official docs:

1. Update `SKILL.md` and `references/command-map.md` with corrected commands, flags, and workflows.
2. Keep `--help`-first progressive discovery as the primary workflow.
3. Record new or changed commands in the reference summary.
4. Call out meaningful behavioral changes (renamed commands, deprecated flags, new subcommands).
5. If stale guidance could cause user errors, prioritize fixing the skill before running high-risk operations.

## Global Flags to Check First

- `-a, --app`: target app ID or environment
- `-w, --team`: target workspace/org
- `--token`: token for a team context
- `-f, --force`: continue on warnings
- `-v, --verbose`: debug output
- `--no-color`: plain output
- `-s, --skip-update`: skip CLI update checks

## Common Command Patterns

```bash
slack help
slack <subcommand> --help
slack create <name>
slack run
slack deploy --team <TEAM_ID_OR_NAME>
slack manifest validate
slack trigger list
```

## References

- For a command overview and frequently used flags, read `references/command-map.md`.
