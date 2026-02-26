# EDA in a Marimo notebook

When exploratory data analysis under this skill is done in a **Marimo notebook** (rather than with scripts in `scripts/`), the notebook must keep the same workflow (context first, one step, journal, ask why) and follow this cell convention.

## Markdown around code cells

Every code cell in the Marimo notebook must have markdown that explains it:

- **Before** the code cell: add a markdown cell that states what the code is about to do (intent, question, or step).
- **After** the code cell: add a markdown cell that explains the results (what the output or plot shows, what it means for the analysis).

This keeps the notebook readable and documents intent and interpretation alongside the code.
