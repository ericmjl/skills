# Skills

This repository contains custom skills following the [Anthropic Agent Skills Specification](https://github.com/anthropics/skills).

## What are skills?

Skills are folders of instructions, scripts, and resources that AI agents load dynamically to improve performance on specialized tasks. Each skill teaches an agent how to complete specific tasks in a repeatable way.

## Structure

Each skill lives in its own directory under `skills/` with:

- `SKILL.md` - Required. Contains YAML frontmatter (name, description) and markdown instructions.
- Supporting files - Scripts, references, or other resources the skill needs.

## Available skills

### gh-daily-timeline

Location: `skills/gh-daily-timeline/`

Reports your GitHub activity for a specific day using the `gh` CLI. Shows commits, issues, and a chronological activity timeline. Use when you need a detailed, event-by-event recap for one date.

### gh-activity-summary

Location: `skills/gh-activity-summary/`

Generates a markdown-friendly summary of your GitHub work over a date range (default: last 7 days). Lists commits, PRs created/merged, reviews, and issues with summary counts. Use for status updates, retrospectives, or piping into an LLM.

### gh-cli

Location: `skills/gh-cli/`

Comprehensive GitHub CLI operations skill for common tasks like creating PRs, viewing GitHub Actions logs, managing issues, reviewing code, and more. Use this when you need to interact with GitHub repositories directly from the command line without switching to the browser.

### gh-pr-code-review

Location: `skills/gh-pr-code-review/`

PR code review workflow: pull diff, two-pass findings, draft and prioritize comments, then optionally post via gh api. Use when reviewing pull requests and leaving actionable feedback.

### ml-experimentation

Location: `skills/ml-experimentation/`

Conduct machine learning experiments from planning through evaluation and report writing. Covers single-hypothesis scoping, fast iteration loops (&lt; 60 s), targeted logging (loguru, .log files), JOURNAL.md protocol, quick vs full run artifact split, data-backed diagnostic plots (WebP), and scientific report writing. Use when running ML experiments, testing hypotheses, training models, or writing up results.

### skill-creator

Location: `skills/skill-creator/`

Guide for creating effective skills. Use when you want to create a new skill (or update an existing skill) that extends an agent with specialized workflows, tool integrations, or repo conventions. Includes init, edit, and package workflow.

### skill-installer

Location: `skills/skill-installer/`

Install and migrate skills across harnesses (OpenCode, Claude Code, Cursor, etc.). Use when installing a skill into a particular product or moving skills between repo-specific and machine-specific locations. See `references/harness-locations.md` for paths.

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
