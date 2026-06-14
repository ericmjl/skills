import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate } from "remotion";
import { EditorWindow } from "./EditorWindow";
import { TypewriterText, TextSegment } from "./TypewriterText";
import {
    Theme,
    ivoryTheme,
    darkEditorTheme,
    chalkBlackboardTheme,
    paperNotebookTheme,
    retroTerminalTheme,
    spotlightTheme,
    lcdTerminalTheme,
    pixelArtTheme,
} from "./themes";

// ═══════════════════════════════════════════════════════════════
// THEME SHOWCASE — Cycles through all 6 themes
//
// Each theme gets a short typing demo to show its personality.
// Total: 6 themes × ~5 seconds each = ~30 seconds
// ═══════════════════════════════════════════════════════════════

// Short demo segments that work well across all themes
const DEMO_SEGMENTS: TextSegment[] = [
    { text: "# Hello, World\n\n", mode: "burst", file: "demo.md", language: "markdown" },
    { text: "This is ", mode: "burst" },
    { text: "Auto-Explainer", mode: "deliberate" },
    { text: " — a visual typing engine.\n\n", mode: "burst" },
    {
        text: "Watch this: ", mode: "burst",
        ghostText: "magic autocomplete ✨",
        ghostPauseFrames: 25
    },
    { text: "\n\n", mode: "burst" },
    { text: "Let me think", mode: "burst" },
    {
        text: " about this carefully.\n", mode: "normal",
        strikeText: " and rush it",
        strikeDelete: "select",
    },
];

// Theme entries with display names
const THEME_ENTRIES: { theme: Theme; label: string }[] = [
    { theme: ivoryTheme, label: "🍦 Ivory" },
    { theme: darkEditorTheme, label: "🌙 Dark Editor" },
    { theme: chalkBlackboardTheme, label: "🪧 Chalk Blackboard" },
    { theme: paperNotebookTheme, label: "📝 Paper Notebook" },
    { theme: retroTerminalTheme, label: "🖥️ Retro Terminal" },
    { theme: spotlightTheme, label: "🍎 macOS Spotlight" },
    { theme: lcdTerminalTheme, label: "📟 LCD Terminal" },
    { theme: pixelArtTheme, label: "🕹️ Pixel Art" },
];

const FRAMES_PER_THEME = 150; // ~5 seconds at 29.97fps
const TRANSITION_FRAMES = 15; // half-second fade

export const ThemeShowcase: React.FC = () => {
    const frame = useCurrentFrame();

    // Which theme is active?
    const themeIndex = Math.min(
        Math.floor(frame / FRAMES_PER_THEME),
        THEME_ENTRIES.length - 1
    );
    const entry = THEME_ENTRIES[themeIndex];
    const theme = entry.theme;
    const localFrame = frame - themeIndex * FRAMES_PER_THEME;

    // Fade in/out for transitions
    const opacity = interpolate(
        localFrame,
        [0, TRANSITION_FRAMES, FRAMES_PER_THEME - TRANSITION_FRAMES, FRAMES_PER_THEME],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    // Determine background style
    const outerBg = theme.outer.bg;
    const isGradient = outerBg.includes("gradient");

    const [currentFile, setCurrentFile] = React.useState("demo.md");

    return (
        <AbsoluteFill
            style={{
                backgroundColor: isGradient ? undefined : outerBg,
                ...(isGradient && { backgroundImage: outerBg }),
            }}
        >
            {theme.outer.backgroundImage && (
                <Img
                    src={staticFile(theme.outer.backgroundImage)}
                    style={{
                        position: "absolute",
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        filter: `blur(${theme.outer.bgBlur ?? 0}px) saturate(${theme.outer.bgSaturation ?? 1})`,
                        transform: "scale(1.05)",
                    }}
                />
            )}

            <AbsoluteFill
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    opacity,
                }}
            >
                <EditorWindow
                    title={currentFile}
                    theme={theme}
                >
                    <TypewriterText
                        segments={DEMO_SEGMENTS}
                        startFrame={themeIndex * FRAMES_PER_THEME + TRANSITION_FRAMES}
                        onFileChange={setCurrentFile}
                        theme={theme}
                    />
                </EditorWindow>
            </AbsoluteFill>

            {/* Theme label — bottom center */}
            <div
                style={{
                    position: "absolute",
                    bottom: 60,
                    left: 0,
                    right: 0,
                    display: "flex",
                    justifyContent: "center",
                    opacity: interpolate(
                        localFrame,
                        [TRANSITION_FRAMES, TRANSITION_FRAMES + 10],
                        [0, 1],
                        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                    ),
                }}
            >
                <div
                    style={{
                        background: "rgba(0,0,0,0.6)",
                        backdropFilter: "blur(12px)",
                        color: "#FFFFFF",
                        padding: "10px 28px",
                        borderRadius: 30,
                        fontSize: 22,
                        fontFamily: "'Inter', 'SF Pro Display', -apple-system, sans-serif",
                        fontWeight: 500,
                        letterSpacing: 0.5,
                    }}
                >
                    {entry.label}
                </div>
            </div>
        </AbsoluteFill>
    );
};
