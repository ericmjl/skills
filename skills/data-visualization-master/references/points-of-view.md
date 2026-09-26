# Nature Methods "Points of View" — distilled guidance

The complete corpus of the *Points of View* column series on data
visualization, *Nature Methods* (2010–2016), written by Bang Wong, Martin
Krzywinski, and coauthors (Nils Gehlenborg, Cydney Nielsen, Noam Shoresh,
Rikke Schmidt Kjærgaard, Erica Savig, Alberto Cairo, Marco Streit, Alexander
Lex, Greg McInerny, BJ Hunnicutt). One distillation per column, organized by
the series' own topic groups. Citation keys resolve in `references/sources.md`.

A distillation compresses each column's main guidance; it is not a substitute
for the column. When a rule from this file decides a real chart, the column is
one fetch away at its DOI.

## Foundations

### Design of data figures — [W10-Design] (Wong, 2010)
Figures are decoded through visual cues; choose encodings that match how
accurately readers judge them. Use strong visual cues (position, length) for
the variables the message depends on, and keep decoding effort low: a reader
should extract the pattern, not solve the chart. Tables beat graphs when
precise values matter more than shape.

### Salience — [W10-Salience] (Wong, 2010)
Distinctive visual properties (a unique color, size, or weight) pull the eye
and speed figure reading. Use salience to differentiate graphical symbols and
to mark the element that matters; applying emphasis uniformly destroys it.

### The design process — [W11-Process] (Wong, 2011)
Good design balances self-expression with the audience's needs, applied in a
logical order: define the message and audience, sketch, draft, critique,
refine. Design decisions should trace to a communication goal, not decoration.

### Elements of visual style — [K13-Style] (Krzywinski, 2013)
Strunk & White applied to figures: omit needless ink, keep related things
visually consistent, use parallel structure across panels, and design for the
reader who is skimming. Consistency of symbol, type, and color is what makes a
multi-panel figure feel authored rather than assembled.

### Storytelling — [K13-Story] (Krzywinski & Cairo, 2013)
Relate data to the reader through narrative: establish context, build to the
key comparison, and land on the consequence. Order and emphasis — not more
ink — carry the story.

### Pencil and paper — [W12-Pencil] (Wong & Schmidt Kjærgaard, 2012)
Sketching data or models by hand is a thinking tool: quick, low-commitment
doodles expose design options and structural questions before any code is
written. Iterate on paper where iteration is cheapest.

### Visualizing biological data — [W12-VizBio] (Wong, 2012)
Clear objectives first: decide what the reader must see, then pick encodings
and computational approaches that surface it. Not every question benefits
from visualization; reserve graphical effort for where it changes decisions,
and have visualization practitioners work beside domain researchers.

## Using color

### Color coding — [W10-Color] (Wong, 2010)
Choose colors to avoid bias and artifacts: hue distinguishes categories,
lightness/saturation carry order and magnitude. Keep categorical palettes to
about four hues plus gray; order colors by meaning (e.g., dark = more), and
never let decoration override semantics.

### Color blindness — [W11-Blindness] (Wong, 2011)
Roughly 8% of men and 0.4% of women have color-vision deficiencies, mostly
red-green. Avoid red-green pairs; use the optimized palettes suggested in the
column (blue/orange families); distinguish with lightness and shape as well as
hue. Test figures with a color-blindness simulator.

### Avoiding color — [W11-Avoiding] (Wong, 2011)
Improve clarity by reaching for alternatives to color first: gray scales,
position, labels. Color competes with data for attention; when gray and
position can carry the message, let them. Check print/grayscale legibility.

### Mapping quantitative data to color — [G12-MapColor] (Gehlenborg & Wong, 2012)
For ordered data, use sequential color maps that vary lightness
perceptually-uniformly; reserve hue for segmenting the range. Diverging maps
need a meaningful midpoint (zero, control). Map the data range deliberately —
theoretical range when the reference matters, observed range when contrast
does — and design so the salient regions of the data stand out.

## Elements of a figure

### Typography — [W11-Typo] (Wong, 2011)
Typefaces, sizes, and spacing structure meaning: consistent families, a small
size hierarchy (title > axis labels > annotations), and nothing below
legible-at-print size. Type guides reading order; do not make the reader
guess what to read first.

### Axes, ticks and grids — [K13-Axes] (Krzywinski, 2013)
Navigational elements must be distinct from data and unobtrusive: thin axes,
few and even ticks, light grids. The data layer keeps the highest visual
priority; axes serve reading like signage serves wayfinding.

### Labels and callouts — [K13-Labels] (Krzywinski, 2013)
Figure labels demand the same consistency and alignment as text: place labels
close to the marks they describe, align label grids across panels, and use
callouts only where direct labeling is impossible.

### Plotting symbols — [KW13-Symbols] (Krzywinski & Wong, 2013)
Choose distinct symbol shapes that stay distinguishable when overlapped, and
communicate relationships (open vs filled, size families) deliberately.
Overplotting needs a strategy (transparency, jitter, aggregation), not hope.

### Arrows — [W11-Arrows] (Wong, 2011)
Arrows guide the reader through complex information; use them sparingly,
consistently proportioned, and with a clear referent. Decorative arrows are
noise.

## Composition and layout

### Gestalt principles (part 1) — [W10-Gestalt1] (Wong, 2010)
Proximity, similarity, and connection let viewers infer groups before reading
anything. Arrange elements so related marks sit close, share appearance, or
are physically linked — grouping by perception, not by legend.

### Gestalt principles (part 2) — [W10-Gestalt2] (Wong, 2010)
Continuity, closure, and figure/ground complete the toolkit: align elements on
implicit lines, let readers close partial shapes, and separate figure from
ground with contrast and whitespace. Meaningful arrangement exploits these
perceptual phenomena instead of fighting them.

### Negative space — [W11-NegSpace] (Wong, 2011)
Whitespace is a powerful, free design material: it separates groups, emphasizes
content, and raises perceived quality. Crowded figures are not thorough;
they are unread. Do not fill every region.

### Points of review (part 1) — [W11-Review1] (Wong, 2011)
Worked redesigns showing how layout expresses meaning and how visual structure
should match the message: misaligned panels, competing emphasis, and
decorative structure are fixed by re-composition, not by adding labels.

### Points of review (part 2) — [W11-Review2] (Wong, 2011)
Simple fixes with large payoff for pie charts, scatter plots, and color
scales: order slices meaningfully, fix overplotting with transparency or
aggregation, and give color scales perceptual ordering with clear endpoints.

### Simplify to clarify — [W11-Simplify] (Wong, 2011)
Remove gridlines, borders, boxes, background fills, and redundant legends that
carry no information. Each removal raises the relative salience of the data.
Simplification is the cheapest clarity upgrade.

### The overview figure — [W11-Overview] (Wong, 2011)
The first figure of a paper should convey the study's general concept
economically to a skimming reader: schematic, legible, self-explanatory, with
details delegated to later figures. Design it last, when the story is stable.

### Layout — [W11-Layout] (Wong, 2011)
Proper layout reveals hierarchical relationships: reading order (left-right,
top-bottom), alignment grids, and grouping by whitespace should mirror the
logical structure of the content. Position is information.

### Salience to relevance — [W11-SalienceRelevance] (Wong, 2011)
Make relevant information the most noticeable, not just noticeable: emphasis
must track importance for the task the reader is performing, or attention
lands on the wrong element and the message is lost.

## Multidimensional data

### Into the third dimension — [G12-3D] (Gehlenborg & Wong, 2012)
3D displays are effective for genuinely spatial data and rarely for anything
else: perspective distorts value reading, occlusion hides data, and 2D
encodings of the same data decode faster and more accurately.

### Power of the plane — [G12-Plane] (Gehlenborg & Wong, 2012)
Combine complementary 2D plots (scatter + bar + heatmap panels) to cover
multivariate structure instead of one overloaded plot; coordinated panels
beat dimensional gimmicks.

### Multidimensional data — [K13-Multi] (Krzywinski & Savig, 2013)
Visually organize complex data by mapping them onto familiar representations
of the system (circos-style layouts, hierarchies, biological schematics);
familiar structure is a decoding aid. Introduce unfamiliar encodings only with
training wheels.

## Plot types

### Bar charts and box plots — [SG14-Bars] (Streit & Gehlenborg, 2014)
Match the plot to data nature and task: bars for counts/aggregates, box plots
for distribution summaries (with n shown), raw points when the distribution's
shape matters. Choose per panel, not per habit.

### Sets and intersections — [LG14-Sets] (Lex & Gehlenborg, 2014)
Euler and Venn diagrams are appropriate up to about three sets; beyond that,
use scalable plots (UpSet plots) that read intersection sizes accurately.

### Temporal data — [SG15-Temporal] (Streit & Gehlenborg, 2015)
Use the inherent properties of time — order, duration, interval — in the
encoding; make temporal alignment easy across panels and respect the calendar
structure of the data.

### Heat maps — [G12-Heat] (Gehlenborg & Wong, 2012)
Heat maps earn their density only with support: cluster rows/columns when
structure matters, choose a perceptually ordered colormap, annotate the
colorbar range, and consider parallel coordinates for trajectory questions.

### Networks — [G12-Networks] (Gehlenborg & Wong, 2012)
Choose the network visualization from the pattern you are looking for —
layout for topology, matrix for dense adjacency — and never let a force-
directed hairball stand in for an answer.

### Unentangling complex plots — [MK15-Untangle] (McInerny & Krzywinski, 2015)
Carefully designed subplots scaled to the data usually beat a single complex
overview plot; disentangle by splitting the question, not by decorating the
chart.

### Pathways — [HK16-Pathways] (Hunnicutt & Krzywinski, 2016)
Apply visual grouping principles (proximity, alignment, consistent connectors)
to make information flow legible in pathway diagrams.

### Neural circuit diagrams — [HK16-Neural] (Hunnicutt & Krzywinski, 2016)
Alignment and consistent visual grammar untangle complex circuit diagrams:
one meaning per visual token, connections routed to preserve readability.

### Binning high-resolution data — [K16-Binning] (Krzywinski, 2016)
Aggregate high-resolution data into bins that preserve the features the
message needs; state the binning, and check that bin size does not manufacture
or erase the effect.

### Intuitive design — [K16-Intuitive] (Krzywinski, 2016)
Design for the reader's first five seconds: familiar forms, obvious labels,
and a visual question the figure visibly answers. Intuition is trained on
conventions — respect the conventions your audience already knows.

## Data exploration

### Data exploration — [SW12-Explore] (Shoresh & Wong, 2012)
Create 'slices' of the data — targeted views that each address one question —
to enhance pattern discovery; exploration is a dialogue between questions and
displays, not a single grand chart.

### Representing the genome — [N12-Genome] (Nielsen & Wong, 2012)
Limit what is displayed to what the question needs; genomic context is
bottomless, and disciplined cropping is what keeps a figure decodable.

### Managing deep data in genome browsers — [N12-Browser] (Nielsen & Wong, 2012)
Compaction and summarization (density maps, aggregated tracks) make
overwhelming browser data navigable; show detail only where the question
lives.

### Representing genomic structural variation — [N12-StructVar] (Nielsen & Wong, 2012)
Arcs, color, dot plots, and node graphs each show relations between distant
genomic positions differently; pick by the relation class (orientation,
distance, reciprocal exchange), and say which you mean.

## Points of View, anew (2026– )

Nature Methods reintroduced the series in June 2026, now written by Helena
Jambor (announcement editorial: Nat. Methods 23, 1069,
https://doi.org/10.1038/s41592-026-03143-5). New columns are tracked here as
they become verifiable. Column tracked so far:

### Color scales and the birth of viridis — [J26-Viridis] (Jambor, 2026)

*Abstract-only entry: full text paywalled at verification time (2026-09-26);
distillation pending full-text access.* Publisher abstract: "The color
palette viridis is replacing rainbow color schemes in scientific figures,
for good reason." It echoes the original series' first column [W10-Color]
and is consistent with rule [COL3] in `SKILL.md` (sequential,
perceptually ordered scales for magnitude; never rainbow).
