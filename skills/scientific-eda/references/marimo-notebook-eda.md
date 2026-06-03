# EDA in a Marimo notebook

When exploratory data analysis under this skill is done in a **marimo notebook** (rather than with scripts in `scripts/`), the notebook lives at the **analysis folder root** and the same workflow applies (context first, one step, lab notebook, ask why).

## Notebook placement

Marimo notebooks (`.py` files) are primary analytical artifacts and live at the root of the analysis folder, not inside `scripts/`. For example:

```text
analyses/260315-260120_APS052_somatic_sv_exploration/
  lab_notebook.md
  plots/
  scripts/
  sv_haplotypes.py          # marimo notebook
```

## Cell ordering convention

Marimo notebooks follow a consistent cell ordering at the top of the notebook:

1. **First cell: all package imports.** Every `import` statement goes here. When a new dependency is needed later, add it to this cell rather than importing inline elsewhere.
2. **Second cell (after the analysis goal markdown): paths and variables.** Define all file paths, directory locations, and key configuration variables in one place. This makes it easy to adapt the notebook to different data without hunting through cells. **All plot output paths must be defined here** so they are visible and easily editable at the top of the notebook.

This mirrors the convention used in Rmarkdown notebooks (packages block, then paths block) and keeps the notebook's dependencies and data sources immediately visible at the top.

## Variable reassignment

Marimo does **not** allow variable reassignment across cells. The correct way to handle this is to **wrap logic in functions** within the cell. Do **not** use underscore-prefixed variables (e.g., `_df`) to work around this restriction — that is an anti-pattern. Instead:

```python
# GOOD: wrap in a function
@app.cell
def _(raw_df):
    def filter_data(df):
        df = df[df["quality"] > 30]
        df = df.drop_duplicates(subset=["sample_id"])
        return df

    filtered_df = filter_data(raw_df)
    return (filtered_df,)

# BAD: underscore prefix hack
@app.cell
def _(raw_df):
    _df = raw_df[raw_df["quality"] > 30]
    _df = _df.drop_duplicates(subset=["sample_id"])
    filtered_df = _df
    return (filtered_df,)
```

## Plots: save and display inline

Every plot in a marimo notebook must:

1. **Save to WebP** in the analysis `plots/` directory.
2. **Return the figure object** from the cell so it renders inline in the notebook.

The plot output path must be defined in the **paths cell at the top** of the notebook (cell 2), not inline in the plotting cell. This makes it easy for humans to find and edit paths.

```python
# In the paths cell (cell 2):
@app.cell
def _():
    PLOTS_DIR = "plots"
    sv_burden_plot_path = f"{PLOTS_DIR}/sv_burden_by_subtype.webp"
    # ... other paths ...
    return PLOTS_DIR, sv_burden_plot_path

# In the plotting cell:
@app.cell
def _(plt, sv_burden_plot_path, data):
    fig, ax = plt.subplots(figsize=(10, 6))
    # ... plotting code ...
    fig.savefig(sv_burden_plot_path, format="webp")
    fig  # return figure for inline display
```

## Markdown around code cells

Every code cell in the marimo notebook must have markdown that explains it:

- **Before** the code cell: add a markdown cell that states what the code is about to do (intent, question, or step).
- **After** the code cell: add a markdown cell that explains the results (what the output or plot shows, what it means for the analysis).

This keeps the notebook readable and documents intent and interpretation alongside the code.

## Lab notebook integration

Even when using a marimo notebook, maintain the analysis's `lab_notebook.md`. The lab notebook should reference what was done in the notebook and capture key findings and interpretation. The marimo notebook contains the executable code; the lab notebook provides the narrative and decision record.
