# Typewriter as B-Roll: A-Roll Sync Choreography

Use this guide when the typewriter is used as **B-roll synced to narration audio (A-roll)**, not as a standalone video. The typewriter becomes a "teacher's blackboard" — board notes appear in sync with what the speaker is saying.

## Start with ONE Scene

Do **not** choreograph the entire video at once. Pick the opening or the most representative 30–60 second section and choreograph it first.

1. **Prototype** — Write segments for one scene (~30–60s)
2. **Get user feedback** — Iterate 3–5 rounds, each focusing on ONE principle (timing, density, visual storytelling, etc.)
3. **Extract principles** — Once the user says the scene works, document what made it work as explicit rules
4. **Scale** — Apply those principles to all remaining chapters in a single pass
5. **Polish in layers** — After the full rough draft, add richer elements one type at a time (see Composition Layers below)

This prevents burning tokens on 15 minutes of content that's built on wrong assumptions. One validated scene is worth more than a full draft that misses the timing.

## The `delayFrames` Property

`delayFrames` on a `TextSegment` tells the engine: "don't start this segment until this many frames have elapsed since the composition started." It overrides the natural sequential timing.

```tsx
{ text: "关键概念", mode: "deliberate", delayFrames: s(12.5) }
// → this segment starts exactly at 12.5s into the composition
```

### How it works (in `buildTimeline`)

When a segment has `delayFrames`, the engine calculates idle time:

```
if (segment.delayFrames > totalFrames) totalFrames = segment.delayFrames;
```

This means `delayFrames` is **absolute** (relative to composition start), not relative to the previous segment.

### The OFFSET Pattern for Multi-Chapter

Each chapter lives in its own Remotion `<Composition>` starting at frame 0, but the A-roll timestamps are absolute. Use an OFFSET constant:

```tsx
const CH3_OFFSET = 228; // A-roll seconds where this chapter starts

// Speaker says "帕斯卡赌注" at 262.0s absolute
// Composition-relative: 262.0 - 228 = 34s
// J-cut 0.5s earlier: 33.5s
{ text: "# 帕斯卡赌注", mode: "burst", delayFrames: s(261.5 - CH3_OFFSET) }
```

### The `s()` Helper

```tsx
const FPS = 30000 / 1001; // NTSC 29.97fps
const s = (seconds: number) => Math.round(seconds * FPS);
```

## Timing Anchor Formula

> ⚠️ **The primary constraint: text must FINISH typing when the speaker finishes the phrase.** The J-cut lead-in is a natural consequence, not the starting point.

For each segment synced to a spoken phrase:

```
delayFrames = phrase_end_frame − typing_cost
```

Where:
- `phrase_end_frame` = `s(end_timestamp - OFFSET)` — when the speaker finishes saying this phrase
- `typing_cost` = `printable_chars × mode_speed` (see Frame Cost Reference below)
- `printable_chars` = characters **excluding** `\n` (newlines cost 0 frames)

### Example

Speaker says "relaxation" ending at 5.2s, segment text is `"relaxation\n"` (10 printable chars + 1 newline), using `burst` mode:

```tsx
// typing_cost = 10 × 2 = 20 frames
// phrase_end_frame = s(5.2) = 156 frames
// delayFrames = 156 - 20 = 136 frames ≈ 4.53s
{ text: "relaxation\n", mode: "burst", delayFrames: s(5.2) - 10 * 2 }
```

This means the segment starts ~0.67s before the phrase ends → text finishes exactly at phrase end. The J-cut "lead-in" happens automatically.

### Simplified shortcut

For quick mental math, if you know text should APPEAR roughly 0.3–0.5s before speech start, use:

```tsx
delayFrames: s(speech_start - 0.5 - OFFSET)
```

But **always validate** that typing finishes before the next phrase starts.

## FLOW vs. Anchor — When to Omit `delayFrames`

> ⚠️ **Rule**: Only use `delayFrames` on the FIRST segment of each narrative beat (roughly every 3–5 seconds of narration). Let subsequent segments within the same beat flow naturally by omitting `delayFrames`.

If you use `delayFrames` on every segment, you WILL create unnatural cursor stalls where the typing freezes mid-sentence while waiting for the next anchor. The engine implements `delayFrames` as an absolute frame jump — if the previous segment finishes early, the cursor sits idle until the delay point.

| Pattern | When to use | Implementation |
|:--------|:-----------|:---------------|
| **Anchor** | Section starts, topic changes, narration sync points | `delayFrames: s(timestamp)` |
| **FLOW** | Mid-sentence, same narrative unit, rapid lists | Omit `delayFrames` entirely |

```tsx
// ✅ CORRECT: anchor at section start, flow within
{ text: "> 本视频所有 B-roll = 我 ✅\n", delayFrames: s(24.0) },  // ANCHOR
{ text: "Ray 已经在好几个视频里用过我了\n" },                      // FLOW
{ text: "之前的视频也有我 ↓\n", delayFrames: s(28.0) },           // ANCHOR (new beat)

// ❌ WRONG: anchor on every segment → mid-line stall
{ text: "> 本视频所有 B-roll = 我 ✅\n", delayFrames: s(24.0) },
{ text: "Ray 已经在好几个视频里用过我了\n", delayFrames: s(26.0) }, // STALL!
```

### How stalls happen

If the first segment finishes at frame 750 and the next has `delayFrames: s(26.0)` = frame 779, the cursor sits idle for 29 frames (~1s). This is fine between sections, but devastating mid-sentence — the user sees the cursor freeze in the middle of a phrase like "观众留言".

### Guideline for anchor spacing

- **Minimum 3s** between consecutive `delayFrames` anchors
- **Within a beat** (2-3 consecutive segments about one point): only the first gets `delayFrames`
- **List items** ("一、二、三、四"): only the first item gets `delayFrames`; rest flow

## Five Choreography Principles

### P1: Speech-Match（语音匹配）

Board note = **simplified version** of what the speaker is saying. Never unrelated text. The teacher writes what they're explaining, not something different.

### P2: J-Cut Timing（画面先完成）

- Board note starts **0.3–0.5s before** the speaker says the phrase
- Board note **finishes typing before** the speaker moves on
- Use `burst` + short `deliberate` to finish within the timing window

**J-Cut Implementation Formula:**

```
narration_timestamp: 10.0s  ("narrator says X")
delayFrames anchor:  s(9.5)  ← lead by 0.5s
segment typing cost: ~1.2s
segment finishes at: 10.7s   ← narrator is still saying X ✅
```

For the Timing Anchor Formula (mathematical approach):
```
delayFrames = phrase_end_frame − typing_cost
```

For the quick shortcut (intuitive approach):
```tsx
delayFrames: s(speech_start - 0.5 - OFFSET)
```

Both approaches work — the Timing Anchor Formula is more precise, the shortcut is faster for drafting. Use the formula when timing is tight (<2s between phrases), and the shortcut for initial choreography.

### P3: Density ≈ 5s/note

- Max blank gap: 6 seconds
- Target: one board note every 4–6 seconds
- Fill gaps with: strike text reveals, emoji reactions, short commentary, logical connectives
- Cursor blinking alone is OK but never for more than 5 consecutive seconds

### P4: PPT Standalone（板书独立可读）

The board must make sense **on its own**, like a PowerPoint slide. If you pause the video, what's on screen should be coherent and informative.

- Include **concrete references** the speaker mentions (video titles, person names, company names)
- Think: "What would a teacher write on the blackboard?"

**P4a: Build the argument, not just the conclusion.** When the speaker explains a logical framework (e.g., Pascal's Wager, a 2×2 matrix, a comparison), show each step of the reasoning AS the speaker explains it. Don't wait until the end to show the final matrix. The board is a thinking aid — it should build up, not just appear fully formed.

> ❌ Speaker spends 60s explaining Pascal's Wager → board only shows decision matrix at the end
> ✅ Speaker says "如果上帝存在" → board types that row; speaker says "如果上帝不存在" → board types that row → matrix builds step by step

### P5: Rapid Reveal（快速揭示）

When the speaker is about to cut away (e.g., to an ad, to the next chapter), lists and previews must burst out **instantly** — no individual `delayFrames` between items.

```tsx
// Speaker says "四个维度" then cuts to ad at 60s
// All 4 items burst out immediately after the title
{ text: "# 四个维度\n\n", mode: "burst", delayFrames: s(57.2 - OFFSET) },
{ text: "一、你买的到底是哪一层？\n", mode: "burst" },  // no delay
{ text: "二、物理世界的 AI\n", mode: "burst" },           // no delay
{ text: "三、做难以规模化的事\n", mode: "burst" },         // no delay
{ text: "四、一千个小时\n", mode: "burst" },               // no delay
```

## Timing Budget Rule

> ⚠️ **Every segment has a timing budget** = its `delayFrames` to the next segment's `delayFrames`. The segment's total frame cost **must** fit within this budget. Failing to check this is the #1 cause of A-roll sync issues in production.

### Frame Cost Reference (from engine constants)

| Feature | Frame cost | Notes |
|---------|-----------|-------|
| **burst** | `chars × 2` | +1 jitter per char |
| **normal** | `chars × 3` | +1 jitter per char |
| **deliberate** | `chars × 5 + 3` | +2 jitter per char, +3 pauseBefore |
| **thinking** | `chars × 2 + 14` | +1 jitter per char, +14 pauseBefore |
| **Strike text** | type cost + `strikePauseFrames` (default 20) + delete cost + 4 | Delete: backspace = `chars × 2`, select = `chars + 11` |
| **IME input** | pinyin typing + `imePauseFrames` (default 18) per char | Each CJK char ≈ 15-20 extra frames |
| **Ghost text** | `ghostPauseFrames` (default 30) + 2 | Pause while ghost is visible, then Tab accept |
| **Emoji picker** | label typing + `emojiPickerFrames` (default 20) + 2 | Early-stop when filter narrows to 1 match |
| **Newline `\n`** | 0 extra frames | But adds a line, affecting visual density |

### Mode Selection by Interval

| Interval to next `delayFrames` | Safe mode | Max chars (approx) |
|-------------------------------|-----------|-------------------|
| < 1.5s (< 45 frames) | burst only | ~20 chars |
| 1.5–3s (45–90 frames) | burst or normal | burst: 40, normal: 25 |
| 3–5s (90–150 frames) | any mode | normal: 40, deliberate: 25 |
| > 5s (> 150 frames) | any mode + effects | Room for strike/IME/ghost |

### Quick Mental Check

Before setting a mode, do this in your head:

```
chars × mode_speed < gap_to_next_delayFrames
```

Example: "反观我们 Vibe Code 什么？" = 16 chars, gap = 45 frames
- normal: 16 × 3 = 48 > 45 ❌ OVERRUN
- burst: 16 × 2 = 32 < 45 ✅

### Post-Choreography Validation (mandatory)

After choreographing all segments for a chapter, **before rendering**, check for:

1. **OVERRUN** — segment typing cost > gap to next `delayFrames` → text mid-line when speaker moves on. Fix: switch to burst or shorten text
2. **LONG WAIT** (> 3s gap) — segment finishes too fast, cursor idle for seconds. Fix: add transitional text, commentary, or adjust `delayFrames`
3. **Effect stacking** — strike/IME/ghost in a segment adds hidden frame costs that squeeze the next segment

For 50+ segment videos, **do not rely on mental math**. Write a quick loop to check:

```tsx
segments.forEach((seg, i) => {
    const next = segments[i + 1];
    if (!next?.delayFrames) return;
    const speed = { burst: 2, normal: 3, deliberate: 5, thinking: 2 }[seg.mode] || 3;
    const cost = seg.text.length * speed;
    const gap = next.delayFrames - (seg.delayFrames || 0);
    if (cost > gap) console.warn(`⚠️ Seg ${i} OVERRUN: ${cost} frames > ${gap} gap`);
    if (gap - cost > 90) console.warn(`⏸️ Seg ${i} LONG WAIT: ${gap - cost} frames idle`);
});
```

## Multi-Chapter Composition Architecture

For long videos (10+ minutes), split into per-chapter compositions:

### Frame Calculation for Multi-Chapter Series

> ⚠️ **Do NOT use `Math.ceil(FPS * seconds)` for chapter durations in a Series.** `Math.ceil` always rounds up, causing unidirectional drift — each chapter adds up to 1 extra frame, and after 7 chapters the B-roll can be 3-7 frames ahead of the A-roll.

Use **boundary subtraction** — convert each chapter's start/end timestamp to an absolute frame position, then subtract:

```tsx
const FPS = 30000 / 1001;
const frameAt = (seconds: number) => Math.round(seconds * FPS);

// Chapter boundaries from captions (seconds)
const boundaries = [0, 44.2, 125.8, 301.1, 426.5, 581.0, 762.3, 786.0];

// Each chapter's frame count = next boundary frame - current boundary frame
const chapterFrames = boundaries.slice(1).map((end, i) =>
    frameAt(end) - frameAt(boundaries[i])
);

// Total frames = frameAt(last boundary)
// All chapters sum to exactly this — zero cumulative drift
```

Register each chapter in `Root.tsx`:
```tsx
<Composition id="ch2-ranking" component={Ch2Comp}
             durationInFrames={chapterFrames[2]} fps={FPS}
             width={1920} height={1080} />
```

### Two-Phase Render Strategy

**Phase 1: Preview** — Render individual chapter comps in Remotion Studio for quick iteration. Each chapter is 1-3 minutes, renders in seconds per frame, fast feedback.

**Phase 2: Export** — Create a `FullBRollComp` master composition that sequences ALL chapters using `<Sequence>` with `frameAt` positions. This is the single file you drop into FCP.

```tsx
export const FullBRollComp: React.FC = () => (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e" }}>
        <Background />
        {/* No A-roll audio — keyboard sounds only */}
        <Sequence from={frameAt(boundaries[0])}>
            <ChapterBRoll segments={Ch0Segments} file="notes.md" />
        </Sequence>
        <Sequence from={frameAt(boundaries[1])}>
            <ChapterBRoll segments={Ch1Segments} file="框架.md" />
        </Sequence>
        {/* ... all chapters sequenced at their boundary frame positions ... */}
    </AbsoluteFill>
);
```
```

**In FCP:** Drop `full-broll.mp4` on top of the A-roll timeline. Frame 0 = second 0. No manual offset needed. Keyboard typing sounds mix naturally under the voice.

### Clean Board = File Switch

Each chapter starts with a new `file: "维度X.md"` → the editor "opens a new tab" → previous board is cleared. This is the visual equivalent of erasing the blackboard.

## Composition Layers — Build in Passes

After the full rough draft exists (text choreography across all chapters), layer in richer elements **one type at a time**. This maintains consistency and prevents mixing concerns.

| Pass | What to add | Guideline |
|:-----|:-----------|:----------|
| 1 | **Text choreography** | All board notes with correct `delayFrames`, density ≈ 5s/note, J-cut timing |
| 2 | **Images** | Inline screenshots and image stacks at the moments the speaker references them |
| 3 | **IME emphasis** | ONE thematic anchor word per chapter (max 4 chars) |
| 4 | **Ghost text** | Rhetorical questions, audience pushback, inevitable conclusions |
| 5 | **Strike text** | Narrative turns and meaning reversals (1–2 per chapter max) |
| 6 | **Visual polish** | Theme, contrast, background, 5K resolution (see below) |
| 7 | **Export** | Master `FullBRollComp`, no A-roll audio |

### 5K Resolution for FCP Compositing

For A-roll sync B-roll destined for Final Cut Pro, **render at 5K (5120×2880)** using the `Canvas5K` wrapper. This gives you room to Ken Burns / reframe on a 4K timeline without losing sharpness.

```tsx
// Root.tsx — 5K composition
<Composition
    id="Typewriter5K"
    component={() => <MyComp />}  // MyComp wraps content in <Canvas5K>
    durationInFrames={frames(DURATION)}
    fps={FPS}
    width={5120}
    height={2880}
/>
```

Inside your component, wrap everything in `<Canvas5K>` — children lay out at 1920×1080 and the CSS transform handles the upscale.

For quick drafts or social media, 1080p is fine — 5K is only needed when compositing in a 4K NLE.

Do NOT mix passes — e.g., don't add IME emphasis while still fixing text timing. Each pass should commit before moving to the next.

## Timestamp Extraction Workflow

1. Get word-level captions (ElevenLabs STT or YouTube auto-subs) as JSON
2. Run a script to group words into sentences (split on `。？！`)
3. Filter for the chapter's time range
4. Identify key phrases → map to board notes with J-cut timing

```python
# Quick sentence-level extraction
import json
with open('captions.json') as f:
    caps = json.load(f)
for c in caps:
    s = c['startMs']/1000
    if START < s < END:
        print(f'{s:6.1f}  {c["text"]}')
```

## Duration from Audio

The composition duration should be derived from the A-roll audio, not set arbitrarily.

### Step 1: Get exact audio duration

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 aroll.mp3
# → 12.996000
```

### Step 2: Add tail buffer

The last segment's `delayFrames + typing_cost` typically extends beyond the audio end (e.g., ghost text punchline + attribution tail). Set:

```tsx
const AUDIO_DURATION = 12.996; // from ffprobe
const TAIL_BUFFER = 2;         // seconds for last segment to complete + 1-2s hold
const VIDEO_DURATION = AUDIO_DURATION + TAIL_BUFFER;
```

The video will be slightly longer than the audio — this is correct for FCP. Just align start points on the timeline.

## Preview Workflow

Before rendering the final video, **preview sync with the A-roll audio embedded** in Remotion Studio. Without this, you can't verify timing without exporting to FCP first.

### Setup

1. Copy the A-roll audio to `public/aroll.mp3`
2. Create a preview composition in `Root.tsx`:

```tsx
import { Audio } from "remotion";
import { staticFile } from "remotion";

const TypewriterPreview: React.FC = () => (
    <>
        <Audio src={staticFile("aroll.mp3")} volume={1} />
        <MyTypewriterComp />  {/* your actual typewriter content */}
    </>
);

// In RemotionRoot:
<Composition
    id="TypewriterPreview"
    component={TypewriterPreview}
    durationInFrames={frames(VIDEO_DURATION)}
    fps={FPS}
    width={1920}
    height={1080}
/>
```

### Usage

- **Preview**: Use `TypewriterPreview` in Remotion Studio — play through to verify text lands on the right narration beats
- **Final render**: Use the composition **without** audio (e.g., `Typewriter` or `Typewriter5K`) — FCP provides the A-roll audio track

> 💡 Always preview sync in Studio before rendering. A 2-minute Studio playback catches timing errors that would cost 10 minutes of render + FCP import.

## Common Pitfalls

### IME is too slow for tight sync
When A-roll timing is tight (<3s per phrase), use `mode: "burst"` or `mode: "deliberate"` **without** `imeInput`. IME adds multiple keystrokes per character and may not finish in time. Reserve IME for moments with breathing room.

**Speed tip**: For punchy emphasis within tight windows, use `mode: "burst", imeInput: true, imePauseFrames: 8` — this types just 1 pinyin letter per character with a short 8-frame candidate panel. A 4-char word completes in ~40 frames (1.3s).

### Strategic IME: one word per chapter
Don't scatter IME everywhere. Pick **one thematic anchor word per chapter** (max 4 chars, prefer 1-2) and make it IME. This creates a rhythmic "weight moment" that viewers feel without being overwhelmed. Examples: `财富转移`, `坍塌`, `护城河`, `入场券`.

### Ghost text for rhetorical beats
Use ghost text not just for code autocomplete, but as a **storytelling device for predictable/obvious thoughts**. Type 2-3 opening characters, then the rest appears as gray autocomplete. Best for audience pushback ("又来…制造焦虑了？"), rhetorical questions ("谁不…想？"), and statements where the conclusion is inevitable ("人的…价值在哪儿？").

### Density gaps from not following the speaker closely enough
The biggest recurring issue: the agent skips 20-30 seconds of narration because it doesn't see "board-worthy" content. **Everything the speaker says has potential board notes.** Even transitional phrases can become commentary, questions, or short connectives on the board.

### Board notes that are conclusions without the argument
Example: showing the decision matrix ONLY at the end of Pascal's wager explanation, but not showing the logic DURING the explanation. Fix: build the argument step-by-step on the board AS the speaker explains it.

### Lists that appear too slowly
When the speaker rattles off a list ("摄影不存在了，剪辑不存在了，编程不存在了"), the board notes should burst out in rapid succession — no individual `delayFrames` between items in the list.

### Studio showing only the default composition
When you have multiple compositions, the Studio defaults to the first one. **Each chapter must be registered as its own `<Composition>` in Root.tsx.** Select the chapter from the Studio sidebar dropdown.

### Inline images breaking timeline sync
When an image segment adds alt text + `\uFFFC` marker to the flat text, `buildTimeline()` must emit instant `char` events for those characters. Without them, `globalCharIndex` falls out of sync with `flattenTextByFile`, and all subsequent segments slice the wrong part of the flat text.

### Sponsor chapters

Sponsor segments work great as typewriter. Full pattern:

1. **Read** the sponsor section in the transcript — identify key selling points (pricing, features, UX)
2. **Capture screenshots** from the sponsor's website — logo, pricing page, feature highlights. Focus on what the speaker specifically mentions. Small, focused crops > full-page screenshots
3. **Create** a `sponsor.md` file in the typewriter editor
4. **Choreograph** as normal board notes — type key selling points, each screenshot appears as an inline image when the speaker mentions that feature
5. **Tone** should be natural — a genuine recommendation, not a sales pitch. The typewriter's editorial voice helps here

### Commit-before-risk protocol

Commit before any change that could break the known-good state:

- **Major choreography moves** — adding a new chapter, restructuring segment order, changing timing across many segments
- **New engine features** — imageStack, 5K canvas upgrade, new component types
- **Visual polish passes** — theme/contrast changes that touch global styles

This lets you `git diff` to see exactly what changed and `git checkout` to recover if something goes wrong. Most choreography sessions should have 5–10 commits.
