# 🎹 Typewriter Video

**VS Code-style typewriter animations with mechanical keyboard sounds** — an AI Agent Skill built on [Remotion](https://remotion.dev).

**VS Code 风格的打字机动画，配搭机械键盘音效** —— 基于 [Remotion](https://remotion.dev) 的 AI Agent Skill。

Text appears character-by-character with realistic typing rhythm, keyboard audio, visual effects, and 8 switchable themes.

文字逐字出现，配有真实打字节奏、键盘音效、视觉特效，支持 8 套可切换主题。

🔊 **Turn on sound for the full experience!** Keyboard sounds are half the magic.

🔊 **请打开声音！** 机械键盘音效是体验的一半。

https://github.com/user-attachments/assets/e2319d8e-36b2-43f9-aca2-5aa4d427adf5

👉 **See it in a real YouTube video · 看看实际 YouTube 视频中的效果：** [Watch on YouTube](https://www.youtube.com/watch?v=7276d60YTI4)

---

## 💡 Learn How to Use It · 免费学习空间

拥有这个 Skill 是一回事，但要运用它制作出节奏感极佳、令人满意爆表的影片，则是另一回事。

欢迎加入下面这个免费的学习空间，获取完整的 **自动打字机(板书)Skill** 教学视频。课程中详细展示了 **12 个核心“讲故事积木”（Building Blocks）** 的具体视觉效果和叙事运用手法，教你如何像导演一样进行场景编排：
- **四种打字速度**：如何用 burst 和 deliberate 速度来控制观众的情绪与节奏
- **鬼影文字 (Ghost Text)**：如何制造「我猜你在想什么」的预期感
- **删除线 (Strike Text)**：如何用退格符和选中删除来制造强烈的剧情反转
- **图片堆叠与文件切换**：如何利用视觉元素无缝完成话题与场景的转场
- （还包括中文拼音重音显示、动效复选框、手绘覆盖等全部 12 种排版组件的系统演示）

👉 [**免费加入空间获取课程**](https://member.pathunfold.com/join?invitation_token=8b9f3cfa9991545682f3123b04970a0875311e46-27313521-3b92-472f-ae3f-b970c03f532e)

---

## Features · 功能

| Feature · 功能 | Description · 说明 |
|---------|-------------|
| **4 typing speeds · 4 种打字速度** | burst、normal、deliberate、thinking — 控制节奏与叙事 |
| **Ghost text · 幽灵补全** | 灰色自动补全预览 → Tab 接受 |
| **Strike-correct · 删除重打** | 先打错字，停顿，删除，再打正确的 — "重新思考"效果 |
| **Emoji picker · 表情选择器** | 动画搜索面板 + 表情目录 |
| **File switching · 文件切换** | 多文件编辑器标签栏切换 |
| **Syntax highlighting · 语法高亮** | VS Code Dark+ 配色（TSX、TypeScript、JavaScript、Bash、Markdown、CSS） |
| **Chinese IME · 中文输入法** | 拼音模式 + 直接吐字模式 |
| **Inline images · 内嵌图片** | 单图 / 多图行，支持 fade、slide-up、scale 动画 |
| **Image stack · 图片堆叠** | 纸堆翻页渐现效果 |
| **Animated checkboxes · 动画复选框** | `[ ]` → `[✓]` 弹簧动画 |
| **Excalidraw diagrams · 手绘图表** 🧪 Beta | rough.js 手绘风格，笔画动画（开发中 · in development） |
| **16:9 + 9:16 · 横屏 + 竖屏** | Landscape (YouTube) and Portrait (Shorts/Reels/TikTok) layout presets · 横屏和竖屏预设 |
| **A-roll sync · 画外音同步** | `delayFrames` 逐帧对齐旁白音频 |

## Themes · 主题

8 套视觉风格 — 通过 `theme` 属性切换：

**Ivory 象牙** · **Dark Editor 暗色编辑器** · **Chalk Blackboard 粉笔黑板** · **Paper Notebook 纸质笔记本** · **Retro Terminal 复古终端** · **macOS Spotlight 聚光灯** · **LCD Terminal 液晶终端** · **Pixel Art 像素风**

## Sound Packs · 音效包

4 套机械键盘音效 — 通过 `soundPack` 属性切换：

| Pack · 音效包 | Feel · 手感 |
|------|------|
| `nk-cream`（默认） | Smooth linear · 顺滑线性 |
| `holy-pandas` | Tactile bump · 段落触感 |
| `cream-travel` | Creamy full travel · 奶油长行程 |
| `turquoise` | Tealio-style linear · Tealio 风格线性 |

## Installation · 安装

Copy this repo URL and tell your AI agent:

复制本仓库链接，告诉你的 AI Agent：

> **"Please install this skill: `https://github.com/yammaku/typewriter-video`"**

That's it. Your agent will clone the repo, read `SKILL.md`, and know how to use it.

就这么简单。Agent 会自动克隆仓库、阅读 `SKILL.md`，然后就知道怎么用了。

## Documentation · 文档

| Doc · 文档 | Content · 内容 |
|-----|----------------|
| [**SKILL.md**](SKILL.md) | Full setup guide (8 steps) · 完整搭建指南（8 步） |
| [API Reference · API 参考](references/API.md) | TextSegment fields, timeline events, constants · 字段、时间线事件、常量 |
| [Content Guide · 内容指南](references/content-guide.md) | Storytelling techniques, rhythm · 叙事技巧、节奏控制 |
| [Audio Guide · 音频指南](references/audio.md) | Sound system, startFrame gotcha · 音效系统、startFrame 陷阱 |
| [A-Roll Sync · 画外音同步](references/aroll-sync.md) | B-roll choreography, timing budget · B-roll 编排、时间预算 |

## What is an Agent Skill? · 什么是 Agent Skill？

This repo is packaged as an **Agent Skill** — a structured knowledge bundle that AI coding agents (Antigravity, Claude Code, Gemini CLI, Codex, Cursor, etc.) can install and use autonomously. The agent reads `SKILL.md`, copies the template, writes content, and renders video — all without human intervention.

本仓库打包为 **Agent Skill** — 一种结构化的知识包，AI 编程 Agent（Antigravity、Claude Code、Gemini CLI、Codex、Cursor 等）可以自主安装和使用。Agent 读取 `SKILL.md`，复制模板，编写内容，渲染视频 — 全程无需人工干预。

Learn more · 了解更多：[agentskills.io](https://agentskills.io)

## Roadmap · 路线图

| # | Feature · 功能 | Description · 说明 |
|---|---------|-------------|
| 1 | **🧪 Excalidraw — Hand-drawn Diagrams · 手绘图表** | Complete the Excalidraw drawing layer: stroke animation, hachure fills, label positioning, and storytelling integration with the typewriter timeline. 完善手绘图层：笔画动画、填充、标签定位，与打字机时间线深度整合。 |
| 2 | **🎥 Auto Camera · 智能运镜** | Intelligent auto-zoom that dynamically pans and zooms to highlight key moments, guiding viewer attention across the canvas. 智能自动缩放运镜，动态聚焦关键内容，引导观众注意力。 |
| 3 | **✂️ Auto Editing · 全自动剪辑** | End-to-end production pipeline: feed in a talking-head A-roll video → AI generates synced typewriter B-roll → auto-composes both layers with dynamic camera, real-time layout adaptation (picture-in-picture, split-screen), responsive to both landscape and portrait. 端到端制作流水线：输入 talking head A-roll → AI 自动生成同步的打字机 B-roll → 自动合成画中画/分屏，实时调整大小和位置，支持横竖屏。 |

## Tech Stack · 技术栈

- [Remotion](https://remotion.dev) — React-based video rendering · 基于 React 的视频渲染
- [rough.js](https://roughjs.com) — Hand-drawn diagram rendering · 手绘风格图表渲染
- TypeScript

## License · 许可证

MIT
