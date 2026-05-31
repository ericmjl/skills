# Education Explainer Video

Create an animated explainer video that teaches any topic. Research the topic, write a 5-scene script, then design and animate all scenes.

## Input

User provides a topic string (e.g., "How AI Agents Work", "How DNS Works", "How Photosynthesis Works").

## Workflow

### Step 1: Research & Script

Before writing any code, research the topic and write a 5-scene script. Each scene needs:

- **Headline**: One-line title (max 6 words)
- **Explanation**: 1-2 sentences of key information
- **Visual**: Description of what to animate (diagram, flowchart, icons, step-by-step)

Present the script to the user and **wait for approval** before coding.

Scene pacing guidance:
- Scene 1 (Hook): 3-4 seconds — pose a question or state a surprising fact
- Scenes 2-4 (Core): 7-8 seconds each — teach the key concepts
- Scene 5 (Recap): 4-5 seconds — summarize with a memorable takeaway

### Step 2: Design & Animate

After approval, build all 5 scenes.

**Visual style**: Use the dark theme from `defaults.md`.

**Scene design principles**:
- Each scene needs a clear visual metaphor — diagrams, flowcharts, icons, or step-by-step animations
- No walls of text — dense information, beautiful motion, fast pacing
- Think Kurzgesagt meets Fireship: complex ideas made visually intuitive
- All icons/diagrams built as SVG components (no external assets)

**Animation specifics**:
- Every element enters with `spring({ damping: 200 })` — no linear motion
- Stagger related items by 8-12 frames
- Use `TransitionSeries` with 12-frame fade transitions between scenes
- Diagrams and flowcharts draw themselves (SVG `stroke-dashoffset`)
- Key numbers use count-up animation with `interpolate()` and `tabular-nums`
- Final scene: particle effect background (10-15 circles drifting upward)

## Duration

30 seconds total. Default 5 scenes.

## Output

- Remotion composition at 1080x1920, 30fps
- Launch `npx remotion studio` for preview
