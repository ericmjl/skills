---
name: opencode-ollama-provider-setup
description: >-
  Add an Ollama-hosted model (local laptop or a remote box like the GB10) as a usable model/provider in opencode, and verify it end-to-end. Use when the user asks to 'add <model> from ollama to opencode', 'use ollama model X in opencode', 'wire up a local model in opencode', when adding an Ollama model to opencode.json, smoke-testing an Ollama OpenAI-compatible endpoint with curl, diagnosing EMPTY content from a thinking/reasoning model, or wondering why the new provider does not appear without a restart. Covers the 5-step procedure (ollama list -> curl /v1/models -> ollama show for the tools-capability gate -> @ai-sdk/openai-compatible provider block -> JSON validation + restart), the chat-completions smoke test, the thinking-model gotcha (reasoning consumes small max_tokens -> empty content, not an endpoint failure), and the stale model-pins trap. Session history in the body.
created_by: autolearn
created_at: "2026-08-15"
---

# Opencode Ollama Provider Setup

Verified recipe for adding an Ollama-served model to opencode as a
provider, plus the smoke-test gotchas that waste turns when skipped.
Do NOT re-derive it from docs — every step is verified-working on this
machine (worked example: 2026-08-15, adding `muse-glimmer:latest`
[18 GB / 27.9B / Q4_K_M / 131072 ctx / tools + thinking] as provider
`ollama-local`; earlier: 2026-02-15 llama3:8b, 2026-06-10 ollama-gb10).

## Instructions

### Step 1: Get the exact model tag

```bash
ollama list
```

The config key must EXACTLY match the tag (`muse-glimmer:latest`, with
the `:latest` suffix if that is how it is listed).

### Step 2: Verify the OpenAI-compatible endpoint

```bash
curl -s http://127.0.0.1:11434/v1/models
```

The model must appear in the response. For a REMOTE box (GB10 etc.),
use its Tailscale hostname/IP instead of 127.0.0.1 — see the
`ollama-gb10` provider entry for the pattern and the
`ollama-on-gb10-dgx-spark` skill for OLLAMA_HOST setup.

### Step 3: `ollama show` — context length AND the tools gate

```bash
ollama show <model-tag>
```

- **Context length** (e.g. 131072) → use as `limit.context`.
- **Capabilities** → MUST include `tools`. A model without `tools`
  cannot make agentic tool calls and will NOT work as an opencode
  coding agent, no matter how good it is at chat. (`vision` and
  `thinking` are bonuses.) Note whether it is a thinking model —
  matters for the smoke test below.

### Step 4: Add the provider block to ~/.config/opencode/opencode.json

Mirror the existing `ollama-gb10` / `ollama-local` pattern:

```json
"ollama-local": {
  "models": {
    "muse-glimmer:latest": {
      "limit": { "context": 131072, "output": 65536 },
      "name": "Muse Glimmer 28B (local)"
    }
  },
  "name": "Ollama (local)",
  "npm": "@ai-sdk/openai-compatible",
  "options": { "baseURL": "http://127.0.0.1:11434/v1" }
}
```

- The `models` map key is the OLLAMA TAG verbatim; the label lives in
  `name`. Additional models on the same server go under the same
  provider's `models` map — no second provider block.
- `npm` is `@ai-sdk/openai-compatible` — opencode installs it on demand.
- Prefer `127.0.0.1` over `localhost` in the baseURL.
- `output: 65536` matches the house convention; it is a cap, not a
  requirement.

### Step 5: Validate JSON, then restart opencode

```bash
python -m json.tool ~/.config/opencode/opencode.json > /dev/null && echo OK
```

opencode reads provider config at STARTUP — quit and restart; the new
provider will not hot-appear. Select per-session with `/models` →
`ollama-local/<model>:latest`, launch with
`opencode --model ollama-local/muse-glimmer:latest`
(`<provider-slug>/<model-key>`), or pin via a `"model"` field. Adding a
provider does NOT change the default model.

### Smoke test the chat endpoint (catches wiring bugs early)

```bash
curl -s http://127.0.0.1:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"<tag>","messages":[{"role":"user","content":"Say ok"}],"max_tokens":200}'
```

Use a GENEROUS `max_tokens` (200+) and timeout (180s):
- **First request pays the model-load cost** — an 18 GB model takes
  ~30s–1min+ to load; subsequent requests are fast.
- If the response has no `choices[0].message.content`, check the RAW
  response (drop any jq filter) before concluding the endpoint is
  broken — see the thinking-model gotcha next.

### Thinking-model gotcha: empty content ≠ failure

TRIGGER: smoke-testing a thinking/reasoning model with a small
`max_tokens` (e.g. 10).

ROOT CAUSE: Ollama's OpenAI-compatible endpoint maps thinking output to
a `reasoning` field, emitted BEFORE `content`. A small token budget is
entirely consumed by reasoning tokens, so `content` comes back empty
(`finish_reason: "length"`) while `reasoning` is populated. HTTP 200 —
the endpoint works fine.

FIX: re-test with a larger `max_tokens` (the model is already loaded,
so the retry is fast). Do not debug the endpoint, config, or provider
wiring — that is all correct. opencode's ai-sdk handles the `reasoning`
field fine; expect a pause while reasoning streams before content
appears.

### Stale model-pins trap

Per-agent `agent.*.model` fields and scheduler-job model pins do NOT
inherit the default — sweep all three surfaces (default model,
agent overrides, job pins) when changing defaults.

## Follow-up additions ("add X as well")

Follow-ups ("add qwen3.8:27b-mlx as well") are the SAME procedure,
shortened: provider block already exists, so the chain is fresh
`ollama list` -> `ollama show <tag>` (context + tools gate) -> add the
model entry under the EXISTING provider `models` map -> `python -m
json.tool` validation -> remind the user to restart. Execute ALL of it
in the SAME turn.

TWO disciplines (born from the 2026-08-15 qwen follow-up that drew a
"Take action now" interrupt):

1. NEVER reason over a PRIOR turn's `ollama list` output — models get
   pulled between turns; an old listing is not ground truth. Re-run it
   fresh; if the tag is absent, report that and stop (the user can
   pull it).
2. Zero narration. Paragraphs of "maybe they just downloaded it, let me
   verify..." with NO tool calls is the narration-without-action
   failure (execution-discipline-narration-without-action skill). A
   follow-up to a just-completed procedure needs even LESS
   deliberation than the original: open with the tool calls.

## Tag discovery when ollama search is unavailable (2026-08-28)

- gb10's ollama build predates the 'ollama search' subcommand — discover exact model tags by curling the registry instead: curl -s https://ollama.com/library/<model>/tags | grep -o '<model>:[a-z0-9._-]*' | sort -u. Verified 2026-08-28: qwen3.8:27b is the dense default tag. Dense-vs-MLX: the Mac's local qwen3.8:27b-mlx is the Mac-only MLX build — pull the PLAIN tag on gb10 (ollama resolves arch layers automatically; never copy an -mlx tag to a non-Mac host). EXECUTION NOTE: once the tag is verified, the pull itself ('ssh gb10 "nohup ollama pull qwen3.8:27b > /tmp/qwen38-pull.log 2>&1 &"') must be the FIRST tool call of the turn — this exact workflow (qwen3.8:27b on gb10) has now drawn 'Take action now' TWICE (2026-08-15 mlx follow-up; 2026-08-28 narrated-pull stall) because the assistant ended turns with a numbered plan + 'Let me kick off the pull in the background...' instead of launching it. Long pole first, narration never.

## Daily-driver default switch

- Daily-driver default switch (add model AND make it the default, e.g. qwen3.8:27b on gb10 2026-08-28): edit ONLY the top-level 'model' key in ~/.config/opencode/opencode.json — the same 'model' key appears again at 6-space indent inside agent.autolearn-reviewer; include the exact leading whitespace (2-space) in the Edit old_str to disambiguate the anchor. That agent pin (cloud model for the background reviewer) is INTENTIONAL — never flip per-agent pins when test-driving a local model as the global default; switching the global default does not require touching them. Validate with python -m json.tool after the edit, and confirm wiring in BOTH harnesses (opencode + pi agent) before waiting on the pull.

## Smoke test is the final step

- The FINAL step of a model add is the SMOKE TEST (chat completions from the client machine) once the pull lands — for long pulls (~17GB), hold one ssh session with a remote wait-loop ('while pgrep -f "ollama pul[l]" >/dev/null; do sleep 30; done; ollama list') under a generous bash timeout (600000ms) rather than announcing the wait in prose: 2026-08-28 'Now waiting for the pull to finish, then smoke-testing:' ended the turn with NO poll command launched and drew 'Take action now' (second qwen3.8-session stall; first was the 2026-08-15 stale-ollama-list narration). If a wait/poll is the next action, launching the blocking command IS the turn.

## exact model IDs, built-in providers, and default-model selection

- VERIFY-THEN-EDIT DISCIPLINE for model config (added 2026-08-28, glm-5.3-flash default-switch session):
- 'opencode models' (CLI) lists EVERY usable model — built-in providers AND configured ones. Pipe through grep to confirm the exact provider/model string BEFORE editing any config (verified: 'opencode models | grep glm-5.3-flash' -> 'zai-coding-plan/glm-5.3-flash'). Never guess a model key.
- ABSENCE of a provider block in opencode.json does NOT mean a provider is missing: some providers are BUILT-IN (zai-coding-plan ships with opencode via opencode auth — no config block required). Check 'opencode models' before adding a redundant provider block.
- The DEFAULT model is the top-level "model" key in ~/.config/opencode/opencode.json (e.g. "model": "zai-coding-plan/glm-5.3-flash"); restart opencode after changing it.
- pi parity surface: pi default = ~/.pi/agent/settings.json (defaultProvider + defaultModel); pi's built-in models-store.json already carries the zai provider (glm-5.3-flash: 1M ctx, 131072 max output) with auth.json holding the key — no custom provider entry needed for zai.
- OPTION vs DEFAULT (user correction 2026-08-28): wiring a new local model for test-driving means adding it as an OPTION in both agents; switching the default is a separate explicit step — do not promote the test-drive model to default unless the user says so.

## Local TTFT/TPS tuning -> see ollama-local-performance-tuning

- Speed tuning of a working local Ollama setup (TTFT / tok-per-s) lives in the dedicated **ollama-local-performance-tuning** skill — load it for the full benchmark + keep-alive/launchd playbook. Headlines (direct measurements 2026-08-29, M4 Max 128GB, qwen3.8:27b-mlx ~18GB MLX): num_ctx is NOT a TTFT lever (warm TTFT flat ~85ms 16k->262k; long-prompt prefill is COMPUTE-BOUND ~209 t/s at ANY depth — a 120k prefill can blow a 10-min bash tool timeout; the earlier '~5000 t/s @262k' was a short-prompt artifact, never cite it); the dominant TTFT costs are keep-alive expiry (default 5 min -> 20-40s cold reloads; fix = OLLAMA_KEEP_ALIVE via launchctl setenv + the com.ericmjl.ollama-warm LaunchAgent, login + 90-min pings — no native preload) and reasoning-model thinking mode (hidden reasoning burned the whole max_tokens budget with nothing visible; fix = CAMELCASE "reasoningEffort": "low" in the MODEL-level options -> visible token 0.1-1.8s; NOTE snake_case "reasoning_effort" is silently dropped from the wire at BOTH model and provider level (verified via wire-payload proxy 2026-08-30; opencode is a compiled binary — verify forwarding empirically)); KV cache grows INCREMENTALLY with actual usage (~190 MB/1k tok; full-262k peak ~65 GB fits 128 GB but do not co-run another big model) — NOT upfront from num_ctx, and it lives in the Metal/GPU heap which ps RSS underreports (measure system free-memory delta, sampled DURING prefill); prefix cache verified (~85 ms warm repeats); decode is a hard ceiling at 37-51 t/s (nothing tunable moved it — smaller quant/model is the only lever); dead ends: OLLAMA_FLASH_ATTENTION / OLLAMA_KV_CACHE_TYPE are unsupported in Ollama 0.33's MLX engine. (Consolidated 2026-08-29: three parallel-reviewer correction bullets merged into this single headline to stop drift.)
- CORRECTION (2026-08-29, 134k-token direct measurement): the headline bullet above carries an earlier WRONG claim — on the MLX engine the KV cache is NOT allocated upfront from num_ctx; it grows INCREMENTALLY with actual context used (~190 MB per 1k tokens; a 24k-token history changed footprint by zero, a 134k prefill dropped system free memory 81%->53% ~26 GB; 262k num_ctx pre-burns nothing — memory only becomes the question at real long-context depth, peak ~65 GB at full window, fits 128 GB). Keep num_ctx large for latency; think memory only when running long contexts alongside other big models. Measured playbook: ollama-local-performance-tuning skill.

## Request payload size (what opencode actually sends)

- - A single opencode agent request is a ~346 KB JSON payload of ~99,000 tokens: ~176 KB agent system prompt + ~85 tool schemas (~177 KB more). Consequence: PREFILL dominates TTFT on any slow/self-hosted endpoint — at ~320 t/s (M4 Max MLX) a 99k-token prefill is ~5 min; at ~1,800 t/s (GB10) it is ~55s. Choose provider targets with this in mind, and remember a reasoning model adds hidden thinking tokens on top of prefill (suppress via model-level options {"reasoningEffort": "low"} — camelCase only, see the REASONING-EFFORT WIRE-FORWARDING section in ollama-local-performance-tuning). Measured via wire-logging proxy 2026-08-30.

## Trigger details (from pre-compression description, preserved verbatim)

Add an Ollama-hosted model (local laptop Ollama or a remote box like the GB10) as a usable model/provider in opencode, and verify it end-to-end. Use when the user asks to 'add <model> from ollama to opencode', 'use ollama model X in opencode', 'wire up a local model in opencode', when adding an Ollama model to ~/.config/opencode/opencode.json, smoke-testing an Ollama OpenAI-compatible endpoint with curl, diagnosing EMPTY content from a thinking/reasoning model, or wondering why the new provider does not appear without a restart. Covers the 5-step procedure: ollama list for exact tag -> curl /v1/models to verify the OpenAI-compatible endpoint -> ollama show for context length AND the tools-capability gate (models without tools capability cannot act as opencode coding agents) -> provider block using npm @ai-sdk/openai-compatible with baseURL http://127.0.0.1:11434/v1 -> JSON validation + opencode restart; plus the chat-completions smoke test (generous max_tokens), the thinking-model gotcha (reasoning field consumes small max_tokens -> empty content with finish_reason=length, NOT an endpoint failure), first-request model-load latency, and the stale model-pins trap. Consolidated 2026-08-16 from ollama-opencode-provider-setup (duplicate created same day). Recurred across 2026-02-15, 2026-06-10 (ollama-gb10 provider), and 2026-08-15 twice (ollama-local + muse-glimmer; then a qwen3.8:27b-mlx 'as well' follow-up that stalled in narration over stale ollama list output and drew a 'Take action now' interrupt) sessions.
