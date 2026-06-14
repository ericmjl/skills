import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { Theme, ivoryTheme } from "./themes";
import { LayoutPreset, LANDSCAPE } from "./layout";

const DOT_GAP = 8;

export const EditorWindow: React.FC<{
    children: React.ReactNode;
    title?: string;
    theme?: Theme;
    /** Layout preset for dimension adaptation (default: LANDSCAPE) */
    layout?: LayoutPreset;
    /** Optional overlay rendered inside the content area (e.g. TypewriterOverlay) */
    overlay?: React.ReactNode;
}> = ({ children, title = "playground/text.mdx", theme = ivoryTheme, layout = LANDSCAPE, overlay }) => {
    const DOT_SIZE = layout.dotSize;
    const TITLE_BAR_HEIGHT = layout.titleBarHeight;
    const LINE_HEIGHT_PX = layout.lineHeight;
    const frame = useCurrentFrame();

    const showChrome = theme.editor.showChrome;
    const isLcdBezel = theme.effects?.lcdBezel ?? false;

    const editorContent = (
        <div
            style={{
                width: layout.editorWidth,
                height: layout.editorHeight,
                borderRadius: theme.editor.borderRadius,
                overflow: "hidden",
                boxShadow: isLcdBezel
                    ? theme.effects?.lcdBezelShadow ?? "inset 0 2px 8px rgba(0,0,0,0.3)"
                    : showChrome
                        ? "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
                        : "none",
                display: "flex",
                flexDirection: "column",
                backgroundColor: theme.editor.windowBg,
                // Optional outer border for chrome-less themes
                ...(theme.editor.borderColor && {
                    border: `${theme.editor.borderWidth ?? 1}px solid ${theme.editor.borderColor}`,
                }),
                // Frosted glass effect for spotlight theme
                ...(theme.name === "spotlight" && {
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    boxShadow: "0 25px 60px -12px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255,255,255,0.4)",
                }),
                position: "relative",
            }}
        >
            {/* Title bar (only for chrome themes) */}
            {showChrome && (
                <div
                    style={{
                        height: TITLE_BAR_HEIGHT,
                        backgroundColor: theme.editor.titleBarBg,
                        borderBottom: `1px solid ${theme.editor.titleBarBorder}`,
                        display: "flex",
                        alignItems: "center",
                        paddingLeft: 18,
                        paddingRight: 18,
                        position: "relative",
                        flexShrink: 0,
                    }}
                >
                    {/* Traffic light dots */}
                    <div style={{ display: "flex", gap: DOT_GAP }}>
                        {theme.editor.dotColors.map((color, i) => (
                            <div
                                key={i}
                                style={{
                                    width: DOT_SIZE,
                                    height: DOT_SIZE,
                                    borderRadius: "50%",
                                    backgroundColor: color,
                                }}
                            />
                        ))}
                    </div>

                    {/* Title */}
                    <div
                        style={{
                            position: "absolute",
                            left: 0,
                            right: 0,
                            textAlign: "center",
                            fontFamily: theme.editor.titleFont,
                            fontSize: 14,
                            color: theme.editor.titleColor,
                            fontWeight: 400,
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            gap: 6,
                        }}
                    >
                        <span>{title}</span>
                        <span
                            style={{
                                width: 8,
                                height: 8,
                                borderRadius: "50%",
                                backgroundColor: theme.editor.titleColor,
                                opacity: 0.5,
                                display: "inline-block",
                            }}
                        />
                    </div>
                </div>
            )}

            {/* Editor body */}
            <div
                style={{
                    flex: 1,
                    padding: `${layout.padTop}px ${layout.padLeft}px`,
                    height: showChrome
                        ? layout.editorHeight - TITLE_BAR_HEIGHT - layout.padTop * 2
                        : layout.editorHeight - layout.padTop * 2,
                    overflow: "hidden",
                    position: "relative",
                    backgroundColor: theme.canvas.bg,
                }}
            >
                {children}
                {overlay}

                {/* ── Ruled lines effect (Paper Notebook) ── */}
                {theme.effects?.ruledLines && (
                    <div
                        style={{
                            position: "absolute",
                            inset: 0,
                            pointerEvents: "none",
                            backgroundImage: `repeating-linear-gradient(
                                to bottom,
                                transparent,
                                transparent ${LINE_HEIGHT_PX - 1}px,
                                ${theme.effects.ruledLineColor ?? "rgba(0,0,0,0.08)"} ${LINE_HEIGHT_PX - 1}px,
                                ${theme.effects.ruledLineColor ?? "rgba(0,0,0,0.08)"} ${LINE_HEIGHT_PX}px
                            )`,
                            backgroundPosition: "0 29px", // align with padding top
                            zIndex: 0,
                        }}
                    />
                )}

                {/* ── Chalk texture overlay (Chalk Blackboard) ── */}
                {theme.effects?.chalkTexture && (
                    <div
                        style={{
                            position: "absolute",
                            inset: 0,
                            pointerEvents: "none",
                            opacity: theme.effects.chalkNoiseOpacity ?? 0.03,
                            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='256' height='256' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E")`,
                            backgroundSize: "128px 128px",
                            zIndex: 5,
                        }}
                    />
                )}

                {/* ── CRT scanlines overlay (Retro Terminal) ── */}
                {theme.effects?.scanlines && (
                    <div
                        style={{
                            position: "absolute",
                            inset: 0,
                            pointerEvents: "none",
                            backgroundImage: `repeating-linear-gradient(
                                to bottom,
                                transparent,
                                transparent 1px,
                                ${theme.effects.scanlineColor ?? "rgba(0,0,0,0.15)"} 1px,
                                ${theme.effects.scanlineColor ?? "rgba(0,0,0,0.15)"} 2px
                            )`,
                            opacity: theme.effects.scanlineOpacity ?? 0.15,
                            zIndex: 5,
                        }}
                    />
                )}
            </div>
        </div>
    );

    // ── LCD Bezel: wrap editor in a physical chassis frame ──
    if (isLcdBezel) {
        const frameColor = theme.effects?.lcdOuterFrameColor ?? "#3A3A38";
        const frameWidth = theme.effects?.lcdOuterFrameWidth ?? 14;
        return (
            <div
                style={{
                    // Outer chassis — the "device body"
                    padding: frameWidth,
                    backgroundColor: frameColor,
                    borderRadius: 6,
                    boxShadow: "6px 6px 0px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08)",
                    position: "relative",
                }}
            >
                {/* Chassis highlight edge (top bevel) */}
                <div
                    style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        right: 0,
                        height: 1,
                        background: "rgba(255,255,255,0.12)",
                        borderRadius: "6px 6px 0 0",
                        pointerEvents: "none",
                    }}
                />
                {/* Corner screws — TE mechanical anchors */}
                {[
                    { top: 6, left: 6 },
                    { top: 6, right: 6 },
                    { bottom: 6, left: 6 },
                    { bottom: 6, right: 6 },
                ].map((pos, i) => (
                    <div
                        key={i}
                        style={{
                            position: "absolute",
                            ...pos,
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            backgroundColor: "rgba(255,255,255,0.1)",
                            border: "0.5px solid rgba(255,255,255,0.15)",
                            zIndex: 2,
                        }}
                    />
                ))}
                {editorContent}
            </div>
        );
    }

    return editorContent;
};

