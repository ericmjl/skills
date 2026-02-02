# Script Patterns

All experiment scripts use **PEP723 inline script metadata** and are run with **`uv run script.py`** when using uv, or with **`pixi run`** (e.g. `pixi run python train.py de-risk`) when pixi is the environment manager. When using pixi, define the environment in **`pyproject.toml`** (under `[tool.pixi]`) or **`pixi.toml`**; prefer running scripts inside a **GPU-enabled environment** (CUDA-enabled deps in that config) wherever possible.

**CWD = experiment directory.** Scripts are written assuming the current working directory is the experiment root (`<experiment>/`). All paths (e.g. `runs/2025-02-02T14-30-00-de-risk`, `runs/2025-02-02T15-00-00-full`) are relative to that. Run names are **full ISO datetime + descriptive string**: **`YYYY-MM-DDTHH-MM-SS-<descriptive-string>`** (time with hyphens for filesystem-safe dirs). Scripts **accept only the descriptive name** (e.g. `de-risk`, `full`); the run path is built with **auto-calculated current datetime** as `runs/YYYY-MM-DDTHH-MM-SS-<descriptive>`. Do not hardcode the descriptive string. The **training script** (e.g. `train.py`) is the **only** script that **creates the run directory** (logs/, plots/, checkpoints/, data/); eval and plot target an existing run (run path as argument). Use **Typer** for all experiment scripts—no sys.argv. The experiment is **self-contained**: anyone running it gets the same structure without relying on the skill. See the Typer-based train scaffold below.

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
#     "torch",  # or "tensorflow", "jax", etc. — respect user's framework
# ]
# ///
```

- List only dependencies actually used in the script.
- Use `requires-python` to match the experiment environment.
- Document in SKILL.md or JOURNAL.md that scripts are run with `uv run script.py` or, when using pixi, `pixi run python script.py` (within a GPU-enabled environment where possible).

**PyTorch GPU example (uv):** use `[[tool.uv.index]]` so `uv run` resolves `torch` from the CUDA wheel index:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "typer", "loguru"]
# [[tool.uv.index]]
# url = "https://download.pytorch.org/whl/cu121"
# ///
```

## Dependencies: respect framework, prefer GPU-enabled

**Respect the user's training framework.** Do not hardcode PyTorch (or JAX, TensorFlow, etc.). Use whichever framework the user prefers for training and evaluation.

**Prefer GPU-enabled installs for training and evaluation.** Scripts that train or evaluate models must be **performant**; use GPU-enabled library variants when available. Only fall back to CPU-only when GPU-enabled is not available (e.g. no GPU, or install fails).

- **JAX** – Use GPU extras in the script deps, e.g. `jax[cuda12]` or `jax[cuda11]` (or `jax[cuda12_pip]` per [JAX install](https://jax.readthedocs.io/en/latest/installation.html)). If no GPU, fall back to `jax`.
- **PyTorch** – PEP 723 allows a `[tool]` table; uv supports custom index URLs in inline script metadata via `[[tool.uv.index]]`. For GPU builds, add the PyTorch CUDA index in the script block, e.g. `[[tool.uv.index]]` with `url = "https://download.pytorch.org/whl/cu121"` (or the CUDA version that matches the environment), and list `torch` in `dependencies`. If no GPU, omit the index and use default `torch` (CPU) from PyPI.
- **TensorFlow** – Use `tensorflow` (includes GPU support when CUDA/cuDNN are present). For GPU-only envs, `tensorflow` is typically sufficient.
- **Other frameworks** – Prefer the GPU-enabled or CUDA-backed variant in dependencies when the ecosystem provides one; otherwise document the install step for GPU.

In the train and eval script scaffolds, **use the user’s chosen framework** and the **GPU-enabled variant** in the dependency list (or the documented install) so that `uv run train.py ...` / `uv run eval.py ...` or `pixi run python train.py ...` (when using pixi) use GPU when available. **Priority: run in a GPU-enabled environment** (uv with CUDA index or jax[cuda*], or pixi env with GPU deps in pyproject.toml / pixi.toml) wherever possible.

## Train script scaffold (Typer, self-contained)

The **training script** lives in the experiment and **creates the run directory** when run. Use this pattern so the experiment is self-contained: a human (or agent) running the experiment gets the exact same structure without depending on the skill. Typer for CLI; descriptive name only; datetime auto-calculated; run dir created with logs/, plots/, checkpoints/, data/.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "loguru", "numpy"]
# # Use GPU-enabled framework when available: e.g. jax[cuda12], or install torch from PyTorch CUDA index
# # Add the user's framework here (torch, jax, tensorflow, etc.)
# ///
"""Train script: accepts descriptive name, creates run dir, logs to run's logs/."""
from datetime import datetime
from pathlib import Path
import json
import sys
import typer
from loguru import logger

app = typer.Typer()

def _run_dir(descriptive: str) -> Path:
    iso = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    return Path("runs") / f"{iso}-{descriptive}"

@app.command()
def main(
    name: str = typer.Argument(..., help="Descriptive name for this run (e.g. de-risk, full)."),
) -> None:
    run_dir = _run_dir(name)
    if run_dir.exists():
        typer.echo(f"Error: {run_dir} already exists.", err=True)
        raise typer.Exit(1)
    for sub in ("logs", "plots", "checkpoints", "data"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(run_dir / "logs" / "train.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    logger.add(sys.stderr, format="{time:HH:mm:ss} | {message}")
    # --- your training loop here ---
    # for epoch in range(n_epochs):
    #     ... train step ...
    #     logger.info("metric {}", json.dumps({"epoch": epoch, "step": step, "loss": loss, "accuracy": acc}))

if __name__ == "__main__":
    app()
```

Run from experiment root: `uv run train.py de-risk`. The script creates `runs/YYYY-MM-DDTHH-MM-SS-de-risk/` with logs/, plots/, checkpoints/, data/ and writes logs there. No external scaffold; the experiment is self-contained. **Only the training script creates the run directory**; eval and plot take an existing run path.

## Eval and plot (Typer, existing run only)

Eval and plot **do not create runs**. They take the **run path** (existing run, created by train) as a Typer argument.

**eval.py** – Typer argument: run path. Writes to that run’s `logs/eval.log`.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "loguru", "numpy"]
# # Use GPU-enabled framework when available (same as train.py); add user's framework
# ///
"""Evaluate model; log to run's logs/eval.log. Run dir must already exist (created by train.py)."""
import json
import sys
from pathlib import Path
import typer
from loguru import logger

app = typer.Typer()

@app.command()
def main(
    run_path: str = typer.Argument(..., help="Run path (e.g. runs/2025-02-02T15-00-00-full)."),
) -> None:
    run_dir = Path(run_path)
    if not run_dir.is_dir():
        typer.echo(f"Error: {run_dir} not found or not a directory.", err=True)
        raise typer.Exit(1)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(run_dir / "logs" / "eval.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    logger.add(sys.stderr, format="{time:HH:mm:ss} | {message}")
    # Load model and eval data; compute metrics
    logger.info("metric {}", json.dumps({"split": "val", "accuracy": 0.85, "f1": 0.82}))

if __name__ == "__main__":
    app()
```

**plot_curves.py** – Typer argument: run path. Reads from that run’s `logs/`, writes to that run’s `plots/`.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "matplotlib", "pandas"]
# ///
"""Plot from existing run logs. Run dir must already exist (created by train.py)."""
import json
import re
from pathlib import Path
import typer
import pandas as pd
import matplotlib.pyplot as plt

app = typer.Typer()

@app.command()
def main(
    run_path: str = typer.Argument(..., help="Run path (e.g. runs/2025-02-02T15-00-00-full)."),
) -> None:
    run_dir = Path(run_path)
    log_path = run_dir / "logs" / "train.log"
    if not log_path.exists():
        typer.echo(f"Error: {log_path} not found. Run train.py first.", err=True)
        raise typer.Exit(1)
    rows = []
    for line in log_path.read_text().strip().split("\n"):
        m = re.search(r"metric (\{.*\})", line)
        if m:
            rows.append(json.loads(m.group(1)))
    df = pd.DataFrame(rows)
    (run_dir / "plots").mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.plot(df["epoch"], df["loss"], label="loss")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.legend()
    plt.savefig(run_dir / "plots" / "loss_curve.webp", dpi=150)
    plt.close()

if __name__ == "__main__":
    app()
```

Example: `uv run eval.py runs/2025-02-02T15-00-00-full`, `uv run plot_curves.py runs/2025-02-02T15-00-00-full`.

## Conventions

- **Use Typer for all experiment scripts**—no sys.argv. Only the **training script** creates the run directory; eval and plot take an existing run path.
- **One main script per purpose** – `train.py`, `eval.py`, `plot_curves.py`, `generate_data.py` (synthetic data). All live in `<experiment>/`; run with CWD = experiment directory.
- **Fail fast** – Validate inputs and required files at startup; print clear errors to stderr.
- **Canonical tree** – Each run is `runs/<run_name>/` with subdirs `logs/`, `plots/`, `checkpoints/`, `data/`. Train creates it; eval/plot use it. See [experiment-setup.md](experiment-setup.md) and [logging-guide.md](logging-guide.md).
