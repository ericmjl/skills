---
name: prompt-card
description: "Build a brief, interactive prompt card: a small card that teaches a reader one fill-in prompt, with numbered color-coded slots whose 'why it matters' notes pop up on hover, and an 'Interacts with' section naming the skill or AGENTS.md instructions the prompt relies on. Use when someone wants a prompt card for a prompt, agent skill, or workflow, to embed at the end of a blog post section, paste into an Obsidian note, or publish as a standalone HTML page. Triggers include 'make a prompt card', 'turn this prompt into a card', 'add a prompt card to this post', or 'show readers the prompt I use'."
license: MIT
---

# Prompt card

## Usage

Use this skill when someone wants to show readers a prompt they actually use, in a form readers can copy and understand. The card sits at the bottom of a blog section or inside a note, so it has to be brief: roughly 350 to 500px tall at 640px wide.

Ask for these when missing:

- The exact prompt, with its blanks.
- The skill or AGENTS.md instructions the prompt relies on, and where they live.
- Where the card goes: a blog post, an Obsidian note, or both.

## What the card contains

Keep to these parts, in this order, and nothing else:

1. **Header.** The card title, a small "prompt card" label, and the hint "Hover a highlight to see why it matters". The standalone version puts the Copy blank template button in the header and the hint just under the template.
2. **The template.** The prompt in a white box. The parts that matter most are numbered, color-coded slots: 1 blue, 2 green, 3 amber, and 4 slate only if you truly need a fourth. Three slots is the sweet spot.
3. **Why notes as popovers.** Each slot reveals its note on hover or keyboard focus. Don't add an always-visible list of notes. Put the same text in the slot's `title=` attribute as a fallback.
4. **Interacts with.** A slate section with no number badge. One or two sentences on the standing instructions the prompt relies on (an agent skill, or else an AGENTS.md instruction) and what they supply, followed by chips naming them. This is what explains why a short prompt works.
5. **Footer.** One line: label, version, date.

Leave out metadata tables, skill lists, intended use, worked examples, limitations, and next steps. If the post needs those, they belong in the prose around the card.

## Ground it before you write

- Read the real skill and AGENTS.md the prompt relies on before writing any why note or the Interacts with text. Describe what they actually tell the agent to do.
- Don't invent capabilities. If a note implies something the instructions don't say, reword it or flag it to the user.
- Never link a private repo. Name a private skill as plain text. Link public skills only after you've confirmed the folder exists.
- Report any gaps between what the blog post claims and what the instructions say, rather than smoothing them over on the card.

## Writing rules

- Plain, warm, direct. Write to the reader as "you".
- Each why note is one sentence, two at most: what the part does, and what goes wrong without it.
- No jargon or internal labels. No em-dashes. Sentence-case headings without colons.

## Styling

If the host site already has interactive widgets, match them. Read its widget CSS first and reuse its fonts, colors, borders, radius, and spacing. Otherwise use the default house style below, which comes from a set of standalone blog widgets:

- Monospace, a `#fafafa` card, a 1px `#ddd` border, 8px radius, `0 2px 8px rgba(0,0,0,0.06)` shadow, 640px max width, `#0066cc` accent.
- Slot palette: blue `#0066cc` on `#eef4ff`, green `#1a7a4b` on `#e7f6ee`, amber `#a05a0c` on `#fdf3e3`, slate `#475569` on `#eef1f4`.
- 12px minimum font everywhere. Check with `rg -n 'font-size' <file>`.

Whichever style you use:

- Scope all CSS under `.prompt-card` and prefix variables with `--pc-`, so the card can't collide with a page or vault theme. To restyle the card, change the variables.
- Popovers sit inside the card. Give the rightmost slot's popover `pc-pop-end` so it aligns right and stays inside the card edge.

The shared CSS lives in `assets/obsidian-snippet.css`. `assets/template.html` inlines the same rules.

## Two delivery targets

**Standalone blog widget.** Start from `assets/template.html`. It's self-contained, with inline `<style>` and `<script>` and no dependencies. The Copy blank template button copies the plain-text prompt from a hidden textarea. `fit()` resizes the iframe by setting its height to `0px` first and then to `scrollHeight`, and runs on load and resize. Embed it with a borderless iframe:

```html
<iframe src="prompt-card.html" width="100%" scrolling="no" style="border:0" onload="this.style.height=this.contentDocument.body.scrollHeight+'px'"></iframe>
```

**Obsidian note.** Obsidian doesn't render iframes to local files and strips scripts, so:

- Paste the markup from `assets/obsidian-note-snippet.html` straight into the note. Don't leave blank lines inside the block, because Markdown breaks out of HTML at a blank line. Don't include `<style>` or `<script>`.
- Append `assets/obsidian-snippet.css` to a vault CSS snippet that's already enabled (check `enabledCssSnippets` in `.obsidian/appearance.json`), or add a new snippet and enable it. Back the snippet file up first. Only add rules; don't change existing ones.
- `:hover`, `:focus`, and `:focus-within` reveal the popovers. Each popover also has an inline `style="display:none"` so it stays hidden if the snippet is off, and `title=` still shows the why text.
- Leave out the copy button. It needs a script.
- Edit the note by replacing the exact card block string only, and diff against a backup to confirm nothing else changed.

## Verify before you deliver

1. Render in headless Chromium or Playwright. For the Obsidian version, render the note markup with only the snippet CSS and no script.
2. Hover each slot, then focus one with the keyboard. Confirm the popover's computed `display` changes from `none` to `block`, and take a screenshot of each hover.
3. Check there are no console or page errors. A missing favicon from a local test server doesn't count.
4. Click Copy and read the clipboard back. Serve the file over `http://localhost` and grant clipboard permissions, because `file://` won't work.
5. Load the card in a same-origin iframe and confirm `fit()` set a height. A cross-origin host can't reach `frameElement`.
6. Check every file you wrote for em-dashes with `grep -nP '\x{2014}' <file>`.

Gotchas worth knowing:

- A CSS comment containing a path glob like `blog/*/x.html` ends the comment at `*/` and silently drops the next rule. If that's `:root`, every variable disappears.
- A shorthand `border: 1px solid` on a more specific selector overrides a per-color `border-color` class. Raise the color rule's specificity.
- A full-page screenshot is never shorter than the viewport. Use a short viewport, such as 672 by 300, to get the card's true height.

## Versioning

Before overwriting, save the previous file as `*.vN.html` (and its PNG). Bump the version in the footer.

## Files

- `assets/template.html`: standalone card with placeholders (CARD TITLE, WHY 1 to 3, INTERACTS, SKILL-NAME, footer date).
- `assets/obsidian-snippet.css`: the scoped card CSS for a vault snippet, including an optional slot 4.
- `assets/obsidian-note-snippet.html`: in-note markup with placeholders.
- `assets/examples/ingest-a-source/`: a filled-in card for "Ingest <url/file> into my <name of vault> please." Contains `standalone.html`, `in-note.html`, `obsidian-snippet.css`, and `hover.png`.
- `assets/examples/make-a-prompt-card/`: a filled-in card for "Make a prompt card for <your prompt> and <its skill> to go in my <blog post or note>." Contains `standalone.html`, `in-note.html`, `obsidian-snippet.css`, `default.png`, and `hover.png`.
