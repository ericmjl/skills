import React from "react";
import {
    AbsoluteFill,
    Img,
    staticFile,
} from "remotion";
import { EditorWindow } from "./EditorWindow";
import { TypewriterText, TextSegment } from "./TypewriterText";

// ═══════════════════════════════════════════════════════════════
// CHINESE FEATURE DEMO — 全中文功能验证
//
// 两种中文打字模式的对比演示：
//   「吐字模式」— 汉字直接出现，像英文字母一样（默认）
//   「IME 模式」— 拼音→候选→选字，展示打字过程
//
// 验证功能：
//   1. 吐字 vs IME 对比
//   2. 打字速度 — burst / normal / deliberate / thinking
//   3. 联想输入 — Ghost text 自动补全
//   4. 删除纠正 — Strike & Correct
//   5. 表情符号 — Emoji Picker
//   6. 文件切换 + 代码高亮 + 光标跳转
//   7. 总结确认
// ═══════════════════════════════════════════════════════════════

const TEXT_SEGMENTS: TextSegment[] = [

    // ─────────────────────────────────────────────────
    // CHAPTER 1: 吐字 vs IME 模式对比
    // Title uses IME to show the pinyin process
    // Body uses direct mode for clean flow
    // ─────────────────────────────────────────────────
    { text: "# ", mode: "burst", file: "笔记.md", language: "markdown" },
    { text: "中文打字机", mode: "normal", imeInput: true },
    { text: "\n\n", mode: "burst" },

    // Direct mode (吐字): clean, fast, no pinyin
    { text: "这是吐字模式，汉字直接出现。\n", mode: "burst" },

    // IME mode: show the pinyin process
    { text: "这是拼音模式", mode: "normal", imeInput: true },
    { text: "，", mode: "burst" },
    { text: "有候选框。\n\n", mode: "normal", imeInput: true },

    // ─────────────────────────────────────────────────
    // CHAPTER 2: 打字速度
    // 四种速度对比 — mix direct and IME
    // ─────────────────────────────────────────────────
    { text: "## 速度对比\n\n", mode: "burst" },

    // burst: 快
    { text: "快速打字可以很快完成整句话。\n", mode: "burst", imeInput: true },

    // normal: 正常
    { text: "正常速度适合内容展示。\n", mode: "normal", imeInput: true },

    // deliberate: 慢, only key word uses IME
    { text: "这个词很", mode: "burst" },
    { text: "重要", mode: "deliberate", imeInput: true },
    { text: "。\n", mode: "burst" },

    // thinking: long pause then type
    { text: "想了很久才写出来。\n\n", mode: "thinking", imeInput: true },

    // ─────────────────────────────────────────────────
    // CHAPTER 3: 联想输入 (Ghost Text)
    // ─────────────────────────────────────────────────
    { text: "## 联想输入\n\n", mode: "burst" },
    {
        text: "人工智能", mode: "normal", imeInput: true,
        ghostText: "正在改变世界。",
        ghostPauseFrames: 35,
    },
    { text: "\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 4: 删除纠正 (Strike & Correct)
    // ─────────────────────────────────────────────────
    { text: "## 删改纠正\n\n", mode: "burst" },

    // Select-delete: type wrong, fix with Chinese
    { text: "这个工具", mode: "burst" },
    {
        text: "非常好用", mode: "normal", imeInput: true,
        strikeText: "just okay",
        strikeDelete: "select",
    },
    { text: "！\n", mode: "burst" },

    // Backspace: type wrong pinyin, fix
    { text: "我要写的是", mode: "burst" },
    {
        text: "代码", mode: "normal", imeInput: true,
        strikeText: "codd",
        strikeDelete: "backspace",
        strikePauseFrames: 15,
    },
    { text: "。\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 5: 表情符号 (Emoji Picker)
    // ─────────────────────────────────────────────────
    { text: "## 表情符号\n\n", mode: "burst" },
    { text: "完成任务 ", mode: "burst" },
    {
        text: "🎉",
        mode: "normal",
        emojiPicker: true,
        emojiPickerFrames: 22,
    },
    { text: " 开心 ", mode: "burst" },
    {
        text: "😊",
        mode: "normal",
        emojiPicker: true,
        emojiPickerFrames: 18,
    },
    { text: "\n\n", mode: "burst" },

    // ─────────────────────────────────────────────────
    // CHAPTER 6: 文件切换 + 代码高亮 + 光标跳转
    // ─────────────────────────────────────────────────
    { text: "// 主页组件\n", mode: "burst", file: "app/page.tsx", language: "tsx" },
    { text: "import React from 'react'\n\n", mode: "burst" },
    {
        text: "export default function ", mode: "burst",
        ghostText: "Page() {", ghostPauseFrames: 20,
    },
    { text: "\n  return (\n", mode: "burst" },
    { text: "    <div>\n", mode: "burst" },
    { text: "      <h1>", mode: "burst" },
    { text: "你好世界", mode: "deliberate", imeInput: true },
    { text: "</h1>\n", mode: "burst" },
    {
        text: "    </div>", mode: "burst",
        ghostText: "\n  );\n}", ghostPauseFrames: 18,
    },

    // Cursor jump: insert 'use client'
    {
        text: "'use client'\n", mode: "thinking",
        insertAt: { line: 0, col: 0 },
    },

    // ─────────────────────────────────────────────────
    // FINALE: 功能清单 (direct mode for clean checklist)
    // ─────────────────────────────────────────────────
    { text: "\n## 功能验证\n\n", mode: "burst", file: "笔记.md" },
    { text: "- [x] 吐字模式\n", mode: "burst" },
    { text: "- [x] 拼音模式\n", mode: "burst" },
    { text: "- [x] 速度对比\n", mode: "burst" },
    { text: "- [x] 联想补全\n", mode: "burst" },
    { text: "- [x] 删改纠正\n", mode: "burst" },
    { text: "- [x] 表情符号\n", mode: "burst" },
    { text: "- [x] 代码高亮\n", mode: "burst" },
    { text: "- [x] 光标跳转\n", mode: "burst" },
    { text: "\n全部通过 ", mode: "burst" },
    {
        text: "✅",
        mode: "normal",
        emojiPicker: true,
        emojiPickerFrames: 12,
    },
];

export const ChineseDemo: React.FC = () => {
    const [currentFile, setCurrentFile] = React.useState("笔记.md");

    return (
        <AbsoluteFill
            style={{
                backgroundColor: "#3a3a2a",
            }}
        >
            <Img
                src={staticFile("background.png")}
                style={{
                    position: "absolute",
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    filter: "blur(4px) saturate(0.9)",
                    transform: "scale(1.05)",
                }}
            />

            <AbsoluteFill
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                }}
            >
                <EditorWindow title={currentFile}>
                    <TypewriterText
                        segments={TEXT_SEGMENTS}
                        startFrame={15}
                        onFileChange={setCurrentFile}
                    />
                </EditorWindow>
            </AbsoluteFill>
        </AbsoluteFill>
    );
};
