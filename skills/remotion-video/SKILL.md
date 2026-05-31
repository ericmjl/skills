---
name: remotion-video
description: "Create animated videos using Remotion from topics, product URLs, Google reviews, talking-head videos, or CSV data. Supports 5 video types: educational explainers, product launch demos, testimonial/social proof, avatar video overlays, and data visualization dashboards. Each follows a 2-step workflow: research/scrape/analyze then design and animate with spring animations, SVG diagrams, and count-up effects. Requires the Remotion best practices skill (install with `npx skills add remotion-dev/skills`). Use when the user asks to create a Remotion video, explainer video, educational video, product demo video, testimonial video, video with animated overlays, data visualization video, animated dashboard, or short-form vertical video for mobile."
license: MIT
---

# Remotion Video

Create animated short-form videos (1080x1920) using Remotion. Five video types, each with a research-then-animate workflow.

## Prerequisites

This skill requires the **Remotion best practices skill**. Before starting, check whether Remotion skills are installed in the project. If not, instruct the user to run:

```bash
npx skills add remotion-dev/skills
```

See [Remotion Agent Skills docs](https://www.remotion.dev/docs/ai/skills) for details.

## Type Selection

Determine the video type from the user's input:

| User provides | Video type | Load reference |
|---|---|---|
| A topic to teach or explain | Education Explainer | [education-explainer.md](references/education-explainer.md) |
| A product URL | Product Demo + Launch | [product-demo.md](references/product-demo.md) |
| A Google Business / Maps link | Testimonial / Social Proof | [testimonial.md](references/testimonial.md) |
| A talking-head video file (9:16) | Avatar + Animated Overlays | [avatar-overlays.md](references/avatar-overlays.md) |
| A CSV or data file | Data Visualization Dashboard | [data-viz.md](references/data-viz.md) |

Load **only** the relevant type reference file plus [defaults.md](references/defaults.md) for shared configuration (safe zone, fonts, animation rules, visual style).

## Common Workflow

All 5 types follow the same two-step pattern:

### Step 1: Research / Scrape / Analyze

Gather information based on the video type (research topic, scrape website, scrape reviews, transcribe video, or analyze data). Present findings and a proposed scene outline. **Wait for user approval before writing code.**

### Step 2: Design & Animate

After approval, build all scenes as Remotion React components. Follow the animation rules from [defaults.md](references/defaults.md):
- Spring entrances (`damping: 200`), no linear motion
- Stagger related items by 8-12 frames
- `TransitionSeries` with 12-frame fade transitions between scenes
- SVG `stroke-dashoffset` for diagram/flowchart drawing
- `interpolate()` + `tabular-nums` for count-up animations
- Particle effects for celebration/closing moments

### Preview

After building, launch Remotion Studio:

```bash
npx remotion studio
```

## Design Principles

- Each scene needs a clear visual metaphor — diagrams, flowcharts, icons, step-by-step animations
- No walls of text — dense information, beautiful motion, fast pacing
- Kurzgesagt meets Fireship: complex ideas made visually intuitive
- All graphics built as SVG components (no external image assets needed)
- Respect the safe zone (see [defaults.md](references/defaults.md)) — nothing important near edges

## Credit

Based on video prompts by [Sabrina Ramonov](https://www.sabrina.dev/p/5-insane-claude-code-video-prompts). Adapted into an Agent Skill with configurable defaults and progressive disclosure.
