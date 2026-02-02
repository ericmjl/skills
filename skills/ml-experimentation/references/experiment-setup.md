# Experiment Setup

## New Experiment vs New Run

Before creating directories or running code, decide:

- **New experiment** – You are trying to answer a **different question**. That means a new hypothesis (or a meaningfully different formulation). Start a **new experiment directory**: new `JOURNAL.md`, new canonical tree (`runs/`, etc.), new report. Do not mix hypotheses in one experiment.
- **New run** – You are making **tweaks to answer the same question**. Same hypothesis; you’re changing config, data subset, hyperparameters, or code to better test it. Add a **new run** under the existing experiment: name the run **full ISO datetime + descriptive string** `YYYY-MM-DDTHH-MM-SS-<descriptive-string>` (e.g. `runs/2025-02-02T14-30-00-de-risk`, `runs/2025-02-02T15-00-00-full`, `runs/2025-02-03T09-00-00-retry`). Time uses hyphens for filesystem-safe directory names. Reuse the same experiment directory, JOURNAL.md, and scripts; only the run name and its outputs (logs, plots, checkpoints, data) are new.

**Rule of thumb:** Same question → new run. Different question → new experiment.

## Hypothesis Scoping

A good experiment tests **one** hypothesis. Before running anything:

1. **State the hypothesis** in one sentence: "If X, then Y (measured by Z)."
2. **Define success and failure** – What metric or outcome would confirm or reject the hypothesis?
3. **List metrics to log** – Only those needed to compute success/failure and to explain unexpected results.
4. **Reject scope creep** – If the user describes multiple ideas, pick one or ask them to choose. Do not bundle several hypotheses into one experiment.

### Canonical Directory Tree

Experiments have **runs**; each run has **logs**, **plots**, **checkpoints**, and **data** as subfolders. Name each run **full ISO datetime + descriptive string**: **`YYYY-MM-DDTHH-MM-SS-<descriptive-string>`** (time with hyphens for filesystem-safe dirs) so you keep a chronological, readable running log without overwriting.

```
<experiment>/
  JOURNAL.md
  IGNORED_RUNS.md          # optional
  report.md                # final scientific report
  train.py
  eval.py
  generate_data.py         # optional: synthetic data generation
  runs/
    2025-02-02T14-30-00-de-risk/   # de-risking run (< 60 s)
      logs/
        train.log
        eval.log
      plots/
        loss_curve.webp
      checkpoints/         # optional
      data/                # optional subsets, exports
    2025-02-02T15-00-00-full/     # full run for hypothesis
      logs/
        train.log
        eval.log
      plots/
        loss_curve.webp
      checkpoints/
      data/
    2025-02-03T09-00-00-retry/    # another run, same structure
      logs/
      plots/
      checkpoints/
      data/
```

**Conventions:**

- **Runs** – One directory per run under `runs/`. Name each run **`YYYY-MM-DDTHH-MM-SS-<descriptive-string>`** (full ISO datetime; time with hyphens for FS safety), e.g. `2025-02-02T14-30-00-de-risk`, `2025-02-02T15-00-00-full`, `2025-02-03T09-00-00-retry`. The datetime is when the run started; the string describes the run (de-risk, full, retry, lr-sweep, etc.). Keep a running log; never overwrite an existing run directory.
- **Inside each run** – `logs/` (loguru `.log` files), `plots/` (e.g. `.webp` from logged data), `checkpoints/` (optional), `data/` (optional subsets or exports). Scripts write into the run’s subdirs (e.g. `runs/2025-02-02T14-30-00-de-risk/logs/train.log`, `runs/2025-02-02T15-00-00-full/plots/loss_curve.webp`).
- **Scripts** – At experiment root (`train.py`, `eval.py`, optional `generate_data.py` for synthetic data, etc.). **Run with CWD = experiment directory** so paths like `runs/2025-02-02T14-30-00-de-risk`, `runs/2025-02-02T15-00-00-full` are relative to the experiment. Scripts **accept only the descriptive name** (e.g. `de-risk`, `full`); the run path is built with **auto-calculated current datetime** as `runs/YYYY-MM-DDTHH-MM-SS-<descriptive>`. The **training script** (`train.py`) **creates the run directory** (logs/, plots/, checkpoints/, data/) when run, so the experiment is **self-contained**: anyone running the experiment gets the exact same structure without relying on the skill or any external script. See [script-patterns.md](script-patterns.md) for the Typer-based train scaffold. Any **synthetic data generation** scripts also live in `<experiment>/` and run from there.
- **Report** – Reference runs by path (e.g. `runs/2025-02-02T14-30-00-de-risk/logs/train.log`, `runs/2025-02-02T15-00-00-full/plots/loss_curve.webp`). Include whichever runs matter; exclude runs listed in `IGNORED_RUNS.md` (or JOURNAL.md “Ignored runs”).

### Ignoring Failed or Irrelevant Runs (Without Deleting)

To have the coding agent **ignore** certain runs when building plots or the report—while **keeping** those runs on disk for the record—maintain **`IGNORED_RUNS.md`** in the experiment root (or a section **`## Ignored runs`** in JOURNAL.md). List run paths to exclude from analysis, one per line. Examples:

```markdown
# IGNORED_RUNS.md
runs/2025-02-02T15-00-00-full       # run failed; keep logs but exclude from plots/report
runs/2025-02-03T10-00-00-full-abort # aborted run; irrelevant
runs/2025-02-02T14-30-00-de-risk-bad # de-risk run with wrong config
```

**Rule for the agent:** Before generating plots or writing the report, read `IGNORED_RUNS.md` (and JOURNAL.md’s “Ignored runs” section if present). Exclude any run whose path appears there. Do not delete those runs or their files; only omit them from plots, tables, and report narrative.

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
