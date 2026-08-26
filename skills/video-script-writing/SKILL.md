---
name: video-script-writing
description: >-
  Write and revise video scripts that hold viewer attention to the end and
  drive the desired action, grounded in retention and persuasion research
  (information-gap curiosity, Zeigarnik open loops, hook-concreteness studies,
  narrative transportation, speech-rate and scene-cut experiments). Use when
  the user asks for a video script, YouTube script, or explainer script; a
  founder, brand-story, or talking-head video; a landing-page, marketing,
  demo, or testimonial video; a video ad or VSL; or a short-form script
  (Shorts, Reels, TikTok). Also use when improving an existing script's hook,
  pacing, retention, or CTA, or when asked whether a script will hold
  attention. Covers hook tests, loop architecture, spoken-register drafting,
  production specs (cut rhythm, captions, words-per-minute bands, placement),
  and per-purpose playbooks with benchmarks.
license: MIT
---

# Video Script Writing

Retention-first script writing for any video purpose. The script is the
product; production quality is secondary. A rough, real, well-structured
script beats a polished script with weak architecture.

Distilled 2026-08-26 from the Learn Anything founder-video session plus a
research pass over hook studies, curiosity psychology, narrative
transportation, speech-rate experiments, and eye-tracking editing research.
Full citations: `references/research-digest.md`.

## Pair with

- A voice skill for the speaker's prose voice (e.g. write-like-eric) when
  writing as a specific person; the script must survive a table read.
- marketing-copy for offer construction and persuasion strategy upstream.
- eric-video (or the production pipeline du jour) when the script moves to
  rendering; this skill ends at the script plus its production spec.

## Step 1 — Intake (ask before drafting)

- Purpose (founder story, conversion, explainer, short-form, demo)?
  Selects the playbook.
- Where does it live (by a form, YouTube, feed)? Placement, CTA shape,
  captions.
- Who watches, and what is their ONE unresolved doubt? The video exists
  to kill that doubt; without one, recommend against a video.
- Length budget? Sets loop spacing and wpm math.
- Whose voice, and what evidence/receipts do they own? Numbers come from
  the speaker's own verifiable material.
- The single action after watching? One CTA per script, no exceptions.

## Step 2 — Choose the playbook

Read the matching section of `references/purpose-playbooks.md` BEFORE
drafting:

| Purpose | Length | Primary metric |
| --- | --- | --- |
| Founder / brand story | 2 to 3 min | Trust + waitlist/signup |
| Landing-page conversion | 60 to 90 s | Conversion lift vs no video |
| YouTube explainer / education | 5 to 10 min | Retention curve shape |
| Short-form (Shorts/Reels/TikTok) | 15 to 60 s | Completion + rewatch |
| Demo / testimonial | 60 to 120 s | Doubt killed, next step taken |

## Step 3 — Architecture: draw the loop map first

Before writing prose, produce a loop map table (loop, where it opens, where
it closes). Rules, all research-backed (see digest):

- One macro loop: opens in the first 15 seconds, closes in the final 20
  percent. Closing it early collapses the reason to keep watching.
- Mid loops at section boundaries; micro-satisfactions (a payoff, a number, a
  reveal, a laugh) at least every 10 to 15 seconds of script.
- At most 2 loops open concurrently; more overloads working memory.
- Every loop CLOSES by the end. Unresolved loops read as betrayal and damage
  the next video too (Zeigarnik works on grudges).
- Place a deliberate re-engagement beat (stakes escalation, specificity
  injection, perspective shift, social proof) at 20 to 30 percent of word
  count: the known flat zone where momentum fades before commitment sets in.
- A single curiosity gap holds pull for 3 to 4 minutes max; renew or resolve.
- Cognitive load ceiling: 4 to 5 new concepts per minute; break any section
  past ~300 words; prefer adversative transitions ("but", "the catch") over
  additive ones ("also", "next").
- Peak-end: put the best moment near the end and end warm with one specific
  next action, never on a summary or a subscribe beg (viewers skip closings,
  thanks, and subscribe prompts; this is measured).

## Step 4 — The hook (first 15 seconds)

Draft the opening last, against the actual promise. It must pass all three
tests (349-video hit-vs-flop study):

1. Reason test: a concrete reason to keep watching (claim, result, question,
   or stake) lands within ~15 seconds. "Today we talk about X" is a topic,
   not a reason.
2. Number test: one real, checkable figure early. Hits carry numbers 63% vs
   52% in flops. Pull it from the speaker's own verified material.
3. Promise test: the opening engages the exact promise the title/thumbnail
   or page headline made. Never open adjacent to it.

Failure modes to strike on sight: context dumps (background before a reason
to care; a quarter of all flops), greetings ("hey everyone, welcome back"),
and promise-only openers ("stick around and I'll show you" asks for credit;
give instead).

Mechanics: make the stake second person ("you") where honest; size the gap
right (enough context to make the gap visible, not so much it self-closes;
curiosity follows an inverted-U); explanatory gaps ("I know what, not why")
pull 2 to 3x longer than surface gaps ("what happens next").

Null finding, keep in mind: within the normal delivery band, speaking pace
and speed-to-point do NOT separate hits from flops. Concreteness does. Do
not fix a weak hook by talking faster.

## Step 5 — Draft in spoken register

- Write for the mouth: short speakable sentences, contractions, no
  semicolon-prose, no written-register curriculum-speak. Read every line
  aloud mentally; if the speaker wouldn't say it to a friend, rewrite.
- Target the purpose's wpm band (playbooks table). Persuasion is curvilinear
  in rate: moderately brisk wins, slow reads as low-competence, frantic
  overloads. Trim dead air in the edit instead of rushing delivery.
- Concrete receipts over adjectives: real numbers, named events, owned
  evidence ("I did X, here is the artifact").
- Vary sentence lengths; land thesis sentences as their own short sentence.
- If the user rejects drafts as "not my voice", stop generating variants and
  ask them to dictate or table-read; their spoken phrasing is authoritative
  and gets spliced near-verbatim.

## Step 6 — Attach the production spec

Every script ships with a spec block (the retention levers live in the edit
as much as the words):

- Visual change (cut, b-roll, overlay, angle, micro-zoom) at least every 4
  to 7 seconds; every extra second of an unchanged scene measurably drops
  attentional focus. No static 5-second windows anywhere in the plan.
- Put each key line immediately AFTER a visual change: attention peaks about
  two-thirds of a second after a cut. Hold important on-screen elements at
  least 1 second, centered, uncluttered (visual complexity depresses focus).
- Seamless jump cuts (dead-air removal) for fluency; use sparing overlap
  only to re-engage, and never chase cut-speed for its own sake (sustained
  attention falls at high transition frequency).
- Burn in captions, always: most mobile viewers watch muted and captioned
  videos finish far more often. The script must work captions-only.
- Click-to-play with a face-forward custom thumbnail; sound-on autoplay
  never. Lazy-load the player so the page CTA renders first.
- Landing/conversion surfaces: video sits beside the CTA, the CTA stays
  visible on a 375px screen when the video ends, video stays ungated, end
  screen points at the single next action.

## Step 7 — Pre-ship verification

- [ ] Muted test: the whole argument survives captions alone.
- [ ] Math: per-section word counts over timestamps land inside the wpm band.
- [ ] Loop map complete; every loop closed; never more than 2 concurrent.
- [ ] Hook passes reason, number, and promise tests within 15 seconds.
- [ ] Exactly one CTA; the end screen or closing line points at it.
- [ ] No planned static window over 5 seconds; key lines follow cuts.
- [ ] Claims audit: promise only what the offerer controls; no invented
      urgency; numbers verified against the speaker's own material.
- [ ] Table read done by the actual speaker; flagged lines rewritten in
      their dictated phrasing.

## Step 8 — Measure after launch

Strong completion targets by length: under 5 min, 65 to 75 percent; 5 to 10
min, 50 to 60; 10 to 15 min, 40 to 50. Embedded conversion video: 60 to 75
percent completion is strong. Cliffs cluster in the first 15 seconds (hook)
and at the 25 to 35 percent mark (missing re-engagement beat); when a cliff
appears, fix that moment, not the whole script.

## Honesty rules

- Video is conversion-neutral ON AVERAGE across landing pages (large
  dataset). It pays when it kills the named doubt from Step 1; otherwise it
  is weight on the page. A/B test rather than assume lift.
- No curiosity bait the video does not pay off inside the video. The
  resolution lives in the watch, never in a caption, comment, or "part 2".
- Do not over-cut. Diminishing returns are real; processing takes time;
  scenes under one second cannot encode.
- Engagement is not conversion. Judge the script by the action it produces.
