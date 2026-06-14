import React from "react";
import { AbsoluteFill } from "remotion";
import { LayoutPreset, LANDSCAPE } from "./layout";

/**
 * Canvas5K — a wrapper for rendering at 5K while developing at standard resolution.
 * Supports both landscape (5120×2880) and portrait (2880×5120) via layout preset.
 *   <Composition width={5120} height={2880} component={MyComp} ... />
 *
 * Inside MyComp, wrap everything in Canvas5K so the internal layout
 * uses standard dimensions but renders at 5K resolution.
 */
export const Canvas5K: React.FC<{ children: React.ReactNode; layout?: LayoutPreset }> = ({
    children,
    layout = LANDSCAPE,
}) => {
    const scale = layout.name === "portrait"
        ? 2880 / layout.width   // 2880 / 1080 ≈ 2.667
        : 5120 / layout.width;  // 5120 / 1920 ≈ 2.667
    return (
        <AbsoluteFill
            style={{
                width: layout.width,
                height: layout.height,
                transform: `scale(${scale})`,
                transformOrigin: "top left",
            }}
        >
            {children}
        </AbsoluteFill>
    );
};
