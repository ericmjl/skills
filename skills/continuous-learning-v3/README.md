# Continuous Learning v3

An agent-agnostic learning system that observes AI coding agent sessions and creates reusable knowledge through atomic "instincts" with confidence scoring.

## Self-Installing

This skill automatically installs its plugin when first loaded:

1. Agent loads SKILL.md
2. Agent checks if plugin is installed at `~/.config/opencode/plugins/continuous-learning.js`
3. If not, agent copies plugin from skill directory
4. Agent creates storage directories at `~/.agent-learning/`
5. Agent tells user to restart OpenCode
6. After restart, plugin observes all tool executions automatically

## Attribution

This skill is a generalized, agent-agnostic fork of [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2) from the [everything-claude-code](https://github.com/affaan-m/everything-claude-code) repository by [affaan-m](https://github.com/affaan-m).

### What Changed in v3

| Feature | v2.x (Original) | v3.0 (This Fork) |
|---------|-----------------|------------------|
| Target agent | Claude Code only | Any AI coding agent |
| Storage location | `~/.claude/homunculus/` | `~/.agent-learning/` |
| Environment vars | `CLAUDE_*` | `AGENT_*` |
| Scope | Global only | Project-scoped + global |
| Agent tracking | None | `agent` field on instincts |
| Self-install | Manual setup.sh | Automatic on first load |

### Key Concepts Preserved

- **Instinct model**: Atomic learned behaviors with confidence scoring
- **Project scoping**: Isolate instincts per project, promote to global
- **Pattern detection**: User corrections, error resolutions, repeated workflows
- **Evolution pipeline**: Instincts → Skills/Commands/Agents
- **Privacy-first**: Observations stay local, only patterns exported

## Installation

### For OpenCode

```bash
# Option 1: Use skill-installer
# The skill will auto-install its plugin on first load

# Option 2: Manual
git clone <repo-url>
cp -r skills/continuous-learning-v3 ~/.config/opencode/skill/
# Then load the skill in OpenCode - it will install the plugin automatically
```

## CLI Usage

```bash
# Show all instincts
uv run ~/.config/opencode/skill/continuous-learning-v3/scripts/instinct-cli.py status

# Cluster instincts into skills
uv run ~/.config/opencode/skill/continuous-learning-v3/scripts/instinct-cli.py evolve

# Export instincts
uv run ~/.config/opencode/skill/continuous-learning-v3/scripts/instinct-cli.py export -o my-instincts.yaml

# Import instincts
uv run ~/.config/opencode/skill/continuous-learning-v3/scripts/instinct-cli.py import my-instincts.yaml
```

## File Structure

```
~/.agent-learning/
├── config.yaml           # Configuration
├── projects.json         # Project registry
├── instincts/
│   ├── personal/         # Global auto-learned
│   └── inherited/        # Global imported
├── evolved/
│   ├── skills/           # Generated skills
│   ├── commands/         # Generated commands
│   └── agents/           # Generated agents
└── projects/
    └── <project-hash>/   # Per-project data
        ├── observations.jsonl
        └── instincts/
            ├── personal/
            └── inherited/
```

See [SKILL.md](./SKILL.md) for full documentation.
