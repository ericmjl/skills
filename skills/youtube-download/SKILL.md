---
name: youtube-download
description: Downloads a YouTube video using yt-dlp. Use this when you need to download a video from YouTube to the local machine for offline viewing or processing.
license: MIT
---

# YouTube Video Downloader

This skill downloads YouTube videos using `yt-dlp`, always using the latest version via `uvx`.

## Usage

Download a video to the default location (`~/Downloads`):

```bash
uvx yt-dlp -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

Download to a custom location:

```bash
uvx yt-dlp -o "/path/to/folder/%(title)s.%(ext)s" "VIDEO_URL"
```

## Requirements

- `uv` - The Python package runner (provides `uvx` command)

No pre-installation of `yt-dlp` is needed. The `uvx` command automatically fetches and runs the latest version.

## Common Options

**Download best quality (default)**:
```bash
uvx yt-dlp -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download audio only (mp3)** - downloads to Synology music folder:
```bash
uvx yt-dlp -x --audio-format mp3 -o "~/Library/CloudStorage/SynologyDrive-sync/music/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download specific quality (e.g., 720p)**:
```bash
uvx yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**List available formats**:
```bash
uvx yt-dlp -F "VIDEO_URL"
```

## Output Template

The `-o` flag uses a template for the output filename:

- `%(title)s` - Video title
- `%(ext)s` - File extension
- `%(id)s` - Video ID
- `%(uploader)s` - Channel name

## Notes

- The default output format is **webm** (what YouTube natively provides for best quality)
- The download location defaults to `~/Downloads` but can be changed based on user preference
- **MP3 downloads go to `~/Library/CloudStorage/SynologyDrive-sync/music/`** (Synology NAS music folder)
- `uvx` ensures you always have the latest `yt-dlp` version without manual updates
- YouTube URLs should be quoted to handle special characters
