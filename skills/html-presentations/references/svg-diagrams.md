# SVG Diagram Patterns

All diagrams use the `.diagram-*` CSS classes from the base layout, so they inherit the active theme automatically. Every SVG that includes arrows needs the shared `<defs>` block (see SKILL.md Step 4).

## Shared `<defs>` block

Include this once per SVG element that uses arrows or drop shadows:

```html
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto-start-reverse">
    <polygon points="0 0, 10 3.5, 0 7" fill="var(--diagram-arrow)" />
  </marker>
  <marker id="arrow-accent" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto-start-reverse">
    <polygon points="0 0, 10 3.5, 0 7" fill="var(--diagram-stroke)" />
  </marker>
  <filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">
    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
  </filter>
</defs>
```

## Flowchart

Use for decision trees, process flows, approval workflows.

**Node types:** rounded rects for start/end, standard rects for process steps, diamonds for decisions.

```html
<svg viewBox="0 0 800 320" xmlns="http://www.w3.org/2000/svg">
  <!-- defs (arrowheads + shadow) -->
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto-start-reverse">
      <polygon points="0 0, 10 3.5, 0 7" fill="var(--diagram-arrow)" />
    </marker>
    <marker id="arrow-accent" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto-start-reverse">
      <polygon points="0 0, 10 3.5, 0 7" fill="var(--diagram-stroke)" />
    </marker>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
    </filter>
  </defs>

  <!-- Start node (pill shape) -->
  <rect class="diagram-node" x="20" y="120" width="130" height="55" rx="27" filter="url(#shadow)" />
  <text class="diagram-label" x="85" y="148">Start</text>

  <!-- Arrow -->
  <line class="diagram-edge" x1="150" y1="148" x2="200" y2="148" marker-end="url(#arrow)" />

  <!-- Process node -->
  <rect class="diagram-node" x="200" y="120" width="140" height="55" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="270" y="148">Process</text>

  <!-- Arrow -->
  <line class="diagram-edge" x1="340" y1="148" x2="400" y2="148" marker-end="url(#arrow)" />

  <!-- Decision diamond -->
  <polygon class="diagram-diamond" points="470,95 530,148 470,200 410,148" filter="url(#shadow)" />
  <text class="diagram-label" x="470" y="148" style="font-size:12px">Valid?</text>

  <!-- Yes path (right) -->
  <line class="diagram-edge-accent" x1="530" y1="148" x2="590" y2="148" marker-end="url(#arrow-accent)" />
  <text class="diagram-label" x="560" y="138" style="font-size:11px">Yes</text>

  <!-- End node (pill, highlighted) -->
  <rect class="diagram-highlight" x="590" y="120" width="120" height="55" rx="27" filter="url(#shadow)" />
  <text class="diagram-label-inv" x="650" y="148">Done</text>

  <!-- No path (down) -->
  <line class="diagram-edge" x1="470" y1="200" x2="470" y2="250" marker-end="url(#arrow)" />
  <text class="diagram-label" x="490" y="230" style="font-size:11px; text-anchor:start">No</text>

  <!-- Retry node -->
  <rect class="diagram-node" x="400" y="250" width="140" height="50" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="470" y="275">Retry</text>

  <!-- Loop-back path -->
  <path class="diagram-edge" d="M 400,275 L 270,275 L 270,175" fill="none" marker-end="url(#arrow)" />
</svg>
```

### Layout tips for flowcharts

- Keep nodes at consistent heights (55–60px) and widths (120–160px).
- Horizontal spacing between nodes: 50–60px (edge-to-edge).
- Align rows on the same Y center. Offset decision branches vertically by ~100px.
- Use bezier curves (`<path d="M ... C ...">`) for loop-back lines instead of sharp right angles when space allows.
- Use `rx="27"` (half the height) on start/end nodes for pill shapes.
- Use `rx="8"` on process nodes for rounded corners.

## Architecture / Layer Diagram

Use for system architecture, technology stacks, layered designs.

```html
<svg viewBox="0 0 700 360" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
    </filter>
  </defs>

  <!-- Top layer -->
  <rect class="diagram-highlight" x="100" y="20" width="500" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label-inv" x="350" y="55" style="font-size:16px; font-weight:600">Presentation Layer</text>

  <!-- Middle layer -->
  <rect class="diagram-node" x="100" y="110" width="500" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="350" y="145" style="font-size:16px; font-weight:600">Business Logic</text>

  <!-- Bottom layer -->
  <rect class="diagram-node" x="100" y="200" width="500" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="350" y="235" style="font-size:16px; font-weight:600">Data Access</text>

  <!-- Sub-components inside bottom layer -->
  <rect style="fill:var(--surface2); stroke:var(--diagram-stroke); stroke-width:1; stroke-dasharray:4,3;" x="120" y="290" width="140" height="50" rx="6" />
  <text class="diagram-label" x="190" y="315" style="font-size:12px">PostgreSQL</text>

  <rect style="fill:var(--surface2); stroke:var(--diagram-stroke); stroke-width:1; stroke-dasharray:4,3;" x="280" y="290" width="140" height="50" rx="6" />
  <text class="diagram-label" x="350" y="315" style="font-size:12px">Redis Cache</text>

  <rect style="fill:var(--surface2); stroke:var(--diagram-stroke); stroke-width:1; stroke-dasharray:4,3;" x="440" y="290" width="140" height="50" rx="6" />
  <text class="diagram-label" x="510" y="315" style="font-size:12px">S3 Storage</text>

  <!-- Connecting lines (dashed) -->
  <line style="stroke:var(--diagram-arrow); stroke-width:1.5; stroke-dasharray:5,4;" x1="190" y1="270" x2="190" y2="290" />
  <line style="stroke:var(--diagram-arrow); stroke-width:1.5; stroke-dasharray:5,4;" x1="350" y1="270" x2="350" y2="290" />
  <line style="stroke:var(--diagram-arrow); stroke-width:1.5; stroke-dasharray:5,4;" x1="510" y1="270" x2="510" y2="290" />
</svg>
```

### Layout tips for architecture diagrams

- Full-width layers (same X, same width) stacked vertically with ~20px gaps.
- Use highlighted fill for the "primary" or "focus" layer.
- Sub-components use dashed borders and slightly smaller/inset rectangles.
- Layer labels centered and slightly bolder (`font-weight:600`).

## Pipeline / Data Flow Diagram

Use for ETL pipelines, CI/CD workflows, data processing chains.

```html
<svg viewBox="0 0 900 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto-start-reverse">
      <polygon points="0 0, 10 3.5, 0 7" fill="var(--diagram-arrow)" />
    </marker>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
    </filter>
  </defs>

  <!-- Stage 1 -->
  <rect class="diagram-node" x="20" y="60" width="140" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="90" y="88" style="font-size:13px; font-weight:600">Ingest</text>
  <text class="diagram-label" x="90" y="108" style="font-size:10px; fill:var(--muted)">CSV / API</text>

  <!-- Arrow 1 -->
  <line class="diagram-edge" x1="160" y1="95" x2="210" y2="95" marker-end="url(#arrow)" />

  <!-- Stage 2 -->
  <rect class="diagram-node" x="210" y="60" width="140" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="280" y="88" style="font-size:13px; font-weight:600">Validate</text>
  <text class="diagram-label" x="280" y="108" style="font-size:10px; fill:var(--muted)">Schema check</text>

  <!-- Arrow 2 -->
  <line class="diagram-edge" x1="350" y1="95" x2="400" y2="95" marker-end="url(#arrow)" />

  <!-- Stage 3 -->
  <rect class="diagram-node" x="400" y="60" width="140" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="470" y="88" style="font-size:13px; font-weight:600">Transform</text>
  <text class="diagram-label" x="470" y="108" style="font-size:10px; fill:var(--muted)">Clean &amp; enrich</text>

  <!-- Arrow 3 -->
  <line class="diagram-edge" x1="540" y1="95" x2="590" y2="95" marker-end="url(#arrow)" />

  <!-- Stage 4 -->
  <rect class="diagram-node" x="590" y="60" width="140" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="660" y="88" style="font-size:13px; font-weight:600">Load</text>
  <text class="diagram-label" x="660" y="108" style="font-size:10px; fill:var(--muted)">Database</text>

  <!-- Arrow 4 -->
  <line class="diagram-edge" x1="730" y1="95" x2="780" y2="95" marker-end="url(#arrow)" />

  <!-- Stage 5 (highlighted = final) -->
  <rect class="diagram-highlight" x="780" y="60" width="100" height="70" rx="8" filter="url(#shadow)" />
  <text class="diagram-label-inv" x="830" y="88" style="font-size:13px; font-weight:600">Report</text>
  <text class="diagram-label-inv" x="830" y="108" style="font-size:10px">Dashboard</text>
</svg>
```

### Layout tips for pipelines

- All nodes on the same Y baseline, uniform height and width.
- Each node has a bold label (stage name) and a smaller subtitle (detail).
- Highlight the final stage or the "current" stage.
- For branching pipelines, offset branches 100px above/below the main line and use bezier curves.

## Comparison / Side-by-Side Diagram

Use for feature comparisons, option trade-offs, before/after.

```html
<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
    </filter>
  </defs>

  <!-- Option A header -->
  <rect class="diagram-highlight" x="40" y="20" width="340" height="50" rx="8" filter="url(#shadow)" />
  <text class="diagram-label-inv" x="210" y="45" style="font-size:16px; font-weight:600">Option A</text>

  <!-- Option A features -->
  <rect class="diagram-node" x="40" y="80" width="340" height="200" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="210" y="115" style="font-size:13px">&#x2713; Fast startup</text>
  <text class="diagram-label" x="210" y="145" style="font-size:13px">&#x2713; Low memory</text>
  <text class="diagram-label" x="210" y="175" style="font-size:13px">&#x2717; Limited plugins</text>
  <text class="diagram-label" x="210" y="205" style="font-size:13px">&#x2717; No hot reload</text>
  <line style="stroke:var(--border); stroke-width:1;" x1="60" y1="230" x2="360" y2="230" />
  <text class="diagram-label" x="210" y="258" style="font-size:14px; font-weight:600; fill:var(--diagram-stroke)">Score: 6/10</text>

  <!-- Option B header -->
  <rect style="fill:var(--accent2); stroke:var(--accent2); stroke-width:2;" x="420" y="20" width="340" height="50" rx="8" filter="url(#shadow)" />
  <text class="diagram-label-inv" x="590" y="45" style="font-size:16px; font-weight:600">Option B</text>

  <!-- Option B features -->
  <rect class="diagram-node" x="420" y="80" width="340" height="200" rx="8" filter="url(#shadow)" />
  <text class="diagram-label" x="590" y="115" style="font-size:13px">&#x2713; Rich ecosystem</text>
  <text class="diagram-label" x="590" y="145" style="font-size:13px">&#x2713; Hot reload</text>
  <text class="diagram-label" x="590" y="175" style="font-size:13px">&#x2713; Plugin support</text>
  <text class="diagram-label" x="590" y="205" style="font-size:13px">&#x2717; Slower startup</text>
  <line style="stroke:var(--border); stroke-width:1;" x1="440" y1="230" x2="740" y2="230" />
  <text class="diagram-label" x="590" y="258" style="font-size:14px; font-weight:600; fill:var(--diagram-stroke)">Score: 8/10</text>
</svg>
```

### Layout tips for comparisons

- Equal-width columns side by side with a ~40px gap.
- Colored header bars distinguish the options; use `--accent` for one, `--accent2` for the other.
- Use check marks (&#x2713;) and cross marks (&#x2717;) for pros/cons.
- A summary line at the bottom with a score or recommendation.

## General Diagram Guidelines

1. **viewBox** — always set a `viewBox` so the SVG scales. Common sizes: `0 0 800 300` for wide diagrams, `0 0 600 400` for taller ones.
2. **filter="url(#shadow)"** — apply to all rectangles and polygons for subtle depth. Omit if you want a flat aesthetic.
3. **Consistent border radius** — use `rx="8"` for regular nodes, `rx="27"` (half height) for pill-shaped start/end nodes.
4. **Text sizing** — labels inside nodes use `font-size:13–16px` in the SVG coordinate space (the viewBox scales it). Smaller annotations use `10–12px`.
5. **Spacing** — 50–60px between node edges. Keep consistent horizontal and vertical rhythm.
6. **Bezier curves** — for curved connections, use cubic bezier paths: `<path d="M x1,y1 C cx1,cy1 cx2,cy2 x2,y2" />`. Control points should be roughly 1/3 of the way to the destination to produce smooth arcs.
