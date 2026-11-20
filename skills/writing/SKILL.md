---
name: writing
description: >-
  Use for ANY writing or drafting task for the user: emails, blog posts, docs,
  READMEs, tutorials, notebook markdown, video scripts, handoffs, PR
  descriptions, or any other prose. This skill is a short router: it names
  the writing passes to run and which specialized skill to load for the job.
  Load it before producing text, then load the specific skills it names
  instead of improvising. Also use when the user asks to write, draft, revise,
  edit, proofread, or "make this sound better."
license: MIT
---

# Writing

## Usage

Load this skill before you write or revise any prose for the user. Then load
the specialized skills named below and follow them. Do not invent your own
writing checklist when one of those skills already covers the job.

## Requirements

- The writing skills this router names should be available in the skills
  library. If a named skill is missing, skip it and say so; still run every
  other pass that is present.
- A voice or slop skill such as `write-like-eric` is optional. Load it when
  it is installed (often in a private library). Do not invent a voice
  profile if it is not.

## What It Does

This skill does not rewrite the draft on its own. It tells you which
writing skills to load, in what order, and which one is the main skill
for the kind of document you are writing.

## How It Works

### Pass order

Run these passes in this order. Each pass catches a different class of
problem; later passes should not undo earlier ones.

1. **Coherence** — `coherent-writing`. Fix conflicts in the argument, logic
   jumps inside paragraphs, and weak transitions. Do this first so later
   cuts do not hide a broken line of thought.
2. **Dedup** — `blog-explainer-prose-dedup`, when the draft is a long
   explainer, tutorial, or pedagogical post (or a close cousin, such as a
   long notebook write-up). Give each fact one home and check that the
   takeaway covers what the piece actually went deep on. Skip this pass
   for a short email or a brief handoff unless the text repeats itself.
3. **Voice and slop** — a voice skill such as `write-like-eric`, when it is
   available. Match the user's voice and remove known slop. If no voice
   skill is installed, skip this pass rather than guessing.
4. **Processing-friendly prose** — `processing-friendly-prose`, always last.
   Unpack stacked nouns, keep optional "that", keep subjects close to
   their verbs, and prefer ordinary wording. Dedup and compression can
   pack sentences; this pass repairs that.

If the user asked only for one of these passes, still load that skill and
consider a final `processing-friendly-prose` read.

### Which skill leads, by job

Load the router first, then the skill that owns the document type, then
the remaining passes in the order above.

- **Blog or explainer post** — start with `coherent-writing` and
  `blog-explainer-prose-dedup`. End with `processing-friendly-prose`.
- **Notebook markdown or experiment write-up** — write the narrative in
  place (see also `awesome-marimo-notebook` or `ml-experimentation` when
  those skills apply). Then run `coherent-writing` and
  `processing-friendly-prose` on the markdown cells and prose. Use
  `blog-explainer-prose-dedup` if the write-up is long and repeats facts.
- **Video script** — `video-script-writing` owns hook, pacing, spoken
  register, and retention. After the script is drafted, run
  `processing-friendly-prose` as a speakability check.
- **Handoff** — `handoff` owns the file structure and length budget. Do
  not compress by stacking nouns or dropping "that". Run
  `processing-friendly-prose` if a section has become dense.
- **Email, PR description, README, docs, or other short prose** —
  `coherent-writing` for flow, then voice if available, then
  `processing-friendly-prose`. Skip explainer dedup unless the text is
  long and repeats itself.

### Do not improvise

Load the skill that applies and follow its checklist. If two skills could
apply, load both; do not merge them from memory. If you are unsure which
skill to use, load this router and the last pass, `processing-friendly-prose`.
