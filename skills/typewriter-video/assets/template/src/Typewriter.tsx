import React from "react";
import {
    AbsoluteFill,
    Img,
    staticFile,
} from "remotion";
import { EditorWindow } from "./EditorWindow";
import { TypewriterText, TextSegment } from "./TypewriterText";

// ═══════════════════════════════════════════════════════════════
// CANONICAL DEMO — Self-Explanatory Feature Tutorial
//
// This file IS the living tutorial. The typewriter explains its
// own capabilities by demonstrating each one as it names it.
//
// MAINTENANCE RULE: When a new feature is added, add a new
// chapter here that explicitly demonstrates it.
//
// Structure:
//   Chapter 1 — Typing Modes (burst / normal / deliberate / thinking)
//   Chapter 2 — Ghost Text (autocomplete preview + Tab accept)
//   Chapter 3 — Strike & Correct (type wrong → fix it)
//   Chapter 4 — Emoji Picker (search + select)
//   Chapter 5 — File Tabs (switch context, preserve state)
//   Chapter 6 — Syntax Highlighting (language-aware coloring)
//   Chapter 7 — Cursor Jump & In-Place Mutation (edit existing code)
//   Chapter 8 — Chinese IME Input (中文输入 via pinyin)
//   Chapter 9 — Inline Images (single + multi-row, animations)
//   Chapter 10 — Image Stack (paper pile effect)
//   Finale   — Return to README, confirm everything works
// ═══════════════════════════════════════════════════════════════

const TEXT_SEGMENTS: TextSegment[] = [

    // ─────────────────────────────────────────────────
    // CHAPTER 1: Typing Modes
    // Show the contrast between all four speeds
    // ─────────────────────────────────────────────────
    { text: "# Typing Modes\n\n", mode: "burst", file: "README.md", language: "markdown" },

    // burst: fast, confident
    { text: "This is ", mode: "burst" },
    { text: "burst", mode: "deliberate" },           // ← deliberate on the word itself
    { text: " mode — fast and confident.\n", mode: "burst" },

    // deliberate: slow, weighty (note: only for key words)
    { text: "This word is typed ", mode: "burst" },
    { text: "slowly", mode: "deliberate" },
    { text: ".\n", mode: "burst" },

    // thinking: long pause, then burst
    { text: "Now a long pause before this thought.\n", mode: "thinking" },

    // normal: moderate, connective
    { text: "And this is normal pace.\n\n", mode: "normal" },

    // ─────────────────────────────────────────────────
    // CHAPTER 2: Ghost Text (autocomplete)
    // Type a partial phrase, show grey preview, Tab accept
    // ─────────────────────────────────────────────────
    { text: "## Ghost Text\n\n", mode: "burst" },
    {
        text: "Watch the grey preview: ", mode: "burst",
        ghostText: "this appears automatically.",
        ghostPauseFrames: 30
    },
    { text: "\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 3: Strike & Correct
    // Type wrong text, select it, replace it
    // ─────────────────────────────────────────────────
    { text: "## Strike & Correct\n\n", mode: "burst" },
    { text: "This tool is ", mode: "burst" },
    {
        text: "great", mode: "normal",
        strikeText: "just okay",
        strikeDelete: "select"
    },
    { text: " — watch the correction.\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 4: Emoji Picker
    // Type emoji with Slack-style search
    // ─────────────────────────────────────────────────
    { text: "## Emoji Picker\n\n", mode: "burst" },
    { text: "Reacting with an emoji: ", mode: "burst" },
    {
        text: "🚀",
        mode: "normal",
        emojiPicker: true,
        emojiPickerFrames: 20,
    },
    { text: "\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 5: File Tabs (switch to code)
    // Switch file — title bar changes, canvas clears
    // ─────────────────────────────────────────────────
    { text: "import React from ", mode: "burst", file: "app/page.tsx", language: "tsx" },
    { text: "'react'", mode: "normal" },
    { text: "\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 6: Syntax Highlighting (TSX)
    // Keywords pink, JSX tags blue, strings orange
    // ─────────────────────────────────────────────────
    {
        text: "export default function ", mode: "burst",
        ghostText: "Page() {", ghostPauseFrames: 20
    },
    { text: "\n  return (\n", mode: "burst" },
    { text: "    <div>\n", mode: "burst" },
    { text: "      <h1>", mode: "burst" },
    { text: "Hello, World!", mode: "deliberate" },
    { text: "</h1>\n", mode: "burst" },
    {
        text: "    </div>", mode: "burst",
        ghostText: "\n  );\n}", ghostPauseFrames: 18
    },

    // ─────────────────────────────────────────────────
    // CHAPTER 7: Cursor Jump & In-Place Mutation
    // Jump to line 0, insert 'use cache' directive
    // ─────────────────────────────────────────────────
    {
        text: "'use cache'\n", mode: "thinking",
        insertAt: { line: 0, col: 0 }
    },

    // ─────────────────────────────────────────────────
    // CHAPTER 8: Chinese IME Input (中文输入)
    // Type Chinese characters via pinyin input method
    // ─────────────────────────────────────────────────
    { text: "\n## 中文输入\n\n", mode: "burst", file: "README.md" },
    { text: "你好世界！", mode: "normal", imeInput: true },
    { text: "\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 9: Inline Images
    // Images scroll with text via \uFFFC marker
    // ─────────────────────────────────────────────────
    { text: "\n\n# Inline Images\n\n", mode: "burst", file: "README.md" },
    {
        text: "Here's a screenshot:\n", mode: "normal",
        image: { src: "background.png", heightLines: 4, alt: "Demo screenshot", animation: "fade" }
    },
    { text: "\nImages scroll naturally with text.\n", mode: "normal" },
    {
        text: "\nSide by side:\n", mode: "normal",
        image: {
            items: [
                { src: "background.png", label: "React" },
                { src: "background.png", label: "Next.js" },
                { src: "background.png", label: "Vercel" },
            ],
            width: 85, height: 100, gap: 10, animation: "slide-up",
            heightLines: 4,
        }
    },

    // ─────────────────────────────────────────────────
    // CHAPTER 10: Image Stack
    // Paper pile effect — images pile up with rotation
    // ─────────────────────────────────────────────────
    {
        text: "\n\n📰 Headlines:\n", mode: "normal",
        imageStack: {
            images: ["background.png", "background.png", "background.png"],
            heightLines: 6,
            intervalFrames: 10,
        }
    },

    // ─────────────────────────────────────────────────
    // FINALE: Return to README, check off every feature
    // Proves file state was preserved across the switch
    // ─────────────────────────────────────────────────
    { text: "\n\n## Features\n\n", mode: "burst" },
    { text: "- [x] Typing modes\n", mode: "burst" },
    { text: "- [x] Ghost text\n", mode: "burst" },
    { text: "- [x] Strike & correct\n", mode: "burst" },
    { text: "- [x] Emoji picker\n", mode: "burst" },
    { text: "- [x] File tabs\n", mode: "burst" },
    { text: "- [x] Syntax highlighting\n", mode: "burst" },
    { text: "- [x] Cursor jump\n", mode: "burst" },
    { text: "- [x] 中文输入\n", mode: "burst" },
    { text: "- [x] Image insertion\n", mode: "burst" },
    { text: "- [x] Image stack\n", mode: "burst" },
    { text: "\nAll working ", mode: "burst" },
    {
        text: "✅",
        mode: "normal",
        emojiPicker: true,
        emojiPickerFrames: 12,
    },
];

export const Typewriter: React.FC = () => {
    const [currentFile, setCurrentFile] = React.useState("README.md");

    return (
        <AbsoluteFill
            style={{
                backgroundColor: "#3a3a2a",
            }}
        >
            <Img
                src={staticFile("background.png")}
                style={{
                    position: "absolute",
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    filter: "blur(4px) saturate(0.9)",
                    transform: "scale(1.05)",
                }}
            />

            <AbsoluteFill
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                }}
            >
                <EditorWindow title={currentFile}>
                    <TypewriterText
                        segments={TEXT_SEGMENTS}
                        startFrame={15}
                        onFileChange={setCurrentFile}
                    />
                </EditorWindow>
            </AbsoluteFill>
        </AbsoluteFill>
    );
};
