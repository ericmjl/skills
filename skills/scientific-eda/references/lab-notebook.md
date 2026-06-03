# Lab notebook convention

Each analysis folder contains a `lab_notebook.md` that serves as the lab notebook entry for that investigation. It is **co-authored** by the user and the agent.

## Structure

The lab notebook follows this structure:

### Goals

What questions this analysis aims to answer. Written or dictated by the user.

### Background

Scientific rationale, hypotheses, and relevant prior work. Written or dictated by the user. Include:

- The main question and why it matters
- Specific hypotheses to test
- Links to prior analyses or notebook pages this builds on

### Code/Data Storage

Links to repos, slides, data locations, and related pipelines. Maintained by both the user and the agent.

### Methods

Numbered, evolving list of what was done. The agent drafts entries after executing code; the user reviews and may revise. Each entry should include:

- What was done and why
- Key decisions and their rationale (e.g., parameter choices, filtering criteria)
- Dead ends and why they were abandoned
- Notes from discussions with collaborators

### Results

Findings, figures, and interpretation organized by sub-analysis. The agent records outputs and references plots; the user adds interpretation and conclusions. Include:

- Descriptions of key plots and tables (reference files in `plots/`)
- What the results mean in context of the analysis goals
- Surprises or unexpected findings

### Conclusions

Key takeaways from the analysis. Written by the user, optionally drafted by the agent.

## Co-authoring rules

1. **The agent never overwrites the user's entries.** Append only.
2. **The agent reads `lab_notebook.md` before each substantive action** to stay aligned with the user's current thinking.
3. **The agent drafts Methods/Results entries** after executing code. These should be clearly identifiable so the user can distinguish agent-drafted text from their own.
4. **The user can write directly** into `lab_notebook.md` at any time — adding interpretation, changing direction, noting conversations with collaborators, or correcting the agent's entries.
5. **Data shape**: after loading or inspecting data, the agent records columns (and types if relevant), row count, and structure in the Methods section.
6. **Timestamps**: use `YYYY-MM-DD` per entry.

## Update triggers

The lab notebook must serve as a **resumption artifact** — any agent or human should be able to pick up the analysis from `lab_notebook.md` alone. Write to it at these specific points:

1. **After plan is established (before touching data):** Write Goals, Background, and an initial Methods outline/plan.
2. **After every new finding:** Append to Results with the plot reference and interpretation immediately after generating a plot or summary.
3. **After any dead end or direction change:** Record what was tried, why it didn't work, and the new direction in Methods.
4. **At natural pauses or before session ends:** Append a "Next steps" note to Methods describing what should be done next, so another agent or future session can resume without loss of context.

## Example skeleton

```markdown
# [Analysis title]

[Author] - [Date created]

## Goals

- [Question 1]
- [Question 2]

## Background

- [Scientific context]
- [Hypotheses]

## Code/Data Storage

- Analyses and data: [link or path]
- Accompanying slides: [link]
- Related pipelines: [links]

## Methods

1. [Step description]
   1. [Sub-step or detail]
   2. [Sub-step or detail]
2. [Step description]

## Results

### [Sub-analysis title]

[Description and interpretation of results]

### [Sub-analysis title]

[Description and interpretation of results]

## Conclusions

- [Takeaway 1]
- [Takeaway 2]
```
