import React from "react";
import { ExcalidrawCanvas } from "./ExcalidrawCanvas";
import type { DrawingElement } from "./drawing-types";
import type { Theme } from "./themes";
import { LayoutPreset, LANDSCAPE } from "./layout";

// ═══════════════════════════════════════════════════════════
// TypewriterOverlay — Drawing annotations on top of the editor
//
// Thin wrapper that renders ExcalidrawCanvas inside the
// editor content area. Coordinates are relative to the text
// canvas origin (0,0 = top-left corner of where text starts).
//
// viewBox matches editor content dimensions (800 × 500) so
// drawing elements align naturally with typewriter text.
// ═══════════════════════════════════════════════════════════

/** Default content area dimensions (EditorWindow with chrome) */
const CONTENT_WIDTH = 800; // 880 - 40px padding left - 40px padding right
const CONTENT_HEIGHT = 500; // editor body height when showChrome is true

export interface TypewriterOverlayProps {
    /** Drawing elements to render over the text */
    elements: DrawingElement[];
    /** Theme — passed through to ExcalidrawCanvas */
    theme?: Theme;
    /** Layout preset for dimension adaptation */
    layout?: LayoutPreset;
    /** Override content area width */
    contentWidth?: number;
    /** Override content area height */
    contentHeight?: number;
}

export const TypewriterOverlay: React.FC<TypewriterOverlayProps> = ({
    elements,
    theme,
    layout = LANDSCAPE,
    contentWidth,
    contentHeight,
}) => {
    const width = contentWidth ?? (layout.editorWidth - layout.padLeft - layout.padRight);
    const height = contentHeight ?? (layout.editorHeight - layout.titleBarHeight - layout.padTop * 2);
    if (!elements || elements.length === 0) return null;

    return (
        <div
            style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                pointerEvents: "none",
                zIndex: 10,
            }}
        >
            <ExcalidrawCanvas
                elements={elements}
                theme={theme}
                viewWidth={width}
                viewHeight={height}
            />
        </div>
    );
};
