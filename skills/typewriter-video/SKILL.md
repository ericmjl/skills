---
name: typewriter-video
description: >
  Create VS Code-style typewriter animation videos with mechanical keyboard sounds.
  Supports 4 typing speeds, ghost text autocomplete, strikethrough corrections,
  emoji picker, file tab switching, syntax highlighting (6 languages), Chinese IME
  (pinyin + direct mode), inline images, image stacks, animated checkboxes,
  Excalidraw hand-drawn diagrams, 8 visual themes, 4 sound packs, and
  A-roll narration sync. Built on Remotion (React-based video rendering). Use when the user wants to
  create code typing videos, explainer B-roll, or typewriter-style animations.
compatibility: Requires Node.js >= 18, npm. Works with any terminal-capable agent.
license: MIT
metadata:
  author: yammaku
  version: "1.1"
---

# Typewriter Video

Create professional typewriter animation videos — a VS Code-style editor where text appears character-by-character with mechanical keyboard sounds, images, and visual effects.

## Required: Install the Official Remotion Skill

This skill covers **typewriter-specific** knowledge (segment authoring, features, storytelling). For general Remotion flexibility (compositions, animations, audio, rendering, deployment), install the official Remotion skill maintained by the Remotion team:

→ [github.com/remotion-dev/remotion/tree/main/packages/skills](https://github.com/remotion-dev/remotion/tree/main/packages/skills)

You can use this skill without it, but having it gives you deeper framework knowledge for advanced customization.

## Step 1: Gather Requirements

Before starting, ask the user:
- **Content**: What text should be typed? Does the user have a script, or should you draft one?
- **A-roll sync?**: Standalone typewriter video, or B-roll synced to narration audio? If synced, you need word-level captions (see A-roll sync below).
- **Aspect ratio**: 16:9 (YouTube landscape, default), 9:16 (Shorts/Reels/TikTok), or 1:1 (Instagram)?
- **Theme**: Visual identity — ivory (default), dark-editor, chalk-blackboard, paper-notebook, retro-terminal, spotlight, lcd-terminal, pixel-art?
- **Sound pack**: nk-cream (default, smooth linear), holy-pandas (tactile bump), cream-travel (creamy full travel), turquoise (tealio-style linear)?
- **Background image**: Does the user have one, or should you generate one?

## Step 2: Set Up the Project

Copy the template and install:
```bash
cp -r <skill-path>/assets/template/ ./my-typewriter-video
cd ./my-typewriter-video
npm install
```

### Verify Bundled Assets

The template ships with all required assets. After setup, confirm these exist:

```bash
# Sound packs (4 packs)
ls public/sounds/key_a.wav          # nk-cream (default, 29 files)
ls public/sounds/holy-pandas/       # 8 files: GENERIC_R0-R4.mp3 + ENTER/SPACE/BACKSPACE.mp3
ls public/sounds/cream-travel/      # same structure
ls public/sounds/turquoise/         # same structure

# Fonts (for themes + Excalidraw)
ls public/fonts/Virgil.woff2              # Excalidraw handwriting font
ls public/fonts/GeistPixel-Square.woff2   # LCD Terminal + Pixel Art themes
ls public/fonts/GeistPixel-Circle.woff2   # Pixel Art theme variant
```

> ⚠️ **If any asset is missing**, see [Troubleshooting: Missing Assets](#troubleshooting-missing-assets) at the bottom.

## Step 3: Learn the Engine

Read these in order:
1. **`src/Typewriter.tsx`** — the living tutorial. Read this first to see every feature demonstrated with inline comments.
2. **[API Reference](references/API.md)** — all TextSegment fields, timeline events, constants
3. **[Content Guide](references/content-guide.md)** — storytelling techniques (strike text philosophy, ghost text, IME placement, rhythm)
4. **[Audio Guide](references/audio.md)** — sound system, the critical `startFrame` offset gotcha, sound pack switching, volume guidelines

## Step 4: Write Content in `src/Typewriter.tsx`

Replace `TEXT_SEGMENTS` with the user's content. Key references:

### Typing Modes

| Mode | Speed | When to use |
|------|-------|-------------|
| `burst` | 2f/char | **Default (~70%).** Confident, fast typing |
| `normal` | 3f/char | Transitions, connective text |
| `deliberate` | 5f/char + pause | **Single key words only.** Emphasis |
| `thinking` | 14f pause + fast | Composing next thought |

### Feature Quick Reference

**Ghost text** — gray autocomplete, Tab to accept:
```tsx
{ text: "paragraph. ", mode: "burst", ghostText: "So we use ghost text." }
```

**Strike-correct** — type wrong, then fix:
```tsx
{ text: "a framework", mode: "burst", strikeText: "something", strikeDelete: "select" }
```

**Emoji picker** — catalog search panel:
```tsx
{ text: "😤", mode: "normal", emojiPicker: true }
```

**File switching** — multi-file editor:
```tsx
{ text: "import React\n", mode: "burst", file: "app/page.tsx" }
```

**Syntax highlighting** — VS Code Dark+ palette (tsx, ts, javascript, bash, markdown, css):
```tsx
{ text: "export default function Page() {\n", mode: "burst", language: "tsx" }
```

**Cursor jump + mutation** — edit existing code:
```tsx
{ text: "'use cache'\n", mode: "thinking", insertAt: { line: 0, col: 0 } }
```

**Chinese IME** — two modes (direct 吐字 or pinyin 拼音):
```tsx
{ text: "这是拼音模式", mode: "normal", imeInput: true }
```

**Inline images** — single or multi-row with animations:
```tsx
// Single with fade
{ text: "Preview:\n", mode: "normal", image: { src: "screenshot.png", heightLines: 5, animation: "fade" } }
// Multi-row with labels
{ text: "Tech:\n", mode: "normal", image: {
    items: [{ src: "a.png", label: "React" }, { src: "b.png", label: "Next.js" }],
    width: 85, height: 100, gap: 10, animation: "slide-up", heightLines: 4,
}}
```

**Animated checkboxes** — type `[ ]` then auto-check with spring-pop:
```tsx
{ text: "- [ ] Step one\n", mode: "burst", checkbox: { checkAfterFrames: 20 } }
```

**Image stack** — paper-pile effect:
```tsx
{ text: "Headlines:\n", mode: "normal", imageStack: { images: ["a.png", "b.png"], heightLines: 8, intervalFrames: 8 } }
```

### Theme & Sound Pack

Set in your composition (e.g. `Typewriter.tsx`):
```tsx
import { chalkBlackboardTheme } from "./themes";

<TypewriterText
  segments={TEXT_SEGMENTS}
  theme={chalkBlackboardTheme}
  soundPack="holy-pandas"
/>
```

**Available themes**: `ivoryTheme` (default), `darkEditorTheme`, `chalkBlackboardTheme`, `paperNotebookTheme`, `retroTerminalTheme`, `spotlightTheme`, `lcdTerminalTheme`, `pixelArtTheme`

**Available sound packs**: `"nk-cream"` (default), `"holy-pandas"`, `"cream-travel"`, `"turquoise"`

## Step 5: Set Background Image

Either:
- **User provides**: Copy to `public/background.png`
- **Generate one**: Use an image generation tool, then `cp /path/to/image.png public/background.png`

A subtle, blurred dark workspace or gradient works best — the template applies `blur(4px)` and `saturate(0.9)`.

## Step 6: Configure Aspect Ratio

Edit `width` and `height` in `src/Root.tsx`:

| Format | width | height | Notes |
|--------|-------|--------|-------|
| **16:9 (default)** | **1920** | **1080** | Standard YouTube |
| 5K B-roll | 5120 | 2880 | A-roll sync only. Use `Canvas5K` wrapper |
| 9:16 | 1080 | 1920 | Shorts/Reels/TikTok |
| 1:1 | 1080 | 1080 | Instagram |

> ⚠️ If changing to 9:16 or 1:1, also adjust `EditorWindow.tsx` width and `CHARS_PER_LINE` in `TypewriterText.tsx`.

Don't manually calculate `DURATION_SECONDS` — set a rough value (20s for short, 50s for long), preview, then adjust.

## Step 6b: A-Roll Sync Mode (if B-roll)

> **Skip this step** if the typewriter is a standalone video.

Use `delayFrames` for absolute timing synced to narration:
```tsx
{ text: "Key insight: ", mode: "burst", delayFrames: 90 } // wait until frame 90
```

Read the full choreography guide: [A-Roll Sync Guide](references/aroll-sync.md). It covers:
- Extracting timestamps from captions
- The OFFSET pattern for multi-chapter compositions
- 5 sync principles (Speech-Match, J-Cut, Density, PPT Standalone, Rapid Reveal)
- **Timing Budget Rule** — frame cost per mode, mandatory post-choreography validation
- Frame calculation for multi-chapter Series (boundary subtraction to avoid drift)

## Step 7: Preview

```bash
npm run studio
```

Check: timing, background, content fits, note where typing ends → update `DURATION_SECONDS`.

## Step 8: Render

```bash
npm run render
```

Output: `out/typewriter.mp4`. For multi-chapter A-roll projects, render specific compositions:
```bash
npx remotion render <comp-id> out/<name>.mp4
```

## Project Structure

```
src/
├── TypewriterText.tsx    # Core engine (timeline, audio, rendering, soundPack)
├── Typewriter.tsx        # Your composition (edit this!)
├── EditorWindow.tsx      # macOS window chrome (theme-aware, chrome-less mode)
├── themes.ts             # 8 visual identities (ivory, dark-editor, chalk, paper, retro, spotlight, lcd, pixel)
├── layout.ts             # Layout presets (LANDSCAPE 1920×1080, PORTRAIT 1080×1920)
├── syntaxHighlight.ts    # Syntax tokenizer (tsx, ts, javascript, bash, markdown, css)
├── ExcalidrawCanvas.tsx  # 🧪 Beta — Hand-drawn diagram layer (rough.js + Virgil font)
├── TypewriterOverlay.tsx # 🧪 Beta — Excalidraw overlay mode (editor annotations 800×500)
├── drawing-types.ts      # 🧪 Beta — Drawing element types (rect, ellipse, arrow, line, text, etc.)
├── ExcalidrawDemo.tsx    # 🧪 Beta — System architecture diagram demo
├── ThemeShowcase.tsx     # Cycles all 8 themes (5s each, fade transitions)
├── Canvas5K.tsx          # 5K render wrapper (B-roll production)
├── EmojiPicker.tsx       # Emoji panel UI
├── ChineseDemo.tsx       # Chinese IME demo composition
├── Root.tsx              # Composition registry (1920×1080, 29.97fps)
├── emoji-catalog.json    # 50 curated emojis
└── pinyin-catalog.json   # ~180 pinyin→character mappings

public/
├── sounds/               # nk-cream WAVs (default) + holy-pandas/, cream-travel/, turquoise/ subdirs
├── fonts/                # Virgil.woff2 + GeistPixel-Square.woff2 + GeistPixel-Circle.woff2
└── background.png        # Your background image
```

## Troubleshooting: Missing Assets

If `npm run studio` shows errors about missing files, the template may need asset recovery.

### Missing Sound Packs

If `public/sounds/holy-pandas/`, `cream-travel/`, or `turquoise/` directories are empty or missing:

```bash
# Clone the MechSim repo (source of all keyboard sounds)
git clone --depth 1 https://github.com/cjlangan/MechSim.git /tmp/MechSim

# Copy row-based packs (holy-pandas has flat structure, others use press/ subdir)
rsync -av --include='*.mp3' --exclude='*' /tmp/MechSim/audio/holy-pandas/ public/sounds/holy-pandas/
rsync -av --include='*.mp3' --exclude='*' /tmp/MechSim/audio/cream-travel/press/ public/sounds/cream-travel/
rsync -av --include='*.mp3' --exclude='*' /tmp/MechSim/audio/turquoise/press/ public/sounds/turquoise/

# Verify (each should have 8 files: GENERIC_R0-R4.mp3 + ENTER.mp3 + SPACE.mp3 + BACKSPACE.mp3)
ls public/sounds/holy-pandas/ public/sounds/cream-travel/ public/sounds/turquoise/

# Clean up
rm -rf /tmp/MechSim
```

### Missing Fonts

If themes fail to render text (LCD Terminal, Pixel Art) or Excalidraw shows wrong fonts:

**Geist Pixel fonts** (required by `lcdTerminalTheme` and `pixelArtTheme`):
```bash
# Download from Vercel's Geist font releases
curl -L -o /tmp/geist-pixel.zip "https://github.com/vercel/geist-font/releases/download/1.4.01/geist-font-1.4.01.zip"
unzip /tmp/geist-pixel.zip -d /tmp/geist-font
# Copy the pixel variants
cp /tmp/geist-font/GeistPixel/woff2/GeistPixel-Square.woff2 public/fonts/
cp /tmp/geist-font/GeistPixel/woff2/GeistPixel-Circle.woff2 public/fonts/
rm -rf /tmp/geist-font /tmp/geist-pixel.zip
```

**Virgil font** (required by `ExcalidrawCanvas`):
```bash
# Download from Excalidraw's CDN
curl -L -o public/fonts/Virgil.woff2 "https://unpkg.com/@excalidraw/excalidraw@0.17.0/dist/prod/Virgil.woff2"
```

### Missing nk-cream Sounds

If the default per-letter WAVs are missing (`key_a.wav` through `key_z.wav`):
```bash
git clone --depth 1 https://github.com/cjlangan/MechSim.git /tmp/MechSim
# nk-cream uses letter-named files (a.wav → key_a.wav)
for f in /tmp/MechSim/audio/nk-cream/[a-z].wav; do
  letter=$(basename "$f" .wav)
  cp "$f" "public/sounds/key_${letter}.wav"
done
cp /tmp/MechSim/audio/nk-cream/space.wav /tmp/MechSim/audio/nk-cream/enter.wav /tmp/MechSim/audio/nk-cream/backspace.wav public/sounds/
rm -rf /tmp/MechSim
```
