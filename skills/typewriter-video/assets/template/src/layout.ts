// ═══════════════════════════════════════════════════════════
// Layout Presets — Dimension presets for different aspect ratios
//
// Centralizes all dimension-dependent constants so the entire
// engine adapts to landscape (16:9) or portrait (9:16) with
// a single preset swap. The timeline engine is unaffected —
// only render-phase layout constants live here.
// ═══════════════════════════════════════════════════════════

export interface LayoutPreset {
    name: string;
    // ── Composition (Remotion) ──
    width: number;
    height: number;
    // ── Editor window ──
    editorWidth: number;
    editorHeight: number;
    // ── Text layout ──
    fontSize: number;
    lineHeight: number;        // px per visual line
    charsPerLine: number;      // word-wrap threshold
    maxVisibleLines: number;   // scroll trigger
    padTop: number;            // editor body top padding
    padLeft: number;           // editor body left padding
    padRight: number;          // editor body right padding
    charWidth: number;         // monospace char width in px
    // ── Title bar ──
    titleBarHeight: number;
    dotSize: number;
}

// ── 16:9 Landscape (existing default) ──
export const LANDSCAPE: LayoutPreset = {
    name: "landscape",
    width: 1920,
    height: 1080,
    editorWidth: 880,
    editorHeight: 660,
    fontSize: 26,
    lineHeight: 44,            // 26px font × 1.7
    charsPerLine: 50,          // 800px / 15.6px ≈ 51 → 50
    maxVisibleLines: 12,       // (660 - 44 - 60) / 44 ≈ 12.6, use 12 to leave room for IME popup
    padTop: 30,
    padLeft: 40,
    padRight: 40,
    charWidth: 15.6,           // JetBrains Mono 26px
    titleBarHeight: 44,
    dotSize: 14,
};

// ── 9:16 Portrait (TikTok / Reels / Shorts) ──
export const PORTRAIT: LayoutPreset = {
    name: "portrait",
    width: 1080,
    height: 1920,
    editorWidth: 880,          // full-width in portrait canvas
    editorHeight: 1128,        // 940 × 1.2 — extended 20% from bottom
    fontSize: 26,              // keep same font size for readability
    lineHeight: 44,            // 26px × 1.7 — same as landscape
    charsPerLine: 50,          // same editor width → same chars per line
    maxVisibleLines: 22,       // (1128 - 44 - 60) / 44 ≈ 23, use 22 to leave room for IME popup
    padTop: 30,
    padLeft: 40,
    padRight: 40,
    charWidth: 15.6,           // same font → same char width
    titleBarHeight: 44,
    dotSize: 14,
};

/**
 * Look up a layout preset by name.
 * Returns LANDSCAPE if name is undefined or unrecognized.
 */
export function getLayout(name?: string): LayoutPreset {
    if (name === "portrait") return PORTRAIT;
    return LANDSCAPE;
}
