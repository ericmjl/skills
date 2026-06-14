# Typewriter Audio Engine

Domain knowledge for the typewriter template's keyboard sound system. Read this before modifying audio behavior in `TypewriterText.tsx`.

## How Sound Works in This Template

Each character typed = one `<Sequence>` + `<Audio>` element in the React tree. Remotion extracts all audio at render time, so audio components must be **unconditionally mounted** (never conditionally rendered based on `useCurrentFrame()`).

The template ships with **4 sound packs** switchable via the `soundPack` prop — no code changes needed.

## Sound Packs

### Switching Packs

Pass `soundPack` to `TypewriterText` (or set it in your composition):

```tsx
<TypewriterText
  segments={segments}
  theme={chalkTheme}
  soundPack="holy-pandas"  // "nk-cream" | "holy-pandas" | "cream-travel" | "turquoise"
/>
```

Default is `"nk-cream"` if omitted.

### Pack Details

| Pack | Feel | Mapping | Files |
|:-----|:-----|:--------|:------|
| **nk-cream** (default) | Smooth linear | Per-letter WAV | `key_a.wav` … `key_z.wav` + `space.wav` + `enter.wav` + `backspace.wav` (29 files) |
| **holy-pandas** | Tactile bump | Row-based MP3 | `GENERIC_R0-R4.mp3` + `SPACE.mp3` + `ENTER.mp3` + `BACKSPACE.mp3` (8 files) |
| **cream-travel** | Creamy full travel | Row-based MP3 | Same structure as holy-pandas (8 files) |
| **turquoise** | Tealio-style linear | Row-based MP3 | Same structure as holy-pandas (8 files) |

### File Layout

```
public/sounds/
├── key_a.wav ... key_z.wav   ← nk-cream (flat)
├── space.wav
├── enter.wav
├── backspace.wav
├── holy-pandas/
│   ├── GENERIC_R0.mp3 ... GENERIC_R4.mp3
│   ├── SPACE.mp3
│   ├── ENTER.mp3
│   └── BACKSPACE.mp3
├── cream-travel/
│   └── (same structure as holy-pandas)
└── turquoise/
    └── (same structure as holy-pandas)
```

### Row-Based Mapping

Row-based packs map each character to a keyboard row (R0=number row → R4=bottom row):

| Row | File | Keys |
|:----|:-----|:-----|
| R0 | `GENERIC_R0.mp3` | `1234567890-=` |
| R1 | `GENERIC_R1.mp3` | `qwertyuiop[]\` |
| R2 | `GENERIC_R2.mp3` | `asdfghjkl;'` (home row, also fallback for unmapped chars) |
| R3 | `GENERIC_R3.mp3` | `zxcvbnm,./` |
| R4 | `GENERIC_R4.mp3` | Bottom row (mostly space bar, which uses its own `SPACE.mp3`) |

Chinese characters, emoji, and other non-ASCII fall back to R2 (home row).

## Critical: The startFrame Offset

`TypewriterText` accepts a `startFrame` prop that offsets when typing begins. Visuals use `localFrame = frame - startFrame`. But `<Sequence from={}>` interprets `from` as **global composition time**.

`event.frame` is in **local time** (starts at 0). You must convert:

```tsx
// ✅ Correct — converts local to global time
<Sequence from={startFrame + event.frame} durationInFrames={10}>
    <Audio src={staticFile(soundFile)} volume={0.5} />
</Sequence>

// ❌ WRONG — plays startFrame frames too early!
<Sequence from={event.frame} durationInFrames={10}>
```

If `startFrame={15}`, omitting it means every sound plays 15 frames (~500ms at 29.97fps) before the character appears on screen.

## Timeline Event System

`buildTimeline()` produces `TimelineEvent[]`:

| Event type | When | Sound to play |
|:-----------|:-----|:-------------|
| `char` | Each character in `segment.text` | Per-letter or row key sound |
| `strike-char` | Temporary text being typed (for emoji `:label` and strike-through) | Same as `char` |
| `delete` | Backspace removing a strike-char | Backspace sound (volume 0.45) |
| `select-grow` | Extend blue selection highlight by one char | None (silent) |
| `select-delete` | Wipe all temp text + selection at once | Backspace sound (volume 0.45) |
| `ghost-show` | Ghost preview appears (gray text) | None (silent) |
| `ghost-accept` | User "presses Tab", ghost fills in | Space sound (soft click, volume 0.4) |
| `file-switch` | Switch to a different file tab | Space sound (volume 0.3) |
| `cursor-jump` | Move cursor to a specific line/col | None (silent) |
| `insert-char` | Type character at a specific position (in-place mutation) | Per-letter or row key sound |

**Behavioral notes:**
- Ghost text does NOT generate `char` events. `ghost-accept` jumps `typedLength` forward in one frame.
- Strike text generates `strike-char` events for typing, then `delete` events for backspacing.
- `file-switch` and `cursor-jump` are **always silent** — no audio emitted.
- `insert-char` uses the same sound mapping as `char` (per-letter or row-based).
- All sound paths are resolved by `resolveSound()` — it handles per-letter vs row-based mapping and file extensions (`.wav` vs `.mp3`) automatically.

## Volume Guidelines

| Event | Volume | Notes |
|:------|:-------|:------|
| Normal keys | 0.50–0.60 | Add ±0.05 random jitter per keystroke |
| Space | 0.45–0.55 | Slightly different character |
| Enter | 0.50–0.60 | Distinct heavier feel |
| Ghost-accept (Tab) | 0.35–0.40 | Quiet — it's a passive action |

## Common Pitfalls

1. **Audio conditionally rendered**: Never use `if (frame > X) return null` to skip audio. Remotion needs all `<Audio>` elements mounted always.
2. **Forgetting startFrame**: Always use `startFrame + event.frame` in `<Sequence from>`.
3. **File extension mismatch**: nk-cream uses `.wav`, row-based packs use `.mp3`. The `resolveSound()` function handles this automatically — don't hardcode extensions.
4. **Bracket filenames**: nk-cream includes `[.wav` and `].wav` for bracket keys. These can break in shell commands — quote paths or skip them.

## Audio Credits

All sound packs sourced from [MechVibes](https://mechvibes.com/) / [MechSim](https://github.com/cjlangan/MechSim).
