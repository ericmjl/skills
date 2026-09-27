---
name: opencode-mcp-server-setup
description: >-
  Add or configure an MCP server in opencode's config (~/.config/opencode/opencode.json or project .opencode/) — both server types: LOCAL/stdio {"type": "local", "command": ["npx", "pkg"], "enabled": true} and REMOTE/HTTP {"type": "remote", "url": "...", "enabled": true}. Use when the user says 'add the X MCP server', 'install/configure MCP', 'connect to <service> MCP', an MCP server appears in docs but isn't wired into opencode, tools from a known MCP server are missing in a session, or a server needs REINSTALLING/RESTORING after its entry was dropped. KEY GOTCHAS: servers load at STARTUP (restart to see new ones); many remote servers (Exa) work FREE without an API key — start with type+url+enabled only; API keys go in a headers block; OAuth servers (Notion, Linear) use "oauth": {} and the user must run 'opencode mcp auth <name>' (the agent cannot complete OAuth); verify JSON validity after editing. Verified examples for Exa/Notion/Jupyter live in the body.
created_by: autolearn
created_at: "2026-07-24"
---

# Opencode Mcp Server Setup

Add or configure an MCP server in opencode's config (~/.config/opencode/opencode.json or project .opencode/) — covers BOTH server types: (1) LOCAL/stdio servers use {"type": "local", "command": ["npx", "pkg"], "enabled": true} (or "command": ["/abs/path/to/binary"]) where opencode spawns the process over stdin/stdout; (2) REMOTE/HTTP servers use {"type": "remote", "url": "https://host/mcp", "enabled": true} where opencode connects to a hosted endpoint. Use when the user says 'add the X MCP server', 'install/configure MCP', 'connect to <service> MCP', an MCP server appears in docs but isn't wired into opencode, or tools from a known MCP server are missing in a session, or an MCP server needs REINSTALLING/RESTORING after its entry was dropped from the config. KEY GOTCHAS: (a) MCP servers load at STARTUP — the running session will NOT see a newly added server until opencode is quit and relaunched; tell the user to restart. (b) Many remote servers (Exa, etc.) offer a FREE plan that works WITHOUT an API key — start with just type+url+enabled, no headers block; add a key only when you hit 429 rate limits. (c) API keys go in a headers block: {"headers": {"x-api-key": "<key>"}} (header name varies by provider; Exa uses x-api-key, check the provider's docs). (d) Some remote servers expose advanced/agent tools behind a query param on the URL (e.g. "?tools=...") — opt in only if needed. (e) Verify JSON validity after editing (python -m json.tool or jq). (f) OAuth-based remote servers (Notion, Linear) use "oauth": {} instead of a headers block — opencode handles the browser OAuth flow automatically; the agent CANNOT complete OAuth itself, instruct the user to run "opencode mcp auth <name>" after restart. Verified-working examples: REMOTE (Exa free plan) {"exa": {"type": "remote", "url": "https://mcp.exa.ai/mcp", "enabled": true}}; REMOTE (Notion OAuth) {"notion": {"type": "remote", "url": "https://mcp.notion.com/mcp", "enabled": true, "oauth": {}}}; LOCAL (stdio) {"jupyter": {"command": ["npx", "jupyterlab-collab-mcp"], "enabled": true, "type": "local"}}. Distinct from jupyterlab-collab-mcp-setup (Jupyter-specific 3-layer architecture) and customize-opencode (built-in, general opencode config but doesn't enumerate the local-vs-remote type distinction).

## Instructions

TODO: Add specific instructions based on observed patterns.
- ## Procedure

1. Decide the server TYPE. Check the provider's docs for the connection model:
   - LOCAL/stdio (opencode spawns a process): provider docs show a CLI command
     like 'npx <pkg>' or a binary path. Use {"type": "local", "command": [...]}.
   - REMOTE/HTTP (opencode connects to a hosted URL): provider docs show an
     https endpoint. Use {"type": "remote", "url": "..."}.
2. Edit the config file:
   - Global (all projects): ~/.config/opencode/opencode.json → "mcp" object.
   - Project-scoped: <repo>/.opencode/opencode.json (or opencode.jsonc).
   Add the entry as a key under "mcp" with "enabled": true.
3. Start REMOTE servers on the FREE plan first — omit any headers/API-key block.
   Many providers (Exa, etc.) work without a key up to a rate limit. Add a key
   ONLY when the user hits a 429.
4. Verify the JSON is still valid after the edit:
   python -m json.tool ~/.config/opencode/opencode.json
   (or: jq . ~/.config/opencode/opencode.json)
5. TELL THE USER TO RESTART opencode. MCP servers load at process startup;
   the running session will NOT see the new server. This is the #1 reason a
   freshly-added server's tools appear missing.

## When tools from a known MCP server are missing in a session

Before debugging the server itself, check (in order):
1. Is the server registered under "mcp" in opencode.json with enabled: true?
   (grep the config — opencode does NOT auto-discover servers.)
2. Was opencode RESTARTED after the config change? A server added mid-session
   is invisible until relaunch.
3. For LOCAL servers: does the command binary exist and run standalone?
   (Run the command array directly; a missing npx package or wrong path fails
   silently at startup.)
4. For REMOTE servers: does the URL resolve? (curl the endpoint.) If 429, add
   an API key via headers.

## API key / auth for remote servers

Add a "headers" block inside the server entry. Header NAME varies by provider
(Exa uses x-api-key; others use Authorization: Bearer). Check the provider docs.
NEVER write a real key into a committed file — if the config is in a repo, use
an env-var reference the harness supports, or keep keys in the global
~/.config/opencode/opencode.json which is outside the repo.

## OAuth-based remote servers (Notion, Linear, GitHub, Google Drive)

Some remote MCP servers authenticate via OAuth, NOT an API key. For these, add
an "oauth" key with an empty object:

  "notion": {"type": "remote", "url": "https://mcp.notion.com/mcp", "enabled": true, "oauth": {}}

The empty "oauth": {} tells opencode to handle the OAuth flow automatically: it
detects the 401, initiates OAuth via Dynamic Client Registration (RFC 7591),
and stores the token after the user authorizes in the browser.

Three auth models for remote servers (check the provider docs to pick):
  1. No auth (free plan): just type + url + enabled (e.g. Exa).
  2. Static API key / Bearer token: "headers": {"x-api-key": "..."} or
     "headers": {"Authorization": "Bearer ..."}. NEVER use "{env:VAR}"
     interpolation inside the headers block, and never duplicate the same
     token across project .env files: (a) {env:VAR} resolves from the
     opencode SERVER PROCESS environment at startup, which does NOT see
     project .env files or direnv — in a fresh launch context the header
     resolves to garbage and the server 401s no matter what the .env holds;
     (b) duplicate token copies drift apart (a 2-char paste error caused a
     Buffer 401 on 2026-09-11). Buffer MCP broke this way TWICE (2026-08-12
     and 2026-09-11→12), the second time after a .env token-splice "fix"
     that did not survive the next launch. Prefer OAuth whenever the server
     supports it — Buffer does.
  3. OAuth flow: "oauth": {} (e.g. Notion, Buffer). No manual token needed.
     MANDATORY for Buffer — Eric's standing preference (2026-08-11,
     re-confirmed 2026-09-12): buffer lives in the GLOBAL
     ~/.config/opencode/opencode.json with "oauth": {}, never project-local
     with a static token. The OAuth token persists in
     ~/.local/share/opencode/mcp-auth.json across restarts AND across config
     removals — re-adding the entry does NOT need a new browser flow
     (verified 2026-09-12: reconnected with all 20 tools, zero re-auth).

Completing the OAuth dance (the agent CANNOT do this itself, it needs a browser
and the user credentials):
  1. After adding the config entry, the user must RESTART opencode (MCP servers
     load at startup; the running session cannot see the new server).
  2. After restart, run "opencode mcp auth <name>" (e.g. "opencode mcp auth
     notion") to open the browser authorization flow.
  3. Verify post-auth with "opencode mcp list" which should show the server as
     authenticated.

Reachability check: curl-ing a remote OAuth endpoint and getting HTTP 401 is the
EXPECTED/GOOD result, it confirms the endpoint is reachable AND requires auth.
Do NOT treat a 401 as a config error or wrong URL; a 404/timeout would indicate
a wrong URL, but a 401 is success. Discovered 2026-08-08 adding the Notion MCP
server (https://mcp.notion.com/mcp): endpoint returned 401, confirming
reachable + needs OAuth.

## Advanced / opt-in tools

Some remote servers gate extra tools behind a URL query param
(e.g. Exa: "https://mcp.exa.ai/mcp?tools=..." to enable agent/search variants).
Opt in only when the user asks for the advanced tools; the default URL exposes
the core tool set.

## Verified-working config snippets

REMOTE (Exa, free plan, no key):
  "exa": {"type": "remote", "url": "https://mcp.exa.ai/mcp", "enabled": true}

REMOTE (Exa, with API key):
  "exa": {"type": "remote", "url": "https://mcp.exa.ai/mcp", "enabled": true,
           "headers": {"x-api-key": "<key>"}}

REMOTE (Notion, OAuth flow):
  "notion": {"type": "remote", "url": "https://mcp.notion.com/mcp", "enabled": true, "oauth": {}}

LOCAL (stdio, npx package):
  "jupyter": {"command": ["npx", "jupyterlab-collab-mcp"], "enabled": true, "type": "local"}

LOCAL (stdio, npx package, sequential thinking):
  "sequential-thinking": {"type": "local", "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"], "enabled": true}

LOCAL (stdio, absolute binary path):
  "codebase-memory": {"command": ["/Users/<user>/.local/bin/codebase-memory-mcp"], "enabled": true, "type": "local"}

## default-global-over-local

- Default to GLOBAL config (~/.config/opencode/opencode.json) for cross-project / general-purpose MCP servers (Buffer, Notion, Exa, codebase-memory, Jupyter, etc. — tools used across multiple repos). Reserve project-local config (opencode.json or .opencode/) for project-SPECIFIC servers only. The user stated this preference explicitly (2026-08-11): 'can we change my buffer mcp configuration to be global to opencode rather than just local?' This is the MCP-config application of the broader cross-project-vs-project-local routing principle. When adding an MCP server, ask: is this server used in more than one project? If yes → global. If no → project-local.

## buffer-mcp-405-oauth-fix

- Buffer MCP specifically: the skill previously suggested 'oauth: false' + a static API-key header (Authorization: Bearer) as a valid approach. This is FRAGILE — it works in the session that launched with the env var resolved, but produces HTTP 405 (Method Not Allowed) on the SSE handshake in OTHER sessions, because either (a) the {env:BUFFER_API_KEY} interpolation is not re-resolved in the new launch context, or (b) the static-token path forces a transport the endpoint rejects. ROBUST FIX (2026-08-12): use the OAuth flow instead — {"buffer": {"type": "remote", "url": "https://mcp.buffer.com/mcp", "enabled": true, "oauth": {}}}, then run 'opencode mcp auth buffer' in the terminal to complete the browser authorization once; the token persists in ~/.local/share/opencode/mcp-auth.json across ALL future sessions. Buffer's own MCP server instructions recommend OAuth ('Many clients connect to Buffer over OAuth, with nothing to create'). The earlier line 'Use oauth: false if the server supports OAuth but you prefer a static token (e.g. Buffer MCP)' is misleading for Buffer — prefer OAuth. Diagnosis: a 405 (not 401, not 429) on a remote MCP endpoint = transport/auth-model mismatch, not a wrong URL; switch auth models before debugging the URL.

## oauth-config-commit-safety

- OAuth-based MCP entries ({"oauth": {}}) are SECRET-FREE and safe to commit in a project-local .opencode/opencode.json — opencode stores the OAuth token OUTSIDE the repo in ~/.local/share/opencode/mcp-auth.json, so a project-scoped OAuth server config can be committed and shared with collaborators. Verify shareability before assuming: 'git check-ignore .opencode/opencode.json' (exit code 1 = NOT ignored = will be committed). This is the OPPOSITE of static API-key entries (headers blocks), which ARE secrets and must never go in a committed file (see 'API key / auth' section). Verified 2026-08-14 adding the openbnb MCP server (https://mcp.openbnb.ai/mcp, Airbnb search for venue research) project-scoped in learn-anything: endpoint 401-probe confirmed OAuth model, config committed cleanly, token persisted outside the repo.

## Smoke-testing a local (stdio) MCP server before wiring it into opencode

- Before editing opencode config (which needs a full restart to test), verify the server command actually launches and responds: pipe a JSON-RPC initialize + tools/list pair into the exact command array you plan to configure and check the JSON response:

echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | <command...>

A response listing tools proves the binary path, deps, and entry file are all correct BEFORE a config edit + restart cycle. This catches wrong absolute paths (e.g. assuming /opt/homebrew/bin/bun) in seconds. Validated 2026-08-17 installing mcp-hey (34 tools returned).

## Reinstalling / restoring a dropped MCP server entry

- TRIGGER: the user asks to REINSTALL/RESTORE an MCP server that was previously configured and has since been DROPPED (absent from the global ~/.config/opencode/opencode.json 'mcp' section and the project's .opencode/ config). Do NOT reconstruct the entry from memory or provider docs (wrong package name, missing -y flag, wrong type) — RECOVER the exact prior entry from PAST SESSION HISTORY: a session that ran 'opencode debug config' (or printed resolved config) captured the FULL merged mcp config as it existed then. QUERY: grep the opencode session store / logs for 'debug config' plus the server's package name (see the opencode-session-history-querying skill) and lift the verbatim prior entry (type, command array, args, enabled flag). Restore it VERBATIM to the SAME SCOPE it previously lived in (the merged dump shows global vs project-local) — this converts a re-research task into a lookup and guarantees the reinstall matches what worked before. ORDER OF GATES: (1) SMOKE-TEST the recovered command BEFORE writing config — pipe a JSON-RPC initialize + tools/list handshake into the exact command array (see the smoke-testing section above); a clean handshake listing the expected tool distinguishes 'entry was dropped' from 'package renamed/broken' — a smoke-test FAILURE means the package changed and the entry needs updating, not blind restoring. (2) Write the entry, validate the JSON still parses (python -m json.tool or jq). (3) VERIFY FROM THE SHELL YOURSELF before ending the turn: 'opencode mcp list' reads the config FRESH and connects to each server on demand, printing '✓ connected' — run it yourself as the final verification instead of deferring it to the user (verified 2026-08-30: it showed 'sequential-thinking ✓ connected' immediately after the config restore; deferring this check to the user drew a 'Take action now.' interrupt). (4) Only the RESTART is genuinely user-side: the running session's tool list is fixed at startup, so the server's TOOLS appear in-session only after quit + relaunch. VERIFIED INSTANCE (2026-08-30): 'reinstall sequential thinking mcp server' — old entry recovered verbatim from a past session's debug-config output (had been silently dropped from GLOBAL config as a local npx server), smoke test returned the `sequentialthinking` tool, restored: {"sequential-thinking": {"type": "local", "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"], "enabled": true}}.

## Environment facts and project scoping (this machine)

- Environment facts: bun lives at /Users/ericmjl/.bun/bin/bun (1.3.4+) — homebrew bun is NOT installed, so /opt/homebrew/bin/bun does not exist; always use the absolute ~/.bun/bin/bun path in MCP "command" arrays for bun-based servers (validated shape: {"command": ["/Users/ericmjl/.bun/bin/bun", "run", "/abs/path/to/repo/src/index.ts"]}). Project scoping: when the user bounds a server to ONE project ('I only need it within <project>'), write the config to <project>/.opencode/opencode.json (project-local), not ~/.config/opencode/opencode.json — project-local servers load only in that project, keeping every other session's context lean. Instance 2026-08-17: mcp-hey scoped to the brain42 vault.

## endpoint-path-variance-not-all-hosted-mcp-servers-use-mcp

- HOSTED MCP SERVERS DO NOT ALL SERVE AT /mcp — verify the endpoint PATH before writing the config. Exa/Notion/Buffer/openbnb all use https://host/mcp, but Calendly serves MCP at the ROOT: https://mcp.calendly.com (POST to https://mcp.calendly.com/mcp returns 404 = wrong path, not a dead server). Discovered 2026-08-21 adding Calendly MCP globally: first probe of /mcp returned 404, root probe returned 401 + WWW-Authenticate header = correct OAuth-protected endpoint. PROBE PROCEDURE when the provider docs name a host but not a full path (or when a guessed /mcp 404s): POST an MCP initialize payload (curl -s -o /dev/null -w '%{http_code}' -X POST with Accept: application/json, text/event-stream) to candidate URLs and read the status: 401 + WWW-Authenticate (often with a resource-metadata link) = CORRECT endpoint, OAuth-protected, config-ready; 404 = wrong path — try the bare root next; 405 on /.well-known/oauth-protected-resource just means you POSTed a GET endpoint (the path exists — supporting evidence the host is an MCP/OAuth server). VERIFIED Calendly entry (global, OAuth 2.1 + Dynamic Client Registration RFC 7591, no static tokens exist): {"calendly": {"type": "remote", "url": "https://mcp.calendly.com", "enabled": true, "oauth": {}}} — then restart opencode + 'opencode mcp auth calendly' (browser consent; token persists across sessions). Rule of thumb: never assume /mcp — a 404 on the conventional path is a PATH problem; re-probe the root before concluding the server is down or the docs are wrong.

## oauth-dcr-loopback-redirect-uri

- - TRIGGER: 'opencode mcp auth <name>' fails with a GENERIC 'Authentication failed' (no error detail in the TUI) on a provider with strict DCR validation (Calendly 2026-08-21; continues the endpoint-path-variance Calendly saga). ROOT CAUSE: opencode's oauth-provider.ts HARDCODES http://127.0.0.1:${port}/mcp/oauth/callback as the redirect_uri in RFC 7591 Dynamic Client Registration — some providers' DCR endpoints REJECT IP-literal loopback redirects ('must be an HTTPS/SSL URI or redirect to localhost') returning invalid_client_metadata, which opencode masks as a bare 'Authentication failed'. Same bug as OpenClaw #91433 (fixed there by falling back to http://localhost:PORT). FIX — override the redirect URI in the oauth block: {"oauth": {"redirectUri": "http://localhost:19876/mcp/oauth/callback"}} — localhost still resolves to 127.0.0.1 so opencode's local callback server catches the browser redirect, but the REGISTERED uri passes the provider's localhost validation. KEY-CASING GOTCHA: the oauth config schema is mid-migration — v2 schema (packages/core/src/config/mcp.ts) uses snake_case keys (redirect_uri, client_id, client_secret, scope, callback_port) while v1 and the TS-internal McpOAuthConfig use camelCase (redirectUri, clientId); issue #6067 examples used camelCase. VERIFY which schema the installed version parses before writing the key (opencode 1.18.21 was mid-migration). ALTERNATIVE: pre-register a client manually via curl with a localhost redirect_uri and pin it via the supported client_id/client_secret oauth fields (PR #5940). DIAGNOSIS TECHNIQUE (saves the multi-turn source dive): when an OAuth flow fails masked, read the CLI's oauth source to see exactly what redirect_uri it registers — opencode's oauth-provider.ts lives on the DEV branch of the opencode repo (raw.githubusercontent fetch on main 404s; use the GitHub API contents endpoint or try dev), and when curling GitHub URLs containing ? in zsh, QUOTE the URL or the glob expansion fails with 'no matches found' before curl runs.

## When opencode mcp auth itself fails (fast-fail DCR diagnosis)

- SYMPTOM: 'opencode mcp auth <name>' prints 'Authentication failed' in ~2s WITHOUT opening a browser. Fast fail + no browser = the failure is at the DCR (RFC 7591 dynamic client registration) step — the client registers with the authorization server BEFORE any browser consent flow. The opencode log (~/.local/share/opencode/log/) does NOT capture the mcp-auth failure detail (it only shows session-start 'server unavailable key=<name> type=remote status=failed' warnings), so do not go digging there for the root cause. DIAGNOSIS PROCEDURE (verified 2026-08-21 on Calendly): (1) Map the OAuth topology: curl the MCP endpoint (expect 401 + WWW-Authenticate), follow its resource_metadata URL to protected-resource metadata, then the authorization_servers entry to AS metadata (/.well-known/oauth-authorization-server). Note cross-origin setups (Calendly: MCP at mcp.calendly.com but AS at calendly.com). (2) REPLICATE the DCR POST via curl with candidate client metadata variants (client_name, redirect_uris, scope) to isolate which field the server rejects — this is the highest-signal probe and takes seconds; a 200 with client_id means DCR itself works and the client's payload is the problem. (3) Search OTHER MCP clients' issue trackers (Claude Code, OpenClaw, n8n, Cursor) for the same server — server-side DCR strictness rules are client-agnostic and are often already documented there. CALENDLY STRICTNESS RULES (confirmed live 2026-08-21): client_name limited to alphanumeric/hyphens/spaces (parentheses rejected -> 'Claude Code (calendly)' style names fail with invalid_client_metadata); redirect_uri http://localhost:PORT accepted but http://127.0.0.1:PORT rejected; adding scope=openid reportedly breaks it (n8n #30147). If the client (opencode or other) sends a parenthesized client_name or a 127.0.0.1 loopback redirect, that is the bug — fix/report upstream.

## crashed-mid-session-mcp-server

- TRIGGER: an MCP server's tools were LIVE earlier in the session but the server process CRASHES mid-conversation (verified 2026-09-13: the plaud server, @plaud-ai/mcp, died mid-OAuth-login and its ~7 tools vanished from the session). A crashed server does NOT reconnect within the running session — same rule as a newly-added server: the in-session tool list is fixed at process launch, so recovery REQUIRES quitting and relaunching opencode (genuinely user-side; the agent cannot restart its own host). The crash does NOT remove the config entry; after relaunch the server loads normally (plaud's tools reappeared in the next session). PARKING-TURN DISCIPLINE (2026-09-13 session ended on a 3-step restart menu + a 'Which is it?' prose question and drew 'Take action now.'): the turn that hits the restart gate must STILL contain every agent-executable step — (1) confirm the entry survives in opencode.json; (2) run 'opencode mcp list' YOURSELF (it connects on demand, independent of the dead in-session connection) to distinguish 'process crashed transiently' from 'config/binary broken' — the 2026-08-30 precedent: deferring this check to the user drew the same interrupt; (3) smoke-test a local/stdio server's command directly; (4) probe NON-MCP access paths for the underlying data (CLI, direct API, local sync folders — see epistemic-resourcefulness) before concluding only the dead server can reach it. THEN hand over ONE crisp blocking ask ('quit + relaunch opencode; after that I'll re-run the login'). Do NOT close with a numbered multi-step menu plus an alternative-branch prose question — if the original request was ambiguous ('transcribe some of this stuff'), ask it via the QUESTION TOOL in the same turn so both asks are live, not stacked prose.

## oauth-gated-mcp-login-completion

- TRIGGER: an OAuth-gated remote MCP server (plaud 2026-09-13/14; Buffer OAuth-in-global-config 2026-09-12; Notion/Linear same family) whose config entry is ALREADY in global config and whose tools are LIVE in-session, but calls fail until the one-time browser OAuth completes. The OAuth click-through is genuinely USER-SIDE and additionally requires the user to be AT THE LAPTOP (plaud arc session 2 opened with 'sorry, I'm back at my laptop') — never spin retry loops while the user is away; park with ONE crisp ask and resume on return.
RESUME DISCIPLINE (the 2026-09-14 failure, 2nd same-arc 'Take action now', #54 family 56th strengthening): when the user returns and says 'try again, I just auth'd in', the ENTIRE remaining work is a cheap agent-executable verification — the config entry survived, the tools are already live, only the auth state changed. That turn must IMMEDIATELY (a) invoke one cheap tool from the server to confirm auth took (or list its live tools in-session), or (b) run 'opencode mcp list'. Do NOT re-explain the setup plan, re-narrate what OAuth is, or re-derive the state — 'I just auth'd in' is a resume signal, not a request for a status briefing. Stall signature of skipping this: 'try again' x2 + 'Take action now'.
BEFORE launching any browser-driven OAuth login flow: clear leftover background drivers from earlier attempts FIRST, in the same turn (plaud arc: a stray background driver held port 8199 and would conflict with the official login — check and kill before starting the flow).
Complete verified sequence (plaud, full arc): global-config entry survives server crash + relaunch (tools reappear per crashed-mid-session-mcp-server) -> user completes browser OAuth at laptop -> agent immediately smoke-tests one tool -> done.

## oauth-post-login-401-server-side-revocation

- TRIGGER: an OAuth-gated MCP server's login reports SUCCESS ('Successfully authenticated with Plaud!'), the token file exists with the correct shape, the token is unexpired — yet every API call returns 401 (plaud arc session 3, 2026-09-14; completes the arc after crashed-mid-session-mcp-server + oauth-gated-mcp-login-completion). DIAGNOSIS ORDER (do not re-derive): (1) confirm login genuinely succeeded and the token-file KEYS are right (shape check, no values); (2) check expiry — token expiry fields are in MILLISECONDS; reading them as seconds misjudges validity by 1000x, do the math once correctly; (3) decode the JWT claims AND read the actual API error body — the answer was verbatim there: CLIENT_USER_AUTH_REVOKED. ROOT CAUSE: the minted token was revoked SERVER-SIDE by mid-flight auth races — an aborted authorization or a second authorize for the same app invalidates the first token. FIX: kill every leftover driver/port first (port 8199 family), then ONE clean re-login with nothing racing it, and VERIFY IMMEDIATELY (one-shot get_current_user + a data listing) before reporting done. TECHNIQUES THAT WORKED: (a) run the package's login CLI DETACHED from the live MCP server (invoke the npx package's login command directly) — the tokens it stores (~/.plaud/tokens-mcp.json) work for any future server, immune to session server instability; (b) killing an MCP server's child process can destabilize the server for the rest of the session (tools vanish again), so prefer the detached driver when the in-session server is flaky; (c) npx-cache patches (login timeout 2 -> 10 min on @plaud-ai/mcp) are FRAGILE — @latest re-resolution can wipe them; re-apply on the next twitchy re-login instead of re-diagnosing.
