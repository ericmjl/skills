# Experiment Setup

## Hypothesis Scoping

A good experiment tests **one** hypothesis. Before running anything:

1. **State the hypothesis** in one sentence: "If X, then Y (measured by Z)."
2. **Define success and failure** – What metric or outcome would confirm or reject the hypothesis?
3. **List metrics to log** – Only those needed to compute success/failure and to explain unexpected results.
4. **Reject scope creep** – If the user describes multiple ideas, pick one or ask them to choose. Do not bundle several hypotheses into one experiment.

### Project Structure

Create an experiment directory with at least:

- `JOURNAL.md` – Observations, anomalies, hunches, TODOs (read before each action). **One journal for the whole experiment**; it covers both quick and full runs. Optionally include a **“Ignored runs”** section listing runs to exclude from plots and the report.
- **`IGNORED_RUNS.md`** (optional) – List of run paths or identifiers to exclude from plots and the report (failed or irrelevant runs). Keeps runs on disk; agent ignores them when analyzing. See “Ignoring failed or irrelevant runs” below.
- Log files, plots, and any saved data – **Split by run type** (see below). Use **loguru** for logs; scripts are disposable, PEP723 + `uv run`, named by purpose (e.g. `train_small.py`, `eval.py`).
- Final report – Scientific structure; see [report-template.md](report-template.md). The report can cite both quick-run and full-run artifacts (excluding any ignored runs).

### Quick Run vs Full Run: Where to Store Logs, Plots, and Data

**Both runs produce important information. Keep both; do not overwrite quick-run outputs when you do the full run.**

Use **subdirectories** to separate artifacts:

| Run type | Purpose | Store logs, plots, and data in |
|----------|---------|--------------------------------|
| **Quick / de-risking** | Fast iteration (&lt; 60 s), sanity checks, debugging | `quick/` (e.g. `quick/train.log`, `quick/eval.log`, `quick/loss_curve.webp`, `quick/` data subsets or checkpoints if saved) |
| **Full / actual** | Final training and evaluation for the hypothesis | `full/` (e.g. `full/train.log`, `full/eval.log`, `full/loss_curve.webp`, `full/` checkpoints or exports) |

**Conventions:**

- **Scripts**: Live at experiment root (e.g. `train_small.py`, `train_full.py` or one script that takes a `--quick` / `--outdir` flag). Point loguru and plot output paths at the chosen subdirectory (e.g. `quick/` or `full/`) so each run writes into its own folder.
- **Logs**: Always write to the run’s subdirectory (e.g. `quick/train.log`, `full/train.log`). Same names inside each folder are fine; the parent directory identifies the run.
- **Plots**: Generate from the logs in that run’s folder; save plots in the same folder (e.g. `quick/loss_curve.webp`, `full/loss_curve.webp`).
- **Data**: If you save subsets, checkpoints, or exports, put them in the same run’s folder (e.g. `quick/` or `full/`) so it’s clear which run they belong to.
- **Report**: Reference both when relevant (e.g. “Quick run (quick/train.log) confirmed the pipeline; full run (full/train.log) yielded …”). Methods can describe the quick run as de-risking; Results can focus on full run and optionally summarize quick run.

If you prefer a **flat layout** instead of subdirectories, use **namespaced filenames** (e.g. `train_quick.log`, `train_full.log`, `loss_curve_quick.webp`, `loss_curve_full.webp`) and document the convention in JOURNAL.md. Either way, **never overwrite quick-run outputs with full-run outputs**; keep both for the record.

### Ignoring Failed or Irrelevant Runs (Without Deleting)

To have the coding agent **ignore** certain runs when building plots or the report—while **keeping** those runs on disk for the record—use one or both of the following.

**1. Ignore list (recommended)**
Maintain a file **`IGNORED_RUNS.md`** in the experiment root (or a section **`## Ignored runs`** in JOURNAL.md). List run identifiers or paths to exclude from analysis, one per line. Examples:

```markdown
# IGNORED_RUNS.md
full/              # run failed; keep logs but exclude from plots/report
full_20250101/     # aborted run; irrelevant
quick_broken/      # quick run with wrong config
```

**Rule for the agent:** Before generating plots or writing the report, read `IGNORED_RUNS.md` (and JOURNAL.md’s “Ignored runs” section if present). Exclude any run whose path or identifier appears there. Do not delete those runs or their files; only omit them from plots, tables, and report narrative.

**2. Ignored directory (optional)**
Runs stored under a directory named **`ignored/`** (or **`_ignored/`**) are **excluded by default** from plots and the report. You can move or copy a run folder into `ignored/` (e.g. `ignored/full/`, `ignored/full_20250101/`) so the agent skips it without deleting anything. The agent should only consider runs under `quick/` and `full/` (or other non-ignored dirs); do not include contents of `ignored/` or `_ignored/` in analysis unless explicitly asked.

Use the ignore list when you have many runs in the same folder and want to exclude specific ones by name. Use the `ignored/` directory when you prefer to exclude by moving runs into a single place.

## Fast Iteration Checklist

Before running an experiment script, verify:

- [ ] Single run completes in **< 60 seconds** (target) or is explicitly justified if longer.
- [ ] Data subset is **representative** (e.g. stratified sample, not just "first N" unless that is valid).
- [ ] Model has the **same architecture** as the full run, just scaled down (fewer layers, smaller width, or fewer steps).
- [ ] **Evaluation metric** is the same as the intended full run.
- [ ] You have read **JOURNAL.md** and incorporated any [TODO] or [WEIRD] items.

If any item fails, fix it before proceeding (e.g. shrink data further, reduce epochs, or document why a longer run is acceptable).

## Scale-Down Strategies

When a run would exceed ~60 seconds:

| Full setup        | Scaled-down proxy                          |
|-------------------|--------------------------------------------|
| Full dataset      | Stratified sample (e.g. 1k–5k examples)    |
| Many epochs       | 1–5 epochs or 100–500 steps                |
| Large model       | Fewer layers / smaller hidden size        |
| Full evaluation   | Subset of eval set or fewer metrics        |
| Long sequence len | Shorter sequences or smaller batch         |

Keep the **same code paths** (data loading, training loop, evaluation) so that success on the proxy suggests the full run is worth doing.
