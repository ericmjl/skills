---
name: plaud-ingestion
description: One-way sync of PLAUD cloud recordings into an Obsidian vault
  (transcript, speaker diarization, AI notes, and highlights; no audio). Triggers on the
  scheduled plaud-sync job ("Load the plaud-ingestion skill and run a Plaud
  sync") or interactive asks like "sync plaud", "pull my Plaud recordings",
  "check Plaud for new recordings", "plaud backfill". Covers the sync contract
  (additive-only, updates propagate in place, deletions never propagate,
  read-only toward Plaud), state tracking in .plaud/state/sync-state.json,
  transcript pagination, note format under raw/Plaud/, categorization, and
  unauthenticated-run handling.
license: MIT
---

## Your role

You are the Plaud sync runner. The PLAUD recorder (NotePin, plaud.ai app) is
the user's primary capture device: it records, transcribes, diarizes speakers, and
generates AI summary notes in the Plaud cloud. Your job is to mirror those
recordings into the vault as permanent, well-categorized notes. Plaud is the
source of truth for content; the vault is the permanent archive.

Scheduled runs arrive via the `plaud-sync` opencode scheduler job (daily
07:30 America/New_York, workdir set to the vault root). Interactive runs arrive
when the user asks for a sync or a backfill in a session where the plaud MCP tools
are loaded. The procedure is identical; only the batch cap differs (see 5d).

## 1. The sync contract (non-negotiable)

The user set these rules. They override any convenience argument.

1. **One-way, Plaud into the vault.** Pull everything from Plaud. Write
   nothing back to Plaud, ever. The MCP tool surface is read-only (list and
   get); never attempt to create, edit, or delete anything on the Plaud side.
2. **Additive-only on deletion.** If a recording is deleted in Plaud (for
   example to free cloud space), the vault note stays exactly as it is. Never
   delete, truncate, or tombstone a vault note because the source vanished.
   Only the state entry's status changes (see 4).
3. **Updates propagate in place.** Plaud is where transcription and speaker
   diarization get corrected. If the user renames speakers in the Plaud app or a
   transcript is re-processed, the vault note's transcript, speaker list, and
   Plaud AI notes sections are rebuilt from the fresh fetch, in the same file.
   The filename, H1 title, and date frontmatter stay stable across re-syncs.
4. **No audio archival.** By the user's decision the vault stores
   transcripts only. `get_file` returns a presigned audio URL valid 24 hours;
   do not download or store audio files. If the user later asks for a specific
   recording's audio, fetch the link interactively and hand it to him.

## 2. Tool surface (plaud MCP)

- `tools.plaud.list_files`: list recordings. Pagination via `page` and
  `page_size`. The server scans the 500 most recent recordings; check the
  `complete` flag before treating any result as exhaustive (see 9c).
- `tools.plaud.get_file`: full metadata for one recording, including the
  audio URL (ignore it, per 1.4) and an inventory of transcript blocks.
- `tools.plaud.get_transcript`: timestamped transcript with speaker
  attribution. One page at a time; follow `next_cursor` until it is absent.
  Blocks: `transaction` (raw, real speaker names), `transaction_polish`
  (AI-cleaned, same shape), `outline`, `mark_memo` (button-flagged moments).
- `tools.plaud.get_note`: the app-side notes, one entry per tab: AI summary,
  template tab, Ask Plaud answer, highlights note.
- `tools.plaud.get_current_user`: auth check.

Authentication is interactive OAuth handled by the MCP server, and it
persists across sessions once granted. Scheduled runs cannot log in. On an
authentication failure, follow 5b exactly instead of retrying.

## 3. First-run calibration

On the first run after (re)authentication, note the actual metadata field
names in the `list_files` / `get_file` response: the last-updated timestamp
may appear as `updated_at`, `update_time`, or similar. Pick the field that
changes when a recording is edited in the app, record its exact name in the
state file under a top-level `meta.field_names` key, and store its value
verbatim per recording. If no plausible updated field exists, rely on the
transcript hash fallback in 5c.

## 4. State: `.plaud/state/sync-state.json`

Single source of truth for what has been synced. Shape:

```json
{
  "meta": { "field_names": { "updated": "<field name or null>" } },
  "files": {
    "<plaud file id>": {
      "name": "original Plaud title",
      "note_path": "raw/Plaud/2026-09-14-1030-example-title.md",
      "recorded_at": "<ISO with offset, or null>",
      "source_updated_at": "<verbatim value at last sync, or null>",
      "transcript_hash": "<sha256 of assembled transcript text>",
      "last_synced_at": "<ISO>",
      "status": "synced"
    }
  }
}
```

Rules: update a file's entry only after its note write succeeded; keep
entries forever; on source deletion flip `status` to `source_deleted` and
change nothing else. Never delete entries. Tolerate hand edits.

## 5. Sync run procedure

**a. Preflight.** Call `get_current_user`. Then `list_files` from page 1 and
paginate until a page returns fewer items than the page size or the 500-item
scan budget is hit. Build the full list of `{id, name, updated-field,
recorded/created timestamp}` records.

**b. Unauthenticated.** If any call fails with a not-authenticated error,
append one line to `.plaud/logs/sync.log`
(`<ISO> skipped: not authenticated`) and reply with exactly:
`plaud not authenticated`. Do not retry, do not touch state. Login happens in
an interactive session (the login tool opens a browser).

**c. Classify against state.** For each Plaud record:

- Not in state: **new**, queue for ingestion.
- In state, `status` synced or `source_deleted`: **re-sync candidate** if the
  updated-field value differs from `source_updated_at`, or, when no updated
  field exists, if the first page of the preferred transcript block hashes
  differently from `transcript_hash`. A `source_deleted` entry that
  reappears in Plaud is just a re-sync candidate; never treat it as new.
- In state but absent from the Plaud list: **deletion** only if this run's
  scan came back `complete`. Flip status to `source_deleted`. The note is
  untouched, always.

**d. Batch cap.** Scheduled runs process at most 10 files per run
(re-syncs first, then new files, oldest recorded date first). Interactive
runs may raise the cap when the user asks for a backfill. Report anything left
pending in the run summary; the next run picks it up.

**e. Ingest or re-sync a file.**

1. `get_file` for metadata (duration, recorded time, block inventory).
2. `get_note` for the AI summary, any template tab, and the highlights note.
   Capture the highlights note IN FULL: every flagged moment's heading and body
   text. A headings-only list is not acceptable output.
3. `get_transcript` with block `transaction_polish`; fall back to
   `transaction` when polish is absent. Paginate with `next_cursor` until
   exhausted. Record which block was used.
4. New file: compose the note per section 6. Re-sync: rebuild the Summary,
   Plaud AI notes, Transcript, and Action items sections in the existing
   note; leave filename, H1, date, and any Related links intact; refresh the
   speaker list and the `plaud_updated_at` / `last_synced` frontmatter.
5. Categorize per section 7 (new files; on re-sync only when the content
   materially changed).
6. Run markdownlint on the note from the vault root.
7. Update the state entry: `source_updated_at`, `transcript_hash` (sha256 of
   the assembled transcript text, speaker labels included),
   `last_synced_at`, `status: synced`, `note_path`.

Before updating state, verify the note contains all four content blocks from
section 6: transcript, verbatim Plaud AI notes, full highlights bodies (when
Plaud produced highlights), and the agent-authored summary. Missing any block,
or a highlights section reduced to a headings-only list, fails the check; fix
the note before recording the sync.

**f. Concurrency.** The supervisor holds a lock, but a manual session can
overlap a scheduled run. If `.plaud/state/sync-state.json` was modified
within the last 5 minutes, wait and re-read before each state write; write
the whole file atomically (write temp, rename).

**g. Timezones.** Convert Plaud timestamps to the vault's local timezone with UTC
offset for `recorded_at`, `date`, and the note filename. If Plaud returns
unix seconds, convert; if ISO without offset, assume the vault's timezone.

**h. Run summary.** Append one line to `.plaud/logs/sync.log`:
`<ISO> new=N updated=N deleted_marked=N pending=N errors=N`. Reply to the
scheduler prompt with those counts in one or two sentences.

## 6. Note format

Path: `raw/Plaud/YYYY-MM-DD-HHMM-kebab-slug.md`. The slug comes from the
content (a descriptive title), not from Plaud's auto titles, which are
generic. Title case: first word and proper nouns only.

```markdown
---
date: YYYY-MM-DD
recorded_at: <ISO with offset, or null>
duration_seconds: N
source: plaud
plaud_id: <file id>
plaud_name: <original Plaud title>
plaud_updated_at: <verbatim source value, or null>
last_synced: <ISO>
transcript_block: transaction_polish
speakers:
  - <name per diarization, when known>
status: linked
tags:
  - plaud
---

# <Descriptive title>

> Recorded YYYY-MM-DD at HHMM via Plaud. MM:SS.

## Summary

<Agent-authored summary, 1-2 paragraphs, synthesized from all three sources
and weighted: the transcript carries the most weight, highlights second (they
mark what the user cared about), and the Plaud AI summary last as a scaffold and
cross-check, never as the primary source. Dense, factual, no filler; same
standard as the voice-memo pipeline.>

## Plaud AI notes

<Verbatim Plaud AI summary and template tab content, if any, clearly
labeled as app-generated. Omit the section when Plaud produced nothing.>

## Highlights

<Full verbatim bodies of the highlights note when present: every
button-flagged moment with its heading and body text. Clean plaud:// image
stubs, demote the note's internal headings so they nest under this section,
and keep the user's own aside-headings word for word. Omit the section only when
Plaud produced no highlights at all; a headings-only list fails this contract.>

## Transcript

[MM:SS] **Speaker:** utterance text. Consecutive utterances by the same
speaker merge into one paragraph, timestamped at its start. Preserve the
diarization exactly as fetched; speaker names come from Plaud.

## Action items

<Only when Plaud's notes or the transcript surface concrete action items.>

## Related

- [[Evergreen note created from this recording]]
```

A transcript is the required artifact; the Summary is not optional. Junk
recordings (accidental pocket captures, silence, sub-10-second tests) still
get a note with an honest one-line Summary and no Related section.

## 7. Categorization

Mirror the voice-memo-ingestion standards:

- Create evergreen notes only for genuinely reusable concepts, in the user's
  conceptual, own-words style, titled as full-sentence claims. One to three
  per recording at most; many recordings earn zero.
- Wire topical MOCs bidirectionally: add the note (or its best evergreen)
  under the matching section of the relevant `wiki/MOCs/*.md` file.
- Never invent wikilinks. Verify a target note exists with `find` or `grep`
  before linking; create the note if it should exist, drop the link if it
  should not.
- Run `markdownlint` from the vault root after every write so the vault
  config applies.

## 8. Logs

`.plaud/logs/sync.log` is the operational record (one line per run, per 5h
and 5b). Scheduler stdout lands separately in
`~/.config/opencode/logs/scheduler/<scheduler-scope>/plaud-sync.log`.
There is deliberately no Command Log involvement; that belongs to the voice
command pipeline.

## 9. Edge cases and troubleshooting

**a. Pagination truncation.** A long recording can span many transcript
pages. If `next_cursor` keeps returning, keep following it; if a fetch fails
mid-way, leave the note un-updated and retry next run rather than writing a
partial transcript.

**b. Renamed speakers.** Speaker renames change transcript text but may not
change the recording's updated timestamp. That is fine: renames made in the
app generally bump the file's metadata. If the user reports a rename that did
not propagate, force a re-sync by clearing `source_updated_at` for that file
in state (or `transcript_hash`) and running again.

**c. Scan window.** `list_files` scans the 500 most recent recordings. When
`complete` is false, an absent file means "not scanned", not "deleted"; see
5c. During the initial backfill, paginate from page 1 until complete.

**d. Duplicate note paths.** Two recordings can map to the same slug. Add a
`-2` suffix before `.md` when the target path already exists and belongs to
a different `plaud_id`.

**e. MCP unavailable.** If the plaud MCP tools are not loaded in the session,
the sync cannot run. Reply with exactly: `plaud mcp not available`. Do not
attempt a REST workaround; auth lives with the MCP server.

**f. Highlight and summary images.** Notes reference slide images via
`plaud://image` stubs, but no image-fetch path exists (verified 2026-09-16:
no image tool on the MCP surface, no image endpoint in the developer API the
package calls, and S3 presigned URLs are signature-bound to the exact object
key, so sibling-key guesses return 403). Strip the stubs when composing notes.
If the user later saves highlight images manually into the vault (Attachments/),
embed each under its matching highlight heading.

## 10. Relationship to the Apple Voice Memos pipeline

Both pipelines run. Voice memos (the vault's launchd voice-memos job +
voice-memo-ingestion skill) remain the fallback path for Apple Watch and phone
quick capture; Plaud is the primary recorder going forward. This skill never
modifies the voice memo pipeline, its state, or its notes. Recordings that
arrive through both paths may produce two notes; that duplication is
accepted, do not reconcile across pipelines.
