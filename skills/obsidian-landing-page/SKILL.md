---
name: obsidian-landing-page
description: "Build a polished DataviewJS landing page for an Obsidian knowledge vault: a header with totals, four to six stat cards, one card per map of content with linked note counts and a fresh dot, and recent-activity chip rows, styled by a CSS snippet scoped to one cssclass. Built for the simple base structure of an index note plus flat raw/, MOCs/ and evergreen/ folders, and adapts when folder names differ. Use when someone asks for a landing page, home page, dashboard, or start page for their vault. Triggers include 'build a landing page for my vault', 'make my vault a home page', 'add a dashboard to Obsidian', or 'make my vault's front page look nice'."
license: MIT
---

# Obsidian landing page

## Usage

Use this skill when someone wants one note that opens their vault: what's in it, what's moving, and where to go next. The steps live here, so the user only needs a short prompt such as "Build a landing page for my <name of vault> please."

Ask for these when missing:

- Which vault, and where it lives on disk.
- The look they want, as a mood or a few colors. If they have no preference, follow the active theme.
- Where the landing page note should go. Default to a new `Landing Page.md` at the vault root.

## The vault this skill expects

The base structure is deliberately simple:

- An index note (often `Index.md`) that lists each map as a line like `- [[Map]] - description`.
- `raw/`, a flat folder of raw sources such as clipped articles, transcripts, and papers.
- `MOCs/`, a flat folder of maps of content. Maps organize the vault by linking out.
- `evergreen/`, a flat folder of evergreen notes. Evergreen notes link one way to the raw sources they draw on, and to each other.
- Raw sources never cite evergreen notes.

Every number on the page comes from links and file metadata, never from custom frontmatter. That keeps the page working in any vault with this shape. If the folder names differ, or a folder is missing, inspect the vault and ask the user which folder plays which role before you write any query. Don't rename or move their folders.

## Safety rules

- Treat the vault as read-only until step 4. Only then create the snippet and the landing page note.
- Never edit an existing note, including the index. The landing page is a new note.
- Change `.obsidian/` config files only after the user approves the exact change, and back each one up first. Prefer that the user clicks the setting in Obsidian.
- Don't install plugins yourself. Ask the user to install them from Community plugins.
- The dataviewjs block only reads the vault and renders HTML. Never load and run code stored in another note or file, and never use `eval` or `new Function`. A block that executes note text runs whatever someone pastes into that note.

## The eight steps

### 1. Inspect the vault read-only

Run `scripts/vault_stats.py` on the vault:

```bash
python3 scripts/vault_stats.py /path/to/vault
```

Pass `--raw`, `--mocs`, `--evergreen`, or `--index` if the names differ. It prints:

- Note counts per top-level folder.
- The most common frontmatter keys and tags, so you know what not to depend on.
- The map lines it found in the index note, and their descriptions.
- Enabled community plugins, whether Dataview is installed and JavaScript queries are on, and which CSS snippets exist and are enabled.
- The link-based numbers the starter page shows: maps, evergreen notes not on any map, raw sources not yet cited by an evergreen, per-map counts, and momentum.

Also list `.obsidian/snippets/` and read any snippet whose name suggests a dashboard, so you don't collide with it. If `raw_sources_that_link_to_evergreens` isn't empty, tell the user. It breaks the one-way rule, and the page will still count it as normal.

### 2. Pick four to six stat cards

Each card should come from one simple query that a reader could check by hand. Start from these defaults:

| Card | Value | Subtitle |
|------|-------|----------|
| Maps | Notes in `MOCs/` | How many are listed in the index |
| Evergreen notes | Notes in `evergreen/` | "N not on any map", meaning no map links to them |
| Raw sources | Notes in `raw/` | "N not yet cited by an evergreen", meaning no evergreen links to them |
| Momentum | Files changed in the last 7 days | Change against the 7 days before, plus a 14-day sparkline |

Add a fifth or sixth card only if the user asks or the vault clearly has another kind of note worth counting. Tell the user plainly that momentum uses file modified time, so it counts any change to a file: a sync, a rename that rewrote links, or a plugin touching frontmatter, not just real edits.

### 3. Make sure Dataview can run JavaScript

The page needs the Dataview community plugin with JavaScript queries on. Check `.obsidian/community-plugins.json` for `dataview`, and `.obsidian/plugins/dataview/data.json` for `"enableDataviewJs": true`.

If either is missing, ask the user to fix it in Obsidian:

1. Settings, Community plugins, Browse, search Dataview, Install, then Enable.
2. Settings, Dataview, turn on Enable JavaScript queries.

If they would rather you edit `data.json`, show them the exact change, get approval, back the file up, make the change, and ask them to reload Obsidian. Obsidian can overwrite a config file it already has open. Re-read `data.json` afterwards to confirm the setting stuck.

### 4. Write and enable a CSS snippet

Copy `assets/landing-page.css` to `.obsidian/snippets/landing-page.css`. If that name is taken, pick another and change the cssclass to match. Every rule is scoped under one cssclass, `landing-page`, in both `.markdown-source-view` (Live Preview) and `.markdown-preview-view` (Reading view), so nothing leaks into other notes. The snippet:

- Paints a soft backdrop on this view only, so no other pane or sidebar shows it.
- Sets `--file-line-width: 100%`, the official knob for line length, and clears the leftover width rail on `.cm-sizer`, `.cm-content`, and `.markdown-preview-sizer`, so the page uses the full pane.
- Hides the inline title, the properties block, the code block edit and copy buttons, and Dataview's toolbar, and drops the embed block border, on this note only.
- Draws frosted panels with `backdrop-filter`.
- Lays out grids with `minmax(0, 1fr)`, so long titles can't blow a column out. Container queries reflow the cards when the pane is narrow, not just the window.
- Lifts cards a little on hover, and turns that off under `prefers-reduced-motion`.
- Styles the 14-day sparkline, a line with a soft fill.

Set the user's look by changing the `--lp-` variables at the top. The defaults use theme variables such as `--interactive-accent`, so the page follows light and dark mode.

Enable the snippet. Ask the user to turn it on in Settings, Appearance, CSS snippets, after clicking reload. Or, with approval, back up `.obsidian/appearance.json` and add the snippet name, without `.css`, to `enabledCssSnippets`.

### 5. Write the dataviewjs block

Create the landing page note from `assets/landing-page.md`. Its frontmatter sets `cssclasses: [landing-page]`, and it holds one `dataviewjs` block. Edit `CONFIG` at the top for the user's folder and index names.

How the block is built, and what to keep if you change it:

- It builds one HTML string and assigns it to `dv.container.innerHTML`, all inside a `try`/`catch`. On error it calls `dv.paragraph("Landing page failed to render: " + e.message)`, so a broken query shows a readable message instead of a blank note.
- `esc()` escapes every value that goes into the HTML, including note names, which can contain `&`, `<`, or quotes.
- Links are `<a class="internal-link" data-href="path" href="path">`, so Obsidian opens them in the vault and shows hover previews.
- The header shows totals for maps, evergreen notes, and raw sources.
- The stat cards follow step 2.
- Dates use `dv.date("now")` and Luxon, the date library Dataview ships with, so week and day boundaries follow the user's clock.
- Map order and descriptions come from the index note's `- [[Map]] - description` list items, read through `dv.page(CONFIG.index).file.lists`. Nothing reads files directly. Maps the index doesn't list come after, in alphabetical order, so a new map never disappears.
- Each map card shows how many evergreen notes and raw sources the map links to, and a fresh dot if the map or anything it links to changed in the last `freshDays` days.
- Everything is counted from `file.outlinks`, `file.folder`, `file.mtime`, and `file.ctime`. No frontmatter.

### 6. Add recent-activity chip rows

Below the map cards, the starter block adds three rows of linked chips, capped at `chipLimit` each:

- New raw sources, newest first by creation time.
- Recently touched evergreens, newest first by modified time.
- Evergreen notes not on any map, so the user can see what needs a home.

Each chip shows a short date, and long names are cut at 36 characters. Each row shows a short message when it's empty. Creation time can reset when files are copied or synced, so mention that if the order looks wrong.

### 7. Verify that it renders

Have the user open the note in Reading view or Live Preview, then check:

- No "Landing page failed to render" message, and no Dataview error.
- The counts match `vault_stats.py`. Spot-check at least one map card by opening the map and counting its links.
- Clicking a map title and a chip opens the right note.
- The page still reads well in a narrow pane. Ask the user to drag the pane narrow, or open the note in a sidebar.
- Other notes look unchanged, which proves the snippet is scoped.

If you can't see the screen, ask the user for a screenshot of the full page and one of the narrow pane. Don't call the page done from the code alone.

### 8. Iterate on the look one change at a time

Make one visual change per round, such as the accent color, card radius, or grid columns, then ask for a fresh screenshot. Change the `--lp-` variables first, then rules. Keep the snippet's rules scoped under `.landing-page`. Back up the snippet and the note before each round, so any change can be undone.

## Gotchas

- A CSS comment that contains a path glob like `notes/*/x.md` ends the comment at `*/` and silently drops the next rule.
- `dv.pages()` includes the landing page and the index. Count by folder, as the starter does, so they don't inflate the numbers.
- A link that doesn't resolve to a note has no matching path, so it won't count toward any map. Mention unresolved links if a map's count looks low.
- Dataview reindexes as files change, but a stale page can follow a big sync. Reopening the note re-runs the block.
- Some themes paint their own background on the note view. That's why the backdrop rule uses `!important`. Leave it scoped to the cssclass.

## Files

- `assets/landing-page.md`: the starter landing page note, with `cssclasses: [landing-page]` and the dataviewjs block.
- `assets/landing-page.css`: the starter CSS snippet, scoped to the `landing-page` cssclass.
- `scripts/vault_stats.py`: a read-only survey of the vault for steps 1 and 7. Standard library only.
