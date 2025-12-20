# Skills

This repository contains custom skills for Claude Code and other automation tools.

## What are skills?

Skills are reusable commands that extend the functionality of your development environment. Each skill is a self-contained tool that performs a specific task, like reporting GitHub activity, analyzing code, or automating workflows.

## Structure

The repository follows this organization:

- `skills/` - All skill implementations live here
- `docs/` - Documentation and guides
- `README.md` - This file (the index)

## Available skills

### GitHub activity reporter

Location: `skills/gh-activity/`

Reports your GitHub activity for a specific day using the `gh` CLI. Useful for tracking what you worked on, generating status updates, or reviewing your contributions.

[Read more →](skills/gh-activity/README.md)

## Adding new skills

Each skill should live in its own directory under `skills/` with:

- The skill implementation (script, program, etc.)
- A `skill.json` metadata file
- A `README.md` explaining what it does and how to use it

The approach is straightforward: keep skills focused on doing one thing well, document them clearly, and make them easy to use.

## Using these skills

The specific method for using these skills depends on your environment. If you're using Claude Code, you can invoke skills with the `/` command syntax.

For standalone use, you can run the scripts directly from their directories.
