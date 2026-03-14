---
name: continuous-learning-v3
description: Instinct-based learning system that observes sessions via hooks, creates atomic instincts with confidence scoring, and evolves them into skills/commands/agents. v3.0 adds project-scoped instincts to prevent cross-project contamination.
origin: skills
version: 3.0.0
license: MIT
---

# Continuous Learning v3

An agent-agnostic learning system that observes your AI coding sessions and creates reusable knowledge through atomic "instincts" — small learned behaviors with confidence scoring.

## ⚡ First-Time Setup (Automatic)

**When this skill is first loaded, automatically perform these steps:**

### Step 1: Check if Plugin is Installed

```bash
# Check for the OpenCode plugin
ls ~/.config/opencode/plugins/continuous-learning.js
```

### Step 2: If Not Installed, Install It

If the plugin file does not exist:

1. Find the skill directory (where this SKILL.md is located)
2. Copy the plugin:
   ```bash
   cp <skill-directory>/plugins/continuous-learning.js \
      ~/.config/opencode/plugins/continuous-learning.js
   ```
3. Create a marker file to track installation:
   ```bash
   touch ~/.config/opencode/skill/continuous-learning-v3/.installed
   ```

### Step 3: Create Storage Directories

```bash
mkdir -p ~/.agent-learning/instincts/personal
mkdir -p ~/.agent-learning/instincts/inherited
mkdir -p ~/.agent-learning/evolved/skills
mkdir -p ~/.agent-learning/evolved/commands
mkdir -p ~/.agent-learning/evolved/agents
mkdir -p ~/.agent-learning/projects
```

### Step 4: Tell User to Restart

After installing the plugin, tell the user:

> ✅ Continuous Learning plugin installed!
> 
> **Please restart OpenCode** to activate automatic learning.
> 
> After restart, all tool executions will be observed and patterns will be learned automatically.
> 
> To check learning status: `uv run ~/.config/opencode/skill/continuous-learning-v3/scripts/instinct-cli.py status`

---

## When to Activate

- User asks about learning, patterns, or preferences
- User wants to see what the agent has learned
- User wants to export/import instincts
- User wants to evolve instincts into skills
- First time the skill is loaded (run setup)

## The Instinct Model

An instinct is a small learned behavior:

```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
source: "session-observation"
scope: project
project_id: "a1b2c3d4e5f6"
project_name: "my-react-app"
agent: "opencode"
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.

## Evidence
- Observed 5 instances of functional pattern preference
- User corrected class-based approach on 2025-01-15
```

**Properties:**
- **Atomic** — one trigger, one action
- **Confidence-weighted** — 0.3 = tentative, 0.9 = near certain
- **Domain-tagged** — code-style, testing, git, debugging, workflow, etc.
- **Evidence-backed** — tracks what observations created it
- **Scope-aware** — `project` (default) or `global`
- **Agent-aware** — tracks which agent learned this pattern

## CLI Commands

Use the CLI to manage instincts:

```bash
# Show all instincts (project + global)
uv run <skill-dir>/scripts/instinct-cli.py status

# Cluster related instincts into skills/commands
uv run <skill-dir>/scripts/instinct-cli.py evolve

# Export instincts
uv run <skill-dir>/scripts/instinct-cli.py export -o my-instincts.yaml

# Import instincts
uv run <skill-dir>/scripts/instinct-cli.py import my-instincts.yaml

# Promote project instincts to global
uv run <skill-dir>/scripts/instinct-cli.py promote

# List known projects
uv run <skill-dir>/scripts/instinct-cli.py projects

# Migrate from v2.x
uv run <skill-dir>/scripts/instinct-cli.py migrate --from ~/.claude/homunculus
```

## File Structure

```
~/.agent-learning/
+-- config.yaml             # Configuration
+-- projects.json           # Registry: project hash -> name/path/remote
+-- observations.jsonl      # Global observations (fallback)
+-- instincts/
|   +-- personal/           # Global auto-learned instincts
|   +-- inherited/          # Global imported instincts
+-- evolved/
|   +-- agents/             # Global generated agents
|   +-- skills/             # Global generated skills
|   +-- commands/           # Global generated commands
+-- projects/
    +-- a1b2c3d4e5f6/       # Project hash (from git remote URL)
    |   +-- project.json    # Per-project metadata
    |   +-- observations.jsonl
    |   +-- instincts/
    |   |   +-- personal/   # Project-specific auto-learned
    |   |   +-- inherited/  # Project-specific imported
    |   +-- evolved/
    |       +-- skills/
    |       +-- commands/
    |       +-- agents/
    +-- ...                 # Other projects
```

## Scope Decision Guide

| Pattern Type | Scope | Examples |
|-------------|-------|---------|
| Language/framework conventions | **project** | "Use React hooks", "Follow Django REST patterns" |
| File structure preferences | **project** | "Tests in `__tests__`/" |
| Code style | **project** | "Use functional style", "Prefer dataclasses" |
| Security practices | **global** | "Validate user input", "Sanitize SQL" |
| General best practices | **global** | "Write tests first", "Always handle errors" |
| Tool workflow preferences | **global** | "Grep before Edit", "Read before Write" |
| Git practices | **global** | "Conventional commits", "Small focused commits" |

## Confidence Scoring

| Score | Meaning | Behavior |
|-------|---------|----------|
| 0.3 | Tentative | Suggested but not enforced |
| 0.5 | Moderate | Applied when relevant |
| 0.7 | Strong | Auto-approved for application |
| 0.9 | Near-certain | Core behavior |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_LEARNING_HOME` | `~/.agent-learning` | Base directory for all data |
| `AGENT_PROJECT_DIR` | (auto-detected) | Override project detection |
| `AGENT_LEARNING_DISABLED` | (unset) | Set to `1` to disable observation |

## Troubleshooting

### Plugin Not Loading

1. Check plugin exists: `ls ~/.config/opencode/plugins/continuous-learning.js`
2. Restart OpenCode
3. Check for errors in OpenCode logs

### No Observations Being Captured

1. Check `AGENT_LEARNING_DISABLED` is not set
2. Verify project detection: `git remote get-url origin`
3. Check observations file: `cat ~/.agent-learning/projects/*/observations.jsonl`

### Reset Everything

```bash
rm -rf ~/.agent-learning
rm ~/.config/opencode/plugins/continuous-learning.js
rm ~/.config/opencode/skill/continuous-learning-v3/.installed
# Then reload this skill to re-run setup
```

## Privacy

- Observations stay **local** on your machine
- Project-scoped instincts are isolated per project
- Only **instincts** (patterns) can be exported — not raw observations
- No actual code or conversation content is shared
- You control what gets exported and promoted

## Attribution

This skill is a generalized, agent-agnostic fork of [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2) from the [everything-claude-code](https://github.com/affaan-m/everything-claude-code) repository.
