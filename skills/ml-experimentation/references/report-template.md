# Report Template

Use this structure for the final experiment report. **No hallucination**: only reference data that was actually collected (log files, tables, figures). **No editorialization**: state what happened and what the data show; do not state what you wish had happened.

---

# [Experiment Title]

## Abstract

[1–2 sentences: what was tested (hypothesis), key result (e.g. confirmed/rejected, main metric). No interpretation beyond the stated result.]

## Introduction

[Background: why this hypothesis matters. Hypothesis statement: "We tested whether …" or "If X, then Y (measured by Z)." Success/failure criteria.]

## Methods

[Data: source, size, preprocessing, subset used for fast iteration if applicable. Model: architecture, hyperparameters. Training: procedure, epochs/steps, optimizer. Evaluation: metrics, splits. Cite script names and run paths (e.g. `runs/2025-02-02T14-30-00-de-risk`, `runs/2025-02-02T15-00-00-full`).]

## Results

[Tables and figures with captions. Present numbers and plots only; no interpretation here. Reference runs by path (e.g. `runs/2025-02-02T14-30-00-de-risk/logs/train.log`, `runs/2025-02-02T15-00-00-full/plots/loss_curve.webp`).]

**Table 1.** [Caption describing the table.]

| Metric | Value |
|--------|-------|
| …      | …     |

**Figure 1.** [Caption describing the figure and the data source, e.g. "Training loss vs epoch (source: runs/2025-02-02T15-00-00-full/logs/train.log)."]

## Discussion

[Interpretation: what the results mean for the hypothesis. Limitations: data size, runtime, assumptions. JOURNAL.md highlights: anomalies, resolved issues, or hunches that affected the experiment. Do not invent results or overstate conclusions.]

## Conclusion

[Did the hypothesis hold? One sentence. Next steps if any (e.g. full-scale run, different metric). No new claims; only summarize what was shown in Results and Discussion.]
