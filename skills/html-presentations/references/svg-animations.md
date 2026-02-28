# SVG Animation Patterns

Animations in these presentations are **slide-activated**: they play when a slide gets the `.active` class and reset when the slide loses it. This means animations replay each time the audience navigates to that slide.

## When to Animate (and When Not To)

### Good uses of animation

| Animation | When to use |
|-----------|-------------|
| **Path drawing** | Showing connections being established. Network topology. Building a diagram stroke by stroke. Tracing a data flow path. |
| **Sequential fade-in** | Building up a concept step by step. Revealing a list of findings one at a time. Telling a story in stages. |
| **Pulse / glow** | Highlighting the currently discussed node in a diagram. Drawing attention to a key element. Showing an "active" or "running" state. |
| **Flow along path** | Showing data or a signal moving through a pipeline. Illustrating a request traveling through services. |
| **Scale / morph** | Showing growth, expansion, or transformation. Before/after comparisons. |

### When NOT to animate

- Purely decorative motion that adds no information.
- Every bullet point on a text-heavy slide (slows the presenter down).
- Content the audience needs to read immediately upon slide entry.
- More than 3–4 animated elements per slide (becomes distracting).

## Animation 1: Sequential Fade-In

Elements fade up into view with staggered timing. Uses the `.anim-fade` class from the base CSS.

### HTML usage

```html
<h2 class="anim-fade">Title fades in first</h2>
<p class="anim-fade" style="--delay: 0.3s">Second element</p>
<p class="anim-fade" style="--delay: 0.6s">Third element</p>
<div class="anim-fade" style="--delay: 0.9s">
  <svg><!-- diagram fades in last --></svg>
</div>
```

### How it works

The base CSS sets `.anim-fade` to `opacity: 0; transform: translateY(20px)`. When the parent `.slide` gains `.active`, the transition fires with the `--delay` offset.

### Recommended timing

- 0.2–0.3s between sequential items for a brisk pace.
- 0.4–0.5s between items for a more deliberate reveal.
- Total animation sequence should not exceed ~3s (audience patience).

## Animation 2: SVG Path Drawing

A path or line appears to draw itself from start to end. Uses the `.anim-draw` class.

### HTML usage

```html
<svg viewBox="0 0 800 300">
  <defs><!-- arrowhead markers --></defs>

  <!-- Static nodes -->
  <rect class="diagram-node" x="50" y="110" width="140" height="60" rx="8" />
  <text class="diagram-label" x="120" y="140">Source</text>

  <rect class="diagram-node" x="610" y="110" width="140" height="60" rx="8" />
  <text class="diagram-label" x="680" y="140">Destination</text>

  <!-- Animated connecting path -->
  <path class="diagram-edge-accent anim-draw" style="--len: 420; --delay: 0.5s"
        d="M 190,140 C 300,80 500,200 610,140"
        marker-end="url(#arrow-accent)" />
</svg>
```

### How it works

The CSS uses `stroke-dasharray` and `stroke-dashoffset` set to `--len`. On `.active`, `stroke-dashoffset` transitions to 0, visually drawing the path.

### Setting `--len`

`--len` should be the approximate total length of the path in SVG units. For straight lines, it is the distance between endpoints. For curves, estimate or use JavaScript: `path.getTotalLength()`. Slightly overestimating is fine (the animation just finishes a fraction early).

### Recommended timing

The default duration is 1.2s (set in the base CSS transition). For longer paths, override in an inline style:

```html
<path class="diagram-edge anim-draw"
      style="--len: 800; --delay: 0.3s; transition: stroke-dashoffset 2s ease-in-out 0.3s"
      d="M ..." />
```

### Combining with fade-in

Draw connecting lines after nodes fade in:

```html
<!-- Nodes fade in -->
<g class="anim-fade" style="--delay: 0s">
  <rect class="diagram-node" ... />
  <text class="diagram-label" ...>Node A</text>
</g>
<g class="anim-fade" style="--delay: 0.3s">
  <rect class="diagram-node" ... />
  <text class="diagram-label" ...>Node B</text>
</g>

<!-- Line draws after both nodes are visible -->
<line class="diagram-edge anim-draw" style="--len: 200; --delay: 0.8s"
      x1="190" y1="140" x2="310" y2="140"
      marker-end="url(#arrow)" />
```

## Animation 3: Pulse / Glow

An element pulses with a glowing drop-shadow to draw attention. Uses the `.anim-pulse` class.

### HTML usage

```html
<svg viewBox="0 0 600 200">
  <!-- Normal node -->
  <rect class="diagram-node" x="50" y="70" width="130" height="60" rx="8" />
  <text class="diagram-label" x="115" y="100">Step 1</text>

  <!-- Pulsing "active" node -->
  <rect class="diagram-highlight anim-pulse" style="--delay: 0.5s"
        x="250" y="70" width="130" height="60" rx="8" />
  <text class="diagram-label-inv" x="315" y="100">Step 2</text>

  <!-- Normal node -->
  <rect class="diagram-node" x="450" y="70" width="130" height="60" rx="8" />
  <text class="diagram-label" x="515" y="100">Step 3</text>
</svg>
```

### Recommended use

- Apply to **one** element per diagram (the focus element).
- Pair with `.diagram-highlight` fill so the pulsing node is already visually distinct.
- Good for "we are here" indicators in multi-step processes.

## Animation 4: Flow Along Path

An element (circle, dot, or icon) moves along a path to show data or signal flow.

### CSS (add to the presentation's `<style>`)

```css
@keyframes flow-dot {
  0%   { offset-distance: 0%; }
  100% { offset-distance: 100%; }
}
.anim-flow {
  offset-rotate: 0deg;
  animation: flow-dot 2s ease-in-out infinite;
  animation-delay: var(--delay, 0s);
}
```

### HTML usage

```html
<svg viewBox="0 0 800 200">
  <defs>
    <path id="flow-path" d="M 50,100 C 200,30 350,170 500,100 S 700,30 750,100" />
  </defs>

  <!-- Visible path -->
  <use href="#flow-path" class="diagram-edge" />

  <!-- Moving dot -->
  <circle r="6" fill="var(--diagram-highlight)" style="offset-path: path('M 50,100 C 200,30 350,170 500,100 S 700,30 750,100');"
          class="anim-flow" />
</svg>
```

### Notes

- The `offset-path` CSS property must duplicate the SVG path `d` attribute (or reference it via `url()`).
- `offset-rotate: 0deg` keeps the dot upright. Set to `auto` if using an arrow shape that should follow the path tangent.
- For multiple dots, create additional `<circle>` elements with different `--delay` values.

### Recommended use

- Data pipelines (showing a record flowing through stages).
- Network diagrams (showing a request traveling between services).
- Process flows (showing progress through steps).

## Animation 5: Expanding / Scaling

An element scales up from zero to full size, good for revealing importance or showing growth.

### CSS (add to the presentation's `<style>`)

```css
.slide .anim-scale {
  transform: scale(0);
  transform-origin: center;
}
.slide.active .anim-scale {
  transform: scale(1);
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) var(--delay, 0s);
}
```

### HTML usage

```html
<svg viewBox="0 0 400 300">
  <!-- Background circle (appears first) -->
  <circle class="anim-scale" style="--delay: 0s"
          cx="200" cy="150" r="100"
          fill="var(--surface)" stroke="var(--diagram-stroke)" stroke-width="2" />

  <!-- Label (appears after circle) -->
  <text class="diagram-label anim-fade" style="--delay: 0.4s"
        x="200" y="155" style="font-size:18px; font-weight:600">Core</text>
</svg>
```

### Recommended use

- Revealing a central concept or key takeaway.
- Showing something growing (user base, revenue, scope).
- Appearing "from nothing" as a dramatic reveal for an important element.

## Composing Animations

The most effective diagram slides combine 2–3 animation types in sequence:

1. **Nodes fade in** (`.anim-fade` with staggered `--delay`)
2. **Connections draw themselves** (`.anim-draw` with later `--delay`)
3. **One node pulses** (`.anim-pulse` starts after connections are drawn)

Example timing for a 3-node diagram:

| Element | Class | `--delay` |
|---------|-------|-----------|
| Node A | `.anim-fade` | `0s` |
| Node B | `.anim-fade` | `0.3s` |
| Node C | `.anim-fade` | `0.6s` |
| Edge A→B | `.anim-draw` | `0.8s` |
| Edge B→C | `.anim-draw` | `1.2s` |
| Node C (highlight) | `.anim-pulse` | `1.8s` |

Total sequence: ~2.5s. The audience sees the diagram build itself logically.

## Performance Notes

- Prefer `opacity` and `transform` animations (GPU-composited, smooth at 60fps).
- `filter` animations (used by `.anim-pulse`) are slightly more expensive; limit to one or two elements per slide.
- Avoid animating `width`, `height`, `top`, `left`, or other layout-triggering properties.
