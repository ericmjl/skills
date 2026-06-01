---
name: remotion-video
description: "Create animated videos using Remotion from topics, product URLs, Google reviews, talking-head videos, CSV data, or channel/brand URLs. Supports 6 video types: educational explainers, product launch demos, testimonial/social proof, avatar video overlays, data visualization dashboards, and lower third overlays. Each follows a 2-step workflow: research/scrape/analyze then design and animate with spring animations, SVG diagrams, and count-up effects. Requires the Remotion best practices skill (install with `npx skills add remotion-dev/skills`). Use when the user asks to create a Remotion video, explainer video, educational video, product demo video, testimonial video, video with animated overlays, data visualization video, animated dashboard, lower third, transparent overlay, short-form vertical video for mobile, or multi-product video from a website."
license: MIT
---

# Remotion Video

Create animated short-form videos (1080x1920) using Remotion. Six video types, each with a research-then-animate workflow.

## Why Remotion

Remotion renders code, not pixels. AI understands code natively — changing an opacity variable is unambiguous, vs. deciding which pixels constitute a "title" in a raster frame. Code also means: resolution-independent output, reusable components, instant preview, and git-based version control.

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
| A channel/brand/social URL | Lower Third / Overlay | [lower-thirds.md](references/lower-thirds.md) |

Load **only** the relevant type reference file plus [defaults.md](references/defaults.md) for shared configuration (safe zone, fonts, animation rules, visual style).

## Additional References (load on demand)

These files are not needed for every video. Load only when the situation calls for them:

- **[integrations.md](references/integrations.md)** — Load when the user needs Playwright (web scraping), Lottie animations, 3D assets, voice-overs, or AI-generated imagery. Some integrations require API keys — always ask the user first.
- **[advanced-patterns.md](references/advanced-patterns.md)** — Load when the user wants timing sliders, controls for every composition, multi-video generation from a catalog, transparent rendering, custom transitions, or git-based save workflow.

## Common Workflow

All types follow the same two-step pattern:

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

### Step 3: Polish (optional)

After the video plays correctly, offer to add controls:
- **Timing sliders** — see [advanced-patterns.md](references/advanced-patterns.md) for adding real-time controls to compositions
- **Integrations** — see [integrations.md](references/integrations.md) for Lottie animations, 3D effects, voice-overs, etc.

### Preview

After building, launch Remotion Studio:

```bash
npx remotion studio
```

## Design Principles

- Each scene needs a clear visual metaphor — diagrams, flowcharts, icons, step-by-step animations
- No walls of text — dense information, beautiful motion, fast pacing
- Kurzgesagt meets Fireship: complex ideas made visually intuitive
- All graphics built as SVG components by default; Lottie and 3D available via [integrations.md](references/integrations.md)
- Respect the safe zone (see [defaults.md](references/defaults.md)) — nothing important near edges

## Credit

Based on video prompts by [Sabrina Ramonov](https://www.sabrina.dev/p/5-insane-claude-code-video-prompts) and production insights from [Remotion AI video editing tutorial](https://www.youtube.com/watch?v=kDq5GTckOVs). Adapted into an Agent Skill with configurable defaults and progressive disclosure.
