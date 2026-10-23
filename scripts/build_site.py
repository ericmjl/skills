# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "markdown"]
# ///
"""Build the ericmjl/skills landing site into _site/.

Scans skills/*/SKILL.md for frontmatter, generates a searchable index page,
a detail page per skill (frontmatter metadata, rendered instructions, and
any prompt cards that invoke it), standalone prompt-card widgets, and the
agent-skills overview deck. Run with: uv run scripts/build_site.py
"""

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

import markdown as md_lib
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
NEW_CARDS_DIR = ROOT / "site" / "cards"
EXAMPLE_CARDS_DIR = SKILLS_DIR / "prompt-card" / "assets" / "examples"
OVERVIEW_SRC = ROOT / "docs" / "agent-skills-overview.html"
OUT = ROOT / "_site"
REPO_URL = "https://github.com/ericmjl/skills"
SKILL_TREE_URL = f"{REPO_URL}/tree/main/skills"
RAW_URL = f"{REPO_URL}/raw/main/skills"
BLOB_URL = f"{REPO_URL}/blob/main/skills"
INSTALL_CMD = "npx skills add ericmjl/skills"

# Measured rendered heights (card page body incl. its 16px padding, plus a
# small buffer) for the hand-authored cards. Iframes carry these as static
# height attributes: no JS resizes them after load. This matters because
# resizing an iframe after the parent page loads leaves Chrome's scrollable
# range stale and the page can become impossible to scroll to the bottom.
CARD_HEIGHTS = {
    "make-a-prompt-card": 456,
    "build-a-landing-page": 444,
    "ingest-a-source": 378,
    "mine-your-chat-logs": 516,
    "review-a-pr": 456,
    # One card per skill, shown on that skill's page (SKILL_CARDS below).
    "agents-md-improver": 438,
    "atomic-commits": 438,
    "audit-before-rewrite": 432,
    "awesome-marimo-notebook": 468,
    "blog-explainer-prose-dedup": 438,
    "codebase-study-parallel-reporters": 438,
    "coherent-writing": 438,
    "cybersecurity-review": 468,
    "data-visualization-master": 468,
    "debug-github-ci": 420,
    "design-driven-dev": 468,
    "docker-offline-verification": 420,
    "dom-anchored-svg-connectors": 420,
    "epistemic-resourcefulness": 438,
    "evident-charts": 438,
    "gh-activity-summary": 420,
    "gh-cli": 420,
    "git-rebase-noninteractive-editor": 420,
    "github-auto-merge-setup": 438,
    "html-presentations": 438,
    "jupyterlab-collab-mcp-setup": 438,
    "large-file-edit-truncation-guardrail": 420,
    "marimo-notebook-patterns": 408,
    "marimo": 408,
    "ml-experimentation": 438,
    "motion-graphics-video": 456,
    "npm-trusted-publishing-oidc-setup": 438,
    "opencode-bash-background-process-survival": 420,
    "opencode-mcp-server-setup": 420,
    "opencode-ollama-provider-setup": 438,
    "opencode-plugin-authoring": 420,
    "pdf-form-filler": 390,
    "plaud-ingestion": 390,
    "publish-to-google-docs": 420,
    "python-importtime-optimization": 438,
    "remotion-video": 438,
    "scientific-eda": 420,
    "skill-creator": 420,
    "slack-cli": 438,
    "stacked-pr-decomposition": 438,
    "typewriter-video": 438,
    "video-script-writing": 438,
    "voss-advisor": 420,
    "webfetch-empty-use-agent-browser": 438,
    "xarray-linked-data": 420,
    "youtube": 390,
}

# Prompt cards embedded on the home page, in display order.
# fields: slug, title, blurb, source path, taught skill (name, tree url or None),
# and an optional "home" flag (default True) for whether the home page shows it
CARDS = [
    {
        "slug": "make-a-prompt-card",
        "title": "Make a prompt card",
        "blurb": "Teach an agent to turn any prompt you use into a card like these.",
        "src": EXAMPLE_CARDS_DIR / "make-a-prompt-card" / "standalone.html",
        "skill": ("prompt-card", f"{SKILL_TREE_URL}/prompt-card"),
    },
    {
        "slug": "build-a-landing-page",
        "title": "Build a landing page",
        "blurb": "Have an agent build a Dataview landing page for your Obsidian vault.",
        "src": EXAMPLE_CARDS_DIR / "build-a-landing-page" / "standalone.html",
        "skill": ("obsidian-landing-page", f"{SKILL_TREE_URL}/obsidian-landing-page"),
    },
    {
        "slug": "ingest-a-source",
        "title": "Ingest a source",
        "blurb": "File a URL or document into your vault without explaining your conventions every time.",
        "src": EXAMPLE_CARDS_DIR / "ingest-a-source" / "standalone.html",
        "skill": None,
    },
    {
        "slug": "mine-your-chat-logs",
        "title": "Mine your chat logs",
        "blurb": "Send the agent back through its own past sessions to turn recurring lessons into a skill or a knowledge base other agents can use.",
        "src": NEW_CARDS_DIR / "mine-your-chat-logs.html",
        "skill": ("mempalace", f"{SKILL_TREE_URL}/mempalace"),
    },
    {
        "slug": "review-a-pr",
        "title": "Review a pull request",
        "blurb": "A two-pass code review that drafts its comments and posts nothing until you approve.",
        "src": NEW_CARDS_DIR / "review-a-pr.html",
        "skill": ("gh-pr-code-review", f"{SKILL_TREE_URL}/gh-pr-code-review"),
    },
]

# One card per remaining skill, each saying when to reach for that skill.
# These appear only on their skill's detail page, not on the home page.
# fields: skill name (also the card slug and site/cards/<name>.html), title, blurb
SKILL_CARDS = [
    ("agents-md-improver", "Turn a correction into a rule",
     "Reach for this right after you correct your agent and want the fix to stick in the repo's AGENTS.md, so you don't repeat it next session."),
    ("atomic-commits", "Split a messy working tree into commits",
     "Reach for this when your working tree holds several unrelated changes and you want a clean history with one logical change per commit."),
    ("audit-before-rewrite", "Rewrite a file without losing features",
     "Reach for this before an agent rewrites, restyles, or regenerates a whole file that has picked up features over earlier turns."),
    ("awesome-marimo-notebook", "Bring a paper to life in marimo",
     "Reach for this when you want an interactive marimo notebook that explains a research paper or dataset, for a tutorial, a competition entry, or a blog companion."),
    ("blog-explainer-prose-dedup", "Cut repetition from an explainer post",
     "Reach for this when a long explainer or tutorial post says the same thing in several sections, or its takeaway doesn't match what the post went deep on."),
    ("codebase-study-parallel-reporters", "Study an unfamiliar codebase",
     "Reach for this when you need a thorough, cited account of how something works in a repo you don't know, or how two repos handle the same thing."),
    ("coherent-writing", "Make a draft read as one argument",
     "Reach for this when a draft feels choppy, jumps between ideas, or contradicts itself, and you want it to flow without new points being added."),
    ("cybersecurity-review", "Check code for security holes",
     "Reach for this before you merge new code or adopt an open source dependency, or when you want an existing repo audited for vulnerabilities."),
    ("data-visualization-master", "Critique and fix a figure",
     "Reach for this when you are making or critiquing a chart or figure, especially a multi-panel or publication figure, and want choices backed by the visualization literature."),
    ("debug-github-ci", "Fix a failing CI run",
     "Reach for this when a GitHub Actions run fails, or when you want the agent to watch a PR's checks until they finish."),
    ("design-driven-dev", "Design a feature before coding it",
     "Reach for this when you start a new feature or a major refactor and want the design agreed before any code is written."),
    ("docker-offline-verification", "Prove a container works offline",
     "Reach for this when you need to show that a containerized app serves every route with no network access, or when ports on a --network none container seem unreachable."),
    ("dom-anchored-svg-connectors", "Draw arrows that stay on their boxes",
     "Reach for this when you draw connector lines between HTML elements, like gantt dependencies or flowchart edges, or when existing connectors drift away from their boxes."),
    ("epistemic-resourcefulness", "Stop guessing and find the source",
     "Reach for this when your agent keeps retrying the same failing command or guessing names, or is about to tell you it has no access to something."),
    ("evident-charts", "Make a chart whose point is obvious",
     "Reach for this when you make or revise a chart for readers, in a blog, report, slide, or social post, and want the point to land at a glance."),
    ("gh-activity-summary", "Summarize your GitHub week",
     "Reach for this when you need a status update, a retro, or a record of what you did on GitHub over a date range or on one day."),
    ("gh-cli", "Open and merge a PR from the terminal",
     "Reach for this for everyday GitHub chores from the command line: opening and merging PRs, reading Actions logs, managing issues and project boards."),
    ("git-rebase-noninteractive-editor", "Unstick a rebase in an agent's shell",
     "Reach for this when git rebase --continue hangs or times out in an agent's shell, CI, or a script, or before running an interactive rebase with no terminal."),
    ("github-auto-merge-setup", "Make auto-merge work",
     "Reach for this when gh pr merge --auto fails, when you want dependency PRs to merge once CI is green, or when a PR stays blocked despite green checks."),
    ("html-presentations", "Build a single-file HTML deck",
     "Reach for this when you want a slide deck as one HTML file that opens in any browser, with no framework or build step."),
    ("jupyterlab-collab-mcp-setup", "Connect your agent to JupyterLab",
     "Reach for this when you want your agent to edit and run notebooks through the jupyterlab-collab-mcp server, or when its Jupyter tools are missing or can't connect."),
    ("large-file-edit-truncation-guardrail", "Edit a big file without losing its end",
     "Reach for this when an agent edits a file of 1000 or more lines, or when an edit reported success but sections near the end went missing."),
    ("marimo-notebook-patterns", "Fix a marimo notebook that won't run",
     "Reach for this when you write or edit a marimo .py notebook, or when one fails with errors like a name defined in more than one cell."),
    ("marimo", "Embed live marimo cells in a blog post",
     "Reach for this for any marimo task, such as putting interactive marimo cells into a static blog or site."),
    ("ml-experimentation", "Run one ML experiment properly",
     "Reach for this when you want to test an idea with a model: train, compare, and write up results with a record of what you tried."),
    ("motion-graphics-video", "Make a motion graphics video",
     "Reach for this when you want a finished MP4 such as a product teaser, kinetic typography, a lyric video, or a launch film, with music and sound effects."),
    ("npm-trusted-publishing-oidc-setup", "Publish to npm without a token",
     "Reach for this when you set up a GitHub Actions workflow to publish an npm package, or npmjs.com asks you to switch to Trusted Publishing."),
    ("opencode-bash-background-process-survival", "Keep a dev server alive between turns",
     "Reach for this when a server your agent started in the background is dead by the next turn, or before starting one that has to outlive the command (opencode on macOS)."),
    ("opencode-mcp-server-setup", "Add an MCP server to opencode",
     "Reach for this when you want a new MCP server's tools in opencode, or when a server you expected is missing from your sessions."),
    ("opencode-ollama-provider-setup", "Use an Ollama model in opencode",
     "Reach for this when you want a model served by Ollama, on your laptop or another machine, to show up as a model in opencode."),
    ("opencode-plugin-authoring", "Write an opencode plugin",
     "Reach for this when you build an opencode plugin, such as one that notifies you when the agent finishes, or install a local plugin from source."),
    ("pdf-form-filler", "Fill this year's PDF form",
     "Reach for this when you have to fill out a PDF form, especially a yearly one like a school enrollment or a renewal where last year's filled copy exists."),
    ("plaud-ingestion", "Sync Plaud recordings into your vault",
     "Reach for this when you want new PLAUD recordings (transcripts, speakers, AI notes) pulled into your Obsidian vault, or a backfill of older ones."),
    ("publish-to-google-docs", "Turn a markdown note into a Google Doc",
     "Reach for this when you want a markdown note as a styled Google Doc or Word file, using your template's fonts and headings."),
    ("python-importtime-optimization", "Speed up a slow Python import",
     "Reach for this when importing your Python package takes seconds, a CI import-time benchmark is slipping, or a CLI starts slowly."),
    ("remotion-video", "Make a short video with Remotion",
     "Reach for this when you want an animated short-form video built with Remotion: an explainer, a product demo, testimonials, a data dashboard, or overlays."),
    ("scientific-eda", "Explore a scientific dataset step by step",
     "Reach for this when you open a new scientific data file (CSV, FASTA, and so on) and want a careful, guided look, one step at a time."),
    ("skill-creator", "Turn a workflow into a skill",
     "Reach for this when you want to write a new agent skill, or fix one that agents don't load when they should."),
    ("slack-cli", "Run a Slack CLI command safely",
     "Reach for this when you build, run, or deploy a Slack app with the slack CLI, or need the right command and flags for a task."),
    ("stacked-pr-decomposition", "Break a huge branch into stacked PRs",
     "Reach for this when a branch has grown too big to review and you want a chain of small PRs, each reviewable in about five minutes."),
    ("typewriter-video", "Make a code typing video",
     "Reach for this when you want a VS Code-style typing animation with keyboard sounds, for a code walkthrough or as B-roll."),
    ("video-script-writing", "Write a video script that holds attention",
     "Reach for this when you need a script for a YouTube explainer, founder story, landing-page video, ad, or short, or want to fix a script's hook or pacing."),
    ("voss-advisor", "Plan a tough conversation",
     "Reach for this before a negotiation or a hard conversation (salary, a vendor, a landlord, pushback at work), or when you need to answer a tricky message."),
    ("webfetch-empty-use-agent-browser", "Read a page that fetching can't",
     "Reach for this when fetching a web page comes back empty, too large, or as a bare JavaScript shell, as with many job boards and single-page apps."),
    ("xarray-linked-data", "Put linked lab data in one xarray",
     "Reach for this when measurements, derived estimates, and model outputs sit in separate files but share samples or conditions, and you want them in one aligned xarray structure."),
    ("youtube", "Get a YouTube transcript",
     "Reach for this when you want the transcript of a YouTube video, or for other YouTube work: downloading video or audio, reading metadata, or working through a playlist."),
]
CARDS += [
    {
        "slug": name,
        "title": title,
        "blurb": blurb,
        "src": NEW_CARDS_DIR / f"{name}.html",
        "skill": (name, f"{SKILL_TREE_URL}/{name}"),
        "home": False,
    }
    for name, title, blurb in SKILL_CARDS
]

TRIGGER_MARKERS = (" Use when", " Use this", " Use it", " Triggers", " Also use", " Also triggers")
BLURB_MAX = 220
TRIGGER_MAX = 260

CSS = """
:root {
  --bg: #f4f6f6;
  --fg: #1a2522;
  --heading: #006044;
  --accent: #006044;
  --accent2: #76A923;
  --surface: #ffffff;
  --surface2: #e2e8e6;
  --muted: #5c6c68;
  --border: #9fb5ae;
  --code-bg: #e8eeec;
  --body-font: "Inter", "Segoe UI", system-ui, sans-serif;
  --mono-font: "SF Mono", "Fira Code", "Cascadia Code", monospace;
}
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
body { background: var(--bg); color: var(--fg); font-family: var(--body-font); line-height: 1.6; }

header.site { background: var(--heading); color: #f2f7f5; padding: 56px 24px 48px; }
header.site .wrap { max-width: 1040px; margin: 0 auto; }
header.site h1 { font-size: 2.4rem; letter-spacing: -0.02em; }
header.site h1 .repo { color: #cfe89a; font-family: var(--mono-font); font-weight: 600; }
header.site p.tagline { font-size: 1.15rem; max-width: 46rem; margin-top: 10px; color: #dcebe4; }
header.site nav { margin-top: 22px; display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.95rem; }
header.site nav a { color: #ffffff; text-decoration: none; border-bottom: 1px dashed rgba(255,255,255,0.55); padding-bottom: 1px; }
header.site nav a:hover { border-bottom-style: solid; border-bottom-color: #cfe89a; }

.install { margin-top: 26px; display: inline-flex; align-items: stretch; gap: 0; background: #0b4d38; border: 1px solid rgba(255,255,255,0.25); border-radius: 8px; overflow: hidden; }
.install code { font-family: var(--mono-font); font-size: 0.95rem; padding: 10px 14px; color: #eaf5ee; }
.install button { border: none; cursor: pointer; background: var(--accent2); color: #16210c; font-family: var(--body-font); font-weight: 600; font-size: 0.9rem; padding: 0 16px; }
.install button.ok { background: #cfe89a; }

.topbar { background: var(--heading); color: #f2f7f5; }
.topbar .wrap { max-width: 1040px; margin: 0 auto; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.topbar a { color: #ffffff; text-decoration: none; font-family: var(--mono-font); font-size: 0.9rem; border-bottom: 1px dashed rgba(255,255,255,0.55); padding-bottom: 1px; }
.topbar a:hover { border-bottom-style: solid; border-bottom-color: #cfe89a; }

main { max-width: 1040px; margin: 0 auto; padding: 48px 24px 24px; }
section { margin-bottom: 64px; }
h2 { font-size: 1.6rem; color: var(--heading); margin-bottom: 6px; letter-spacing: -0.01em; }
.section-sub { color: var(--muted); margin-bottom: 22px; max-width: 52rem; }
.section-sub a, .skillpage .lede a { color: var(--accent); }

/* skills grid */
.search-row { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
#search { flex: 1 1 280px; max-width: 420px; font-size: 1rem; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--fg); }
#search:focus { outline: 2px solid var(--accent2); border-color: var(--accent2); }
#count { font-size: 0.9rem; color: var(--muted); font-family: var(--mono-font); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.skill-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px 16px 12px; display: flex; flex-direction: column; gap: 8px; transition: border-color 0.15s; }
.skill-card:hover { border-color: var(--accent); }
.skill-card.hidden { display: none; }
.skill-card h3 { font-size: 0.95rem; font-family: var(--mono-font); word-break: break-word; }
.skill-card h3 a { color: var(--heading); text-decoration: none; }
.skill-card h3 a:hover { text-decoration: underline; }
.skill-card p { font-size: 0.88rem; color: #33413c; flex: 1; }
.skill-links { display: flex; justify-content: space-between; align-items: center; }
.skill-links a { font-size: 0.8rem; color: var(--muted); text-decoration: none; font-family: var(--mono-font); }
.skill-links a:hover { color: var(--accent); text-decoration: underline; }
.no-results { display: none; color: var(--muted); font-size: 0.95rem; padding: 12px 0; }

/* prompt cards */
.card-embed { margin-bottom: 40px; }
.card-embed iframe { display: block; background: #ffffff; border-radius: 8px; }
.card-embed-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.card-embed h3 { font-size: 1.15rem; color: var(--heading); }
.standalone-link { font-size: 0.85rem; color: var(--muted); text-decoration: none; font-family: var(--mono-font); }
.standalone-link:hover { color: var(--accent); text-decoration: underline; }
.card-blurb { font-size: 0.95rem; color: #33413c; margin: 4px 0 12px; max-width: 52rem; }
.card-teaches { display: inline; margin: 0; }
.card-teaches a { color: var(--accent); font-family: var(--mono-font); font-size: 0.88rem; }

/* skill detail page */
.skillpage main { padding-top: 36px; }
.skillpage .eyebrow { font-family: var(--mono-font); font-size: 0.82rem; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; }
.skillpage h1.name { font-family: var(--mono-font); font-size: 2rem; color: var(--heading); margin: 4px 0 14px; word-break: break-word; }
.skillpage .lede { font-size: 1.05rem; max-width: 54rem; margin-bottom: 8px; }
.meta-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 18px 20px; margin: 26px 0 12px; }
.meta-grid { display: grid; grid-template-columns: 150px 1fr; gap: 10px 18px; font-size: 0.92rem; }
.meta-grid dt { color: var(--muted); font-family: var(--mono-font); font-size: 0.85rem; padding-top: 2px; }
.meta-grid dd { margin: 0; word-break: break-word; }
.meta-grid code, .md-body code { font-family: var(--mono-font); background: var(--code-bg); padding: 0.1em 0.35em; border-radius: 4px; font-size: 0.85em; }
.meta-grid pre { background: var(--code-bg); border-radius: 6px; padding: 10px 12px; overflow-x: auto; font-size: 0.8rem; font-family: var(--mono-font); }
.file-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.file-chips a { font-family: var(--mono-font); font-size: 0.82rem; color: var(--accent); border: 1px solid var(--border); border-radius: 6px; padding: 2px 8px; text-decoration: none; }
.file-chips a:hover { border-color: var(--accent); }
.md-body { max-width: 54rem; }
.md-body h1 { font-size: 1.45rem; color: var(--heading); margin: 28px 0 10px; }
.md-body h2 { font-size: 1.25rem; color: var(--heading); margin: 26px 0 8px; }
.md-body h3, .md-body h4 { font-size: 1.05rem; color: var(--heading); margin: 20px 0 6px; }
.md-body p, .md-body li { font-size: 0.95rem; line-height: 1.65; }
.md-body ul, .md-body ol { padding-left: 1.4rem; margin: 8px 0 14px; }
.md-body li { margin-bottom: 4px; }
.md-body ul li { list-style: disc; }
.md-body ol li { list-style: decimal; }
.md-body pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; overflow-x: auto; margin: 12px 0 18px; }
.md-body pre code { background: none; padding: 0; }
.md-body blockquote { border-left: 3px solid var(--accent2); padding: 2px 0 2px 14px; color: var(--muted); margin: 10px 0 16px; }
.md-body table { border-collapse: collapse; margin: 12px 0 18px; font-size: 0.9rem; }
.md-body th, .md-body td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
.md-body img { max-width: 100%; }
.md-body a { color: var(--accent); }
.md-body hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }

footer.site { border-top: 1px solid var(--border); color: var(--muted); font-size: 0.85rem; padding: 24px; text-align: center; }
footer.site a { color: var(--accent); }
footer.site .mono { font-family: var(--mono-font); }

@media (max-width: 560px) { .meta-grid { grid-template-columns: 1fr; gap: 2px 0; } .meta-grid dt { padding-top: 8px; } }
"""

FAVICON = """<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧰</text></svg>">"""

COPY_SCRIPT = """
(function () {
  'use strict';
  var btn = document.getElementById('install-copy');
  if (!btn) return;
  var cmd = document.getElementById('install-cmd').textContent;
  btn.addEventListener('click', function () {
    var done = function () {
      btn.textContent = 'Copied';
      btn.classList.add('ok');
      setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('ok'); }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(cmd).then(done, done);
    } else { done(); }
  });
})();
"""

INDEX_SCRIPT = """
(function () {
  'use strict';
  var skills = JSON.parse(document.getElementById('skills-data').textContent);
  var grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.skill-card'));
  var input = document.getElementById('search');
  var count = document.getElementById('count');
  var none = document.getElementById('no-results');

  function apply() {
    var q = input.value.trim().toLowerCase();
    var visible = 0;
    cards.forEach(function (card, i) {
      var hay = (skills[i].name + ' ' + skills[i].full).toLowerCase();
      var show = !q || hay.indexOf(q) !== -1;
      card.classList.toggle('hidden', !show);
      if (show) visible += 1;
    });
    count.textContent = visible + ' of ' + skills.length + ' skills';
    none.style.display = visible ? 'none' : 'block';
  }
  input.addEventListener('input', apply);
  apply();
})();
"""


def page_shell(title: str, description: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
{FAVICON}
<style>{CSS}</style>
</head>
<body>
{body}
<footer class="site">
  <p class="mono"><a href="{REPO_URL}">ericmjl/skills</a> · MIT licensed · built {date.today().strftime("%b %d, %Y")} with GitHub Actions</p>
</footer>
</body>
</html>
"""


def topbar(home_href: str) -> str:
    return f"""<header class="topbar"><div class="wrap">
  <a href="{home_href}">← All skills</a>
  <a href="{REPO_URL}">GitHub repository</a>
</div></header>"""


def hero() -> str:
    return f"""<header class="site"><div class="wrap">
    <h1>Agent skills <span class="repo">ericmjl/skills</span></h1>
    <p class="tagline">A library of $skill_count skills that teach coding agents to do real, repeatable work — review pull requests, run ML experiments, build marimo notebooks, make charts whose point is evident, and more. Free to install, MIT licensed.</p>
    <div class="install"><code id="install-cmd">{INSTALL_CMD}</code><button type="button" id="install-copy">Copy</button></div>
    <nav>
      <a href="{REPO_URL}">GitHub repository</a>
      <a href="overview.html">What are agent skills?</a>
      <a href="#prompt-cards">Prompt cards</a>
    </nav>
  </div></header>"""


def embed_iframe(src: str, height: int, title: str) -> str:
    # Static height, no resize script: see the CARD_HEIGHTS note above.
    return (f'<iframe src="{src}" width="100%" scrolling="no" height="{height}" '
            f'style="border:0" title="{html.escape(title)}"></iframe>')


def strip_fit(card_html: str) -> str:
    """Remove the iframe-resizing fit() logic from an embedded card copy.

    fit() shrinks the parent iframe to 0px before restoring it, and a
    post-load parent resize leaves the browser's scrollable range stale
    (the page becomes impossible to scroll to the bottom). Embedded cards
    rely on their height attribute instead. The copy button stays.
    """
    card_html = re.sub(r"  function fit\(\) \{\n(?:.*\n)*?  \}\n", "", card_html)
    for line in ("  window.addEventListener('load', fit);\n",
                 "  window.addEventListener('resize', fit);\n",
                 "  fit();\n"):
        card_html = card_html.replace(line, "")
    return card_html


def card_block(card: dict, base: str) -> str:
    if card["skill"]:
        sname, _ = card["skill"]
        teaches = (f'<p class="card-blurb">Teaches the skill '
                   f'<span class="card-teaches"><a href="{base}skills/{sname}/">{html.escape(sname)}</a></span></p>')
    else:
        teaches = '<p class="card-blurb">Teaches: your vault ingestion conventions</p>'
    return f"""<div class="card-embed" id="card-{card["slug"]}">
  <div class="card-embed-head">
    <h3>{html.escape(card["title"])}</h3>
    <a class="standalone-link" href="{base}cards/{card["slug"]}.html" target="_blank" rel="noopener">open standalone ↗</a>
  </div>
  <p class="card-blurb">{html.escape(card["blurb"])}</p>
  {teaches}
  {embed_iframe(f"{base}cards/{card['slug']}.html", CARD_HEIGHTS[card["slug"]], f"Prompt card: {card['title']}")}
</div>"""


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("missing frontmatter")
    meta = yaml.safe_load(m.group(1))
    if not isinstance(meta, dict):
        raise ValueError("frontmatter is not a mapping")
    return meta, m.group(2)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def short_blurb(description: str) -> str:
    """Description up to the first trigger clause, else the whole thing."""
    desc = normalize(description)
    cut = len(desc)
    for marker in TRIGGER_MARKERS:
        pos = desc.find(marker)
        if pos > 40 and pos < cut:  # keep blurbs that would otherwise go empty
            cut = pos
    blurb = desc[:cut].rstrip(" ,.;:")
    if len(blurb) > BLURB_MAX:
        blurb = blurb[:BLURB_MAX].rsplit(" ", 1)[0] + "…"
    return blurb


def trigger_clause(description: str) -> str | None:
    desc = normalize(description)
    for marker in TRIGGER_MARKERS:
        pos = desc.find(marker)
        if pos != -1:
            clause = desc[pos + 1:]
            if len(clause) > TRIGGER_MAX:
                clause = clause[:TRIGGER_MAX].rsplit(" ", 1)[0] + "…"
            return clause
    return None


def pretty_date(value) -> str:
    s = str(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return date.fromisoformat(s).strftime("%b %d, %Y")
    return s


def render_markdown(body: str, skill_name: str) -> str:
    # Drop a leading H1 that would duplicate the page title.
    body = re.sub(r"^#\s+.+\n+", "", body, count=1)
    rendered = md_lib.markdown(body, extensions=["fenced_code", "tables", "sane_lists"])
    # Point relative images at the repo and internal .md links at GitHub blobs.
    rendered = re.sub(r'(src=")(?!https?://)', rf"\1{RAW_URL}/{skill_name}/", rendered)
    rendered = re.sub(r'(href=")((?!https?://|#|mailto:)[^"]+\.md)"', rf"\1{BLOB_URL}/{skill_name}/\2\"", rendered)
    return rendered


class Skill:
    def __init__(self, path: Path):
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        self.name = str(meta.get("name") or path.parent.name)
        self.description = str(meta.get("description") or "")
        if not self.description:
            raise ValueError(f"{path}: empty description")
        self.meta = meta
        self.body_md = body
        self.blurb = short_blurb(self.description)
        self.full = normalize(self.description)
        self.trigger = trigger_clause(self.description)
        entries = []
        for child in sorted(path.parent.iterdir()):
            if child.name.startswith("."):
                continue
            kind = "tree" if child.is_dir() else "blob"
            entries.append((child.name, kind))
        self.files = entries

    def search_row(self) -> dict:
        return {"name": self.name, "blurb": self.blurb, "full": self.full}


def skill_meta_rows(skill: Skill) -> str:
    rows = []

    def row(label: str, value: str):
        if value:
            rows.append(f"<dt>{html.escape(label)}</dt><dd>{value}</dd>")

    if skill.meta.get("license"):
        row("License", html.escape(str(skill.meta["license"])))
    if skill.meta.get("created_at"):
        row("Created", html.escape(pretty_date(skill.meta["created_at"])))
    if skill.meta.get("created_by"):
        row("Created by", html.escape(str(skill.meta["created_by"])))
    for key in ("compatibility", "metadata"):
        if key in skill.meta:
            pretty = json.dumps(skill.meta[key], indent=2)
            row(key.capitalize(), f"<pre>{html.escape(pretty)}</pre>")
    row("Location", f"<code>skills/{html.escape(skill.name)}/</code>")
    row("Install", f"<code>{INSTALL_CMD}</code>")
    chips = "".join(
        f'<a href="{BLOB_URL}/{skill.name}/{html.escape(fname)}">{html.escape(fname)}{" /" if kind == "tree" else ""}</a>'
        for fname, kind in skill.files
    )
    row("Files", f'<div class="file-chips">{chips}</div>')
    return "<dl class=\"meta-grid\">" + "".join(rows) + "</dl>"


def skill_page(skill: Skill, cards_for_skill: list[dict]) -> str:
    base = "../../"
    invoke = ""
    if cards_for_skill:
        embeds = "".join(card_block(card, base) for card in cards_for_skill)
        invoke = f"""
  <section id="invoke">
    <h2>Invoke it</h2>
    <p class="section-sub">Prompt cards that show how to invoke this skill. Browse <a href="{base}index.html#prompt-cards">all prompt cards</a> on the home page.</p>
    {embeds}
  </section>"""
    lede = normalize(skill.description)
    body = f"""{topbar("../../")}
<main class="skillpage">
  <div class="eyebrow">agent skill</div>
  <h1 class="name">{html.escape(skill.name)}</h1>
  <p class="lede">{html.escape(lede)}</p>
  <div class="meta-panel">{skill_meta_rows(skill)}</div>{invoke}
  <section id="instructions">
    <h2>What the skill tells the agent</h2>
    <p class="section-sub">The full <a href="{BLOB_URL}/{skill.name}/SKILL.md">SKILL.md</a>, rendered. Agents load this on demand when the skill's name or triggers come up.</p>
    <div class="md-body">{render_markdown(skill.body_md, skill.name)}</div>
  </section>
</main>"""
    return page_shell(f"{skill.name} · ericmjl agent skills",
                      skill.blurb, body)


def index_page(skills: list[Skill], skills_json: str) -> str:
    skill_cards = "\n".join(
        f"""<div class="skill-card" data-name="{html.escape(s.name)}">
  <h3><a href="skills/{s.name}/">{html.escape(s.name)}</a></h3>
  <p>{html.escape(s.blurb)}</p>
  <div class="skill-links">
    <a href="skills/{s.name}/">details →</a>
    <a href="{SKILL_TREE_URL}/{s.name}">source ↗</a>
  </div>
</div>"""
        for s in skills
    )
    prompt_cards = "\n".join(card_block(c, "") for c in CARDS if c.get("home", True))
    body = f"""{hero()}
<main>
<section id="skills">
  <h2>The skills</h2>
  <p class="section-sub">Every skill is a folder with a <span class="mono">SKILL.md</span> that an agent loads on demand. Search by name or by what you want done; each card opens a detail page with the skill's metadata, its instructions, and any prompt cards that invoke it.</p>
  <div class="search-row">
    <input type="search" id="search" placeholder="Search skills… e.g. review, notebook, vault" autocomplete="off">
    <span id="count"></span>
  </div>
  <div class="grid" id="grid">{skill_cards}</div>
  <p class="no-results" id="no-results">No skills match that search.</p>
</section>

<section id="prompt-cards">
  <h2>Prompt cards</h2>
  <p class="section-sub">A prompt card teaches one prompt with blanks to fill: hover a highlight to see why each part is there, copy the blank template, and fill in your own details. Some cards teach how to use a skill from the library above; others stand on their own. Every skill in the library has a card on its detail page; the cards below are a sample. <a href="https://github.com/ericmjl/skills/tree/main/skills/prompt-card">The prompt-card skill</a> explains the format.</p>
  {prompt_cards}
</section>
</main>
<script id="skills-data" type="application/json">{skills_json}</script>
<script>{INDEX_SCRIPT}{COPY_SCRIPT}</script>"""
    return page_shell("ericmjl · agent skills",
                      f"A library of {len(skills)} agent skills for coding agents, plus prompt cards that teach how to use them.",
                      body)


def main() -> None:
    skills = [Skill(p) for p in sorted(SKILLS_DIR.glob("*/SKILL.md"))]
    cards_by_skill: dict[str, list[dict]] = {}
    for card in CARDS:
        if card["skill"]:
            cards_by_skill.setdefault(card["skill"][0], []).append(card)

    if OUT.exists():
        shutil.rmtree(OUT)
    cards_out = OUT / "cards"
    cards_out.mkdir(parents=True)

    skills_json = json.dumps([s.search_row() for s in skills]).replace("</", "<\\/")
    (OUT / "index.html").write_text(index_page(skills, skills_json), encoding="utf-8")

    for card in CARDS:
        target = cards_out / f"{card['slug']}.html"
        shutil.copy(card["src"], target)
        target.write_text(strip_fit(target.read_text(encoding="utf-8")), encoding="utf-8")

    for skill in skills:
        page_dir = OUT / "skills" / skill.name
        page_dir.mkdir(parents=True)
        (page_dir / "index.html").write_text(
            skill_page(skill, cards_by_skill.get(skill.name, [])), encoding="utf-8")

    shutil.copy(OVERVIEW_SRC, OUT / "overview.html")

    print(f"Built {len(skills)} skill pages, "
          f"{len(CARDS)} prompt cards into {OUT}/")


if __name__ == "__main__":
    main()
