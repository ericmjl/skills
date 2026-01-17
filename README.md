# Skills

This repository contains custom skills following the [Anthropic Agent Skills Specification](https://github.com/anthropics/skills).

## What are skills?

Skills are folders of instructions, scripts, and resources that AI agents load dynamically to improve performance on specialized tasks. Each skill teaches an agent how to complete specific tasks in a repeatable way.

## Structure

Each skill lives in its own directory under `skills/` with:

- `SKILL.md` - Required. Contains YAML frontmatter (name, description) and markdown instructions.
- Supporting files - Scripts, references, or other resources the skill needs.

## Available skills

### gh-activity

Location: `skills/gh-activity/`

Reports your GitHub activity for a specific day using the `gh` CLI. Shows commits, issues, and activity timeline. Useful for tracking what you worked on, generating status updates, or reviewing your contributions.

### gh-cli

Location: `skills/gh-cli/`

Comprehensive GitHub CLI operations skill for common tasks like creating PRs, viewing GitHub Actions logs, managing issues, reviewing code, and more. Use this when you need to interact with GitHub repositories directly from the command line without switching to the browser.

### youtube

Location: `skills/youtube/`

Comprehensive YouTube operations using yt-dlp. Download videos and audio, extract transcripts and subtitles, get video metadata, work with playlists, download thumbnails, and inspect available formats. Use this for any YouTube content processing task including transcript extraction for research or creating audio archives.

### agents-md-improver

Location: `skills/agents-md-improver/`

Keeps repo-local agent instructions consistent by proposing updates to `AGENTS.md` when a user corrects the coding agent or asks to change `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`, or `GEMINI.md`. Also proposes consolidation and follow-up delete/symlink/stub actions for repo-local `CLAUDE.md` files.

## Adding new skills

Create a new directory under `skills/` with a `SKILL.md` file:

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it (min 20 chars)
license: MIT
---

# My Skill Name

Instructions for the agent to follow when this skill is active.
```

The `name` field must match the directory name (lowercase with hyphens).

## Using these skills

These skills are compatible with:

- **OpenCode** via the [opencode-skills](https://github.com/malhashemi/opencode-skills) plugin
- **Claude Code** via native skills support
- **Standalone use** by running the scripts directly
