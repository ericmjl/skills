# Harness locations

This table lists officially documented locations for skills, or the closest equivalent mechanism when a harness does not support Agent Skills folders.

## Emerging standard

Many products now support a common layout for agent skills:

- **Repo-specific:** `.agents/skills/<name>/SKILL.md`
- **Machine-specific (global):** `~/.agents/skills/<name>/SKILL.md`

Products that support this standard (as of 2026 February) include **Codex**, **OpenCode**, **GitHub Copilot**, and **Cursor**. **Anthropic Claude Code** currently uses only `.claude/skills/` and has not adopted the `.agents/skills` paths yet. When a harness supports the standard, prefer `.agents/skills` (repo) or `~/.agents/skills` (global) for portability. See [Theo](https://x.com/theo/status/2018819504252608710) and [Lee Robinson](https://x.com/leerob/status/2018770085956010119) on industry adoption.

## Table

| Harness | Agent Skills folders supported? | Repo-specific location(s) | Machine-specific location(s) | Closest equivalent if no skills folders | Source |
| --- | --- | --- | --- | --- | --- |
| **Codex** | Yes | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | N/A | Standard (industry adoption) |
| **OpenCode** | Yes | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | N/A | `https://opencode.ai/docs/skills/` |
| **GitHub Copilot** | Yes | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | N/A | `https://docs.github.com/en/copilot/concepts/agents/about-agent-skills` |
| **Cursor** | Yes | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | N/A | `https://cursor.com/docs/context/skills` |
| Anthropic Claude Code | Yes | `.claude/skills/<name>/SKILL.md` (no `.agents/skills` yet) | `~/.claude/skills/<name>/SKILL.md` | Also supports repo instructions via `CLAUDE.md` | `https://docs.anthropic.com/en/docs/claude-code/skills` |
| Gemini CLI | Yes | `.gemini/skills/<name>/SKILL.md` | `~/.gemini/skills/<name>/SKILL.md` | Also supports workspace context via `GEMINI.md` | `https://geminicli.com/docs/cli/skills/` |
| Google Antigravity | Yes | `.agent/skills/<name>/SKILL.md` | `~/.gemini/antigravity/skills/<name>/SKILL.md` | N/A | `https://antigravity.google/docs/skills` |
| **Amp** | Yes | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | N/A | `https://ampcode.com/news/agent-skills` |
| Google Gemini Code Assist (GitHub integration) | No | N/A | N/A | Repo customization via `.gemini/styleguide.md` and `.gemini/config.yaml` | `https://developers.google.com/gemini-code-assist/docs/customize-gemini-behavior-github` |
| Claude Desktop | No skills folders found in official docs | N/A | N/A | Extensions via MCP, configured in the app | `https://support.claude.com/en/collections/16163169-claude-desktop` |
| Sourcegraph Cody | No skills folders found in official docs | N/A | N/A | Prompt Library in the instance UI | `https://sourcegraph.com/docs/cody/capabilities/prompts` |

## Notes

- Use **`.agents/skills`** (repo) and **`~/.agents/skills`** (global) for harnesses that support the standard.
- If you have another harness that supports skills folders, add it to the table with an official docs link.
