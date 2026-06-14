// ═══════════════════════════════════════════════════════════
// Lightweight regex-based syntax highlighter for Remotion.
//
// No external deps (no Prism/Shiki) — keeps bundle tiny.
// Returns colored spans for a given line of text.
// Accepts an optional SyntaxColors palette from the theme system.
// ═══════════════════════════════════════════════════════════

import type { SyntaxColors } from "./themes";

export type SyntaxLanguage = "tsx" | "ts" | "javascript" | "bash" | "markdown" | "css";

export interface ColoredSpan {
    text: string;
    color: string; // CSS color value
}

// ── Default VS Code Dark+ inspired palette ──
const DEFAULT_COLORS: SyntaxColors = {
    keyword: "#C586C0",     // purple-pink (if, const, return, export, etc.)
    type: "#4EC9B0",        // teal (React.FC, string, number, etc.)
    string: "#CE9178",      // warm orange (strings)
    number: "#B5CEA8",      // green (numbers)
    comment: "#6A9955",     // muted green (comments)
    tag: "#569CD6",         // blue (JSX/HTML tags)
    attribute: "#9CDCFE",   // light blue (JSX attributes)
    function: "#DCDCAA",    // yellow (function names)
    operator: "#D4D4D4",    // light gray (=, +, etc.)
    punctuation: "#808080", // gray (brackets, parens)
    default: "#D4D4D4",     // light gray (plain text)
    // Bash-specific
    command: "#569CD6",     // blue (commands)
    flag: "#CE9178",        // orange (flags like --force)
    // Markdown-specific
    heading: "#569CD6",     // blue (# headers)
    bold: "#D4D4D4",        // white (bold text)
    link: "#4EC9B0",        // teal (links)
    listMarker: "#CE9178",  // orange (- [ ] etc)
};

// ── Token patterns per language ──
interface TokenRule {
    pattern: RegExp;
    color: string;
}

const JS_KEYWORDS = [
    "const", "let", "var", "function", "return", "if", "else", "for", "while",
    "do", "switch", "case", "break", "continue", "new", "delete", "typeof",
    "instanceof", "in", "of", "class", "extends", "super", "this",
    "import", "export", "default", "from", "as", "async", "await",
    "try", "catch", "finally", "throw", "yield", "void", "null",
    "undefined", "true", "false", "static", "get", "set",
];

const TS_KEYWORDS = [
    ...JS_KEYWORDS,
    "type", "interface", "enum", "namespace", "declare", "readonly",
    "abstract", "implements", "private", "protected", "public",
    "keyof", "infer", "extends", "satisfies",
];

function buildRules(language: SyntaxLanguage, COLORS: SyntaxColors = DEFAULT_COLORS): TokenRule[] {
    switch (language) {
        case "tsx":
        case "ts":
        case "javascript": {
            const keywords = language === "javascript" ? JS_KEYWORDS : TS_KEYWORDS;
            const kwPattern = new RegExp(`\\b(${keywords.join("|")})\\b`);
            return [
                // Comments (// ...)
                { pattern: /\/\/.*$/, color: COLORS.comment },
                // Strings (single, double, backtick)
                { pattern: /'(?:[^'\\]|\\.)*'/, color: COLORS.string },
                { pattern: /"(?:[^"\\]|\\.)*"/, color: COLORS.string },
                { pattern: /`(?:[^`\\]|\\.)*`/, color: COLORS.string },
                // JSX tags: <Component or </div>
                { pattern: /<\/?[A-Za-z][A-Za-z0-9.]*/, color: COLORS.tag },
                // Closing tag bracket
                { pattern: /\/>/, color: COLORS.tag },
                // Type annotations after : (simplified)
                { pattern: /:\s*[A-Z][A-Za-z0-9<>[\], |]*/, color: COLORS.type },
                // Numbers
                { pattern: /\b\d+\.?\d*\b/, color: COLORS.number },
                // Keywords
                { pattern: kwPattern, color: COLORS.keyword },
                // Function calls: word followed by (
                { pattern: /\b[a-z][a-zA-Z0-9]*(?=\()/, color: COLORS.function },
                // JSX attributes: word=
                { pattern: /\b[a-z][a-zA-Z0-9]*(?==)/, color: COLORS.attribute },
            ];
        }

        case "bash": {
            return [
                // Comments
                { pattern: /#.*$/, color: COLORS.comment },
                // Strings
                { pattern: /'(?:[^'\\]|\\.)*'/, color: COLORS.string },
                { pattern: /"(?:[^"\\]|\\.)*"/, color: COLORS.string },
                // Flags (--flag or -f)
                { pattern: /\s--?[a-zA-Z][\w-]*/, color: COLORS.flag },
                // Commands (first word on line or after pipe/&&)
                { pattern: /^[a-z][\w.-]*/, color: COLORS.command },
                { pattern: /(?<=\|\s*)[a-z][\w.-]*/, color: COLORS.command },
                // Variables ($VAR)
                { pattern: /\$[A-Za-z_]\w*/, color: COLORS.attribute },
                // Numbers
                { pattern: /\b\d+\b/, color: COLORS.number },
            ];
        }

        case "markdown": {
            return [
                // Headings (# ...)
                { pattern: /^#{1,6}\s.*$/, color: COLORS.heading },
                // Bold (**text**)
                { pattern: /\*\*[^*]+\*\*/, color: COLORS.bold },
                // Links [text](url)
                { pattern: /\[([^\]]+)\]\([^)]+\)/, color: COLORS.link },
                // Inline code `code`
                { pattern: /`[^`]+`/, color: COLORS.string },
                // List markers (- [ ] or - [x])
                { pattern: /^-\s\[[ x]\]/, color: COLORS.listMarker },
                // Unordered list marker
                { pattern: /^-\s/, color: COLORS.listMarker },
            ];
        }

        case "css": {
            return [
                // Comments
                { pattern: /\/\*[\s\S]*?\*\//, color: COLORS.comment },
                // Strings
                { pattern: /'(?:[^'\\]|\\.)*'/, color: COLORS.string },
                { pattern: /"(?:[^"\\]|\\.)*"/, color: COLORS.string },
                // Properties
                { pattern: /[\w-]+(?=\s*:)/, color: COLORS.attribute },
                // Values with units
                { pattern: /\b\d+\.?\d*(px|em|rem|%|vh|vw|s|ms)\b/, color: COLORS.number },
                // Colors (#hex)
                { pattern: /#[0-9a-fA-F]{3,8}\b/, color: COLORS.number },
                // Selectors (simplified)
                { pattern: /\.[a-zA-Z][\w-]*/, color: COLORS.type },
                { pattern: /#[a-zA-Z][\w-]*/, color: COLORS.type },
            ];
        }

        default:
            return [];
    }
}

/**
 * Tokenize a single line of text into colored spans.
 * Returns an array of spans that, concatenated, reproduce the original line.
 */
export function tokenizeLine(line: string, language: SyntaxLanguage, syntaxColors?: SyntaxColors): ColoredSpan[] {
    const colors = syntaxColors ?? DEFAULT_COLORS;
    const rules = buildRules(language, colors);
    if (rules.length === 0) {
        return [{ text: line, color: colors.default }];
    }

    const spans: ColoredSpan[] = [];
    let remaining = line;
    let pos = 0;

    while (remaining.length > 0) {
        let earliestMatch: { index: number; length: number; color: string } | null = null;

        for (const rule of rules) {
            const match = remaining.match(rule.pattern);
            if (match && match.index !== undefined) {
                if (!earliestMatch || match.index < earliestMatch.index) {
                    earliestMatch = {
                        index: match.index,
                        length: match[0].length,
                        color: rule.color,
                    };
                }
            }
        }

        if (earliestMatch && earliestMatch.index >= 0) {
            // Add unmatched text before the match as default
            if (earliestMatch.index > 0) {
                spans.push({
                    text: remaining.slice(0, earliestMatch.index),
                    color: colors.default,
                });
            }
            // Add the matched token
            spans.push({
                text: remaining.slice(earliestMatch.index, earliestMatch.index + earliestMatch.length),
                color: earliestMatch.color,
            });
            remaining = remaining.slice(earliestMatch.index + earliestMatch.length);
            pos += earliestMatch.index + earliestMatch.length;
        } else {
            // No more matches — rest is default
            spans.push({ text: remaining, color: colors.default });
            break;
        }
    }

    return spans;
}

/**
 * Apply syntax highlighting to a string of text, returning per-character colors.
 * This is designed for the typewriter rendering where we need to color individual characters.
 */
export function highlightText(text: string, language: SyntaxLanguage, syntaxColors?: SyntaxColors): string[] {
    const lines = text.split("\n");
    const colors: string[] = [];

    for (let i = 0; i < lines.length; i++) {
        const spans = tokenizeLine(lines[i], language, syntaxColors);
        for (const span of spans) {
            for (const char of span.text) {
                colors.push(span.color);
            }
        }
        // Add color for the newline character (except last line)
        if (i < lines.length - 1) {
            colors.push((syntaxColors ?? DEFAULT_COLORS).default);
        }
    }

    return colors;
}
