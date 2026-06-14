# Content Writing Guide — Storytelling Techniques

> The typewriter is a **storytelling medium**. The typing behavior IS the performance. Every segment transition is a beat, every pause is dramatic tension. When writing content, think like a filmmaker, not a writer.

## Mindset: Think Visually

Before writing ANY segment, close your eyes and visualize the screen:

- The **speaker's face** is in a small corner (picture-in-picture)
- The **typewriter** occupies most of the frame
- The viewer is **reading** what's on screen while **hearing** the narration

**The cardinal rule:** Screen text must be a simplified echo of the narration — never a different sentence that happens to mean the same thing. If the viewer reads one thing while hearing another, their brain short-circuits. A teacher at a blackboard writes what they're *saying*, not a paraphrase.

✅ Speaker says "AI正在制造一场巨大的财富转移" → Board types "AI 正在制造一场巨大的财富转移"
✅ Speaker says "看明白的人已经在跑一场排位赛了" → Board types "排位赛" (simplified)
❌ Speaker says "因为我真的同意他" → Board types "赶在 AGI 到来之前站好位置" (different words — viewer confused)

## When to Use Each Technique

| Technique | Feeling | Best for |
|:----------|:--------|:---------|
| `deliberate` mode | Weight, gravity | Key words, punchlines |
| `thinking` pause | Suspense, anticipation | Before surprising statements |
| Strike + backspace | Intimate, hesitant | Small word swaps ("good" → "great") |
| Strike + select | Decisive, dramatic | Meaning reversals, big narrative turns |
| Ghost text | Predictability, inevitability | Rhetorical questions, audience reactions, callbacks |
| IME burst (`imePauseFrames: 8`) | Punchy emphasis | 1-4 char keywords — one per chapter |
| Emoji | Personality, punctuation | Emotional beats (🔥, 😤, 💡) |
| File switch | Context shifts | Moving from concept/README to code |
| Cursor jump (`insertAt`) | Live editing, afterthoughts | Injecting code, cheeky disclaimers, late-arriving caveats (see below) |
| Image / Image Stack | Visual evidence | Screenshots, thumbnails, rapid-fire news |
| Animated checkbox | Completion, satisfaction | Summaries, progress lists, feature checklists |

## Strike Text Philosophy — The Most Powerful Tool

The deleted text is NOT throwaway — it carries meaning. **Both the original phrase (with strikeText) and the final phrase (after replacement) must independently make sense.** The deletion is the narrative turn.

✅ **Correct — meaning shifts through deletion:**

```tsx
// "It's not just code" → select-delete "not just code" → "It's storytelling."
// Reader sees: "It's not just code" → thinks it's dismissive → then the flip
{ text: "It's ", mode: "burst" },
{
    text: "storytelling",
    strikeText: "not just code",
    strikeDelete: "select",     // dramatic sweep
    strikePauseFrames: 15,
    mode: "deliberate",
},
```

```tsx
// "A good illusion" → backspace "good" → "A beautiful illusion"
// Reader sees: settling for "good" → reconsider → upgrade to "beautiful"
{ text: "A ", mode: "thinking" },
{
    text: "beautiful",
    strikeText: "good",
    mode: "deliberate",         // defaults to backspace
},
{ text: " illusion.", mode: "burst" },
```

❌ **Wrong — grammar breaks or meaning doesn't shift:**

```tsx
// "It's not just code" → delete "just code" → "It's not storytelling"
// ❌ "It's not storytelling" is the OPPOSITE of the intended message!
{ text: "It's not ", mode: "burst" },
{ text: "storytelling", strikeText: "just code", ... },
```

**The rule**: Read the sentence WITH strikeText. Then read it with the replacement. Both must make sense, and the shift between them should feel like a revelation or reconsideration.


## Ghost Text as Storytelling

Ghost text = **"so predictable even the editor autocompletes it."** Type 2-3 opening characters, then the rest appears as gray autocomplete. Best for:
- Audience pushback: `{ text: "又来", ghostText: "制造焦虑了？" }`
- Rhetorical questions: `{ text: "谁不", ghostText: "想？" }`
- Inevitable conclusions: `{ text: "人的", ghostText: "价值在哪儿？" }`

## Strategic IME Placement

Use 1 IME word per chapter as the thematic anchor — max 4 chars, prefer 1-2. Always use `mode: "burst", imeInput: true, imePauseFrames: 8` for speed. The IME slows just enough to make the viewer feel the weight without breaking flow.

## Rhythm and Pacing

- **Vary speed constantly**: fast burst → slow deliberate → thinking pause → fast again
- **Short paragraphs** (2–3 sentences max). Leave whitespace (`\n\n`) for dramatic beats.
- **Hook the FIRST line** — no "Hello, today I will discuss..."
- **End with impact** — the last segment should land hard (deliberate mode + emoji)
- **Strike text is a climax** — use it 1–2 times per video, not in every paragraph

## Insertable Disclaimer — The "Oh Wait" Pattern

Use `insertAt` + IME to create a moment where the typewriter "goes back" and adds a caveat — as if the writer realized they should add a disclaimer. This creates a cheeky, human storytelling beat.

```tsx
// Title already typed: "# AI 时代投资的四个维度"
// Now jump back and insert a disclaimer after the title
{
    text: "（非投资建议）",
    mode: "burst",
    imeInput: true,
    imePauseFrames: 8,
    insertAt: { line: 0, col: 14 },   // after the heading text
    delayFrames: s(59.5 - OFFSET),     // after the 4 previews burst out
}
```

The key: the insert happens AFTER the main content is already established. It feels like an afterthought — intimate, self-aware, human.
