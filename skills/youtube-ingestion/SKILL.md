---
name: youtube-ingestion
description: Ingest YouTube videos into the vault. Triggers when user pastes a YouTube URL (youtube.com/watch or youtu.be). Fetches transcript, creates transcript note and summary note. User may provide additional context about the video.
---

# YouTube Video Ingestion

Ingest YouTube videos into your vault by fetching transcripts and creating structured notes.

## Workflow

1. **Extract video ID** from the YouTube URL (the `v` parameter or from youtu.be short links)
2. **Fetch video metadata** (title, speaker/channel name) via the oEmbed API, see below
3. **Fetch transcript** using the bundled script
4. **Create transcript note** with full content and metadata
5. **Create summary note** with key insights, plus any user-provided reflections
6. **Run markdownlint** on both notes

## Usage

### Fetching transcripts

Run the transcript fetcher script (uses PEP723 inline metadata):

```bash
uv run <path-to-skill>/scripts/fetch_transcript.py <video_id> [--lang <language_code>]
```

The script outputs the transcript text to stdout. It does NOT output the video title or speaker name.

#### Non-English transcripts

The script tries `en` first, then falls back to whatever transcript languages are available. Pass `--lang <code>` to force a specific language (e.g. `--lang zh-CN` for Chinese-only videos). Many YouTube videos, especially from non-English creators, only have transcripts in their native language. Without the fallback the fetch silently fails and ingestion stalls.

### Obtaining video metadata (title and speaker)

The transcript script only provides spoken words. You need the title and speaker name separately for the note templates. Use the YouTube oEmbed API (no API key required):

```bash
curl -s 'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<video_id>&format=json'
```

This returns JSON with `title` (the video title) and `author_name` (the channel name).

- Use `title` as the Video Title for note naming and the frontmatter.
- Use `author_name` as the Speaker/Channel name. This is authoritative; do NOT hallucinate a real person's name from transcript context (e.g. the transcript may say "Hey, it's Jared" but you cannot infer a last name).
- Only fall back to WebFetch on the YouTube page if the oEmbed API fails.

### Creating notes

Create two notes in the vault. Both go in `Sources/`, NOT `Evergreen Notes/`:

1. **Transcript note**: `Sources/<Video Title> - <Speaker Name> (Transcript).md`
2. **Summary note**: `Sources/<Video Title> - Key insights.md`

Never file transcripts or key-insights summaries in `Evergreen Notes/`. That folder is reserved for atomic, concept-oriented notes written in your own words (see the `evergreen-note-quality` skill). Source artifacts, including raw transcripts and bullet-point summaries of external content, belong in `Sources/`.

### Note structure

**Transcript note structure:**

```markdown
# <Video Title> - <Speaker> (Transcript)

**Source**: [YouTube - <Video Title>](<youtube_url>)
**Speaker**: <speaker name>
**Project**: <project/company if mentioned>

---

## Full Transcript

<transcript text>

---

## Related

- [[<Summary note name>]]
```

**Summary note structure:**

```markdown
# <Video Title> - Key insights

**Source**: [[<Transcript note name>]]
**Speaker**: <speaker name>

---

## Core argument

<1-2 sentence summary of main thesis>

## Key points

### <Section 1 heading>

<bullet points or prose summarizing key insights>

### <Section 2 heading>

<bullet points or prose summarizing key insights>

## Key takeaway

<final synthesis or call to action>

## Connections to existing vault content

<Optional but high-value. When the user asks to see how the video connects to existing vault notes or collections, create an analytical section that maps the video's ideas to specific existing notes. Include:
- Where the video CONFIRMS existing principles (with wiki links to each)
- Where the video STOPS SHORT or diverges (the gaps are often the most valuable insight)
- Use a heading like "## Connections to <collection name>" and structure with confirmations and gaps. This is analytical work, not just a link list.>

## Reflections and open questions

<If the user shared thoughts, questions, or reactions when requesting ingestion, weave them in here. These are the user's own reflections, not summarised from the video. Format as questions or statements the user can build on later.>

## Related

- [[<Transcript note name>]]
```

## Guidelines

- Follow vault writing guidelines from AGENTS.md
- No em-dashes in agent-written prose, use commas/semicolons/periods instead. Verbatim source content (transcripts, direct quotes) is exempt: store as-is for fidelity
- No AI-sounding phrases ("stands as", "serves as", "it's important to note")
- Headers: capitalize first word only
- Never hallucinate wikilinks. Only link to notes that actually exist
- Link the transcript and summary notes to each other
- When the user asks to see connections to existing vault content, create an analytical "Connections to" section that maps the video to specific existing notes with both confirmations and gaps. This is distinct from the standard "Related" link list

## Script

See `scripts/fetch_transcript.py` for the transcript fetching implementation.

## Evergreen note extraction

When the user asks to "identify evergreen notes," "extract concepts," or "what can I learn from this video," do NOT stop at the summary note. Extract ATOMIC concept notes (one durable idea per note) following the `evergreen-note-quality` skill checklist. A summary note that bundles 5+ insights is NOT an evergreen note.

### Transcript notes are source artifacts, not evergreen

Confirmed by user correction (2026-06-14) and a prior vault audit: transcripts and key-insights summaries belong in `Sources/`, full stop. Never file them in `Evergreen Notes/`. `Evergreen Notes/` is for atomic concept notes synthesized in your own words only. If you want to extract durable concepts from a video into evergreen notes, see the evergreen-extraction workflow below, which creates separate atomic notes that DO belong in `Evergreen Notes/`.

### Workflow for evergreen extraction requests

1. Create the transcript note in `Sources/` as a source artifact (per the Creating notes section above)
2. For each distinct atomic claim in the video, create a SEPARATE evergreen note with a declarative title-as-API (e.g. "Active reading requires compressing ideas into your own words before moving on," not "ACTOR framework")
3. Link each evergreen note back to the transcript note as provenance
4. Search the vault for related notes and add 3+ wiki-links per evergreen note
5. Check for duplicates before creating (search the vault for existing notes on the same concept)
6. Run `markdownlint` on all created notes

This is distinct from the default workflow (transcript + summary). The default workflow is fine when the user just wants a record of the video. Use this extended workflow when the user explicitly asks for evergreen notes or concept extraction.
