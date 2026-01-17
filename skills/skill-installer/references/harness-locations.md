# Harness locations

This table lists officially documented locations for skills, or the closest equivalent mechanism when a harness does not support Agent Skills folders.

## Table

| Harness | Agent Skills folders supported? | Repo-specific location(s) | Machine-specific location(s) | Closest equivalent if no skills folders | Source |
| --- | --- | --- | --- | --- | --- |
| OpenCode | Yes | `.opencode/skill/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md` | `~/.config/opencode/skill/<name>/SKILL.md`, `~/.claude/skills/<name>/SKILL.md` | N/A | `https://opencode.ai/docs/skills/` |
| Anthropic Claude Code | Yes | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Also supports repo instructions via `CLAUDE.md` | `https://docs.anthropic.com/en/docs/claude-code/skills` |
| GitHub Copilot (general) | Yes | `.github/skills/<name>/SKILL.md` (recommended), `.claude/skills/<name>/SKILL.md` (legacy) | `~/.copilot/skills/<name>/SKILL.md` (recommended), `~/.claude/skills/<name>/SKILL.md` (legacy) | Also supports `AGENTS.md` and `.github/copilot-instructions.md` | `https://docs.github.com/en/copilot/concepts/agents/about-agent-skills` |
| VS Code Copilot documentation | Yes | `.github/skills/<name>/SKILL.md` | `~/.copilot/skills/<name>/SKILL.md` | Also supports `.github/prompts/*.prompt.md` | `https://code.visualstudio.com/docs/copilot/customization/agent-skills` |
| Cursor | Yes | `.cursor/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md` | `~/.cursor/skills/<name>/SKILL.md`, `~/.claude/skills/<name>/SKILL.md` | Also supports Cursor rules via `.cursor/rules/*.md` | `https://cursor.com/docs/context/skills` |
| Gemini CLI | Yes | `.gemini/skills/<name>/SKILL.md` | `~/.gemini/skills/<name>/SKILL.md` | Also supports workspace context via `GEMINI.md` | `https://geminicli.com/docs/cli/skills/` |
| Amp | Yes | `.agents/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md` | `~/.config/agents/skills/<name>/SKILL.md`, `~/.claude/skills/<name>/SKILL.md` | N/A | `https://ampcode.com/news/agent-skills` |
| Google Gemini Code Assist (GitHub integration) | No | N/A | N/A | Repo customization via `.gemini/styleguide.md` and `.gemini/config.yaml` | `https://developers.google.com/gemini-code-assist/docs/customize-gemini-behavior-github` |
| Claude Desktop | No skills folders found in official docs | N/A | N/A | Extensions via MCP, configured in the app | `https://support.claude.com/en/collections/16163169-claude-desktop` |
| Sourcegraph Cody | No skills folders found in official docs | N/A | N/A | Prompt Library in the instance UI | `https://sourcegraph.com/docs/cody/capabilities/prompts` |

## Notes

- If a harness supports both a native skills directory and a Claude-compatible `.claude/skills/` directory, prefer the native directory first.
- If you have another harness that supports skills folders, add it to the table with an official docs link.
