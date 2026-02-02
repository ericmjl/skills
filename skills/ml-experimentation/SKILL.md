---
name: ml-experimentation
description: Conduct machine learning experiments from planning through evaluation and report writing. Use when running ML experiments, testing hypotheses, training models, or writing up results. Covers single-hypothesis scoping, fast iteration loops, targeted logging, JOURNAL.md protocol, data-backed diagnostic plots, and scientific report writing.
license: MIT
---

# ML Experimentation

This skill guides a hypothesis-driven ML experiment life cycle: planning, fast iteration, script execution, targeted logging, journaling, diagnostic visualization, and scientific report writing.

## Usage

Use this skill when the user wants to run an ML experiment, test a model or idea, or write up experiment results. Follow the six phases in order; read [references/experiment-setup.md](references/experiment-setup.md) for hypothesis scoping and the fast-iteration checklist.

## Requirements

- Python 3.11+ with `uv` for running scripts (`uv run script.py`)
- Dependencies declared via PEP723 inline script metadata in each script

## What It Does

1. **Planning** – Extract one testable hypothesis, define success criteria, identify metrics to log, create experiment directory and JOURNAL.md
2. **De-risking** – Keep runs under ~60 seconds; scale down data, epochs, or model size before longer runs
3. **Scripts** – Disposable scripts with PEP723 metadata, run with `uv run`
4. **Logging** – Log only what the hypothesis needs; avoid verbose or redundant logs
5. **Journal** – Read JOURNAL.md before each action; record observations, anomalies, hunches
6. **Plots and report** – Generate plots from logged data only; write a scientific report (abstract, intro, methods, results, discussion, conclusion) with no hallucination or editorialization

## How It Works

### Phase 1: Experiment Planning

- Extract a **single, testable hypothesis** from the user’s goal. Reject vague or multi-part goals; narrow to one claim that can be verified.
- Define **success and failure criteria** before running anything.
- List **metrics to log** that map directly to the hypothesis and criteria.
- Create an experiment directory and add **JOURNAL.md** (see Phase 5).
- See [references/experiment-setup.md](references/experiment-setup.md) for hypothesis scoping and project structure.

### Phase 2: De-risking Loop (Fast Iteration)

- **Target: single run completes in under 60 seconds.** If a run would take longer, scale down first.
- Scale down by: smaller data subset (representative, not just “first N”), fewer epochs, simpler or smaller model, or fewer evaluation steps.
- Sanity-check data loading, training loop, and evaluation on the scaled-down setup before committing to longer runs.
- If something would take > 2 minutes, find a proxy that finishes in under 1 minute.
- Before each run, verify the fast-iteration checklist in [references/experiment-setup.md](references/experiment-setup.md).
- **Store quick-run and full-run outputs separately** (e.g. `quick/` and `full/` subdirectories for logs, plots, and data). Keep both; do not overwrite quick-run artifacts when running the full experiment. See [references/experiment-setup.md](references/experiment-setup.md) for the split.
- To **ignore failed or irrelevant runs** without deleting them: use `IGNORED_RUNS.md` (or a “Ignored runs” section in JOURNAL.md) to list runs to exclude from plots and the report; optionally move runs into an `ignored/` directory so they are excluded by default. See [references/experiment-setup.md](references/experiment-setup.md).

### Phase 3: Script Execution

- All Python scripts use **PEP723 inline script metadata** and are run with `uv run script.py`.
- Scripts are **disposable**: they are experiment artifacts, not production code.
- Use the patterns in [references/script-patterns.md](references/script-patterns.md) for data loading, training, and evaluation.

### Phase 4: Logging (Targeted)

- Log **only what the hypothesis and success criteria need**.
- Required: metrics that determine success/failure (e.g. loss, accuracy, F1).
- Optional: diagnostics that could explain unexpected results (e.g. per-batch stats, timing).
- Avoid: verbose debug logs, full model state, gradients (unless the hypothesis is about them).
- Use **loguru** for logging; write to plain-text **`.log`** files (e.g. `train.log`, `eval.log`).
- See [references/logging-guide.md](references/logging-guide.md) for loguru setup and conventions.

### Phase 5: JOURNAL.md Protocol

- **Before each action** (next run, next script, next analysis): read JOURNAL.md.
- Record: observations, anomalies, unexpected behavior, hunches, follow-ups.
- Add a **timestamp** to each entry.
- Use tags: `[WEIRD]`, `[HUNCH]`, `[TODO]`, `[RESOLVED]` so entries are scannable.
- The journal is the primary memory for the experiment; use it to decide the next step and to inform the Discussion section of the final report.

### Phase 6: Diagnostic Plots and Reporting

**Plots**

- **Before plotting:** Read `IGNORED_RUNS.md` (and JOURNAL.md’s “Ignored runs” section if present); exclude any listed runs from plots. Do not include runs under `ignored/` or `_ignored/` unless asked.
- Generate **only** plots that correspond to **logged data**. Do not invent or assume data.
- Examples: training curves (loss/accuracy vs step/epoch), metric distributions, comparison bars.
- Save plots as WebP (e.g. `loss_curve.webp`) next to the log files they use.
- If you log epoch and loss to e.g. `train.log`, you may generate `loss_curve.webp` from that log; do not plot quantities that were not logged.

**Scientific Report**

- **Before writing:** Exclude runs listed in `IGNORED_RUNS.md` or JOURNAL.md “Ignored runs”, and runs under `ignored/` or `_ignored/`, from the report narrative and figures; do not delete those runs from disk.
- Structure: **Abstract**, **Introduction**, **Methods**, **Results**, **Discussion**, **Conclusion**.
- **No hallucination**: only refer to data that was actually collected (cite log files, tables, figures).
- **No editorialization**: state what happened and what the data show; do not state what you wish had happened.
- Include highlights from JOURNAL.md (e.g. anomalies, resolved issues) in Discussion.
- Use the template in [references/report-template.md](references/report-template.md).

## Guardrails

1. **No long runs without justification** – If a script would take > 2 minutes, either get explicit confirmation or propose a scaled-down run that finishes in under 1 minute.
2. **Journal-first** – Always read JOURNAL.md before suggesting or taking the next action.
3. **Data-backed plots only** – Never generate a plot without corresponding logged data; every curve or point must come from a specified log or file.
4. **Report factuality** – Every claim in the report must be tied to a specific log file, table, or figure; no unsupported claims.
