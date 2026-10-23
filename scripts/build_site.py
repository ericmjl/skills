# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Build the ericmjl/skills landing site into _site/.

Scans skills/*/SKILL.md for frontmatter, generates a searchable index page,
copies the prompt-card standalone widgets, and bundles the agent-skills
overview deck. Run with: uv run scripts/build_site.py
"""

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
NEW_CARDS_DIR = ROOT / "site" / "cards"
EXAMPLE_CARDS_DIR = SKILLS_DIR / "prompt-card" / "assets" / "examples"
OVERVIEW_SRC = ROOT / "docs" / "agent-skills-overview.html"
OUT = ROOT / "_site"
REPO_URL = "https://github.com/ericmjl/skills"
SKILL_TREE_URL = f"{REPO_URL}/tree/main/skills"

# Prompt cards embedded on the page, in display order.
# fields: slug, title, blurb, source path, taught skill (name, tree url or None)
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

TRIGGER_MARKERS = (" Use when", " Use this", " Use it", " Triggers", " Also use", " Also triggers")
BLURB_MAX = 220


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing frontmatter")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError(f"{path}: unterminated frontmatter")
    meta = yaml.safe_load(text[3:end])
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    return meta


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def short_blurb(description: str) -> str:
    """Description up to the first trigger clause, else the first sentence."""
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


def load_skills() -> list[dict]:
    skills = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        meta = parse_frontmatter(skill_md)
        name = str(meta.get("name") or skill_md.parent.name)
        description = str(meta.get("description") or "")
        if not description:
            raise ValueError(f"{skill_md}: empty description")
        skills.append(
            {
                "name": name,
                "blurb": short_blurb(description),
                "full": normalize(description),
                "url": f"{SKILL_TREE_URL}/{name}",
            }
        )
    return skills


def card_block(card: dict, index: int) -> str:
    skill_chip = ""
    if card["skill"]:
        sname, surl = card["skill"]
        skill_chip = (
            f'<p class="card-teaches">Teaches the skill '
            f'<a href="{surl}">{html.escape(sname)}</a></p>'
        )
    else:
        skill_chip = '<p class="card-teaches">Teaches: your vault ingestion conventions</p>'
    return f"""<div class="card-embed" id="card-{card["slug"]}">
  <div class="card-embed-head">
    <h3>{html.escape(card["title"])}</h3>
    <a class="standalone-link" href="cards/{card["slug"]}.html" target="_blank" rel="noopener">open standalone ↗</a>
  </div>
  <p class="card-blurb">{html.escape(card["blurb"])} {skill_chip}</p>
  <iframe src="cards/{card["slug"]}.html" width="100%" scrolling="no" loading="lazy" style="border:0" title="Prompt card: {html.escape(card["title"])}" onload="this.style.height=this.contentDocument.body.scrollHeight+'px'"></iframe>
</div>"""


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ericmjl · agent skills</title>
<meta name="description" content="A library of $skill_count agent skills for coding agents, plus prompt cards that teach how to use them.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧰</text></svg>">
<style>
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

header.site {
  background: var(--heading);
  color: #f2f7f5;
  padding: 56px 24px 48px;
}
header.site .wrap { max-width: 1040px; margin: 0 auto; }
header.site h1 { font-size: 2.4rem; letter-spacing: -0.02em; }
header.site h1 .repo { color: #cfe89a; font-family: var(--mono-font); font-weight: 600; }
header.site p.tagline { font-size: 1.15rem; max-width: 46rem; margin-top: 10px; color: #dcebe4; }
header.site nav { margin-top: 22px; display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.95rem; }
header.site nav a { color: #ffffff; text-decoration: none; border-bottom: 1px dashed rgba(255,255,255,0.55); padding-bottom: 1px; }
header.site nav a:hover { border-bottom-style: solid; border-bottom-color: #cfe89a; }

.install {
  margin-top: 26px; display: inline-flex; align-items: stretch; gap: 0;
  background: #0b4d38; border: 1px solid rgba(255,255,255,0.25); border-radius: 8px; overflow: hidden;
}
.install code { font-family: var(--mono-font); font-size: 0.95rem; padding: 10px 14px; color: #eaf5ee; }
.install button {
  border: none; cursor: pointer; background: var(--accent2); color: #16210c;
  font-family: var(--body-font); font-weight: 600; font-size: 0.9rem; padding: 0 16px;
}
.install button.ok { background: #cfe89a; }

main { max-width: 1040px; margin: 0 auto; padding: 48px 24px 24px; }
section { margin-bottom: 64px; }
h2 {
  font-size: 1.6rem; color: var(--heading); margin-bottom: 6px; letter-spacing: -0.01em;
}
.section-sub { color: var(--muted); margin-bottom: 22px; max-width: 52rem; }
.section-sub a { color: var(--accent); }

/* skills grid */
.search-row { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
#search {
  flex: 1 1 280px; max-width: 420px; font-size: 1rem; padding: 10px 14px;
  border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--fg);
}
#search:focus { outline: 2px solid var(--accent2); border-color: var(--accent2); }
#count { font-size: 0.9rem; color: var(--muted); font-family: var(--mono-font); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.skill-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px 16px 12px;
  display: flex; flex-direction: column; gap: 8px; transition: border-color 0.15s;
}
.skill-card:hover { border-color: var(--accent); }
.skill-card.hidden { display: none; }
.skill-card h3 { font-size: 0.95rem; font-family: var(--mono-font); color: var(--heading); word-break: break-word; }
.skill-card p { font-size: 0.88rem; color: #33413c; flex: 1; }
.skill-card a { font-size: 0.8rem; color: var(--muted); text-decoration: none; font-family: var(--mono-font); }
.skill-card a:hover { color: var(--accent); text-decoration: underline; }
.no-results { display: none; color: var(--muted); font-size: 0.95rem; padding: 12px 0; }

/* prompt cards */
.card-embed { margin-bottom: 40px; }
.card-embed-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.card-embed h3 { font-size: 1.15rem; color: var(--heading); }
.standalone-link { font-size: 0.85rem; color: var(--muted); text-decoration: none; font-family: var(--mono-font); }
.standalone-link:hover { color: var(--accent); text-decoration: underline; }
.card-blurb { font-size: 0.95rem; color: #33413c; margin: 4px 0 12px; max-width: 52rem; }
.card-teaches { display: inline; margin: 0; }
.card-teaches a { color: var(--accent); font-family: var(--mono-font); font-size: 0.88rem; }

footer.site {
  border-top: 1px solid var(--border); color: var(--muted); font-size: 0.85rem;
  padding: 24px; text-align: center;
}
footer.site a { color: var(--accent); }
footer.site .mono { font-family: var(--mono-font); }
</style>
</head>
<body>

<header class="site">
  <div class="wrap">
    <h1>Agent skills <span class="repo">ericmjl/skills</span></h1>
    <p class="tagline">A library of $skill_count skills that teach coding agents to do real, repeatable work — review pull requests, run ML experiments, build marimo notebooks, make charts whose point is evident, and more. Free to install, MIT licensed.</p>
    <div class="install"><code id="install-cmd">npx skills add ericmjl/skills</code><button type="button" id="install-copy">Copy</button></div>
    <nav>
      <a href="https://github.com/ericmjl/skills">GitHub repository</a>
      <a href="overview.html">What are agent skills?</a>
      <a href="#prompt-cards">Prompt cards</a>
    </nav>
  </div>
</header>

<main>
<section id="skills">
  <h2>The skills</h2>
  <p class="section-sub">Every skill is a folder with a <span class="mono">SKILL.md</span> that an agent loads on demand. Search by name or by what you want done; each card links to its source.</p>
  <div class="search-row">
    <input type="search" id="search" placeholder="Search skills… e.g. review, notebook, vault" autocomplete="off">
    <span id="count"></span>
  </div>
  <div class="grid" id="grid">$skill_cards</div>
  <p class="no-results" id="no-results">No skills match that search.</p>
</section>

<section id="prompt-cards">
  <h2>Prompt cards</h2>
  <p class="section-sub">A prompt card teaches one fill-in prompt: hover a highlight to see why each part is there, copy the blank template, and fill in your own details. Some cards teach how to use a skill from the library above; others stand on their own. <a href="https://github.com/ericmjl/skills/tree/main/skills/prompt-card">The prompt-card skill</a> explains the format.</p>
  $prompt_cards
</section>
</main>

<footer class="site">
  <p>$skill_count skills · built $build_date · MIT licensed · deployed with GitHub Actions · <a href="$repo_url">source</a></p>
</footer>

<script id="skills-data" type="application/json">$skills_json</script>
<script>
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

  var btn = document.getElementById('install-copy');
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
</script>
</body>
</html>
"""


def main() -> None:
    skills = load_skills()
    if OUT.exists():
        shutil.rmtree(OUT)
    cards_out = OUT / "cards"
    cards_out.mkdir(parents=True)

    skill_cards = "\n".join(
        f"""<div class="skill-card" data-name="{html.escape(s["name"])}">
  <h3>{html.escape(s["name"])}</h3>
  <p>{html.escape(s["blurb"])}</p>
  <a href="{s["url"]}">skills/{html.escape(s["name"])} ↗</a>
</div>"""
        for s in skills
    )
    prompt_cards = "\n".join(card_block(c, i) for i, c in enumerate(CARDS))

    page = (
        TEMPLATE.replace("$skill_cards", skill_cards)
        .replace("$prompt_cards", prompt_cards)
        .replace("$skills_json", json.dumps(skills).replace("</", "<\\/"))
        .replace("$skill_count", str(len(skills)))
        .replace("$build_date", date.today().strftime("%b %-d, %Y"))
        .replace("$repo_url", REPO_URL)
    )
    (OUT / "index.html").write_text(page, encoding="utf-8")

    for card in CARDS:
        shutil.copy(card["src"], cards_out / f"{card['slug']}.html")
    shutil.copy(OVERVIEW_SRC, OUT / "overview.html")

    print(f"Built {len(skills)} skills and {len(CARDS)} prompt cards into {OUT}/")
    for s in skills:
        print(f"  {s['name']}: {s['blurb'][:90]}")


if __name__ == "__main__":
    main()
