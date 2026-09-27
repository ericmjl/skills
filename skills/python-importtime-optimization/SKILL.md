---
name: python-importtime-optimization
description: >-
  Diagnose and fix slow Python package import times. Use when: 'import pkg' or 'from pkg import X' takes seconds (CI import-time benchmarks slipping, CLI startup lag, marimo/Jupyter import latency); you suspect eager heavy imports in __init__.py; a module-level 'import lib' exists ONLY to set a side-effect flag and you need the lazy-set pattern; making imports lazy and verifying nothing still imports at load time; or dating an import-time regression from CI per-PR benchmark comments. Covers python -X importtime profiling, the __init__.py tax mechanic, the side-effect-flag fixes, sys.modules poison verification (per-process — never check a parent after a subprocess imported), cross-worktree commit-confound isolation, and per-PR benchmark-comment forensics. Memory consolidations listed in the body.
created_by: autolearn
created_at: "2026-08-16"
---

# Python Importtime Optimization

Diagnose and fix slow Python package import times. Procedure distilled from the
llamabot case (litellm = 4.1s of a 4.7s `import llamabot`, 2026-08-16) and the
earlier uvicorn fix (PR #388).

## Step 1: Profile with `-X importtime`

```bash
python -X importtime -c "import pkg" 2> profile.txt
sort -t'|' -k2 -rn profile.txt | head -30   # by cumulative time
```

- The **cumulative** column identifies the hogs; one heavy dependency
  (litellm: 4.1s) typically dominates the package total (4.7s).
- Interpreter startup + small deps account for the remainder (~0.6s) — don't
  chase those until the dominant cost is gone.

## Step 2: Know the two eager-import sites

1. **`pkg/__init__.py` module-level imports.** `from pkg import X` ALWAYS
   executes `pkg/__init__.py` first, so an eager heavy import there taxes
   EVERY import path — a submodule benchmark can never be faster than the
   parent's `__init__` cost. (lazy_loader/`attach()` does NOT help if a bare
   `import lib` also sits in the file.)
2. **Submodule module-level imports.** e.g. `from litellm import f, g` at the
   top of `pkg/bot/structuredbot.py` — pull it in even when only that bot is
   imported. Grep the package for `from <heavylib> import` and `import
   <heavylib>` outside functions.

## Step 3: The side-effect-flag anti-pattern

A module-level `import lib` added ONLY to set a flag (e.g.
`litellm.suppress_debug_info = True`) is a known regression source: the flag
usually only needs to be set **before the first call**, NOT at import time.
Fixes, in order of preference:

1. **Set the flag at each lazy import site**: wherever a function does
   `import litellm`, follow with `litellm.suppress_debug_info = True`.
2. **Configure-helper**: a tiny module with a function that imports the lib,
   sets the flag, and returns the module — call it wherever the lib is needed.
   (No underscore-prefixed helpers if the repo bans them.)

## Step 4: Make imports lazy, preserving behavior

- Move module-level imports into the functions/methods that use them (the
  values are used at call time, so function-level import is behavior-neutral).
- If the import is used in `__init__`, move it INTO `__init__`'s body.
- Keep truly cheap imports (stdlib: pathlib, typing) eager — don't scatter
  everything.

## Step 5: Verify with the sys.modules poison technique

```python
import sys
sys.modules["litellm"] = None   # any 'import litellm' now raises
import pkg                       # must NOT raise
```

If importing the package still raises ModuleNotFoundError, a module-level
import remains somewhere. Faster and more deterministic than uninstalling.

## Step 6: Date regressions from CI benchmark comments (forensics)

- Per-PR timing comments vary **±0.5s across runners** — don't conclude
  anything from a single pair of PRs; look at the trend across several.
- **PR closedAt ≠ merge date.** A PR's benchmark runs against its merge base,
  so numbers can predate a regression landing on main. Date-stamp regressions
  with `git log --follow <file>` / merged-commit dates, not the PR list.

## Constraints (llamabot-specific)

- Target: **≤1s** per import ("1 second is our benchmark").
- The agent may open/push perf-investigation PRs but must NOT merge them —
  merging is reserved for Eric.

## Step 4a: Triage call sites when introducing an accessor

- When the fix is an ACCESSOR (a function that imports the heavy lib, sets side-effect flags, and returns the module — e.g. a configured_litellm() in llamabot.config), do NOT mechanically convert every reference to the lib. Triage each site by WHEN it executes:

- MUST use the accessor: anything that runs at import time, and any site whose execution triggers the lib's resolution paths (e.g. litellm calls that resolve a provider via get_llm_provider, where suppress_debug_info must already be set).
- KEEP the direct reference: code that only runs AFTER a first real call — e.g. stream helpers (stream_chunk_builder) that only ever execute once a completion call has already loaded the lib into sys.modules. Converting them buys zero import-time savings and inflates the diff.

Rule: convert the minimum set of sites that makes 'import pkg' lazy; leave post-first-call references alone (minimal-diff triage).

Mechanical checks while editing:
- Inserting a new import mid-file? Re-check the whole import block's isort ordering (ruff will flag it on the next run anyway).
- After the refactor, re-run BOTH verifications before reporting the win: the sys.modules poison test (Step 5) and the -X importtime re-profile (Step 1). Run the re-profile and paste the delta — never end a turn by announcing it.

## Cold vs warm page cache: decoding CI benchmark spread + CI-first iteration

- CI benchmark numbers that look CONTRADICTORY are usually page-cache state, not noise:

- In a CI suite of import-benchmark subprocesses, the FIRST subprocess to touch a heavy lib pays the cold-FS cost of its thousands of files (litellm: ~2.9s on CI); every subsequent subprocess shares the WARM page cache (~0.9s). With eager litellm in __init__, this decodes the confusing #388-era set: 'import llamabot' (run first) = 3.58s cold while SimpleBot = 1.02s warm in the SAME CI run. Model CI numbers as cold-first + warm-rest before concluding two results disagree.
- LOCAL numbers measured after repeated profiling runs are hot-cache and 5-10x optimistic vs CI cold FS; a single import can measure 0.7s cold-ish then 0.14s warm seconds later. When estimating CI from local: multiply hot local by ~2-4x, and treat single local wall-clock numbers as ranges — sanity-check against the importtime cumulative column rather than wall-clock alone.
- CI-FIRST ITERATION RULE: when the remaining heavy import is ARCHITECTURAL (e.g. module-level ORM models needing declarative_base at import — recorder.py -> sqlalchemy), do NOT do the risky central-module refactor speculatively. Push, read the CI benchmark comment, and iterate (e.g. split ORM models into a lazily-imported submodule) only if the threshold (llamabot: <=1s) is actually exceeded on CI. Matches the repo's standing 'let CI validate' preference.
- Post-fix llamabot state (2026-08-16): litellm out of __init__ + structuredbot lazified -> 'import llamabot' 4.7s -> 0.042s local. Remaining offenders: ImageBot (eager httpx+PIL) and ToolBot (components.tools -> recorder -> sqlalchemy; est 0.4-0.9s CI, borderline). Before pushing such a change, ACTUALLY RUN (do not narrate): banner-suppression check (bogus model name -> BadRequestError WITHOUT Provider List banner), grep for residual litellm references expecting pre-import, bare-import test + unit tests.

## Post-push CI outcome + accessor idempotency (llamabot PR #395)

- OUTCOME (2026-08-16, PR #395 'perf: defer litellm import out of package init'): the CI Import-time-benchmark comment confirmed the fix on real CI hardware — import llamabot 0.134s, AgentBot 0.070s, SimpleBot 0.616s, ChatMemory 0.217s, tool 0.379s, prompt 0.385s, ToolBot 0.951s (all <=1s). The CI-FIRST ITERATION RULE was validated end-to-end: the deferred recorder/sqlalchemy ORM-split was NOT needed because ToolBot landed at 0.951s — under the bar but borderline, so recheck ToolBot on future benchmark comments before assuming headroom (a small slip puts it over 1s). ACCESSOR IDEMPOTENCY CHECK (add to the pre-push verification list alongside the banner check): (1) verify the accessor works when the heavy lib was ALREADY imported by someone else before the accessor runs — an import-and-set-attribute helper is naturally idempotent (calling it twice, or after an external import, is safe because it just re-sets the attr); state this check explicitly, do not assume it. (2) Verify the ORIGINAL bug the eager import fixed (the litellm Provider-List banner, #386) stays suppressed THROUGH THE ACCESSOR path, not only via direct module import: call with a bogus model name and confirm the error raises WITHOUT the banner. (3) Confirm the refactor changed WHERE imports happen but NOT package metadata — no dependencies added/removed (the bare-install CI test, e.g. scripts/test_bare_imports.py via 'uv pip install .', guards core-dep presence and must remain unaffected).

## lazy-imports-vs-annotation-evaluation

- ## Lazy imports vs. annotation evaluation (PEP 526 / 563)

When deferring a heavy import that a class also references in annotations, know what CPython actually evaluates (empirically verified 2026-08-16 — do NOT reason from half-remembered PEP text; a 5-line exec() test settles it):

- **Method/function-BODY annotations are NEVER evaluated at runtime** — BOTH simple names (x: T | None = None) AND attribute targets (self._m: T | None = None). Annotating with a not-yet-imported type inside a method body is safe with NO future import — the annotation is inert text to the interpreter (type checkers still read it).
- **Parameter annotations ARE evaluated at def time.** def __init__(self, cfg: HeavyType) executes the annotation expression when the class body is defined -> the name must be importable, OR made lazy via the next bullet.
- **from __future__ import annotations (PEP 563) makes ALL annotations lazy strings** — the universal escape hatch. Recipe for a class with a heavy collaborator: add it at module top, KEEP the light type-imports module-level (e.g. a pydantic-only specs module), and move the HEAVY module import into the methods that instantiate the collaborator (__init__/close_mcp). Instance: llamabot toolbot.py — 'from llamabot.mcp.manager import MCPClientManager' chain ~206ms local (components.pocketflow ~161ms of it) vs llamabot.mcp.specs (pydantic-only, light). In-repo precedent: agentbot.py:127 function-local MCPClientManager import.

Verify with the Step 5 poison test EXTENDED to the submodule: sys.modules['<heavy.module>'] = None, then import the bot module — must not raise (proves no module-level import remains).

## post-refactor-verification

- ## Post-refactor verification: call-path coverage audit

After an accessor/lazy-import refactor ships (or when REVIEWING one in a worktree), verify NO call path reaches the heavy lib without the side-effect flag set. The audit that answers this:

1. Run `grep -rn "<heavylib>" <pkg>/ --include="*.py"` and classify EVERY hit:
   - COVERED: goes through the accessor (e.g. configured_litellm()).
   - COVERED-BY-ORDER: function-local `from <heavylib> import X` whose execution is guaranteed AFTER a first real call already loaded the lib via the accessor in-process (stream helpers like stream_chunk_builder) — safe by ordering, not by accessor.
   - BUG (module-level): any remaining module-level import — the poison test (Step 5) catches this mechanically.
   - BUG (uncovered path): a call that triggers the lib's resolution paths (e.g. litellm provider resolution printing the Provider List banner unless suppress_debug_info was set) on a path where the accessor has NOT run first in-process.
2. For class-collaborator defers (import moved into __init__ only, e.g. toolbot's MCPClientManager): read the file IN FULL and check EVERY use of the lazily-imported name for NameError risk — methods outside __init__ (close_mcp, reset), isinstance/type checks, async sibling classes in the same file. Confirm `from __future__ import annotations` covers surviving annotations, and EXTEND the poison test to the submodule: sys.modules['<heavy.module>'] = None, then import the bot module — must not raise.

Instance (llamabot perf/import-times PR, 2026-08-16): the maintainer's review prompts for the litellm accessor and the toolbot MCPClientManager defer asked for exactly this audit — it is the standard review procedure for lazy-import PRs in this repo.

- - FLAG-READ-SEMANTICS CHECK (ground truth behind accessor idempotency): before trusting set-flag-at-lazy-import-site, grep the LIBRARY'S OWN SOURCE for where it reads the flag. litellm (2026-08-16): 'grep -rn suppress_debug_info' finds the module-level default (litellm/__init__.py:335) and reads INSIDE function bodies (get_llm_provider_logic.py:445, exception_mapping_utils.py:223, both 'if litellm.suppress_debug_info is False:'). Function-body reads are module-attribute lookups evaluated at CALL TIME with no import-time caching — so the lazy-set works even when the lib was already imported by someone else. If the library cached the flag at module import (e.g. '_X = lib.flag' at top level), the lazy-set pattern would be INSUFFICIENT — you would need the flag set before first call unconditionally.
- GREP PATTERN FOR RUNTIME REFS: classify runtime heavy-lib references with 'import litellm\|from litellm\|litellm\.' — a bare-name grep over-flags docstring/comment mentions (e.g. nodes.py:250 mentions litellm in backticks; the patterned grep correctly returns zero hits for llamabot components/, cli/, web/). Zero patterned-grep hits in a subtree = no runtime refs there, regardless of prose mentions.
- Instance outcomes (llamabot, 2026-08-16): all LLM call paths route through the accessor — pocketflow DecideNode/AsyncDecideNode construct ToolBot/AsyncToolBot at runtime via function-local imports (nodes.py:434/455/596/614) -> make_response -> configured_litellm; ImageBot's ollama path uses httpx directly (no litellm). test_agentbot_mcp.py's patch('llamabot.bot.toolbot.ToolBot') still works under the MCPClientManager defer because DecideNode imports at call time. GAP: no test constructs ToolBot with mcp_servers directly — the lazy MCP manager path is exercised only indirectly (AgentBot builds its own manager; tests/mcp/test_manager_integration.py covers MCPClientManager directly).
## benchmark-harness-warmup

- ## Benchmark harness warmup: the row-1 cold-interpreter artifact

A subprocess-per-import benchmark takes ONE sample per row; row 1 pays the cold-FS first-touch of the interpreter binary + stdlib, which is NOT package cost (observed 2026-08-16: `import llamabot` 1.462s vs 0.134s across CI runs on identical code — a ~10x spread on row 1 only, while later rows stayed warm-consistent). If you control the harness, run ONE untimed warmup subprocess (`sys.executable -c "pass"`) before the timed loop: it warms interpreter+stdlib (identical for every Python program — fair to exclude) while leaving the package's own files cold for row 1 (honest — that cost IS real package cost). Do NOT warm with `import <pkg>` — that launders the package's own cold cost out of row 1. Complements the cold-first/warm-rest decode rule and the ±0.5s runner-noise rule (Step 6): distinguish random runner variance from this SYSTEMATIC row-1 artifact, which the warmup removes entirely.

## auditing-a-lazy-import-pr-review-checklist

- ## Auditing a lazy-import PR (review-side checklist)

When REVIEWING a lazy-import change (your own or someone else's), verify in this order:

1. TYPE_CHECKING imports — always safe; no runtime effect. Skip.
2. Annotations — confirm 'from __future__ import annotations' at module top (all annotations become inert strings; see the annotation-evaluation section). Parameter annotations WITHOUT the future import ARE evaluated at def time and need the name importable.
3. Remaining module-level imports — TRACE THEIR OWN CHAINS. A light-looking import left at module level (e.g. 'from llamabot.mcp.specs import MCPServerConfig') silently re-pulls the heavy module if that 'light' module itself imports the heavy one (FALSIFIED 2026-08-16: specs.py itself imports only pydantic, BUT importing it still executes llamabot/mcp/__init__.py which eagerly imports manager — the defer was PERF-INEFFECTIVE for exactly this reason. Trace the chain through EVERY parent __init__ and ground-truth with the fresh-subprocess sys.modules check — see package-init-tax-false-negative section).
4. Name-reference grep — grep the changed file for EVERY occurrence of the lazily-imported name. References outside the lazy scope (isinstance checks, cleanup/close methods, class-body expressions) raise NameError at runtime even though import time is now fast.
5. Subclasses — a subclass inheriting __init__ from the lazified class is fine (the parent's __init__ executes the import in its own scope). SEPARATE sibling classes with their own module-level imports (e.g. async_agentbot.py importing MCPClientManager at module level) are independent: the PR's win does not apply to them — flag as a follow-up, not a regression of this PR.
6. Function-local imports of the heavy lib — REACHABILITY TRACE: can this function be the FIRST code path to touch the lib in a fresh process? Trace all callers; if every path goes through the accessor/config entry point first (stream_chunks is only ever called after make_response → configured_litellm), the direct function-local import is CORRECT per the Step 4a minimal-diff triage — do not flag it. If a public API exposes the function without the accessor on its call path, flag it.
7. Re-run the poison test scoped to the affected submodule: sys.modules['<heavy.submodule>'] = None, then import the bot module — must not raise.

Instance distilled from: llamabot toolbot MCPClientManager lazy-import PR review (commit d9ca8038), 2026-08-16.

## package-init-tax-false-negative

- ## package-init-tax-false-negative (SUPERSEDES the checklist item-3 llamabot instance)

The auditing checklist above (item 3) treats 'the light-looking module itself does not import the heavy one' as safe — its llamabot instance note ('specs.py imports only pydantic -> safe') was EMPIRICALLY FALSIFIED 2026-08-16: the toolbot MCPClientManager defer landed (commit 51259d12) and was PERF-INEFFECTIVE, because importing llamabot.mcp.specs executes llamabot/mcp/__init__.py FIRST, and that __init__ (line 3) eagerly imports manager -> adapter -> pocketflow. After 'from llamabot.bot.toolbot import ToolBot', 'llamabot.mcp.manager' in sys.modules is STILL True. RULE: a submodule import kept at module level is only safe if BOTH (a) the submodule's own imports AND (b) EVERY parent-package __init__ on its dotted path are free of the heavy chain. The chain-trace must go THROUGH the package __init__, not just into the target module.

GROUND-TRUTH VERIFICATION for every deferred-import PR (do NOT trust the commit message's claimed benchmark): in a FRESH subprocess, import the target module and check sys.modules membership:

    python -c "import llamabot.bot.toolbot, sys; print('llamabot.mcp.manager' in sys.modules)"

If True, the deferral is nullified — fix by making the package __init__ lazy (PEP 562 module-level __getattr__, or remove the eager import from __init__.py), NOT by shuffling more submodule imports. Before/after timing across worktrees: fresh subprocess per run, 3 runs each, take the MIN.

MOCK-PATCH COMPATIBILITY (tests survive the lazy refactor): @patch('litellm.completion') keeps working when code under test switches to a call-time accessor (litellm = configured_litellm(); litellm.completion(...)), because unittest.mock.patch sets the attribute on the REAL module object and the code resolves it at call time. What WOULD break: patch('myapp.mymod.litellm')-style patches of the importing module's captured name, and module-level 'from litellm import completion' bindings in code under test. Harmless extras: patch itself imports the module at patch/collection time, and the accessor re-setting side-effect flags is idempotent (flag reads are call-time module-attribute lookups).

## same-process-evidence-and-worktree-confounds

- Two verification traps when confirming an import-deferral commit (llamabot d9ca8038 review, 2026-08-16): (1) PROCESS BOUNDARY — sys.modules is PER-PROCESS: a membership check run in the PARENT process after a subprocess performed the import inspects the parent's module table (only subprocess/time) and returns a meaningless False. Trigger: any subprocess-based measurement script. Fix: print sys.modules diagnostics from INSIDE the subprocess (or parse its stdout) — never across the process boundary. (2) CROSS-WORKTREE CONFOUND — timing an import in two worktrees with different HEADs measures the SUM of all intervening commits and attributes the biggest one to the commit under study (perf worktree carried BOTH the litellm deferral, seconds-class, AND the manager deferral ~0.2s; main carried neither, so the 0.8s delta was litellm's, not the manager's). Isolate with commit^ vs commit in ONE tree; under a read-only constraint, 'git archive <commit> | tar -x -C <tmpdir>' + PYTHONPATH gives an isolated tree without touching any worktree. DECISIVE-EVIDENCE HIERARCHY: to verify a deferral actually defers, the same-process POSITIVE sys.modules check beats wall-clock — in ONE process, after importing the bot module (no instantiation), check 'pkg.heavy' in sys.modules: if PRESENT, the deferral saves ~nothing at import time because some other module in the graph still pulls the chain eagerly (find WHICH one with -X importtime, whose indented tree shows the importing parent); env differences, page-cache state, and commit deltas all distort clocks, but module membership cannot lie.

## Nullified consumer defers - PEP 562 lazy package __init__

- SYMPTOM: you deferred a heavy import inside a consumer module (moved 'from pkg.sub2 import Heavy' into a function/__init__ body), but importtime or sys.modules shows the heavy chain STILL loads on the supposedly-lightened import path. ROOT CAUSE: any 'from pkg.sub import X' ALWAYS executes pkg/__init__.py FIRST (parent package init runs before the submodule); if that __init__ eagerly imports the heavy modules — or the consumer still imports a SIBLING submodule while deferring only one name — every import pays the full chain regardless of the consumer-side deferral. Concrete instance (llamabot 2026-08-16, PR #395): deferring 'from llamabot.mcp.manager import MCPClientManager' into ToolBot.__init__ was nullified because toolbot.py's module-level 'from llamabot.mcp.specs import ...' (kept because specs.py itself is light, 1.5ms self) still ran llamabot/mcp/__init__.py, which eagerly imported manager -> adapter -> pocketflow (~200ms cumulative). DIAGNOSIS: (a) python -X importtime — the heavy cumulative time is attributed to the PARENT package (210ms on llamabot.mcp) while the imported submodule shows tiny self-time; (b) verify with a sys.modules probe ('pocketflow' in sys.modules after importing the lightened path). FIX AT THE SOURCE, not the consumer: make the parent __init__.py lazy via a PEP 562 module-level __getattr__ that imports-and-returns heavy names on first attribute access (keep genuinely light submodule imports eager). This fixes ALL consumers at once AND preserves 'from pkg import Heavy' import styles. A consumer-side defer can never beat the parent's __init__ cost (see the __init__.py tax mechanic) — when importtime shows the parent package as the cumulative offender, patch the parent, not the importer. AFTER FIX: re-verify with sys.modules — a heavy dependency may STILL load via a THIRD path (llamabot: manager gone but pocketflow remained via another importer); keep tracing until the sys.modules probe is clean. BENCHMARK VARIANCE TRAP: single-run CI import timings swing +-0.1-0.5s across runners; a before/after delta on one run can be pure variance and get falsely attributed to a commit (llamabot 0.951->0.823s 'improvement' was variance — a read-only reviewer with importtime evidence proved the defer moved ~0ms). Stabilize the harness with interpreter warmup + min-of-3 repeats, and never claim a commit-level improvement without it. Dispatch a read-only reviewer for perf refactors even when CI is green — CI aggregate numbers masked an entirely ineffective defer.

## pr-395-final-state

- - FINAL STATE (2026-08-16, SUPERSEDES the 0.951s numbers in the post-push-outcome section above): PR #395 after all 4 commits (litellm deferral via configured_litellm(), mcp PEP 562 lazy __init__, benchmark warmup + min-of-3): all 15 import rows green, worst 0.426s vs the 1s bar — a 2.4x margin, with ToolBot at 0.410s. ToolBot is NO LONGER borderline, so the recorder/sqlalchemy ORM-split is CLOSED as unnecessary (previously 'deferred, recheck if it slips'); the 'recheck ToolBot on future benchmark comments' caveat is downgraded to routine monitoring. STOP RULE applied and validated: when every row is >2x under target, further risk-laden refactors (splitting a 2390-line central module) are NOT justified — update the PR body with final numbers and the diagnosis story, and stop. PR left open for the maintainer to merge (merging reserved for Eric).
the fix addressed a cold-only or slow-FS-only cost that the min-of-3 harness cannot see — do NOT conclude the fix failed; (c) reproducibility across runs (e.g. 0.407 -> 0.410 on identical code) is the signal the harness is now stable enough to trust small deltas — and that the delta is noise, not regression.

## terminal-condition-cost-not-membership

- - TERMINAL CONDITION IS COST-BASED, NOT MEMBERSHIP-BASED (SUPERSEDES the 'keep tracing until the sys.modules probe is clean' advice in the nullified-consumer-defers section): some remaining imports are BY DESIGN and CHEAP, and chasing membership-clean wastes effort. Final llamabot instance (PR #395, 2026-08-16): after the PEP 562 mcp/__init__ lazy fix, 'pocketflow' STILL appeared in sys.modules after importing ToolBot — traced to llamabot/components/tools.py DEFAULT_TOOLS: the @tool decorator applies nodeify at MODULE level (decorator application is module-level executable code), which imports pocketflow at import time BY DESIGN (DEFAULT_TOOLS are nodeified at import). But -X importtime showed pocketflow self=226µs and llamabot.components.pocketflow cumulative=573µs — the earlier 160-200ms attributed to that subtree was the mcp adapter chain (manager -> adapter) hanging under it, NOT pocketflow itself. RULE: sys.modules membership tells you WHAT loads; importtime cumulative tells you whether it MATTERS. Stop tracing when the remaining chain is sub-ms, even if the module is still present — decorator-driven module-level imports (@tool/nodeify on module-level registries) are a legitimate, usually-cheap import path; only chase them if importtime shows real cost.

## Trigger details (from pre-compression description, preserved verbatim)

Diagnose and fix slow Python package import times. Use when: 'import pkg' or 'from pkg import X' takes seconds (CI import-time benchmarks slipping, CLI startup lag, marimo/Jupyter import latency); you suspect eager heavy imports in __init__.py; a module-level 'import lib' exists ONLY to set a side-effect flag (litellm.suppress_debug_info-style) and you need the lazy-set pattern; you are making imports lazy (function-level imports) and must verify nothing still imports at load time; or you are dating an import-time regression from CI per-PR benchmark comments. Covers: python -X importtime profiling and reading the cumulative column; the __init__.py tax mechanic (from pkg import X executes pkg/__init__.py first, so eager imports there dominate EVERY import path); the side-effect-flag anti-pattern and its fixes (set flag at lazy import site / configure-helper module); moving module-level imports into functions while preserving behavior; the sys.modules poison verification technique; the same-process POSITIVE sys.modules check (sys.modules is per-process — never check it in a parent process after a subprocess did the importing) and cross-worktree commit-confound isolation (commit^ vs commit in one tree, or git archive to a tempdir under read-only constraints); and per-PR benchmark-comment forensics (±0.5s runner noise, closedAt != merge date). Consolidates the import-perf fragments from memories #346/#554/#1113 (llamabot 4.1s litellm case) into one loadable procedure.
