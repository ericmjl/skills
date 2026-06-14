#!/usr/bin/env python3
# /// script
# dependencies = ["youtube-transcript-api"]
# ///
"""Fetch YouTube video transcript.

Usage:
    uv run fetch_transcript.py <video_id> [--lang <language_code>]

If --lang is omitted, tries 'en' first, then falls back to the first
available transcript language (handles non-English-only videos).
"""

import sys
from youtube_transcript_api import YouTubeTranscriptApi


def main():
    args = sys.argv[1:]
    lang = None

    if "--lang" in args:
        idx = args.index("--lang")
        lang = args[idx + 1]
        args = args[:idx] + args[idx + 2 :]

    if len(args) != 1:
        print(
            "Usage: uv run fetch_transcript.py <video_id> [--lang <language_code>]",
            file=sys.stderr,
        )
        sys.exit(1)

    video_id = args[0]

    try:
        api = YouTubeTranscriptApi()

        # Try requested language (default 'en'), then fall back to any available.
        languages_to_try = [lang] if lang else ["en"]
        transcript = None

        for try_lang in languages_to_try:
            try:
                transcript = api.fetch(video_id, languages=[try_lang])
                break
            except Exception:
                continue

        if transcript is None:
            # Fall back: list all available transcripts and fetch the first one.
            transcript_list = api.list(video_id)
            available = list(transcript_list)
            if not available:
                print(f"No transcripts available for video {video_id}", file=sys.stderr)
                sys.exit(1)
            transcript = available[0].fetch()

        for snippet in transcript.snippets:
            print(snippet.text, end=" ")
        print()

    except Exception as e:
        print(f"Error fetching transcript: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
