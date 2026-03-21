---
name: epistemic-resourcefulness
description: >
  Breaks the cycle of repeated failed attempts by redirecting the agent to find the
  authoritative source of truth about a system's structure before trying again.
  Trigger this skill when: (1) the same command or query has failed 2+ times with
  variations, (2) output is garbled/binary and unreadable, (3) guessed field names,
  endpoints, or flags keep returning errors, (4) file/directory scanning is producing
  no useful signal. In short: if you're brute-forcing and it's not working, stop and
  use this skill.
license: MIT
---

# Epistemic Resourcefulness

Before interacting with any unfamiliar system, **find the authoritative source of truth
about its structure**. Do not guess, scan blindly, or trial-and-error your way to an
answer when a definitive source exists.

## The Core Rule

> For every structured system, there is an authoritative description of that structure.
> Locate it first. Then act.

## Quick Reference: Authoritative Sources by System Type

| System | Authoritative source | How to access |
|--------|---------------------|---------------|
| SQLite database | Schema | `sqlite3 file.db ".schema"` |
| Any SQL DB | Table/column info | `DESCRIBE table` / `information_schema` |
| CLI tool | Help text | `tool --help` or `man tool` |
| REST API | OpenAPI/Swagger spec | `/docs`, `/openapi.json`, or repo |
| Python package | Installed interface | `python -c "import pkg; help(pkg)"` |
| File format | Format library docs | Check PyPI/npm for a parser library |
| Config system | Schema/defaults | Config file comments, `--show-config` |
| Running process | Its own API | Check docs for management interface |
| Codebase | Entry points | README, AGENTS.md, `__init__.py`, `index.ts` |
| npm/Python project | Dependencies | `package.json`, `pyproject.toml` |

## The Anti-Pattern: Brute-Forcing

**Brute-forcing** looks like:
- Reading a binary file byte-by-byte without knowing its format
- Querying a DB with guessed column names
- Scanning every file in a directory when a manifest exists
- Repeating variations of a failed command hoping one works
- Trying API endpoints at random

Brute-forcing is wasteful and unreliable. It signals that the agent skipped the investigation step.

## The Pattern: Investigate First

When facing an unfamiliar system:

1. **Identify what kind of system it is** (database? CLI? API? file format?)
2. **Look up the authoritative source** for that system type (see table above)
3. **Retrieve the structure** (schema, help text, spec, manifest)
4. **Then act** with knowledge of the actual structure

## Worked Example

**Task:** Read conversation history from the OpenCode SQLite database.

**Brute-force approach** (wrong):
```bash
cat ~/.local/share/opencode/opencode.db   # binary garbage
ls ~/.local/share/opencode/               # scanning around
```

**Resourceful approach** (correct):
```bash
# Step 1: Identify - it's SQLite
# Step 2: Authoritative source = schema
sqlite3 ~/.local/share/opencode/opencode.db ".tables"
sqlite3 ~/.local/share/opencode/opencode.db ".schema session"
# Step 3: Now query with known column names
sqlite3 ~/.local/share/opencode/opencode.db \
  "SELECT id, title FROM session ORDER BY time_created DESC LIMIT 5;"
```

## A Note on "Obvious" Systems

Even systems you think you know may have changed or have non-obvious quirks in this
specific environment. When something isn't working as expected, resist the urge to
iterate blindly - treat it as an unfamiliar system and re-run the investigation step.
