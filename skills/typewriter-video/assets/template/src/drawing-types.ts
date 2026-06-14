// ═══════════════════════════════════════════════════════════
// Drawing Layer — Type Definitions
//
// Shared types for the Excalidraw-style hand-drawn layer.
// Used by ExcalidrawCanvas.tsx and any future overlay mode.
// ═══════════════════════════════════════════════════════════

/** Supported drawing element types */
export type DrawingElementType =
    | "rectangle"
    | "ellipse"
    | "diamond"
    | "arrow"
    | "line"
    | "freedraw"
    | "text";

/** Fill style options for rough.js shapes */
export type FillStyle =
    | "hachure"
    | "solid"
    | "zigzag"
    | "cross-hatch"
    | "dots";

/** Stroke style (solid, dashed, dotted) */
export type StrokeStyle = "solid" | "dashed" | "dotted";

/** Label position relative to the shape */
export type LabelPosition =
    | "center"    // inside shape, centered (default)
    | "above"     // above shape
    | "below"     // below shape
    | "right"     // to the right
    | "left";     // to the left

/** Arrowhead type */
export type ArrowHeadType = "arrow" | "triangle" | "dot" | "bar" | "none";

/**
 * A single drawing element to render on the canvas.
 *
 * Position (x, y) is relative to the SVG viewBox (default 1920×1080).
 * Timing is in Remotion frames (29.97fps).
 */
export type DrawingElement = {
    /** Optional stable ID for referencing */
    id?: string;

    /** Shape type */
    type: DrawingElementType;

    /** Top-left X position */
    x: number;

    /** Top-left Y position */
    y: number;

    /** Width (rectangle, ellipse, diamond) */
    width?: number;

    /** Height (rectangle, ellipse, diamond) */
    height?: number;

    /** Polyline points for arrow/line — relative to (x, y) */
    points?: [number, number][];

    /** SVG path data for freedraw elements */
    pathData?: string;

    /** Text content — for text elements, or as a label on shapes */
    label?: string;

    /** Font size override for label */
    labelFontSize?: number;

    /** Label position relative to shape */
    labelPosition?: LabelPosition;

    // ── Timing ──

    /** Frame at which this element begins drawing */
    appearAtFrame: number;

    /** Number of frames for the stroke animation */
    drawDurationFrames: number;

    // ── Style overrides (defaults come from theme.drawing) ──

    /** Stroke color */
    stroke?: string;

    /** Stroke width */
    strokeWidth?: number;

    /** Fill color ('none' for transparent) */
    fill?: string;

    /** Fill pattern style */
    fillStyle?: FillStyle;

    /** Stroke pattern (solid, dashed, dotted) */
    strokeStyle?: StrokeStyle;

    /** Roughness: 0 (smooth) to 3 (very rough). Default: 2.5 */
    roughness?: number;

    /** Opacity (0–1) for the whole element */
    opacity?: number;

    /** Rotation in degrees */
    rotation?: number;

    // ── Arrow-specific ──

    /** Start arrowhead type */
    startArrowHead?: ArrowHeadType;

    /** End arrowhead type (default: "arrow") */
    endArrowHead?: ArrowHeadType;
};

/**
 * Theme extension for the drawing layer.
 * Added as an optional `drawing` field on the Theme interface.
 */
export type DrawingThemeConfig = {
    /** Default stroke color */
    stroke: string;

    /** Default stroke width */
    strokeWidth: number;

    /** Default fill color */
    fill: string;

    /** Default roughness (0-3) */
    roughness: number;

    /** Text label color */
    labelColor: string;

    /** Text label font family */
    labelFont: string;

    /** Text label font size */
    labelSize: number;

    /** Arrowhead triangle size (px) */
    arrowHeadSize: number;
};
