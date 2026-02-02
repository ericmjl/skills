# Experiment Setup

## Hypothesis Scoping

A good experiment tests **one** hypothesis. Before running anything:

1. **State the hypothesis** in one sentence: "If X, then Y (measured by Z)."
2. **Define success and failure** – What metric or outcome would confirm or reject the hypothesis?
3. **List metrics to log** – Only those needed to compute success/failure and to explain unexpected results.
4. **Reject scope creep** – If the user describes multiple ideas, pick one or ask them to choose. Do not bundle several hypotheses into one experiment.

### Project Structure

Create an experiment directory with at least:

- `JOURNAL.md` – Observations, anomalies, hunches, TODOs (read before each action).
- Log files (e.g. `train.jsonl`, `eval.jsonl`) – Written by scripts; machine-parseable.
- Scripts – Disposable; PEP723 + `uv run`. Name by purpose (e.g. `train_small.py`, `eval.py`).
- Plots – Generated from logged data only; save alongside logs (e.g. `loss_curve.png`).
- Final report – Scientific structure; see [report-template.md](report-template.md).

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
