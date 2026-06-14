import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { ExcalidrawCanvas } from "./ExcalidrawCanvas";
import { TypewriterOverlay } from "./TypewriterOverlay";
import { EditorWindow } from "./EditorWindow";
import { TypewriterText, TextSegment } from "./TypewriterText";
import { Theme, ivoryTheme } from "./themes";
import type { DrawingElement } from "./drawing-types";

// ═══════════════════════════════════════════════════════════
// EXCALIDRAW DEMO — Two modes:
//
// Section A (0–12s):  Standalone canvas — system architecture diagram
// Section B (12–20s): Overlay mode — annotations on typewriter editor
//
// Total: ~20s (600 frames @ 29.97fps)
// ═══════════════════════════════════════════════════════════

// ── Section A: Standalone Canvas Elements ──

const CANVAS_ELEMENTS: DrawingElement[] = [
    // Title
    {
        id: "title",
        type: "text",
        x: 960, y: 80,
        width: 0, height: 0,
        appearAtFrame: 0,
        drawDurationFrames: 1,
        label: "System Architecture",
        labelFontSize: 44,
    },

    // Client rectangle (with fill)
    {
        id: "client",
        type: "rectangle",
        x: 140, y: 250,
        width: 240, height: 120,
        appearAtFrame: 15,
        drawDurationFrames: 35,
        label: "Client",
        fill: "rgba(173, 216, 230, 0.4)",
    },

    // Arrow: Client → Gateway
    {
        id: "client-to-gw",
        type: "arrow",
        x: 0, y: 0,
        points: [[380, 310], [560, 310]],
        appearAtFrame: 55,
        drawDurationFrames: 20,
    },

    // API Gateway
    {
        id: "gateway",
        type: "rectangle",
        x: 560, y: 250,
        width: 280, height: 120,
        appearAtFrame: 80,
        drawDurationFrames: 35,
        label: "API Gateway",
    },

    // Arrow: Gateway → Decision
    {
        id: "gw-to-decision",
        type: "arrow",
        x: 0, y: 0,
        points: [[840, 310], [1020, 310]],
        appearAtFrame: 120,
        drawDurationFrames: 20,
    },

    // Decision diamond
    {
        id: "decision",
        type: "diamond",
        x: 1020, y: 230,
        width: 200, height: 160,
        appearAtFrame: 145,
        drawDurationFrames: 40,
        label: "Auth?",
        labelFontSize: 26,
        fill: "rgba(255, 223, 186, 0.5)",
    },

    // Arrow: Decision → DB (down-right)
    {
        id: "decision-to-db",
        type: "arrow",
        x: 0, y: 0,
        points: [[1120, 390], [1120, 520]],
        appearAtFrame: 190,
        drawDurationFrames: 20,
        label: "Yes",
        labelPosition: "right",
        labelFontSize: 20,
    },

    // Arrow: Decision → rejected (right, dashed)
    {
        id: "decision-to-reject",
        type: "arrow",
        x: 0, y: 0,
        points: [[1220, 310], [1500, 310]],
        appearAtFrame: 190,
        drawDurationFrames: 20,
        strokeStyle: "dashed",
        label: "No",
        labelPosition: "above",
        labelFontSize: 20,
    },

    // 403 text
    {
        id: "rejected",
        type: "text",
        x: 1580, y: 310,
        width: 0, height: 0,
        appearAtFrame: 215,
        drawDurationFrames: 1,
        label: "403 ✋",
        labelFontSize: 28,
        stroke: "#D94040",
    },

    // Database ellipse
    {
        id: "database",
        type: "ellipse",
        x: 980, y: 520,
        width: 280, height: 130,
        appearAtFrame: 215,
        drawDurationFrames: 35,
        label: "Database",
        fill: "rgba(144, 238, 144, 0.3)",
    },

    // Bi-directional arrow: Gateway ↔ Cache
    {
        id: "gw-to-cache",
        type: "arrow",
        x: 0, y: 0,
        points: [[700, 370], [700, 520]],
        appearAtFrame: 245,
        drawDurationFrames: 20,
        startArrowHead: "arrow",
        endArrowHead: "arrow",
    },

    // Cache rectangle (dashed border)
    {
        id: "cache",
        type: "rectangle",
        x: 560, y: 520,
        width: 280, height: 120,
        appearAtFrame: 270,
        drawDurationFrames: 35,
        label: "Cache",
        strokeStyle: "dashed",
        fill: "rgba(221, 160, 221, 0.3)",
    },

    // Freedraw scribble
    {
        id: "emphasis-scribble",
        type: "freedraw",
        x: 0, y: 0,
        points: [
            [140, 780], [300, 776], [460, 782], [620, 778],
            [780, 784], [940, 780], [1100, 776], [1260, 782],
            [1420, 778], [1580, 784], [1740, 780],
        ],
        appearAtFrame: 305,
        drawDurationFrames: 30,
        strokeWidth: 1.5,
        opacity: 0.5,
    },

    // System boundary (dotted ellipse)
    {
        id: "system-boundary",
        type: "ellipse",
        x: 80, y: 180,
        width: 1280, height: 530,
        appearAtFrame: 310,
        drawDurationFrames: 50,
        strokeStyle: "dotted",
        strokeWidth: 1.5,
        label: "Trusted Zone",
        labelPosition: "above",
        labelFontSize: 20,
        opacity: 0.6,
    },
];

// ── Section B: TypewriterOverlay mode ──

const OVERLAY_SEGMENTS: TextSegment[] = [
    { text: "function authenticate(token) {\n", mode: "burst" },
    { text: "  if (!token) {\n", mode: "burst" },
    { text: "    throw new Error('Missing token');\n", mode: "normal" },
    { text: "  }\n", mode: "burst" },
    { text: "  const user = verifyJWT(token);\n", mode: "burst" },
    { text: "  return user;\n", mode: "normal" },
    { text: "}\n", mode: "burst" },
];

// Overlay annotations — pixel-precise coordinates
// Layout constants from TypewriterText:
//   PAD_TOP = 30, PAD_LEFT = 40
//   LINE_HEIGHT = 44px, CHAR_WIDTH = 15.6px
//   Line N text baseline y ≈ PAD_TOP + N * LINE_HEIGHT + 30 (middle of line)
//   Char M x ≈ PAD_LEFT + M * CHAR_WIDTH
//
// Code lines (0-indexed):
//   0: "function authenticate(token) {"     y_top=30
//   1: "  if (!token) {"                    y_top=74
//   2: "    throw new Error('Missing');"     y_top=118
//   3: "  }"                                y_top=162
//   4: "  const user = verifyJWT(token);"    y_top=206
//   5: "  return user;"                      y_top=250
//   6: "}"                                  y_top=294

const OVERLAY_ELEMENTS: DrawingElement[] = [
    // 1. Underline "throw new Error('Missing token')" on line 2
    //    "    throw" starts at char 4 → x = 40 + 4*15.6 = 102.4
    //    line ends at ~char 38 → x = 40 + 38*15.6 = 632.8
    //    bottom of line 2 → y = 118 + 40 = 158
    {
        id: "underline-error",
        type: "freedraw",
        x: 0, y: 0,
        points: [
            [102, 155], [180, 153], [280, 156], [380, 154],
            [480, 157], [570, 155], [630, 153],
        ],
        appearAtFrame: 65,
        drawDurationFrames: 20,
        stroke: "#E74C3C",
        strokeWidth: 2.5,
    },

    // 2. "Guard clause" label — in right margin, aligned with line 2
    //    Right margin starts around x=660, line 2 midpoint y ≈ 118 + 22 = 140
    {
        id: "guard-label",
        type: "text",
        x: 665, y: 140,
        width: 0, height: 0,
        appearAtFrame: 90,
        drawDurationFrames: 1,
        label: "← guard clause",
        labelFontSize: 18,
        stroke: "#E74C3C",
    },

    // 3. Underline "verifyJWT(token)" on line 4
    //    "verifyJWT" starts at char 16 → x = 40 + 16*15.6 = 289.6
    //    "token)" ends at char 31 → x = 40 + 31*15.6 = 523.6
    //    bottom of line 4 → y = 206 + 40 = 246
    {
        id: "underline-jwt",
        type: "freedraw",
        x: 0, y: 0,
        points: [
            [290, 243], [340, 241], [390, 244], [440, 242], [490, 245], [525, 243],
        ],
        appearAtFrame: 115,
        drawDurationFrames: 18,
        stroke: "#27AE60",
        strokeWidth: 2.5,
    },

    // 4. "critical path" label in right margin, aligned with line 4
    {
        id: "jwt-label",
        type: "text",
        x: 665, y: 228,
        width: 0, height: 0,
        appearAtFrame: 138,
        drawDurationFrames: 1,
        label: "← key logic",
        labelFontSize: 18,
        stroke: "#27AE60",
    },

    // 5. Arrow: from "return user" (line 5) up to function name (line 0)
    //    Placed in the left margin: x ≈ 22
    //    line 5 mid → y = 250 + 22 = 272
    //    line 0 mid → y = 30 + 22 = 52
    {
        id: "arrow-return-to-fn",
        type: "arrow",
        x: 0, y: 0,
        points: [[25, 268], [25, 56]],
        appearAtFrame: 160,
        drawDurationFrames: 25,
        stroke: "#2980B9",
        strokeWidth: 2,
    },

    // 6. "returns" label next to the arrow, midpoint
    {
        id: "returns-label",
        type: "text",
        x: 12, y: 165,
        width: 0, height: 0,
        appearAtFrame: 188,
        drawDurationFrames: 1,
        label: "↑",
        labelFontSize: 16,
        stroke: "#2980B9",
    },
];

// ── Section A: Standalone canvas ──
const StandaloneSection: React.FC<{ theme: Theme }> = ({ theme }) => (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
        <AbsoluteFill
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
            }}
        >
            <ExcalidrawCanvas elements={CANVAS_ELEMENTS} theme={theme} />
        </AbsoluteFill>
    </AbsoluteFill>
);

// ── Section B: Overlay on typewriter ──
const OverlaySection: React.FC<{ theme: Theme }> = ({ theme }) => {
    const [currentFile, setCurrentFile] = React.useState("auth.ts");

    const outerBg = theme.outer.bg;
    const isGradient = outerBg.includes("gradient");

    return (
        <AbsoluteFill
            style={{
                backgroundColor: isGradient ? undefined : outerBg,
                ...(isGradient && { backgroundImage: outerBg }),
            }}
        >
            <AbsoluteFill
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                }}
            >
                <EditorWindow
                    title={currentFile}
                    theme={theme}
                    overlay={
                        <TypewriterOverlay
                            elements={OVERLAY_ELEMENTS}
                            theme={theme}
                        />
                    }
                >
                    <TypewriterText
                        segments={OVERLAY_SEGMENTS}
                        startFrame={5}
                        onFileChange={setCurrentFile}
                        theme={theme}
                    />
                </EditorWindow>
            </AbsoluteFill>
        </AbsoluteFill>
    );
};

// ── Main demo composition ──
export const ExcalidrawDemo: React.FC<{ theme?: Theme }> = ({
    theme = ivoryTheme,
}) => {
    return (
        <Series>
            <Series.Sequence durationInFrames={360}>
                <StandaloneSection theme={theme} />
            </Series.Sequence>
            <Series.Sequence durationInFrames={240}>
                <OverlaySection theme={theme} />
            </Series.Sequence>
        </Series>
    );
};
