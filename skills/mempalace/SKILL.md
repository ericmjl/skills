---
name: mempalace
description: >
  Persist, search, and manage AI memory across sessions using MemPalace's MCP server.
  Triggers whenever the user's MCP configuration includes mempalace tools (mempalace_*),
  or when the user asks to remember, recall, save, store, or retrieve information that
  should persist across conversations — including past decisions, preferences, facts about
  people or projects, conversation history, and any verbatim content the user wants preserved.
  Also triggers when the user asks about their "palace", "wings", "rooms", "drawers",
  "knowledge graph", "AAAK", or when they want to search through historical context,
  traverse connections between topics, or maintain an agent diary.
license: MIT
---

# MemPalace

Persistent AI memory via MemPalace's MCP server. Store everything, find anything.

## When to invoke this skill

This skill activates when **any** of the following are true:

1. **MCP tools with `mempalace_` prefix are available** in the current session (check your tool list for `mempalace_search`, `mempalace_status`, etc.)
2. User explicitly mentions mempalace, memory palace, palace, wings, rooms, drawers, AAAK, or knowledge graph
3. User asks to **remember, save, store, record, file, or persist** information across sessions
4. User asks to **recall, retrieve, look up, find, search** past conversations, decisions, or facts
5. User asks about **past decisions** ("why did we choose X?", "what did we decide about Y?")
6. User asks about **people or projects** they've discussed before ("what do you know about Kai?", "tell me about the Orion project")
7. User says things like **"don't forget"**, **"keep this in mind"**, **"from now on"**, **"as I mentioned before"**
8. User wants to **check for contradictions** or verify facts against stored knowledge
9. User wants to **traverse connections** between topics across different projects or domains
10. User wants to maintain a **personal agent diary** or journal across sessions

## Requirements

- MemPalace installed: `pip install mempalace`
- Palace initialized: `mempalace init <dir>`
- Data mined: `mempalace mine <dir>` (or `--mode convos` for conversation exports)
- MCP server registered: `claude mcp add mempalace -- python -m mempalace.mcp_server`

## Architecture

MemPalace organizes memory as a navigable building:

- **Wings** — major domains (people, projects, topics). Each wing is a separate world.
- **Rooms** — specific subjects within a wing (auth-migration, ci-pipeline, pricing)
- **Halls** — memory types connecting rooms: `hall_facts`, `hall_events`, `hall_discoveries`, `hall_preferences`, `hall_advice`
- **Tunnels** — cross-wing connections. Same room name in different wings = automatic link.
- **Closets** — summaries that point to original content
- **Drawers** — verbatim files. The exact words, never summarized.

Underlying storage: ChromaDB for semantic search, SQLite for knowledge graph. Everything local.

## The 19 MCP Tools

### Palace Read

| Tool | What it does | When to use |
|------|-------------|-------------|
| `mempalace_status` | Palace overview + AAAK spec + memory protocol | **Call this first** at session start (wake-up) |
| `mempalace_list_wings` | All wings with drawer counts | User asks "what projects/people do I have?" |
| `mempalace_list_rooms` | Rooms within a wing | User asks about a specific project's structure |
| `mempalace_get_taxonomy` | Full wing → room → count tree | User wants a complete map of their palace |
| `mempalace_search` | Semantic search with wing/room filters | User asks any question about past information |
| `mempalace_check_duplicate` | Check if content already exists | Before filing new content to avoid duplicates |
| `mempalace_get_aaak_spec` | AAAK compressed dialect reference | When reading/writing compressed memories |

### Palace Write

| Tool | What it does | When to use |
|------|-------------|-------------|
| `mempalace_add_drawer` | File verbatim content into wing/room | User says "remember this", "save this", "don't forget" |
| `mempalace_delete_drawer` | Remove a drawer by ID | User explicitly asks to delete specific stored content |

### Knowledge Graph

| Tool | What it does | When to use |
|------|-------------|-------------|
| `mempalace_kg_query` | Entity relationships with time filtering | User asks "what do you know about X?" |
| `mempalace_kg_add` | Add facts (subject → predicate → object) | User states a fact to remember: "Kai works on Orion" |
| `mempalace_kg_invalidate` | Mark facts as ended/no longer true | User says something changed: "Kai moved to project Nova" |
| `mempalace_kg_timeline` | Chronological entity story | User asks "what happened with X over time?" |
| `mempalace_kg_stats` | Graph overview | User asks about the knowledge graph's size/structure |

### Navigation

| Tool | What it does | When to use |
|------|-------------|-------------|
| `mempalace_traverse` | Walk the graph from a room across wings | User asks "what's connected to X?" or "how does X relate to Y?" |
| `mempalace_find_tunnels` | Find rooms bridging two wings | User asks about cross-project connections |
| `mempalace_graph_stats` | Graph connectivity overview | User asks about the overall structure and connections |

### Agent Diary

| Tool | What it does | When to use |
|------|-------------|-------------|
| `mempalace_diary_write` | Write AAAK diary entry | End of session, or after significant work, to record observations |
| `mempalace_diary_read` | Read recent diary entries | Start of session, to recall past observations and context |

## Workflow

### Session Start (Wake-up)

1. Call `mempalace_status` — loads palace overview, AAAK spec, and memory protocol
2. Call `mempalace_diary_read` (if using agent diary) — recall past session observations
3. Now you know the user's world: their people, projects, and past context

### When the User Asks About the Past

1. Call `mempalace_search` with the query. Filter by wing/room if the topic is clear.
2. If the question is about a specific person or entity, call `mempalace_kg_query`.
3. If exploring connections, call `mempalace_traverse` from a relevant room.

### When the User Wants to Save Information

1. Call `mempalace_check_duplicate` first to avoid storing duplicates.
2. Call `mempalace_add_drawer` with the verbatim content, choosing an appropriate wing and room.
3. If the content contains entity relationships (people, projects, roles), also call `mempalace_kg_add` for each fact.
4. If a previously stored fact has changed, call `mempalace_kg_invalidate` on the old fact and `mempalace_kg_add` for the new one.

### Session End (Save)

1. Call `mempalace_diary_write` with a compressed summary of what happened, what was learned, what matters.
2. Write in AAAK format for token efficiency: entity codes, emotion markers, pipe-separated fields.

## Important Parameters

### mempalace_search

```
query: str    — What to search for
limit: int    — Max results (default 5)
wing: str     — Filter by wing (optional)
room: str     — Filter by room (optional)
```

### mempalace_add_drawer

```
wing: str        — Project or person name (e.g., "wing_orion")
room: str        — Subject slug (e.g., "auth-migration")
content: str     — Verbatim content to store (exact words, never summarized)
source_file: str — Where this came from (optional)
added_by: str    — Who is filing this (default: "mcp")
```

### mempalace_kg_add

```
subject: str       — The entity (e.g., "Kai")
predicate: str     — The relationship (e.g., "works_on", "prefers", "completed")
object: str        — The target (e.g., "Orion", "Postgres")
valid_from: str    — When this became true, YYYY-MM-DD (optional)
source_closet: str — Closet ID reference (optional)
```

### mempalace_kg_query

```
entity: str     — Entity to query (e.g., "Kai", "Orion")
as_of: str      — Date filter, only facts valid at this date (optional, YYYY-MM-DD)
direction: str   — "outgoing", "incoming", or "both" (default: "both")
```

## AAAK Dialect (Compressed Memory)

AAAK is a lossy abbreviation system for packing repeated entities into fewer tokens. Key rules:

- **Entities**: 3-letter uppercase codes (ALC=Alice, JOR=Jordan, KAI=Kai)
- **Emotions**: `*action markers*` before text (`*warm*`=joy, `*fierce*`=determined, `*raw*`=vulnerable)
- **Structure**: Pipe-separated fields. `FAM: family | PROJ: projects | ⚠: warnings`
- **Dates**: ISO format (2026-04-08). Counts: `Nx` = N mentions (e.g., `570x`)
- **Importance**: ★ to ★★★★★ (1-5 scale)

Example diary entry in AAAK:

```
SESSION:2026-04-08|fixed.auth.bug.in.OAuth|KAI→reviewed|ALC→approved.deploy|★★★★
```

Call `mempalace_get_aaak_spec` for the full specification.

## Key Principles

1. **Store verbatim** — never summarize when filing drawers. The 96.6% recall score comes from raw mode.
2. **Check before filing** — always call `mempalace_check_duplicate` before `mempalace_add_drawer`.
3. **Update facts, don't duplicate** — when facts change, use `mempalace_kg_invalidate` + `mempalace_kg_add`.
4. **Verify before answering** — call `mempalace_search` or `mempalace_kg_query` before stating facts about people or projects. Wrong is worse than slow.
5. **Write diary entries** — at session end, record what happened in AAAK. Future sessions will thank you.

## CLI Commands (for setup and mining, not MCP)

```bash
# Setup
mempalace init <dir>                                    # guided onboarding
mempalace mine <dir>                                    # mine project files
mempalace mine <dir> --mode convos                      # mine conversation exports
mempalace mine <dir> --mode convos --wing myapp         # tag with wing name
mempalace mine <dir> --mode convos --extract general    # auto-classify content

# Splitting concatenated transcripts
mempalace split <dir>                                   # split into per-session files
mempalace split <dir> --dry-run                         # preview first

# Search (also available via MCP)
mempalace search "query"                                # search everything
mempalace search "query" --wing myapp                   # search within a wing
mempalace search "query" --room auth-migration          # search within a room

# Memory stack
mempalace wake-up                                       # load L0 + L1 context
mempalace wake-up --wing driftwood                      # project-specific wake-up

# Status
mempalace status                                        # palace overview
```

## Common Patterns

### User asks "what did we decide about X?"
```
→ mempalace_search(query="X decision", limit=5)
→ mempalace_kg_query(entity="X")
→ Synthesize from results, cite wings/rooms
```

### User says "remember that we chose Y over Z because..."
```
→ mempalace_check_duplicate(content="chose Y over Z because...")
→ mempalace_add_drawer(wing="wing_project", room="Y-vs-Z", content=<verbatim>)
→ mempalace_kg_add(subject="project", predicate="chose", object="Y", valid_from="2026-04-08")
```

### User asks "what do you know about person X?"
```
→ mempalace_kg_query(entity="X", direction="both")
→ mempalace_search(query="X", limit=5)
→ Present all relationships and relevant memories
```

### User says "actually, X moved to project Y"
```
→ mempalace_kg_invalidate(subject="X", predicate="works_on", object="OldProject")
→ mempalace_kg_add(subject="X", predicate="works_on", object="Y", valid_from="2026-04-08")
→ mempalace_add_drawer(wing="wing_X", room="role-change", content=<verbatim context>)
```

### Session end diary entry
```
→ mempalace_diary_write(agent_name="assistant", entry="SESSION:2026-04-08|discussed.auth.migration|KAI→assigned|fixed.OAuth.bug|★★★", topic="session-summary")
```
