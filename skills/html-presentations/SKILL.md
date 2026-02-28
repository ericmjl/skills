---
name: html-presentations
description: Create single-file HTML slide presentations with vanilla JS/CSS. Themed (terminal.css, catppuccin, nord), keyboard-navigable, with inline SVG diagrams and animations. Use when the user asks for an HTML presentation, slide deck, or single-file slides without a framework.
license: MIT
---

# HTML Presentations

Create self-contained HTML slide presentations. No frameworks, no CDN, no build step — one `.html` file you can open in any browser.

## Usage

Use this skill when the user asks for a presentation, slide deck, or slides and wants a single HTML file with vanilla HTML, CSS, and JavaScript. Not for reveal.js or framework-based presentations. **Before generating slides**, ask about goals, audience, and delivery mode (Step 0); use the answers to shape length, emphasis, and content density.

## Requirements

None. Output is a single `.html` file. Works in any modern browser (Chrome, Firefox, Safari, Edge).

## What It Does

1. **Single file** — All CSS, JS, SVG diagrams, and content in one `.html` file
2. **Themed** — Three color presets: terminal.css (default), catppuccin, nord
3. **Keyboard navigation** — Space/Right/k forward, Shift+Space/Left/j backward; **Escape** opens a visual grid of all slides to jump to any slide
4. **SVG diagrams** — Flowcharts, architecture diagrams, pipelines, comparisons — all themed via CSS custom properties
5. **SVG animations** — Path drawing, sequential fade-in, pulse/glow, flow — triggered when a slide becomes active

## How It Works

**Example to study first:** read [assets/example-agent-skills-overview.html](assets/example-agent-skills-overview.html) — a complete, polished presentation that demonstrates the spotlight layout, two-column grids, rich SVG diagrams, pill badges, progress nav, and overview grid. Use it as a quality benchmark when generating new presentations.

### Step 0: Ask the user (before building)

**Do not generate slides until you have clarified the following with the user.** Ask conversationally; one or two questions per message is fine. Use answers to decide length, emphasis, and how much text vs. diagrams to use.

**(a) Goals of the presentation**

If the user hasn't stated a clear goal, offer choices so they can pick or mix:

- **Pitch / persuade** — convince the audience of an idea, product, or decision
- **Explain / teach** — convey a concept, process, or system so the audience understands
- **Update / status** — share progress, results, or findings (e.g. project update, experiment results)
- **Reference / handout** — something to keep and skim later; dense but scannable
- **Overview / roadmap** — high-level structure or plan; minimal detail, big picture
- **Other** — let them describe

**(b) Intended audience**

Ask who will see it (e.g. executives, engineers, clients, students, general public). This drives jargon level, depth, and what to spell out vs. assume.

**(c) Delivery mode**

- **With a speaker** — slides support the talk; less text per slide, more visuals; speaker fills in. Favor short bullets and diagrams.
- **Kiosk-style (no speaker)** — audience reads alone; slides must stand on their own. More explanatory text, clearer labels, possibly more slides or denser content.

**(d) Other useful questions**

- **Rough length** — "A few minutes?" / "10–15?" / "Deep dive?" — to calibrate slide count and detail.
- **Must-haves and skip** — "Anything that must be included or that we should skip?"
- **Tone** — formal vs. casual, serious vs. light, if it affects wording or design.

Record the user's answers and use them when choosing theme, building the outline, and deciding how much to put on each slide.

### Step 1: Pick a theme

Read one of the theme reference files and paste its CSS into the presentation's `<style>` block. **Default to catppuccin** unless the user requests otherwise.

| Theme | File | Aesthetic |
|-------|------|-----------|
| terminal.css | [references/theme-terminal.css](references/theme-terminal.css) | Green phosphor on black, monospace, scanlines |
| catppuccin | [references/theme-catppuccin.css](references/theme-catppuccin.css) | Pastel accents on warm dark base (Mocha variant) |
| nord | [references/theme-nord.css](references/theme-nord.css) | Arctic blue-gray, muted palette |

All themes define the same CSS custom properties (`--bg`, `--fg`, `--accent`, etc.), so the base layout CSS and all diagrams work with any theme.

### Step 2: Generate the HTML file

Use this skeleton. The three sections — **theme CSS**, **base layout CSS**, and **navigation JS** — are always the same structure; only slide content varies.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PRESENTATION_TITLE</title>
  <style>
    /* ===== Theme (paste from reference file) ===== */
    :root { /* ... theme variables ... */ }

    /* ===== Base layout ===== */
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; overflow: hidden; }
    body {
      background: var(--bg);
      color: var(--fg);
      font-family: var(--body-font);
    }
    .deck { position: relative; width: 100vw; height: 100vh; overflow: hidden; }
    .slide {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 6vh 8vw;
      opacity: 0;
      transition: opacity 0.5s ease;
      pointer-events: none;
      overflow: hidden;
    }
    .slide.active {
      opacity: 1;
      pointer-events: auto;
    }

    /* ===== Typography ===== */
    h1 { font-size: 3.5vw; font-family: var(--heading-font); color: var(--heading); margin-bottom: 2vh; }
    h2 { font-size: 2.8vw; font-family: var(--heading-font); color: var(--heading); margin-bottom: 2vh; }
    h3 { font-size: 2.2vw; font-family: var(--heading-font); color: var(--heading); margin-bottom: 1.5vh; }
    p, li { font-size: 1.6vw; line-height: 1.7; margin-bottom: 1vh; }
    ul, ol { padding-left: 2vw; }
    code {
      font-family: var(--mono-font);
      background: var(--surface);
      padding: 0.15em 0.4em;
      border-radius: 4px;
      font-size: 0.9em;
    }
    pre {
      background: var(--surface);
      padding: 2vh 2vw;
      border-radius: 8px;
      overflow-x: auto;
    }
    pre code { background: none; padding: 0; font-size: 1.3vw; }

    /* ===== Bottom nav bar (arrows + progress dots) ===== */
    .nav-bar {
      position: fixed;
      bottom: 2.5vh;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      gap: 12px;
      align-items: center;
      z-index: 100;
    }
    .progress {
      display: flex;
      gap: 6px;
      align-items: center;
    }
    .progress-dot {
      width: 8px;
      height: 8px;
      border-radius: 4px;
      background: var(--muted);
      transition: width 0.35s ease, background 0.35s ease;
      cursor: pointer;
    }
    .progress-dot.active {
      width: 32px;
      background: var(--accent);
    }
    .nav-arrow {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 32px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--muted);
      cursor: pointer;
      transition: color 0.2s, border-color 0.2s;
      user-select: none;
      flex-shrink: 0;
    }
    .nav-arrow:hover {
      color: var(--accent);
      border-color: var(--accent);
    }
    .nav-arrow .arrow {
      font-size: 1vw;
      line-height: 1;
      font-family: var(--body-font);
    }
    .nav-arrow .key {
      font-size: 0.55vw;
      font-family: var(--mono-font);
      opacity: 0.7;
    }

    /* ===== Overview grid (Escape) ===== */
    .overview-overlay {
      position: fixed;
      inset: 0;
      background: var(--bg);
      z-index: 200;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 3vh 3vw;
      overflow: auto;
    }
    .overview-overlay.visible {
      display: flex;
      flex-direction: column;
    }
    .overview-overlay .overview-hint {
      font-size: 1.2vw;
      color: var(--muted);
      margin-bottom: 2vh;
    }
    .overview-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 1rem;
      max-width: 90vw;
    }
    .overview-card {
      background: var(--surface);
      border: 2px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      cursor: pointer;
      text-align: center;
      transition: border-color 0.2s, transform 0.2s;
    }
    .overview-card:hover {
      border-color: var(--accent);
      transform: scale(1.02);
    }
    .overview-card.active {
      border-color: var(--accent);
      background: var(--surface2);
    }
    .overview-card .num {
      font-size: 1.5vw;
      font-weight: 700;
      color: var(--accent);
      display: block;
    }
    .overview-card .title {
      font-size: 0.9vw;
      margin-top: 0.5rem;
      color: var(--fg);
      line-height: 1.3;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    /* ===== Supplementary slides ===== */
    .supp-label {
      display: inline-block; font-size: 0.85vw; text-transform: uppercase;
      letter-spacing: 0.15em; color: var(--muted); border: 1px solid var(--border);
      border-radius: 4px; padding: 0.2em 0.7em; margin-bottom: 2vh;
    }
    .supp-link {
      color: var(--accent); text-decoration: none;
      border-bottom: 1px dashed var(--accent); cursor: pointer;
    }
    .supp-link:hover { border-bottom-style: solid; }
    .progress-sep {
      width: 1px; height: 12px; background: var(--border); margin: 0 4px; flex-shrink: 0;
    }
    .progress-dot.supplementary { opacity: 0.5; }
    .progress-dot.supplementary.active { opacity: 1; }
    .overview-card.supplementary { opacity: 0.7; }

    /* ===== Diagram base classes ===== */
    .diagram-node      { fill: var(--diagram-fill); stroke: var(--diagram-stroke); stroke-width: 2; }
    .diagram-highlight  { fill: var(--diagram-highlight); stroke: var(--diagram-highlight); stroke-width: 2; }
    .diagram-diamond    { fill: var(--surface2); stroke: var(--diagram-stroke); stroke-width: 2; }
    .diagram-label      { fill: var(--diagram-text); font-family: var(--body-font); font-size: 14px; text-anchor: middle; dominant-baseline: central; }
    .diagram-label-inv  { fill: var(--bg); font-family: var(--body-font); font-size: 14px; text-anchor: middle; dominant-baseline: central; }
    .diagram-label-sm   { fill: var(--diagram-text); font-family: var(--body-font); font-size: 11px; text-anchor: middle; dominant-baseline: central; opacity: 0.7; }
    .diagram-edge       { stroke: var(--diagram-arrow); stroke-width: 2; fill: none; }
    .diagram-edge-accent { stroke: var(--diagram-stroke); stroke-width: 2; fill: none; }
    .slide svg          { max-width: 100%; height: auto; }

    /* ===== Animation base classes ===== */
    .slide .anim-fade {
      opacity: 0;
      transform: translateY(20px);
    }
    .slide.active .anim-fade {
      opacity: 1;
      transform: translateY(0);
      transition: opacity 0.6s ease var(--delay, 0s),
                  transform 0.6s ease var(--delay, 0s);
    }
    .slide .anim-draw {
      stroke-dasharray: var(--len, 1000);
      stroke-dashoffset: var(--len, 1000);
    }
    .slide.active .anim-draw {
      stroke-dashoffset: 0;
      transition: stroke-dashoffset 1.2s ease-in-out var(--delay, 0s);
    }
    @keyframes pulse-glow {
      0%, 100% { filter: drop-shadow(0 0 3px var(--diagram-stroke)); }
      50%      { filter: drop-shadow(0 0 10px var(--diagram-stroke)); }
    }
    .slide.active .anim-pulse {
      animation: pulse-glow 2s ease-in-out infinite;
      animation-delay: var(--delay, 0s);
    }

    /* Additional theme-specific rules (paste from theme file if any) */
  </style>
</head>
<body>
  <div class="deck">

    <section class="slide" id="title">
      <h1>Presentation Title</h1>
      <p>Author &mdash; Date</p>
    </section>

    <section class="slide" id="slide-2">
      <h2>Slide Heading</h2>
      <ul>
        <li>Point one</li>
        <li>Point two</li>
      </ul>
    </section>

    <!-- more <section class="slide"> elements -->

  </div>

  <div class="nav-bar">
    <div class="nav-arrow nav-prev"><span class="arrow">&#8249;</span><span class="key">j</span></div>
    <div class="progress"></div>
    <div class="nav-arrow nav-next"><span class="arrow">&#8250;</span><span class="key">k</span></div>
  </div>

  <div class="overview-overlay" id="overview" aria-label="Slide overview">
    <p class="overview-hint">Click a slide to jump · Esc to close</p>
    <div class="overview-grid"></div>
  </div>

  <script>
    (function () {
      var slides = document.querySelectorAll('.slide');
      var current = 0;
      var total = slides.length;
      var progress = document.querySelector('.progress');
      var prevBtn = document.querySelector('.nav-prev');
      var nextBtn = document.querySelector('.nav-next');
      var overview = document.getElementById('overview');
      var overviewGrid = overview.querySelector('.overview-grid');

      var suppInserted = false;
      for (var i = 0; i < total; i++) {
        if (!suppInserted && slides[i].hasAttribute('data-supplementary')) {
          var sep = document.createElement('div');
          sep.className = 'progress-sep';
          progress.appendChild(sep);
          suppInserted = true;
        }
        var dot = document.createElement('div');
        dot.className = 'progress-dot';
        if (slides[i].hasAttribute('data-supplementary')) dot.classList.add('supplementary');
        dot.dataset.index = i;
        dot.addEventListener('click', function () {
          show(parseInt(this.dataset.index));
        });
        progress.appendChild(dot);
      }
      var dots = progress.querySelectorAll('.progress-dot');

      for (var i = 0; i < total; i++) {
        var card = document.createElement('button');
        card.type = 'button';
        card.className = 'overview-card';
        if (slides[i].hasAttribute('data-supplementary')) card.classList.add('supplementary');
        card.dataset.index = i;
        var titleEl = slides[i].querySelector('h1, h2, h3');
        var title = titleEl ? titleEl.textContent.trim() : 'Slide ' + (i + 1);
        card.innerHTML = '<span class="num">' + (i + 1) + '</span><span class="title">' + title.replace(/</g, '&lt;') + '</span>';
        card.addEventListener('click', function () {
          show(parseInt(this.dataset.index));
          overview.classList.remove('visible');
        });
        overviewGrid.appendChild(card);
      }
      var overviewCards = overviewGrid.querySelectorAll('.overview-card');

      var slideIdMap = {};
      for (var i = 0; i < total; i++) {
        if (slides[i].id) slideIdMap[slides[i].id] = i;
      }

      function show(idx) {
        if (idx < 0 || idx >= total) return;
        slides[current].classList.remove('active');
        dots[current].classList.remove('active');
        if (overviewCards[current]) overviewCards[current].classList.remove('active');
        current = idx;
        slides[current].classList.add('active');
        dots[current].classList.add('active');
        if (overviewCards[current]) overviewCards[current].classList.add('active');
      }

      document.addEventListener('click', function (e) {
        var link = e.target.closest('[data-goto]');
        if (link) {
          e.preventDefault();
          var target = link.getAttribute('data-goto');
          if (slideIdMap[target] !== undefined) show(slideIdMap[target]);
        }
      });

      prevBtn.addEventListener('click', function () { show(current - 1); });
      nextBtn.addEventListener('click', function () { show(current + 1); });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          overview.classList.toggle('visible');
          if (overview.classList.contains('visible')) {
            for (var i = 0; i < overviewCards.length; i++) {
              overviewCards[i].classList.toggle('active', i === current);
            }
          }
          return;
        }
        if (overview.classList.contains('visible')) return;
        switch (e.key) {
          case ' ':
            e.preventDefault();
            show(current + (e.shiftKey ? -1 : 1));
            break;
          case 'ArrowRight': case 'k':
            show(current + 1);
            break;
          case 'ArrowLeft': case 'j':
            show(current - 1);
            break;
        }
      });

      show(0);
    })();
  </script>
</body>
</html>
```

### Step 3: Add slide content

**Title slide** — centered, large heading, subtitle:

```html
<section class="slide" id="title">
  <h1>Title Text</h1>
  <p>Subtitle or author</p>
</section>
```

**Content slide** — heading + body:

```html
<section class="slide" id="topic-name">
  <h2>Heading</h2>
  <p>Body text or a list:</p>
  <ul>
    <li>Item</li>
  </ul>
</section>
```

**Two-column slide** — use inline CSS grid:

```html
<section class="slide" id="comparison">
  <h2>Side by Side</h2>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:4vw; flex:1;">
    <div>Left column content</div>
    <div>Right column content</div>
  </div>
</section>
```

**Diagram slide** — inline SVG using diagram classes:

```html
<section class="slide" id="architecture">
  <h2>System Architecture</h2>
  <svg viewBox="0 0 800 400">
    <!-- diagram elements using .diagram-node, .diagram-edge, etc. -->
  </svg>
</section>
```

**Spotlight / feature slide** — two-column grid with text on the left and a large SVG on the right. Use for showcasing a tool, feature, or concept with visual impact:

```html
<section class="slide" id="spotlight-feature" style="justify-content:center;">
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:4vw; align-items:center;">
    <div>
      <p class="dim anim-fade" style="--delay:0.1s; font-size:1vw; text-transform:uppercase; letter-spacing:0.2em; margin-bottom:1vh;">Label</p>
      <h2 class="anim-fade" style="--delay:0.2s; font-size:3.2vw;"><code style="background:var(--surface); padding:0.15em 0.4em; border-radius:6px;">Feature Name</code></h2>
      <p class="anim-fade" style="--delay:0.4s; font-size:2.4vw; color:var(--accent); margin-top:2vh; line-height:1.3;">Short tagline.<br>One line per idea.</p>
      <div class="anim-fade" style="--delay:0.7s; display:flex; gap:0.8vw; flex-wrap:wrap; margin-top:3vh;">
        <span style="background:var(--accent); color:white; padding:0.4em 1em; border-radius:999px; font-size:1.1vw; font-weight:600;">Primary pill</span>
        <span style="background:var(--surface); color:var(--fg); padding:0.4em 1em; border-radius:999px; font-size:1.1vw;">Secondary pill</span>
        <span style="background:var(--surface); color:var(--fg); padding:0.4em 1em; border-radius:999px; font-size:1.1vw;">Another pill</span>
      </div>
    </div>
    <div class="anim-fade" style="--delay:0.5s;">
      <svg viewBox="0 0 400 340">
        <!-- Large, detailed diagram that fills the right half -->
      </svg>
    </div>
  </div>
</section>
```

Spotlight design principles:

- **Fill both columns.** The SVG `viewBox` should be generous (e.g. `0 0 400 340`) so the diagram fills the right half of the slide. Tiny SVGs with excess whitespace look unfinished.
- **No bullets.** Replace bullet lists with a short tagline (line-broken with `<br>`) and keyword pills below.
- **One highlighted pill.** Use `background:var(--accent); color:white; font-weight:600` for the primary keyword; keep the rest neutral (`var(--surface)` / `var(--fg)`).
- **Rich diagrams.** The right-column SVG should tell a story — use multiple nodes, arrows, labels, phases, or a miniature wireframe. The diagram is the hero of the slide.

**Supplementary slide** — detail, FAQ, or reference slides placed *after* the Thank You slide. Linked from main slides via `data-goto`:

```html
<section class="slide" id="supp-topic" data-supplementary>
  <span class="supp-label">Supplementary</span>
  <h2>Detailed Topic</h2>
  <p>Deep-dive content that supports a main slide.</p>
</section>
```

Supplementary slide conventions:

- **Place after Thank You.** The presentation flows: main slides → acknowledgments → thank-you → supplementary. The audience sees a clean ending; supplementary material is available for Q&A or self-study.
- **Mark with `data-supplementary`.** Add this attribute to the `<section>`. The JS uses it to insert a visual separator in the progress bar and dim supplementary dots.
- **Add `<span class="supp-label">`.** Shows "Supplementary" or "Supplementary · FAQ" badge at the top of the slide.
- **Link from main slides.** Use `<a class="supp-link" data-goto="supp-topic">Detail →</a>` in any main slide. The JS intercepts clicks and jumps to the target slide by ID.
- **Link from Thank You.** List all supplementary slides as links on the thank-you slide so the audience knows what's available.
- **ID convention.** Prefix supplementary slide IDs with `supp-` (e.g. `supp-detail`, `supp-harness`).

Required CSS (already in the base layout above):

```css
.supp-label {
  display: inline-block; font-size: 0.85vw; text-transform: uppercase;
  letter-spacing: 0.15em; color: var(--muted); border: 1px solid var(--border);
  border-radius: 4px; padding: 0.2em 0.7em; margin-bottom: 2vh;
}
.supp-link {
  color: var(--accent); text-decoration: none;
  border-bottom: 1px dashed var(--accent); cursor: pointer;
}
.supp-link:hover { border-bottom-style: solid; }
.progress-sep {
  width: 1px; height: 12px; background: var(--border); margin: 0 4px; flex-shrink: 0;
}
.progress-dot.supplementary { opacity: 0.5; }
.progress-dot.supplementary.active { opacity: 1; }
```

Required JS additions (already in the base script above):

- Build a `slideIdMap` mapping each slide's `id` to its index.
- On `data-goto` link click: `show(slideIdMap[target])`.
- When building progress dots, insert a `.progress-sep` `<div>` before the first supplementary slide.
- Add `.supplementary` class to dots and overview cards for `data-supplementary` slides.

Every `<section>` must have a unique `id`.

### Presentation structure

A well-structured presentation follows this order:

1. **Title** — name, author, date
2. **Main slides** — the core content (definition, why, how, examples, etc.)
3. **Acknowledgments** — credit collaborators, tools, sources
4. **Thank You** — closing slide with links and a list of supplementary topics
5. **Supplementary** — detail slides, FAQ, reference material (linked from main slides and the thank-you slide)

The progress bar visually separates main from supplementary with a thin vertical line.

### Step 4: Add SVG diagrams

Read [references/svg-diagrams.md](references/svg-diagrams.md) for complete patterns:

- **Flowcharts** — decision trees, process flows with boxes, diamonds, and arrows
- **Architecture diagrams** — layered stacks, connected services
- **Pipeline diagrams** — data flowing through processing stages
- **Comparison diagrams** — side-by-side feature or option comparisons

All diagram SVG elements use the `.diagram-*` CSS classes defined in the base layout, so they automatically match the active theme.

**Arrowhead markers** — every SVG that uses arrows needs this `<defs>` block:

```html
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto-start-reverse">
    <polygon points="0 0, 10 3.5, 0 7" fill="var(--diagram-arrow)" />
  </marker>
  <marker id="arrow-accent" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto-start-reverse">
    <polygon points="0 0, 10 3.5, 0 7" fill="var(--diagram-stroke)" />
  </marker>
  <filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">
    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
  </filter>
</defs>
```

Use `marker-end="url(#arrow)"` on `.diagram-edge` lines and `marker-end="url(#arrow-accent)"` on `.diagram-edge-accent` lines.

### Step 5: Add SVG animations where appropriate

Read [references/svg-animations.md](references/svg-animations.md) for complete patterns and guidance on **when** each animation type is appropriate.

Three built-in animation classes (defined in the base CSS):

| Class | Effect | Trigger |
|-------|--------|---------|
| `.anim-fade` | Fade up into view | Slide becomes active |
| `.anim-draw` | SVG path draws itself (stroke-dashoffset) | Slide becomes active |
| `.anim-pulse` | Pulsing glow on an SVG element | Slide becomes active |

Stagger timing with inline `--delay`:

```html
<p class="anim-fade" style="--delay:0.2s">Appears first</p>
<p class="anim-fade" style="--delay:0.5s">Appears second</p>
```

For SVG path drawing, set `--len` to the path's total length:

```html
<path class="diagram-edge anim-draw" style="--len:350"
      d="M 50,100 C 150,50 250,150 350,100" />
```

**When to use animations** (summary — see reference file for full guidance):

- **Path drawing**: showing connections being established, network topology, building a diagram
- **Sequential fade-in**: step-by-step concept building, lists that tell a story
- **Pulse/glow**: highlighting the current step in a process, drawing attention to a key node
- **Do NOT animate** purely decorative elements, every bullet point, or content that the audience needs to read immediately

### Design guidelines

1. **One idea per slide** — avoid cramming. More slides is fine.
2. **Large text** — if a slide has little content, scale up. Use `font-size: 2.5vw` or larger.
3. **Diagrams over bullet lists** — when explaining a process, architecture, or flow, use an SVG diagram rather than a bulleted list.
4. **Consistent spacing** — use `vh`/`vw` units for padding and margins so spacing scales with the viewport.
5. **Color hierarchy** — `--heading` for titles, `--fg` for body, `--muted` for secondary text, `--accent` for emphasis.
6. **Code blocks** — use `<pre><code>` with the theme's `--code-bg`/`--code-fg`. Keep code short (< 15 lines per slide).
7. **Python in slides** — when including Python code, make it runnable with **`uv run script.py`** so it is self-contained and does not require external software environments. Use PEP 723 inline script metadata at the top of the script (`# /// script`, `requires-python`, `dependencies`, `# ///`) and state in the slide or speaker notes that the audience runs it with `uv run script.py`.
8. **No external assets** — everything inline. If an image is needed, use an inline SVG illustration rather than a raster image.
9. **Fill the slide** — avoid layouts where content clusters in one corner and the rest is empty space. Use two-column grids (`grid-template-columns: 1fr 1fr`) to balance text and diagrams side by side, with `align-items:center` to vertically center both columns.
10. **Taglines over bullets for features** — when spotlighting a feature or concept, replace bullet lists with a short tagline (2–3 short lines broken with `<br>`) and keyword pills beneath. This is punchier and more scannable.
11. **Make SVGs the hero** — when a slide has a diagram, give it at least half the slide width. Use generous `viewBox` dimensions and fill the space with detail: multiple nodes, labels, phases, wireframe lines, loop-back arrows. A tiny diagram floating in whitespace looks unfinished.
