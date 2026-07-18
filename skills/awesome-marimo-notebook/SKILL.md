---
name: awesome-marimo-notebook
description: >
  Build an awesome marimo notebook that brings a research paper or dataset to
  life — for competitions, tutorials, demos, or blog companions. Use when asked
  to "make an awesome marimo notebook," "build a notebook for this paper,"
  "create a competition submission," or pair-program an interactive research
  explainer on molab. Covers: what makes a notebook engaging (intuition game,
  real experiment, novel extension, design system), paper selection, narrative
  arc and proportions, custom anywidget patterns (bi-directional JS<->Python
  state: JS brushing/selection -> Python region-of-interest; Python variables
  reactively driving JS), wigglystuff CellTour,
  effective GPU usage, memory-efficient training (fused STE, gradient
  checkpointing), parallel review subagents, and a pre-publication polish
  checklist. CRITICAL: mo is auto-injected (import in
  ONE cell); every top-level name must be unique across ALL cells; custom
  anywidget needs model.save_changes() for JS->Python sync; use mo.output.replace() for live charts;
  guard all torch.cuda calls for CPU-only machines.
license: MIT
metadata:
  author: ericmjl
  version: "1.0"
---

# Awesome marimo Notebook

A workflow for building marimo notebooks that people remember — interactive
research explainers that bring a paper, method, or dataset to life. Useful for
competition entries, conference tutorials, blog companions, or standalone demos.

**Related skills:**
- `marimo-pair` — pair-program inside a running marimo kernel (the build tool)
- `marimo-notebook-patterns` — exhaustive gotcha reference for marimo `.py` editing

---

## Principles of an engaging notebook

The most memorable marimo notebooks share five qualities. Aim for all five:

1. **An original tactile interaction** that makes the core idea feel obvious
   *before any math*. A drag-the-parameter game, a visual metaphor the reader
   manipulates. The "aha" should land in the fingers before it lands in the
   equations.
2. **Real code, not description** — ideally the paper authors' own repo, or a
   faithful reimplementation. Readers should be able to trace every result to
   the cell that produced it.
3. **A clearly-labeled original contribution** with its own quantitative
   trade-off. Something you built that goes beyond the paper: an untested
   variant, a new visualization, a side-by-side comparison. Label it explicitly
   ("My extension," "Our contribution") so readers can find it.
4. **At least one custom-built widget** (anywidget with hand-written ESM).
   Stock `mo.ui` sliders are fine for controls, but a bespoke widget — one that
   couldn't exist without your specific insight — is what makes the notebook
   unforgettable.
5. **A coherent design system** — hero banner, hand-authored SVG art,
   consistent color palette reused across every figure, `hide_code=True` on
   most cells. Reads like a designed page, not a code dump.

### Narrative proportions

Allocate screen real estate deliberately:

```
~5%   Editorial hero (banner, SVG art, paper attribution)
~5%   Problem framing (why the status quo is unsatisfying -> ends with a question)
~20%  INTUITION ONLY — interactive game + visual bridge, NO equations
~5%   Math formalization (introduce equations AFTER the reader has the picture)
~30%  Real experiment (decomposed into numbered steps, state flowing between them)
~10%  The paper's algorithm, demonstrated live
~15%  ORIGINAL EXTENSION (honestly flagged, with quantitative trade-off)
~5%   Efficiency / limits analysis (honest, nuanced)
~5%   Close + acknowledgments (AI-tool disclosure)
```

The narrative spine:
> **Hook -> Metaphor -> Math -> Real experiment -> Algorithm -> Original extension -> Trade-off -> Close.**
> Each act opens with a *question*, closes by *naming the formal concept*.

---

## Phase 1: Research

### Pick the right paper

Ideal paper characteristics:

- **Single-thesis core idea** with a clean "one knob" (e.g., replace norm with
  tanh; crush weights to 3 values; drop the noise-level input)
- **High audience pull** (upvotes, name recognition, famous authors)
- **GPU-leverageable** (can run real training/inference, not just theory)
- **Extension opportunities** (the paper doesn't sweep a parameter, doesn't
  test on a certain architecture, doesn't address an obvious follow-up)
- **Fast to a compelling demo** (can train in seconds-minutes on GPU)

### Quality dimensions

A great notebook does well across these dimensions (no weights — just aim
high on each):

| Dimension | What it means |
|---|---|
| Paper engagement | Go beyond the abstract; explore methods/results; deliver a clear takeaway |
| Creativity & impact | Fresh angle; novel visualizations; cross-reference related work |
| Interactivity | Reactive widgets that DRIVE exploration, not just decorate |
| Design & shareability | Polished, self-contained, makes people want to try marimo |
| Code quality | Clean, reproducible, no errors |
| GPU utilization (if applicable) | Meaningful GPU use — measurement, batched ops, appropriate device placement |

**Errors are the #1 engagement killer.** A notebook that errors mid-flow loses
the reader. Test end-to-end before sharing.

---

## Phase 2: Design

Map the paper onto the narrative spine above. Decide early:
- What is the **intuition interaction**? (The tactile widget that makes the
  thesis feel obvious before any math.)
- What is the **centerpiece experiment**? (Something only real compute can do:
  a training race, activation instrumentation, efficiency measurement.)
- What is the **original extension**? (An honest, labeled follow-up the paper
  didn't test. Pick one that reuses the trained model for speed.)
- What is the **design motif**? (One visual element echoed everywhere — e.g.,
  the S-curve for DyT, the tri-color heatmap for BitNet.)

---

## Phase 3: Build

Use the **`marimo-pair`** skill to pair-program inside the running kernel. For
the exhaustive gotcha list (reactive graph, code_mode quirks, triple-quote
collisions, etc.), load **`marimo-notebook-patterns`**. Below are only the
most critical conventions.

### Cell conventions (non-negotiable)

**1. `mo` is auto-injected — import in ONE cell only.** Every other cell uses
`mo` bare. Two cells both doing `import marimo as mo` causes
`MultiplyDefinedNameError`.

**2. Every top-level name must be UNIQUE across ALL cells.** Wrap heavy
computation in a function (`run_experiment()`) so locals are isolated — only
the function name and its output need to be unique. Loop variables like `i`,
`fig`, `ax` collide across cells: namespace by purpose (`frontier_fig`,
`heat_ax`).

**3. NO underscore-prefixed names for anything downstream cells need.**
marimo treats underscore-prefixed variables as PRIVATE — they do not appear
in the cell's defs at all, so they cannot be referenced in ANY form (`_model`
or `model`) from another cell. Use clean public names (`vis_model`) so the
name is available in every cell.

**4. Cells don't auto-execute on creation** — call `ctx.run_cell(cid)` after
`ctx.create_cell(...)`.

**5. Edit through `code_mode`, never the filesystem.** Direct `.py` edits are
silently lost when the kernel saves. Use `ctx.edit_cell(target, code=...)`
with the full new cell body.

**6. Use `skip_staleness_check=True` for batch edits.**

### App-level configuration

```python
app = marimo.App(width="medium", auto_download=["html"])
```

Apply `hide_code=True` on most cells (all plotting/training cells; keep code
visible only in pedagogical cells like the implementation walkthrough).

---

## Phase 4: Widget craft

The custom widget is what makes a notebook unforgettable. Budget time for it
early — don't leave it for the end.

### Custom anywidget pattern

An anywidget is a **bi-directional reactive bridge**: `traitlets` tagged
`sync=True` flow BOTH ways between the browser and the kernel. This is what
makes a bespoke widget powerful — not just "a custom visual," but a channel
for reader actions to become Python variables, and for Python variables to
reshape the visual live.

**The two API calls that make the bridge:**
- **JS → Python:** `model.set('trait', v)` then **`model.save_changes()`**
  pushes a browser-side change into the kernel trait; downstream cells that
  read the widget's value re-run reactively.
- **Python → JS:** the JS reads initial state via `model.get('trait')` in
  `render`; it can also react to later mutations via
  `model.on('change:trait', cb)` — but only needed when the trait mutates on
  a *persistent* instance (see Pattern B).

Decide first which direction the widget serves.

#### Pattern A — JS → Python (the widget is an INPUT)

The reader acts in the browser (brush, drag, select); the action becomes a
Python value downstream cells consume. Wrap in `mo.ui.anywidget()` and read
`.value` in a **different** cell.

Classic case — **brush a scatterplot → save the selection as a region of
interest:**

```python
class BrushScatter(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      const pts = model.get('points');
      // ...draw an SVG scatter of pts with a brush rectangle...
      svg.addEventListener('pointerup', () => {
        model.set('value', pointsInsideBrushRect());  // selection -> Python
        model.save_changes();   // CRITICAL: without this, Python never sees it
      });
    }
    export default { render };
    """
    points = traitlets.List().tag(sync=True)
    value = traitlets.List([]).tag(sync=True)   # filled from JS = the selection

brush = mo.ui.anywidget(BrushScatter(points=[[x, y] for x, y in data]))
brush   # last expression = cell output
```

```python
# DIFFERENT cell — re-runs every time the reader brushes.
roi = brush.value                              # the selected points
mo.md(f"**Region of interest:** {len(roi)} points, mean y = {mean_y(roi):.2f}")
```

`brush.value` returns the widget's synced `value` trait. For a multi-trait
widget, read the specific trait you care about so the cell only re-runs when
that one changes.

#### Pattern B — Python → JS (the widget is a DISPLAY)

A Python control (dropdown/slider) or computed value changes what the widget
shows. The reliable marimo pattern is **recompute-and-reinstantiate**: the
widget's data is a function of Python state; when that state changes, the cell
re-runs and mounts a fresh widget whose `render` reads the new traits at
startup. No `change:` handler is needed because the widget is remounted.

```python
# cell 1 — control
graph_choice = mo.ui.dropdown(["toy", "real-A", "real-B"], value="toy")
graph_choice
```

```python
# cell 2 — reads graph_choice.value (DIFFERENT cell!), rebuilds the widget
data = load_graph(graph_choice.value)
BFSAnimation(nodes_json=json.dumps(data["nodes"]),
             steps_exists_json=json.dumps(data["steps"]),
             target_label=str(data["target"]))   # bare instance — nothing reads it
```

This is exactly **Network-Analysis-Made-Simple `02-paths.py`**: a dropdown
swaps the BFS animation between the toy teaching graph and real sociopatterns
ego subgraphs; each graph's nodes/edges/BFS-steps are computed in Python
(spring layout + step precomputation) and the JS just renders
`model.get(...)` at mount. Use this pattern whenever the data swaps wholesale
(new dataset, new layout) — and pass bulky data as JSON-string traits
(`traitlets.Unicode(json.dumps(data))`, then `JSON.parse(model.get('x_json'))`
in the ESM) rather than relying on object sync.

For a **cheap scalar update that must preserve JS-side state** (current zoom,
play position, scroll), keep the widget mounted and register
`model.on('change:source', handler)` in `render` to mutate the existing DOM in
place when a Python trait changes. For smooth in-place updates *within a single
cell* (live training curves), use `mo.output.replace()` (see "Live-updating
charts").

#### Key gotchas

- **Every trait that crosses the boundary needs `.tag(sync=True)`** — unsynced
  traits never propagate in either direction.
- **`model.save_changes()` is REQUIRED for JS→Python sync** — without it the
  trait never updates and downstream cells don't re-run. The #1 anywidget bug.
- **Reading `.value` must happen in a DIFFERENT cell** from the one that
  created the widget — marimo raises `RuntimeError: Accessing the value of a
  UIElement in the cell that created it is not allowed`. Split into a
  create-cell and a consume-cell.
- **Wrap in `mo.ui.anywidget()` to make an anywidget a marimo UI element.**
  This is REQUIRED to read its `.value` downstream (input widgets). Display-only
  widgets often render bare too (e.g. `BFSAnimation`), but wrapping is always
  safe and is the conventional default for interactive widgets like CellTour.
- **`_esm` and `_css` are anywidget's required class-attribute names** (the
  framework looks them up by those exact names). These are class attributes,
  not cell variables — so the no-underscore rule for shared cell names (rule
  #3) doesn't apply to them.
- **The widget's variable name must be non-underscore** if a downstream cell
  reads it — underscore-prefixed names are cell-private and not shared (rule
  #3), so name it `brush`, not `_brush`.

### wigglystuff CellTour (guided walkthrough)

```python
import wigglystuff
tour = wigglystuff.CellTour(
    steps=[{"cell_name": "hero", "title": "...", "description": "..."}],
    auto_start=False, show_progress=True,
)
mo.ui.anywidget(tour)
```

The `steps` list accepts either `{"cell": <int-index>, ...}` or
`{"cell_name": "<name>", ...}` — use the latter if you name your cells.
Verify all references resolve to existing cells — stale refs silently break
the tour.

#### Code tour description voice

The tour is an **onboarding tool** — the first thing a reader sees when they
open a notebook. Write descriptions that orient, not summarize. The test:
*if someone just opened this notebook for the first time, does this sentence
tell them what section they're in, what their role is, and what to pay
attention to?*

Rules:

1. **Label the section type.** Tell the reader what kind of cell this is:
   "Background section," "Hands-on section," "Reflection section,"
   "Try-it-yourself section," "Wrap-up." This helps them calibrate attention.
2. **Point at what's on screen.** "Look at the two answers above" — not
   "Specialization trades simplicity for focus." The reader has the output
   right in front of them; direct their eyes.
3. **Tell them what to do.** "Fill in blanks to connect the searcher and
   synthesizer" — not "Implement the specialist pipeline." Use plain language
   a first-time reader understands.
4. **Never spoil the punchline.** Discussion and reflection cells should set
   up a question, not hand the conclusion. "Did the extra cost buy better
   evidence?" — not "Specialization improves quality at higher cost."
5. **One to two sentences max.** The tour widget has limited space. If you
   can't say it in two sentences, the cell's markdown should carry the
   detail.
6. **Reference the arc.** Connect back to earlier context: "the
   `search_corpus` tool from Part 3," "the same question from Exercise 4."
   This anchors the notebook in its narrative.

Example (good):

```python
{
    "cell_name": "ex1_header",
    "title": "Exercise 1: wire the specialists",
    "description": "Hands-on section. You fill in blanks to connect two "
        "specialized agents — one that searches, one that synthesizes — "
        "into a single pipeline. The pieces are from Part 5.",
}
```

Example (bad — don't do this):

```python
{
    "cell_name": "ex1_header",
    "title": "Exercise 1: wire the specialists",
    "description": "Implement run_specialist_pipeline — wire SearcherAgent "
        "and SynthesizerAgent into a ResearchOrchestrator.",
}
```

The bad version drops raw class names the reader hasn't seen yet, doesn't
label the section type, and reads like a docstring instead of a guide.

### Live-updating charts

```python
chart = LiveChart()
mo.output.replace(chart)
for step in range(100):
    # ... train ...
    chart.data = new_data
    mo.output.replace(chart)  # native mid-cell output API
    await asyncio.sleep(0.01)
```

`mo.output.replace()` is the native mid-cell output API — more reliable than
cross-cell widget mutation for in-cell live updates.

### Plotly charts

Prefer `plotly` over matplotlib — renders natively and interactively in
marimo. Use a consistent 5-color palette and `paper_bgcolor="white"` across
all figures for a cohesive, designed look.

---

## Phase 5: GPU strategy

### Device placement

```python
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
runtime_gpu = torch.cuda.get_device_name(0) if DEVICE.type == "cuda" else "CPU"
```

Always guard `torch.cuda.*` calls with `DEVICE.type == "cuda"` — readers may
open the notebook on CPU-only machines, and an unguarded `get_device_name(0)`
crashes mid-narrative.

### Using GPU compute effectively

Go beyond "I trained on GPU." The most compelling angle: load a real
pretrained model and *empirically measure* the paper's core claim on its
internals — activation distributions, throughput, FLOPs, memory. Present as:
"The paper predicted this. Here it is, measured."

Other strong GPU moves:
- **Live A/B race** — two/three variants training side-by-side, loss curves
  updating in real time.
- **Reactive re-inference** — pretrain-once-cache-checkpoints, then let the
  reader flip one knob and re-run inference instantly without retraining.
- **Efficiency as a result** — if the paper removes/reduces computation,
  measure the real wall-clock + memory delta and present it as a headline.

### Measuring GPU usage

```python
torch.cuda.reset_peak_memory_stats()
# ... work ...
peak_gb = torch.cuda.max_memory_allocated() / 1e9
throughput = n_samples / elapsed_seconds
```

Present these as stat-card dashboards — concrete numbers make the GPU usage
tangible.

### Memory-efficient training

When fine-tuning at scale, the autograd graph is the memory killer:

1. **Fused autograd Function** — combine round/clamp/scale into one
   `torch.autograd.Function` with in-place forward, reducing intermediates:

```python
class FusedSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, w):
        gamma = w.abs().mean() + 1e-8
        q = w / gamma
        q.round_().clamp_(-1, 1).mul_(gamma)
        return q
    @staticmethod
    def backward(ctx, grad):
        return grad  # STE: pass-through
```

2. **Gradient checkpointing** — `model.gradient_checkpointing_enable()`.
3. **Gradient clipping** — `clip_grad_norm_(params, 1.0)` prevents divergence
   in STE/QAT training (numerically sensitive).
4. **Clear resident models** before heavy cells:
   `gc.collect(); torch.cuda.empty_cache()`.

### CUDA OOM recovery

CUDA OOM **poisons the kernel** — all subsequent CUDA ops fail until restart.
There is no in-code recovery. Prevention:
- Monitor peak VRAM after the first training step.
- Use `bf16` weights + `torch.autocast` for training to halve VRAM.
- Train once, cache checkpoints; reactive cells re-*infer*, never re-*train*.

---

## Phase 6: Review & refine

After the notebook is built, dispatch 2-3 read-only review subagents in
parallel, each with a distinct focus:

1. **Structure & flow** — logical top-to-bottom argument? Explicit
   transitions? Redundancy between sections?
2. **Coherence & claims** — contradictions across cells? Numbers consistent?
   Claims that overstate the evidence? LaTeX rendering bugs?
3. **Quality & engagement** — how does it score on each quality dimension?
   Extensions clearly flagged? Interactive widgets drive exploration? Code
   reproducible?

Each agent reads the notebook dump (cell-by-cell `.txt`) + this skill.
They report findings; you consolidate and apply fixes.

### Common fixes after review

- **Reorder sections** to match the narrative arc (`ctx.move_cell`).
- **Delete redundancy** (two cells showing the same curve).
- **Label extensions** explicitly — readers can only appreciate what they can
  find.
- **Reconcile numbers** — if cell A says "30k" and cell B says "19k" for the
  same metric, pick one and use it everywhere.
- **Fix LaTeX** — use raw strings (`mo.md(r"""...""")`) so `\t` doesn't
  become a tab.
- **Add CPU guards** — `if DEVICE.type == "cuda"` before all `torch.cuda.*`.
- **Verify CellTour** — all `cell_name` references resolve.
- **Merge related visuals into one plot** — when two cells show DIFFERENT but
  related aspects of the SAME underlying diagram (e.g. a point-marker selection
  AND a window band on the same ruler plot, both driven by the same controls),
  combine them into ONE cell/plot so the viewer sees the relationship. Splitting
  related aspects across cells fragments understanding; one combined plot makes
  the interaction cohesive. (User correction, 07-15.)
- **Verify SVG label/axis clipping** — in hand-authored SVG (row labels, axis
  ticks), `text-anchor="end"` labels extend LEFTWARD from the anchor and clip
  if the left margin is narrower than the label width (`response_locked` shows
  as `ponse_locked`); bottom axis labels need bottom padding. Always check the
  RENDERED output for clipped text, not just the SVG source. (07-15.)

---

## Phase 7: Polish

### Pre-publication checklist

- [ ] **0 errors** — run all cells end-to-end.
- [ ] **App config** — `width="medium"`, `auto_download=["html"]`.
- [ ] **hide_code=True** on most cells (keep pedagogical code visible).
- [ ] **No underscore-prefixed names** anywhere downstream (scan with regex).
- [ ] **CellTour** — all references valid, correct page order.
- [ ] **Numbers consistent** — same metric cited identically across cells.
- [ ] **LaTeX renders** — use raw strings; check `\text`, `\times`.
- [ ] **CPU guards** on all `torch.cuda.*` calls.
- [ ] **VRAM note** — if a cell needs >40 GB, note it + add graceful skip.
- [ ] **AI disclosure** — note in the close cell if AI tools were used.

### Biggest engagement-killers

1. **Unlabeled extensions** — readers can't appreciate what they can't find.
2. **Errors or missing deps** — breaks the reading flow instantly.
3. **Decorative widgets** — if a widget doesn't drive exploration, it's noise.
4. **No sense of compute** — if you used a GPU, make it tangible (numbers,
   measurements, not just "trained on GPU").

---

## Dependencies

This skill assumes:
- **`marimo-pair`** skill — pair-programming inside a running kernel (the build tool)
- **`marimo-notebook-patterns`** skill — exhaustive marimo gotcha reference
- Python packages: `anywidget` + `traitlets` (widgets), `wigglystuff`
  (CellTour — install via `ctx.packages.add("wigglystuff")`), `plotly`
  (charts), `torch` (GPU experiments), `transformers` (language model
  experiments)

## celltour-granularity

- CellTour GRANULARITY: target **~7-12 stops at "main beats" granularity** — NOT
  15-25 (that range was tried and rejected as "going too overboard"). The
  evolution on Network-Analysis-Made-Simple (07-12): 6 steps → too few ("the
  tour should follow the story of the notebook"); 23 steps → too many ("now
  that's going too overboard. we want main points, coherent narrative flipping
  through stops"); 9-12 stops → "ok, great, this granularity is much better."
  Each stop is a MAIN NARRATIVE BEAT (hero, dataset intro, core concept, key
  exercise, generalization, distribution/viz, key insight, optional extension,
  recap), never a micro-step.

- CellTour AUTHORING RULES (from Network-Analysis-Made-Simple 07-12): (1) Cell 0
  is ALWAYS the hero (first stop); (2) Cell 1 is ALWAYS the CellTour itself
  (SKIP it — never reference it as a tour stop); (3) Target markdown section
  headers, key code cells, exercises, and interactive widgets; (4) Each
  description = ONE sentence about what the reader should learn at that stop;
  (5) Steps follow the notebook's reading order, not jumping around.

- CellTour VERIFICATION: after writing steps, dump each cell index + first
  meaningful line (a script counting `@app.cell` decorators from 0) to confirm
  every cell index matches its title/description. When asked to populate
  CellTours across a series of notebooks, apply these rules consistently to ALL
  notebooks in the series.
