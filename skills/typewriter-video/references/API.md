# Auto-Explainer — API Reference

> Engineering documentation for the typewriter engine and visual primitives. This is the reference for understanding and extending the codebase.

## Architecture

The core insight: typing speed must serve the **meaning** of the text, not just the characters. The system uses annotated text segments with typing modes (`burst`, `normal`, `deliberate`, `thinking`) to control the cadence.

### Key Files

| File | Purpose |
|---|---|
| `src/TypewriterText.tsx` | **Timing engine** — takes `TextSegment[]`, builds timeline events, renders typewriter with cursor. Contains ALL display logic: scrolling, ghost text, strike-through, emoji picker, file tabs, cursor jump, in-place mutation, syntax highlighting, IME input, audio sync, inline images, image stacks |
| `src/Typewriter.tsx` | **Canonical demo & score** — background + editor window + annotated text segments. This file IS the reference tutorial — it demonstrates every feature in a self-explanatory sequence |
| `src/syntaxHighlight.ts` | **Syntax highlighter** — lightweight regex-based tokenizer. Supports `tsx`, `ts`, `javascript`, `bash`, `markdown`, `css`. Accepts optional `SyntaxColors` palette from theme system (defaults to VS Code Dark+) |
| `src/EditorWindow.tsx` | macOS window chrome (traffic light dots, title bar). Accepts `theme` prop — supports chrome-less mode (no dots/title) and visual effects (ruled lines, chalk texture, CRT scanlines) |
| `src/themes.ts` | **Theme system** — `Theme` interface + 6 theme objects. Each theme defines: editor chrome, canvas colors, syntax palette, popup styling, outer background, font config, visual effects |
| `src/EmojiPicker.tsx` | Emoji catalog panel UI — filters and renders the sliding window of emoji candidates during `:search` |
| `src/Canvas5K.tsx` | 5K render wrapper — scales 1920×1080 layout to 5120×2880 for B-roll production |
| `src/ChineseDemo.tsx` | Standalone Chinese typing demo composition (separate from main `Typewriter.tsx`) |
| `src/emoji-catalog.json` | 50 curated emojis in fixed order, grouped by emotional tone. Used by the emoji picker's catalog filtering |
| `src/pinyin-catalog.json` | ~180 pinyin → character mappings with 5 candidates each. Used by the IME input system |
| `src/Root.tsx` | Composition registry (1920×1080, 29.97fps) |
| `src/ThemeShowcase.tsx` | Theme demo composition — cycles all 6 themes (5s each, fade transitions) |

### Timeline Architecture (in `TypewriterText.tsx`)

The engine uses a **timeline event** system — no CSS transitions. `buildTimeline()` converts `TextSegment[]` into a flat list of frame-accurate events:

| Event Type | Purpose |
|---|---|
| `char` | Type one real character |
| `strike-char` | Type one temporary character (for emoji `:label` and strike-through) |
| `delete` | Backspace one temp char |
| `select-grow` | Extend blue selection highlight by one char |
| `select-delete` | Wipe all temp text + selection at once |
| `ghost-show` | Show gray autocomplete preview |
| `ghost-accept` | Tab-accept ghost text into real text |
| `file-switch` | Switch to a different file tab (clears canvas, updates title bar) |
| `cursor-jump` | Move cursor to a specific line/col without typing |
| `insert-char` | Type a character at a specific line/col (in-place mutation) |
| `checkbox-check` | Mark a checkbox line as checked (triggers `[ ]` → `[✓]` animation) |

`getDisplayState(events, frame)` resolves the current display at any frame: `typedLength`, `tempSuffix`, `selectionCount`, `ghostText`, `ghostOpacity`, `currentFile`, `fileTextMap`, `insertions`, `cursorPosition`, `currentLanguage`, `checkedLines`, `checkFrames`.

Image and stack rendering is handled on the render side via marker detection (`\uFFFC` / `\uFFFD`) — separate from the event timeline.

### Typing Modes

| Mode | Speed | Usage |
|---|---|---|
| `burst` | 2f/char | **Default for ~70% of text.** Confident, fast typing |
| `normal` | 3f/char | Moderate connective text, transitions |
| `deliberate` | 5f/char + 3f pause | **Single key words only.** Emphasis, weight |
| `thinking` | 2f/char + 14f pause before | Composing next thought, followed by fast typing |

---

## Special Behaviors

### Ghost Text (autocomplete)
Gray preview text appears, pauses, then Tab accepts it into real text. Use for long predictable phrases.
```tsx
{ text: "paragraph. ", mode: "burst", ghostText: "So we use ghost text and tab to keep them engaged." }
```

### Strike Text (delete-and-retype)
Two modes — `backspace` (char-by-char delete, intimate/hesitant) and `select` (blue highlight sweep + single delete, decisive/dramatic):
```tsx
{ text: "just a framework", mode: "burst", strikeText: "something", strikeDelete: "select" }
```

### Emoji Picker
**Emergent behavior** — no dedicated event types. Uses existing strike-char system:
```tsx
{ text: "😤", mode: "normal", emojiPicker: true }
```

How it works:
1. Engine looks up "😤" in `emoji-catalog.json` → label is "frustrated"
2. Types `:` then `f`, `r` as `strike-char` events (temporary text)
3. Render detects `tempSuffix.startsWith(":")` → filters catalog by prefix
4. **Early-stop**: stops typing as soon as filter narrows to 1 match (e.g., at `:fr`)
5. Pauses (`emojiPickerFrames ?? 20`), then `select-delete` clears `:fr` instantly
6. Normal `char` event types the actual 😤 emoji

The emoji panel is rendered by filtering `emoji-catalog.json` against the typed prefix. Panel shrinks in real-time as more characters are typed — exactly like Slack/Discord emoji pickers.

### File Tab Switching
When `file` changes between segments, the editor "opens a new file" — title bar updates, canvas shows that file's accumulated text. Text is preserved per-file in `fileTextMap`.
```tsx
{ text: "import React\n", mode: "burst", file: "app/page.tsx" }
```

### Cursor Jump & In-Place Mutation
`insertAt` makes the cursor jump to a specific line/col, then types text there. Existing text shifts down. Insertions are tracked per-file.
```tsx
{ text: "'use cache'\n", mode: "thinking", insertAt: { line: 0, col: 0 } }
```

### Syntax Highlighting
`language` enables VS Code Dark+ style coloring. Set once — it applies to all subsequent text in that file. Supports: `tsx`, `ts`, `javascript`, `bash`, `markdown`, `css`.
```tsx
{ text: "export default function Page() {\n", mode: "burst", file: "app/page.tsx", language: "tsx" }
```

### Chinese Input — Two Modes

**Direct mode (吐字)** — Default. Chinese characters appear one by one, like English letters. No pinyin, no candidate panel. Clean and fast.
```tsx
{ text: "这是吐字模式", mode: "burst" }
```

**IME mode (拼音)** — Full pinyin → candidate panel → select cycle. Visually rich, shows the typing process.
```tsx
{ text: "这是拼音模式", mode: "normal", imeInput: true }
```

**Storytelling guidance for AI agents**: IME mode is a "performance" — it adds visual drama but slows the pace. Use it deliberately:

| Scenario | Mode to use | Why |
|---|---|---|
| Narration / connecting text | Direct (吐字) | Clean, fast, no distraction |
| Feature checklists | Direct (吐字) | Scan-friendly, rhythmic |
| Key phrases worth emphasizing | IME + `deliberate` | Draws attention to word choice |
| Pausing to think before a key insight | IME + `thinking` | Shows the thought forming before the characters appear |
| Fast-paced demo content | IME + `burst` | Shows skilled typing, characters fly |

**Speed profile** (direct mode uses standard English speed profiles; IME pinyin is faster to compensate for multi-keystroke overhead):

| Mode | Pinyin typed | Panel pause | Post-char |
|---|---|---|---|
| burst | **1 letter** (single key → select) | 3f | 0f (fluid) |
| normal | **50-70%** of full pinyin | 10f | 1f |
| deliberate | **full pinyin** (shows complete process) | 20f | 3f |
| thinking | **50-70%** + initial 14f pause | 10f | 1f |

Predictive truncation simulates real smart IME — you rarely type full pinyin in practice. `imePauseFrames` overrides the panel pause per-segment. Non-CJK characters bypass IME automatically. Chinese full-width punctuation (`。！？，` etc.) uses the same pause timings as English equivalents.

### `delayFrames` — A-Roll Sync

Absolute timing: pause the timeline until a specific frame, enabling sync with narration audio.
```tsx
{ text: "Key insight: ", mode: "burst", delayFrames: 90 } // wait until frame 90 before typing
```
If `totalFrames` already exceeded `delayFrames`, no idle is inserted.

### Inline Image (`\uFFFC` marker)

Images are **embedded in the text flow** using the Object Replacement Character (\uFFFC). They scroll naturally with text. The `image` field on `TextSegment` triggers instant char events that keep `globalCharIndex` in sync.

**Single image:**
```tsx
{ text: "Preview:\n", mode: "normal", image: { src: "screenshot.png", heightLines: 5, alt: "App preview", animation: "fade" } }
```

**Multi-image row** (side-by-side with card backgrounds):
```tsx
{ text: "Technologies:\n", mode: "normal",
  image: {
    items: [
      { src: "react.png", label: "React" },
      { src: "next.png", label: "Next.js" },
      { src: "vercel.png", label: "Vercel" },
    ],
    width: 85, height: 100, gap: 10, animation: "slide-up", heightLines: 4,
  }
}
```

| Field | Default | Description |
|---|---|---|
| `src` | — | Single image path (relative to `public/`) |
| `heightLines` | 5 | Visual lines the image occupies (× 44px = height) |
| `alt` | — | Label typed above the image before it appears |
| `items` | — | Array of `{ src, label? }` for multi-image row |
| `width` | 80 | Percentage of editor width |
| `height` | — | Explicit height in px (overrides heightLines for rendering) |
| `gap` | 12 | Spacing between row items in px |
| `animation` | none | `"fade"` \| `"slide-up"` \| `"scale"` |

### Image Stack (paper pile effect)

Multiple images pile up with pseudo-random rotation (±5°) and offset (±15px). Uses `\uFFFD` stack marker.
```tsx
{ text: "Headlines:\n", mode: "normal",
  imageStack: { images: ["a.png", "b.png", "c.png"], heightLines: 8, intervalFrames: 8 }
}
```

| Field | Default | Description |
|---|---|---|
| `images` | — | Array of src paths relative to `public/` |
| `heightLines` | 8 | Height of the stack region in visual lines |
| `intervalFrames` | 8 | Frames between each image appearing |

Images and stacks are scroll-aware — their height is factored into the visual line count for terminal-style scrolling.

### Animated Checkboxes

Checkbox items type as `- [ ]`, then animate to `[✓]` after a configurable delay. The checkmark uses a spring-pop scale animation (0 → 1.3 → 1.0 over 8 frames) with a green color (`#22C55E`). Checked lines dim to 65% opacity.

```tsx
{ text: "- [ ] Step one\n", mode: "burst", checkbox: { checkAfterFrames: 20 } }
{ text: "- [ ] Step two\n", mode: "burst", checkbox: { checkAfterFrames: 20 } }
{ text: "- [ ] Final step\n", mode: "deliberate", checkbox: { checkAfterFrames: 30 } }
```

| Field | Default | Description |
|---|---|---|
| `checkAfterFrames` | 20 | Frames to wait after the checkbox text is fully typed before checking it |

The text must contain `[ ]` for the system to detect and animate it. The engine emits a `checkbox-check` timeline event after the typing + delay, targeting the correct line per-file. No separate sound — the keyboard typing sound serves as the audio cue.

---

## Frame Cost Constants

These constants control how many frames each character/event costs in the timeline. Essential for calculating timing budgets in A-roll sync mode.

### Speed Profiles (`MODE_PROFILES`)

| Mode | `baseFrames` | `jitter` | `pauseBefore` | Effective cost per char |
|:-----|:------------|:---------|:-------------|:----------------------|
| `burst` | 2 | ±1 | 0 | ~2f |
| `normal` | 3 | ±1 | 0 | ~3f |
| `deliberate` | 5 | ±2 | 3 | ~5f + 3f pause before first char |
| `thinking` | 2 | ±1 | 14 | ~2f + 14f pause before first char |

### Punctuation Extra Cost (`HARD_CHARS`)

| Characters | Extra frames | Notes |
|:-----------|:------------|:------|
| `.` `!` `?` `。` `！` `？` | 6 | ±1 jitter. Full stops, exclamations |
| `"` | 8 | Opening double quote |
| `'` | 5 | Single quotes, Chinese quotes `'` `'` `"` `"` |
| `,` `，` `、` | 2 | ±1 jitter. Commas |
| `:` `;` `：` `；` | 3 | ±1 jitter. Colons and semicolons |

### Structural Costs

| Event | Frames | Notes |
|:------|:-------|:------|
| `NEWLINE_FRAMES` (`\n`) | 4 | ±1 jitter |
| `PARAGRAPH_BREAK_FRAMES` (`\n\n`) | 16 | ±3 jitter. Consecutive newlines |
| `EMOJI_FRAMES` | 5 | ±1 jitter. Per emoji character |
| `DEFAULT_GHOST_PAUSE` | 30 | Frames ghost text is visible before Tab accept |
| `GHOST_FADE_FRAMES` | 8 | Ghost text fade-in animation |
| `CURSOR_BLINK_FRAMES` | 20 | Blink period (not a cost) |
| Image segment | 1 | `seg.text` types normally, then image appears in 1 frame |
| Image stack | 1 | Text + marker appear in 1 frame |

### Special Characters

| Constant | Value | Purpose |
|:---------|:------|:--------|
| `IMAGE_MARKER` | `\uFFFC` (U+FFFC) | Object Replacement Character — marks inline image position in flat text |
| `STACK_MARKER` | `\uFFFD` (U+FFFD) | Replacement Character — marks image stack position in flat text |

> **Image segments with text**: When a segment has both `text` and `image`, the engine types the text char-by-char with normal frame costs, THEN shows the image in 1 frame. The `text` characters are included in `flattenTextByFile()` and cost frames in `buildTimeline()`.

---

### Scrolling
Terminal-style scrolling: text pushes up when it exceeds the visible area. `scrollOffset` is calculated from `cursorVisualLine`. The scrolling `div` uses `transform: translateY(-${scrollOffset}px)` — no CSS transitions.

### Audio
Each keystroke maps to a sound file via semantic categorization (`space.wav`, `backspace.wav`, `enter.wav`, generic keystrokes). Audio is synced frame-perfectly using Remotion `<Sequence>` + `<Audio>`. `cursor-jump` events are silent.

### Cursor XY Positioning
The cursor's X position is calculated by simulating CSS word-wrap (finding the last space before `CHARS_PER_LINE` limit). The emoji picker panel uses these coordinates to float at the cursor's position.

---

## Themes

The theme system controls the entire visual identity. Pass a `theme` prop to `Typewriter`, `EditorWindow`, or `TypewriterText`.

```tsx
import { darkEditorTheme } from "./themes";
<Typewriter theme={darkEditorTheme} />
```

**Available themes:** `ivoryTheme`, `darkEditorTheme`, `chalkBlackboardTheme`, `paperNotebookTheme`, `retroTerminalTheme`, `spotlightTheme`, `lcdTerminalTheme`, `pixelArtTheme`.

Each `Theme` object defines 7 layers:

| Layer | Controls |
|---|---|
| `editor` | Window chrome — title bar bg, dot colors, border radius, `showChrome` toggle |
| `canvas` | Typing surface — text color, cursor color/width, active line bg, ghost text, selection |
| `syntax` | Syntax highlighting palette — keyword, string, comment, tag, etc. (passed to `tokenizeLine`) |
| `popup` | Emoji picker + IME panel — bg, border, shadow, selected item styling |
| `outer` | Background behind the editor — solid color, gradient, or blurred image |
| `font` | Font family (`@remotion/google-fonts` ID or `localFile` for bundled .woff2) |
| `effects` | Optional visual effects — CRT scanlines, text glow, ruled lines, chalk texture, LCD bezel |

**Local fonts:** Themes can bundle `.woff2` files in `public/fonts/` using `localFile` + `localFamily` fields (loaded via `@remotion/fonts`). Currently bundled: Geist Pixel Square (retro terminal, LCD terminal), Geist Pixel Circle (pixel art).

**LCD Bezel:** The `lcdBezel` effect wraps the editor in a physical chassis frame with corner screws, inset shadows for recessed depth, and a hard block shadow. Configure via `lcdOuterFrameColor`, `lcdOuterFrameWidth`, and `lcdBezelShadow`.

The `showChrome: false` setting (Chalk, Paper, Terminal themes) hides the macOS title bar and traffic light dots.

---

## Editor Layout

The editor wraps text automatically. When writing code blocks, check `CHARS_PER_LINE` in `TypewriterText.tsx` for the exact wrap limit. All layout constants (line height, padding, visible lines, etc.) are defined in `TypewriterText.tsx` and `EditorWindow.tsx`.

---

## Drawing Layer (ExcalidrawCanvas)

Hand-drawn diagram primitives using rough.js (same rendering library as Excalidraw). Renders `DrawingElement[]` as animated SVG paths with Virgil handwriting font.

### Key Files

| File | Purpose |
|---|---|
| `src/ExcalidrawCanvas.tsx` | Core component — rough.js generator + SVG rendering + stroke animation |
| `src/drawing-types.ts` | Type definitions — `DrawingElement`, `DrawingThemeConfig`, helper types |
| `src/ExcalidrawDemo.tsx` | Demo composition — system architecture diagram showcasing all features |

### Usage

```tsx
import { ExcalidrawCanvas } from "./ExcalidrawCanvas";
import { ivoryTheme } from "./themes";
import type { DrawingElement } from "./drawing-types";

const elements: DrawingElement[] = [
    { id: "box", type: "rectangle", x: 400, y: 300, width: 260, height: 120,
      appearAtFrame: 0, drawDurationFrames: 30, label: "Hello" },
];

<ExcalidrawCanvas elements={elements} theme={ivoryTheme} />
```

### Element Types

| Type | rough.js method | Requires | Description |
|---|---|---|---|
| `rectangle` | `gen.rectangle()` | `x, y, width, height` | Box with optional label |
| `ellipse` | `gen.ellipse()` | `x, y, width, height` | Oval/circle with optional label |
| `diamond` | `gen.polygon()` | `x, y, width, height` | Rotated square (decision node) |
| `arrow` | `gen.linearPath()` | `x, y, points` | Polyline with hand-drawn arrowhead(s) |
| `line` | `gen.linearPath()` | `x, y, points` | Polyline without arrowheads |
| `freedraw` | `gen.curve()` / `gen.path()` | `x, y, points` or `pathData` | Freehand curve |
| `text` | SVG `<text>` | `x, y, label` | Text label (Virgil font) |

### DrawingElement Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | `string?` | — | Stable ID (used for deterministic rough.js seed) |
| `type` | `DrawingElementType` | — | **Required.** One of 7 types above |
| `x`, `y` | `number` | — | **Required.** Top-left position (SVG viewBox coords) |
| `width`, `height` | `number?` | 200, 100 | Shape dimensions (rectangle, ellipse, diamond) |
| `points` | `[number, number][]?` | — | Polyline points for arrow/line/freedraw (relative to x,y) |
| `pathData` | `string?` | — | Raw SVG path data for freedraw |
| `label` | `string?` | — | Text displayed inside/near the shape |
| `labelFontSize` | `number?` | theme | Override label size |
| `labelPosition` | `LabelPosition?` | `"center"` | `center` / `above` / `below` / `left` / `right` |
| `appearAtFrame` | `number` | — | **Required.** Frame to start drawing |
| `drawDurationFrames` | `number` | — | **Required.** Frames for stroke animation |
| `stroke` | `string?` | theme | Stroke color |
| `strokeWidth` | `number?` | theme | Stroke width |
| `fill` | `string?` | `"none"` | Fill color (pass rgba for translucent fills) |
| `fillStyle` | `FillStyle?` | `"hachure"` | `hachure` / `solid` / `zigzag` / `cross-hatch` / `dots` |
| `strokeStyle` | `StrokeStyle?` | `"solid"` | `solid` / `dashed` / `dotted` |
| `roughness` | `number?` | 2.5 | Hand-drawn wobble (0 = smooth, 3 = very rough) |
| `opacity` | `number?` | 1 | Element opacity (0–1) |
| `rotation` | `number?` | — | Rotation in degrees |
| `startArrowHead` | `ArrowHeadType?` | `"none"` | Start arrowhead (`arrow` / `none`) |
| `endArrowHead` | `ArrowHeadType?` | `"arrow"` | End arrowhead (`arrow` / `none`) |

### Theme Integration

Each theme has an optional `drawing` field (`DrawingThemeConfig`):

```ts
drawing: {
    stroke: "#374151",       // default stroke color
    strokeWidth: 2.5,        // default stroke width
    fill: "none",           // default fill
    roughness: 2.5,          // default roughness
    labelColor: "#111111",   // text label color
    labelFont: "Virgil, ...",// label font stack
    labelSize: 28,           // label font size
    arrowHeadSize: 18,       // arrowhead triangle size in px
}
```

### Animation

- **Stroke draw-on**: `stroke-dashoffset` animated from full path length to 0 over `drawDurationFrames`. Eased with `Easing.out(Easing.cubic)`.
- **Fill reveal**: `fillOpacity` fades from 0 to 1 alongside stroke animation.
- **Label fade-in**: Text fades in over 10 frames *after* the stroke animation completes.
- **Path length estimation**: DOM-free `estimatePathLength()` walks SVG path commands (M/L/C/Q/Z) for headless SSR compatibility.

### TypewriterOverlay (Editor Annotations)

The `TypewriterOverlay` component renders `ExcalidrawCanvas` inside the editor content area, enabling annotations on top of typewriter text (underlines, margin labels, arrows between lines).

```tsx
import { TypewriterOverlay } from "./TypewriterOverlay";

<EditorWindow title="auth.ts" theme={theme}
    overlay={<TypewriterOverlay elements={annotations} theme={theme} />}
>
    <TypewriterText segments={segments} startFrame={5} theme={theme} />
</EditorWindow>
```

**Coordinate system** (relative to editor content div, including padding):

| Constant | Value | Description |
|---|---|---|
| `PAD_TOP` | 30px | Top padding before first line |
| `PAD_LEFT` | 40px | Left padding before text |
| `LINE_HEIGHT` | 44px | Vertical spacing per line |
| `CHAR_WIDTH` | 15.6px | Monospace character width (JetBrains Mono 26px) |

**Position formulas:**
- Line N top: `y = 30 + N × 44`
- Line N bottom: `y = 30 + N × 44 + 40`
- Char M left edge: `x = 40 + M × 15.6`

> **⚠️ Timing:** Overlay `appearAtFrame` must be *after* the referenced text has finished typing. Calculate the target text's completion frame from `buildTimeline()` output. A drawing storytelling guide (similar to `aroll-sync.md`) is pending — to be developed from production practice.


