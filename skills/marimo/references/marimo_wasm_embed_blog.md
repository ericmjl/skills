# marimo wasm embed blog

# Marimo WASM Embed in Blog

Embed interactive marimo notebook cells/outputs as WASM snippets in a static blog
post, so readers get live, linked cells running Python in the browser via Pyodide.

**Read this FIRST.** This taxonomy was distilled after the identical research was
performed across 5 sessions (07-24, 08-01, and subagent variants). Do NOT re-run
web searches for "marimo embed wasm blog" — the answer is below. Only fetch docs
if you need a detail not covered here (exact flag names for a new marimo version).

## The one distinction that matters most

`marimo export html` (STATIC) ≠ `marimo export html-wasm` (INTERACTIVE).

- `marimo export html notebook.py -o out.html` → a **static snapshot**. No Python
  runs in the browser; outputs are frozen. This is the wrong command if the user
  wants interactive cells.
- `marimo export html-wasm notebook.py -o dir --mode run` → a **self-contained
  interactive** bundle. Python runs via Pyodide (WASM) in the browser. Sliders,
  reactive linked cells, plots all work offline, no server. Host the dir, iframe it.

If the user wants "wasm snippets, with marimo cell outputs, you know what I mean"
they want the INTERACTIVE path. The whole-notebook iframe (`export html-wasm`) is
the simplest fully-self-hosted interactive option.

## The 5 embedding approaches

| # | Approach | Granularity | Self-hosted? | Build step | Best for |
|---|----------|-------------|--------------|------------|----------|
| 1 | `marimo export html-wasm` + iframe | whole notebook | YES | one command | full control, no external dep |
| 2 | Marimo islands (`MarimoIslandGenerator`) | individual cells | YES | Python API | weave cells into page prose |
| 3 | `@marimo-team/marimo-snippets` | per code block | NO (marimo.app) | one `<script>` tag | easiest markdown drop-in |
| 4 | molab iframe embed | whole notebook | NO (marimo.app) | none | fastest, couples to marimo.app |
| 5 | self-hosted WASM HTML export | whole notebook | YES | export + serve | same as #1, explicit framing |

### 1. `marimo export html-wasm` (whole-notebook, self-hosted, interactive)

```bash
marimo export html-wasm notebook.py -o build/out --mode run
```

Produces an `index.html` + Pyodide assets in `build/out/`. Serve that dir, then
iframe it from the blog post. Numpy/scipy/matplotlib are pre-installed in Pyodide.
`--mode run` = read-only interactive app; `--mode edit` = full editor. This is the
simplest fully-self-hosted interactive path and matches a blog's existing
iframe-widget pattern (see website-standalone-html-widget).

### 2. Marimo islands / `MarimoIslandGenerator` (cell-level, self-hosted)

```python
from marimo._islands import MarimoIslandGenerator
gen = MarimoIslandGenerator()
gen.add_cell("import marimo as mo; mo.slider(0)")
html = gen.render()  # emit per-cell <marimo-island> elements woven into your HTML
```

Build-time step generates island HTML; runtime loads Pyodide in the browser and
reconnects the cells reactively. This is what powers mdx-marimo, quarto-marimo, and
jupyter-book-marimo. Gives true cell-level weaving (cells sit inline in your prose).
Heaviest integration effort: needs a Python build step + serving the marimo runtime
assets. Early/preview feature — verify current API before relying on it.

### 3. `@marimo-team/marimo-snippets` (per-block, depends on marimo.app)

```html
<script src="https://cdn.jsdelivr.net/npm/@marimo-team/marimo-snippets"></script>
<pre data-marimo>
# your cell source here
</pre>
```

One script tag; it wraps `<pre>` code blocks (or `<marimo-iframe>` tags) into an
interactive iframe. EASIEST drop-in for any SSG, Lektor included (markdown body
allows raw HTML). CAVEAT: it is a wrapper around the **marimo.app online
playground** — the cell source is sent to / loaded from marimo.app, so it is NOT
fully self-hosted (depends on the marimo.app CDN). Fine if you accept that
coupling; not fine if the user wants zero external dependency.

### 4. molab iframe embed (hosted, depends on marimo.app)

Host the notebook on GitHub, iframe:
`https://marimo.app/github/<owner>/<repo>/<path>/notebook.py/wasm?embed=true`.
Fastest, zero build step, but couples the post to marimo.app availability.

### 5. Self-hosted WASM HTML export

Same as #1, named explicitly when the user emphasizes "my own WASM bundle / no
marimo.app dependency." Run `marimo export html-wasm` to a dir under the blog's
static assets, serve it, iframe it. Heaviest payload (Pyodide assets per notebook)
but full control.

## Not applicable to a Lektor blog

`mdx-marimo`, `quarto-marimo`, `jupyter-book-marimo` are for MDX / Quarto /
Jupyter Book hosts ONLY. They all use the islands model (approach #2) under the
hood. Do not propose them for a Lektor (markdown/HTML) blog — but know they exist
as references for the islands integration pattern if you build it manually.

## Recommendation for a Lektor blog (e.g. ericmjl.github.io)

- **Easiest, markdown-friendly, but depends on marimo.app:** approach #3
  (`marimo-snippets`, one CDN script + code blocks). Accept the marimo.app coupling.
- **Fully self-hosted, matches the existing iframe-widget pattern, whole-notebook:**
  approach #1/#5 (`export html-wasm` then iframe the output dir).
- **True cell-level weaving, self-hosted, but needs a Python build step + Lektor
  integration:** approach #2 (`MarimoIslandGenerator`). Most flexible, most work.

For a single embedded interactive demo, default to #1 (export html-wasm + iframe)
unless the user explicitly wants cells scattered through the prose (#2) or the
quickest possible drop-in (#3).

## Verification before shipping

- Run the export locally and open the `index.html` in a browser; confirm the cell
  actually executes via Pyodide (watch the network panel for the Pyodide WASM load).
- Confirm deps used by the notebook are in Pyodide (numpy/scipy/matplotlib yes;
  exotic packages may need `--include-sources` or may be unavailable).
- If iframing, size the iframe height (the website-standalone-html-widget skill's
  `fit()` reset-to-0-then-scrollHeight pattern handles auto-resize).
