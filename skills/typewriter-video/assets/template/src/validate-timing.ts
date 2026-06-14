/**
 * Timing Validation Script for A-Roll Sync
 *
 * Run this BEFORE asking the user to visually review.
 * It analyzes TextSegment[] and reports per-segment timing,
 * warnings for overruns, stalls, and common mistakes.
 *
 * Usage (from composition file):
 *   import { validateTiming } from "./validate-timing";
 *   validateTiming(MY_SEGMENTS, { chapterDurationSeconds: 46.0 });
 *
 * Usage (standalone — print to console):
 *   npx tsx src/validate-timing.ts
 *   (edit the bottom of this file to import your segments)
 */

// ── Engine constants (mirrored from TypewriterText.tsx) ──
// These MUST stay in sync with the engine. If you change costs there, update here.

const FPS = 30000 / 1001; // NTSC 29.97fps

const MODE_SPEEDS: Record<string, { base: number; jitter: number; pauseBefore: number }> = {
    burst: { base: 2, jitter: 1, pauseBefore: 0 },
    normal: { base: 3, jitter: 1, pauseBefore: 0 },
    deliberate: { base: 5, jitter: 2, pauseBefore: 3 },
    thinking: { base: 2, jitter: 1, pauseBefore: 14 },
};

const HARD_CHARS: Record<string, number> = {
    ".": 6, "!": 6, "?": 6, '"': 8, "'": 5, ",": 2, ":": 3, ";": 3,
    "。": 6, "！": 6, "？": 6, "，": 2, "：": 3, "；": 3, "、": 2,
    "\u201C": 5, "\u201D": 5, "\u2018": 5, "\u2019": 5,
};

const NEWLINE_FRAMES = 4;
const PARAGRAPH_BREAK_FRAMES = 16;
const EMOJI_FRAMES = 5;
const IMAGE_SEGMENT_FRAMES = 1;

// ── Segment type (simplified — only fields relevant to timing) ──
interface TimingSegment {
    text: string;
    mode: string;
    delayFrames?: number;
    ghostText?: string;
    ghostPauseFrames?: number;
    strikeText?: string;
    strikeMode?: string;
    strikePauseFrames?: number;
    strikeDelete?: "backspace" | "select";
    emojiPicker?: boolean | unknown[];
    emojiPickerFrames?: number;
    imeInput?: boolean;
    imePauseFrames?: number;
    image?: { src?: string; alt?: string; items?: unknown[]; [key: string]: unknown };
    imageStack?: { images: string[]; intervalFrames?: number; [key: string]: unknown };
    checkbox?: { checkAfterFrames?: number };
    file?: string;
    insertAt?: { line: number; col: number };
}

// ── Estimate segment cost in frames ──
function estimateSegmentCost(seg: TimingSegment): number {
    const profile = MODE_SPEEDS[seg.mode] || MODE_SPEEDS.burst;
    let cost = 0;

    // pauseBefore (only if not first segment — we can't know here, so include it)
    if (profile.pauseBefore > 0) {
        cost += profile.pauseBefore;
    }

    // Strike text phase
    if (seg.strikeText) {
        const strikeProfile = MODE_SPEEDS[seg.strikeMode ?? seg.mode] || profile;
        // Type strike chars
        cost += seg.strikeText.length * strikeProfile.base;
        // Pause
        cost += seg.strikePauseFrames ?? 20;
        // Delete
        if (seg.strikeDelete === "select") {
            cost += seg.strikeText.length + 8 + 3; // sweep + pause + delete
        } else {
            cost += seg.strikeText.length * 2; // backspace
        }
        cost += 4; // pause after delete
    }

    // Emoji picker phase
    if (seg.emojiPicker) {
        // Rough estimate: ~4 chars of label typing + picker pause
        cost += 4 * 2; // label chars at burst speed
        cost += seg.emojiPickerFrames ?? 20;
        cost += 2; // select-delete
    }

    // Text typing
    if (seg.image) {
        // Image segments: text types normally, then image appears in 1 frame
        cost += estimateTextCost(seg.text, profile);
        cost += IMAGE_SEGMENT_FRAMES;
    } else if (seg.imageStack) {
        cost += IMAGE_SEGMENT_FRAMES;
    } else if (seg.insertAt) {
        cost += 8; // cursor jump pause
        cost += estimateTextCost(seg.text, profile);
    } else {
        // Normal text
        if (seg.imeInput) {
            cost += estimateIMECost(seg.text, seg.mode, seg.imePauseFrames);
        } else {
            cost += estimateTextCost(seg.text, profile);
        }
    }

    // Ghost text
    if (seg.ghostText) {
        cost += seg.ghostPauseFrames ?? 30;
        cost += 2; // Tab accept
    }

    // Checkbox
    if (seg.checkbox) {
        cost += seg.checkbox.checkAfterFrames ?? 20;
        cost += 2; // check beat
    }

    return cost;
}

function estimateTextCost(
    text: string,
    profile: { base: number; jitter: number },
): number {
    let cost = 0;
    for (let i = 0; i < text.length; i++) {
        const char = text[i];
        const prevChar = i > 0 ? text[i - 1] : "";

        if (char === "\n" && prevChar === "\n") {
            cost += PARAGRAPH_BREAK_FRAMES;
        } else if (char === "\n") {
            cost += NEWLINE_FRAMES;
        } else if (HARD_CHARS[char]) {
            cost += HARD_CHARS[char];
        } else if (char.codePointAt(0)! > 0x1F000) {
            cost += EMOJI_FRAMES;
        } else {
            cost += profile.base;
        }
    }
    return cost;
}

function estimateIMECost(text: string, mode: string, imePauseOverride?: number): number {
    let cost = 0;
    const basePause = imePauseOverride ??
        (mode === "burst" ? 3 : mode === "deliberate" ? 18 : 4);

    for (let i = 0; i < text.length; i++) {
        const code = text.codePointAt(i) || 0;
        const isCJK = (code >= 0x4E00 && code <= 0x9FFF) ||
            (code >= 0x3400 && code <= 0x4DBF);

        if (isCJK) {
            // Pinyin typing + candidate pause + select + post-char breath
            const pinyinChars = mode === "deliberate" ? 4 : 1; // approximate
            cost += pinyinChars * (mode === "deliberate" ? 2 : 1);
            cost += basePause;
            cost += 1; // select-delete
            cost += 1; // char event + breath
        } else {
            // Non-CJK: normal typing
            const profile = MODE_SPEEDS[mode] || MODE_SPEEDS.burst;
            if (text[i] === "\n") {
                cost += NEWLINE_FRAMES;
            } else if (HARD_CHARS[text[i]]) {
                cost += HARD_CHARS[text[i]];
            } else {
                cost += profile.base;
            }
        }
    }
    return cost;
}

// ── Validation result ──
interface SegmentReport {
    index: number;
    delayLabel: string;       // "0.5s" or "FLOW"
    costFrames: number;
    costSeconds: number;
    endSeconds: number;
    idleFrames: number;
    idleSeconds: number;
    tags: string[];           // ["IMAGE", "IME", "STRIKE", etc.]
    warnings: string[];
}

interface ValidationResult {
    segments: SegmentReport[];
    warnings: string[];
    totalFrames: number;
    totalSeconds: number;
}

export interface ValidateOptions {
    chapterDurationSeconds?: number;  // if set, checks total fits
    verbose?: boolean;                // print to console
}

export function validateTiming(
    segments: TimingSegment[],
    options: ValidateOptions = {},
): ValidationResult {
    const reports: SegmentReport[] = [];
    const globalWarnings: string[] = [];
    let runningFrame = 0;

    for (let i = 0; i < segments.length; i++) {
        const seg = segments[i];
        const cost = estimateSegmentCost(seg);

        // Determine start frame
        let startFrame = runningFrame;
        if (seg.delayFrames !== undefined && seg.delayFrames > runningFrame) {
            startFrame = seg.delayFrames;
        }

        const endFrame = startFrame + cost;
        const idleFrames = startFrame - runningFrame;

        // Tags
        const tags: string[] = [];
        if (seg.image) tags.push("IMAGE");
        if (seg.imageStack) tags.push("STACK");
        if (seg.imeInput) tags.push("IME");
        if (seg.strikeText) tags.push("STRIKE");
        if (seg.ghostText) tags.push("GHOST");
        if (seg.emojiPicker) tags.push("EMOJI");
        if (seg.checkbox) tags.push("CHECK");
        if (seg.insertAt) tags.push("INSERT");
        if (seg.file) tags.push(`FILE:${seg.file}`);

        // Warnings
        const warnings: string[] = [];

        // Check: image segment with non-empty text (the old bug pattern)
        // No longer a bug after the engine fix, but worth noting
        if (seg.image && seg.text && seg.text.length > 0) {
            tags.push("TEXT+IMG");
        }

        // Check: overrun — segment cost exceeds gap to next anchor
        const nextAnchor = segments.slice(i + 1).find(s => s.delayFrames !== undefined);
        if (nextAnchor?.delayFrames !== undefined) {
            const gap = nextAnchor.delayFrames - startFrame;
            if (cost > gap) {
                warnings.push(`OVERRUN: cost ${cost}f > gap ${gap}f to next anchor`);
            }
        }

        // Check: long idle wait
        if (idleFrames > 90) {
            warnings.push(`LONG WAIT: ${idleFrames}f (${(idleFrames / FPS).toFixed(1)}s) idle before this segment`);
        }

        // Check: consecutive anchors too close
        if (i > 0 && seg.delayFrames !== undefined) {
            const prev = segments[i - 1];
            if (prev.delayFrames !== undefined) {
                const anchorGap = seg.delayFrames - prev.delayFrames;
                if (anchorGap < Math.round(FPS * 1.0)) {
                    warnings.push(`CLOSE ANCHORS: ${(anchorGap / FPS).toFixed(1)}s gap to previous anchor (< 1s)`);
                }
            }
        }

        reports.push({
            index: i,
            delayLabel: seg.delayFrames !== undefined ? `${(seg.delayFrames / FPS).toFixed(1)}s` : "FLOW",
            costFrames: cost,
            costSeconds: parseFloat((cost / FPS).toFixed(1)),
            endSeconds: parseFloat((endFrame / FPS).toFixed(1)),
            idleFrames,
            idleSeconds: parseFloat((idleFrames / FPS).toFixed(1)),
            tags,
            warnings,
        });

        if (warnings.length > 0) {
            globalWarnings.push(...warnings.map(w => `  ⚠️ Segment #${i}: ${w}`));
        }

        runningFrame = endFrame;
    }

    // Summary
    const totalFrames = runningFrame;
    const totalSeconds = parseFloat((runningFrame / FPS).toFixed(1));

    if (options.chapterDurationSeconds) {
        const chapterFrames = Math.round(options.chapterDurationSeconds * FPS);
        if (totalFrames > chapterFrames) {
            globalWarnings.push(
                `  🔴 OVERFLOW: total ${totalSeconds}s > chapter ${options.chapterDurationSeconds}s`
            );
        }
    }

    const result: ValidationResult = {
        segments: reports,
        warnings: globalWarnings,
        totalFrames,
        totalSeconds,
    };

    // Print if verbose
    if (options.verbose !== false) {
        printReport(result, options);
    }

    return result;
}

function printReport(result: ValidationResult, options: ValidateOptions): void {
    console.log("\nSegment Analysis:");
    for (const r of result.segments) {
        const tagsStr = r.tags.length > 0 ? ` [${r.tags.join(", ")}]` : "";
        const warnFlag = r.warnings.length > 0 ? " ⚠️" : " ✅";
        const textPreview = "";  // could add seg.text preview here
        console.log(
            `  #${String(r.index).padStart(2)}  ` +
            `delay=${r.delayLabel.padEnd(6)}  ` +
            `cost=${String(r.costFrames).padStart(4)}f(${r.costSeconds}s)  ` +
            `end=${r.endSeconds}s  ` +
            `idle=${r.idleSeconds}s` +
            `${warnFlag}${tagsStr}${textPreview}`
        );
    }

    if (result.warnings.length > 0) {
        console.log("\nWarnings:");
        for (const w of result.warnings) {
            console.log(w);
        }
    }

    console.log("\nSummary:");
    console.log(`  Total: ${result.totalFrames}f = ${result.totalSeconds}s`);
    if (options.chapterDurationSeconds) {
        const chapterFrames = Math.round(options.chapterDurationSeconds * FPS);
        const margin = chapterFrames - result.totalFrames;
        const marginSec = (margin / FPS).toFixed(1);
        if (margin >= 0) {
            console.log(`  Chapter: ${chapterFrames}f = ${options.chapterDurationSeconds}s`);
            console.log(`  ✅ FITS (margin: ${marginSec}s)`);
        } else {
            console.log(`  Chapter: ${chapterFrames}f = ${options.chapterDurationSeconds}s`);
            console.log(`  🔴 OVERFLOW by ${Math.abs(margin)}f (${Math.abs(parseFloat(marginSec))}s)`);
        }
    }
    console.log("");
}
