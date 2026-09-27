---
name: codebase-study-parallel-reporters
description: >-
  Study an unfamiliar codebase (or audit a feature across repos) by dispatching PARALLEL READ-ONLY reporter subagents in a SINGLE tool block, NOT by reading files one-at-a-time in the main thread. Use when the user says 'study how X works', 'audit the codebase', 'understand the architecture', 'investigate the repo', 'read these files and report', hands you a file/line-range/grep list to examine, or asks to compare how two repos implement the same feature. Each reporter gets: a focused concern, a specific file list to read IN FULL, a numbered-question output template, a hard file_path:line citation requirement, and a markdown-brief format. CRITICAL: if your plan names 2+ files to examine, put ALL read/grep/dispatch calls in ONE tool block THIS turn — never announce the next read without executing it. Synthesis guidance in the body.
created_at: "2026-07-26"
---

# Codebase Study via Parallel Reporters

Study an unfamiliar codebase (or audit how a feature is implemented across a
repo) by dispatching PARALLEL READ-ONLY reporter subagents in a SINGLE tool
block. Do NOT read files one-at-a-time in the main thread with narration
between each.

## When to use

The user asks any of:
- "study how X wires / implements Y"
- "audit the codebase" / "understand the architecture"
- "investigate the repo" / "read these files and report"
- "give me a thorough, code-quoting technical breakdown of ..."
- hands you a list of files / line-ranges / grep commands to examine
- asks to compare how two repos implement the same feature

The user will often pre-digest the exploration for you: exact file paths,
line ranges (e.g. "a1.py lines 350-587"), grep commands, and a numbered
report outline. This is a gift — execute against it immediately, do not
re-deliberate.

## The critical discipline (anti-narration)

**If your plan names 2+ files or sources to examine, put ALL of the
read / grep / subagent-dispatch calls in ONE tool block THIS turn.**

The #1 failure mode is the announce-read-narrate-next-read loop:

> Turn 1: "Let me start by exploring the repo. I'll dispatch parallel
>  searches." (zero tool calls)
> Turn 2: "Let me read all the requested files in parallel. I'll start by
>  reading all the requested files." (zero tool calls — DOUBLED narration)
> Turn 3: "Now let me dispatch parallel reads." (zero tool calls)
> User: "Take action now."

Each announcement of intent that does not resolve into a tool call forces the
user to interrupt and do the work themselves. ACT, then report. End the turn
with tool calls, not with a description of intended tool calls.

## Procedure

### 1. Decompose into orthogonal concerns

Split the investigation into N focused, non-overlapping concerns. Examples for
an agent-framework study:
- core agent loop + message handling
- LLM / dependency layer (which SDK, hard dep vs optional extra)
- the specific feature under study (MCP consumption, MCP exposure, HITL, tools)
- default / built-in tool registry
- tests and usage examples

### 2. Dispatch one READ-ONLY reporter subagent per concern, ALL IN ONE BLOCK

Each reporter subagent prompt MUST specify:
- **Scope**: the single concern it owns (reporters must not overlap).
- **Files to read IN FULL**: exact paths and line ranges the user supplied,
  plus any the reporter should discover via glob/grep.
- **Optional discovery globs**: e.g. directory shape, import graphs.
- **Numbered-question output template**: the structured questions the reporter
  must answer, in order.
- **Citation contract**: every claim MUST cite `file_path:line_number`. No
  uncited assertions.
- **Output format**: a markdown brief.
- **READ-ONLY**: the reporter reports findings; it does not edit anything.

Reporters are READ-ONLY so they can run concurrently without conflicting with
each other or with the main thread. Partition concerns so no two reporters
read-edit the same files.

### 3. Synthesize, do not relay

Collect the reporters' briefs and synthesize them into a single answer that
addresses the user's original questions. Resolve contradictions between
reporters by re-reading the cited lines yourself.

## Output contract

The final synthesized answer is a markdown brief structured around the user's
numbered questions (or the standard breakdown if the user did not supply one):
dependency, direction(s) of data flow, the relevant method signatures quoted
with line numbers, the failure modes, and the concrete takeaways.

## Related

- Global AGENTS.md rules: Parallelism-via-Subagents, Verification-via-Subagents.
- Memory #1796 (the positive workflow this skill codifies), #1797 and #1769
  (the narration-without-action failure mode this skill counteracts), #59
  (read full files not just diffs).

## dispatch-shape-discipline

- When the batch spans MANY items (quiz questions, files, lint warnings, doc sections — not just codebase study), partition the items into K SUBSETS of ~2-4 items each and dispatch K reporter subagents in ONE tool block. Two distinct defects to avoid, both flagged by user correction 2026-08-02 (sgbs-training Lesson 2 quiz audit: 'you did sequential, and each one only did one question, that was wrong, it has gotta be parallel subagents, each handling a small subset for review'): (1) SEQUENTIAL dispatch — subagents fire one-after-another (each returns before the next is issued) instead of all-at-once in a single tool block; (2) ONE-ITEM-per-subagent — N subagents each auditing a single item wastes per-subagent overhead and is the wrong shape for large batches. The correct shape is subset-partitioned SINGLE-BLOCK dispatch: inventory all items, group into K subsets, issue K Task calls in ONE assistant turn. Do NOT narrate 'let me inventory first... let me count... let me read AGENTS.md...' across sequential turns before dispatching — that announce-inventory-narrate-next-step loop is the #152 failure mode and forces a 'Take action now' interrupt. Supersedes the earlier 'one read-only subagent per question' phrasing (now outdated for multi-item audits).

## Reporter-prompt execution line (subagents do not inherit loaded skills)

- Add to EVERY reporter subagent prompt, alongside the scope/files/citation contract: an explicit execution-discipline line - 'Open your reply with the read tool calls; do not restate the task, plan the chunking, or narrate; reads first, then analysis.' Reason (observed 2026-08-28, learn-anything transcript-research dispatch): subagents do NOT inherit the parent session's loaded skills, so the anti-narration discipline that fires in the main agent does nothing inside the reporter - a subagent handed a complete prompt (exact path, chunking guidance included) still opened with 'Let me read the file. It is ~61KB, so I should read it in full, possibly in chunks. Let me start reading.' (zero calls, drew 'Take action now'). Even explicit prompt instructions ('use offset/limit chunks') get restated as prose unless the prompt forbids narration outright. The dispatch prompt is the dispatcher's only channel into the subagent's context - spend one sentence of it on the discipline.

## Second-wave supporting reads (2026-08-29)

- The one-block rule extends PAST the required file list: when the required reading surfaces references needed for citation accuracy (constants modules, sibling implementation files, meta/config files), do NOT deliberate about whether they are in scope — a read-only reporter may read anything — dispatch those reads in the same turn you notice them. 'I should also read X to answer Q3 accurately' must be immediately followed by the read calls for X in that same message, never by scope-weighing prose that ends the turn. Instance 2026-08-29: a CPO reporter completed its 5-file required list, then burned an entire turn debating three additional reads and ended on 'Now checking the supporting constants and Stripe action layer...' with zero calls, drawing a 'Take action now' interrupt.

## Trigger details (from pre-compression description, preserved verbatim)

Study an unfamiliar codebase (or audit how a feature is implemented across a repo) by dispatching PARALLEL READ-ONLY reporter subagents in a SINGLE tool block, NOT by reading files one-at-a-time in the main thread. Use when the user says 'study how X works', 'audit the codebase', 'understand the architecture', 'investigate the repo', 'read these files and report', 'give me a technical breakdown of how X is implemented', hands you a list of files/line-ranges/grep commands to examine, or asks to compare how two repos implement the same feature. Each reporter subagent gets: (a) a focused concern (core impl, dependency layer, API surface, test patterns), (b) a specific list of files to read IN FULL, (c) a numbered-question output template, (d) a hard file_path:line_number citation requirement for EVERY claim, and (e) a markdown-brief output format. The CRITICAL discipline: if your plan names 2+ files/sources to examine, put ALL read/grep/subagent-dispatch calls in ONE tool block THIS turn — never announce the next read without executing it (the announce-read-narrate-next-read loop is the #1 failure mode and forces a user 'Take action now' interrupt). Synthesize the reporters' briefs into the final answer.
created_by: autolearn
