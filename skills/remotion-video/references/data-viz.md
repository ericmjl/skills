# Data Visualization Dashboard Video

Create an animated data dashboard video from a CSV file. Design and animate charts, KPIs, and trend indicators — no design skills needed.

## Input

User provides a CSV file (place in `public/data.csv`).

## Workflow

### Step 1: Analyze

Read the CSV file. Identify:

- A compelling title for the dashboard
- The single most impressive KPI stat (for the hero card)
- Data suitable for a bar chart (categorical comparison)
- Data suitable for a donut/pie chart (parts of a whole)
- Data suitable for a line chart (trend over time)

If the CSV doesn't have all 4 chart types, pick the best 4 visualizations for the data and adapt.

Present the proposed dashboard layout. **Wait for approval** before coding.

### Step 2: Animate

Build 4 panels in a vertical stack (15 seconds total).

**Layout**: Vertical stack with 30px padding between panels. Top margin 150px (safe zone), bottom panel ends above 170px (safe zone). Side margins 60px. Dark background `#0a0a0a`.

**PANEL 1 — KPI Hero Card**:
- Large headline number counting up from 0 using `interpolate()`, with suffix (%, $, k, M)
- Subtitle describing the metric, Inter 400, 20px, `#94a3b8`
- Trend indicator: colored arrow (green up or red down) with change, slides in after count finishes
- Glass-morphism card: `rgba(255,255,255,0.05)`, border 1px solid `rgba(255,255,255,0.1)`, backdrop-blur
- `tabular-nums` font-variant for smooth counting
- Entrance: card scales from 0.8 to 1.0 with spring at frame 10

**PANEL 2 — Bar Chart**:
- Horizontal bars, one per category, using real labels and values from CSV
- Each bar grows from width 0 using `spring({ damping: 200, delay: index * 10 })`
- Bar colors: gradient from `#6366f1` to `#8b5cf6`
- Labels on left, values appear at bar end after growth completes
- Rounded-right corners (8px)
- Entrance: staggered, starting at frame 25

**PANEL 3 — Donut Chart**:
- SVG donut using `stroke-dasharray` / `stroke-dashoffset`
- Segments draw clockwise, each starting after previous finishes
- Colors: `#3b82f6`, `#22c55e`, `#f59e0b`, `#ef4444` (cycle if more segments)
- Radius 80px, stroke-width 24px
- Center text: category name swaps as each segment draws
- Colored legend dots below, staggered fade-in
- Entrance: starts at frame 50

**PANEL 4 — Line Chart**:
- SVG polyline drawing left to right via `stroke-dashoffset` + `interpolate()`
- Data point circles (r=4) pop in with scale spring as line reaches them
- Gradient fill below line (color to transparent) reveals with the draw
- Axis labels from CSV data
- Line color: `#22c55e`
- Entrance: starts at frame 70

**Global elements**:
- Dashboard title (from analysis) fades in at frame 0, top safe zone, Inter 800, 36px
- Source subtitle fades in at frame 5, Inter 400, 16px, `#64748b`
- All panels use matching glass-morphism card style

**Reusable components to create**:
- `CountUp` — accepts `from`, `to`, `durationInFrames`, `suffix`
- `AnimatedBar` — accepts `width`, `delay`, `label`, `value`
- `DonutSegment` — accepts `percentage`, `color`, `delay`
- `AnimatedLine` — accepts `points`, `drawDuration`

## Visual Style

Dark theme from `defaults.md`. Chart colors: `#6366f1` / `#8b5cf6` gradient for bars, `#22c55e` for line, `#3b82f6` / `#22c55e` / `#f59e0b` / `#ef4444` for donut.

## Duration

15 seconds. 4 panels.

## Output

- Remotion composition at 1080x1920, 30fps
- Launch `npx remotion studio` for preview
