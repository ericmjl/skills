# Logging Guide

Use **loguru** for logging. Write to plain-text **`.log`** files (e.g. `train.log`, `eval.log`). **Put logs in the run’s output directory** (e.g. `quick/train.log` for the de-risking run, `full/train.log` for the full run) so quick-run and full-run artifacts are kept separate. Log only what the **hypothesis and success criteria** need; avoid verbose or redundant logs.

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

## Loguru Setup

Add `loguru` to your script dependencies (PEP723) and configure a sink to a `.log` file **in the run’s output directory** (e.g. `quick/` or `full/`):

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["loguru", "torch", "numpy"]
# ///
from loguru import logger
import sys
from pathlib import Path

# Run output dir: quick/ or full/ (e.g. from argv or env)
out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "quick")
out_dir.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(out_dir / "train.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(sys.stderr, format="{time:HH:mm:ss} | {message}")
```

For **metric records** that plotting scripts will parse, use a consistent one-line format per record (e.g. JSON) so you can extract them from the `.log` file:

```python
import json
logger.info("metric {}", json.dumps({"epoch": 0, "step": 0, "loss": 0.693, "accuracy": 0.52}))
logger.info("metric {}", json.dumps({"epoch": 0, "step": 100, "loss": 0.512, "accuracy": 0.71}))
```

That yields a log file (e.g. `quick/train.log` or `full/train.log`) with plain-text lines; plotting scripts can grep for `"metric "` and parse the JSON to build curves.

## Schema Conventions

- **epoch** / **step** – Training progress (integers).
- **loss** / **accuracy** / **f1** – Metric names match what the hypothesis and report use.
- **split** – e.g. `"train"`, `"val"`, `"test"` for evaluation logs.
- **run_id** or **seed** – If you run multiple seeds or configs, include an identifier so plots can separate them.

Keep keys short and consistent across scripts so the same plotting/report logic works for all runs.

## Data-Backed Plots

Only generate plots from **logged data**. If you log epoch and loss to e.g. `quick/train.log` or `full/train.log` (via the `metric` JSON lines above), you may plot loss vs epoch and save in the same run directory (e.g. `quick/loss_curve.webp`, `full/loss_curve.webp`). Do not plot quantities that were not logged; do not invent or interpolate data for display.
