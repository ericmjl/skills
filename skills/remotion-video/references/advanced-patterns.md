# Advanced Patterns

Load this file when the user wants to go beyond a basic build: polish with controls, generate multiple videos, render with transparency, or manage versions.

## Timing Sliders

Add real-time controls to a composition so the user can tweak animations in Remotion Studio without editing code.

**Prompt pattern**: "Add timing sliders to my composition called `<name>`."

The agent will:
1. Identify animation properties (stagger delays, fade durations, float speeds, glow intensities)
2. Create `<Composition>` props with `z.object()` schema from `zod`
3. Expose them as sliders in Remotion Studio's right panel

**Result**: The user can adjust values in real-time and see changes instantly, because Remotion renders code (not pixels).

## Wizard Schema Control

Add customizable properties to **every** composition and every clip/sequence within each composition. More comprehensive than timing sliders for a single composition.

**What it adds**: Controls for animation speeds, positions, scales, opacities, text labels, colors — scoped per composition.

**When to use**: Apply after building all compositions. The user gets a full control panel for the entire project, similar to a video editor's property inspector.

**Best practice**: Always apply this as a post-build step. Build the video first, verify it works, then add controls on top. This separates content creation from parameterization.

## Multi-Video Generation

Scrape a website or data source and generate multiple Remotion compositions from a single prompt.

**Pattern**:
1. Use Playwright MCP to scrape structured data (product names, prices, images, specs)
2. Store data as an array of objects
3. Create one composition per item, using a shared component template
4. Each composition gets its own entry in the Remotion Studio sidebar

**When to use**: When the user provides a product catalog page, a list of items, or asks for "a video for each product."

**Key insight**: The agent should create a reusable scene component that accepts props (name, price, image), then instantiate it once per item. This avoids duplicating code.

## Transparent Rendering

Render videos with transparency for use as overlays in other video editors.

```bash
npx remotion render <composition-id> out/overlay.webm --transparent
```

**When to use**: Lower thirds, overlays, title cards, and any element meant to be composited on top of other footage. The WebM format supports alpha channels.

## Custom Transitions

Create reusable transition components (glitch, swipe, fade, zoom) as separate compositions.

**Pattern**:
1. Create a transition component accepting `enterProgress` / `exitProgress`
2. Use `TransitionSeries` with the custom transition
3. Can be rendered as standalone assets for use in external editors

**When to use**: When the user asks for specific transition styles or wants a library of reusable transitions.

## Git Workflow (Version Control)

Use git commits as "saves" — similar to autosave in traditional video editors.

**Pattern**:
- After each successful build or major change: `git add -A && git commit -m "feat: add scene 3 animation"`
- Before risky changes: `git stash` or commit first
- To revert: `git checkout -- <file>` or `git revert <commit>`
- Each commit is a snapshot the user can return to

**When to use**: Recommend this workflow at the start of every project, especially for users unfamiliar with git. Frame it as "saving your progress" rather than version control jargon.
