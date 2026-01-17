# AGENTS.md

This is a skills repository following the [Anthropic Agent Skills Specification](https://github.com/anthropics/skills).

## Build/Test Commands

No build or test system. Skills are markdown instructions with optional scripts.

## Creating Skills

1. Create a folder under `skills/` with lowercase hyphenated name
2. Add `SKILL.md` with YAML frontmatter: `name`, `description` (min 20 chars), `license`
3. The `name` field must match the directory name exactly

## Shell Script Style

- Shebang: `#!/usr/bin/env bash`
- Always use `set -euo pipefail` for strict error handling
- Variables: `UPPERCASE` naming (e.g., `DATE`, `USERNAME`)
- Default parameters: `${1:-default_value}`
- Errors to stderr with actionable messages: `echo "Error: ..." >&2`
- Validate inputs early with clear error messages

## Python Script Style

- Use PEP723-style inline script metadata at the top of the file
- Include `requires-python` and `dependencies` in the metadata block
- Always run scripts with `uv run script.py` (document this in SKILL.md)
- Example metadata block:
  ```python
  # /// script
  # requires-python = ">=3.11"
  # dependencies = ["requests", "rich"]
  # ///
  ```

## SKILL.md Structure

Include sections: Usage, Requirements, What It Does, How It Works. Use fenced code blocks with language specifiers for examples.
