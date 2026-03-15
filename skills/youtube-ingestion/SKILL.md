---
name: youtube-ingestion
description: Ingest YouTube videos into the vault. Triggers when user pastes a YouTube URL (youtube.com/watch or youtu.be). Fetches transcript using yt-dlp, extracts metadata, creates transcript note and summary note. User may provide additional context about the video.
---

# YouTube Video Ingestion

Ingest YouTube videos into your vault by fetching transcripts and creating structured notes.

## Requirements

- `uv` - Provides `uvx` command for running yt-dlp

## Workflow

1. **Extract video ID** from the YouTube URL (the `v` parameter or from youtu.be short links)
2. **Fetch metadata** using yt-dlp (title, description, duration, uploader)
3. **Fetch transcript** using yt-dlp (downloads VTT, converts to plain text)
4. **Create transcript note** with full content and metadata
5. **Create summary note** with key insights extracted from the transcript
6. **Run markdownlint** on both notes

## Usage

### Fetching metadata

```bash
uvx yt-dlp --dump-json "YOUTUBE_URL"
```

Extract fields: `title`, `description`, `duration`, `uploader`, `upload_date`

### Fetching transcript

```bash
uvx yt-dlp --write-auto-subs --sub-lang en --skip-download -o "/tmp/youtube_transcript" "YOUTUBE_URL"
```

This creates `/tmp/youtube_transcript.en.vtt`. Then strip VTT formatting:

```bash
grep -v "^WEBVTT\|^Kind:\|^Language:\|-->\|^[0-9]" /tmp/youtube_transcript.en.vtt | \
  sed 's/<[0-9:.]*>//g' | \
  tr -s '\n' | \
  fold -s -w 80
```

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
**Duration**: <duration in mm:ss>
**Published**: <upload date>

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
- Duration format: convert seconds to `mm:ss` or `hh:mm:ss`

## Why yt-dlp

This skill uses `yt-dlp` instead of `youtube-transcript-api` because:

1. More reliable transcript fetching
2. Handles rate limiting better
3. Works with more video types
4. Provides rich metadata in a single call
5. Actively maintained with frequent updates
