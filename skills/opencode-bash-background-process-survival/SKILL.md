---
name: opencode-bash-background-process-survival
description: >-
  Diagnose and fix backgrounded processes (dev servers, nohup'd jobs) that get KILLED when the bash tool's command terminates, completes, or times out — even when started with nohup & disown. Use when: a backgrounded server died by the next turn or when the launching command timed out; the dev server started last turn returns connection refused / curl 000; 'shell tool terminated command after exceeding timeout' appears and the PID is gone; you need a process to survive across multiple bash-tool turns on macOS; or about to add more disown/nohup flags hoping to make a job survive (insufficient alone). ROOT CAUSE: disown detaches from the job table but NOT the process group; the bash tool signals the whole group on termination. FIX: the subshell double-fork '( nohup cmd >log 2>&1 & )' — the subshell exits immediately, orphaning the child to launchd (PID 1); verify with 'ps -p <pid>' next turn. Lookalike distinctions live in the body.
created_by: autolearn
created_at: "2026-08-04"
---

# Opencode Bash Background Process Survival

Diagnose and fix backgrounded processes (dev servers, nohup'd jobs, long-running commands) that get KILLED when the opencode bash tool's command terminates, completes, or times out — even though they were started with 'nohup ... & disown'. Use when: you backgrounded a server/process with 'nohup cmd >log 2>&1 & disown' and it died by the next turn or when the launching command timed out; the dev server you started last turn returns connection refused / curl 000; 'shell tool terminated command after exceeding timeout' appears and the backgrounded PID is gone; you need a process to survive across multiple bash-tool turns on macOS; or you are about to add more 'disown' / 'nohup' flags hoping to make a backgrounded job survive (disown alone is insufficient). ROOT CAUSE: 'disown' detaches a job from the shell's JOB TABLE but does NOT move it to a new process group/session; when the bash tool terminates its command (on normal completion OR timeout), SIGTERM/SIGKILL is delivered to the entire PROCESS GROUP, and the disowned child shares that group and dies with it. macOS does NOT ship 'setsid' (no easy 'setsid cmd &' like Linux). FIX (robust macOS pattern): the subshell double-fork — '( nohup cmd >log 2>&1 & )' — the parentheses spawn a subshell that backgrounds the child then EXITS immediately, orphaning the child which gets reparented to launchd (PID 1); combined with nohup (ignores SIGHUP) and redirected stdio, the child survives the parent shell's death AND the bash tool's process-group signal. Verify with 'ps -p <pid>' on the next turn. Distinct from Python stdout block-buffering (memory: visibility into a surviving process, not survival itself), from pixi-run process-group signaling (memory #832: 'setsid' workaround for signaling a pixi job, not surviving bash-tool termination), and from the marimo/Lektor preview-server lifecycle rules (those say WHEN to background; THIS says HOW to background so it actually survives). Generalizes to any long-running process backgrounded from the opencode bash tool on macOS (Lektor preview, marimo edit, vLLM/Ollama serve, python http.server, uvicorn, dev servers).

## The failure, step by step

The opencode bash tool runs each command in a shell. When that command finishes (or the tool kills it on timeout), the tool terminates the process **group**, not just the lead process:

1. You run `nohup my_server > /tmp/srv.log 2>&1 & disown` and capture PID `$!`.
2. `disown` removes the job from the shell's **job table** (so the shell won't send it SIGHUP on exit, and `jobs` won't list it).
3. **But `disown` does NOT create a new process group or session.** The backgrounded child still shares the shell's process group (PGID).
4. The bash tool terminates the command → SIGTERM/SIGKILL is delivered to the **whole process group** → your "detached" child dies with it.
5. Next turn: `curl localhost:PORT` returns `000` (connection refused), `ps -p <pid>` shows nothing. The `disown` gave a false sense of safety.

The string `shell tool terminated command after exceeding timeout` in the tool output is the smoking gun: the timeout kill took the process group, and your server with it.

## The fix: subshell double-fork

macOS does **not** ship `setsid` (the Linux one-liner `setsid cmd &`). The macOS-equivalent robust pattern is the **subshell double-fork**:

```bash
mkdir -p /tmp/srv-logs
( nohup my_server > /tmp/srv-logs/srv.log 2>&1 & echo $! > /tmp/srv-logs/srv.pid )
```

Why this works:
- The `( ... )` runs the body in a **subshell**.
- Inside, `nohup cmd &` backgrounds the child in the subshell, and the subshell writes the PID to a file then **exits immediately**.
- When the subshell exits, the child is **orphaned** and **reparented to launchd (PID 1)**.
- `nohup` makes it ignore SIGHUP; the redirected stdio detach it from the tool's pipe.
- Because the child is now a child of launchd in its own reparented state, it is **outside** the bash tool's process group and survives the tool's group-wide signal.

This is the pattern that makes a server survive across many turns. (`setsid` would also work if installed; `brew install util-linux` provides it — but the subshell pattern needs no extra install and is the portable macOS default.)

## Verification (do this every time, on the NEXT turn)

```bash
PID=$(cat /tmp/srv-logs/srv.pid); ps -p "$PID" && echo "ALIVE" || echo "DEAD"
curl -sS -o /dev/null -w "%{http_code}\n" --max-time 5 http://localhost:PORT
```

If `ps -p` reports DEAD or curl returns `000`, the detachment failed — re-launch with the subshell pattern.

## Common variants

**Lektor preview server (website repo, two worktrees, two ports):**
```bash
mkdir -p /tmp/lektor-dev
( cd /Users/ericmjl/github/website/worktree-a && nohup /Users/ericmjl/github/website/.pixi/envs/default/bin/lektor server -p 5001 -h 0.0.0.0 > /tmp/lektor-dev/a.log 2>&1 & echo $! > /tmp/lektor-dev/a.pid )
```
Note `/tmp/` is cleared on reboot — always `mkdir -p` the log dir first, or the redirect silently fails with "no such file". (See memory #1291.)

**marimo edit server:**
```bash
( nohup uvx marimo edit --sandbox --no-token /path/to/nb > /tmp/marimo.log 2>&1 & echo $! > /tmp/marimo.pid )
```

**python http.server (static expose over Tailscale):**
```bash
( nohup python3 -m http.server 8080 > /tmp/http.log 2>&1 & echo $! > /tmp/http.pid )
```

## Gotchas that compound this

- **Python stdout is block-buffered** when redirected to a file: even a *surviving* process can look dead because its log stays empty for minutes. Use `python -u` or `PYTHONUNBUFFERED=1` so you can actually see it working. This is a VISIBILITY problem, distinct from the SURVIVAL problem this skill fixes. (Memory #775.)
- **pgrep/pkill self-match**: when checking liveness, `pgrep -af my_server` matches its own command line and returns a phantom PID every call. Capture `$!` at launch (as above) and check with `ps -p <PID>` instead. (Memory #781.)
- **macOS port 5000 is occupied** by ControlCenter (AirPlay Receiver) — use 5001/5002/etc. for dev servers. (Memory #1197/#1291.)
- **The bash tool's default 120s timeout** is separate from this: even a correctly-detached process whose *launch command itself* runs >120s will be killed mid-launch. Detach fast (the subshell returns immediately) and verify on the next turn.
- **DO NOT add `disown` inside the subshell** — `( nohup cmd >log 2>&1 & disown )` is a trap. The `&` already detached the job in the subshell's context, so `disown` has no job-table entry to act on and errors (`disown: not a job control shell` / `no such job`). Worse, that error makes the subshell return NON-ZERO, which aborts any `&&` chain that follows the launch (e.g. `( ... & disown ) && sleep 4 && cat log` never runs the sleep/cat because the subshell exited non-zero) AND can prevent the server from starting cleanly at all. The correct pattern is `( nohup cmd >log 2>&1 & )` with NOTHING after the `&` — the subshell exits 0 immediately, orphaning the child to launchd. The `disown` is not merely redundant here, it is actively harmful. (Discovered 2026-08-08 brain42 vault-browser vite dev server launch: `disown` errored, the dev server never came up, and the verification `cat log` was skipped because the `&&` chain aborted on the subshell's non-zero exit.)

## When NOT to use this

- **Interactive creative tools** (the website video editor at localhost:4096, a GUI app the user will drive): per memory #62, hand the user the launch command instead of backgrounding — the user owns the lifecycle of an interactive tool, the agent owns the lifecycle of a preview/serve process.
- **A command whose output you need inline** (a one-shot build, a test run): don't background at all; let it complete in the foreground and raise the bash-tool `timeout` if needed.
- **You need the process to die when the session ends**: then a plain `&` (no detach) is correct — the survival pattern is for processes you want to PERSIST.

## Related

- Memory #832 — pixi `run dev` puts itself + grandchildren in one process group; `setsid` isolates a backgrounded pixi job for *signaling*. Sibling technique, different goal (signal a job vs. survive bash-tool termination).
- Memory #1197 / #1291 — Lektor preview-server lifecycle: WHEN to background + dual-port dual-worktree setup. THIS skill supplies the HOW that makes the backgrounding actually survive.
- Memory #775 — Python stdout block-buffering (visibility into a surviving process).
- Memory #781 — pgrep/pkill self-match when checking liveness.

## After backgrounding a dev server: verify which port YOUR instance bound

- A curl 200 on the default port (3000) may come from a PRE-EXISTING server — often the MAIN checkout's dev server when you started yours from a git worktree, serving DIFFERENT code. Next.js auto-increments ports (3000→3001) and logs the actual port in the server's own log. PROCEDURE: after backgrounding the server, read THE LOG YOU REDIRECTED (not a curl probe of :3000) for the Ready/port line, then run browser QA / curls against THAT port. Never treat a successful curl on the default port as evidence your instance is serving — you would QA the wrong app (stale code from another branch). Discovered 2026-08-16 (learn-anything portal-gantt worktree: main checkout's server held :3000; worktree instance bound :3001).
