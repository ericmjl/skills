#!/usr/bin/env python3
# /// script
# dependencies = ["youtube-transcript-api"]
# ///
"""Fetch YouTube video transcript.

Usage:
    uv run fetch_transcript.py <video_id>
"""

import sys
from youtube_transcript_api import YouTubeTranscriptApi


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run fetch_transcript.py <video_id>", file=sys.stderr)
        sys.exit(1)

    video_id = sys.argv[1]

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)

        for snippet in transcript.snippets:
            print(snippet.text, end=" ")
        print()

    except Exception as e:
        print(f"Error fetching transcript: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
