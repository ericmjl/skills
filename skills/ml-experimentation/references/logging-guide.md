# Logging Guide

Log only what the **hypothesis and success criteria** need. Avoid verbose or redundant logs.

## What to Log

**Required**

- Metrics that determine success/failure (e.g. loss, accuracy, F1, AUC).
- Identifiers for the run (e.g. epoch, step, split, run_id) so plots and reports can reference them.

**Optional**

- Diagnostics that could explain unexpected results (e.g. per-batch loss, timing, learning rate).
- Resource usage (e.g. wall time, peak memory) if relevant to the hypothesis.

**Avoid**

- Verbose debug logs (e.g. every tensor shape).
- Full model state or gradients unless the hypothesis is about them.
- Intermediate checkpoints unless needed for analysis or reproducibility.

## Format

Use **JSON lines** (one JSON object per line) or **CSV** so logs are machine-parseable and easy to plot.

### JSONL Example

```jsonl
{"epoch": 0, "step": 0, "loss": 0.693, "accuracy": 0.52}
{"epoch": 0, "step": 100, "loss": 0.512, "accuracy": 0.71}
{"epoch": 1, "step": 200, "loss": 0.401, "accuracy": 0.78}
```

- One line per record; no pretty-printing.
- Use consistent keys across lines so plotting scripts can rely on them.
- Save to a stable path (e.g. `train.jsonl`, `eval.jsonl`) so plots and the report can cite the file.

### CSV Example

```csv
epoch,step,loss,accuracy
0,0,0.693,0.52
0,100,0.512,0.71
1,200,0.401,0.78
```

- One header row; one row per record.
- Use for small, tabular metrics; JSONL is often easier for nested or variable keys.

## Schema Conventions

- **epoch** / **step** – Training progress (integers).
- **loss** / **accuracy** / **f1** – Metric names match what the hypothesis and report use.
- **split** – e.g. `"train"`, `"val"`, `"test"` for evaluation logs.
- **run_id** or **seed** – If you run multiple seeds or configs, include an identifier so plots can separate them.

Keep keys short and consistent across scripts so the same plotting/report logic works for all runs.

## Data-Backed Plots

Only generate plots from **logged data**. If you log `epoch` and `loss` to `train.jsonl`, you may plot `loss` vs `epoch` and save as e.g. `loss_curve.png`. Do not plot quantities that were not logged; do not invent or interpolate data for display.
