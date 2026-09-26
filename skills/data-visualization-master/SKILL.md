---
name: data-visualization-master
description: >-
  Master skill for creating, critiquing, and improving data visualizations —
  charts, plots, and figures for analysis, publications, blogs, slides, and
  dashboards. Synthesizes the Nature Methods "Points of View" series (Bang
  Wong, Martin Krzywinski, and coauthors) with the evidence-tagged rules of
  the evident-charts skill (Cleveland & McGill graphical perception, Tufte,
  and modern visualization research). Load for any chart/figure/plot request
  in matplotlib, seaborn, plotly, ggplot2, Altair/Vega-Lite, D3, or any other
  visualization library; for "critique this figure", publication-figure and
  multi-panel figure design, color/encoding/layout/typography questions; and
  to consult or extend the literature bibliography that backs every rule.
  This skill is self-improving: a scheduled GitHub Actions research agent
  reads new visualization literature and proposes cited updates as pull
  requests.
license: MIT
metadata:
  author: Eric Ma
  version: "1.0.0"
  sources: "references/sources.md"
---

# Data Visualization Master

The entry-point skill for visualization work. It carries the distilled,
literature-backed principles; the sibling skill `evident-charts` (same repo)
carries the deep rule engine, per-chart-type references, and deterministic
check scripts. When both are installed, use this skill for direction and
`evident-charts` for execution detail. When alone, this skill is sufficient
for sound default decisions.

## What It Does

- Directs any chart-making or figure-critique task through a fixed workflow:
  analyze the data, state the takeaway, choose the form, build, check, review,
  deliver.
- Applies principles from three evidence layers: the Nature Methods
  *Points of View* series (43 columns, 2010–2016, cited per rule), experimental
  graphical-perception research, and practitioner consensus from newsroom and
  statistical-agency style guides.
- Enforces honesty constraints (integrity rules) that may not be broken for
  aesthetics.
- Maintains a literature-backed bibliography (`references/sources.md`) that a
  scheduled research agent extends via pull requests — see
  `references/research-protocol.md`.

## Usage

- Any visualization request: load this skill first. State the takeaway before
  writing plotting code.
- Chart-specific decisions (chart-type selection tables, palettes, presets,
  lint scripts): open `skills/evident-charts/SKILL.md` if installed.
- "Why does this rule exist?": look up the citation key in
  `references/sources.md`, or the distillation in
  `references/points-of-view.md`.
- Reviewing an automated research PR: follow "Reviewing research PRs" below.

## How It Works

1. **Analyze.** Load the data. Print summary statistics. Confirm units, scope,
   sample sizes, and that parts sum to totals. Check for sentinel codes,
   duplicates, and preliminary last points before any plotting.
2. **Brief.** One line: `Takeaway: <claim the data supports> | Audience:
   <lay/expert> | Destination: <blog/slide/paper/poster/dashboard>`. The
   takeaway becomes the title [MSG1]. Ask at most two questions, only if the
   takeaway is ambiguous.
3. **Choose the form** from the takeaway and data shape, not from habit
   [MSG2]. Comparison → bars/dot plots; trend over ordered time → lines;
   relationship → scatter; composition (few parts) → stacked bars; precise
   lookup → table. Position on a common scale is the most accurately decoded
   encoding; length second; color area and angle last [ENC1].
4. **Build** in the project's stack. Apply the core principles below and the
   scientific-figure rules if the destination is a paper, thesis, or report.
5. **Check.** If `evident-charts` is installed, run its `scripts/check_chart.py`
   (matplotlib) or `scripts/check_palette.py` (any other stack). Otherwise run
   the manual checklist in "Integrity" and "Accessibility" below.
6. **Review the rendered image, never the code.** Look at the actual pixels
   [FIG6]. Fix overlapping/clipped text, labels that don't match data, missing
   units, and legend/label redundancy. Iterate until clean.
7. **Deliver** with: the brief; paths to image + code; analysis choices a
   reader should know (transforms, exclusions, minimum n); data source; alt
   text [A1]; any rule broken and why.

## Core principles

Tags: `[E]` experimental evidence — break only with a stated reason;
`[P]` practitioner consensus — break for a clear reason; `[T]` taste/convention
— bend freely. Citation keys resolve in `references/sources.md`; POV keys are
distilled in `references/points-of-view.md`. A project style guide overrides
`[T]` rules and the house look, never `[E]` integrity rules.

### Message

- MSG1 `[E]` The title states the takeaway, not the topic ("Battery-electric
  share tripled in four years", not "EV sales by country"). Subtitle carries
  qualifications: what, units, when. Cite: [B16], [K18], [A22]; POV: [W10-Design].
- MSG2 `[E]` Pick the chart form from the question the reader must answer.
  Match the form to the task, then simplify [W11-Simplify]. Cite: [CM84],
  [V91], [PSPI21].
- MSG3 `[P]` One chart, one message. Split a figure trying to say three things
  into a panel figure (see "Publication figures"). POV: [W11-Overview],
  [W12-VizBio].

### Encoding

- ENC1 `[E]` Encoding accuracy ranking, best to worst: position on a common
  scale > length > angle/slope > area > volume > color saturation. Reserve
  pies/donuts for the rare single-part-to-whole glance; never for comparison
  or trends. Cite: [CM84], [HB10], [T14]; POV: [W10-Design].
- ENC2 `[E]` Lines only over an ordered axis (usually time). Bars for discrete
  categories. Never connect unordered categories with a line. Cite: [Z99];
  POV: [W10-Design].
- ENC3 `[P]` Encode at most ~4 data dimensions per chart. Beyond that, use
  small multiples instead of stuffing more channels into one plot. Cite:
  [PSPI21]; POV: [G12-Plane], [K13-Multi].

### Color

- COL1 `[E]` Color-blind-safe palettes by default; ~8% of men cannot
  distinguish common red-green pairs. Never encode meaning in red vs green
  alone. Cite: [B12], [M09]; POV: [W11-Blindness].
- COL2 `[P]` At most ~4 categorical hues per chart (plus grays). One accent
  color on gray when a single element is the story. Cite: [HE12], [GAF];
  POV: [W10-Color].
- COL3 `[E]` For quantitative data, sequential colormaps (lightness ramps) for
  ordered data, diverging colormaps anchored on a meaningful midpoint (zero,
  control) for signed data. Never rainbow/jet for magnitude. Cite: [B07],
  [C20]; POV: [G12-MapColor].
- COL4 `[P]` Prefer no color at all when gray + position carries the message;
  color is the loudest channel and competes with the data. POV: [W11-Avoiding].
- COL5 `[P]` Test the figure in grayscale for print destinations. POV:
  [W11-Avoiding], [RDB14 rule 6].

### Layout and composition

- LAY1 `[E]` Gestalt principles do the grouping work: proximity, similarity,
  connection, and enclosure imply relatedness before a single label is read.
  Place related marks close; separate panels clearly. Cite: PSPI21;
  POV: [W10-Gestalt1], [W10-Gestalt2].
- LAY2 `[P]` Negative space is a design element: white space around and inside
  figures directs attention and improves perceived quality. Do not fill every
  region with ink. POV: [W11-NegSpace].
- LAY3 `[P]` Visual hierarchy: the reader's eye should land on the data first,
  then title, then annotation, then axes/grid — in that order. Make
  navigational elements (axes, ticks, grids) visually quiet. POV: [W11-Layout],
  [K13-Axes], [W10-Salience].
- LAY4 `[P]` Simplify to clarify: remove gridlines, borders, boxes, and
  legends that carry no information ("chartjunk"); maximize the data-ink
  share. Cite: [T83], [A22]; POV: [W11-Simplify].

### Text and elements

- TXT1 `[E]` Direct-label the data instead of forcing legend lookups when
  labels fit; drop the legend when direct labels exist. Cite: PSPI21;
  POV: [K13-Labels].
- TXT2 `[E]` Minimum ~12 px text at display size; journal figures: text must
  be legible at final printed column width (typically 8 pt minimum after
  scaling). POV: [W11-Typo].
- TXT3 `[P]` Sans-serif faces for figures; consistent type family across a
  panel set; label weights and sizes create hierarchy. POV: [W11-Typo],
  [K13-Style].
- TXT4 `[P]` Arrows and callouts guide, sparingly and consistently; symbols
  must stay distinct when overplotted. POV: [W11-Arrows], [KW13-Symbols].
- TXT5 `[P]` Axes, ticks, and grids are navigational furniture: unobtrusive,
  consistent, never louder than the data. Light gridlines help reading; heavy
  boxes do not. POV: [K13-Axes]; cite: [HB10].

### Integrity (breakable never)

- INT1 `[E]` Bars start at zero. Truncated bar baselines exaggerate
  differences and deceive a majority of readers even after warnings. Line
  charts may use a non-zero range when stated. Cite: [P15], [C20], [Y21].
- INT2 `[E]` No dual y-axes; no inverted value axes; no 3D effect charts;
  aspect ratio must not distort the perceived effect. Cite: [P15], [F08];
  POV: [G12-3D].
- INT3 `[E]` Show uncertainty when comparing groups or claiming differences:
  intervals or n; never rank tiny samples. Cite: [H20], [CG14], [HRA15];
  POV: [SG14-Bars].
- INT4 `[P]` Every number on a chart must be computed or verified against the
  data; name the real data source; flag preliminary values. Cite: evident-charts
  H11, H17, SRC1.

### Storytelling and audience

- STO1 `[P]` A figure is an argument, not a data dump: order panels and
  emphasis so the reader arrives at the intended conclusion. POV: [K13-Story],
  [W11-SalienceRelevance].
- STO2 `[P]` Sketch by hand before coding when the design is not obvious;
  iterate on paper where iteration is cheapest. POV: [W12-Pencil].
- STO3 `[P]` Design is a process: define audience and message → sketch →
  draft → critique → refine; budget for two critique rounds. POV:
  [W11-Process]; cite: [RDB14 rule 10].

## Publication figures

Extra rules when the destination is a journal, thesis, or technical report:

- FIG1 `[P]` Panels are labeled (a, b, c, …) in reading order; every panel is
  referenced from the caption; panel labels use one consistent style and
  position. POV: [W11-Overview], [K13-Labels].
- FIG2 `[P]` The caption is self-sufficient: a reader who sees only figure +
  caption gets the takeaway, methods needed to decode the display, definitions
  of all symbols/abbreviations, and the statistical basis (n, test, error
  bars) [SG14-Bars], [H20], [CG14].
- FIG3 `[P]` The overview figure: the first figure of a paper carries the
  study's core concept legibly to a skimming reader; detailed evidence lives
  in later figures. POV: [W11-Overview].
- FIG4 `[T]` Figure width targets the journal's column system (single ~89 mm,
  double ~183 mm for Nature journals); export vector (PDF/SVG) for line art,
  ≥300 dpi raster for images; fonts embedded.
- FIG5 `[P]` Redesign pass: compare the draft against the points of review
  checklists — mismatched visual weight, decorative noise, missing units,
  legend distance, unreadable color scales — and fix in one batch.
  POV: [W11-Review1], [W11-Review2].
- FIG6 `[E]` Judge the figure by looking at the rendered pixels, not the code
  that made it. Cite: MatPlotAgent, [Y24].
- FIG7 `[T]` Domain plot conventions win at equals: genome browsers for
  genomic loci, heat maps with clustered rows for expression matrices,
  UpSet/intersection plots beyond three sets. POV: [N12-Genome],
  [G12-Heat], [LG14-Sets].

## Accessibility (always on)

- ACC1 `[E]` Never rely on color alone to carry a distinction: add shape,
  pattern, label, or direct annotation. Cite: WCAG 1.4.1; POV: [W11-Blindness].
- ACC2 `[E]` Text contrast ≥ 4.5:1 against its background; marks ≥ 3:1.
  Cite: WCAG 1.4.3/1.4.11; cite: [C22-Chartability].
- ACC3 `[P]` Provide alt text stating the takeaway and the trend, not
  "a chart of X". Cite: [L22].

## The literature backbone and self-improvement

Every rule above carries a citation key. The key resolves in
`references/sources.md`, which holds verified bibliographic entries — including
the complete Nature Methods *Points of View* corpus (43 columns, all DOIs
resolved via Crossref) and the experimental literature behind the `[E]` tags.
Long-form distillations of the Points of View columns live in
`references/points-of-view.md`.

This skill improves itself on a schedule: a GitHub Actions workflow
(`.github/workflows/dataviz-research.yml`) runs the `pi` coding agent, which
searches the visualization literature, verifies sources, and opens pull
requests proposing cited rule updates. The agent's operating manual is
`references/research-protocol.md`; the run history is `references/research-log.md`.

Reviewing research PRs:

1. Check that every new/changed rule line carries a citation key that exists in
   `references/sources.md`, and every new source entry has a resolvable DOI or
   URL plus a provenance mark (`(2nd)`, `(preprint)`, `[UNVERIFIED]` where
   applicable).
2. Check the diff touches only `skills/data-visualization-master/`.
3. Confirm tag changes are evidence-backed: a rule may move `[T]`→`[P]`→`[E]`
   only with a new citation, and `[E]`→`[T]` only with a stated contradiction
   or retraction.
4. Merge if satisfied; the agent never merges its own PRs.

## Files

| File | Read when |
|---|---|
| `references/points-of-view.md` | Distilled guidance from each Nature Methods Points of View column, with citations |
| `references/sources.md` | Bibliography: full citations and DOIs behind every rule key |
| `references/research-protocol.md` | The research agent's operating manual (also the spec for hand-run literature updates) |
| `references/research-log.md` | Append-only history of research runs and what they proposed |
| `skills/evident-charts/` (sibling) | Deep rule engine: chart-type selection, palettes, presets, check scripts, per-library themes |

## Requirements

- None to read the principles. To run `evident-charts` check scripts: Python 3
  with matplotlib installed in the project (palette check needs Python 3 only).
- To run the research automation: `pi` (Node ≥ 22.19), an Anthropic API key,
  and optionally an Exa API key — configured as repository secrets
  (`ANTHROPIC_API_KEY`, `EXA_API_KEY`); see the workflow file.
