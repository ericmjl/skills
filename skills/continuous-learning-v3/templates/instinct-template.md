# Instinct Template

## YAML Frontmatter

```yaml
---
id: <kebab-case-identifier>
trigger: "when <condition or context>"
confidence: 0.5
domain: "<domain>"
source: "session-observation"
scope: project
agent: "<agent-name>"
---
```

## Body

```markdown
# <Human-Readable Title>

## Action
<What the agent should do when the trigger condition is met>

## Evidence
- <Observation 1>
- <Observation 2>
- Last observed: <date>

## Examples (optional)
<Concrete examples of when this applies>
```

## Domains

| Domain | Description |
|--------|-------------|
| `code-style` | Formatting, naming conventions, patterns |
| `testing` | Test strategies, coverage preferences |
| `git` | Commit practices, branching strategies |
| `debugging` | Error resolution, debugging approaches |
| `workflow` | Tool sequences, process preferences |
| `security` | Validation, sanitization, auth patterns |
| `documentation` | Comments, README, API docs |
| `architecture` | File structure, module organization |
| `general` | Cross-cutting concerns |

## Scope Values

| Value | Meaning |
|-------|---------|
| `project` | Only applies to this project (default) |
| `global` | Applies across all projects |

## Agent Values

| Value | Meaning |
|-------|---------|
| `claude-code` | Claude Code CLI |
| `cursor` | Cursor IDE |
| `gemini` | Gemini CLI |
| `opencode` | OpenCode |
| `any` | Universal (works with any agent) |

## Complete Example

```yaml
---
id: prefer-functional-components
trigger: "when creating React components"
confidence: 0.7
domain: "code-style"
source: "session-observation"
scope: project
project_id: "a1b2c3d4e5f6"
project_name: "my-react-app"
agent: "claude-code"
---

# Prefer Functional Components

## Action
Use functional components with hooks instead of class components for all new React components.

## Evidence
- Observed 8 instances of functional component preference
- User corrected class-based approach on 2025-01-15
- Last observed: 2025-01-22
```
