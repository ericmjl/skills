import React from "react";
import { interpolate, useCurrentFrame, Sequence, Audio, staticFile, Img } from "remotion";
import { loadFont as loadLocalFont } from "@remotion/fonts";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadCaveat } from "@remotion/google-fonts/Caveat";
import { loadFont as loadKalam } from "@remotion/google-fonts/Kalam";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import emojiCatalog from "./emoji-catalog.json";
import pinyinCatalog from "./pinyin-catalog.json";
import { tokenizeLine, type SyntaxLanguage } from "./syntaxHighlight";
import { Theme, ivoryTheme } from "./themes";
import { LayoutPreset, LANDSCAPE } from "./layout";

// ── Dynamic font loading ──
// Google Fonts loaders
const googleFontLoaders: Record<string, () => string> = {
    JetBrainsMono: () => loadJetBrainsMono("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
    Caveat: () => loadCaveat("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
    Kalam: () => loadKalam("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
    Inter: () => loadInter("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
};

// Local font registration cache (only register once)
const registeredLocalFonts = new Set<string>();

function getFontFamily(theme: Theme): string {
    // Explicit family override
    if (theme.font.family) return theme.font.family;

    // Local .woff2 font from public/fonts/
    if (theme.font.localFile && theme.font.localFamily) {
        const family = theme.font.localFamily;
        if (!registeredLocalFonts.has(family)) {
            loadLocalFont({
                family,
                url: staticFile(`fonts/${theme.font.localFile}`),
            });
            registeredLocalFonts.add(family);
        }
        return family;
    }

    // Google Fonts
    const loader = googleFontLoaders[theme.font.loadId];
    return loader ? loader() : "monospace";
}

// ═══════════════════════════════════════════════════════════
// Timing engine v7 — with ghost text support.
//
// Modes: burst, normal, deliberate, thinking, ghost
//
// Ghost text flow:
//   1. Type trigger text char-by-char (mode from triggerMode)
//   2. Ghost preview fades in (gray, 40% opacity)
//   3. Pause (thinking)
//   4. Tab press — ghost becomes real text instantly
// ═══════════════════════════════════════════════════════════

export type TypingMode = "burst" | "normal" | "deliberate" | "thinking";

// ── Sound pack system ──
export type SoundPack = "nk-cream" | "holy-pandas" | "cream-travel" | "turquoise";

// Keyboard row map for row-based packs (R0=number row → R4=bottom row)
const ROW_MAP: Record<string, number> = {
    // Row 0: number row
    "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0, "0": 0,
    "`": 0, "-": 0, "=": 0,
    // Row 1: QWERTY
    "q": 1, "w": 1, "e": 1, "r": 1, "t": 1, "y": 1, "u": 1, "i": 1, "o": 1, "p": 1,
    "[": 1, "]": 1, "\\": 1,
    // Row 2: home row (ASDF)
    "a": 2, "s": 2, "d": 2, "f": 2, "g": 2, "h": 2, "j": 2, "k": 2, "l": 2,
    ";": 2, "'": 2,
    // Row 3: ZXCV
    "z": 3, "x": 3, "c": 3, "v": 3, "b": 3, "n": 3, "m": 3,
    ",": 3, ".": 3, "/": 3,
};

/**
 * Resolve a sound file path based on the active sound pack.
 * - nk-cream (default): per-letter WAV files flat in sounds/
 * - holy-pandas, cream-travel, turquoise: row-based MP3 files in sounds/{pack}/
 */
function resolveSound(
    type: "key" | "space" | "enter" | "backspace",
    pack: SoundPack,
    char?: string,
    seedIndex?: number,
): string {
    if (pack === "nk-cream") {
        // Per-letter mapping
        if (type === "space") return "sounds/space.wav";
        if (type === "enter") return "sounds/enter.wav";
        if (type === "backspace") return "sounds/backspace.wav";
        // Key
        const lower = (char || "").toLowerCase();
        if (lower >= "a" && lower <= "z") return `sounds/key_${lower}.wav`;
        // Fallback for non-letter chars
        const fallbackLetters = "asdfjkl";
        const idx = Math.floor(seededRandom(seedIndex ?? 0) * fallbackLetters.length);
        return `sounds/key_${fallbackLetters[idx]}.wav`;
    }

    // Row-based packs
    const dir = `sounds/${pack}`;
    if (type === "space") return `${dir}/SPACE.mp3`;
    if (type === "enter") return `${dir}/ENTER.mp3`;
    if (type === "backspace") return `${dir}/BACKSPACE.mp3`;
    // Map char to keyboard row
    const row = ROW_MAP[(char || "").toLowerCase()] ?? 2; // default to home row
    return `${dir}/GENERIC_R${row}.mp3`;
}

export interface TextSegment {
    text: string;
    mode: TypingMode;
    // File tab: when this changes between segments, the editor "opens a new file"
    // — title bar updates, canvas clears. If omitted, inherits previous segment's file.
    file?: string;
    // Language for syntax highlighting. When set, text is rendered with colored tokens.
    // If omitted, inherits previous segment's language (or no highlighting).
    language?: SyntaxLanguage;
    // Insert-at: type text at a specific line/col instead of appending at the end.
    // Cursor jumps to that position first, then types. Existing text shifts down.
    insertAt?: { line: number; col: number };
    // Ghost text: after typing `text`, show `ghostText` in gray,
    // then after a pause, fill it in instantly (Tab accept)
    ghostText?: string;
    ghostPauseFrames?: number; // how long ghost is visible before Tab (default 30)
    // Strike text: type `strikeText` first, pause, then delete it,
    // then type `text`. Creates a "thinking/reconsidering" storytelling effect.
    strikeText?: string;
    strikeMode?: TypingMode;    // typing mode for strikeText (default: same as mode)
    strikePauseFrames?: number; // pause after typing strike before deleting (default: 20)
    // How to delete strike text:
    //   "backspace" (default) — char-by-char backspace
    //   "select" — highlight sweeps across, then single delete
    strikeDelete?: "backspace" | "select";
    // Emoji picker: show a floating dropdown panel with emoji options
    // before the text is typed. The text should be a single emoji character.
    //   true — auto-generate panel from catalog (recommended)
    //   EmojiOption[] — manual override with custom list
    emojiPicker?: true | { emoji: string; label: string }[];
    emojiPickerSelected?: number; // manual override: index of selected emoji
    emojiPickerFrames?: number;   // how long picker is visible (default: 25)
    // IME input: when true, each Chinese character in `text` is typed via
    // simulated pinyin input method. The engine looks up each char in pinyin-catalog,
    // types the romanized pinyin as strike-chars, shows a candidate panel,
    // then "selects" the correct character. Non-CJK chars are typed directly.
    imeInput?: boolean;
    imePauseFrames?: number;  // how long candidate panel is visible (default: 18)
    // Delay: wait this many frames before processing this segment.
    // Used for syncing typewriter to external audio (A-roll narration).
    // The delay is ABSOLUTE from the start of the typewriter, not relative.
    // If set, totalFrames jumps to this value (if it's ahead of current position).
    delayFrames?: number;
    // Inline image: renders an image inside the text flow.
    // The image scrolls with the text like a markdown inline image.
    // `src` is relative to public/ (e.g. "screenshots/tweet.png").
    // `heightLines` controls how many visual lines the image occupies (default: 5 ≈ 220px).
    // `alt` is a label typed above the image before it appears.
    image?: {
        src?: string;         // path for single image (relative to public/)
        heightLines?: number; // visual lines the image occupies (default: 5)
        alt?: string;         // label typed above the image before it appears
        // Multi-image row (flex row with card backgrounds):
        items?: { src: string; label?: string }[];  // array of images side-by-side
        gap?: number;         // gap between items in px (default: 12)
        width?: number;       // percentage of editor width (default: 80)
        height?: number;      // explicit height in px (overrides heightLines for rendering)
        animation?: "fade" | "slide-up" | "scale"; // entry animation (default: none)
    };
    // Image stack: renders multiple images piling up like newspaper clippings.
    // Images appear one at a time with pseudo-random rotation and offset.
    // The stack occupies a fixed-height region that scrolls with the text.
    imageStack?: {
        images: string[];       // src paths relative to public/
        heightLines?: number;   // total height of the stack region (default: 8)
        intervalFrames?: number; // frames between each image appearing (default: 8)
    };
    // Checkbox: the text should contain markdown checkbox syntax `- [ ] item`.
    // After the text is fully typed, the checkbox animates from unchecked → checked
    // with a satisfying spring-pop animation and green color transition.
    //   checkAfterFrames — delay before checking starts (default: 20)
    checkbox?: {
        checkAfterFrames?: number;   // frames after typing before check animation (default: 20)
    };
}

// ── Image marker character ──
const IMAGE_MARKER = '\uFFFC';
// Stack marker: a different invisible char to distinguish stacks from single images
const STACK_MARKER = '\uFFFD';

// ── Speed profiles ──
const MODE_PROFILES: Record<TypingMode, {
    baseFrames: number;
    jitter: number;
    pauseBefore: number;
}> = {
    burst: { baseFrames: 2, jitter: 1, pauseBefore: 0 },
    normal: { baseFrames: 3, jitter: 1, pauseBefore: 0 },
    deliberate: { baseFrames: 5, jitter: 2, pauseBefore: 3 },
    thinking: { baseFrames: 2, jitter: 1, pauseBefore: 14 },
};

const HARD_CHARS: Record<string, number> = {
    ".": 6, "!": 6, "?": 6, '"': 8, "'": 5, ",": 2, ":": 3, ";": 3,
    // Chinese full-width punctuation
    "。": 6, "！": 6, "？": 6, "，": 2, "：": 3, "；": 3, "、": 2,
    "“": 5, "”": 5, "‘": 5, "’": 5,
};
const NEWLINE_FRAMES = 4;
const PARAGRAPH_BREAK_FRAMES = 16;
const EMOJI_FRAMES = 5;
const CURSOR_BLINK_FRAMES = 20;
const GHOST_FADE_FRAMES = 8; // frames for ghost text to fade in
const DEFAULT_GHOST_PAUSE = 30; // frames ghost is visible before Tab

// ── Color palette — now driven by theme (see themes.ts) ──
// Legacy references removed; all colors come from theme.canvas.*

// ── Seeded pseudo-random ──
function seededRandom(seed: number): number {
    const x = Math.sin(seed * 9301 + 49297) * 49297;
    return x - Math.floor(x);
}

function jitter(seed: number, base: number, range: number): number {
    const offset = Math.round(seededRandom(seed) * range * 2 - range);
    return Math.max(1, base + offset);
}

function isEmoji(text: string, index: number): boolean {
    const code = text.codePointAt(index) || 0;
    return code > 0x1F000 || (code >= 0xD800 && code <= 0xDFFF);
}

// ── Chinese character detection ──
function isChinese(char: string): boolean {
    const code = char.codePointAt(0) || 0;
    // CJK Unified Ideographs: U+4E00–U+9FFF
    // CJK Extension A: U+3400–U+4DBF
    // CJK Compatibility Ideographs: U+F900–U+FAFF
    return (code >= 0x4E00 && code <= 0x9FFF) ||
        (code >= 0x3400 && code <= 0x4DBF) ||
        (code >= 0xF900 && code <= 0xFAFF);
}

// ── Pinyin catalog lookup ──
interface PinyinEntry {
    pinyin: string;
    candidates: string[];
}

function lookupPinyin(char: string): PinyinEntry | null {
    for (const entry of pinyinCatalog as PinyinEntry[]) {
        if (entry.candidates.includes(char)) {
            return entry;
        }
    }
    return null;
}

// ── Timeline event types ──
// Instead of a simple frame schedule, we build a timeline of events
interface TimelineEvent {
    frame: number;
    type: "char" | "delete" | "strike-char" | "select-grow" | "select-delete" | "ghost-show" | "ghost-accept" | "file-switch" | "cursor-jump" | "insert-char" | "checkbox-check";
    charIndex: number;
    localCharIndex?: number;
    ghostText?: string;
    ghostEndIndex?: number;
    ghostLocalEndIndex?: number;
    strikeChar?: string;
    imeChar?: string;
    fileName?: string;
    targetLine?: number;
    targetCol?: number;
    insertChar?: string;
    checkboxLine?: number;  // for checkbox-check: which line to check off
}

function buildTimeline(segments: TextSegment[]): TimelineEvent[] {
    const events: TimelineEvent[] = [];
    let totalFrames = 0;
    let globalCharIndex = 0;
    let fileLocalIndex = 0;  // per-file character counter
    let currentFile: string | undefined;
    const fileLocalIndices = new Map<string, number>(); // saved local indices per file

    for (const segment of segments) {
        const profile = MODE_PROFILES[segment.mode];

        // ── Delay: jump timeline to a specific frame (for A-roll sync) ──
        if (segment.delayFrames !== undefined && segment.delayFrames > totalFrames) {
            totalFrames = segment.delayFrames;
        }

        // ── File switch: if segment specifies a new file, emit file-switch ──
        if (segment.file && segment.file !== currentFile) {
            // Save current file's local index before switching
            if (currentFile) {
                fileLocalIndices.set(currentFile, fileLocalIndex);
            }
            // Small pause before file switch (if not the first segment)
            if (globalCharIndex > 0) {
                totalFrames += 10; // pause before switching
            }
            events.push({
                frame: totalFrames,
                type: "file-switch",
                charIndex: globalCharIndex,
                fileName: segment.file,
            });
            currentFile = segment.file;
            // Restore local index if returning to a previously opened file
            fileLocalIndex = fileLocalIndices.get(currentFile) || 0;
            totalFrames += 5; // small pause after file opens
        }

        // ── Image segment: type seg.text first, then emit instant image chars ──
        // flattenTextByFile() includes seg.text + alt + marker + newline,
        // so buildTimeline must process ALL of those to keep globalCharIndex in sync.
        if (segment.image) {
            // FIRST: type seg.text char-by-char (with proper frame costs)
            if (segment.text.length > 0) {
                for (let i = 0; i < segment.text.length; i++) {
                    const char = segment.text[i];
                    events.push({
                        frame: totalFrames,
                        type: "char",
                        charIndex: globalCharIndex,
                        localCharIndex: fileLocalIndex,
                    });

                    const prevChar = i > 0 ? segment.text[i - 1] : "";
                    let frames: number;
                    if (char === "\n" && prevChar === "\n") {
                        frames = jitter(globalCharIndex, PARAGRAPH_BREAK_FRAMES, 3);
                    } else if (char === "\n") {
                        frames = jitter(globalCharIndex, NEWLINE_FRAMES, 1);
                    } else if (HARD_CHARS[char]) {
                        frames = jitter(globalCharIndex, HARD_CHARS[char], 1);
                    } else if (isEmoji(segment.text, i)) {
                        frames = jitter(globalCharIndex, EMOJI_FRAMES, 1);
                    } else {
                        frames = jitter(globalCharIndex, profile.baseFrames, profile.jitter);
                    }
                    totalFrames += frames;
                    globalCharIndex++;
                    fileLocalIndex++;
                }
            }

            // THEN: emit instant char events for alt text + image marker + newline
            const altText = segment.image.alt ? segment.image.alt + '\n' : '';
            const imageChars = altText + IMAGE_MARKER + '\n';
            for (let i = 0; i < imageChars.length; i++) {
                events.push({
                    frame: totalFrames, // all at the same frame = instant
                    type: "char",
                    charIndex: globalCharIndex,
                    localCharIndex: fileLocalIndex,
                });
                globalCharIndex++;
                fileLocalIndex++;
            }
            // Advance by 1 frame so the image "appears" in a single beat
            totalFrames += 1;
            continue; // skip normal char processing below
        }

        // ── Image stack segment: emit instant char events for marker + newline ──
        if (segment.imageStack) {
            const stackChars = segment.text + STACK_MARKER + '\n';
            for (let i = 0; i < stackChars.length; i++) {
                events.push({
                    frame: totalFrames,
                    type: "char",
                    charIndex: globalCharIndex,
                    localCharIndex: fileLocalIndex,
                });
                globalCharIndex++;
                fileLocalIndex++;
            }
            totalFrames += 1;
            continue;
        }

        // ── Checkbox: track which line this segment targets ──
        // We'll emit a checkbox-check event AFTER the text is typed
        const isCheckbox = !!segment.checkbox;

        // Pause before segment
        if (profile.pauseBefore > 0 && globalCharIndex > 0) {
            totalFrames += jitter(globalCharIndex * 100, profile.pauseBefore, 4);
        }

        // ── Strike text phase (type → pause → delete) ──
        if (segment.strikeText) {
            const strikeProfile = MODE_PROFILES[segment.strikeMode ?? segment.mode];
            const strikePause = segment.strikePauseFrames ?? 20;

            // Type strike text char-by-char
            for (let i = 0; i < segment.strikeText.length; i++) {
                events.push({
                    frame: totalFrames,
                    type: "strike-char",
                    charIndex: globalCharIndex,
                    strikeChar: segment.strikeText[i],
                });
                const frames = jitter(
                    globalCharIndex + i * 1000,
                    strikeProfile.baseFrames,
                    strikeProfile.jitter,
                );
                totalFrames += frames;
            }

            // Pause — the "hmm, no" moment
            totalFrames += strikePause;

            const deleteMode = segment.strikeDelete ?? "backspace";

            if (deleteMode === "select") {
                // Selection sweep: highlight grows from right to left, ~1 frame per char
                for (let i = 0; i < segment.strikeText.length; i++) {
                    events.push({
                        frame: totalFrames,
                        type: "select-grow",
                        charIndex: globalCharIndex,
                    });
                    totalFrames += 1; // fast sweep
                }

                // Pause with full selection visible
                totalFrames += 8;

                // Single delete removes everything
                events.push({
                    frame: totalFrames,
                    type: "select-delete",
                    charIndex: globalCharIndex,
                });
                totalFrames += 3;
            } else {
                // Char-by-char backspace
                for (let i = segment.strikeText.length - 1; i >= 0; i--) {
                    events.push({
                        frame: totalFrames,
                        type: "delete",
                        charIndex: globalCharIndex,
                    });
                    totalFrames += jitter(globalCharIndex + i * 1000, 2, 1);
                }
            }

            // Small pause after deleting before typing replacement
            totalFrames += 4;
        }

        // ── Emoji picker phase: type `:label` as strike-chars, then delete ──
        if (segment.emojiPicker) {
            const targetEmoji = segment.text.trim();
            const catalogEntry = emojiCatalog.find(e => e.emoji === targetEmoji);
            const label = catalogEntry?.label || targetEmoji;
            const emojiText = ":" + label;

            // Type `:label` char-by-char, but stop early once filter narrows to 1 match
            for (let i = 0; i < emojiText.length; i++) {
                const ch = emojiText[i];
                events.push({
                    frame: totalFrames,
                    type: "strike-char",
                    charIndex: globalCharIndex,
                    strikeChar: ch,
                });
                const charFrames = i === 0 ? 2 : jitter(globalCharIndex + i, 2, 1);
                totalFrames += charFrames;

                // After typing this char, check if filter has narrowed to 1 match
                if (i > 0) { // skip the colon itself
                    const typedPrefix = label.slice(0, i).toLowerCase();
                    const matches = emojiCatalog.filter(e =>
                        e.label.toLowerCase().startsWith(typedPrefix)
                    );
                    if (matches.length === 1) break; // only one left — accept!
                }
            }

            // Pause to let viewer see the final filtered result
            totalFrames += segment.emojiPickerFrames ?? 20;

            // "Enter" — instantly accept the emoji (clears temp text)
            events.push({
                frame: totalFrames,
                type: "select-delete",
                charIndex: globalCharIndex,
            });
            totalFrames += 2;
        }

        // ── Insert-at mode: cursor jump + type at specific position ──
        if (segment.insertAt) {
            // Cursor jump to the target position
            events.push({
                frame: totalFrames,
                type: "cursor-jump",
                charIndex: globalCharIndex,
                localCharIndex: fileLocalIndex,
                targetLine: segment.insertAt.line,
                targetCol: segment.insertAt.col,
            });
            totalFrames += 8; // pause for cursor animation

            // Type characters as insert-char events (not appended at end)
            for (let i = 0; i < segment.text.length; i++) {
                events.push({
                    frame: totalFrames,
                    type: "insert-char",
                    charIndex: globalCharIndex,
                    localCharIndex: fileLocalIndex,
                    targetLine: segment.insertAt.line,
                    targetCol: segment.insertAt.col + i,
                    insertChar: segment.text[i],
                });

                const char = segment.text[i];
                let frames: number;
                if (char === "\n") {
                    frames = jitter(globalCharIndex, NEWLINE_FRAMES, 1);
                } else if (HARD_CHARS[char]) {
                    frames = jitter(globalCharIndex, profile.baseFrames + 2, profile.jitter);
                } else {
                    frames = jitter(globalCharIndex, profile.baseFrames, profile.jitter);
                }
                totalFrames += frames;
                globalCharIndex++;
                fileLocalIndex++;
            }
        } else {
            // ── Type the real text char-by-char (append at end) ──
            for (let i = 0; i < segment.text.length; i++) {
                const char = segment.text[i];

                // ── IME input: Chinese characters go through pinyin cycle ──
                if (segment.imeInput && isChinese(char)) {
                    const entry = lookupPinyin(char);
                    const pinyin = entry?.pinyin || "?";

                    // Thinking mode: pause before composing this character
                    if (segment.mode === "thinking" && i === 0) {
                        totalFrames += jitter(globalCharIndex, profile.pauseBefore, 4);
                    }

                    // Deliberate mode: extra pause between characters (not first)
                    if (segment.mode === "deliberate" && i > 0) {
                        totalFrames += jitter(globalCharIndex, profile.pauseBefore, 1);
                    }

                    // ── Predictive truncation ──
                    // Real typing rarely uses full pinyin. Only deliberate shows complete process.
                    let typedPinyinLen: number;
                    if (segment.mode === "deliberate") {
                        typedPinyinLen = pinyin.length; // full pinyin for emphasis
                    } else if (segment.mode === "burst") {
                        typedPinyinLen = 1; // aggressive: single letter then select
                    } else {
                        // normal/thinking: mostly 1 letter, occasionally 2
                        typedPinyinLen = seededRandom(globalCharIndex * 13) < 0.7 ? 1 : 2;
                    }
                    typedPinyinLen = Math.min(typedPinyinLen, pinyin.length);
                    const displayPinyin = pinyin.slice(0, typedPinyinLen);

                    // ── Type pinyin letters ──
                    const pinyinSpeed = segment.mode === "deliberate" ? 2 : 1;
                    for (let p = 0; p < displayPinyin.length; p++) {
                        events.push({
                            frame: totalFrames,
                            type: "strike-char",
                            charIndex: globalCharIndex,
                            strikeChar: displayPinyin[p],
                            imeChar: char,
                        });
                        totalFrames += jitter(globalCharIndex + p, pinyinSpeed, 0);
                    }

                    // ── Candidate panel pause — JITTERED for natural rhythm ──
                    const basePause = segment.imePauseFrames
                        ?? (segment.mode === "burst" ? 3
                            : segment.mode === "deliberate" ? 18
                                : 4); // normal/thinking: quick flash
                    const pauseJitter = segment.mode === "deliberate" ? 4 : 2;
                    totalFrames += jitter(globalCharIndex * 7, basePause, pauseJitter);

                    // Select-delete — clear pinyin
                    events.push({
                        frame: totalFrames,
                        type: "select-delete",
                        charIndex: globalCharIndex,
                    });
                    totalFrames += 1;

                    // Type the actual Chinese character
                    events.push({
                        frame: totalFrames,
                        type: "char",
                        charIndex: globalCharIndex,
                        localCharIndex: fileLocalIndex,
                    });

                    // ── Post-char breathing — JITTERED, not uniform ──
                    if (segment.mode === "burst") {
                        // 0 most of the time, occasionally 1f breath
                        totalFrames += seededRandom(globalCharIndex * 19) < 0.8 ? 0 : 1;
                    } else if (segment.mode === "deliberate") {
                        totalFrames += jitter(globalCharIndex, 3, 2);
                    } else {
                        // normal/thinking: 0-2f random breath between chars
                        totalFrames += Math.round(seededRandom(globalCharIndex * 23) * 2);
                    }

                    globalCharIndex++;
                    fileLocalIndex++;
                    continue;
                }

                // ── Normal character typing ──
                events.push({
                    frame: totalFrames,
                    type: "char",
                    charIndex: globalCharIndex,
                    localCharIndex: fileLocalIndex,
                });

                const prevChar = i > 0 ? segment.text[i - 1] : "";
                let frames: number;

                if (char === "\n" && prevChar === "\n") {
                    frames = jitter(globalCharIndex, PARAGRAPH_BREAK_FRAMES, 3);
                } else if (char === "\n") {
                    frames = jitter(globalCharIndex, NEWLINE_FRAMES, 1);
                } else if (HARD_CHARS[char]) {
                    frames = jitter(globalCharIndex, HARD_CHARS[char], 1);
                } else if (isEmoji(segment.text, i)) {
                    frames = jitter(globalCharIndex, EMOJI_FRAMES, 1);
                } else {
                    frames = jitter(globalCharIndex, profile.baseFrames, profile.jitter);
                }

                totalFrames += frames;
                globalCharIndex++;
                fileLocalIndex++;
            }

            // Ghost text phase
            if (segment.ghostText) {
                const ghostPause = segment.ghostPauseFrames ?? DEFAULT_GHOST_PAUSE;

                // Ghost text appears (fades in)
                events.push({
                    frame: totalFrames,
                    type: "ghost-show",
                    charIndex: globalCharIndex,
                    localCharIndex: fileLocalIndex,
                    ghostText: segment.ghostText,
                    ghostEndIndex: globalCharIndex + segment.ghostText.length,
                    ghostLocalEndIndex: fileLocalIndex + segment.ghostText.length,
                });

                totalFrames += ghostPause;

                // Tab press — ghost text becomes real
                events.push({
                    frame: totalFrames,
                    type: "ghost-accept",
                    charIndex: globalCharIndex,
                    localCharIndex: fileLocalIndex,
                    ghostEndIndex: globalCharIndex + segment.ghostText.length,
                    ghostLocalEndIndex: fileLocalIndex + segment.ghostText.length,
                });

                // Advance past the ghost text characters
                globalCharIndex += segment.ghostText.length;
                fileLocalIndex += segment.ghostText.length;
                totalFrames += 2; // tiny gap after Tab accept
            }
        } // end else (regular char typing)

        // ── Checkbox check event: emitted after text is fully typed ──
        if (isCheckbox) {
            const checkDelay = segment.checkbox!.checkAfterFrames ?? 20;
            totalFrames += checkDelay;

            // Calculate which line (in the *current file*) this checkbox sits on.
            // First, determine which file this segment belongs to (inherits from previous)
            let targetFile = "";
            for (const s of segments) {
                if (s.file) targetFile = s.file;
                if (s === segment) break;
            }
            // Accumulate all text typed in targetFile up to and including this segment
            let cbFileText = "";
            let trackFile = "";
            for (const s of segments) {
                if (s.file) trackFile = s.file;
                if (s.insertAt) continue;
                if (trackFile === targetFile) {
                    let t = s.text;
                    if (s.ghostText) t += s.ghostText;
                    if (s.image) {
                        const alt = s.image.alt ? s.image.alt + '\n' : '';
                        t = alt + IMAGE_MARKER + '\n';
                    }
                    if (s.imageStack) {
                        t = s.text + STACK_MARKER + '\n';
                    }
                    cbFileText += t;
                }
                if (s === segment) break;
            }
            // Find the line that contains "[ ]" (searching from the end)
            const cbLines = cbFileText.split('\n');
            let lineIndex = 0;
            for (let li = cbLines.length - 1; li >= 0; li--) {
                if (cbLines[li].includes('[ ]')) {
                    lineIndex = li;
                    break;
                }
            }

            events.push({
                frame: totalFrames,
                type: "checkbox-check",
                charIndex: globalCharIndex,
                checkboxLine: lineIndex,
            });
            totalFrames += 2; // small beat after check
        }


    }
    return events;
}

// ── Flatten all text per file ──
// Returns a map of fileName → flat text (including ghost text).
// Segments without a `file` field are grouped under "" (default file).
function flattenTextByFile(segments: TextSegment[]): Map<string, string> {
    const fileTexts = new Map<string, string>();
    let currentFile = "";
    for (const seg of segments) {
        if (seg.file) currentFile = seg.file;
        if (seg.insertAt) continue; // insertAt text is tracked via insertions, not typedLength
        const existing = fileTexts.get(currentFile) || "";
        // Image segments: append alt text + marker + newline
        if (seg.image) {
            const alt = seg.image.alt ? seg.image.alt + '\n' : '';
            fileTexts.set(currentFile, existing + seg.text + alt + IMAGE_MARKER + '\n');
        } else if (seg.imageStack) {
            // Stack: insert text + stack marker + newline
            fileTexts.set(currentFile, existing + seg.text + STACK_MARKER + '\n');
        } else {
            fileTexts.set(currentFile, existing + seg.text + (seg.ghostText || ""));
        }
    }
    return fileTexts;
}

// ── Build per-file language map ──
// Returns a map of fileName → SyntaxLanguage (last language set per file wins).
function getFileLanguages(segments: TextSegment[]): Map<string, SyntaxLanguage> {
    const map = new Map<string, SyntaxLanguage>();
    let currentFile = "";
    for (const seg of segments) {
        if (seg.file) currentFile = seg.file;
        if (seg.language) map.set(currentFile, seg.language);
    }
    return map;
}

// Legacy helper: flatten all text into a single string (for audio char lookup)
function flattenTextAll(segments: TextSegment[]): string {
    return segments.filter(s => !s.insertAt).map((s) => s.text + (s.ghostText || "")).join("");
}

// ── Build image metadata map ──
// Returns a map: for each segment with an image, the metadata needed for rendering.
interface ImageMeta {
    src?: string;
    heightLines: number;
    alt?: string;
    // Multi-image row:
    items?: { src: string; label?: string }[];
    gap: number;
    width: number;      // percentage of editor width
    height?: number;    // explicit height in px
    animation?: "fade" | "slide-up" | "scale";
    showFrame: number;  // frame when image appeared (for animation progress)
}
interface StackMeta {
    images: string[];
    heightLines: number;
    intervalFrames: number;
    startFrame: number; // absolute frame when the stack segment was emitted
}
function buildImageMap(segments: TextSegment[], timeline: TimelineEvent[]): Map<string, ImageMeta[]> {
    const result = new Map<string, ImageMeta[]>();
    let currentFile = "";
    let charOffset = 0;
    for (const seg of segments) {
        if (seg.file && seg.file !== currentFile) {
            currentFile = seg.file;
            charOffset = 0;
        }
        if (seg.insertAt) continue;
        if (seg.image) {
            const alt = seg.image.alt ? seg.image.alt + '\n' : '';
            charOffset += seg.text.length + alt.length;
            // Find the timeline event at this charIndex to get the show frame
            const ev = timeline.find(e => e.type === 'char' && e.charIndex === charOffset);
            const list = result.get(currentFile) || [];
            list.push({
                src: seg.image.src,
                heightLines: seg.image.heightLines ?? 5,
                alt: seg.image.alt,
                items: seg.image.items,
                gap: seg.image.gap ?? 12,
                width: seg.image.width ?? 80,
                height: seg.image.height,
                animation: seg.image.animation,
                showFrame: ev?.frame ?? 0,
            });
            result.set(currentFile, list);
            charOffset += 1 + 1;
        } else if (seg.imageStack) {
            charOffset += seg.text.length + 1 + 1; // text + marker + newline
        } else {
            charOffset += seg.text.length + (seg.ghostText?.length || 0);
        }
    }
    return result;
}

function buildStackMap(segments: TextSegment[], timeline: TimelineEvent[]): Map<string, StackMeta[]> {
    const result = new Map<string, StackMeta[]>();
    let currentFile = "";
    let charIdx = 0;
    for (const seg of segments) {
        if (seg.file) currentFile = seg.file;
        if (seg.insertAt) continue;
        if (seg.imageStack) {
            // Find the timeline event at this charIndex
            const ev = timeline.find(e => e.type === 'char' && e.charIndex === charIdx);
            const list = result.get(currentFile) || [];
            list.push({
                images: seg.imageStack.images,
                heightLines: seg.imageStack.heightLines ?? 8,
                intervalFrames: seg.imageStack.intervalFrames ?? 8,
                startFrame: ev?.frame ?? 0,
            });
            result.set(currentFile, list);
            charIdx += seg.text.length + 1 + 1; // text + marker + newline
        } else if (seg.image) {
            const alt = seg.image.alt ? seg.image.alt + '\n' : '';
            charIdx += seg.text.length + alt.length + 1 + 1;
        } else {
            charIdx += seg.text.length + (seg.ghostText?.length || 0);
        }
    }
    return result;
}

// ── Resolve display state from timeline at a given frame ──
interface DisplayState {
    typedLength: number;
    ghostText: string;
    ghostOpacity: number;
    isTyping: boolean;
    totalFrames: number;
    tempSuffix: string;    // temporary text from strike-char (gets deleted)
    selectionCount: number; // how many chars from end of tempSuffix are selected
    currentFile: string;   // current file name for the title bar
    fileTextMap: Map<string, string>; // accumulated text per file
    // In-place mutation state:
    insertions: { line: number; col: number; text: string }[]; // text inserted at specific positions
    cursorPosition: { line: number; col: number } | null; // explicit cursor position (null = end of text)
    // Syntax highlighting:
    currentLanguage: SyntaxLanguage | null;
    // IME state:
    imeTarget: string | null; // target Chinese character being composed via pinyin
    // Checkbox state:
    checkedLines: Set<number>;          // set of line indices that have been checked
    checkFrames: Map<number, number>;   // line index → frame when checked (for animation)
}

function getDisplayState(events: TimelineEvent[], frame: number): DisplayState {
    let typedLength = 0;
    let ghostText = "";
    let ghostOpacity = 0;
    let ghostShowFrame = -1;
    let tempSuffix = "";
    let selectionCount = 0;
    let currentFile = "";
    const fileTextMap = new Map<string, string>();
    let insertions: { line: number; col: number; text: string }[] = [];
    let cursorPosition: { line: number; col: number } | null = null;
    const fileInsertionsMap = new Map<string, { line: number; col: number; text: string }[]>();
    let currentLanguage: SyntaxLanguage | null = null;
    let imeTarget: string | null = null;
    const checkedLines = new Set<number>();
    const checkFrames = new Map<number, number>();

    for (const event of events) {
        if (event.frame > frame) break;

        if (event.type === "file-switch") {
            // Save current file's state before switching
            if (currentFile) {
                fileTextMap.set(currentFile, String(typedLength));
                fileInsertionsMap.set(currentFile, [...insertions]);
            }
            currentFile = event.fileName || "";
            // Restore state if returning to a previously opened file
            const savedLength = fileTextMap.get(currentFile);
            typedLength = savedLength ? parseInt(savedLength, 10) : 0;
            // Restore insertions for this file
            const savedInsertions = fileInsertionsMap.get(currentFile);
            insertions.length = 0;
            if (savedInsertions) insertions.push(...savedInsertions);
            cursorPosition = null; // cursor goes back to end of text
            tempSuffix = "";
            selectionCount = 0;
            ghostText = "";
            ghostOpacity = 0;
            ghostShowFrame = -1;
        } else if (event.type === "char") {
            // Use localCharIndex for per-file display
            typedLength = (event.localCharIndex ?? event.charIndex) + 1;
            ghostText = "";
            ghostOpacity = 0;
        } else if (event.type === "strike-char") {
            tempSuffix += event.strikeChar || "";
            selectionCount = 0; // reset selection when typing
            if (event.imeChar) imeTarget = event.imeChar; // track IME target
        } else if (event.type === "delete") {
            if (tempSuffix.length > 0) {
                tempSuffix = tempSuffix.slice(0, -1);
            }
        } else if (event.type === "select-grow") {
            selectionCount = Math.min(selectionCount + 1, tempSuffix.length);
        } else if (event.type === "select-delete") {
            tempSuffix = "";
            selectionCount = 0;
            imeTarget = null; // clear IME state
        } else if (event.type === "ghost-show") {
            ghostText = event.ghostText || "";
            ghostShowFrame = event.frame;
            const elapsed = frame - event.frame;
            ghostOpacity = Math.min(1, elapsed / GHOST_FADE_FRAMES);
        } else if (event.type === "ghost-accept") {
            // Use local end index for per-file display
            typedLength = event.ghostLocalEndIndex ?? event.ghostEndIndex ?? typedLength;
            ghostText = "";
            ghostOpacity = 0;
        } else if (event.type === "cursor-jump") {
            // Move cursor to a specific line/col without adding text
            cursorPosition = {
                line: event.targetLine ?? 0,
                col: event.targetCol ?? 0,
            };
        } else if (event.type === "insert-char") {
            // Insert a character at the cursor position
            const char = event.insertChar || "";
            const line = event.targetLine ?? 0;
            const col = event.targetCol ?? 0;
            // Find or create insertion entry for this line
            const existingIdx = insertions.findIndex(ins => ins.line === line && ins.col <= col && ins.col + ins.text.length >= col);
            if (existingIdx >= 0) {
                // Append to existing insertion
                insertions[existingIdx].text += char;
            } else {
                insertions.push({ line, col, text: char });
            }
            // Update cursor position
            if (char === "\n") {
                cursorPosition = { line: line + 1, col: 0 };
            } else {
                cursorPosition = { line, col: col + 1 };
            }
        } else if (event.type === "checkbox-check") {
            // Mark a line as checked
            if (event.checkboxLine !== undefined) {
                checkedLines.add(event.checkboxLine);
                checkFrames.set(event.checkboxLine, event.frame);
            }
        }
    }

    // Keep ghost visible with updated opacity
    if (ghostText && ghostShowFrame >= 0) {
        const elapsed = frame - ghostShowFrame;
        ghostOpacity = Math.min(1, elapsed / GHOST_FADE_FRAMES);
    }

    const totalFrames = events.length > 0
        ? events[events.length - 1].frame + 2
        : 0;
    const isTyping = frame < totalFrames;

    return { typedLength, ghostText, ghostOpacity, isTyping, totalFrames, tempSuffix, selectionCount, currentFile, fileTextMap, insertions, cursorPosition, currentLanguage, imeTarget, checkedLines, checkFrames };
}

// ── Cursor ──
const Cursor: React.FC<{ frame: number; isTyping: boolean; theme: Theme }> = ({
    frame,
    isTyping,
    theme,
}) => {
    const opacity = isTyping
        ? 1
        : interpolate(
            frame % CURSOR_BLINK_FRAMES,
            [0, CURSOR_BLINK_FRAMES * 0.4, CURSOR_BLINK_FRAMES * 0.5, CURSOR_BLINK_FRAMES * 0.9, CURSOR_BLINK_FRAMES],
            [1, 1, 0, 0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

    return (
        <span
            style={{
                display: "inline-block",
                width: theme.canvas.cursorWidth ?? 2,
                height: "1.2em",
                backgroundColor: theme.canvas.cursorColor,
                verticalAlign: "text-bottom",
                marginLeft: 1,
                opacity,
            }}
        />
    );
};

// ── Main component ──
export const TypewriterText: React.FC<{
    segments: TextSegment[];
    startFrame?: number;
    onFileChange?: (fileName: string) => void;
    theme?: Theme;
    /** Sound pack for keyboard audio (default: nk-cream) */
    soundPack?: SoundPack;
    /** Layout preset for dimension adaptation (default: LANDSCAPE) */
    layout?: LayoutPreset;
}> = ({ segments, startFrame = 0, onFileChange, theme = ivoryTheme, soundPack = "nk-cream", layout = LANDSCAPE }) => {
    const frame = useCurrentFrame();
    const fontFamily = getFontFamily(theme);

    const fileTexts = React.useMemo(() => flattenTextByFile(segments), [segments]);
    const allText = React.useMemo(() => flattenTextAll(segments), [segments]);
    const timeline = React.useMemo(() => buildTimeline(segments), [segments]);
    const fileLanguages = React.useMemo(() => getFileLanguages(segments), [segments]);
    const imageMap = React.useMemo(() => buildImageMap(segments, timeline), [segments, timeline]);
    const stackMap = React.useMemo(() => buildStackMap(segments, timeline), [segments, timeline]);

    const localFrame = frame - startFrame;
    const state = localFrame < 0
        ? { typedLength: 0, ghostText: "", ghostOpacity: 0, isTyping: false, totalFrames: 0, tempSuffix: "", selectionCount: 0, currentFile: "", fileTextMap: new Map<string, string>(), insertions: [] as { line: number; col: number; text: string }[], cursorPosition: null as { line: number; col: number } | null, currentLanguage: null as SyntaxLanguage | null, imeTarget: null as string | null, checkedLines: new Set<number>(), checkFrames: new Map<number, number>() }
        : getDisplayState(timeline, localFrame);

    // Derive current language from file language map
    const currentLanguage = fileLanguages.get(state.currentFile) || state.currentLanguage || null;

    // Notify parent of file changes
    React.useEffect(() => {
        if (onFileChange && state.currentFile) {
            onFileChange(state.currentFile);
        }
    }, [state.currentFile, onFileChange]);

    // Get the full text for the CURRENT file
    const fullText = fileTexts.get(state.currentFile) || fileTexts.get("") || "";

    // Split tempSuffix into non-selected + selected parts
    const suffixUnselected = state.tempSuffix.slice(0, state.tempSuffix.length - state.selectionCount);
    const suffixSelected = state.tempSuffix.slice(state.tempSuffix.length - state.selectionCount);

    const typedText = fullText.slice(0, state.typedLength) + state.tempSuffix;
    let lines = (typedText + (state.ghostText ? "\u200B" : "")).split("\n");
    // \u200B is zero-width space to ensure ghost text renders on the right line

    // ── Apply insertions overlay ──
    // Insertions are typed at specific line/col positions (from insert-at segments).
    // We merge them into the lines array for display.
    if (state.insertions.length > 0) {
        // Sort by line descending so we don't shift indices
        const sorted = [...state.insertions].sort((a, b) => b.line - a.line || b.col - a.col);
        for (const ins of sorted) {
            if (ins.line < lines.length) {
                const line = lines[ins.line];
                const col = Math.min(ins.col, line.length);
                lines[ins.line] = line.slice(0, col) + ins.text + line.slice(col);
            } else {
                // Insertion on a line beyond current text — pad with empty lines
                while (lines.length <= ins.line) lines.push("");
                lines[ins.line] = " ".repeat(ins.col) + ins.text;
            }
        }
        // Re-split in case insertions contained newlines
        lines = lines.flatMap(l => l.split("\n"));
    }

    // ── Determine active line (cursor position) ──
    // If cursorPosition is set (from cursor-jump/insert-at), use that line.
    // Otherwise, the cursor is at the end of typed text (last line).
    const activeLine = state.cursorPosition
        ? Math.min(state.cursorPosition.line, lines.length - 1)
        : lines.length - 1;

    // ── Terminal-style scroll ──
    // Text stays put. When the active (bottom) line would be below the
    // visible area, the entire content shifts up by exactly one line height.
    // No smooth animation — instant push-up, like a terminal or VS Code.
    const CHARS_PER_LINE = layout.charsPerLine;
    const LINE_HEIGHT_PX = layout.lineHeight;

    // ── Image line detection ──
    const currentImages = imageMap.get(state.currentFile) || [];
    let imageIdx = 0;
    const lineImageMap = new Map<number, ImageMeta>();
    // ── Stack line detection ──
    const currentStacks = stackMap.get(state.currentFile) || [];
    let stackIdx = 0;
    const lineStackMap = new Map<number, StackMeta>();
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes(IMAGE_MARKER) && imageIdx < currentImages.length) {
            lineImageMap.set(i, currentImages[imageIdx]);
            imageIdx++;
        }
        if (lines[i].includes(STACK_MARKER) && stackIdx < currentStacks.length) {
            lineStackMap.set(i, currentStacks[stackIdx]);
            stackIdx++;
        }
    }

    // How many visual lines before the active line?
    let visualLinesBefore = 0;
    for (let i = 0; i < activeLine; i++) {
        const imgMeta = lineImageMap.get(i);
        const stkMeta = lineStackMap.get(i);
        if (imgMeta) {
            visualLinesBefore += imgMeta.heightLines;
        } else if (stkMeta) {
            visualLinesBefore += stkMeta.heightLines;
        } else {
            const cleanLen = lines[i].replace("\u200B", "").length;
            visualLinesBefore += Math.max(1, Math.ceil(cleanLen / CHARS_PER_LINE));
        }
    }
    // Add the active line itself
    const activeImgMeta = lineImageMap.get(activeLine);
    const activeStkMeta = lineStackMap.get(activeLine);
    const activeLineLen = lines[activeLine]?.replace("\u200B", "").length || 0;
    const activeLineVisual = activeImgMeta
        ? activeImgMeta.heightLines
        : activeStkMeta
            ? activeStkMeta.heightLines
            : Math.max(1, Math.ceil(activeLineLen / CHARS_PER_LINE));
    const cursorVisualLine = visualLinesBefore + activeLineVisual;

    // The editor body fits ~14 visual lines (660px - 44px title - 30px pad = 586px / 44px ≈ 13.3)
    // Use 13 so there's always ~1 line of padding below the cursor
    const MAX_VISIBLE_LINES = layout.maxVisibleLines;
    // Only scroll if cursor would be off-screen
    const scrollLines = Math.max(0, cursorVisualLine - MAX_VISIBLE_LINES);
    const scrollOffset = scrollLines * LINE_HEIGHT_PX;

    // ── Cursor XY for emoji picker positioning ──
    // These coordinates are relative to the EditorWindow body (position: relative)
    const EDITOR_PAD_TOP = layout.padTop;
    const EDITOR_PAD_LEFT = layout.padLeft;
    const CHAR_WIDTH_PX = layout.charWidth;
    // Get cursor column: from cursorPosition if set, else end of active line
    const activeLineText = lines[activeLine]?.replace("\u200B", "") || "";
    const cursorCol = state.cursorPosition
        ? Math.min(state.cursorPosition.col, activeLineText.length)
        : activeLineText.length;
    // Simulate CSS word-wrap to find chars on the last visual line
    let wrapPos = 0;
    while (wrapPos + CHARS_PER_LINE < activeLineText.length) {
        const breakAt = activeLineText.lastIndexOf(" ", wrapPos + CHARS_PER_LINE);
        if (breakAt <= wrapPos) {
            wrapPos += CHARS_PER_LINE; // no space found, force break
        } else {
            wrapPos = breakAt + 1; // skip the space
        }
    }
    const charsOnLastWrap = Math.max(0, cursorCol - wrapPos);
    const cursorX = EDITOR_PAD_LEFT + charsOnLastWrap * CHAR_WIDTH_PX;
    const cursorY = EDITOR_PAD_TOP + (cursorVisualLine - 1) * LINE_HEIGHT_PX - scrollOffset;

    return (
        <>
            <div
                style={{
                    fontFamily,
                    fontSize: theme.font.size,
                    fontWeight: 400,
                    lineHeight: 1.7,
                    color: theme.canvas.textColor,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    position: "relative",
                    transform: `translateY(-${scrollOffset}px)`,
                    // No transition — instant push-up like a terminal
                    ...(theme.effects?.textShadow && { textShadow: theme.effects.textShadow }),
                }}
            >
                {lines.map((line, lineIndex) => {
                    const isActiveLine = lineIndex === activeLine;
                    const hasGhostMarker = line.includes("\u200B");
                    const cleanLine = line.replace("\u200B", "");

                    // ── Syntax highlighted text rendering ──
                    const renderText = (text: string): React.ReactNode => {
                        if (!currentLanguage || text.length === 0) return text;
                        const spans = tokenizeLine(text, currentLanguage, theme.syntax);
                        return spans.map((span, i) => (
                            <span key={i} style={{ color: span.color }}>{span.text}</span>
                        ));
                    };

                    // ── Checkbox rendering helper ──
                    const isCheckedLine = state.checkedLines.has(lineIndex);
                    const checkFrame = state.checkFrames.get(lineIndex);
                    const renderCheckboxLine = (text: string): React.ReactNode => {
                        if (!isCheckedLine) return renderText(text);
                        // Replace "[ ]" with animated "[✓]"
                        const checkboxMatch = text.match(/^(\s*-\s*)\[ \](.*)$/);
                        if (!checkboxMatch) return renderText(text);
                        const [, prefix, suffix] = checkboxMatch;
                        // Spring-pop animation timing
                        const elapsed = checkFrame !== undefined ? localFrame - checkFrame : 10;
                        const checkScale = interpolate(
                            elapsed,
                            [0, 4, 8],
                            [0, 1.3, 1.0],
                            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
                        );
                        const checkOpacity = interpolate(
                            elapsed,
                            [0, 3],
                            [0, 1],
                            { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
                        );
                        return (
                            <>
                                {renderText(prefix)}
                                <span style={{ color: theme.canvas.textColor }}>{'['}</span>
                                <span style={{
                                    color: "#22C55E",
                                    display: "inline-block",
                                    transform: `scale(${checkScale})`,
                                    opacity: checkOpacity,
                                    fontWeight: 700,
                                }}>{'✓'}</span>
                                <span style={{ color: theme.canvas.textColor }}>{']'}</span>
                                <span style={{ opacity: 0.65 }}>{renderText(suffix)}</span>
                            </>
                        );
                    };

                    // ── Image stack line ──
                    const stkMeta = lineStackMap.get(lineIndex);
                    if (stkMeta) {
                        const stackHeight = stkMeta.heightLines * LINE_HEIGHT_PX;
                        const imgH = stackHeight - 32; // padding
                        const imgW = imgH * 1.6; // assume ~16:10 aspect for headlines
                        return (
                            <div
                                key={lineIndex}
                                style={{
                                    position: "relative",
                                    height: stackHeight,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    overflow: "hidden",
                                }}
                            >
                                {stkMeta.images.map((src, idx) => {
                                    // Progressive reveal: each image appears after intervalFrames
                                    const showAtFrame = stkMeta.startFrame + idx * stkMeta.intervalFrames;
                                    if (localFrame < showAtFrame) return null;
                                    // Pseudo-random rotation and offset per image
                                    const seed = seededRandom(idx * 137 + 42);
                                    const rotation = (seed - 0.5) * 10; // ±5°
                                    const offsetX = (seededRandom(idx * 271 + 13) - 0.5) * 30; // ±15px
                                    const offsetY = (seededRandom(idx * 397 + 7) - 0.5) * 20; // ±10px
                                    return (
                                        <Img
                                            key={idx}
                                            src={staticFile(src)}
                                            style={{
                                                position: "absolute",
                                                maxWidth: Math.min(imgW, 580),
                                                maxHeight: imgH,
                                                objectFit: "contain",
                                                borderRadius: 6,
                                                boxShadow: theme.canvas.imageShadow,
                                                transform: `rotate(${rotation}deg) translate(${offsetX}px, ${offsetY}px)`,
                                                zIndex: idx,
                                            }}
                                        />
                                    );
                                })}
                            </div>
                        );
                    }

                    // ── Inline image line ──
                    const imgMeta = lineImageMap.get(lineIndex);
                    if (imgMeta) {
                        const elapsed = localFrame - imgMeta.showFrame;
                        const animDuration = 12; // frames for animation
                        const progress = Math.min(1, Math.max(0, elapsed / animDuration));
                        const widthPct = `${imgMeta.width}%`;

                        let animStyle: React.CSSProperties = {};
                        if (imgMeta.animation === "fade") {
                            animStyle = { opacity: interpolate(progress, [0, 1], [0, 1]) };
                        } else if (imgMeta.animation === "slide-up") {
                            animStyle = {
                                opacity: interpolate(progress, [0, 0.3, 1], [0, 1, 1]),
                                transform: `translateY(${interpolate(progress, [0, 1], [30, 0])}px)`,
                            };
                        } else if (imgMeta.animation === "scale") {
                            animStyle = {
                                opacity: interpolate(progress, [0, 0.3, 1], [0, 1, 1]),
                                transform: `scale(${interpolate(progress, [0, 1], [0.7, 1])})`,
                            };
                        }

                        // Multi-image row (items array)
                        if (imgMeta.items && imgMeta.items.length > 0) {
                            const itemH = imgMeta.height ?? 120;
                            return (
                                <div
                                    key={lineIndex}
                                    style={{
                                        display: "flex",
                                        justifyContent: "flex-start",
                                        gap: imgMeta.gap,
                                        padding: "8px 0",
                                        width: widthPct,
                                        ...animStyle,
                                    }}
                                >
                                    {imgMeta.items.map((item, itemIdx) => (
                                        <div
                                            key={`item-${itemIdx}`}
                                            style={{
                                                flex: 1,
                                                display: "flex",
                                                flexDirection: "column",
                                                alignItems: "center",
                                                justifyContent: "center",
                                                backgroundColor: theme.canvas.imageCardBg,
                                                borderRadius: 8,
                                                padding: 12,
                                            }}
                                        >
                                            <Img
                                                src={staticFile(item.src)}
                                                style={{
                                                    height: itemH - 24, // account for padding
                                                    objectFit: "contain",
                                                }}
                                            />
                                            {item.label && (
                                                <span style={{
                                                    fontSize: 14,
                                                    color: theme.canvas.imageLabelColor,
                                                    marginTop: 6,
                                                    fontFamily: "sans-serif",
                                                }}>
                                                    {item.label}
                                                </span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            );
                        }

                        // Single image
                        const imgH = imgMeta.height ?? (imgMeta.heightLines * LINE_HEIGHT_PX);
                        return (
                            <div
                                key={lineIndex}
                                style={{
                                    position: "relative",
                                    height: imgMeta.heightLines * LINE_HEIGHT_PX,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    padding: "8px 0",
                                    ...animStyle,
                                }}
                            >
                                <Img
                                    src={staticFile(imgMeta.src!)}
                                    style={{
                                        maxWidth: widthPct,
                                        maxHeight: imgH - 16,
                                        objectFit: "contain",
                                        borderRadius: 8,
                                        boxShadow: theme.canvas.imageShadow,
                                    }}
                                />
                            </div>
                        );
                    }

                    return (
                        <div
                            key={lineIndex}
                            style={{
                                position: "relative",
                                minHeight: "1.7em",
                            }}
                        >
                            {isActiveLine && (
                                <div
                                    style={{
                                        position: "absolute",
                                        left: -40,
                                        right: -40,
                                        bottom: 0,
                                        height: "1.7em",
                                        backgroundColor: theme.canvas.activeLineBg,
                                        zIndex: 0,
                                    }}
                                />
                            )}
                            <span style={{ position: "relative", zIndex: 1 }}>
                                {isActiveLine && state.selectionCount > 0 ? (
                                    <>
                                        {/* Main text (not from tempSuffix) */}
                                        {renderText(cleanLine.slice(0, cleanLine.length - state.tempSuffix.length))}
                                        {/* Unselected part of tempSuffix */}
                                        {suffixUnselected}
                                        {/* Selected part with blue highlight */}
                                        <span style={{
                                            backgroundColor: theme.canvas.selectionColor,
                                            borderRadius: 2,
                                        }}>
                                            {suffixSelected}
                                        </span>
                                    </>
                                ) : state.cursorPosition && isActiveLine ? (
                                    // Insert-at mode: cursor in the middle of existing text
                                    <>
                                        {renderText(cleanLine.slice(0, cursorCol))}
                                        <Cursor frame={frame} isTyping={state.isTyping} theme={theme} />
                                        {renderText(cleanLine.slice(cursorCol))}
                                    </>
                                ) : (
                                    renderCheckboxLine(cleanLine)
                                )}
                                {isActiveLine && !state.cursorPosition && (
                                    <Cursor frame={frame} isTyping={state.isTyping} theme={theme} />
                                )}
                                {isActiveLine && hasGhostMarker && state.ghostText && (
                                    <span
                                        style={{
                                            color: theme.canvas.ghostTextColor,
                                            opacity: state.ghostOpacity * 0.5,
                                        }}
                                    >
                                        {state.ghostText}
                                    </span>
                                )}
                            </span>
                        </div>
                    );
                })}
            </div >

            {/* ── Emoji picker — derived from tempSuffix starting with : ── */}
            {(() => {
                if (!state.tempSuffix.startsWith(":") || state.selectionCount > 0) return null;
                const prefix = state.tempSuffix.slice(1).toLowerCase();
                const PANEL_MAX = 8;

                // Filter catalog by typed prefix
                const filtered = prefix.length === 0
                    ? emojiCatalog.slice(0, PANEL_MAX)
                    : emojiCatalog.filter(e => e.label.toLowerCase().startsWith(prefix));
                if (filtered.length === 0) return null;

                const visible = filtered.slice(0, PANEL_MAX);
                // Highlight the exact match, or the first result
                const exactIdx = visible.findIndex(e => e.label.toLowerCase() === prefix);
                const selectedIdx = exactIdx >= 0 ? exactIdx : 0;

                return (
                    <div
                        style={{
                            position: "absolute",
                            top: cursorY - (visible.length * 38 + 12),
                            left: cursorX,
                            zIndex: 10,
                            backgroundColor: theme.popup.bg,
                            border: theme.popup.border,
                            borderRadius: theme.popup.borderRadius,
                            boxShadow: theme.popup.shadow,
                            padding: "6px 0",
                            minWidth: 200,
                            fontFamily,
                        }}
                    >
                        {visible.map((option, idx) => {
                            const isSelected = idx === selectedIdx;
                            return (
                                <div
                                    key={idx}
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: 10,
                                        padding: "7px 16px",
                                        backgroundColor: isSelected
                                            ? theme.popup.selectedBg
                                            : "transparent",
                                        borderLeft: isSelected
                                            ? `3px solid ${theme.popup.selectedBorder}`
                                            : "3px solid transparent",
                                        fontSize: 18,
                                        color: theme.popup.textColor,
                                    }}
                                >
                                    <span style={{ fontSize: 24, lineHeight: 1 }}>{option.emoji}</span>
                                    <span style={{
                                        fontWeight: isSelected ? 600 : 400,
                                        fontSize: 16,
                                    }}>{option.label}</span>
                                </div>
                            );
                        })}
                    </div>
                );
            })()}

            {/* ── IME candidate panel — horizontal bar below cursor ── */}
            {(() => {
                // Show when we have a non-colon tempSuffix with an imeTarget
                if (!state.imeTarget || state.tempSuffix.startsWith(":") || state.selectionCount > 0 || state.tempSuffix.length === 0) return null;

                const entry = lookupPinyin(state.imeTarget);
                if (!entry) return null;

                const candidates = entry.candidates;
                const selectedIdx = candidates.indexOf(state.imeTarget);
                const highlightIdx = selectedIdx >= 0 ? selectedIdx : 0;

                return (
                    <div
                        style={{
                            position: "absolute",
                            top: cursorY + 44, // below cursor line
                            left: Math.max(cursorX - 20, 40),
                            zIndex: 10,
                            backgroundColor: theme.popup.imeBg,
                            border: theme.popup.imeBorder,
                            borderRadius: 6,
                            boxShadow: theme.popup.imeShadow,
                            padding: "4px 8px",
                            display: "flex",
                            gap: 4,
                            fontFamily: "'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
                        }}
                    >
                        {/* Pinyin label */}
                        <span style={{
                            fontSize: 14,
                            color: theme.popup.imeLabelColor,
                            marginRight: 6,
                            alignSelf: "center",
                            letterSpacing: 0.5,
                        }}>
                            {state.tempSuffix}
                        </span>
                        {candidates.map((char, idx) => {
                            const isSelected = idx === highlightIdx;
                            return (
                                <span
                                    key={idx}
                                    style={{
                                        display: "inline-flex",
                                        alignItems: "center",
                                        gap: 2,
                                        padding: "3px 8px",
                                        borderRadius: 4,
                                        backgroundColor: isSelected ? theme.popup.imeSelectedBg : "transparent",
                                        color: isSelected ? theme.popup.imeSelectedTextColor : theme.popup.textColor,
                                        fontSize: 20,
                                        fontWeight: isSelected ? 600 : 400,
                                        lineHeight: 1.2,
                                    }}
                                >
                                    <span style={{ fontSize: 12, color: isSelected ? "rgba(255,255,255,0.8)" : theme.popup.secondaryColor, marginRight: 2 }}>
                                        {idx + 1}.
                                    </span>
                                    {char}
                                </span>
                            );
                        })}
                    </div>
                );
            })()}

            {/* ── Audio: each character = one sound, perfectly synced ── */}
            {
                timeline.map((event, eventIndex) => {
                    // File-switch = "opening a new tab" → subtle click sound
                    if (event.type === "file-switch") {
                        return (
                            <Sequence key={`audio-fileswitch-${eventIndex}`} from={startFrame + event.frame} durationInFrames={10}>
                                <Audio src={staticFile(resolveSound("space", soundPack))} volume={0.3} />
                            </Sequence>
                        );
                    }

                    // Ghost-show = silent (visual only)
                    if (event.type === "ghost-show") return null;

                    // Ghost-accept = Tab to accept autocomplete → single space/tab click
                    if (event.type === "ghost-accept") {
                        return (
                            <Sequence key={`audio-accept-${eventIndex}`} from={startFrame + event.frame} durationInFrames={10}>
                                <Audio src={staticFile(resolveSound("space", soundPack))} volume={0.4} />
                            </Sequence>
                        );
                    }

                    // Delete = backspace key sound
                    if (event.type === "delete") {
                        return (
                            <Sequence key={`audio-del-${eventIndex}`} from={startFrame + event.frame} durationInFrames={10}>
                                <Audio src={staticFile(resolveSound("backspace", soundPack))} volume={0.45} />
                            </Sequence>
                        );
                    }

                    // Select-delete = single backspace after selection highlight
                    if (event.type === "select-delete") {
                        return (
                            <Sequence key={`audio-seldel-${eventIndex}`} from={startFrame + event.frame} durationInFrames={10}>
                                <Audio src={staticFile(resolveSound("backspace", soundPack))} volume={0.5} />
                            </Sequence>
                        );
                    }

                    // Select-grow = silent (visual only)
                    if (event.type === "select-grow") return null;

                    // Strike-char = temporary text being typed (use same key sounds as normal chars)
                    if (event.type === "strike-char") {
                        const sChar = (event.strikeChar || "").toLowerCase();
                        const soundType = sChar === " " ? "space" as const : "key" as const;
                        const soundFile = resolveSound(soundType, soundPack, sChar, eventIndex);
                        const vol = 0.5 + (seededRandom(eventIndex * 7) - 0.5) * 0.1;
                        return (
                            <Sequence key={`audio-strike-${eventIndex}`} from={startFrame + event.frame} durationInFrames={10}>
                                <Audio src={staticFile(soundFile)} volume={Math.max(0.2, Math.min(0.7, vol))} />
                            </Sequence>
                        );
                    }
                    // Cursor-jump = silent (visual only — cursor moves)
                    if (event.type === "cursor-jump") return null;

                    // insert-char and char both produce key sounds
                    if (event.type !== "char" && event.type !== "insert-char") return null;

                    // For insert-char, use the insertChar; for regular char, use allText lookup
                    const char = event.type === "insert-char"
                        ? (event.insertChar || " ")
                        : (allText[event.charIndex] || " ");

                    // Enter key
                    if (char === "\n") {
                        const prevChar = event.charIndex > 0 ? fullText[event.charIndex - 1] : "";
                        if (prevChar === "\n" || prevChar === "") return null;
                        return (
                            <Sequence key={`audio-${eventIndex}`} from={startFrame + event.frame} durationInFrames={10}>
                                <Audio src={staticFile(resolveSound("enter", soundPack))} volume={0.55} />
                            </Sequence>
                        );
                    }

                    // Space key
                    if (char === " ") {
                        return (
                            <Sequence key={`audio-${eventIndex}`} from={startFrame + event.frame} durationInFrames={10}>
                                <Audio src={staticFile(resolveSound("space", soundPack))} volume={0.5} />
                            </Sequence>
                        );
                    }

                    // Letter keys (a-z) → per-letter sound
                    const soundFile = resolveSound("key", soundPack, char, event.charIndex);

                    const baseVol = 0.55;
                    const jitterAmt = (seededRandom(event.charIndex * 7) - 0.5) * 0.1;
                    const volume = Math.max(0.2, Math.min(0.7, baseVol + jitterAmt));

                    return (
                        <Sequence
                            key={`audio-${eventIndex}`}
                            from={startFrame + event.frame}
                            durationInFrames={10}
                        >
                            <Audio src={staticFile(soundFile)} volume={volume} />
                        </Sequence>
                    );
                })
            }
        </>
    );
};

