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
# dependencies = ["torch", "numpy"]
# ///
"""Train for a few epochs; log metrics to JSONL."""
import json
import sys
from pathlib import Path

def main():
    # 1. Load config / data (small subset for fast iteration)
    # 2. Build model (same architecture, possibly smaller)
    # 3. For each epoch/step: train, compute metrics
    # 4. Write one JSON object per line to e.g. train.jsonl
    #    e.g. {"epoch": 1, "step": 100, "loss": 0.5, "accuracy": 0.82}
    log_path = Path("train.jsonl")
    with open(log_path, "w") as f:
        for epoch in range(n_epochs):
            # ... training step ...
            f.write(json.dumps({"epoch": epoch, "loss": loss, ...}) + "\n")

if __name__ == "__main__":
    main()
```

### Evaluation

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "numpy"]
# ///
"""Evaluate model; log metrics to JSONL for report and plots."""
import json
from pathlib import Path

def main():
    # Load model and eval data (or subset)
    # Compute metrics that match success/failure criteria
    # Write one line per run or per split, e.g. eval.jsonl
    with open("eval.jsonl", "w") as f:
        f.write(json.dumps({"split": "val", "accuracy": 0.85, "f1": 0.82}) + "\n")

if __name__ == "__main__":
    main()
```

### Plot from Logged Data

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib", "pandas"]
# ///
"""Generate plot only from existing log file. Do not invent data."""
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def main():
    log_path = Path("train.jsonl")
    if not log_path.exists():
        raise SystemExit("Error: train.jsonl not found. Run training script first.")
    rows = [json.loads(line) for line in log_path.read_text().strip().split("\n")]
    # e.g. plot epoch vs loss
    df = pd.DataFrame(rows)
    plt.figure()
    plt.plot(df["epoch"], df["loss"], label="loss")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.legend()
    plt.savefig("loss_curve.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    main()
```

## Conventions

- **One main script per purpose** – e.g. `train_small.py`, `eval.py`, `plot_curves.py`. Duplicate and rename for new experiments.
- **No hidden state** – Prefer explicit paths and args (argv or argparse) over hardcoded project roots.
- **Fail fast** – Validate inputs and required files at startup; print clear errors to stderr.
- **Log to files** – Write JSONL/CSV to the experiment directory so plots and reports can cite them.
