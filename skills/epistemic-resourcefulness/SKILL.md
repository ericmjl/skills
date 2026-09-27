---
name: epistemic-resourcefulness
description: >-
  Breaks the cycle of repeated failed attempts by redirecting to the authoritative source of truth before trying again. Trigger when: the same command or query has failed 2+ times; output is garbled/binary; guessed field names, endpoints, or flags keep erroring; scanning yields no signal; you are about to say 'I don't have access to X' (a CLI may exist: gog = Gmail; check which/brew and script logs first); you are about to label a step 'manual' or 'human-only' (the API likely supports it — introspect input types before delegating to the human); you are reconstructing what was SAID in past communication (grep derived notes once, then go to the mailbox thread); or you are about to end a turn asking Eric to check his own inbox for a code/link, or parked at a sign-in screen handing him the auth step (fetch the message via gog or mint a session JWT yourself — an inbox handoff dresses an agent-executable step as a blocker).
license: MIT
---

# Epistemic Resourcefulness

Before interacting with any unfamiliar system, **find the authoritative source of truth
about its structure**. Do not guess, scan blindly, or trial-and-error your way to an
answer when a definitive source exists.

## The Core Rule

> For every structured system, there is an authoritative description of that structure.
> Locate it first. Then act.

## Quick Reference: Authoritative Sources by System Type

| System | Authoritative source | How to access |
|--------|---------------------|---------------|
| SQLite database | Schema | `sqlite3 file.db ".schema"` |
| Any SQL DB | Table/column info | `DESCRIBE table` / `information_schema` |
| CLI tool | Help text | `tool --help` or `man tool` |
| Installed CLI tools | Package-manager manifest | `brew list` / `brew info`, `uv tool list` |
| REST API | OpenAPI/Swagger spec | `/docs`, `/openapi.json`, or repo |
| Python package | Installed interface | `python -c "import pkg; help(pkg)"` |
| File format | Format library docs | Check PyPI/npm for a parser library |
| Config system | Schema/defaults | Config file comments, `--show-config` |
| Running process | Its own API | Check docs for management interface |
| Codebase | Entry points | README, AGENTS.md, `__init__.py`, `index.ts` |
| npm/Python project | Dependencies | `package.json`, `pyproject.toml` |

## The Anti-Pattern: Brute-Forcing

**Brute-forcing** looks like:
- Reading a binary file byte-by-byte without knowing its format
- Querying a DB with guessed column names
- Scanning every file in a directory when a manifest exists
- Repeating variations of a failed command hoping one works
- Trying API endpoints at random

Brute-forcing is wasteful and unreliable. It signals that the agent skipped the investigation step.

## The Pattern: Investigate First

When facing an unfamiliar system:

1. **Identify what kind of system it is** (database? CLI? API? file format?)
2. **Look up the authoritative source** for that system type (see table above)
3. **Retrieve the structure** (schema, help text, spec, manifest)
4. **Then act** with knowledge of the actual structure

## Worked Example

**Task:** Read conversation history from the OpenCode SQLite database.

**Brute-force approach** (wrong):
```bash
cat ~/.local/share/opencode/opencode.db   # binary garbage
ls ~/.local/share/opencode/               # scanning around
```

**Resourceful approach** (correct):
```bash
# Step 1: Identify - it's SQLite
# Step 2: Authoritative source = schema
sqlite3 ~/.local/share/opencode/opencode.db ".tables"
sqlite3 ~/.local/share/opencode/opencode.db ".schema session"
# Step 3: Now query with known column names
sqlite3 ~/.local/share/opencode/opencode.db \
  "SELECT id, title FROM session ORDER BY time_created DESC LIMIT 5;"
```

## A Note on "Obvious" Systems

Even systems you think you know may have changed or have non-obvious quirks in this
specific environment. When something isn't working as expected, resist the urge to
iterate blindly - treat it as an unfamiliar system and re-run the investigation step.

## User-Named Tool Not on PATH

When the **user names a CLI tool** and `which <name>` / `command -v <name>` fails,
the authoritative source for what is actually installed is the **package-manager
manifest** — query it BEFORE speculating the user meant a different tool (gcloud?
a typo? an alias?). Check in order:

1. `brew list | grep -i <name>` and `brew info <name>` — the info output lists the
   opt prefix and linked `bin/` symlinks, so the **real binary names** are right there
2. `ls /opt/homebrew/bin | grep -i <partial>`
3. `uv tool list`, `pixi global list`, `npm ls -g --depth=0`
4. `grep -i <name> ~/.zshrc ~/.zprofile` for aliases

**Root cause:** users refer to tools by their package/formula name, but PATH lookup
is by *binary* name, and the two frequently differ — brew formula `gogcli` (Google
Suite CLI) installs a binary named `gog`; the tool IS installed and authenticated
while `which gogcli` fails.

**Worked failure (2026-08-14):** user said "use gogcli"; the assistant searched
PATH/pixi/uv/npm but never brew, burned 3 turns speculating about `gcloud` and
typos, and drew a "Take action now." interrupt. One `brew list | grep -i gog`
would have answered instantly.

## Claiming "I Don't Have Access to X" When a CLI Exists

Before telling the user "I don't have access to X" (email, calendar, cloud
storage, any external service), CHECK THE ENVIRONMENT AND REPO EVIDENCE FIRST —
the capability often exists as a CLI with no MCP tool in the session.

**Trigger condition:** the user asks you to check/read/send something in an
external service and your first instinct is "no such tool is available."

**Root cause:** equating "no MCP tool in this session" with "no capability on
this machine" — while scheduled jobs and scripts in the repo contain working
invocations of exactly that capability.

**Fix procedure, in order:**

1. `which <likely-cli>` — for email: `which gog`; the gog CLI provides Gmail
   (`gog gmail messages search <query>`)
2. Grep scheduled-job definitions/logs and scripts for prior invocations —
   `gog gmail messages search label:...` appeared verbatim in the
   venue-inbox-monitor job logs while the assistant claimed no email access
   THREE times
3. Check `~/.zshrc` aliases and `brew list` (see the User-Named Tool section)

4. When the CLI exists but is BROKEN (dead token, or re-auth needs the GUI:
   locked login keychain, exit 36 in a non-interactive agent shell), do NOT
   stop at "blocked until re-auth" — check whether the needed CONTENT already
   reached sibling surfaces: the repo working tree (uncommitted changes from
   other sessions), Notion, and Calendly/calendar bookings. 2026-09-03
   (Charity walkthrough): gog auth was dead and the booking state was
   recovered from the Calendly events list instead.

**gog beyond Gmail (2026-08-17):** gog is a FULL Google Suite CLI (v0.35.0 covers
Gmail/Calendar/Chat/Classroom/Drive/Contacts/Tasks/Sheets/Docs/Slides/People/Forms/
Meet/AppScript/Analytics/SearchConsole/Groups/Admin/Keep/YouTube/Maps/Photos), not
just Gmail. When the user asks you to look at their Google Calendar, go DIRECTLY to
the calendar surface — no help-walk needed (a 2026-08-17 session burned turns walking
`gog calendar --help` to rediscover this):

- List events in a window: `gog calendar events --from=2026-09-15 --to=2026-11-08 --all --plain --weekday`
  (`--from`/`--to` accept RFC3339, plain dates, or relative words: now, today,
  tomorrow, monday; `--all` = all calendars, default is primary only; `--weekday`
  adds day-of-week columns — exactly what line-up-the-weeks scheduling needs)
- GOTCHA: `--max` defaults to 10 — raise it (`--max=100`) or add `--all-pages` when
  pulling a multi-week window, or the result is silently truncated to 10 events
- Siblings: `gog calendars` (list calendars), `gog calendar freebusy` (free/busy),
  `gog calendar conflicts` (busy-time overlaps across calendars),
  `gog calendar search <query>` (free-text event search)
- Output flags as everywhere in gog: `-p/--plain` (TSV), `-j/--json`, `-a auto`

**Worked failure (2026-08-15):** asked "any new emails about lodging?", the
assistant said three times it couldn't read email; the user corrected "No
that's incorrect, you do have email access. You can check my email using the
Gog Cli" — and the gog invocation was already visible in job logs inside the
assistant's own context. Sibling of "User-Named Tool Not on PATH" (the
previous day's gogcli/gog failure): that one is tool DISCOVERY when the user
names it; THIS one is capability DENIAL when the user hasn't named it yet.

**General rule:** before asserting "I can't do X", grep jobs/scripts/history
for prior invocations of X.

## The Inbox Handoff Is Not a Blocker

**Trigger condition:** a flow you are testing just triggered an email to one of Eric's
real addresses and the next step is reading a code or link out of it — and you feel
the turn should end with "check your inbox and tell me the code."

**Root cause:** the inbox is treated as user-only territory, but `gog` is authenticated
on Eric's Gmail accounts (gmail.com and nonlinearlabs.ai), so that message is as
readable to the agent as any other mailbox source. Asking the user to relay it converts
an agent-executable step into a human round-trip.

**Fix procedure:** immediately after the form submit or send, call gog on the recipient
account (`gog gmail search '<sender or subject>'`), extract the code or link, and
continue the flow in the same turn. The turn ends with the fetch (or a later step),
never with the request.

**Worked failure (2026-09-01):** sgbs-training registration E2E — the Resend 6-digit
code landed at eric.ma@nonlinearlabs.ai; the assistant submitted the form
successfully, then ended the turn asking Eric to read the code from his inbox;
"Take action now." Distinct from the Clerk client-trust case: synthetic-address
mailboxes genuinely do not exist, so THAT handoff is real.

## Labeling Agent-Doable Steps "Manual" or "Human Steps"

Sibling of capability denial ("I don't have access to X"): the **under-claiming
variant**, where a wrap-up defers an operation to the human as a "remaining human
step" / "manual user action" when the API fully supports it.

**Trigger condition:** you are about to write "remaining human step:",
"manual:", or "Eric's call to do X" for an operation ON AN EXTERNAL SERVICE
(archive a board, flip a setting, grant access) — not for genuine
judgment/preference decisions (merge timing, spending money), which legitimately
belong to the human.

**Root cause:** equating "no dedicated subcommand" with "not API-doable". The
CLI surface (`gh project --help` shows no `archive`) is a subset of the API
surface (GraphQL `UpdateProjectV2Input` has `closed: Boolean`).

**Fix procedure:** before writing the wrap-up, introspect the service's input
types (GraphQL introspection of the relevant `*Input` type, REST OpenAPI spec,
`--help` two levels deep). If a field exists for the operation, execute it;
reserve "human step" for judgment calls.

**Worked failure (2026-08-16):** the learn-anything board-migration wrap-up
listed "archive the old board" as the remaining human step; the next session
archived it in one `gh api graphql` call (`updateProjectV2` with `closed: true`).
The human was asked to do a job the agent could do in one mutation.

## gog calendar AUTH: per-service scopes + the API-enable step

**Trigger condition (2026-08-17):** first-time `gog calendar` use on an account
whose stored token was created for Gmail only (calls fail with a permissions
error even though `gog` itself is installed and authenticated).

**Root cause (two independent gates, both must pass):**

1. gog auth is **per-service** — a gmail-scoped token cannot read calendar.
   Fix: `gog auth add <account> --services=calendar --force-consent` (opens a
   browser OAuth flow the user must approve; check current scopes first via
   `gog auth` listing rather than assuming).
2. **OAuth consent is NOT enough**: even after the flow succeeds, calendar
   calls still fail until the **Calendar API is enabled on the account's
   Google Cloud project**. This is a separate manual step: open the GCP
   Console API page in the user's browser — the user clicks "Enable"
   themselves (the agent cannot click it) — then wait ~1 min for propagation
   before retrying. Scope granted != API enabled.

**Scope boundary:** gog covers GOOGLE calendars only. Apple Calendar is
unreachable via gog; on macOS query it via `osascript`/AppleScript or
`icalBuddy` instead.

## gog calendar events: ONE calendarId max + failures swallowed by pipes

**Trigger condition (2026-08-17):** passing multiple positional calendarIds to
`gog calendar events` (it accepts at most ONE), or interpreting empty grep
output as "no matching events".

**Root cause:** with more than one ID the command errors; when its output is
piped through grep, the error text does not match the grep pattern, so the
failure surfaces as "(no output)" — indistinguishable from an empty result.
A 2026-08-17 session drew three invalid per-calendar "no match" conclusions
this way (the multi-ID command had silently failed through the pipe).

**Fix procedure:**

1. Use `--all` for all calendars, or ONE calendarId per invocation.
2. Before concluding "no results" from a grepped command, verify the upstream
   command SUCCEEDED — dump raw output to a file (or run unpiped) and check
   exit status first. A silently-failed command through grep looks exactly
   like an empty match.
3. Companion zsh gotcha: quote grep patterns that begin with `=` — unquoted
   `===` triggers zsh =command expansion and the command dies with a parse
   error ("== not found").

## Apple Calendar on macOS: osascript TCC hang + verify the local store first

**Trigger condition (2026-08-17):** following the scope-boundary advice above
to query Apple Calendar via `osascript`/AppleScript from a non-interactive
shell.

**Root cause:** Calendar.app needs an Automation (TCC) grant; the permission
prompt cannot appear in a non-interactive shell, so osascript HANGS (timed
out at 120s in testing) instead of erroring immediately with -1743.
icalBuddy may not be installed either.

**Fix procedure:**

1. Check the local store directly first: `ls -la ~/Library/Calendars/`.
   An EMPTY directory means no Apple/iCloud calendar accounts exist on the
   machine (true on this Mac as of 2026-08-17) — there is nothing to query;
   tell the user that directly instead of burning turns on osascript.
2. If accounts DO exist, read the per-calendar `.ics` files under
   `~/Library/Calendars/*.calendar/` (grep for SUMMARY/DTSTART) or install
   icalBuddy — do not use osascript from a non-interactive shell.

## TCC permission-walled folders: SSH to a Mac where the grant exists

**Trigger condition (2026-08-26):** a macOS folder is TCC permission-walled
from the agent's shell (Voice Memos Recordings, MobileSync Backup), or a
local search (mdfind) is blind to it, and you are about to conclude the data
is unreachable.

**Root cause:** TCC grants are per-machine and per-app; the working Mac's
agent shell lacks the grant, but the user's other Macs may have it.
iCloud-synced system data (Voice Memos, CloudDocs) is mirrored on every
synced machine, so the same path usually exists somewhere readable.

**Fix procedure:** SSH into the user's MacBook Air — `mba` in ~/.ssh/config,
Tailscale IP 100.102.18.52, permissions available there (user directive
2026-08-26: "you can search on my macbook air (ssh in) as the permissions on
there are available") — and read the same path remotely, e.g. `ssh mba 'ls
~/Library/Group\ Containers/group.com.apple.VoiceMemos.shared/Recordings/'`.
Verified 2026-08-26: used to authoritatively confirm five food-diary days had
no dinner memos, by mapping every remote recording timestamp 1:1 against the
vault's transcript-note timestamps (next-morning window included, since
dinner memos are sometimes recorded the morning after).

## Apple Notes embedded recordings: pasted paths are EPHEMERAL PLAYBACK HARDLINKS

**Trigger condition (2026-08-29):** the user pastes a filesystem path to a call recording embedded in an Apple Notes note and asks to transcribe it.

**Root cause (three independent blockers):** (1) Notes materializes a TEMPORARY HARDLINK to the recording ONLY while it is actively playing in the Notes UI — once playback stops the hardlink is cleaned up and the pasted path goes stale; (2) the Notes store (`~/Library/Group Containers/group.com.apple.notes/`) is TCC-walled from the agent shell; (3) the Notes AppleScript bridge times out from a non-interactive shell (same TCC-hang mechanism as the Calendar section above).

**Fix procedure (route ladder BEFORE asking the user for a manual export):**

1. Check alternate copies on disk first: Voice Memos, `~/Downloads`, `~/Desktop`.
2. SSH route (see the TCC permission-walled section above): `ssh mba` and list `~/Library/Group Containers/group.com.apple.notes/` — the mba TCC grant may expose the Notes store and its recording media.
3. iCloud web via agent-browser: icloud.com -> Notes -> open the note -> play or download the recording (the browser session holds the iCloud grant).
4. Only then ask the user: right-click the recording -> Save Attachment, or Share -> Save to Files/Desktop, into `~/Desktop` or `~/Downloads`.

Then transcribe locally with the ready `mlx_whisper` large-v3-turbo stack (see memory: local transcription stack). Discovered 2026-08-29 on the Daniel Chen call transcript task (learn-anything).

## Past communications: the mailbox is the source of truth, not derived notes

**Trigger condition:** you are reconstructing what was actually SAID in a past
communication — a vendor commitment, "the X answer given to Y", what was
quoted or promised — by grepping second-hand derived notes (planning logs,
outreach-logs, per-vendor YAMLs, READMEs) that reference the exchange.

**Root cause:** derived notes are INDEXES — they record that an exchange
happened ("after Eric's detailed answers (14 services, ~320 covers, $8–12K
envelope)") without containing the verbatim substance. Grepping them for the
substance yields only meta-references and attribution puzzles ("whose
question list is this line?"), and each additional grep compounds the
archaeology instead of converging.

**Fix procedure:** after ONE failed grep of derived notes, pivot directly to
the mailbox CLI — `gog` for Gmail, `hey` for HEY — and read the cited thread
(thread ids often appear in the log entry itself or are one `gog gmail
messages search <correspondent>` away). The pivot turn must END with the
mailbox tool call, not an announcement of it.

**Worked failure (2026-08-21):** the learn-anything Suki Otsuki snack-reply
session burned 4+ turns grepping the outreach-log and sd-chef-jenn.yaml for
Eric's snack-format answer to Chef Jenn when the Gmail thread id
(1a0146adc3984882) was already known; the eventual pivot ("Let me search the
Gmail thread...") was narrated without executing and drew a "Take action
now." interrupt.

## Person lookups by NAME fail on spelling, not location

**Trigger condition:** a `gog gmail search "<Name>"` (or HEY contact/repo grep)
for a person you KNOW exists returns zero hits, and you are tempted to
conclude the mailbox/account surface is wrong and pivot to another mail
surface (Gmail → HEY → repo).

**Root cause:** the search key, not the surface, is the problem. Names arrive
via dictation or memory and arrive phonetically mangled ("daniel foscher" for
**Fischer**, like "V Async" for VeSync in 1Password lookups). The surface
pivot is a wasted turn — the right surface usually had it all along under a
different spelling.

**Fix procedure (ordered):**
1. Try spelling/phonetic variants of the SURNAME in the SAME account
   (foscher/fischer/fisher/fiscer) BEFORE switching surfaces.
2. Better — harvest the canonical email address from an ADJACENT ARTIFACT:
   a calendar-invite thread in the mailbox, Calendly intake-call notes, the
   CRM row. Search by ADDRESS (e.g. `danielfisc2@gmail.com`) — it is
   spelling-immune and matches every thread regardless of how the name was
   typed.
3. Only after variant-search + address-harvest both miss, question the
   surface (gog NL account vs hey).

**Worked instance (2026-09-17, learn-anything):** "daniel foscher asked me a
request, see gmail" — NL Gmail search by "Foscher" → nothing; pivot to HEY →
nothing; user had to correct BOTH surface ("its in non linear labs") and
spelling ("and fischer"). The request was in the NL Gmail Discord-invite
thread all along; extracting the invitee address from that thread and
searching by address located it instantly.

## Vendor-step delegation instances (human-only labels that drew "Take action now")

Dated instances of point (6) — labeling wrap-up steps human-only without exhausting agent-executable paths. (a) 2026-09-01 sgbs-training: "check your inbox and relay the code" — the inbox was gog-readable; the inbox handoff dresses an agent-executable step as a blocker. (b) 2026-09-01 sgbs-roster auth cutover: wrap-up listed "two things only you can do" — set RESEND_API_KEY on the prod Convex deployment and add+verify the sending domain in the Resend dashboard — plus "say merge when done". Eric replied "Take action now." AGENT-EXECUTABLE PATHS to check FIRST: retrieve the secret from 1Password masked and pipe into `npx convex env set` (never echo); use the vendor's REST API instead of the dashboard (Resend has a full Domains API: create domain, get DKIM/SPF records, verify); write DNS records via the DNS provider's API (Cloudflare); set the FROM env var yourself. Genuinely-human residue is usually ONE short step (Eric minting a key he has never shared) — isolate THAT, execute everything around it, and ask for only the mint, not the whole checklist.

Dated instances of point (8) — auth/code handoffs that dress agent-executable steps as blockers. (a) 2026-09-01 sgbs-training — "check your inbox and relay the code"; the inbox was gog-readable. (b) 2026-09-04 learn-anything enrollment preview — Eric asked for an agent-browser session to click around a Clerk-gated page; the agent opened the browser, parked it at the Clerk sign-in screen, and ended the turn with "Your turn: sign in... I'm stopping here per the credential handoff — passwords/MFA are yours." Eric replied "Take action now." The handoff framed email-code sign-in as a credential problem, but Clerk dev email-code requires NO password — the code lands in Eric's gog-connected inbox; executable paths — drive the email-code flow in agent-browser and gog-fetch the code in the same turn, or mint a session JWT via the Clerk Backend API (POST /v1/sessions + /tokens) and inject __session cookies (convex-dev-backend-qa recipe). Genuinely-Eric-only surfaces are secrets he has never shared (passwords, TOTP seeds, hardware keys) — email-code/magic-link auth is NOT one. When Eric asks to click around a gated page, the staging contract is end-to-end — he lands PAST auth, ready to interact.
