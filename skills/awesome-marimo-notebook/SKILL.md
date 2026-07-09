---
name: awesome-marimo-notebook
description: >
  Build an awesome marimo notebook that brings a research paper or dataset to
  life — for competitions, tutorials, demos, or blog companions. Use when asked
  to "make an awesome marimo notebook," "build a notebook for this paper,"
  "create a competition submission," or pair-program an interactive research
  explainer on molab. Covers: what makes a notebook engaging (intuition game,
  real experiment, novel extension, design system), paper selection, narrative
  arc and proportions, custom anywidget patterns, wigglystuff CellTour,
  effective GPU usage, memory-efficient training (fused STE, gradient
  checkpointing), parallel review subagents, and a pre-publication polish
  checklist. CRITICAL: mo is auto-injected (import in
  ONE cell); every top-level name must be unique across ALL cells; custom
  anywidget needs model.save_changes(); use mo.output.replace() for live charts;
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
`_model` is treated as private and does NOT propagate. Use clean public names
(`vis_model`).

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

```python
class MyWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      el.innerHTML = '<button>Click</button>';
      el.querySelector('button').addEventListener('click', () => {
        model.set('value', model.get('value') + 1);
        model.save_changes();  // CRITICAL: without this, Python never sees the change
      });
      model.on('change:value', () => { /* update DOM on Python->JS */ });
    }
    export default { render };
    """
    _css = ".my-widget { font-size: 1.2rem; }"
    value = traitlets.Int(0).tag(sync=True)

widget = mo.ui.anywidget(MyWidget(value=42))  # wrap for marimo reactivity
widget  # last expression = cell output
```

**Key gotchas:**
- `model.save_changes()` is REQUIRED for JS->Python trait sync — without it,
  `.value` never updates and downstream cells don't re-run.
- `_esm` and `_css` are anywidget's required attribute names (cannot rename).
- Wrap in `mo.ui.anywidget()` — bare AnyWidget instances may not render.
- Read the widget's value downstream via `widget.value`.

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
