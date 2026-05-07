# Slack CLI Command Map

This reference summarizes Slack CLI help and command-reference documentation to speed up command selection.

## Source-of-truth order

1. Installed CLI `--help` output (runtime truth for the current machine)
2. Official Slack CLI docs (latest documented behavior)
3. This skill reference (maintained summary)

When they disagree, report the mismatch and adapt recommendations accordingly.

## Base command shape

```bash
slack <command> <subcommand> [flags]
```

## Fast discovery flow

```bash
slack help
slack SUBCOMMAND --help
slack SUBCOMMAND SUBCOMMAND --help
```

Use this as a progressive drill-down pattern: broad command list first, then subcommand-specific options.

## Core global flags

- `-a, --app string`: app ID or environment
- `-w, --team string`: workspace/org name or ID
- `--token string`: token associated with a team
- `-f, --force`: ignore warnings and continue
- `-v, --verbose`: debug logging
- `--no-color`: remove styles and formatting
- `-s, --skip-update`: skip update check

## High-frequency commands

- `slack login`, `slack logout`, `slack list`, `slack auth`
- `slack create`, `slack init`, `slack run`, `slack deploy`
- `slack install`, `slack uninstall`, `slack app`
- `slack manifest`, `slack trigger`, `slack env`, `slack function`
- `slack activity`, `slack doctor`, `slack version`, `slack upgrade`

## Notable command details

### `slack create`

- Creates a local project from template.
- Syntax:

```bash
slack create [name | agent <name>] [flags]
```

- Useful flags: `--template`, `--subdir`, `--name`, `--list`, `--branch`.

### `slack deploy`

- Deploys app to Slack platform.
- Syntax:

```bash
slack deploy [flags]
```

- Useful flags: `--hide-triggers`, `--org-workspace-grant`.

### `slack manifest`

- Prints, validates, or inspects app manifest.
- Common usage:

```bash
slack manifest info
slack manifest validate
```

## Practical safety checks

Before any state-changing command, confirm:

1. Correct target app (`--app`) and workspace (`--team`).
2. Whether action is reversible.
3. Whether user asked for help-only exploration.

## Version checks and upgrade guidance

- Validate installed version with:

```bash
slack version
```

- If local CLI appears older than docs or missing documented flags/subcommands:
  - recommend local Slack CLI upgrade
  - re-run help discovery after upgrade
  - refresh this skill if command behavior changed

## Skill maintenance checklist

Update this skill when any of the following is observed:

- A command/flag in docs does not exist in local help output
- A command/flag in local help is missing from this reference
- Command syntax changes (new required args, renamed subcommands, deprecated flags)

When updating, modify both:

- `skills/slack-cli/SKILL.md` (workflow and trigger guidance)
- `skills/slack-cli/references/command-map.md` (concise command summary)
