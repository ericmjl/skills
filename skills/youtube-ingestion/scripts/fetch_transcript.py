#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Fetch YouTube video transcript and metadata using yt-dlp.

This script is a wrapper around yt-dlp for convenience.
Requires uv/uvx to be installed.

Usage:
    uv run fetch_transcript.py <video_id_or_url>
    uv run fetch_transcript.py --metadata <video_id_or_url>
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from URL or return as-is if already an ID."""
    patterns = [
        r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def get_metadata(url: str) -> dict:
    """Fetch video metadata as JSON."""
    result = subprocess.run(
        ["uvx", "yt-dlp", "--dump-json", "--no-download", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")

    data = json.loads(result.stdout)
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "description": data.get("description"),
        "duration": data.get("duration"),
        "uploader": data.get("uploader"),
        "upload_date": data.get("upload_date"),
        "channel": data.get("channel"),
        "channel_url": data.get("channel_url"),
    }


def get_transcript(url: str) -> str:
    """Fetch transcript text from YouTube video."""
    video_id = extract_video_id(url)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = str(Path(tmpdir) / "transcript")

        result = subprocess.run(
            [
                "uvx",
                "yt-dlp",
                "--write-auto-subs",
                "--sub-lang",
                "en",
                "--skip-download",
                "--sub-format",
                "vtt",
                "-o",
                output_template,
                url,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {result.stderr}")

        vtt_path = Path(tmpdir) / f"transcript.en.vtt"

        if not vtt_path.exists():
            raise FileNotFoundError(f"Transcript file not found at {vtt_path}")

        vtt_content = vtt_path.read_text()
        return parse_vtt(vtt_content)


def parse_vtt(vtt_content: str) -> str:
    """Parse VTT content and extract plain text."""
    lines = vtt_content.split("\n")
    text_lines = []

    for line in lines:
        if line.strip().startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line:
            continue
        if re.match(r"^\d+$", line.strip()):
            continue
        line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", line)
        line = re.sub(r"</?c>", "", line)
        line = line.strip()
        if line:
            text_lines.append(line)

    return " ".join(text_lines)


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: uv run fetch_transcript.py [--metadata] <video_id_or_url>",
            file=sys.stderr,
        )
        sys.exit(1)

    if sys.argv[1] == "--metadata":
        if len(sys.argv) < 3:
            print(
                "Usage: uv run fetch_transcript.py --metadata <video_id_or_url>",
                file=sys.stderr,
            )
            sys.exit(1)
        url = sys.argv[2]
        video_id = extract_video_id(url)
        metadata = get_metadata(video_id)
        print(json.dumps(metadata, indent=2))
    else:
        url = sys.argv[1]
        transcript = get_transcript(url)
        print(transcript)


if __name__ == "__main__":
    main()
