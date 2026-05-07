---
name: slack-cli
description: Use Slack CLI (`slack`) for app lifecycle and workspace operations including login/logout, create/init, run/deploy, manifest validation, trigger management, app install/uninstall, environment management, and diagnostics. Use when users ask to run or troubleshoot commands like `slack create`, `slack run`, `slack deploy`, `slack trigger`, `slack manifest`, `slack auth`, `slack activity`, `slack datastore`, `slack env`, or request help-only command discovery with `slack help` / `slack SUBCOMMAND --help`.
license: MIT
---

# Slack CLI

Use this skill when working with the Slack command-line tool (`slack`) for local development, app lifecycle, deployment, and command troubleshooting.

## Requirements

- Slack CLI installed and available as `slack`
- Slack account/team authorization for operations that require workspace access

## What This Skill Covers

- Command discovery and flag lookup via help output
- Local project setup (`create`, `init`, `run`)
- Deployment and lifecycle operations (`deploy`, `install`, `uninstall`, `delete`)
- App metadata and configuration (`manifest`, `env`, `function`, `external-auth`)
- Operational support (`activity`, `doctor`, `version`, `upgrade`)

## Default Workflow

1. Clarify intent (discover command syntax, debug, or execute lifecycle action).
2. Start from help:
   - `slack help`
   - `slack <subcommand> --help`
3. Identify whether the task is read-only/help-only or state-changing.
4. For state-changing commands, confirm target workspace/app context (`--team`, `--app`) before execution.
5. Prefer explicit flags over interactive prompts for reproducibility.

## Help-Only Study Mode

If a user asks to "study the CLI" or "do not run real operations":

1. Restrict work to help output and documentation.
2. Do not execute commands that create, modify, deploy, install, uninstall, or delete resources.
3. Build a command map from help pages and global flags.
4. Return recommended command templates and safe next steps.

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
