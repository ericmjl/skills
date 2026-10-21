#!/usr/bin/env python3
"""Read-only survey of an Obsidian vault for the obsidian-landing-page skill.

Prints per-folder note counts, common frontmatter keys and tags, the map lines in
the index note, installed plugins and CSS snippets, and the same link-based
numbers the starter landing page shows, so you can spot-check the rendered page.

Usage:
    python3 vault_stats.py /path/to/vault [--index Index] [--raw raw] [--mocs MOCs] [--evergreen evergreen]

Standard library only. Never writes to the vault.
"""
import argparse
import collections
import json
import re
import time
import urllib.parse
from pathlib import Path

WIKILINK = re.compile(r"!?\[\[([^\]|#^]+)(?:[#^][^\]|]*)?(?:\|[^\]]*)?\]\]")
MDLINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+\.md)(?:#[^)]*)?\)")
INDEX_LINE = re.compile(r"^\s*[-*]\s*\[\[([^\]|#]+)[^\]]*\]\]\s*(?:[-:\u2013\u2014]\s*)?(.*)$")
TAG = re.compile(r"(?:^|\s)#([A-Za-z0-9_/-]*[A-Za-z_/-][A-Za-z0-9_/-]*)")
DAY = 86400


def split_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[4:end], text[end + 4 :]
    return "", text


def frontmatter_keys(fm):
    return [m.group(1) for m in re.finditer(r"^([A-Za-z0-9_-]+):", fm, re.M)]


def strip_code(body):
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", body)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("--index", default="Index")
    ap.add_argument("--raw", default="raw")
    ap.add_argument("--mocs", default="MOCs")
    ap.add_argument("--evergreen", default="evergreen")
    a = ap.parse_args()
    root = Path(a.vault).expanduser().resolve()

    notes = sorted(p for p in root.rglob("*.md") if not any(part.startswith(".") for part in p.relative_to(root).parts))
    rel = {p: p.relative_to(root).as_posix() for p in notes}
    by_name = collections.defaultdict(list)
    for p, r in rel.items():
        by_name[p.stem.lower()].append(r)
    all_rel = set(rel.values())

    def resolve(target, src):
        t = urllib.parse.unquote(target).strip()
        if t.lower().endswith(".md"):
            t = t[:-3]
        if "/" in t:
            cand = (Path(src).parent / (t + ".md")).as_posix() if t.startswith(".") else t + ".md"
            cand = Path(cand).as_posix()
            if cand in all_rel:
                return cand
            t = t.split("/")[-1]
        hits = by_name.get(t.lower(), [])
        return sorted(hits, key=len)[0] if hits else None

    def top(p):
        parts = rel[p].split("/")
        return parts[0] if len(parts) > 1 else "(vault root)"

    folder_counts = collections.Counter(top(p) for p in notes)
    fm_keys, tags, outlinks = collections.Counter(), collections.Counter(), {}
    for p in notes:
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, body = split_frontmatter(text)
        fm_keys.update(set(frontmatter_keys(fm)))
        clean = strip_code(body)
        tags.update(TAG.findall(clean))
        links = set()
        for m in WIKILINK.finditer(clean):
            r = resolve(m.group(1), rel[p])
            if r:
                links.add(r)
        for m in MDLINK.finditer(clean):
            r = resolve(m.group(1), rel[p])
            if r:
                links.add(r)
        outlinks[rel[p]] = links

    def in_folder(r, folder):
        return r == folder or r.startswith(folder.rstrip("/") + "/")

    raw = [r for r in all_rel if in_folder(r, a.raw)]
    mocs = [r for r in all_rel if in_folder(r, a.mocs)]
    ever = [r for r in all_rel if in_folder(r, a.evergreen)]
    mapped = set().union(*(outlinks[m] for m in mocs)) if mocs else set()
    cited = set().union(*(outlinks[e] for e in ever)) if ever else set()
    raw_citing_ever = [r for r in raw if outlinks[r] & set(ever)]

    now = time.time()
    mtime = {rel[p]: p.stat().st_mtime for p in notes}
    tracked = raw + mocs + ever
    this_week = sum(1 for r in tracked if now - mtime[r] < 7 * DAY)
    last_week = sum(1 for r in tracked if 7 * DAY <= now - mtime[r] < 14 * DAY)
    today = time.mktime(time.localtime(now)[:3] + (0, 0, 0, 0, 0, -1))
    spark = [sum(1 for r in tracked if today - (13 - i) * DAY <= mtime[r] < today - (12 - i) * DAY) for i in range(14)]

    index_lines = []
    idx = [r for r in all_rel if Path(r).stem.lower() == a.index.lower()]
    if idx:
        for line in (root / sorted(idx, key=len)[0]).read_text(encoding="utf-8", errors="replace").splitlines():
            m = INDEX_LINE.match(line)
            if m:
                index_lines.append({"link": m.group(1).strip(), "description": m.group(2).strip()})

    obs = root / ".obsidian"
    def load(path, default):
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    dataview = load(obs / "plugins" / "dataview" / "data.json", {})
    report = {
        "vault": str(root),
        "notes_per_top_folder": dict(folder_counts.most_common()),
        "common_frontmatter_keys": dict(fm_keys.most_common(15)),
        "common_tags": dict(tags.most_common(15)),
        "index_note": idx[0] if idx else None,
        "index_map_lines": index_lines,
        "enabled_plugins": load(obs / "community-plugins.json", []),
        "dataview_installed": (obs / "plugins" / "dataview").is_dir(),
        "dataview_js_enabled": dataview.get("enableDataviewJs", False),
        "css_snippets": sorted(p.name for p in (obs / "snippets").glob("*.css")) if (obs / "snippets").is_dir() else [],
        "enabled_css_snippets": load(obs / "appearance.json", {}).get("enabledCssSnippets", []),
        "folders_used": {"raw": a.raw, "mocs": a.mocs, "evergreen": a.evergreen},
        "counts": {"mocs": len(mocs), "evergreen": len(ever), "raw": len(raw)},
        "evergreen_not_on_any_map": len([e for e in ever if e not in mapped]),
        "raw_not_cited_by_an_evergreen": len([r for r in raw if r not in cited]),
        "raw_sources_that_link_to_evergreens": sorted(raw_citing_ever)[:20],
        "per_map": {Path(m).stem: {"evergreen": len(outlinks[m] & set(ever)), "raw": len(outlinks[m] & set(raw))} for m in sorted(mocs)},
        "momentum_by_mtime": {"this_week": this_week, "last_week": last_week, "last_14_days": spark},
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
