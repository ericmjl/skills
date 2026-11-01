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

## 2026-11-01 (run trigger: schedule)
- Searched: Exa web searches (new Nature Methods Points of View 2026
  columns; IEEE VIS/TVCG/CHI 2024–2026 truncation, labeling, and guideline-
  evaluation studies; uncertainty-display studies 2023–2026; pie-vs-bar
  comparisons; dual-axis empirical studies; Datawrapper Academy 2025–2026);
  direct fetches: nature.com column pages, author OA PDFs (alvitta.com),
  eScholarship (CogSci OA full text), ETH Research Collection, Taylor &
  Francis abstract page, Datawrapper blog; Crossref lookups for every
  candidate DOI (+ DataCite for the CogSci repository DOI, Unpaywall for the
  Computers & Education journal version).
- Findings: 4 — (1) INT1: added [MO26] (CHI '26; three experiments, N=62/57/
  60): truncation harm concentrates in ratio judgments; direct value labels
  mitigate it (tag unchanged); (2) TXT1: added supporting cite [MO26] —
  value labels reduced error and time across tasks (tag unchanged);
  (3) INT2: added [RR24] (CogSci 2024, 68 analyzed): inverted y-axes ≈7× and
  dual axes ≈6× lower odds of a correct reading — first direct experimental
  support for the inverted-axes and dual-axes bans (tag unchanged); (4) ENC2:
  extended with interval-proportional tick spacing citing [RR24] (unevenly
  spaced time steps, OR≈15.4, was the largest measured deception effect).
  Source-only additions: five relaunched POV columns (JL26-Click, LJ26-Code,
  JD26-GraphAbs, JR26-Engaging, BJ26-Companion, all paywalled, no rule
  change yet) and [Ch20] [UNVERIFIED] watch item (no comprehension advantage
  of direct vs indirect annotation labels in news graphics; candidate TXT1
  nuance — needs full-text read before any rule change).
- PR: n/a (branch research/dataviz-2026-11-01; URL to be appended after
  opening the PR)
