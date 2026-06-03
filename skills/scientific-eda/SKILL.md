---
name: scientific-eda
description: Defensive exploratory data analysis for scientific data (CSV, FASTA, etc.). Context-first, human-guided; one plot at a time, ask why before executing, co-authored lab notebook per analysis, scripts with uv run, WebP plots. Supports marimo notebooks and Rmarkdown. Use when opening data files for EDA or when the user wants guided scientific data exploration.
license: MIT
---

# Scientific exploratory data analysis

This skill guides **defensive**, **human-led** exploratory data analysis on scientific data. The agent does not open files and dump code; it captures problem context first, helps narrow to a single first step, takes instruction from the user, and asks "why?" before executing when the user requests a specific plot or table.

## Usage

Use this skill when the user provides one or more data files (CSV, FASTA, or other scientific formats) and wants to explore or analyze them. **Start by capturing context**—do not load or plot data until the problem (biological, chemical, or data-science question) is clearly stated and the agent is aligned as a guided assistant.

## Requirements

- **uv** for running Python scripts and marimo notebooks. Scripts are run with **`uv run script.py`**, which uses the project's existing environment. If a script requires dependencies not in the project's `pyproject.toml`, add PEP723 inline script metadata to declare them.
- Ability to read the relevant data formats (pandas, BioPython, etc.) via dependencies in the project environment or declared in the script.

## What It Does

1. **Context first** – Capture and record the problem context (what question, what domain) before touching the data.
2. **Single first step** – Help the user narrow to **one** first plot or one first summary (not a barrage of code or plots).
3. **Human-guided execution** – Take instruction on what to do next; when the user says "make this plot" or "give me that table," **ask why** before doing it, then execute.
4. **Analysis folder** – Each investigation is an **analysis**: one folder under `analyses/` (or project-agreed base) with a descriptive name and start date, containing `lab_notebook.md`, `plots/`, `scripts/`, and any notebooks.
5. **Lab notebook** – Co-authored `lab_notebook.md` per analysis: the user writes goals, background, and interpretation; the agent drafts methods and results entries for the user to review.
6. **Scripts, notebooks, and plots** – Throwaway scripts in `scripts/`; notebooks (marimo `.py`, Rmarkdown `.Rmd`) at the analysis folder root; plots saved as **WebP** (not PNG) for small file size.
7. **Suggest next step** – After each action, suggest the most logical next step and let the user decide.

## How It Works

### Phase 1: Capture context (before touching data)

- **Do not** open the data file and start coding or plotting.
- Ask for or confirm: the **problem context**—biological, chemical, or data-science question; what the user hopes to learn or decide; and any constraints (e.g. specific variables, subsets).
- Record this in the analysis's `lab_notebook.md` (see Phase 3). Only after context is recorded and agreed, proceed to inspect data shape and plan the first step.

### Phase 2: Start an analysis

- Create **one analysis folder** under `analyses/` (or a project-agreed base). Name it **`[YYMMDD]_[optional_ID]_descriptive-slug`** on creation. The date is the **creation date** and never changes, even when work resumes on a later day.
  - Example with ID: `analyses/260315_SV-APS-052_somatic_sv_exploration/`
  - Example without ID: `analyses/260315_protein_binding_eda/`
- **Optional notebook ID**: The ID follows the format **`PROJ-INITIALS-NNN`** where:
  - `PROJ` is a 1–4 letter uppercase project code (e.g. `SV`, `BIND`, `PROT`)
  - `INITIALS` identifies the analyst (default: `APS`; other users should set their own)
  - `NNN` is a page number, assigned by the user (eyeball the next available number)
  - The ID is **optional** — analyses without a notebook page ID simply omit it from the folder name.
- **Do not rename folders** when resuming work. The creation date is permanent. Use `ls -lt` or git log to see recent activity.
- **Canonical layout** for each analysis folder:
  - `lab_notebook.md` – co-authored lab notebook for this analysis
  - `plots/` – all figures (WebP only for matplotlib)
  - `scripts/` – disposable scripts that load data, summarize, or make plots
  - Notebooks (marimo `.py`, Rmarkdown `.Rmd`) live at the **analysis folder root**, not inside `scripts/`
- See [references/analysis-structure.md](references/analysis-structure.md) for the canonical tree.

### Phase 3: Lab notebook (co-authored, per analysis)

The `lab_notebook.md` is a **co-authored document** — the user and the agent both write in it. It replaces a traditional lab notebook entry for this analysis.

**Structure** (see [references/lab-notebook.md](references/lab-notebook.md) for the full convention):

- **Goals** – What questions this analysis aims to answer. Written or dictated by the user.
- **Background** – Scientific rationale, hypotheses, relevant prior work. Written or dictated by the user.
- **Code/Data Storage** – Links to repos, slides, data locations, related pipelines. Maintained by both.
- **Methods** – Numbered, evolving list of what was done. The agent drafts entries after executing code; the user reviews and may revise.
- **Results** – Findings, figures, and interpretation. The agent records outputs; the user adds interpretation and conclusions.
- **Conclusions** – Key takeaways. Written by the user, optionally drafted by the agent.

**Co-authoring rules:**

1. The agent **never overwrites** the user's entries. Append only.
2. The agent **reads `lab_notebook.md` before each substantive action** to stay aligned with the user's current thinking.
3. The agent **drafts Methods/Results entries** after executing code, clearly marking them so the user can distinguish agent-drafted text.
4. The user can **write directly** into `lab_notebook.md` at any time — adding interpretation, changing direction, noting conversations with collaborators, or correcting the agent's entries.
5. **Data shape**: after loading or inspecting data, the agent records columns (and types if relevant), row count, and structure in the Methods section. Do this as soon as shape is known and after any major data step.
6. Use **timestamps** per entry (e.g. `YYYY-MM-DD`).

**Update triggers (when to write to `lab_notebook.md`):**

The lab notebook must serve as a **resumption artifact** — any agent or human should be able to pick up the analysis from `lab_notebook.md` alone. Update it at these points:

1. **After Phase 1 (plan established):** Write Goals, Background, and an initial Methods outline/plan before touching data.
2. **After every new finding:** Append to Results with the plot reference and interpretation immediately after generating a plot or summary.
3. **After any dead end or direction change:** Record what was tried, why it didn't work, and the new direction in Methods.
4. **At natural pauses or before session ends:** Append a "Next steps" note to Methods describing what should be done next, so another agent or future session can resume without loss of context.

### Phase 4: Understand shape, then one first step

- **Shape of the data**: Before proposing or making plots, ensure the agent (and user) knows: what columns/fields exist, how many rows/records, and any critical structure. Record this in `lab_notebook.md`.
- **Single first plot (or table)**: Help the user choose **one** first visualization or summary (e.g. one distribution, one overview table). Do not generate many plots at once; get alignment on that single step, then execute.

### Phase 5: Human-guided execution and "ask why"

- **Take instruction**: The user may ask for a specific plot, table, or filter. Execute only after clarity.
- **Ask why before doing**: When the user says "make this plot" or "give me that table," briefly ask **why** (e.g. what decision or question it supports). Then run the script and record the outcome in the lab notebook.
- **After each action**: Suggest the **most logical next step** (one step), and let the user confirm or redirect. Do not auto-execute a long pipeline.

### Phase 6: Scripts (disposable, uv run)

- Throwaway Python scripts live in the analysis's **`scripts/`** folder.
- Run scripts with **`uv run script.py`**, which uses the project's existing environment from `pyproject.toml` and `uv.lock`. Do **not** run raw `python` or paste code in a REPL; the script is the unit of execution.
- **PEP723 inline metadata** is only needed when a script requires dependencies not already in the project environment. Most scripts will not need it.
- Scripts are **throwaway**: they are for this analysis's plots and summaries, not production. Paths in scripts are relative to the analysis folder (e.g. `../../data/file.csv` or as agreed).

### Phase 7: Plots (WebP only for matplotlib)

- Save **all matplotlib (and similar) figures as WebP**, not PNG, to keep image sizes small. Use e.g. `fig.savefig("plots/overview.webp", format="webp")`.
- Write plot files into the analysis's **`plots/`** directory. Name files descriptively (e.g. `distribution_response.webp`, `first_ten_records.webp`).
- Reference these plots in the lab notebook when you record what was done.

### Notebooks

The analysis folder supports multiple notebook formats at its root:

#### Marimo notebooks

When the user conducts EDA in a **marimo notebook** (`.py` file), it lives at the analysis folder root. Follow the same phases above (context first, one step, lab notebook, ask why). In addition:

- **Cell ordering**: The **first cell** contains all package imports. The **second cell** (after the analysis goal markdown) defines all paths and key variables — **including all plot output paths** so they are visible and editable at the top.
- **No variable reassignment**: Marimo does not allow reassignment across cells. Wrap logic in functions within the cell. Do **not** use underscore-prefixed variables (e.g., `_df`) as a workaround.
- **Plots: save and display**: Every plot must (1) save to WebP in `plots/` and (2) return the figure object from the cell for inline display. Plot paths are defined in the paths cell, not inline.
- **Markdown before and after code**: For each code cell, add **markdown cells before and after** that explain what the code does and what the results mean.

See [references/marimo-notebook-eda.md](references/marimo-notebook-eda.md) for the canonical convention.

#### Rmarkdown notebooks

When the user conducts EDA in an **Rmarkdown notebook** (`.Rmd` file), it lives at the analysis folder root. Follow the same phases above. In addition:

- Rmarkdown notebooks should state the **Goal** and **Background** at the top of the document.
- Plots from Rmarkdown can be saved to `plots/` but this is not strictly required since `knitr` embeds figures in the HTML output.
- The `lab_notebook.md` should still reference what was done in the Rmd and key findings.

### "Just one more thing ..."

When the agent has additional clarifying or follow-up questions during an analysis — especially after the user thinks they've finished explaining — lead with **"Just one more thing ..."** (an homage to Lt. Columbo). This applies to follow-up questions in any phase, not just context capture.

## Guardrails

1. **Context before data** – Do not open or analyze the data until the problem context is stated and recorded in the lab notebook.
2. **One first step** – Propose and agree on a single first plot or summary; do not generate a large block of code or many plots in one go.
3. **Ask why** – When the user requests a specific plot or table, ask why (what question or decision it serves) before executing.
4. **Lab notebook as shared memory** – Read and append to the analysis's `lab_notebook.md`; record data shape and findings so the next step is informed. Never overwrite the user's entries.
5. **Scripts via uv run** – No ad-hoc Python; run scripts with `uv run script.py`. Only add PEP723 metadata when the script needs dependencies outside the project environment.
6. **WebP for plots** – Use WebP for matplotlib (and similar) output; do not save as PNG by default.
7. **Suggest, don't assume** – After each action, suggest one logical next step and wait for the user to confirm or change direction.
8. **Marimo notebooks** – When EDA is in a marimo notebook, add markdown cells before and after each code cell to explain intent and results. Never use underscore-prefixed variables to work around reassignment restrictions — use functions instead. All plot paths go in the paths cell at the top (see [references/marimo-notebook-eda.md](references/marimo-notebook-eda.md)).
9. **Rmarkdown notebooks** – When EDA is in an Rmarkdown notebook, state Goal and Background at the top; reference findings in the lab notebook.
10. **Notebooks at root, scripts in `scripts/`** – Notebooks are primary analytical artifacts and live at the analysis folder root. Disposable scripts go in `scripts/`.
