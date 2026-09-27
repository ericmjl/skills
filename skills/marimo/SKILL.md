---
name: marimo
description: >-
  Everything marimo notebooks: authoring and editing notebook .py files
  (cell params, unique-variable rules, StaleCellError, API gotchas), pairing
  on a LIVE notebook via marimo-pair code_mode, embedding interactive marimo
  cells in a blog or website (WASM/Pyodide approaches and trade-offs),
  migrating a docs repo so marimo .py notebooks are the single source of
  truth with generated artifacts gitignored, and building an awesome marimo
  notebook that brings a research paper or dataset to life (competitions,
  tutorials, blog companions). Load when the user asks to create, edit,
  debug, pair on, embed, export, or migrate ANY marimo notebook, mentions
  molab, or wants an interactive notebook explainer.
license: MIT
---

# marimo

Umbrella skill for the marimo notebook toolchain. Load the reference that
matches the task; each reference is the former standalone skill's full body,
preserved verbatim.

| Task | Reference |
|------|-----------|
| Authoring or editing ANY marimo notebook .py file; pitfalls, API signatures, StaleCellError, code_mode mutations | [references/marimo_notebook_patterns.md](references/marimo_notebook_patterns.md) |
| Pairing on a live marimo session (kernel state, committing durable changes) | the marimo-pair skill (third-party, installed separately) |
| Embedding marimo cells/snippets in a blog or static site (WASM, Pyodide, islands) | [references/marimo_wasm_embed_blog.md](references/marimo_wasm_embed_blog.md) |
| Making marimo .py notebooks the single source of truth in a docs repo (build-time exports) | [references/marimo_source_of_truth_export_pipeline.md](references/marimo_source_of_truth_export_pipeline.md) |
| Building a competition/tutorial/blog-companion notebook from a paper or dataset | [references/awesome_marimo_notebook.md](references/awesome_marimo_notebook.md) |

Consolidated 2026-09-27 from five narrow skills (marimo-notebook-patterns,
awesome-marimo-notebook, marimo-wasm-embed-blog,
marimo-source-of-truth-export-pipeline; marimo-pair remains third-party and
separate).
