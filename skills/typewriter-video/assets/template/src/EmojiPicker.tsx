import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

// ═══════════════════════════════════════════════════════════
// Emoji Picker — a floating autocomplete popup that appears
// when the user types `:emoji_name`. Shows a suggestion with
// the emoji preview and label, then disappears after selection.
//
// Based on reference frame_07: small rounded pill with teal
// border, showing emoji thumbnail + text label.
// ═══════════════════════════════════════════════════════════

interface EmojiSuggestion {
    emoji: string;
    label: string;
}

export const EmojiPicker: React.FC<{
    suggestion: EmojiSuggestion;
    showAtFrame: number;
    hideAtFrame: number;
}> = ({ suggestion, showAtFrame, hideAtFrame }) => {
    const frame = useCurrentFrame();

    if (frame < showAtFrame || frame > hideAtFrame + 10) return null;

    // Fade in
    const fadeIn = interpolate(
        frame,
        [showAtFrame, showAtFrame + 6],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    // Slide up entrance
    const slideY = interpolate(
        frame,
        [showAtFrame, showAtFrame + 6],
        [8, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    // Fade out
    const fadeOut = interpolate(
        frame,
        [hideAtFrame, hideAtFrame + 6],
        [1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    const opacity = Math.min(fadeIn, fadeOut);

    return (
        <div
            style={{
                position: "absolute",
                bottom: "100%",
                left: 0,
                marginBottom: 4,
                opacity,
                transform: `translateY(${slideY}px)`,
            }}
        >
            <div
                style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "6px 14px",
                    borderRadius: 8,
                    border: "1.5px solid #2DA44E",
                    backgroundColor: "rgba(45, 164, 78, 0.06)",
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)",
                    fontFamily: "monospace",
                    fontSize: 18,
                    color: "#24292E",
                    whiteSpace: "nowrap",
                }}
            >
                <span style={{ fontSize: 22 }}>{suggestion.emoji}</span>
                <span>{suggestion.label}</span>
            </div>
        </div>
    );
};
