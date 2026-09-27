---
created_at: '2026-07-09'
created_by: autolearn
description: >-
  Build opencode (opencode-ai) plugins — the lifecycle pattern, the event surface for notifications/hooks, and local from-source install. Use when creating an opencode plugin, writing a notification/hook plugin, wiring session.idle/session.error events, deciding how to install a local plugin (symlink vs plugin array), reading the @opencode-ai/plugin types, using the Bun $ shell helper inside a plugin, checking npm/GitHub name availability for an opencode plugin package, or configuring plugin secrets via env vars vs plugin options. ALSO covers opencode2 (v2 beta) dual-stack support: the 'plugins' config key, plain-object v2 plugin exports, v2 event names (session.inbox.enqueued, session.text.ended, session.step.ended, session.execution.*), the shared .mjs core pattern, and 'opencode2 api delete' cleanup.
name: opencode-plugin-authoring
---

# Opencode Plugin Authoring

Build opencode (opencode-ai) plugins — the lifecycle pattern, the event
surface for notifications/hooks, and local from-source install.

## Plugin lifecycle (verified shape)

```typescript
import type { Plugin } from "@opencode-ai/plugin"

type Options = {
  backend?: string
  url?: string
  // ... your config keys
}

const plugin: Plugin = async ({ $, directory, project, client, worktree }, options: Options = {}) => {
  // $        = Bun shell template literal for subprocess calls (auto-escaped)
  // directory = project working-directory path (derive project name from it)
  // options   = plugin config object from opencode.json (second positional arg)

  return {
    event: async ({ event }) => {
      // event.type values include: "session.idle", "session.error", and others
      if (event.type === "session.idle") {
        // TURN COMPLETE — agent finished, waiting for user input
        // This is THE event for "notify me when done" notifications
        await $`osascript -e 'display notification "Done!" with title "opencode"'`
      }
    },
  }
}

export default plugin
```

Key facts:
- The default export is an async function taking `(context, options)`.
- `options` is the **second positional arg** — it comes from the plugin's config in `opencode.json`.
- The returned object's `event` handler receives `{ event }` where `event.type` is a string enum.

## Event surface

| event.type         | meaning                                       |
|--------------------|-----------------------------------------------|
| `session.idle`     | Turn complete — agent finished, waiting       |
| `session.error`    | Session errored                               |

`session.idle` is the canonical "notify me when done" event. Do NOT look
for `session.complete`, `session.end`, or `session.finish` — they don't exist.

## The `$` shell helper

The destructured `$` is a Bun shell template literal. Template expressions are
auto-escaped (safe for user-provided values):

```typescript
await $`curl -s -m 10 -X POST -H "Content-Type: application/json" -d ${jsonPayload} ${url}`
```

Never use `child_process.exec` or string concatenation — `$` is the provided mechanism.

## Configuration: plugin options vs env vars

Two config channels, both valid:

1. **Plugin options** (in `opencode.json`) — takes precedence:
```json
{
  "plugin": [
    ["~/github/opencode-push", { "backend": "ntfy", "ntfy_url": "http://gb10" }]
  ]
}
```
**Schema (verified against https://opencode.ai/config.json):** each `plugin` entry is
either a plain string (path or npm name) OR a 2-element tuple `[path, optionsObject]`.
The object form `{ "path": ..., "options": ... }` is REJECTED with
`"Expected string | array, got {...} plugin.N"` — it does NOT work. ALWAYS check the
live schema before writing an opencode.json plugin entry; do not trust secondhand examples.

2. **Environment variables** (in `~/.zshenv` — NOT `~/.zshrc`, which daemon/launchd-launched opencode does not source; see daemon-env-var-gotcha below) — read via `process.env`. The
   opencode-push plugin supports TWO backends (bark and ntfy), switchable
   WITHOUT any code change — set the env vars and the plugin picks them up
   at load time:

```bash
# Backend selection (default: "bark"; set to "ntfy" to switch)
export NOTIFY_BACKEND="ntfy"

# ntfy backend config (self-hosted ntfy server — e.g. on a gb10 box)
export NTFY_URL="http://gb10"        # ntfy server base URL (MagicDNS hostname works)
export NTFY_TOPIC="opencode"         # topic name (default: "opencode")

# bark backend config (the alternative backend)
export BARK_URL="https://api.day.app/<your-key>"

# Host label — which machine this notification originates from
export NOTIFY_HOST="mac"
```

A `first(options.x, process.env.X)` helper lets the plugin fall back from
options to env. **Secrets (API keys, tokens) must NEVER be committed to the
plugin repo** — use env vars or opencode.json (which is local config, not in
the repo).

**Switching backends is config-only** (07-09): the plugin already supports
both bark and ntfy internally; no source edit is needed. Just set
`NOTIFY_BACKEND` and the corresponding backend's URL/topic env vars (or
plugin options), then restart opencode.

## Install: local from-source (two mechanisms)

**Mechanism A — auto-load symlink (preferred for active development):**

```bash
mkdir -p ~/.config/opencode/plugins
ln -sf ~/github/<your-plugin>/index.ts ~/.config/opencode/plugins/<name>.ts
```

Opencode auto-loads any `.ts`/`.js` file in `~/.config/opencode/plugins/`.
A symlink to your git-repo source keeps the repo as source-of-truth — no
opencode.json change needed.

**Mechanism B — plugin array in opencode.json:**

```json
{
  "plugin": [
    "~/github/<your-plugin>",
    "/absolute/path/to/index.ts",
    ["~/github/<your-plugin>", { "some_option": "value" }]
  ]
}
```

Entries are strings OR `[path, options]` tuples (see schema note in
"Configuration" section). If switching from the auto-load symlink
(Mechanism A) to the plugin array (Mechanism B) to pass options, REMOVE
the symlink first to avoid double-loading the plugin.

After install, restart opencode for the plugin to load.

## Reinstalling / updating a local plugin

When the user says "reinstall" or "update" a local plugin, check HOW it is
installed FIRST — "reinstall" rarely means a literal reinstall, because
plugins auto-load from their install location on opencode restart:

- **Mechanism A (symlink in `~/.config/opencode/plugins/`):** already live —
  the symlink points at the repo source, so a `git pull` in the repo is
  reflected on next opencode restart. No opencode.json change needed.
- **Mechanism B (path reference in `opencode.json` plugin array):** `git pull`
  the repo at that path, then restart opencode. No opencode.json edit needed.
- **Install-script plugins (e.g. opencode-autolearn):** re-run the canonical
  `install.sh`, which re-symlinks skills + patches opencode.json idempotently.

So "reinstall opencode-push from my github repo" (07-10) = `git -C
~/github/opencode-push pull` + restart opencode — the plugin is
path-referenced in `opencode.json`, so the updated source loads on next start.
This recurs whenever the user updates a local plugin; the per-method mapping
above avoids guessing whether to pull, re-link, or re-run a script.

## Package structure

```
<your-plugin>/
├── index.ts          # the plugin (default export)
├── package.json      # name, "type": "module", main/module = index.ts
├── README.md
└── .gitignore
```

`package.json` essentials:
```json
{
  "name": "<available-name>",
  "type": "module",
  "main": "index.ts",
  "devDependencies": { "@opencode-ai/plugin": "*" }
}
```

## Naming: check npm + GitHub availability FIRST

Opencode plugin names collide frequently on npm. Before committing:

```bash
# 404 = available, 200 = taken
curl -s -o /dev/null -w "%{http_code}" https://registry.npmjs.org/<name>
```

Known TAKEN names (as of 2026-07-09): `opencode-notify`,
`opencode-notification`, `opencode-alert`.
Known AVAILABLE: `opencode-push`.

Also check GitHub: `gh repo view ericmjl/<name>` (404 = free under your account).

## Full worked example: opencode-push

A configurable push-notification plugin (Bark / ntfy.sh backends) lives at
`~/github/opencode-push` (https://github.com/ericmjl/opencode-push). It
demonstrates all of the above: options-or-env config, `session.idle` +
`session.error` events, `$` shell helper for curl, symlink install, and a
`first()` fallback helper.

## Token-efficiency note

The above was discovered by reading the opencode plugin docs and probing
npm/GitHub availability. This skill shortcuts that exploration — when building
a plugin, start from the lifecycle template and event table above rather than
re-reading docs from scratch.

## daemon-env-var-gotcha

- ## CRITICAL: env vars in ~/.zshrc do NOT reach daemon/launchd-launched opencode

The env-var config channel above (point 2) assumes opencode is launched from
an INTERACTIVE shell that sourced ~/.zshrc. That assumption BREAKS when
opencode is launched by launchd, a daemon, a GUI app, or any non-interactive
non-login process — which is the common case for "opencode --auto" spawned
by a plugin/server (e.g. herdr server) under launchd.

zsh sourcing rules:
- ~/.zshenv   — ALWAYS sourced (every shell: interactive, non-interactive, login, non-login)
- ~/.zprofile — login shells only
- ~/.zshrc    — INTERACTIVE shells only
- ~/.zlogin   — login shells only

So a launchd -> daemon -> zsh -> opencode launch chain sources ONLY ~/.zshenv.
Env vars in ~/.zshrc (NOTIFY_BACKEND, NTFY_URL, BARK_URL, etc.) are INVISIBLE
to the plugin, which silently falls back to its defaults (e.g. backend="bark").
Symptom: the plugin logs "BARK_URL not set" even though BARK_URL and
NOTIFY_BACKEND=ntfy are both correctly exported in ~/.zshrc.

### Fix (prefer the config-layer fix for daemon-resilience)

1. **Plugin options in opencode.json (PREFERRED — no shell-sourcing dependency):**
   Move the config OUT of env vars entirely and into opencode.json plugin
   options. This works regardless of how opencode is launched:
   ```json
   ["~/github/opencode-push", { "backend": "ntfy", "ntfy_url": "http://gb10", "ntfy_topic": "opencode", "host": "mac" }]
   ```
   (tuple form — see schema note in "Configuration" section).
   If switching from the auto-load symlink (Mechanism A) to the plugin-array
   (Mechanism B) to pass options, REMOVE the symlink first to avoid
   double-loading the plugin.

2. **Move exports to ~/.zshenv (shell-layer fix):**
   If you want to keep the env-var pattern, move the exports from ~/.zshrc to
   ~/.zshenv so every zsh invocation (including daemon-spawned) sources them.
   Downside: ~/.zshenv is sourced by EVERY shell including scripts (slightly
   heavier), and it does not help if opencode is ever launched by a non-zsh
   process.

### Diagnostic chain (when env-var config silently fails for a plugin)

1. Confirm the env vars ARE set in ~/.zshrc (grep the file).
2. Check the RUNNING opencode process's actual env: the opencode Bash tool
   inherits opencode's environment, so `echo $NOTIFY_BACKEND` from the bash
   tool reveals what opencode actually sees (unset = not inherited).
3. Trace the launch chain (`ps -o ppid= -p <opencode-pid>` repeatedly, or
   `pstree -p`) to find a launchd/daemon parent (e.g. herdr server under
   launchd) — a daemon parent means a non-interactive non-login shell.
4. Conclude: env vars in ~/.zshrc cannot reach a launchd-spawned opencode.

Discovered 2026-07-09 debugging opencode-push: launchd -> herdr server ->
zsh -> opencode --auto never sourced ~/.zshrc, so NOTIFY_BACKEND/NTFY_URL
were invisible and the plugin fell back to backend="bark". Fixed via
opencode.json plugin options. Sibling of memory entry on the same gotcha
(zsh sourcing hierarchy + launchd daemon launch chain) and of the bash
equivalent (SSH non-interactive shells don't source ~/.bashrc).

## description-zshenv-fix

- The skill description and Configuration section still say '~/.zshrc' for BARK_URL/API-key env vars, but the skill's own daemon-env-var-gotcha section (added 07-09) proves ~/.zshrc is INVISIBLE to daemon/launchd-launched opencode — ~/.zshenv is required (sourced by every shell). Both the YAML description '(5) Secrets (BARK_URL, API keys) go in ~/.zshrc env vars' and the Configuration section header 'Environment variables (in ~/.zshrc)' must say ~/.zshenv, not ~/.zshrc, to match the gotcha section and prevent agents from putting secrets in the wrong file. Confirmed 07-11: the assistant in the bark-setup conversation correctly put BARK_URL in ~/.zshenv (applying the 07-09 lesson), not ~/.zshrc.

## diagnostic-chain-reorder

- ### Diagnostic chain (when env-var config silently fails for a plugin) — REVISED 07-11

STEP 0 (DO THIS FIRST — before grepping any config files): Check the RUNNING opencode process's actual env. The opencode Bash tool inherits opencode's environment, so 'echo $NOTIFY_BACKEND' / 'echo $NTFY_URL' from the bash tool reveals what opencode ACTUALLY sees. On macOS, 'ps eww -p <opencode-pid>' shows the full env of a specific process. The running process env is GROUND TRUTH — it may contain stale values from a previous launch context that NO current config file reflects (e.g. NTFY_URL was set in ~/.zshenv at launch time, then removed, but the still-running daemon retains it). Grepping config files first leads to CIRCULAR REASONING when the source is a stale runtime value — confirmed 07-11 when the agent spent 4+ turns grepping zshenv/zshrc/opencode.json/launchd without finding gb10, because the value lived only in the running daemon's env.

STEP 1: If step 0 reveals the env var is unset (not inherited), grep config files to confirm WHERE it should be set: ~/.zshenv (always sourced), ~/.zshrc (interactive only), opencode.json plugin options.

STEP 2: Trace the launch chain ('ps -o ppid= -p <opencode-pid>' repeatedly, or 'pstree -p') to find a launchd/daemon parent (e.g. herdr server under launchd) — a daemon parent means a non-interactive non-login shell that sources ONLY ~/.zshenv.

STEP 3: Conclude — if the env var is in ~/.zshrc but the launch chain is daemon/launchd, the var cannot reach opencode. Fix via opencode.json plugin options (preferred) or move exports to ~/.zshenv.

## plugin-env-caching-stale-interactive-shell

- ## Plugin env caching + stale interactive shells (07-11)

The daemon-env-var-gotcha above covers 'daemon doesn't source ~/.zshrc.' This section covers the COMPLEMENT failure mode and the load-time caching that makes both unfixable without restart.

### Plugins cache env at LOAD TIME

opencode-push (and any plugin following the same pattern) reads env into MODULE-LEVEL CONSTS once at module load:
```typescript
const backend = process.env.NOTIFY_BACKEND || "bark"  // opencode-push.ts:32
```
This const is evaluated ONCE when the plugin module is imported. No subsequent config edit, shell re-source, or env mutation changes it for the lifetime of the running opencode process. This means:
- Editing ~/.zshenv or ~/.zshrc fixes FUTURE launches only.
- `source ~/.zshrc` in the current shell does NOT help — the plugin already cached the old value.
- The ONLY fix for a running session with wrong cached env is to RESTART opencode from a FRESH shell.

### Stale interactive shell (complement of the daemon case)

The daemon case is 'env vars in ~/.zshrc invisible to launchd-spawned opencode.' The interactive case is the REVERSE: env vars are correctly set in ~/.zshrc NOW, but the running opencode inherited OLD values because its PARENT SHELL (a terminal tab) was opened BEFORE the config edit.

Chain: terminal-tab-opened-09:00AM (sources old ~/.zshrc with NOTIFY_BACKEND=ntfy) → opencode-launched-07:03PM from that tab (inherits stale ntfy env) → user-edits-~/.zshrc-to-bark-at-08:00PM → running opencode STILL has ntfy (cached at launch). New terminal tabs opened after 08:00PM will correctly source bark.

This is why STEP 0 of the diagnostic chain (check RUNNING process env) is essential — the stale value exists ONLY in the running process, and NO current config file reflects it. Grepping config files will show bark everywhere (correct for the future) while the running session silently hits the old ntfy/gb10 backend.

### Fix sequence for stale interactive shells

The config is ALREADY correct (unlike the daemon case where vars are in the wrong file). The only issue is stale runtime env. Fix:
```bash
unset NOTIFY_BACKEND NTFY_URL NTFY_TOPIC   # clear stale vars in current shell
exec zsh                                    # re-source ~/.zshenv + ~/.zshrc
# then relaunch opencode from this fresh shell
```
Or simpler: open a NEW terminal tab (sources current config) and launch opencode from there. Belt-and-suspenders: set the backend selector in ~/.zshenv (sourced by ALL shells) so even non-interactive/daemon paths default correctly, reducing the window for staleness.

### Verification discipline

Do NOT claim 'this should fix it' for the CURRENT running session after editing config — the plugin cached env at load time. Be explicit: 'config is fixed for future sessions; current sessions need restart.' (07-11)

## reinstall-mechanism-accuracy

- The example sentence at the end of the 'Reinstalling / updating a local plugin' section says 'the plugin is path-referenced in opencode.json' for opencode-push. This was the 07-10 observation, but as of 07-14 the plugin is actually installed via Mechanism A (symlink at ~/.config/opencode/plugins/opencode-push.ts -> ~/github/opencode-push/index.ts), NOT via opencode.json. The procedure is identical for both (git pull + restart), but do NOT assume a specific mechanism — run 'ls -la ~/.config/opencode/plugins/' and check opencode.json to determine which is in use before acting. opencode-push has been observed on BOTH mechanisms across sessions.

## opencode-push-config-file

- As of the 07-14 update, opencode-push supports a THIRD config channel: a JSON config file at ~/.config/opencode-push.json (see config.example.json in the repo). Config precedence is: env vars > config file > defaults. The existing two channels (plugin options in opencode.json, env vars in ~/.zshenv) still work unchanged. The 07-14 update also switched from a curl subprocess to native fetch internally — no action needed if you were using the plugin before. If a reinstall pulls new updates, check config.example.json for newly-added config keys.


## Original description (preserved on trim, 2026-07-19)

Build opencode (opencode-ai) plugins — the lifecycle pattern, the event surface for notifications/hooks, and local from-source install. Use when creating an opencode plugin, writing a notification/hook plugin, wiring session.idle/session.error events, deciding how to install a local plugin (symlink vs plugin array), reading the @opencode-ai/plugin types, using the Bun $ shell helper inside a plugin, checking npm/GitHub name availability for an opencode plugin package, or configuring plugin secrets via env vars vs plugin options. ALSO use when EDITING or FIXING opencode.json plugin entries, debugging opencode config validation errors (e.g. 'Expected string | array, got {...} plugin.N'), fixing a plugin not loading or not firing events, reconciling conflicting plugin env vars across .zshenv and .zshrc, or reinstalling/updating a local plugin — the schema note in the Configuration section documents that the plugin array accepts strings OR [path, options] tuples but NOT {path, options} objects. Covers the non-obvious facts discovered 2026-07-09 building opencode-push: (1) the Plugin export shape is 'const plugin: Plugin = async ({ project, client, $, directory, worktree }, options) => { return { event: async ({ event }) => {...} } }' — the second arg is the plugin OPTIONS object declared in opencode.json, and the returned object has an 'event' handler keyed by event.type. (2) session.idle is THE event for 'turn complete / agent finished waiting' (not session.complete or session.end); session.error fires on errors. The canonical notification example uses 'if (event.type === "session.idle")'. (3) The $ helper is a Bun shell template literal for subprocess calls (e.g. $`curl -s ...`); template expressions are auto-escaped. (4) TWO install mechanisms: local plugins AUTO-LOAD from ~/.config/opencode/plugins/*.ts (symlink to the git repo source-of-truth works); OR reference a file path in the opencode.json plugin array. (5) Secrets (BARK_URL, API keys) go in ~/.zshenv env vars (NOT ~/.zshrc — daemon-launched opencode does not source ~/.zshrc; see daemon-env-var-gotcha) read via process.env — NEVER committed to the plugin repo; plugin options in opencode.json are the alternative (options take precedence over env). (6) npm/GitHub name collisions are common for opencode plugins: opencode-notify, opencode-notification, opencode-alert are ALL TAKEN (npm 200); check availability with 'curl -s -o /dev/null -w "%{http_code}" https://registry.npmjs.org/<name>' (404=free, 200=taken) before committing to a name.

## v1 vs v2 (beta) compatibility

- OpenCode v1 and v2 differ on EVERY plugin surface — check the binary before assuming the API (learned 2026-08-29, opencode-autorepo v2 migration):
- Binary: v1 `opencode`; v2 beta `opencode2` (installed side-by-side during the migration window).
- Config key in opencode.json: v1's primary key is `plugin`; v2 uses `plugins` — but the keys are NOT exclusive per binary: v1 ALSO parses `plugins` (2026-09-01 log evidence: registering a v2 plain-object plugin under `plugins` makes v1 error with "must default export an object with server()" — that error is PROOF v1 parsed the key; v1 just requires the function-export shell shape), and v2 expects `plugins` entries to point at DIRECTORIES, not individual files. E2E-TEST GOTCHA (verified 2026-09-01): a persistent "opencode2 serve --service" process survives across runs and "opencode2 run" ATTACHES to it (your own test commands show up in the pre-existing service's logs); plugins load at SERVICE STARTUP, so a plugin installed after the service started never loads in attached runs — before reading a missing plugin log line as "plugin did not load", check for a stale service (ps aux | grep opencode2 serve), note its start time and cwd, and kill/restart it before re-running the E2E turn. v1 (opencode run) spawns a fresh process per run, so v1 E2E is not affected the same way. Verification discipline (Eric correction 2026-09-01): verify plugin/config loading behavior against trusted official opencode documentation rather than concluding from log inference or inherited skill assumptions.
- Export shape: v1 plugins export a FUNCTION (async ({ $, directory, project, client, worktree }, options) => ({ event: ... })); v2 plugins export a plain OBJECT.
- Session DB tables (for plugins that query history): v1 `session`/`message`/`part`; v2 `session_v2`/`session_message` (introspect before hardcoding names).
- CLI: v1 has `opencode session delete <id>`; v2 has NO session-delete subcommand — use `opencode2 api delete /api/session/<id>`. v2 also has NO schedule subcommand.
To support BOTH, factor shared logic into a core module (e.g. autolearn-core.js) imported by per-version entrypoints (autolearn.js v1 function-export, autolearn-v2.js v2 plain-object), and gate docs/installer/verification code on the binary detected.
- Verified v2 plugin API (opencode-autolearn v2 shell review, 2026-08-29): v2 plugins export a plain OBJECT `{ id, setup(ctx) }` (id string + setup function) — NOT the v1 async-function export. Events arrive via `ctx.event.subscribe`, an ASYNC ITERABLE consumed with `for await`, not the v1 returned `event` handler. Verified v2 event shapes: session.created {sessionID, title, parentID}; session.inbox.enqueued {sessionID, inboxID, item:{type, payload:{text}}}; session.step.started {sessionID, assistantMessageID, agent, model}; session.text.ended {sessionID, assistantMessageID, text}; session.step.ended {sessionID, assistantMessageID, ...} (remaining fields truncated in the source prompt — verify before relying on them). Dual-binary gotchas surfaced by the same review: (1) BINARY SHADOWING — a shared subprocess wrapper that resolves its binary from PATH defaults silently routes v1-spawned work to `opencode2` on dual-install machines, contradicting docs; pin the binary explicitly per caller (e.g. env: {AUTOLEARN_OPENCODE_BIN: 'opencode'} at every v1 call site) rather than trusting the wrapper's PATH preference. (2) MULTI-FILE PLUGIN INSTALLS — a per-version entrypoint importing `./autolearn-core.js` breaks if an installer copies only the entrypoint file; the installer must copy core + ALL version shells together.

- Core-module RUNTIME PORTABILITY (dual-shell packages, 2026-09-01 opencode-push): a shared core imported by BOTH the v1 (Node) and v2 (Bun) shells must use Node-standard APIs only — node:fs/promises, global fetch, etc. NEVER put Bun.file or other Bun.* globals in the core: Bun-only APIs tie the core to the Bun runtime and break the v1 Node shell, while fs/promises works under BOTH runtimes (Bun implements Node APIs). Keep Bun conveniences (Bun.file, $ shell) in the per-runtime shells; when the npm package ships a shim/installer, the shim dispatches per runtime to the right shell. Smoking gun for the miss: core reads config via Bun.file and the Node shell crashes or drifts from the Bun path.
## Verifying plugin changes in isolation

- When testing a modified or variant plugin (e.g. a v2 rewrite or a local patch) on a machine where the plugin is also installed globally, do NOT test in place. Build an isolated harness that (1) runs the variant and asserts a load-time marker string appears (print e.g. 'PLUGIN LOADED (v1)' at plugin init, grep the output for it), (2) exercises the COMPLETE pipeline end-to-end through spawn — not just import — and (3) restores the global plugin installation afterward. This yields binary evidence of both load and end-to-end function without corrupting the live install. Proven in the autolearn v1/v2 plugin-shell work (v2probe, 2026-08-29): each shell verified in isolation with its own marker + full spawn pipeline before any global swap.

## plugin-auto-discovery-loads-every-file

- PLUGIN AUTO-DISCOVERY LOADS EVERY FILE IN THE PLUGINS DIR (2026-08-29, autolearn v2 install): opencode plugin discovery auto-discovers EVERY file in ~/.config/opencode/plugins/ and schema-validates each as a plugin entrypoint. A shared/helper/core module (e.g. autolearn-core.js) placed there as a sibling of the plugin shells gets loaded as a plugin candidate, FAILS schema validation, and emits a warning line on every plugin listing. TRIGGER: any multi-file plugin whose support modules live in the plugins directory. ROOT CAUSE: discovery has no manifest — every file is treated as a plugin. FIX (verified): rename the core module to an extension discovery ignores — .mjs works — so it stays a sibling (identical repo/installed layout, imports unchanged in spirit) while dodging discovery; update all import references. Symptom: plugin listing shows 'autolearn (active)' plus a stray schema-validation warning naming the core file. Rule: NEVER ship a plain-.js helper module inside the opencode plugins directory.

## installer-races-live-plugin-activation

- INSTALLER RACES LIVE PLUGIN ACTIVATION — the tmp-file collision is DETERMINISTIC during install, not transient (2026-08-29, autolearn v2 install.sh, v2probe): running an installer (install.sh) against a LIVE opencode service that has just had the plugin wired in produces a guaranteed registry-write collision. TRIGGER SEQUENCE: install step 3 patches opencode.json -> the running service hot-reloads config -> the newly-active v2 plugin's composeContext() fires immediately and spawns 'memory compose' -> its registry.save() write (fixed tmp filename memories.jsonl.tmp) collides with install step 4's 'retention score' write, which uses the SAME tmp filename before its os.replace -> installer aborts mid-step-4. WHY NOT TRANSIENT: unlike an ambient concurrent-writer race (retry and it succeeds — see the atomic-write memory), this collision REFIRES on every retry because each config patch re-triggers plugin activation; the deterministic chain is config-patch -> hot-reload -> compose spawn -> write. FIX (structural, in the plugin repo's registry.py): make registry.save() use a PID-unique tmp filename (e.g. memories.jsonl.<pid>.tmp or .<pid>.<uuid>.tmp) so concurrent writers never share a temp path; this is the same canonical fix already identified for the ambient race, and the installer context is the case that makes it MANDATORY rather than nice-to-have. Installer-side hardening (secondary): order install steps so no two steps write the same store, or quiesce/restart the service between the config patch and store-writing steps. Related: plugin-auto-discovery-loads-every-file (same install arc).

## opencode2 (v2 beta) dual-stack plugins

- Verified live 2026-08-29 during the autolearn v2-compat migration. The machine runs opencode (v1) and opencode2 (v2 beta) side-by-side; a plugin supporting both uses ONE shared core + TWO thin shells. (1) LOADING: v1 loads function-export modules via the 'plugin' config key; v2 loads plain-object plugin exports via the 'plugins' (plural) config key. (2) V2 EVENT SURFACE (verified against live beta): 'session.inbox.enqueued' = user text enqueued; 'session.text.ended' + 'session.step.ended' = assistant turn text/steps; 'session.execution.*' = turn boundaries. Do NOT assume v1 event names carry over. (3) SHARED-CORE EXTENSION TRICK: put shared logic in a '.mjs' module (e.g. autolearn-core.mjs) imported by both shells — v2's plugin auto-discovery ignores .mjs files, so the core is not double-loaded as a plugin. (4) V2 CLI GOTCHAS: v2 has NO 'session delete' CLI command — use 'opencode2 api delete' for cleanup; run isolated v2 end-to-end tests with '--standalone'. (5) RECURSION GUARD: v2 plugins run inside the shared service (not per-session), so reviewer-style recursion guards need BOTH an env-var flag AND agent/title marking — a single guard is insufficient (env markers do not propagate through every spawn path; title checks miss renames/restarts). (6) VERSION-AWARE WRAPPERS: any code that spawns opencode from a plugin must pin the binary per session family — v1 sessions invoke 'opencode', v2 sessions invoke 'opencode2'. (7) DUAL-INSTALL DB MIRRORING: with both binaries in use, messages are MIRRORED into BOTH table families (session/message AND session_v2/session_message); any plugin or search aggregating across both must dedupe (autolearn skips ~133k mirrored messages).

- SECOND APPLICATION — the pattern generalizes across plugins (2026-09-01, opencode-push): commissioned as the second plugin converted to dual-shell after autolearn, same structure (shared .mjs core + v1 function-export shell + v2 plain-object shell; BOTH plugin and plugins keys patched into the SHARED opencode.json; a single dual-format export file is REJECTED — the v1 function-export and v2 plain-object shapes are mutually exclusive, per opencode-autolearn design doc Decision 14). When asked to make ANY plugin work with both binaries, START from this section instead of re-deriving. PER-BINARY INSTALL: a dual-shell plugin must be installed/registered for EACH binary — a v1-only install leaves opencode2 without the plugin (the opencode-push commission included an explicit reinstall-for-opencode2 step).

- V2 SHARED SERVICE BOOTS ONE PLUGIN INSTANCE PER PROJECT LOCATION (2026-09-01, opencode-push unified-shell arc): the v2 service instantiates the plugin once per project directory it serves, NOT once per process — a module-level GLOBAL guard or fixed-string dedupe latch silences every project after the first that trips it. Scope guards/dedupe keys per directory, and prefer the session ID (when available) over a fixed string as the dedupe key so two different sessions finishing inside the dedupe window (e.g. 5s) don't swallow each other's events. Refines point (5) below-the-fold reading: 'shared service, not per-session' means per-LOCATION instance, not per-binary global.

- THE '2.0' BRANCH SOURCE IS NOT AUTHORITATIVE FOR THE INSTALLED BETA BINARY (2026-09-01): grepping the repo's 2.0 branch to predict the installed opencode2 beta's plugin-loader contract surfaced a DIFFERENT loader lineage than the live binary actually exhibits — branch source and shipped beta have diverged. Treat branch source as a hint only; verify loader/plugin behavior against the LIVE binary (probe loads, logs, E2E), and do authoritative source-reading from the INSTALLED version's tag (as the v1.18.25 readV1Plugin finding did).

## v1 object-plugin support (readV1Plugin detect mode) — corrects the function-export premise

- **v1.18.25 NATIVELY SUPPORTS OBJECT PLUGINS (source-verified 2026-09-01 from the v1.18.25 tag of github.com/anomalyco/opencode; corrects the 'v1 just requires the function-export shell shape' framing above and Decision 14's 'mutually exclusive shapes' premise).** The v1 loader readV1Plugin runs in mode 'detect': a default-exported OBJECT with 'id' + 'server(input)' is accepted — v1 calls server(input, options) and expects hooks returned; bare function exports fall through as the legacy path. The v1 error 'must default export an object with server()' therefore means 'your object lacked a server method', NOT 'objects unsupported' — exactly why a v2 plain-object shell { id, setup } throws it. UNIFIED SHELL - DESIGN ADOPTED (later same-day slice 2026-09-01): ONE default export { id, setup(ctx), server(input) } is the winning dual-binary shape - v2 live-confirmed loading the { id, setup } object via plugins-directory auto-discovery, v1 source-confirmed invoking server(input, options) and expecting hooks back; obsoletes the two-shell pattern. Install via DIRECTORY AUTO-DISCOVERY ONLY - no plugin/plugins config keys (file paths listed there trigger v2's 'configured plugin path must be a directory' warnings; strip them from opencode.json and remove any stale dual-shell file). Residual caveat: confirm in a live v2 session that its module schema tolerates the extra 'server' key before declaring fully verified. Related log facts (2026-09-01, opencode-push arc): v1's object-export error is AMBIENT NOISE predating any new install (first fired Aug 29 when autolearn-v2.js landed; 162 occurrences since) — do not attribute it to your own change; v2's plugins-DIRECTORY auto-discovery DOES load loose .js files (INFO 'loading plugin id=...') while the 'configured plugin path must be a directory' warning fires only for file paths listed in the plugin/plugins CONFIG keys; and plugin console.error inside the shared v2 service may not reach the service log — a missing log line from your plugin is NOT proof of failure.

## unified-shell corollaries: 2.0-branch source caveat, per-directory guards, session-ID dedupe (2026-09-01)

- THE REPO'S 2.0 BRANCH IS NOT THE BETA BINARY'S LOADER: the 2.0 branch carries the SAME server-plugin contract as v1 ({ id, server(input) -> hooks }, no setup), yet the live beta binary loaded a { id, setup } object - the beta's loader lineage DIFFERS from the branch source. When verifying plugin loader semantics, cite the v1.18.25 TAG source (readV1Plugin) as authoritative and never infer beta behavior from branch source alone.
- PER-DIRECTORY GUARDS, NOT GLOBAL: v2's shared service boots ONE plugin instance PER LOCATION (project directory). A global module-level 'already ran' guard silences every project after the first - scope recursion/dedupe guards per directory.
- DEDUPE KEY = SESSION ID WHEN AVAILABLE: any notification/dedupe window keyed on a fixed string makes two DIFFERENT sessions finishing within the window swallow each other's events; key on the session id when the platform provides one, and only fall back to a scoped constant when absent.

## V2 dual-binary debugging refinements (2026-09-01)

- - '--standalone' is a flag of the 'run' SUBCOMMAND: 'opencode2 run --standalone'. Root-level placement ('opencode2 --standalone run') fails with a flag-placement error; when the documented v2 E2E invocation does not boot the private server, check placement first.

- INSTALLED-COPY INSTRUMENTATION (the deliberate in-place COMPLEMENT of the isolated-harness rule above, which governs testing VARIANTS): when a plugin LOADS cleanly in v2 (no schema errors) but produces no visible effect ('no sent line'), instrument the INSTALLED copy under ~/.config/opencode/plugins/ (append-to-file filesystem markers at each export/entry point and inside each event handler) to learn exactly which entry point each binary (v1 vs v2) actually calls and which events actually arrive. Do NOT instrument the repo source for this purpose: the binary loads the installed copy, so repo-side markers never execute and yield false 'no effect' conclusions. Clean the markers up afterward.

- LOG-GREP FALSE-NEGATIVE GUARD: when checking streamed opencode output for a turn-end log/marker line, do not truncate with 'head -N' - truncation can cut off the line and produce a false 'absent' conclusion. Re-run the grep with a tighter pattern and NO head before concluding the marker never fired (proven in this arc: the untruncated rerun confirmed the marker genuinely absent rather than hidden).

## Notification-spam debugging: installed-copy inspection, errored-path dedupe asymmetry, event-dump hook (2026-09-04)

- - ERRORED-PATH DEDUPE ASYMMETRY (root cause of 'TON of errored pushes', found 2026-09-04): the installed opencode-push notifies ERRORED on BOTH 'session.execution.failed' AND 'session.error' with NO dedupe - only the FINISHED path is deduped. Dual event emissions therefore multiply errored notifications. Generalizes the dedupe guidance above: dedupe coverage must span ALL notify paths (errored AND finished), not just the happy path - audit every notify call site, not only the success branch.
- DEBUG THE INSTALLED COPY, NOT THE REPO SOURCE: the actually-installed plugin was a BUNDLED PAIR (opencode-push.js + opencode-push-core.mjs) that diverges from the repo index.ts - reading repo source misleads about live behavior (handler set, dedupe coverage). Locate the installed files first (plugin dir / symlink target / bundled output) and read THOSE when diagnosing what the running plugin actually does.
- EVENT-DUMP DEBUG HOOK: the installed plugin writes every received event to /tmp/ocp-event-*.txt - check there FIRST when debugging which events actually arrive. May be empty if tmp was cleaned or the service restarted; absence of debug files is NOT proof no events fired.

## ## Diagnosing the RUNNING opencode-push plugin: installed-files drift and the errored-path dedupe gap (2026-09-04)

- ## Diagnosing the RUNNING opencode-push plugin: installed-files drift and the errored-path dedupe gap (2026-09-04)

- ROOT CAUSE OF "a TON of errored opencode-push notifications" (2026-09-04): the INSTALLED plugin pushed "errored" on BOTH session.execution.failed AND session.error with NO dedupe - only the "finished" path had a dedupe window - so one underlying failure produced two pushes, and v2 execution.* turn-boundary events multiplied them further. Fix direction: give the errored path the same session-ID-keyed dedupe window as the finished path (see the per-directory guards / session-ID dedupe corollaries above).
- READ THE INSTALLED FILES, NOT THE REPO SOURCE: the installed generation was opencode-push.js + shared opencode-push-core.mjs (unified-shell auto-discovery layout) while the repo still showed index.ts - reading repo source misleads about what is actually running. First step of any plugin-behavior diagnosis: locate the actually-loaded file(s) (ls -la ~/.config/opencode/plugins/ plus the opencode.json plugin/plugins keys) and read THOSE, then reconcile with git -C ~/github/opencode-push log --oneline -5 to see whether the repo is ahead of the install. Extends the install-mechanism-drift note above: do not assume even the FILE SET - the installed generation can differ from repo HEAD.
- DEBUG HOOK: the installed plugin writes every received event to /tmp/ocp-event-*.txt. Absent files mean the hook has not fired since /tmp was last cleaned (or the installed generation lacks the hook), NOT that the plugin is dead.

## installed-copy drift and error-push spam diagnosis (2026-09-04)

- - DEBUG THE INSTALLED COPY, NOT REPO SOURCE: the live install was opencode-push.js + opencode-push-core.mjs (compiled pair; .mjs core per the discovery-dodge trick) while the repo ships index.ts — the 07-14 symlink note (opencode-push.ts -> index.ts) is stale for the current install. Before diagnosing plugin behavior, 'ls -la ~/.config/opencode/plugins/' and read the ACTUAL files; repo source may not be what opencode loaded.
- ERROR-PUSH SPAM ROOT CAUSE (Eric: 'a TON of opencode-pushes errorred out'): the installed plugin pushes 'errored' for BOTH session.execution.failed (v2) and session.error (v1) with NO dedupe — only the 'finished' path is deduped. Fix in the plugin repo: dedupe error notifications under the same per-directory/session-ID key discipline as the 09-01 corollaries, and treat the two event names as ONE failure alias so a single failure does not push twice.
- DIAGNOSTIC AIDS: the installed plugin's debug hook writes every received event to /tmp/ocp-event-*.txt (no files = hook silent, not plugin dead); opencode.log contained NO error events in its last 200MB despite active spam — absence of events in the main log tail does NOT mean errors did not fire. See memory opencode-main-log for the unbounded 4.3GB log fact (no rotation policy documented).

## v2-cutover-2026-09-14

### The 2026-09-14 V1-to-V2 cutover (v2.0.3 intentionally dropped the V1 plugin API)

- On v2.0.3, plugins still exporting the old V1 shape HARD-FAIL at load — the drop is INTENTIONAL (12 of 14 failures in the cutover were V1-shape exports; do not debug them as bugs). Port-in-place recipe that verified clean: keep helpers/logic VERBATIM, change only the export wrapper + hook registration, then line-count + marker check before/after (git-ai.ts 515-to-533 lines, 19 helper markers intact — the large-file-edit-truncation guardrail).
- NEW V2 event/API facts (from the ocp-probe log, the authoritative record of the real event vocabulary): "permission.asked" is the V2 permission-prompt event — NOT "permission.updated"; "session.execution.*" confirmed for turn lifecycle; "ctx.session.get" for session data. Notify-style plugins need "ctx.event.subscribe" + these names.
- REGEX PORTING GOTCHA: PCRE inline modifiers are REJECTED by the JS runtime — a "(?i)" inline modifier in a ported plugin throws at load; convert to the flag argument (new RegExp(src, "i") or a literal with the i flag).
- CONFIG TRAPS that outlive the port: (1) replace dead V1 "plugin": [...] entries with a single "plugins": [] — explicit FILE entries under "plugins" trigger 'must be a directory' warnings when discovery already loads them; (2) AUDIT THE WHOLE opencode.json FOR DUPLICATE KEYS before concluding a warning persists: a pre-existing duplicate "plugins" key at the JSON tail (last-key-wins) shadowed the edited key and reproduced the warning after the fix; (3) drop dead deps from ~/.config/opencode/package.json but KEEP the live ones (detect-terminal + node-notifier are used by notify.ts).
- VERIFICATION PROCEDURE: throwaway "opencode run" in a FRESH directory forces a full plugin load; then grep the log delta for 'failed to load plugin'. FALSE-POSITIVE GUARD (sibling of the false-negative head-truncation guard): the service LOGS YOUR OWN SHELL COMMANDS, so grepping for a plugin name matches your own earlier grep — before calling a log-delta match a failure, target the test run by TIMESTAMP or exclude self-logged command lines.
- V1-only plugins go to a DATED REVERSIBLE ARCHIVE (~/.config/opencode/archive-v1-plugins-2026-09-14/) with a RESTORE.md explaining each file — never delete outright.
- RESIDUAL (as of 2026-09-14): eric-ormoni/opencode-scheduler failed during npm install itself under the cutover — the commissioned dual-form scheduler fork is still not landed (see wiki pattern opencode-plugin-dual-form-v1-v2 + memory #2699).
