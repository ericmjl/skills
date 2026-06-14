import React, { useMemo } from "react";
import { useCurrentFrame, interpolate, Easing, staticFile } from "remotion";
import { loadFont as loadLocalFont } from "@remotion/fonts";
import rough from "roughjs";
import type { RoughGenerator } from "roughjs/bin/generator";
import type { PathInfo } from "roughjs/bin/core";
import type {
    DrawingElement,
    DrawingThemeConfig,
    StrokeStyle,
    LabelPosition,
} from "./drawing-types";
import type { Theme } from "./themes";

// ── Load Virgil font (Excalidraw's signature handwriting font) ──
let virgilLoaded = false;
function ensureVirgil() {
    if (virgilLoaded) return;
    virgilLoaded = true;
    loadLocalFont({
        family: "Virgil",
        url: staticFile("fonts/Virgil.woff2"),
        weight: "400",
    });
}

// ═══════════════════════════════════════════════════════════
// ExcalidrawCanvas — Hand-drawn diagram layer
//
// Renders DrawingElement[] as rough.js SVG paths with
// stroke-dashoffset draw-on animation driven by useCurrentFrame().
//
// Uses RoughGenerator.toPaths() for DOM-free SVG path generation,
// compatible with Remotion's headless SSR rendering pipeline.
// ═══════════════════════════════════════════════════════════

// ── Default drawing theme (fallback when theme.drawing is undefined) ──
const DEFAULT_DRAWING_CONFIG: DrawingThemeConfig = {
    stroke: "#1a1a1a",
    strokeWidth: 2,
    fill: "none",
    roughness: 2.5,
    labelColor: "#1a1a1a",
    labelFont:
        "Virgil, Segoe Print, Bradley Hand, Chilanka, TSCu_Comic, casual, cursive",
    labelSize: 28,
    arrowHeadSize: 18,
};

/** Merge theme drawing config with defaults */
function getDrawingConfig(theme?: Theme): DrawingThemeConfig {
    const themeDrawing = theme?.drawing;
    if (!themeDrawing) return DEFAULT_DRAWING_CONFIG;
    return { ...DEFAULT_DRAWING_CONFIG, ...themeDrawing };
}

// ── Pre-computed path data for a single element ──
interface ComputedElement {
    element: DrawingElement;
    paths: (PathInfo & { length: number })[];
    arrowHeadPaths: (PathInfo & { length: number })[];
    totalLength: number;
}

// ── SVG path length estimation (DOM-free for SSR) ──

function estimatePathLength(d: string): number {
    let length = 0;
    let cx = 0,
        cy = 0;
    let mx = 0,
        my = 0;

    const commands = d.match(/[MLCQZmlcqz][^MLCQZmlcqz]*/gi) || [];

    for (const cmd of commands) {
        const type = cmd[0];
        const nums = cmd
            .slice(1)
            .trim()
            .split(/[\s,]+/)
            .map(Number);

        switch (type) {
            case "M":
                cx = nums[0];
                cy = nums[1];
                mx = cx;
                my = cy;
                break;
            case "m":
                cx += nums[0];
                cy += nums[1];
                mx = cx;
                my = cy;
                break;
            case "L":
                for (let i = 0; i < nums.length; i += 2) {
                    const dx = nums[i] - cx;
                    const dy = nums[i + 1] - cy;
                    length += Math.sqrt(dx * dx + dy * dy);
                    cx = nums[i];
                    cy = nums[i + 1];
                }
                break;
            case "l":
                for (let i = 0; i < nums.length; i += 2) {
                    length += Math.sqrt(
                        nums[i] * nums[i] + nums[i + 1] * nums[i + 1],
                    );
                    cx += nums[i];
                    cy += nums[i + 1];
                }
                break;
            case "C":
                for (let i = 0; i < nums.length; i += 6) {
                    const ex = nums[i + 4],
                        ey = nums[i + 5];
                    const chord = Math.sqrt(
                        (ex - cx) ** 2 + (ey - cy) ** 2,
                    );
                    const cp1 = Math.sqrt(
                        (nums[i] - cx) ** 2 + (nums[i + 1] - cy) ** 2,
                    );
                    const cp2 = Math.sqrt(
                        (nums[i + 2] - nums[i]) ** 2 +
                        (nums[i + 3] - nums[i + 1]) ** 2,
                    );
                    const cp3 = Math.sqrt(
                        (ex - nums[i + 2]) ** 2 +
                        (ey - nums[i + 3]) ** 2,
                    );
                    length += (chord + cp1 + cp2 + cp3) / 2;
                    cx = ex;
                    cy = ey;
                }
                break;
            case "c":
                for (let i = 0; i < nums.length; i += 6) {
                    const ex = nums[i + 4],
                        ey = nums[i + 5];
                    const chord = Math.sqrt(ex * ex + ey * ey);
                    const cp1 = Math.sqrt(
                        nums[i] ** 2 + nums[i + 1] ** 2,
                    );
                    const cp2 = Math.sqrt(
                        (nums[i + 2] - nums[i]) ** 2 +
                        (nums[i + 3] - nums[i + 1]) ** 2,
                    );
                    const cp3 = Math.sqrt(
                        (ex - nums[i + 2]) ** 2 +
                        (ey - nums[i + 3]) ** 2,
                    );
                    length += (chord + cp1 + cp2 + cp3) / 2;
                    cx += ex;
                    cy += ey;
                }
                break;
            case "Q":
                for (let i = 0; i < nums.length; i += 4) {
                    const ex = nums[i + 2],
                        ey = nums[i + 3];
                    const dx = ex - cx,
                        dy = ey - cy;
                    length += Math.sqrt(dx * dx + dy * dy) * 1.1;
                    cx = ex;
                    cy = ey;
                }
                break;
            case "Z":
            case "z": {
                const dx = mx - cx,
                    dy = my - cy;
                length += Math.sqrt(dx * dx + dy * dy);
                cx = mx;
                cy = my;
                break;
            }
        }
    }

    return Math.max(length, 1);
}

// ── Hand-drawn arrowhead generator ──

function generateArrowHead(
    fromX: number,
    fromY: number,
    toX: number,
    toY: number,
    size: number,
    gen: RoughGenerator,
    strokeColor: string,
    strokeWidth: number,
    roughness: number,
): (PathInfo & { length: number })[] {
    const angle = Math.atan2(toY - fromY, toX - fromX);
    const a1 = angle + Math.PI * 0.78;
    const a2 = angle - Math.PI * 0.78;
    const x1 = toX + size * Math.cos(a1);
    const y1 = toY + size * Math.sin(a1);
    const x2 = toX + size * Math.cos(a2);
    const y2 = toY + size * Math.sin(a2);

    const opts = {
        stroke: strokeColor,
        strokeWidth,
        roughness: roughness * 0.6,
        bowing: 1,
    };

    const line1 = gen.line(x1, y1, toX, toY, opts);
    const line2 = gen.line(x2, y2, toX, toY, opts);

    return [
        ...gen.toPaths(line1).map((pi) => ({
            ...pi,
            length: estimatePathLength(pi.d),
        })),
        ...gen.toPaths(line2).map((pi) => ({
            ...pi,
            length: estimatePathLength(pi.d),
        })),
    ];
}

// ── Stroke dash pattern for dashed/dotted ──

function getStrokeLineDash(
    style: StrokeStyle | undefined,
    strokeWidth: number,
): number[] | undefined {
    switch (style) {
        case "dashed":
            return [strokeWidth * 4, strokeWidth * 3];
        case "dotted":
            return [strokeWidth * 1.5, strokeWidth * 2];
        default:
            return undefined;
    }
}

// ── Label position calculator ──

function getLabelPosition(
    el: DrawingElement,
    pos: LabelPosition,
    fontSize: number,
): {
    x: number;
    y: number;
    anchor: "start" | "middle" | "end";
    baseline: "auto" | "central";
} {
    const cx = el.x + (el.width ?? 0) / 2;
    const cy = el.y + (el.height ?? 0) / 2;
    const gap = fontSize * 0.6;

    switch (pos) {
        case "above":
            return {
                x: cx,
                y: el.y - gap,
                anchor: "middle",
                baseline: "auto",
            };
        case "below":
            return {
                x: cx,
                y: el.y + (el.height ?? 0) + gap + fontSize * 0.3,
                anchor: "middle",
                baseline: "auto",
            };
        case "left":
            return {
                x: el.x - gap,
                y: cy,
                anchor: "end",
                baseline: "central",
            };
        case "right":
            return {
                x: el.x + (el.width ?? 0) + gap,
                y: cy,
                anchor: "start",
                baseline: "central",
            };
        case "center":
        default:
            return {
                x: cx,
                y: cy,
                anchor: "middle",
                baseline: "central",
            };
    }
}

// ── Main component ──

export interface ExcalidrawCanvasProps {
    elements: DrawingElement[];
    theme?: Theme;
    /** SVG viewBox width, default 1920 */
    viewWidth?: number;
    /** SVG viewBox height, default 1080 */
    viewHeight?: number;
}

export const ExcalidrawCanvas: React.FC<ExcalidrawCanvasProps> = ({
    elements,
    theme,
    viewWidth = 1920,
    viewHeight = 1080,
}) => {
    const frame = useCurrentFrame();
    const config = getDrawingConfig(theme);
    ensureVirgil();

    // Pre-compute rough.js paths (runs once, memoized)
    const computed = useMemo<ComputedElement[]>(() => {
        const gen: RoughGenerator = rough.generator();

        return elements.map((el) => {
            const strokeColor = el.stroke ?? config.stroke;
            const strokeW = el.strokeWidth ?? config.strokeWidth;
            const fillColor = el.fill ?? config.fill;
            const roughnessVal = el.roughness ?? config.roughness;

            const lineDash = getStrokeLineDash(el.strokeStyle, strokeW);

            const opts = {
                stroke: strokeColor,
                strokeWidth: strokeW,
                fill: fillColor,
                fillStyle: el.fillStyle ?? "hachure",
                roughness: roughnessVal,
                bowing: 2,
                curveFitting: 0.95,
                seed: el.id ? hashCode(el.id) : undefined,
                ...(lineDash && {
                    strokeLineDash: lineDash,
                }),
            };

            let drawable;
            let arrowHeadPaths: (PathInfo & { length: number })[] = [];

            switch (el.type) {
                case "rectangle":
                    drawable = gen.rectangle(
                        el.x,
                        el.y,
                        el.width ?? 200,
                        el.height ?? 100,
                        opts,
                    );
                    break;

                case "ellipse":
                    drawable = gen.ellipse(
                        el.x + (el.width ?? 200) / 2,
                        el.y + (el.height ?? 100) / 2,
                        el.width ?? 200,
                        el.height ?? 100,
                        opts,
                    );
                    break;

                case "diamond": {
                    const w = el.width ?? 160;
                    const h = el.height ?? 100;
                    // Diamond = rotated square as a polygon
                    const pts: [number, number][] = [
                        [el.x + w / 2, el.y], // top
                        [el.x + w, el.y + h / 2], // right
                        [el.x + w / 2, el.y + h], // bottom
                        [el.x, el.y + h / 2], // left
                    ];
                    drawable = gen.polygon(pts, opts);
                    break;
                }

                case "line": {
                    const pts =
                        el.points ?? [
                            [0, 0],
                            [200, 0],
                        ];
                    const absolutePts = pts.map(
                        ([px, py]) =>
                            [el.x + px, el.y + py] as [number, number],
                    );
                    drawable = gen.linearPath(absolutePts, opts);
                    break;
                }

                case "arrow": {
                    const pts =
                        el.points ?? [
                            [0, 0],
                            [200, 0],
                        ];
                    const absolutePts = pts.map(
                        ([px, py]) =>
                            [el.x + px, el.y + py] as [number, number],
                    );
                    drawable = gen.linearPath(absolutePts, opts);

                    // End arrowhead (default: "arrow")
                    const endHead = el.endArrowHead ?? "arrow";
                    if (
                        endHead !== "none" &&
                        absolutePts.length >= 2
                    ) {
                        const from =
                            absolutePts[absolutePts.length - 2];
                        const to =
                            absolutePts[absolutePts.length - 1];
                        arrowHeadPaths.push(
                            ...generateArrowHead(
                                from[0],
                                from[1],
                                to[0],
                                to[1],
                                config.arrowHeadSize,
                                gen,
                                strokeColor,
                                strokeW,
                                roughnessVal,
                            ),
                        );
                    }

                    // Start arrowhead (if specified)
                    if (
                        el.startArrowHead &&
                        el.startArrowHead !== "none" &&
                        absolutePts.length >= 2
                    ) {
                        const from = absolutePts[1];
                        const to = absolutePts[0];
                        arrowHeadPaths.push(
                            ...generateArrowHead(
                                from[0],
                                from[1],
                                to[0],
                                to[1],
                                config.arrowHeadSize,
                                gen,
                                strokeColor,
                                strokeW,
                                roughnessVal,
                            ),
                        );
                    }
                    break;
                }

                case "freedraw": {
                    if (el.pathData) {
                        drawable = gen.path(el.pathData, {
                            ...opts,
                            fill: "none", // freedraw is stroke-only
                        });
                    } else if (el.points && el.points.length >= 2) {
                        // Convert points to a smooth curve
                        const absolutePts = el.points.map(
                            ([px, py]) =>
                                [el.x + px, el.y + py] as [
                                    number,
                                    number,
                                ],
                        );
                        drawable = gen.curve(absolutePts, {
                            ...opts,
                            fill: "none",
                        });
                    } else {
                        return {
                            element: el,
                            paths: [],
                            arrowHeadPaths: [],
                            totalLength: 0,
                        };
                    }
                    break;
                }

                case "text":
                    return {
                        element: el,
                        paths: [],
                        arrowHeadPaths: [],
                        totalLength: 0,
                    };
            }

            const pathInfos = gen.toPaths(drawable);
            const pathsWithLength = pathInfos.map((pi) => ({
                ...pi,
                length: estimatePathLength(pi.d),
            }));
            const totalLength = pathsWithLength.reduce(
                (acc, p) => acc + p.length,
                0,
            );

            return {
                element: el,
                paths: pathsWithLength,
                arrowHeadPaths,
                totalLength,
            };
        });
    }, [elements, config]);

    return (
        <svg
            viewBox={`0 0 ${viewWidth} ${viewHeight}`}
            width="100%"
            height="100%"
            style={{ position: "absolute", top: 0, left: 0 }}
        >
            {computed.map((comp, idx) => {
                const el = comp.element;
                const localFrame = frame - el.appearAtFrame;

                // Not yet visible
                if (localFrame < 0) return null;

                // Draw progress (0 → 1)
                const drawProgress = interpolate(
                    localFrame,
                    [0, el.drawDurationFrames],
                    [0, 1],
                    {
                        extrapolateRight: "clamp",
                        easing: Easing.out(Easing.cubic),
                    },
                );

                // Label fade-in — starts after stroke completes, 10 frame fade
                const labelOpacity = el.label
                    ? interpolate(
                        localFrame,
                        [
                            el.drawDurationFrames,
                            el.drawDurationFrames + 10,
                        ],
                        [0, 1],
                        {
                            extrapolateLeft: "clamp",
                            extrapolateRight: "clamp",
                        },
                    )
                    : 0;

                // Element-level opacity
                const elementOpacity = el.opacity ?? 1;

                // Rotation transform
                const rotateTransform = el.rotation
                    ? `rotate(${el.rotation} ${el.x + (el.width ?? 0) / 2} ${el.y + (el.height ?? 0) / 2})`
                    : undefined;

                const fontSize =
                    el.labelFontSize ?? config.labelSize;
                const labelPos = getLabelPosition(
                    el,
                    el.labelPosition ?? "center",
                    fontSize,
                );

                return (
                    <g
                        key={el.id ?? idx}
                        opacity={elementOpacity}
                        transform={rotateTransform}
                    >
                        {/* Stroke + fill paths */}
                        {comp.paths.map((pathData, pi) => {
                            const dashOffset =
                                pathData.length * (1 - drawProgress);
                            return (
                                <path
                                    key={pi}
                                    d={pathData.d}
                                    stroke={pathData.stroke}
                                    strokeWidth={pathData.strokeWidth}
                                    fill={pathData.fill ?? "none"}
                                    strokeDasharray={pathData.length}
                                    strokeDashoffset={dashOffset}
                                    fillOpacity={drawProgress}
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            );
                        })}

                        {/* Arrow heads (hand-drawn) */}
                        {comp.arrowHeadPaths.map(
                            (pathData, pi) => {
                                const dashOffset =
                                    pathData.length *
                                    (1 - drawProgress);
                                return (
                                    <path
                                        key={`ah-${pi}`}
                                        d={pathData.d}
                                        stroke={pathData.stroke}
                                        strokeWidth={
                                            pathData.strokeWidth
                                        }
                                        fill="none"
                                        strokeDasharray={
                                            pathData.length
                                        }
                                        strokeDashoffset={dashOffset}
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                );
                            },
                        )}

                        {/* Text label */}
                        {el.label && labelOpacity > 0 && (
                            <text
                                x={labelPos.x}
                                y={labelPos.y}
                                textAnchor={labelPos.anchor}
                                dominantBaseline={
                                    labelPos.baseline
                                }
                                fill={
                                    el.stroke ?? config.labelColor
                                }
                                fontFamily={config.labelFont}
                                fontSize={fontSize}
                                fontWeight="400"
                                opacity={labelOpacity}
                            >
                                {el.label}
                            </text>
                        )}
                    </g>
                );
            })}
        </svg>
    );
};

/** Simple string hash for deterministic rough.js seeds */
function hashCode(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash |= 0;
    }
    return Math.abs(hash);
}
