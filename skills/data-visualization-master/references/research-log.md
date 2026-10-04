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

## 2026-10-04 (run trigger: schedule)
- Searched: Crossref sweeps (Jambor/Nature Methods 2026 works; CHI 2024
  truncation record; TVCG 2025–2026 empirical sweep; CGF/EuroVis 2025–2026
  sweep; bibliographic query for the MASSVIS complexity paper); Exa web
  search (new Points of View columns; Hill 2024 pie-chart full text;
  2024–2026 truncated-axis replications; IEEE VIS/TVCG 2025–2026
  best-practice papers; Datawrapper blog); nature.com pages of the four new
  columns; official SAGE mirror (sage.cnpereading.com) for Hill 2024; ACM
  DL record and author PDF for Song et al.
- Findings: 4 — (1) sources.md + points-of-view.md: four new "Points of
  View, anew" columns (J26-Click, J26-Code, J26-GraphAbs, J26-Engaging)
  added; Crossref-verified with standfirsts read; paywalled, so no rule
  changes from them. (2) ENC1: added [H24] Hill 2024 — now verified (full
  text via open-access SAGE mirror; [UNVERIFIED] lifted): pies/donuts equal
  to bars for part-whole extraction, worse for ranking near-equal segments,
  slower; tag unchanged. (3) INT1: added [LK24] Long & Kay CHI 2024 —
  truncation spares absolute-difference accuracy; harm concentrates in
  perceived relative change and non-monotonic truncation; [E] tag kept,
  nuance recorded in sources.md. (4) LAY4: added [SC25] Song et al.
  TVCG/VIS 2025 — decorative embellishments (cartoon bars, hand-drawn
  fonts) lower perceived credibility; tag unchanged.
- Deferred: CHI EA 2025 MASSVIS complexity analysis (correlational — would
  over-claim to base rules on it); Datawrapper dual-axis guide (2026-07,
  practitioner nuance on INT2, no experimental contradiction); TVCG 2026
  icon-array perception paper (no rule family maps to it yet); full texts
  of the five 2026 POV columns for future distillation.
- PR: https://github.com/ericmjl/skills/pull/45
