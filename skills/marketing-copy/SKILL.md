---
name: marketing-copy
description: >-
  Write, review, and critique marketing copy using proven copywriting frameworks. Use when the user asks to write or generate sales copy, headlines, bullet points, email teasers or sequences, sales letters, sales pages, landing page or hero copy, social media ad copy (Facebook, Instagram, LinkedIn), product descriptions, Amazon listings, webinar registration copy, or newsletter P.S. blocks — or says 'sell the benefits', 'marketing copy', 'persuasive', 'make it compelling', or 'advocate for X'. Also use when asked to review, critique, audit, score, or improve existing copy. Frameworks (customer avatar, headline formulas, ultimate bullet formula, PAS, subject-line patterns, offer building and risk reversal, stealth closes, hooks and angles, swipe files, newsletter P.S. formula, persona-matched CTAs, price-objection reframing) live in the body. Produces multiple variations by default.
license: MIT
---

# Marketing Copy

Frameworks adapted from Jim Edwards' *Copywriting Secrets* (31 secrets). Principles are presented as universal craft; consult the reference files for detailed templates and examples.

## Modes

| Mode | When to use | Behavior |
| ------ | ------------- | ---------- |
| Quick (default) | User wants copy now | Infer avatar and formula from context; produce immediately |
| Guided | User says "help me write" or context is thin | Ask F.R.E.D. questions first, then produce |

If critical information is missing (product, audience, desired action), ask before generating regardless of mode.

## Writing copy workflow

### 1. Gather context

Determine from the request or by asking:

- **Product/service**: What are we selling?
- **Audience**: Who is the ideal customer? (If unclear, build a F.R.E.D. avatar, see below)
- **Desired action**: What should the reader do? (Click, buy, sign up, register, reply)
- **Medium**: Where will this copy appear? (Sales page, email, ad, social post, product listing)
- **Angle/hook**: What is the main promise or curiosity trigger?

### 2. Verify factual claims (gate before persuasion)

Frameworks amplify whatever claims the copy makes, true or false. Before generating, verify every checkable claim:

- **Autobiographical claims** (the author's history, "most/half of my ..."): use only claims the author has explicitly stated about themselves, verbatim or weaker. Never convert a general statement into a first-person statistic; "that's how a lot of us found our jobs" became "Most of the jobs I've had started with someone passing something along", which Eric flagged as categorically false (2026-08-21). If no attested claim is available, write a claim-free line instead.
- **Program mechanics** (application vs waitlist, funnel stage, dates, capacity, venue, pricing, referenced pages): check the live site and use its exact terminology and CTA. "Applications have been coming in" was wrong for Learn Anything; the site funnel is "Join the waitlist" then "Applications open to the waitlist first", so the accurate claim was "the waitlist has been growing" (2026-08-21).
- **Demand and social-proof numbers**: only use stats the user supplied. "Been floored by the response" is usable color; an invented signup count is not.

If a claim cannot be verified this turn, cut it or mark it [VERIFY] for the user. A weaker true claim beats a stronger invented one.

### 3. Build the avatar (when needed)

If the audience is undefined, load [references/fred-avatar.md](references/fred-avatar.md) and run through the F.R.E.D. framework:

- **F**ears: What keeps them up at night?
- **R**eal desires: What do they actually want (not what they say they want)?
- **E**nd goals: What is the ultimate outcome they are chasing?
- **D**reams: What does success look like for them?

Also capture: demographics, where they hang out online, words and phrases they use, their objections and skepticism.

### 4. Apply the framework

Select the copy type and load the matching reference:

| Copy type | Primary reference | Key frameworks |
| ----------- | ------------------- | ---------------- |
| Headlines | [headlines-and-bullets.md](references/headlines-and-bullets.md) | Headline types, curiosity hooks |
| Bullets | [headlines-and-bullets.md](references/headlines-and-bullets.md) | Feature + Benefit + "which means..." |
| Sales letter / page | [sales-formulas.md](references/sales-formulas.md) | PAS, Benefit, Before/After/Bridge + 13-step template |
| Email teaser / sequence | [email-and-ads.md](references/email-and-ads.md) | Subject-line patterns, teaser body formula |
| Newsletter P.S. block (event/product promo) | [newsletter-ps-blocks.md](references/newsletter-ps-blocks.md) | 5-part P.S. formula, tie-in with the main post, weekly rotation guidance |
| Advocacy blog post / recurring cadence | [advocacy-and-cadence.md](references/advocacy-and-cadence.md) | Value-on-top-of-persuasion, persona CTAs, end strong |
| Social media ad | [email-and-ads.md](references/email-and-ads.md) | Hook + ad purpose + angle selection |
| Offer / bonus stacking | [offers-and-desire.md](references/offers-and-desire.md) | Desire builders, stacking, risk reversal |
| Product listing / webinar | [sales-formulas.md](references/sales-formulas.md) | Benefit-driven descriptions, registration copy |
| Video script / founder video | [video-retention-science.md](references/video-retention-science.md) | Hook, open loops, speech rate, CTA friction |

For psychology and emotional triggers, load [psychology-and-emotion.md](references/psychology-and-emotion.md).

For video scripts and timed spoken persuasion, load [video-retention-science.md](references/video-retention-science.md).

For proof elements (testimonials, credibility), load [proof-and-closes.md](references/proof-and-closes.md).

### 5. Generate variations

For headlines, bullets, subject lines, and hooks: produce **3 to 5 variations** using different angles or formulas. Label each with the technique used.

For long-form copy (sales letters, emails): produce one complete version, then offer alternative openings or headlines.

### 6. Polish

Apply the editing checklist from [swipe-and-polish.md](references/swipe-and-polish.md):

- Cut filler words and hedging language
- Tighten paragraphs (1 to 3 sentences for email and ads)
- Strengthen verbs; replace passive with active voice
- Check reading level (aim for grade 6 to 8)
- Read aloud to catch awkward phrasing

## Reviewing copy workflow

### Checklist audit (quick)

Load [review-checklist.md](references/review-checklist.md) and score the copy on a 0 to 2 scale across each dimension:

- **Headline**: Does it grab attention and create curiosity?
- **F.R.E.D. alignment**: Does it speak to the avatar's fears, desires, and language?
- **Bullets**: Are they benefit-driven (not just features)?
- **Emotion**: Does it connect emotionally before asking for action?
- **Call to action**: Is it clear, specific, and singular?
- **Proof**: Are there credibility elements?
- **Factual fidelity**: Is every checkable claim attested (the author's own words for personal claims, the live site for program mechanics, user-supplied numbers for demand)?
- **Risk reversal**: Is there a guarantee or objection handling?
- **Clarity**: Could a 12-year-old understand the offer?

Output a scored table with specific fix recommendations for anything scoring 0 or 1.

### Deep critique (thorough)

Go line by line through weak sections. For each problem:

1. Quote the problematic text
2. Identify the principle violated
3. Provide a rewritten alternative
4. Explain why the rewrite works

Offer to apply all fixes and produce a revised version.

## Key principles (always apply)

1. **People buy on emotion, justify with logic.** Lead with feeling, support with facts.
2. **It is all about them, never about you.** The reader cares about their problems, not your product features.
3. **The headline is the most important piece of copy.** If the headline fails, nothing else gets read. Spend disproportionate time here.
4. **Features tell, benefits sell.** Every feature must answer "which means..." to the customer.
5. **A confused mind says no.** Clarity beats cleverness. One message, one offer, one call to action.
6. **Risk reversal increases conversion.** Remove the buyer's risk with guarantees, trials, or bonuses.
7. **Great copy is assembled, not written.** Use proven formulas and patterns (swipe files) rather than inventing from scratch.
8. **Sequence closers preserve future optionality.** The final message of a drip/reminder sequence must convey SHORT-TERM finality ("Last note from me for now"), never permanent goodbye ("Last note from me, I promise"). A forever-goodbye closer burns the list: if a future broader campaign to the same audience is conceivable (a full-list blast when plans firm up, a relaunch, a new cohort), the graceful exit stays graceful AND revocable. When writing any "final" reminder, ask what campaigns might still target this list and scope the finality to the sequence, not the relationship. (Instance: learn-anything waitlist R3 corrected 2026-08-23 — Eric reserved a full waitlist blast for when retreat plans clear.)

9. **Lead with what the reader walks away with, not with what happens.** Copy that narrates the process or itinerary (what happens at the event, how the program works) without naming the durable takeaways and why they matter to the reader reads as a schedule, not a pitch. State the takeaways (skills, practices, theory, a repeatable method) and their personal relevance in the first breath; the process becomes the proof the promise works, not the headline. Sharpening of principle 4 for experiential offerings: the itinerary is a feature, the takeaway is the benefit. (Instance: learn-anything referral blurbs v1 rejected 2026-08-23 — "it tells what happens. It doesn't say what they take away and why this could be important for them.")

## Reference library

| File | When to load |
| ------ | ------------- |
| [fred-avatar.md](references/fred-avatar.md) | Building a customer avatar; audience is unclear |
| [headlines-and-bullets.md](references/headlines-and-bullets.md) | Writing or evaluating headlines, bullet points |
| [sales-formulas.md](references/sales-formulas.md) | Writing sales letters, sales pages, long-form copy |
| [email-and-ads.md](references/email-and-ads.md) | Writing email teasers, ad copy, social posts |
| [newsletter-ps-blocks.md](references/newsletter-ps-blocks.md) | Writing newsletter/Substack/LinkedIn P.S. blocks that promote an event or product; must tie into the post's main content |
| [advocacy-and-cadence.md](references/advocacy-and-cadence.md) | Advocacy posts, recurring promo cadences, price objections, persona-matched CTAs, copy work |
| [offers-and-desire.md](references/offers-and-desire.md) | Building offers, bonus stacks, risk reversal |
| [psychology-and-emotion.md](references/psychology-and-emotion.md) | Understanding why people buy, emotional triggers, positioning |
| [proof-and-closes.md](references/proof-and-closes.md) | Adding testimonials, stealth closes, ethical persuasion |
| [swipe-and-polish.md](references/swipe-and-polish.md) | Research methods, swipe files, editing and refinement |
| [review-checklist.md](references/review-checklist.md) | Auditing or scoring existing copy |
| [video-retention-science.md](references/video-retention-science.md) | Writing or auditing video scripts, founder videos, landing-page videos |
| [all-secrets-index.md](references/all-secrets-index.md) | Quick lookup of any of the 31 copywriting secrets |
