# Session folder structure

Each analysis session is one folder under `analysis/` (or project-agreed base). Name: **ISO datetime + descriptive slug**, e.g. `2025-02-05T14-30-00-protein-binding`.

**Canonical layout:**

```text
analysis/
  2025-02-05T14-30-00-<descriptive-slug>/
    journal.md      # append-only; shape, actions, findings
    plots/          # WebP figures only
    scripts/        # disposable PEP723 scripts; uv run
```

- **journal.md** – Timestamped entries; tags `[SHAPE]`, `[PLOT]`, `[FINDING]`, `[NEXT]`. Record columns, row count, and structure as soon as known.
- **plots/** – All figures from this session; save as `.webp` (matplotlib: `format="webp"`).
- **scripts/** – One script per plot or summary; PEP723 block at top; run with `uv run script.py` (CWD = session folder).
