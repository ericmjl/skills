# Shared Defaults

All video types share these defaults unless a type-specific reference file overrides them.

## Video Specs

| Parameter | Default | Override example |
|---|---|---|
| Resolution | 1080x1920 (9:16 vertical) | Product demo may use same |
| FPS | 30 | — |
| Duration | 30 seconds | Data viz: 15s; Testimonial: 20s |
| Scene count | 5 | Product demo: 6 |

## Safe Zone

All text and key content must stay within the safe zone — nothing important should touch the edges.

| Edge | Minimum inset | Reason |
|---|---|---|
| Top | 150px | Platform search bars, status bar |
| Bottom | 170px | Navigation buttons, swipe-up UI |
| Left | 60px | Side margin |
| Right | 60px | Side margin |

**Rule**: If in doubt, give more padding, not less.

## Font Size Minimums

| Role | Minimum | Notes |
|---|---|---|
| Headlines | 56px | Scene titles, hero text |
| Body / Subtitles | 36px | Explanations, descriptions |
| Labels / Small text | 28px | Absolute minimum — nothing under 28px |

Use Inter font family (weights 400, 600, 800) unless a type specifies otherwise.

## Visual Style (Dark Theme)

Default for Education Explainer, Product Demo, Avatar Overlays, and Data Viz:

| Element | Value |
|---|---|
| Background | `#0a0a0a` |
| Primary text | `white` |
| Accent | `#6366f1` (indigo) |
| Success / Emphasis | `#22c55e` (green) |

## Visual Style (Light Theme)

Used by Testimonial type:

| Element | Value |
|---|---|
| Background | `#f8f9fa` |
| Card background | `#ffffff` |
| Primary text | `#1a1a1a` |
| Secondary text | `#64748b` |
| Accent (gold) | `#f59e0b` |
| Card borders | `#e2e8f0` |

## Animation Rules

| Rule | Value |
|---|---|
| Entrance spring | `spring({ damping: 200 })` — no linear motion |
| Stagger delay | 8-12 frames between related items |
| Scene transitions | 12-frame fade via `TransitionSeries` |
| Diagram drawing | SVG `stroke-dashoffset` animation |
| Number animations | `interpolate()` with `tabular-nums` font-variant |
| Particle effects | 10-15 circles (final scene / celebration moments) |
| Cursor movement | `spring({ damping: 15 })` for natural, human-like motion |

## Common Remotion Patterns

### Spring Entrance

```tsx
const scale = spring({
  frame,
  fps,
  config: { damping: 200 },
  from: 0,
  to: 1,
});
```

### Count-Up Animation

```tsx
const value = interpolate(frame, [0, durationInFrames - 10], [0, targetValue], {
  extrapolateRight: "clamp",
});
// Apply: style={{ fontVariantNumeric: "tabular-nums" }}
```

### SVG Path Drawing

```tsx
const pathLength = interpolate(frame, [0, duration], [0, 1], {
  extrapolateRight: "clamp",
});
// Apply: strokeDasharray="1" strokeDashoffset={1 - pathLength}
```

### Staggered Entrance

```tsx
items.map((item, i) => {
  const delay = i * 10; // 10 frames between items
  const opacity = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return <div style={{ opacity }}>{item}</div>;
});
```

## Preview & Render

After building, launch Remotion Studio for preview:

```bash
npx remotion studio
```

For final render:

```bash
npx remotion render <composition-id> out/video.mp4
```

For transparent overlay (lower thirds, overlays):

```bash
npx remotion render <composition-id> out/overlay.webm --transparent
```

## Git Workflow

Use git commits as "saves" between builds — similar to autosave in traditional video editors. Commit after each working scene or major change. This lets the user revert to any earlier version.

```
git add -A && git commit -m "feat: scene 3 animation complete"
```
