# Script Patterns

All experiment scripts use **PEP723 inline script metadata** and are run with:

```bash
uv run script.py
```

Scripts are **disposable**: they are experiment artifacts, not production code. Duplicate and modify as needed for each experiment.

## PEP723 Metadata Block

Place at the top of every Python script:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "pandas",
#     "matplotlib",
#     "torch",  # or "tensorflow", "jax", etc.
# ]
# ///
```

- List only dependencies actually used in the script.
- Use `requires-python` to match the experiment environment.
- Document in SKILL.md or JOURNAL.md that scripts are run with `uv run script.py`.

## Common Patterns

### Data Loading

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Load and optionally subsample data for a fast-iteration run."""
import json
import sys
from pathlib import Path

def main():
    data_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data.csv")
    # Load, optionally subsample (stratified if needed), write subset
    # Keep run time under ~60s; log row counts and any sampling seed.

if __name__ == "__main__":
    main()
```

### Training Loop (Minimal)

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "numpy", "loguru"]
# ///
"""Train for a few epochs; log metrics with loguru to train.log."""
import json
import sys
from pathlib import Path
from loguru import logger

logger.remove()
logger.add("train.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(sys.stderr, format="{time:HH:mm:ss} | {message}")

def main():
    # 1. Load config / data (small subset for fast iteration)
    # 2. Build model (same architecture, possibly smaller)
    # 3. For each epoch/step: train, compute metrics
    # 4. Log metric records so plotting scripts can parse (see logging-guide.md)
    for epoch in range(n_epochs):
        # ... training step ...
        logger.info("metric {}", json.dumps({"epoch": epoch, "step": step, "loss": loss, "accuracy": acc}))

if __name__ == "__main__":
    main()
```

### Evaluation

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "numpy", "loguru"]
# ///
"""Evaluate model; log metrics with loguru to eval.log for report and plots."""
import json
from pathlib import Path
from loguru import logger

logger.remove()
logger.add("eval.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

def main():
    # Load model and eval data (or subset)
    # Compute metrics that match success/failure criteria
    logger.info("metric {}", json.dumps({"split": "val", "accuracy": 0.85, "f1": 0.82}))

if __name__ == "__main__":
    main()
```

### Plot from Logged Data

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib", "pandas"]
# ///
"""Generate plot only from existing .log file. Do not invent data."""
import json
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def main():
    log_path = Path("train.log")
    if not log_path.exists():
        raise SystemExit("Error: train.log not found. Run training script first.")
    # Parse "metric {...}" lines from loguru output
    rows = []
    for line in log_path.read_text().strip().split("\n"):
        m = re.search(r"metric (\{.*\})", line)
        if m:
            rows.append(json.loads(m.group(1)))
    df = pd.DataFrame(rows)
    plt.figure()
    plt.plot(df["epoch"], df["loss"], label="loss")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.legend()
    plt.savefig("loss_curve.webp", dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
```

## Conventions

- **One main script per purpose** – e.g. `train_small.py`, `eval.py`, `plot_curves.py`. Duplicate and rename for new experiments.
- **No hidden state** – Prefer explicit paths and args (argv or argparse) over hardcoded project roots.
- **Fail fast** – Validate inputs and required files at startup; print clear errors to stderr.
- **Log with loguru to .log files** – Use loguru; write to `.log` files in the **run’s output directory** (e.g. `quick/` or `full/`) so quick-run and full-run logs are kept separate (see [experiment-setup.md](experiment-setup.md) and [logging-guide.md](logging-guide.md)).
