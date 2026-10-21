---
cssclasses:
  - landing-page
---

```dataviewjs
// Landing page for a flat vault: an index note plus raw/, MOCs/ and evergreen/.
// Edit CONFIG to match your folder names. Everything below only reads the vault.
const CONFIG = {
  index: "Index",          // note that lists your maps as "- [[Map]] - description"
  raw: "raw",              // raw sources
  mocs: "MOCs",            // maps of content
  evergreen: "evergreen",  // evergreen notes
  freshDays: 7,            // a map gets a fresh dot if it or a linked note changed this recently
  chipLimit: 8,            // chips per recent-activity row
};

try {
  const now = dv.date("now");
  const inFolder = (p, folder) => p.file.folder === folder || p.file.folder.startsWith(folder + "/");
  const pages = dv.pages();
  const raw = pages.where((p) => inFolder(p, CONFIG.raw)).array();
  const mocs = pages.where((p) => inFolder(p, CONFIG.mocs)).array();
  const evergreen = pages.where((p) => inFolder(p, CONFIG.evergreen)).array();

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const link = (p, label) =>
    `<a class="internal-link" data-href="${esc(p.file.path)}" href="${esc(p.file.path)}">${esc(label ?? p.file.name)}</a>`;
  const short = (s, n = 36) => (s.length > n ? s.slice(0, n - 1) + "\u2026" : s);
  const outPaths = (p) => new Set((p.file.outlinks ?? []).map((l) => l.path));
  const changedWithin = (p, days) => p.file.mtime && p.file.mtime >= now.minus({ days });

  // Links, not frontmatter: what each map links to, and what each evergreen cites.
  const mocLinks = new Map(mocs.map((m) => [m.file.path, outPaths(m)]));
  const mapped = new Set();
  for (const s of mocLinks.values()) for (const x of s) mapped.add(x);
  const cited = new Set();
  for (const e of evergreen) for (const x of outPaths(e)) cited.add(x);
  const unmapped = evergreen.filter((e) => !mapped.has(e.file.path));
  const uncited = raw.filter((r) => !cited.has(r.file.path));

  // Momentum: files changed this week vs. the week before, by modified time.
  const tracked = [...raw, ...mocs, ...evergreen];
  const week = tracked.filter((p) => changedWithin(p, 7)).length;
  const prevWeek = tracked.filter((p) => changedWithin(p, 14) && !changedWithin(p, 7)).length;
  const delta = week - prevWeek;
  const days14 = [...Array(14)].map((_, i) => {
    const d0 = now.minus({ days: 13 - i }).startOf("day");
    return tracked.filter((p) => p.file.mtime >= d0 && p.file.mtime < d0.plus({ days: 1 })).length;
  });
  const sparkSvg = (vals) => {
    const W = 140, H = 30, mx = Math.max(...vals, 1);
    const pts = vals.map((v, i) => [(i / (vals.length - 1)) * W, H - 2 - (v / mx) * (H - 6)]);
    const line = pts.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" ");
    return `<svg class="lp-spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><polygon class="lp-spark-fill" points="0,${H} ${line} ${W},${H}"/><polyline class="lp-spark-line" points="${line}"/></svg>`;
  };

  // Map order and descriptions come from the "- [[Map]] - description" list items in the index.
  const index = dv.page(CONFIG.index);
  const order = [];
  const blurbs = new Map();
  for (const l of index?.file.lists ?? []) {
    const m = String(l.text ?? "").match(/^\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]\s+[-\u2013\u2014]\s+(.+)$/s);
    if (!m) continue;
    const moc = mocs.find((p) => p.file.name === m[1].split("/").pop().trim());
    if (moc && !order.includes(moc)) { order.push(moc); blurbs.set(moc.file.path, m[2].split("\n")[0].trim()); }
  }
  // Maps the index doesn't list come after, by name, so a new map never disappears.
  for (const m of [...mocs].sort((a, b) => a.file.name.localeCompare(b.file.name))) {
    if (!order.includes(m)) order.push(m);
  }

  const byPath = new Map(pages.array().map((p) => [p.file.path, p]));
  const mapCards = order.map((m) => {
    const targets = [...mocLinks.get(m.file.path)].map((x) => byPath.get(x)).filter(Boolean);
    const ev = targets.filter((p) => inFolder(p, CONFIG.evergreen)).length;
    const rw = targets.filter((p) => inFolder(p, CONFIG.raw)).length;
    const fresh = [m, ...targets].some((p) => changedWithin(p, CONFIG.freshDays));
    const edited = m.file.mtime ? m.file.mtime.toFormat("yyyy-MM-dd") : "";
    return `<div class="lp-card lp-map" title="${esc(`${targets.length} links out · edited ${edited}`)}">
      <div class="lp-map-head">${fresh ? `<span class="lp-dot" title="Changed in the last ${CONFIG.freshDays} days"></span>` : ""}${link(m)}</div>
      ${blurbs.has(m.file.path) ? `<div class="lp-map-blurb">${esc(blurbs.get(m.file.path))}</div>` : ""}
      <div class="lp-map-counts"><span>${ev} evergreen</span><span>${rw} raw</span></div>
    </div>`;
  }).join("");

  const stat = (label, value, sub, extra = "") => `<div class="lp-card lp-stat">
      <div class="lp-stat-label">${esc(label)}</div>
      <div class="lp-stat-value">${esc(value)}</div>
      <div class="lp-stat-sub">${esc(sub)}</div>${extra}</div>`;

  const newest = (list, key) => [...list].sort((a, b) => b.file[key] - a.file[key]);
  const chips = (title, list, key, empty) => `<div class="lp-row">
      <div class="lp-row-title">${esc(title)}</div>
      <div class="lp-chips">${list.length
        ? newest(list, key).slice(0, CONFIG.chipLimit).map((p) =>
            `<span class="lp-chip">${link(p, short(p.file.name))}<span class="lp-chip-date">${p.file[key] ? p.file[key].toFormat("MM-dd") : ""}</span></span>`).join("")
        : `<span class="lp-empty">${esc(empty)}</span>`}</div></div>`;

  dv.container.innerHTML = `<div class="lp">
    <header class="lp-header">
      <div class="lp-title">${esc(dv.current().file.name)}</div>
      <div class="lp-totals">${mocs.length} maps · ${evergreen.length} evergreen notes · ${raw.length} raw sources · ${now.toFormat("yyyy-MM-dd HH:mm")}</div>
    </header>
    <section class="lp-grid lp-stats">
      ${stat("Maps", mocs.length, `${blurbs.size} listed in ${CONFIG.index}`)}
      ${stat("Evergreen notes", evergreen.length, `${unmapped.length} not on any map`)}
      ${stat("Raw sources", raw.length, `${uncited.length} not yet cited by an evergreen`)}
      ${stat("Momentum", week, `${delta >= 0 ? "+" : ""}${delta} vs. prior week`, sparkSvg(days14))}
    </section>
    <div class="lp-section">Maps</div>
    <section class="lp-grid lp-maps">${mapCards || '<div class="lp-empty">No maps yet.</div>'}</section>
    <div class="lp-section">Recent activity</div>
    <section class="lp-card lp-activity">
      ${chips("New raw sources", raw, "ctime", "No raw sources yet.")}
      ${chips("Recently touched evergreens", evergreen, "mtime", "No evergreen notes yet.")}
      ${chips("Not on any map", unmapped, "mtime", "Every evergreen note is on a map.")}
    </section>
  </div>`;
} catch (e) {
  dv.paragraph("Landing page failed to render: " + e.message);
}
```
