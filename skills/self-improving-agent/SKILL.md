---
name: self-improving-agent
description: |
  Always-on lightweight observer. After EVERY user message, silently check:
  (1) did the user correct me or express a preference? (2) did the user
  express frustration about repetition? (3) is this a rule I've seen before
  in a different project? If ANY are true, run
  `uv run improve.py observe "<rule>" --project <name> [--domain <domain>]`
  to record it. Do NOT load the full skill for observation — this
  description is sufficient. Load the full SKILL.md body only when:
  checking escalation thresholds, writing to AGENTS.md, or running
  /improve. Manages ~/.agent-improvement/rules.yaml via improve.py CLI.
license: MIT
---

# Self-Improving Agent

An always-on observer that captures user corrections and preferences, tracks repetition across projects, and escalates behavioral rules to the appropriate AGENTS.md file.

## Two-Tier Activation

### Tier 1: Observation (always in context)

The YAML description above is loaded every session. It contains everything needed for the lightweight per-message check:

1. After every user message, silently evaluate: did the user correct me, express a preference, or show frustration about repetition?
2. If yes, run one CLI command to record it.
3. Do NOT load the rest of this SKILL.md for observation alone.

### Tier 2: Escalation & Writing (loaded on demand)

The sections below are loaded only when the agent needs to:
- Check escalation thresholds (`/improve due`)
- Write rules into AGENTS.md files
- Review the domain taxonomy or escalation logic
- Run `/improve` command

---

## Observation Protocol

### What to Capture

Record an observation when the user:

- **Corrects the agent**: "don't do X", "use Y instead", "that's wrong", "not like that"
- **States a preference**: "I prefer X", "always do Y", "from now on, Z"
- **Expresses frustration about repetition**: "again?", "I keep having to tell you", "every time", "I've said this before"
- **Gives an explicit instruction**: "remember this", "write that down", "note this"

### What NOT to Capture

- One-time task instructions ("add a button here", "rename this variable")
- Clarification questions ("what did you mean by X?")
- Normal conversational flow
- Things already captured as identical rules

### How to Record

```
uv run <skill-dir>/scripts/improve.py observe "<rule>" --project <name> [--domain <domain>] [--context "<what happened>"] [--explicit-scope global|local]
```

**Rule phrasing**: Write rules as imperatives. Bad: "user doesn't like pip". Good: "Use uv tool for Python CLI tools, never pip3 install".

**Domain**: Pick from the taxonomy below. If unsure, omit it (defaults to "unknown").

**Explicit scope**: Use `--explicit-scope global` when the user says "always", "everywhere", "in all projects". Use `--explicit-scope local` when the user says "in this project", "just here".

**Project detection**: If `--project` is omitted, the CLI auto-detects from `git remote get-url origin`.

---

## Session Startup Protocol

At the start of each session, run:

```
uv run <skill-dir>/scripts/improve.py status
```

This loads all active rules into your context. Apply them during the session. Rules with `written_to` entries are confirmed — treat them as hard rules. Rules without are tentative — apply them but don't enforce rigidly.

---

## Domain Taxonomy

Domains determine whether a rule should escalate to global or stay project-local.

### General Domains (escalate to global when cross-project)

| Domain | Examples |
|--------|----------|
| `python-tooling` | Package managers, virtualenvs, linting |
| `git-practices` | Commit messages, branching, PR conventions |
| `security` | Input validation, secret handling, permissions |
| `code-style` | Naming, formatting, comment style |
| `error-handling` | Try/catch patterns, error messages |
| `testing` | Test frameworks, coverage, test structure |
| `documentation` | Docstrings, README style, API docs |
| `communication` | Response length, tone, formatting |
| `tool-usage` | Which tools to use, search patterns |
| `search-patterns` | Grep vs glob, code navigation |

### Project-Specific Domains (stay local even when cross-project)

| Domain | Examples |
|--------|----------|
| `auth-architecture` | Auth middleware, JWT patterns, session handling |
| `import-patterns` | Module structure, barrel exports, aliases |
| `file-structure` | Directory layout, naming conventions |
| `api-design` | REST patterns, endpoint naming, response format |
| `database-queries` | ORM patterns, migration style, query conventions |
| `ui-components` | Component patterns, state management, styling |
| `config-management` | Environment variables, config files, secrets |
| `deployment` | CI/CD, Docker, infrastructure |

If a rule's domain is `unknown`, treat it as project-specific until the domain is identified.

---

## Escalation Decision Tree

After recording an observation, the CLI prints the recommended action. The full logic:

```
IF explicit_scope == "global":
    → Write to global AGENTS.md immediately (any count)

ELSIF explicit_scope == "local":
    → Never escalate beyond project AGENTS.md (any count)
    → Write to project AGENTS.md at count >= 2

ELSIF total_count == 1:
    → Apply in-session only, no file write

ELSIF total_count >= 2 AND cross_project == false:
    → Write to project AGENTS.md

ELSIF total_count >= 2 AND cross_project == true AND domain is general:
    → Write to global AGENTS.md

ELSIF total_count >= 2 AND cross_project == true AND domain is project-specific:
    → Write to each affected project's local AGENTS.md

ELSIF domain == "unknown":
    → Treat as project-specific, do not escalate until domain is identified
```

### Checking for Due Escalations

At session end (or when the user runs `/improve`):

```
uv run <skill-dir>/scripts/improve.py due
```

This shows all rules that have reached their escalation threshold but haven't been written yet.

### Escalating

```
uv run <skill-dir>/scripts/improve.py escalate --dry-run
```

This prints exactly what should be written to which file. After reviewing, run without `--dry-run` to mark them as escalated in rules.yaml.

---

## Writing Protocol

When a rule is ready for escalation, write it into the appropriate AGENTS.md file.

### Where to Write

| Scope | Path |
|-------|------|
| Global | `~/.config/opencode/AGENTS.md` (or equivalent for the agent harness) |
| Local | `<project-root>/AGENTS.md` |

### How to Write

1. Read the existing AGENTS.md file
2. Find the appropriate section (or create one)
3. Add the rule as a concise bullet point — use the exact rule text from rules.yaml
4. Do NOT duplicate rules that already exist in the file
5. After writing, confirm:

```
uv run <skill-dir>/scripts/improve.py confirm <rule-id> --scope global|local
```

### Formatting Rules in AGENTS.md

Write rules as concise, actionable instructions:

```markdown
## Python Tool Management

- Use `uv tool` for installing Python CLI tools (never `pip3 install`).
- Use `uv run -- python -c "..."` for one-off Python commands (never `python3` or `python`).
```

Not like:

```markdown
- The user has corrected me 3 times about pip. I should use uv instead.
```

---

## Anti-Patterns

### Over-Recording

Not every message is a correction. A user saying "try the other approach" is exploration, not a rule. Only record when the intent is clearly "do it this way from now on."

### Premature Escalation

A rule said once is NOT a rule. Wait for repetition (count >= 2) unless the user explicitly says "always" or "everywhere."

### Vague Rules

"I prefer clean code" is not actionable. Translate to specific behaviors: "Write functions under 20 lines. Extract helpers when logic exceeds 3 levels of nesting."

### Conflicting Rules

If a new rule contradicts an existing one:
1. Record the new observation normally
2. Check which rule has more evidence (higher count, more recent)
3. If both are strong, ask the user which one to keep
4. Retire the loser by adding `"retired": true` to its entry in rules.yaml

### Writing Without Confirming

Always run `confirm` after writing to AGENTS.md. Otherwise the system thinks the rule is still pending and will try to escalate it again.

---

## CLI Reference

All commands use the improve.py script:

```
uv run <skill-dir>/scripts/improve.py <command>
```

| Command | When | Purpose |
|---------|------|---------|
| `observe <rule>` | After user correction/preference | Record a new observation |
| `status` | Session start | Show all rules and counts |
| `due` | Session end or `/improve` | Show pending escalations |
| `escalate [--dry-run]` | When escalation is due | Mark rules for escalation |
| `confirm <id> --scope` | After writing to AGENTS.md | Mark rule as written |
| `history <id>` | Debugging | Full observation history |
| `domains` | Reference | List domain taxonomy |
| `seed --from-agents-md` | First-time setup | Import rules from existing AGENTS.md |
| `init [--force]` | First-time setup | Initialize rules.yaml |

### Path Resolution

The CLI is located at `<skill-dir>/scripts/improve.py`. The skill directory is:
- Local install: `.claude/skills/self-improving-agent/scripts/improve.py`
- Global install: `~/.claude/skills/self-improving-agent/scripts/improve.py`
- OpenCode: `~/.config/opencode/skill/self-improving-agent/scripts/improve.py`

If unsure, search for `improve.py` within the skill directory.

### Data Location

All data is stored at `~/.agent-improvement/rules.yaml`. Override with `AGENT_IMPROVEMENT_HOME` environment variable.

---

## Complete Workflow Example

### Session Start

```
$ uv run improve.py status
  use-uv-not-pip
    rule: Use uv tool for Python CLI tools, never pip3 install
    count: 3 (cross-project, domain=python-tooling [general])
    escalation: global, written_to: 1 files

  check-pyproject-first
    rule: Check pyproject.toml before assuming library availability
    count: 1 (single-project, domain=tool-usage [general])
    escalation: none, written_to: 0 files
```

### During Session (Observation)

User says: "Stop using grep for finding files, use glob instead."

```
$ uv run improve.py observe "Use glob for file pattern matching, not grep" \
    --project my-app --domain search-patterns \
    --context "user corrected grep usage for file search"
RECORDED (count=1) → apply in-session only
```

Same correction in another project, next week:

```
$ uv run improve.py observe "Use glob for file pattern matching, not grep" \
    --project other-project --domain search-patterns \
    --context "user repeated same correction about grep vs glob"
RECORDED (count=2, cross-project, general domain) → candidate for GLOBAL AGENTS.md
```

### Session End (Escalation)

```
$ uv run improve.py due
  use-glob-for-file-pattern-matching-not-grep
    rule: Use glob for file pattern matching, not grep
    count: 2, projects: my-app, other-project
    → ESCALATE TO: global AGENTS.md
```

Agent reads global AGENTS.md, adds the rule, then confirms:

```
$ uv run improve.py confirm use-glob-for-file-pattern-matching-not-grep --scope global
Confirmed: use-glob-for-file-pattern-matching-not-grep written to ~/.config/opencode/AGENTS.md
```
