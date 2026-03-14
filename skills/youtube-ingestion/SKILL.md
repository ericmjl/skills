---
name: youtube-ingestion
description: Ingest YouTube videos into the vault. Triggers when user pastes a YouTube URL (youtube.com/watch or youtu.be). Fetches transcript, creates transcript note and summary note. User may provide additional context about the video.
---

# YouTube Video Ingestion

Ingest YouTube videos into your vault by fetching transcripts and creating structured notes.

## Workflow

1. **Extract video ID** from the YouTube URL (the `v` parameter or from youtu.be short links)
2. **Fetch transcript** using the bundled script
3. **Create transcript note** with full content and metadata
4. **Create summary note** with key insights extracted from the transcript
5. **Run markdownlint** on both notes

## Usage

### Fetching transcripts

Run the transcript fetcher script:

```bash
uvx --with youtube-transcript-api python3 ~/.agents/skills/youtube-ingestion/scripts/fetch_transcript.py <video_id>
```

The script outputs the transcript text to stdout.

### Creating notes

Create two notes in the vault:

1. **Transcript note**: `Evergreen Notes/<Video Title> - <Speaker Name> (Transcript).md`
2. **Summary note**: `Evergreen Notes/<Video Title> - Key insights.md`

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

## Related

- [[<Transcript note name>]]
```

## Guidelines

- Follow vault writing guidelines from AGENTS.md
- No em-dashes, use commas/semicolons/periods instead
- No AI-sounding phrases ("stands as", "serves as", "it's important to note")
- Headers: capitalize first word only
- Never hallucinate wikilinks. Only link to notes that actually exist
- Link the transcript and summary notes to each other

## Script

See `scripts/fetch_transcript.py` for the transcript fetching implementation.
