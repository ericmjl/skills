---
name: blog-explainer-prose-dedup
description: >-
  Tighten long-form explainer/pedagogical blog prose by auditing for facts and concepts stated 2+ times across sections and condensing each to a single mention with forward-references. Use when the user says 'less repetitive', 'more pedagogically coherent', 'too repetitive', 'this restates what was already said', 'tighten the prose', or flags a concept explained multiple times (intro re-explains, body re-derives, later section re-states). ALSO governs the INVERSE coverage problem: a takeaway/summary that UNDER-represents the post's actual deep arc — use when the user says 'the takeaway doesn't reflect what we went deep into' or 'this summary is generic'. Distinct from coherent-writing (transitions/flow): THIS governs information redundancy across sections AND summary-coverage fidelity. The dedup technique, takeaway-coverage rewrite, redundancy patterns, and summary-drift failure mode live in the body.
created_at: "2026-08-04"
---

# Blog Explainer Prose Dedup

Tighten long-form explainer / pedagogical / educational blog prose by auditing for facts and concepts stated 2+ times across sections and condensing each to a single mention with forward-references. Use when the user says 'less repetitive', 'more pedagogically coherent', 'too repetitive', 'this restates what was already said', 'tighten the prose', asks to reduce redundancy across sections of a technical/educational blog post, tutorial, or explainer, or flags that a concept was explained multiple times (intro re-explains it, body re-derives it, later section re-states it). Distinct from coherent-writing (which governs TRANSITIONS and FLOW between paragraphs/sections — smooth the connections) — THIS governs INFORMATION REDUNDANCY across sections (the same fact appearing 2-3 times in different wording). The technique: (1) READ the full post and index every fact/concept to the sections that mention it; (2) for each fact mentioned 2+ times, identify its BEST home (where it is first needed or most fully explained); (3) CUT the redundant mentions, replacing them with forward-references or back-references ('which is where we head next', 'the Bloch circle already showed this', 'as planted in the intro') so the reader is oriented without re-reading an explanation; (4) verify the post still reads coherently — the concept must be reachable from every section that needs it via the cross-reference, not orphaned. Use a PLANT/HARVEST structure: the intro PLANTS a seed (one sentence foreshadowing), the main section USES it (the full explanation), a later section HARVESTS it (applies it to a new case) — each mention serves a distinct rhetorical purpose, never re-explanation. Common redundancy patterns to audit for: (a) TRIPLE-STATED SIGNIFICANCE — a key property (e.g. 'amplitudes are signed') stated in the geometric intro, restated in the main section, re-explained in a later section; fix = state once in its proper home, forward-reference elsewhere; (b) RE-DERIVED SQUARING — measurement probability = amplitude² re-derived in multiple sections when one earlier widget/section already demonstrated it; fix = reference the earlier demonstration, do not re-derive; (c) RE-STATED WIDGET COVERAGE — prose re-describing what an interactive widget on the same page already shows; fix = point at the widget, trim the prose. Verify heading arc coherence after edits: the section headings should form a clean narrative arc (e.g. Fundamentals → Many qubits → Probability view → Entanglement → Interference → Takeaway) with no heading left orphaned by its section's trimmed content.

## Instructions

Apply the dedup audit when tightening an explainer/pedagogical blog post. Work in five passes.

### Pass 1 — Index every fact to its sections

Read the full post and build a mental (or scratch) index: for each fact, concept, or mechanism, note which sections mention it. A fact mentioned in 2+ sections is a dedup candidate.

### Pass 2 — For each repeated fact, decide its BEST home and cut the rest

For each fact mentioned 2+ times, identify where it is FIRST NEEDED or MOST FULLY explained — that is its home. Cut the other mentions. Replace each cut mention with a forward-reference or back-reference ('which is where we head next', 'the Bloch circle already showed this', 'as planted in the intro') so the reader stays oriented without re-reading an explanation. Use a PLANT/HARVEST structure: the intro PLANTS a seed (one foreshadowing sentence), the main section USES it (full explanation), a later section HARVESTS it (applies to a new case) — each mention serves a distinct rhetorical purpose, never re-explanation.

### Pass 3 — Widget-prose redundancy (the highest-leverage cut when the post has interactive widgets)

When the post embeds interactive widgets (sliders, drag-rotate diagrams, butterfly diagrams, bar tracks), the prose SURROUNDING a widget must do ORIENTATION work, not EXPLANATION work. The widget IS the equation, visualized — do not re-derive in symbols what the widget shows interactively. Apply the BEFORE/AFTER orientation scaffolding:

- BEFORE the widget: frame in plain words what the widget does ('blends the two input amplitudes together, with a minus sign baked into one of the blends') and tell the reader what to look for ('watch for reinforcement vs cancellation in the butterfly diagram'). No equations.
- AFTER the widget: walk the reader through ONE concrete interactive case ('drag to 45 degrees, look at the butterfly, watch positive + positive reinforce, positive + negative cancel'), then invite exploration of other states. The only 'math' allowed is in words ('positive + positive = reinforce').

Watch for the ENGINE-PARAGRAPH anti-pattern: a dense summary paragraph placed right after a widget that re-explains the mechanism the reader just interacted with (e.g. 'This is the engine that does the work... phase flips... recombination...'). Trim the re-explained mechanism (the widget showed it); keep only the core insight that does NOT appear in the widget (e.g. 'gates arrange interference to concentrate amplitude on good answers and cancel the rest'). Distilled from the quantum-ML-for-Bayesians post edits (2026-08-07): the 'This is the engine...' paragraph repeated the Hadamard widget's phase-flip/recombination demonstration in prose; the fix kept the one-sentence core (gates arrange interference) and cut the redundant re-derivation.

### Pass 4 — Heading-arc coherence + buried-thesis rescue

After trimming, verify the section headings form a clean narrative arc with no heading orphaned by its trimmed content (e.g. Fundamentals → Many qubits → Probability view → Entanglement → Interference → From interference to answers → Takeaway).

Watch for the BURIED-THESIS-PARAGRAPH pattern: the post's KEY thesis paragraph (the 'why the reader should care' bridge — e.g. 'If you are a Bayesian, frame it like this...') wedged between a dense mechanism summary and a personal payoff reflection, with no visual separation. When you find it, PROMOTE it to its own ### section (e.g. `### From interference to answers`) so the MECHANISM section (how it works) and the PAYOFF section (why it matters to the reader) are cleanly separated. A thesis buried between two paragraphs reads as digression; the same thesis under its own heading reads as structure. This is the structural fix that makes a trimmed post cohere — do not leave a trimmed section's thesis dangling. (quantum-ML-for-Bayesians post, 2026-08-07: the Bayesian-bridge paragraph was buried between the engine summary and the MCMC payoff; promoting it to `### From interference to answers` fixed the arc.)

### Pass 5 - Takeaway / summary coverage alignment (the inverse of dedup)

The INVERSE failure mode of dedup: a takeaway/summary/conclusion/'walk away with' section that UNDER-represents the post's actual deep arc. The signature is SUMMARY DRIFT - the takeaway was last edited before the post's body went deep, so it names only the GENERIC frame ('a quantum state is a probability distribution', 'this is about sampling problems') while omitting the load-bearing mechanisms the post actually argues (amplitudes-as-signed-arrow, entanglement-as-non-factorizability, interference-as-reinforcement/cancellation, gates-shaping-the-distribution).

Procedure when revising a takeaway (or when the user flags 'the takeaway doesn't reflect what we went deep into'):
1. RE-READ the post's actual section arc in order (e.g. amplitudes -> many qubits -> entanglement -> interference -> gates -> measurement -> Bayesian parallel). Do NOT trust the existing takeaway as the spec - it is the thing being audited.
2. For each DEEP section in the arc, write ONE building-block sentence that names the section's contribution in the post's own vocabulary (arrow on a unit circle, cannot be split into one circle per qubit, signed amplitudes reinforce or cancel). A generic synonym ('probability distribution') that omits the mechanism is the failure.
3. Keep the closing personal/payoff paragraph, but anchor it in the post's actual vocabulary (e.g. update 'sampling problems' to 'amplitude vectors, clever encodings, and interference doing the heavy lifting'), not a stale generic.
4. Mirror the Bayesian/connection paragraph with a STRUCTURAL ECHO if the post makes a structural parallel: 'Your prior and likelihood shape a posterior; a quantum circuit's gates shape amplitudes. You sample from your posterior; you measure from the quantum state.' The echo only works if it uses the post's real terms.

Distinct from Pass 2 (dedup): Pass 2 removes REPEATED facts; Pass 5 adds MISSING coverage to a summary. They compose - first dedup the body, then ensure the takeaway faithfully compresses the (now-trimmed) body. Stated 2026-08-07 on the quantum-ML-for-the-probabilistic-Bayesian post: user flagged 'the takeaway section doesn't seem to reflect what we went deep into'; the rewrite mirrored the full arc.

### Common redundancy patterns to audit for

(a) TRIPLE-STATED SIGNIFICANCE — a key property (e.g. 'amplitudes are signed') stated in the geometric intro, restated in the main section, re-explained in a later section; fix = state once in its proper home, forward-reference elsewhere.
(b) RE-DERIVED SQUARING — measurement probability = amplitude² re-derived in multiple sections when one earlier widget/section already demonstrated it; fix = reference the earlier demonstration, do not re-derive.
(c) RE-STATED WIDGET COVERAGE — prose re-describing what an interactive widget on the same page already shows; fix = replace the prose with BEFORE/AFTER orientation scaffolding (Pass 3), do not just delete it. Deleting alone leaves the reader disoriented; the scaffolding re-purposes the freed space to teach how to USE the widget.
