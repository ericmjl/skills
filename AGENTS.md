# AGENTS.md

This is a skills repository following the [Anthropic Agent Skills Specification](https://github.com/anthropics/skills).

## Build/Test Commands

No package build. Skills are markdown instructions with optional scripts.
The pronunciation-lexicon sync check is `bash scripts/check-pronunciation-lexicon.sh`
(GitHub Actions runs it on push and pull requests).

## Version Control

This repository is git-tracked. Any change made inside this directory — editing,
adding, or removing skills — must be tracked with git: commit each logical change
with a descriptive message, and do not leave work uncommitted. Prefer atomic
commits (one skill per commit) over mixed batches.

## Creating Skills

1. Create a folder under `skills/` with lowercase hyphenated name
2. Add `SKILL.md` with YAML frontmatter: `name`, `description` (min 20 chars), `license`
3. The `name` field must match the directory name exactly

## Writing

For any writing or drafting task, including academic papers, load the
`writing` skill before producing text. It is a short router that names
the specialized writing skills to run and the order to run them in. Then
load those skills instead of improvising.

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

## Pronunciation lexicon

The canonical pronunciation glossary is `skills/explainer-video/lexicon.json`
in this repository. Each voice skill that uses the glossary keeps its own
copy of that file inside the skill folder. Skills must not import the
glossary from another skill at runtime.

Edit the canonical file first, then copy it unchanged to every path listed
in `scripts/pronunciation-lexicon-copies.txt`. Those copies must match the
canonical file exactly (byte-for-byte). A CI check fails when the canonical
file is missing, or when a listed copy is missing or differs.

Copies that must match the canonical file are the paths in
`scripts/pronunciation-lexicon-copies.txt`. None are listed yet: do not add
a copy to a skill until that skill can use it, then add the path to the
manifest in the same change.

Only one entry has been verified by ear so far: `pixi` is respelt `pixie`
(2026-11-20). Leave other entries unverified until Eric confirms them.

Voice skills in this repo that can produce spoken audio, but do not yet
carry a `lexicon.json` copy (list only):

- `skills/motion-graphics-video` — optional voiceover; no glossary file.

