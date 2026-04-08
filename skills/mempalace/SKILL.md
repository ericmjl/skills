---
name: mempalace
description: >
  Use the MemPalace CLI to persist, search, and manage AI memory across sessions.
  Triggers whenever the user asks to remember, recall, save, store, or retrieve
  information that should persist across conversations — including past decisions,
  preferences, facts about people or projects, conversation history, and any verbatim
  content the user wants preserved. Also triggers when the user mentions "palace",
  "wings", "rooms", "drawers", "knowledge graph", "AAAK", or when they want to search
  through historical context, traverse connections between topics, or check what their
  AI knows. Mirrors the MemPalace MCP server tools: each CLI command maps to an MCP
  tool with an equivalent trigger condition.
license: MIT
---

# MemPalace CLI

Use MemPalace CLI commands to store and retrieve persistent memory. Each command below mirrors an MCP server tool with the same trigger condition.

## Requirements

```bash
pip install mempalace
```

## Architecture

MemPalace organizes memory as a navigable building:

- **Wings** — major domains (people, projects, topics)
- **Rooms** — specific subjects within a wing (auth-migration, ci-pipeline, pricing)
- **Halls** — memory types: `hall_facts`, `hall_events`, `hall_discoveries`, `hall_preferences`, `hall_advice`
- **Tunnels** — cross-wing connections. Same room name in different wings = automatic link
- **Closets** — summaries pointing to original content
- **Drawers** — verbatim files. The exact words, never summarized

Underlying storage: ChromaDB (semantic search) + SQLite (knowledge graph). Everything local, no API key.

## Commands and Triggers

Each command has a trigger condition that mirrors its MCP server counterpart.

---

### `mempalace init <dir>`

**Mirrors:** First-time setup (no direct MCP tool — prerequisite for all tools)

**Trigger:** User wants to set up MemPalace for the first time, or says "initialize my palace", "set up memory", "start mempalace".

```bash
mempalace init ~/projects/myapp
mempalace init ~/projects/myapp --yes    # auto-accept detected entities
```

Detects people and projects from file content, then detects rooms from folder structure. Creates wing config and entity registry. Must run before mining.

---

### `mempalace status`

**Mirrors:** `mempalace_status` — Palace overview, total drawers, wing and room counts, AAAK spec, memory protocol

**Trigger:** User asks "what's in my palace?", "show me my memory status", "how many memories do we have?", "what do you know?". Also call at the start of a session to understand the user's world.

```bash
mempalace status
```

Shows total drawers filed, wing breakdown, room counts. Use this to get oriented before any memory operation.

---

### `mempalace search "query"`

**Mirrors:** `mempalace_search` — Semantic search with wing/room filters. Returns verbatim drawer content with similarity scores.

**Trigger:** User asks any question about past information: "what did we decide about X?", "why did we choose Y?", "find our discussion about Z", "what was the reasoning for...", "search my memory for...", "what do you know about...". Any time the user references a past decision, conversation, or fact that should exist in stored memory.

```bash
mempalace search "why did we switch to GraphQL"
mempalace search "auth decision" --wing myapp
mempalace search "pricing discussion" --wing myapp --room costs
mempalace search "Kai sprint" --results 10
```

Returns verbatim text with similarity scores, wing/room location, and source files. Filter by `--wing` and `--room` for targeted retrieval.

---

### `mempalace wake-up`

**Mirrors:** `mempalace_status` + `mempalace_diary_read` — Load L0 (identity) and L1 (essential story) into context

**Trigger:** User starts a new session and wants the AI to "remember" them, or says "wake up", "load your memory", "what do you know about me?", "recall our context". Also use when injecting palace context into a local model's system prompt.

```bash
mempalace wake-up
mempalace wake-up --wing driftwood
```

Generates ~600-900 tokens of context: identity from `~/.mempalace/identity.txt` plus essential story auto-generated from top palace drawers. Redirect to a file for local model injection:

```bash
mempalace wake-up > context.txt
```

---

### `mempalace mine <dir>`

**Mirrors:** `mempalace_add_drawer` — File verbatim content into the palace (batch operation)

**Trigger:** User wants to ingest project files or conversation exports into the palace: "import my chats", "mine this project", "ingest these conversations", "load my Claude/ChatGPT history", "add my project files to memory". Also when user says "remember everything in this folder" or "store all these conversations".

```bash
# Mine project files (code, docs, notes)
mempalace mine ~/projects/myapp

# Mine conversation exports (Claude, ChatGPT, Slack)
mempalace mine ~/chats/ --mode convos

# Tag with a specific wing name
mempalace mine ~/chats/ --mode convos --wing myapp

# Auto-classify into decisions, preferences, milestones, problems
mempalace mine ~/chats/ --mode convos --extract general

# Preview what would be filed without filing
mempalace mine ~/projects/myapp --dry-run

# Limit number of files
mempalace mine ~/projects/myapp --limit 50
```

---

### `mempalace split <dir>`

**Mirrors:** No direct MCP tool — preprocessing step for `mempalace mine --mode convos`

**Trigger:** User has concatenated transcript mega-files that need splitting before mining: "split my chat exports", "these transcripts are all in one file", "separate my conversation sessions". Run before `mempalace mine --mode convos` when exports contain multiple sessions per file.

```bash
mempalace split ~/chats/
mempalace split ~/chats/ --dry-run
mempalace split ~/chats/ --min-sessions 3
mempalace split ~/chats/ --output-dir ~/chats/split/
```

---

### `mempalace compress`

**Mirrors:** `mempalace_get_aaak_spec` — AAAK compression of palace content

**Trigger:** User wants to compress stored memories for token-efficient context loading: "compress my memories", "reduce token usage", "AAAK encode my palace", "make my memory smaller for context".

```bash
mempalace compress --wing myapp
mempalace compress --wing myapp --dry-run
mempalace compress                         # all wings
```

Compresses drawers using AAAK dialect and stores in a separate `mempalace_compressed` collection.

---

### `mempalace repair`

**Mirrors:** No direct MCP tool — recovery operation

**Trigger:** Palace is corrupted, returns errors, or ChromaDB segfaults (known on macOS ARM64): "my palace is broken", "repair my memory", "mempalace crashed", "ChromaDB error", "palace won't load".

```bash
mempalace repair
```

Rebuilds palace vector index from stored data. Creates a backup before rebuilding.

---

### Knowledge Graph (Python API)

**Mirrors:** `mempalace_kg_query`, `mempalace_kg_add`, `mempalace_kg_invalidate`, `mempalace_kg_timeline`, `mempalace_kg_stats`

**Trigger:** User asks about entity relationships, wants to store structured facts, or needs temporal queries: "what do you know about Kai?", "who works on Orion?", "add that Kai works on Orion", "Kai moved to Nova project", "show me the timeline for project X", "what was true about Y in January?"

The knowledge graph is accessible via Python API (no CLI command yet):

```python
from mempalace.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()

# Add a fact (mirrors mempalace_kg_add)
kg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")

# Query entity relationships (mirrors mempalace_kg_query)
kg.query_entity("Kai")
# → [Kai → works_on → Orion (current), Kai → recommended → Clerk (2026-01)]

# Temporal query — what was true on a specific date
kg.query_entity("Maya", as_of="2026-01-20")
# → [Maya → assigned_to → auth-migration (active)]

# Invalidate a changed fact (mirrors mempalace_kg_invalidate)
kg.invalidate("Kai", "works_on", "Orion", ended="2026-03-01")

# Chronological timeline (mirrors mempalace_kg_timeline)
kg.timeline("Orion")
# → chronological story of the project

# Graph overview (mirrors mempalace_kg_stats)
kg.stats()
# → entities, triples, current vs expired facts, relationship types
```

Run inline with `uv run` or `python -c`:

```bash
python -c "from mempalace.knowledge_graph import KnowledgeGraph; kg = KnowledgeGraph(); print(kg.query_entity('Kai'))"
```

---

### Search via Python API

**Mirrors:** `mempalace_search` — programmatic access to search results

**Trigger:** Same as `mempalace search` CLI, but when you need structured data instead of printed output.

```python
from mempalace.searcher import search_memories

results = search_memories("auth decisions", palace_path="~/.mempalace/palace")
# Returns dict with query, filters, and results list
```

---

### Palace Graph Traversal (Python API)

**Mirrors:** `mempalace_traverse`, `mempalace_find_tunnels`, `mempalace_graph_stats`

**Trigger:** User wants to explore connections between topics across projects: "what's connected to auth-migration?", "how do these projects relate?", "find cross-project connections", "show me tunnels between wings", "what topics bridge my personal and work wings?"

```python
from mempalace.palace_graph import traverse, find_tunnels, graph_stats
import chromadb

client = chromadb.PersistentClient(path="~/.mempalace/palace")
col = client.get_collection("mempalace_drawers")

# Walk from a room across wings (mirrors mempalace_traverse)
traverse("auth-migration", col=col, max_hops=2)

# Find rooms bridging two wings (mirrors mempalace_find_tunnels)
find_tunnels("wing_code", "wing_team", col=col)

# Graph connectivity overview (mirrors mempalace_graph_stats)
graph_stats(col=col)
```

---

### Memory Stack (Python API)

**Mirrors:** 4-layer memory protocol from `mempalace_status` — L0 identity, L1 essential story, L2 on-demand, L3 deep search

**Trigger:** User wants layered memory loading: "load my identity", "get my essential context", "retrieve on-demand memories for project X", "deep search for..."

```python
from mempalace.layers import MemoryStack

stack = MemoryStack()

# L0 + L1 wake-up (~600-900 tokens) — same as `mempalace wake-up`
stack.wake_up()

# L2 on-demand retrieval by wing/room
stack.recall(wing="driftwood", room="auth-migration")

# L3 deep semantic search
stack.search("pricing change")
```

## AAAK Dialect

AAAK is a lossy abbreviation system for token-efficient memory storage. Used by `mempalace compress` and agent diaries.

- **Entities**: 3-letter uppercase codes (ALC=Alice, JOR=Jordan, KAI=Kai)
- **Emotions**: `*action markers*` (`*warm*`=joy, `*fierce*`=determined, `*raw*`=vulnerable, `*bloom*`=tenderness)
- **Structure**: Pipe-separated fields. `FAM: family | PROJ: projects | ⚠: warnings`
- **Dates**: ISO format. Counts: `Nx` = N mentions. Importance: ★ to ★★★★★

```
SESSION:2026-04-08|fixed.auth.bug.in.OAuth|KAI→reviewed|ALC→approved.deploy|★★★★
```

## All Commands Quick Reference

```
mempalace init <dir>                               # set up palace from project
mempalace mine <dir>                               # mine project files
mempalace mine <dir> --mode convos                 # mine conversation exports
mempalace mine <dir> --mode convos --wing myapp    # tag with wing name
mempalace mine <dir> --mode convos --extract general  # auto-classify
mempalace split <dir>                              # split concatenated transcripts
mempalace search "query"                           # semantic search
mempalace search "query" --wing myapp              # search within a wing
mempalace search "query" --room auth-migration     # search within a room
mempalace wake-up                                  # load identity + essential story
mempalace wake-up --wing driftwood                 # project-specific wake-up
mempalace compress --wing myapp                    # AAAK compress
mempalace repair                                   # rebuild corrupted index
mempalace status                                   # palace overview
```

All commands accept `--palace <path>` to override the default palace location.

## Key Principles

1. **Store verbatim** — never summarize when mining. The 96.6% recall score comes from raw mode
2. **Search before asserting** — run `mempalace search` before stating facts about people or projects. Wrong is worse than slow
3. **Update facts, don't duplicate** — use `kg.invalidate()` + `kg.add_triple()` when facts change
4. **Wake up first** — run `mempalace wake-up` at session start to load context
5. **Filter for precision** — use `--wing` and `--room` on search for targeted retrieval
