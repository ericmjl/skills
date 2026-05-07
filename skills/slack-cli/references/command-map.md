# Slack CLI Command Map

This reference summarizes Slack CLI help and command-reference documentation to speed up command selection.

## Base command shape

```bash
slack <command> <subcommand> [flags]
```

## Fast discovery flow

```bash
slack help
slack <subcommand> --help
```

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
