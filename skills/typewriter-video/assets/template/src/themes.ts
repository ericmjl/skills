// ═══════════════════════════════════════════════════════════
// Theme System — Visual identities for Auto-Explainer
//
// Each theme is a plain object defining:
//   editor  → window chrome (title bar, dots, borders)
//   canvas  → typing surface (text, cursor, active line)
//   syntax  → syntax highlighting palette
//   popup   → emoji picker + IME panel
//   outer   → background behind the editor window
//   font    → primary font configuration
//   effects → optional visual effects (CRT, ruled lines, etc.)
//   drawing → optional hand-drawn diagram layer colors
// ═══════════════════════════════════════════════════════════

import type { DrawingThemeConfig } from "./drawing-types";

// ── Syntax color palette ──
export interface SyntaxColors {
    keyword: string;
    type: string;
    string: string;
    number: string;
    comment: string;
    tag: string;
    attribute: string;
    function: string;
    operator: string;
    punctuation: string;
    default: string;
    // Bash-specific
    command: string;
    flag: string;
    // Markdown-specific
    heading: string;
    bold: string;
    link: string;
    listMarker: string;
}

// ── Full theme definition ──
export interface Theme {
    name: string;
    editor: {
        windowBg: string;          // overall window background
        titleBarBg: string;        // title bar background
        titleBarBorder: string;    // border below title bar
        titleColor: string;        // title text color
        titleFont: string;         // title font family
        dotColors: [string, string, string]; // traffic light dot colors
        borderRadius: number;      // window corner radius
        showChrome: boolean;       // show macOS title bar (dots + title)?
        borderColor?: string;      // outer border of the editor window
        borderWidth?: number;
    };
    canvas: {
        bg: string;                // editor body background
        textColor: string;         // primary text color
        cursorColor: string;       // cursor bar color
        cursorWidth?: number;      // cursor bar width (default: 2)
        activeLineBg: string;      // active (current) line highlight
        ghostTextColor: string;    // ghost text (autocomplete preview)
        selectionColor: string;    // text selection highlight
        imageLabelColor: string;   // image label text color
        imageCardBg: string;       // multi-image card background
        imageShadow: string;       // image drop shadow
    };
    syntax: SyntaxColors;
    popup: {
        bg: string;                // popup background
        border: string;            // popup border
        shadow: string;            // popup box-shadow
        borderRadius: number;
        selectedBg: string;        // selected item background
        selectedBorder: string;    // selected item left border
        textColor: string;         // popup text color
        secondaryColor: string;    // secondary text (label, index)
        // IME panel specific
        imeBg: string;
        imeBorder: string;
        imeShadow: string;
        imeSelectedBg: string;
        imeSelectedTextColor: string;
        imeLabelColor: string;
    };
    outer: {
        bg: string;                // background behind editor
        backgroundImage?: string;  // optional: path to bg image (relative to public/)
        bgBlur?: number;           // blur amount for background image
        bgSaturation?: number;     // saturation for background image
    };
    font: {
        family: string;            // CSS font-family (loaded font)
        loadId: string;            // @remotion/google-fonts font ID (empty if using localFile)
        localFile?: string;        // local .woff2 filename in public/fonts/ (for bundled fonts)
        localFamily?: string;      // CSS family name for local font registration
        weight: string;            // font weight
        size: number;              // font size in px
    };
    effects?: {
        // CRT scanlines (Retro Terminal)
        scanlines?: boolean;
        scanlineColor?: string;
        scanlineOpacity?: number;
        // Text glow (Retro Terminal)
        textShadow?: string;
        // Ruled lines (Paper Notebook)
        ruledLines?: boolean;
        ruledLineColor?: string;
        // Chalk texture (Chalk Blackboard)
        chalkTexture?: boolean;
        chalkNoiseOpacity?: number;
        // LCD Bezel (embedded display effect)
        lcdBezel?: boolean;
        lcdBezelShadow?: string;       // inset shadow for depth
        lcdOuterFrameColor?: string;   // outer chassis frame color
        lcdOuterFrameWidth?: number;   // outer frame thickness
    };
    drawing?: DrawingThemeConfig;
}

// ═══════════════════════════════════════════════════════════
// Theme Definitions
// ═══════════════════════════════════════════════════════════

// ── 🍦 Ivory (existing theme, now formalized) ──
export const ivoryTheme: Theme = {
    name: "ivory",
    editor: {
        windowBg: "#F7F5F0",
        titleBarBg: "#EFECE5",
        titleBarBorder: "#DDD8CE",
        titleColor: "#6E6E6E",
        titleFont: "monospace",
        dotColors: ["#C0C0C0", "#C0C0C0", "#C0C0C0"],
        borderRadius: 12,
        showChrome: true,
    },
    canvas: {
        bg: "#F7F5F0",
        textColor: "#111111",
        cursorColor: "#2DA44E",
        activeLineBg: "#EDE9E0",
        ghostTextColor: "#9CA3AF",
        selectionColor: "rgba(59, 130, 246, 0.35)",
        imageLabelColor: "#666",
        imageCardBg: "rgba(0,0,0,0.06)",
        imageShadow: "0 2px 12px rgba(0,0,0,0.15)",
    },
    syntax: {
        keyword: "#7C3AED",
        type: "#0D9488",
        string: "#B45309",
        number: "#059669",
        comment: "#6B7280",
        tag: "#2563EB",
        attribute: "#0284C7",
        function: "#B45309",
        operator: "#374151",
        punctuation: "#6B7280",
        default: "#111111",
        command: "#2563EB",
        flag: "#B45309",
        heading: "#2563EB",
        bold: "#111111",
        link: "#0D9488",
        listMarker: "#B45309",
    },
    popup: {
        bg: "#FFFFFF",
        border: "1px solid #D0D7DE",
        shadow: "0 4px 16px rgba(0, 0, 0, 0.12)",
        borderRadius: 12,
        selectedBg: "rgba(45, 164, 78, 0.1)",
        selectedBorder: "#2DA44E",
        textColor: "#111111",
        secondaryColor: "#666",
        imeBg: "#F8F8F8",
        imeBorder: "1px solid #C8C8C8",
        imeShadow: "0 2px 12px rgba(0, 0, 0, 0.15)",
        imeSelectedBg: "#2DA44E",
        imeSelectedTextColor: "#FFFFFF",
        imeLabelColor: "#666",
    },
    outer: {
        bg: "#3a3a2a",
        backgroundImage: "background.png",
        bgBlur: 4,
        bgSaturation: 0.9,
    },
    font: {
        family: "", // will be set by font loader
        loadId: "JetBrainsMono",
        weight: "400",
        size: 26,
    },
    drawing: {
        stroke: "#374151",
        strokeWidth: 2.5,
        fill: "none",
        roughness: 2.5,
        labelColor: "#111111",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 28,
        arrowHeadSize: 18,
    },
};

// ── 🌙 Dark Editor (VS Code Dark+) ──
export const darkEditorTheme: Theme = {
    name: "dark-editor",
    editor: {
        windowBg: "#1E1E1E",
        titleBarBg: "#323233",
        titleBarBorder: "#1A1A1A",
        titleColor: "#8C8C8C",
        titleFont: "monospace",
        dotColors: ["#FF5F57", "#FEBC2E", "#28C840"], // classic macOS colored dots
        borderRadius: 12,
        showChrome: true,
    },
    canvas: {
        bg: "#1E1E1E",
        textColor: "#D4D4D4",
        cursorColor: "#AEAFAD",
        activeLineBg: "#264F78",
        ghostTextColor: "#5A5A5A",
        selectionColor: "rgba(38, 79, 120, 0.6)",
        imageLabelColor: "#8C8C8C",
        imageCardBg: "rgba(255,255,255,0.05)",
        imageShadow: "0 2px 12px rgba(0,0,0,0.4)",
    },
    syntax: {
        keyword: "#C586C0",
        type: "#4EC9B0",
        string: "#CE9178",
        number: "#B5CEA8",
        comment: "#6A9955",
        tag: "#569CD6",
        attribute: "#9CDCFE",
        function: "#DCDCAA",
        operator: "#D4D4D4",
        punctuation: "#808080",
        default: "#D4D4D4",
        command: "#569CD6",
        flag: "#CE9178",
        heading: "#569CD6",
        bold: "#D4D4D4",
        link: "#4EC9B0",
        listMarker: "#CE9178",
    },
    popup: {
        bg: "#252526",
        border: "1px solid #3C3C3C",
        shadow: "0 4px 16px rgba(0, 0, 0, 0.4)",
        borderRadius: 8,
        selectedBg: "rgba(4, 57, 94, 0.6)",
        selectedBorder: "#007ACC",
        textColor: "#D4D4D4",
        secondaryColor: "#8C8C8C",
        imeBg: "#2D2D2D",
        imeBorder: "1px solid #3C3C3C",
        imeShadow: "0 2px 12px rgba(0, 0, 0, 0.4)",
        imeSelectedBg: "#007ACC",
        imeSelectedTextColor: "#FFFFFF",
        imeLabelColor: "#8C8C8C",
    },
    outer: {
        bg: "#1a1a2e",
    },
    font: {
        family: "",
        loadId: "JetBrainsMono",
        weight: "400",
        size: 26,
    },
    drawing: {
        stroke: "#9CDCFE",
        strokeWidth: 2.5,
        fill: "none",
        roughness: 2.5,
        labelColor: "#D4D4D4",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 28,
        arrowHeadSize: 18,
    },
};

// ── 🪧 Chalk Blackboard ──
export const chalkBlackboardTheme: Theme = {
    name: "chalk-blackboard",
    editor: {
        windowBg: "#2D3A2E",
        titleBarBg: "#2D3A2E",
        titleBarBorder: "transparent",
        titleColor: "#8A9B8E",
        titleFont: "monospace",
        dotColors: ["transparent", "transparent", "transparent"],
        borderRadius: 4,
        showChrome: false,
        borderColor: "#3D4D3F",
        borderWidth: 2,
    },
    canvas: {
        bg: "#2D3A2E",
        textColor: "#E8E4D9",
        cursorColor: "#F5DEB3",
        cursorWidth: 3,
        activeLineBg: "rgba(255,255,255,0.04)",
        ghostTextColor: "rgba(232, 228, 217, 0.3)",
        selectionColor: "rgba(245, 222, 179, 0.2)",
        imageLabelColor: "#8A9B8E",
        imageCardBg: "rgba(255,255,255,0.04)",
        imageShadow: "0 2px 12px rgba(0,0,0,0.3)",
    },
    syntax: {
        keyword: "#E8B4B8",      // soft chalk pink
        type: "#A8D8EA",         // powder blue chalk
        string: "#F2D398",       // warm yellow chalk
        number: "#B8D4A3",       // sage green chalk
        comment: "#6B7D6E",      // faded chalk (barely visible)
        tag: "#A8CAE6",          // sky blue chalk
        attribute: "#B8CEDC",    // light blue chalk
        function: "#F2D398",     // yellow chalk (same as string for simplicity)
        operator: "#C8C0B4",     // gray chalk
        punctuation: "#8A9B8E",  // muted green chalk
        default: "#E8E4D9",      // chalk white
        command: "#A8CAE6",
        flag: "#F2D398",
        heading: "#A8CAE6",
        bold: "#E8E4D9",
        link: "#A8D8EA",
        listMarker: "#F2D398",
    },
    popup: {
        bg: "#354537",
        border: "1px solid #4D5D4F",
        shadow: "0 4px 16px rgba(0, 0, 0, 0.3)",
        borderRadius: 6,
        selectedBg: "rgba(245, 222, 179, 0.15)",
        selectedBorder: "#F5DEB3",
        textColor: "#E8E4D9",
        secondaryColor: "#8A9B8E",
        imeBg: "#354537",
        imeBorder: "1px solid #4D5D4F",
        imeShadow: "0 2px 12px rgba(0, 0, 0, 0.3)",
        imeSelectedBg: "#F5DEB3",
        imeSelectedTextColor: "#2D3A2E",
        imeLabelColor: "#8A9B8E",
    },
    outer: {
        bg: "#1B2721",
    },
    font: {
        family: "",
        loadId: "Caveat",
        weight: "400",
        size: 32, // handwritten fonts need to be larger
    },
    effects: {
        chalkTexture: true,
        chalkNoiseOpacity: 0.03,
    },
    drawing: {
        stroke: "#E8E4D9",
        strokeWidth: 3,
        fill: "none",
        roughness: 2.5,
        labelColor: "#F5DEB3",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 30,
        arrowHeadSize: 18,
    },
};

// ── 📝 Paper Notebook ──
export const paperNotebookTheme: Theme = {
    name: "paper-notebook",
    editor: {
        windowBg: "#FDF6E3",
        titleBarBg: "#FDF6E3",
        titleBarBorder: "transparent",
        titleColor: "#8B7D6B",
        titleFont: "monospace",
        dotColors: ["transparent", "transparent", "transparent"],
        borderRadius: 4,
        showChrome: false,
        borderColor: "#D5C9B1",
        borderWidth: 1,
    },
    canvas: {
        bg: "#FDF6E3",
        textColor: "#3C3836",
        cursorColor: "#4A90D9",
        activeLineBg: "#F5EDDA",
        ghostTextColor: "rgba(60, 56, 54, 0.25)",
        selectionColor: "rgba(74, 144, 217, 0.2)",
        imageLabelColor: "#8B7D6B",
        imageCardBg: "rgba(0,0,0,0.04)",
        imageShadow: "0 1px 8px rgba(0,0,0,0.1)",
    },
    syntax: {
        keyword: "#9D174D",      // burgundy
        type: "#5B7553",         // olive green
        string: "#92400E",       // sepia
        number: "#5B7553",       // olive
        comment: "#A89F91",      // warm gray (pencil-like)
        tag: "#4A64A4",          // ink blue
        attribute: "#6B8DAA",    // muted blue
        function: "#92400E",     // sepia
        operator: "#5C534A",     // dark brown-gray
        punctuation: "#A89F91",  // warm gray
        default: "#3C3836",      // dark warm gray
        command: "#4A64A4",
        flag: "#92400E",
        heading: "#4A64A4",
        bold: "#3C3836",
        link: "#5B7553",
        listMarker: "#92400E",
    },
    popup: {
        bg: "#FDF6E3",
        border: "1px solid #D5C9B1",
        shadow: "0 2px 12px rgba(139, 125, 107, 0.2)",
        borderRadius: 8,
        selectedBg: "rgba(74, 144, 217, 0.1)",
        selectedBorder: "#4A90D9",
        textColor: "#3C3836",
        secondaryColor: "#8B7D6B",
        imeBg: "#FDF6E3",
        imeBorder: "1px solid #D5C9B1",
        imeShadow: "0 2px 8px rgba(139, 125, 107, 0.2)",
        imeSelectedBg: "#4A90D9",
        imeSelectedTextColor: "#FFFFFF",
        imeLabelColor: "#8B7D6B",
    },
    outer: {
        bg: "#D4C5A9",
    },
    font: {
        family: "",
        loadId: "Kalam",
        weight: "400",
        size: 28, // handwritten fonts need to be slightly larger
    },
    effects: {
        ruledLines: true,
        ruledLineColor: "rgba(176, 160, 132, 0.3)",
    },
    drawing: {
        stroke: "#5C534A",
        strokeWidth: 2,
        fill: "none",
        roughness: 2.5,
        labelColor: "#3C3836",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 26,
        arrowHeadSize: 16,
    },
};

// ── 🖥️ Retro Terminal ──
export const retroTerminalTheme: Theme = {
    name: "retro-terminal",
    editor: {
        windowBg: "#0A0A0A",
        titleBarBg: "#0A0A0A",
        titleBarBorder: "transparent",
        titleColor: "#33FF33",
        titleFont: "monospace",
        dotColors: ["transparent", "transparent", "transparent"],
        borderRadius: 2,
        showChrome: false,
        borderColor: "#1A3A1A",
        borderWidth: 2,
    },
    canvas: {
        bg: "#0A0A0A",
        textColor: "#33FF33",
        cursorColor: "#33FF33",
        cursorWidth: 10,
        activeLineBg: "rgba(51,255,51,0.04)",
        ghostTextColor: "rgba(51,255,51,0.25)",
        selectionColor: "rgba(51,255,51,0.15)",
        imageLabelColor: "#1A8A1A",
        imageCardBg: "rgba(51,255,51,0.05)",
        imageShadow: "0 0 12px rgba(51,255,51,0.15)",
    },
    syntax: {
        keyword: "#55FF55",      // bright green
        type: "#33DDAA",         // teal-green
        string: "#FFAA33",       // amber
        number: "#55FF55",       // green
        comment: "#1A6B1A",      // dim green
        tag: "#33DDAA",          // teal-green
        attribute: "#44CC88",    // mid-green
        function: "#55FF55",     // bright green
        operator: "#33CC33",     // green
        punctuation: "#228822",  // muted green
        default: "#33FF33",      // phosphor green
        command: "#55FF55",
        flag: "#FFAA33",
        heading: "#55FF55",
        bold: "#55FF55",
        link: "#33DDAA",
        listMarker: "#FFAA33",
    },
    popup: {
        bg: "#0D1A0D",
        border: "1px solid #1A3A1A",
        shadow: "0 0 20px rgba(51,255,51,0.1)",
        borderRadius: 2,
        selectedBg: "rgba(51,255,51,0.1)",
        selectedBorder: "#33FF33",
        textColor: "#33FF33",
        secondaryColor: "#1A8A1A",
        imeBg: "#0D1A0D",
        imeBorder: "1px solid #1A3A1A",
        imeShadow: "0 0 12px rgba(51,255,51,0.1)",
        imeSelectedBg: "#33FF33",
        imeSelectedTextColor: "#0A0A0A",
        imeLabelColor: "#1A8A1A",
    },
    outer: {
        bg: "#000000",
    },
    font: {
        family: "",
        loadId: "",
        localFile: "GeistPixel-Square.woff2",
        localFamily: "GeistPixelSquare",
        weight: "400",
        size: 24,  // pixel font is visually larger, use slightly smaller
    },
    effects: {
        scanlines: true,
        scanlineColor: "rgba(0,0,0,0.15)",
        scanlineOpacity: 0.15,
        textShadow: "0 0 8px rgba(51,255,51,0.4)",
    },
    drawing: {
        stroke: "#33FF33",
        strokeWidth: 2,
        fill: "none",
        roughness: 1.5,
        labelColor: "#33FF33",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 24,
        arrowHeadSize: 16,
    },
};

// ── 🍎 macOS Spotlight ──
export const spotlightTheme: Theme = {
    name: "spotlight",
    editor: {
        windowBg: "rgba(255,255,255,0.82)",
        titleBarBg: "rgba(255,255,255,0.55)",
        titleBarBorder: "rgba(0,0,0,0.06)",
        titleColor: "#86868B",
        titleFont: "sans-serif",
        dotColors: ["#FF5F57", "#FEBC2E", "#28C840"],
        borderRadius: 20,
        showChrome: true,
        borderColor: "rgba(255,255,255,0.35)",
        borderWidth: 1,
    },
    canvas: {
        bg: "transparent",
        textColor: "#1D1D1F",
        cursorColor: "#007AFF",
        activeLineBg: "rgba(0,122,255,0.05)",
        ghostTextColor: "rgba(29, 29, 31, 0.25)",
        selectionColor: "rgba(0,122,255,0.15)",
        imageLabelColor: "#86868B",
        imageCardBg: "rgba(0,0,0,0.03)",
        imageShadow: "0 1px 6px rgba(0,0,0,0.08)",
    },
    syntax: {
        keyword: "#AD3DA4",      // Xcode purple
        type: "#3E8087",         // Xcode teal
        string: "#D12F1B",       // Xcode red
        number: "#1C00CF",       // Xcode blue-purple
        comment: "#5D6C79",      // Xcode gray
        tag: "#2F6EB3",          // Xcode blue
        attribute: "#4B8DA3",    // Xcode light blue
        function: "#326D74",     // Xcode dark teal
        operator: "#1D1D1F",     // dark gray
        punctuation: "#86868B",  // Apple secondary gray
        default: "#1D1D1F",
        command: "#2F6EB3",
        flag: "#D12F1B",
        heading: "#2F6EB3",
        bold: "#1D1D1F",
        link: "#3E8087",
        listMarker: "#D12F1B",
    },
    popup: {
        bg: "rgba(255,255,255,0.92)",
        border: "1px solid rgba(0,0,0,0.1)",
        shadow: "0 8px 32px rgba(0, 0, 0, 0.12)",
        borderRadius: 12,
        selectedBg: "rgba(0,122,255,0.08)",
        selectedBorder: "#007AFF",
        textColor: "#1D1D1F",
        secondaryColor: "#86868B",
        imeBg: "rgba(255,255,255,0.92)",
        imeBorder: "1px solid rgba(0,0,0,0.1)",
        imeShadow: "0 4px 20px rgba(0, 0, 0, 0.12)",
        imeSelectedBg: "#007AFF",
        imeSelectedTextColor: "#FFFFFF",
        imeLabelColor: "#86868B",
    },
    outer: {
        bg: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    },
    font: {
        family: "",
        loadId: "Inter",
        weight: "400",
        size: 24,
    },
    drawing: {
        stroke: "#1D1D1F",
        strokeWidth: 2.5,
        fill: "none",
        roughness: 2,
        labelColor: "#1D1D1F",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 26,
        arrowHeadSize: 18,
    },
};

// ── 📟 LCD Terminal (Teenage Engineering / Moment Ideas) ──
export const lcdTerminalTheme: Theme = {
    name: "lcd-terminal",
    editor: {
        windowBg: "#FFFFFF",
        titleBarBg: "#FFFFFF",
        titleBarBorder: "#000000",
        titleColor: "#1A1A1A",
        titleFont: "monospace",
        dotColors: ["transparent", "transparent", "transparent"],
        borderRadius: 0,  // hard industrial corners — no rounding
        showChrome: false,
        borderColor: "#000000",
        borderWidth: 2,
    },
    canvas: {
        bg: "#9EA792",            // retro LCD green (TE's lcdGreen)
        textColor: "#1A1A1A",     // dark primary text on LCD
        cursorColor: "#FF4D00",   // Action Orange cursor
        cursorWidth: 3,
        activeLineBg: "rgba(0,0,0,0.06)",
        ghostTextColor: "rgba(26,26,26,0.3)",
        selectionColor: "rgba(255,77,0,0.18)",  // orange tint
        imageLabelColor: "#4A4A4A",
        imageCardBg: "rgba(0,0,0,0.05)",
        imageShadow: "4px 4px 0px rgba(0,0,0,0.2)",  // hard block shadow
    },
    syntax: {
        keyword: "#8B4513",       // saddlebrown — warm, mechanical
        type: "#2E5E4E",          // deep teal-green (muted industrial)
        string: "#924000",        // burnt orange-brown
        number: "#1A6B1A",        // dark green (LCD digit color)
        comment: "#6B7D6E",       // muted LCD green-gray
        tag: "#2E5E4E",           // teal
        attribute: "#4A7A6A",     // medium teal
        function: "#924000",      // burnt orange
        operator: "#1A1A1A",      // pure dark
        punctuation: "#6B7D6E",   // muted green
        default: "#1A1A1A",       // dark primary
        command: "#2E5E4E",
        flag: "#924000",
        heading: "#FF4D00",       // Action Orange for headings
        bold: "#1A1A1A",
        link: "#2E5E4E",
        listMarker: "#FF4D00",
    },
    popup: {
        bg: "#FFFFFF",
        border: "2px solid #000000",
        shadow: "4px 4px 0px rgba(0,0,0,1)",  // hard block shadow (TE style)
        borderRadius: 0,
        selectedBg: "rgba(255,77,0,0.1)",
        selectedBorder: "#FF4D00",
        textColor: "#1A1A1A",
        secondaryColor: "#666666",
        imeBg: "#FFFFFF",
        imeBorder: "2px solid #000000",
        imeShadow: "4px 4px 0px rgba(0,0,0,1)",
        imeSelectedBg: "#FF4D00",
        imeSelectedTextColor: "#FFFFFF",
        imeLabelColor: "#666666",
    },
    outer: {
        bg: "linear-gradient(180deg, #D4D0C8 0%, #C8C4BC 30%, #BFBBB3 70%, #B8B4AC 100%)",
    },
    font: {
        family: "",
        loadId: "",
        localFile: "GeistPixel-Square.woff2",
        localFamily: "GeistPixelSquare",
        weight: "400",
        size: 24,
    },
    effects: {
        lcdBezel: true,
        lcdBezelShadow: "inset 0 3px 10px rgba(0,0,0,0.35), inset 0 1px 3px rgba(0,0,0,0.25), inset 0 -1px 2px rgba(255,255,255,0.1)",
        lcdOuterFrameColor: "#4A4842",
        lcdOuterFrameWidth: 14,
    },
    drawing: {
        stroke: "#1A1A1A",
        strokeWidth: 2.5,
        fill: "none",
        roughness: 2,
        labelColor: "#1A1A1A",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 24,
        arrowHeadSize: 16,
    },
};

// ── 🕹️ Pixel Art (arcade / 8-bit aesthetic) ──
export const pixelArtTheme: Theme = {
    name: "pixel-art",
    editor: {
        windowBg: "#0C0C1A",
        titleBarBg: "#0C0C1A",
        titleBarBorder: "transparent",
        titleColor: "#FF6EC7",
        titleFont: "monospace",
        dotColors: ["transparent", "transparent", "transparent"],
        borderRadius: 0,  // hard pixel edges — no rounding
        showChrome: false,
        borderColor: "#FF6EC7",
        borderWidth: 3,
    },
    canvas: {
        bg: "#0C0C1A",
        textColor: "#FFFFFF",
        cursorColor: "#00FFFF",
        cursorWidth: 12,  // chunky block cursor
        activeLineBg: "rgba(0,255,255,0.06)",
        ghostTextColor: "rgba(255,255,255,0.2)",
        selectionColor: "rgba(255,110,199,0.25)",
        imageLabelColor: "#FF6EC7",
        imageCardBg: "rgba(255,110,199,0.08)",
        imageShadow: "0 0 16px rgba(255,110,199,0.2)",
    },
    syntax: {
        keyword: "#FF6EC7",      // hot pink
        type: "#00FFFF",         // cyan
        string: "#FFD700",       // gold
        number: "#00FF7F",       // spring green
        comment: "#4A4A6A",      // dim purple-gray
        tag: "#00CCFF",          // electric blue
        attribute: "#B388FF",    // light purple
        function: "#FFD700",     // gold
        operator: "#FF6EC7",     // hot pink
        punctuation: "#6B6B8D",  // muted purple
        default: "#FFFFFF",      // white
        command: "#00CCFF",
        flag: "#FFD700",
        heading: "#FF6EC7",
        bold: "#FFFFFF",
        link: "#00FFFF",
        listMarker: "#FF6EC7",
    },
    popup: {
        bg: "#12122A",
        border: "2px solid #FF6EC7",
        shadow: "0 0 24px rgba(255,110,199,0.2)",
        borderRadius: 0,
        selectedBg: "rgba(0,255,255,0.12)",
        selectedBorder: "#00FFFF",
        textColor: "#FFFFFF",
        secondaryColor: "#8888AA",
        imeBg: "#12122A",
        imeBorder: "2px solid #FF6EC7",
        imeShadow: "0 0 16px rgba(255,110,199,0.15)",
        imeSelectedBg: "#FF6EC7",
        imeSelectedTextColor: "#0C0C1A",
        imeLabelColor: "#8888AA",
    },
    outer: {
        bg: "#030308",
    },
    font: {
        family: "",
        loadId: "",
        localFile: "GeistPixel-Circle.woff2",
        localFamily: "GeistPixelCircle",
        weight: "400",
        size: 24,
    },
    effects: {
        scanlines: true,
        scanlineColor: "rgba(255,110,199,0.06)",
        scanlineOpacity: 0.06,
        textShadow: "0 0 6px rgba(0,255,255,0.3), 0 0 20px rgba(255,110,199,0.15)",
    },
    drawing: {
        stroke: "#FF6EC7",
        strokeWidth: 3,
        fill: "none",
        roughness: 1.5,
        labelColor: "#00FFFF",
        labelFont: "Virgil, Segoe Print, Bradley Hand, casual, cursive",
        labelSize: 24,
        arrowHeadSize: 18,
    },
};

// ── Theme Registry ──
export const themes = {
    ivory: ivoryTheme,
    "dark-editor": darkEditorTheme,
    "chalk-blackboard": chalkBlackboardTheme,
    "paper-notebook": paperNotebookTheme,
    "retro-terminal": retroTerminalTheme,
    spotlight: spotlightTheme,
    "lcd-terminal": lcdTerminalTheme,
    "pixel-art": pixelArtTheme,
} as const;

export type ThemeName = keyof typeof themes;
