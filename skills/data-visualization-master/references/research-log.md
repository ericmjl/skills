# Research log

Append-only record of literature-research runs for this skill. The CI research
agent appends one block per PR-producing run (inside the run's commit); a
no-change run appends nothing.

Format:

```
## YYYY-MM-DD (run trigger: schedule|dispatch)
- Searched: <venues/queries covered>
- Findings: <N> — <one line each: rule touched, change, key added>
- PR: <url|n/a>
```

## Initial state

Bibliography seeded 2026-09-26 by hand (Eric + agent): complete Nature Methods
Points of View corpus (43 columns, DOIs resolved against Crossref), plus the
foundational experimental literature. No automated runs yet.

## 2026-09-26 (run trigger: dispatch)
- Searched: Crossref venue sweeps (TVCG recent issues, CGF/EuroVis
  2024–2026, Information Visualization, Nature Methods), Crossref
  bibliographic queries (truncated axes, deceptive visualization, direct
  labeling, uncertainty communication, chart titles), Krzywinski POV
  bibliography + Nature Methods "Points of View, anew" editorial, Europe
  PMC, OpenAlex OA lookups, arXiv cs.HC, Datawrapper blog feed; JCOM and
  nature.com pages fetched directly (Exa MCP unavailable this run).
- Findings: 3 — (1) INT1: added supporting cite [WSB22] (truncated bar-chart
  axes mislead news consumers; an accurate alternative chart is the most
  effective correction; tag unchanged); (2) COL1: added [OI02] Okabe–Ito
  palette, surfaced by the 2023 Author Correction to W11-Blindness
  ("Corrected:" note added to sources.md; tag unchanged); (3) Points of View
  relaunched June 2026 under Helena Jambor — editorial and [J26-Viridis]
  added to sources.md, abstract-only stub in points-of-view.md; no rule
  change from it (full text paywalled).
- PR: n/a
