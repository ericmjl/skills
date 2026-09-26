# Research protocol — how this skill gets updated from the literature

This file is the operating manual for the literature-research agent: the
scheduled GitHub Actions run (`.github/workflows/dataviz-research.yml`) that
executes the `pi` coding agent headlessly, and any human or agent doing a
hand-run literature update. Follow it exactly. It is versioned with the skill,
so PRs may propose changes to this protocol too — flag them clearly in the PR
body.

## Mission

Keep the skill's rules backed by current, verifiable literature: find new
evidence for existing rules, add new rules when the literature supports them,
and demote or annotate rules whose evidence has been contradicted — with a
citation for every change.

## Scope

- Allowed paths: `skills/data-visualization-master/**` — nothing else. In
  particular, never edit `skills/evident-charts/**` (upstream-owned; see the
  repo README) or any workflow file.
- Typical run: 0–5 rule changes and 0–10 source additions. A run that finds
  nothing solid must produce a no-change report, not filler.

## Inputs (read in this order)

1. This file.
2. `SKILL.md` — the current rules and tags.
3. `references/sources.md` — the current bibliography.
4. `references/research-log.md` — recent runs; don't repeat what a recent run
   already covered.

## Search strategy

Search the literature with the available web tools (Exa MCP `web_search_exa`
when configured; fall back to fetching known venues directly). Rotate focus
across runs so coverage stays broad:

1. **Nature Methods Points of View**: check for new columns in the series
   (after the 2010–2016 corpus) and citations/corrections to existing ones.
2. **Peer-reviewed venues**: IEEE TVCG, CHI, EuroVis, IEEE VIS, Computer
   Graphics Forum, JASA, Psychological Science in the Public Interest, PLOS
   Computational Biology.
3. **Preprints with caution**: arXiv (cs.HC, stat.AP). May be added only with
   the `(preprint)` mark and must not upgrade a rule to `[E]`.
4. **Practitioner sources** (for `[P]` rules): Datawrapper blog, Economist
   Graphic Detail, FT Visual Vocabulary, Urban Institute style guide, BBC
   bbplot, UK Government Analysis Function.
5. **Replications and contradictions** of rules already in `SKILL.md` — these
   are the highest-value findings.

Good queries pair a technique with a perceptual outcome ("truncated y-axis
misreading replication", "direct labeling vs legend accuracy study", "color
viz CVD accessibility evaluation 2025").

## What qualifies as a finding

- A source you have actually fetched and read (at minimum, abstract + the
  section that supports the claim). Never cite from a snippet alone.
- A resolvable DOI (verify via `https://api.crossref.org/works/<DOI>` or a
  Crossref bibliographic query) or, for practitioner sources, a stable URL
  with publisher and date.
- A claim that changes or supports a rule in `SKILL.md`, with enough method
  detail to state it honestly (sample, task, effect size when available).

Disqualifiers: aggregator re-posts, marketing blog posts about a vendor's
product, and sources whose full text you could not reach (mark those
`[UNVERIFIED]` and leave them out of rule changes).

## Update procedure

1. **Propose rule changes** in `SKILL.md` using the existing format:
   `- ID [tag] rule text. Cite: [keys]; POV: [keys].` One line per rule. New
   rule IDs continue the existing family (MSG, ENC, COL, LAY, TXT, INT, STO,
   FIG, ACC) with the next number.
2. **Tag changes are evidence changes**: `[T]`→`[P]` or `[P]`→`[E]` requires a
   new citation supporting the stronger tag; downgrading a tag or removing a
   rule requires the contradicting citation and a one-line `Note:` in
   `references/research-log.md`.
3. **Add source entries** to `references/sources.md` in the existing format
   (`- [KEY] Authors year, Title, Venue. https://doi.org/...` + provenance
   mark). Keys are stable and never repurposed. For new Points of View
   columns, also add the column to `references/points-of-view.md`.
4. **Keep the diff small**: at most ~30 changed lines in `SKILL.md` per run.
   If a finding implies more, propose the highest-value subset and note the
   remainder in the log.
5. Never paraphrase a source into a stronger claim than it makes. If a study
   found an effect in one task type, the rule says that.

## PR procedure

1. Branch from the current default branch: `research/dataviz-<YYYY-MM-DD>`
   (append `-2`, `-3` on same-day collisions).
2. Commit with message: `research(dataviz): <one-line summary of findings>`.
3. Append the run record to `references/research-log.md` (format at the top of
   that file) — include it in the same commit.
4. Push the branch and open a PR to the default branch with `gh`:
   - Title: `research(dataviz): <date> — <N> finding(s)`
   - Body must contain: **Findings** (one bullet per finding: claim, rule
     touched, old tag → new tag), **Sources added** (key + full citation),
     **Verification** (how each source was checked: fetched + Crossref
     confirmed), **Nothing changed** section when proposing no rule changes,
     and **Out of scope / deferred** items.
5. Never merge, never approve, never rebase others' branches, never push to
   the default branch.

## No-change report

If nothing qualifies: make no commits, open no PR, and end the run with a
short report: what was searched (venues, queries), why candidates were
rejected, and anything worth watching next run. Append nothing to the log.
The workflow captures this as the job summary.

## Escalation

If the workflow's guardrail step fails (out-of-scope diff), or a source cannot
be verified but seems important, say so in the run output — a human decides
what to do with it.
