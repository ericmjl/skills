# Avatar + Animated Overlays

Overlay animated titles, topic graphics, captions, and progress indicators on top of a talking-head video — synced to speech. The original video stays full-frame, untouched.

## Input

User provides a 9:16 talking-head video file (place in `public/avatar.mp4`). Selfie-style shot where the face is in the lower 60% of the frame, with open space above.

## Workflow

### Step 1: Transcribe & Plan

Transcribe `public/avatar.mp4` using Whisper. Analyze the transcript to identify:

- Total duration (set composition length to match the video)
- 3-5 key topic segments with their start timestamps
- For each segment, propose an overlay graphic for the top portion of the frame (above the head). Options:
  - Topic title with large step number (e.g., "01" faded in background, "Elements of AI" as headline)
  - Keyword pill/badge highlighting the current topic
  - Simple animated icon or diagram illustrating the concept
  - Progress bar or step indicator showing position in video
  - Animated caption/quote pulling a key phrase

Present transcript segments and proposed overlays. **Wait for approval** before coding.

### Step 2: Build

**BASE LAYER — Full-frame avatar video**:
- `<OffthreadVideo src={staticFile("avatar.mp4")} />` filling the entire 1080x1920 composition
- `style={{ width: "100%", height: "100%", objectFit: "cover" }}`
- Background layer: plays from frame 0 for the full duration
- Audio from this video is the composition's audio track
- Do NOT crop, resize, split, or put in a panel — it IS the full frame

**OVERLAY LAYER — Animated graphics** (top ~35% of frame, above the head):
- Use `AbsoluteFill` on top of the video layer
- All graphics positioned in top portion (y: 150px to ~700px)
- Subtle dark gradient overlay ONLY in top 40% (transparent at bottom, `rgba(0,0,0,0.6)` at top) so white text is readable

**Overlay style per segment**:
- Large faded step number ("01", "02", etc.) — Inter 800, ~200px, `rgba(255,255,255,0.08)`
- Topic headline below it — Inter 700, 56-64px, white
- Keyword badge — small rounded pill with glass-morphism background, 32px text
- Animated progress bar under badge — thin line filling to show segment progress, accent `#22c55e`
- Each overlay enters with `spring({ damping: 200 })` at segment start timestamp
- Previous overlay fades out (opacity 0 over 10 frames) as new one enters
- Use `Sequence` components with `from={Math.round(timestamp * fps)}` to sync to speech

**OPTIONAL BOTTOM OVERLAY — Captions**:
- If word-level timestamps available from Whisper, add animated captions in lower portion (above bottom safe zone, around y: 1600-1700px)
- Bold white text, 36px, subtle text shadow for readability
- Highlight current word in accent color (`#6366f1`)

## Visual Style

Dark theme from `defaults.md`. Accents: `#6366f1` (indigo) and `#22c55e` (green).

## Duration

Matches the input video duration. Not a fixed length.

## Output

- Remotion composition at 1080x1920, 30fps (same as input)
- Launch `npx remotion studio` for preview
