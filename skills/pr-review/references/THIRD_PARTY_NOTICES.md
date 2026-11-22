# Third-party notices

Legal attribution. Do not load this file into a review prompt.

This skill paraphrases review workflow ideas from
[The-PR-Agent/pr-agent](https://github.com/The-PR-Agent/pr-agent)
at commit `db4c4ad9cffacbb65badc6bc29c3f9ef6eac9a8` (`db4c4ad`).
It is not a fork and does not vendor PR-Agent source.

Field names in `review-output-schema.md`, the `__new hunk__` / `__old hunk__`
markers in `large-diff-strategy.md`, and the sensitive-path glob list are
kept close to upstream so a review stays interoperable. Prose is
paraphrased.

## Studied upstream paths (commit db4c4ad)

- `pr_agent/settings/pr_reviewer_prompts.toml` (`[pr_review_prompt].system`)
- `pr_agent/settings/configuration.toml` (`[pr_reviewer]`, including
  `sensitive_paths`, `persistent_finding_state`, `num_max_findings`)
- `pr_agent/settings/prompt_fragments.toml` (`diff_hunk_format`)
- `pr_agent/algo/deterministic_risk.py`
- `pr_agent/algo/pr_processing.py`
- `pr_agent/algo/git_patch_processing.py`
- `pr_agent/algo/token_budget.py`
- `pr_agent/algo/review_finding_state.py`
- `pr_agent/algo/inline_comment_dedup.py`
- `pr_agent/algo/review_merge.py`
- `docs/docs/core-abilities/compression_strategy.md`
- `docs/docs/core-abilities/dynamic_context.md`

## MIT License (PR-Agent)

MIT License

Copyright (c) 2026 The PR Agent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
