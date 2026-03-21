# Skill `description` field = trigger text

Agents load **only** `name` and `description` from every skill before choosing what to read. The `description` is therefore the **entire** trigger: if it is vague, the skill will not run when it should; if it is too broad, it will fire on the wrong tasks.

Official references:

- [Agent Skills specification — `description` field](https://agentskills.io/specification#description-field)
- [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) (testing and tuning triggers)

## What a strong `description` contains

1. **Capabilities** — What the skill actually does (concrete verbs and outcomes), in one or two short clauses.
2. **When to use it** — Imperative phrasing aimed at the agent: *Use when …* / *Use this skill when …* (not only “This skill helps with …”).
3. **User intent and phrasing** — Phrases users say (corrections, “from now on”, file names, tools, URLs) so matching does not depend on one magic keyword.
4. **Scope hints** — Optional: adjacent tasks that sound similar but are **out of scope**, to reduce false triggers (see optimizing-descriptions “near-miss” negatives).

Keep the whole field under **1024 characters** (spec hard limit). Prefer one tight paragraph over a long bullet list in YAML.

## Anti-patterns (common when using skill-creator alone)

| Weak pattern | Why it fails |
|--------------|----------------|
| “Guide for …” or “Helps with …” only | Does not tell the agent **when** to load the skill. |
| Repeating the skill `name` | Adds no new matching signal. |
| Generic “for developers” / “best practices” | Matches nothing specific in the user message. |
| Putting “When to use” **only** in the body | Body is not visible until **after** the skill is chosen; triggers must live in `description`. |

## Checklist before you consider the skill done

- [ ] Removed any init placeholder / `[TODO` text from `description`.
- [ ] Wrote **3–5 example user requests** that should trigger the skill; the `description` clearly covers them (including informal wording).
- [ ] Included **concrete anchors**: file names, tools, hosts, or deliverable types where relevant.
- [ ] Read the `description` in isolation: would another agent pick this skill without seeing the body?

## Optional: eval queries

For skills where triggering is business-critical, collect ~20 labeled prompts (should trigger / should not) and run them through your agent client, as described in [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions). Revise `description` using train/validation splits so you do not overfit single phrases.
