---
name: youtube
description: >-
  Comprehensive YouTube operations using yt-dlp - download videos/audio, extract transcripts and subtitles, get metadata, work with playlists, download thumbnails, and inspect available formats. Also covers fixing HTTP 429 rate-limit / bot-check failures with --cookies-from-browser, and the follow-on 'Only images are available for download' / 'Requested format is not available' metadata-extraction failure on old videos (fix: --remote-components ejs:github pulls the current n/sig challenge solver). Use this for any YouTube content processing task.
license: MIT
---

# YouTube operations

This skill provides comprehensive YouTube operations using `yt-dlp`, always using the latest version via `uvx`.

## Requirements

- `uv` - The Python package runner (provides `uvx` command)

No pre-installation of `yt-dlp` is needed. The `uvx` command automatically fetches and runs the latest version.

## Video downloads

**Download best quality (default)**:
```bash
uvx yt-dlp -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download to custom location**:
```bash
uvx yt-dlp -o "/path/to/folder/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download specific quality (e.g., 720p)**:
```bash
uvx yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**List available formats before downloading**:
```bash
uvx yt-dlp -F "VIDEO_URL"
```

## Audio downloads

**Download audio only (mp3)** - downloads to Synology music folder:
```bash
uvx yt-dlp -x --audio-format mp3 -o "~/Library/CloudStorage/SynologyDrive-sync/music/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download audio in other formats**:
```bash
# AAC format
uvx yt-dlp -x --audio-format aac -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"

# Opus format
uvx yt-dlp -x --audio-format opus -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"

# Best quality audio (no conversion)
uvx yt-dlp -f bestaudio -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

## Transcript and subtitle extraction

**Download subtitles only (no video)**:
```bash
# Auto-generated or manual subtitles in English
uvx yt-dlp --skip-download --write-auto-subs --sub-lang en --sub-format vtt -o "~/Downloads/%(title)s" "VIDEO_URL"

# Manual subtitles only (not auto-generated)
uvx yt-dlp --skip-download --write-subs --sub-lang en --sub-format vtt -o "~/Downloads/%(title)s" "VIDEO_URL"
```

**Download subtitles in multiple languages**:
```bash
uvx yt-dlp --skip-download --write-subs --sub-lang en,es,fr --sub-format vtt -o "~/Downloads/%(title)s" "VIDEO_URL"
```

**List available subtitles**:
```bash
uvx yt-dlp --list-subs "VIDEO_URL"
```

**Convert subtitles to plain text** (remove timestamps):
```bash
# Download as SRT first, then process
uvx yt-dlp --skip-download --write-auto-subs --sub-lang en --sub-format srt -o "~/Downloads/%(title)s" "VIDEO_URL"

# Then use sed or awk to extract just the text
sed '/^[0-9]*$/d; /^[0-9][0-9]:/d; /^$/d' ~/Downloads/video-title.en.srt > ~/Downloads/transcript.txt
```

**Download video with embedded subtitles**:
```bash
uvx yt-dlp --write-subs --embed-subs --sub-lang en -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

## Metadata extraction

**Get video information without downloading**:
```bash
# Basic info as JSON
uvx yt-dlp --dump-json "VIDEO_URL"

# Just the title
uvx yt-dlp --get-title "VIDEO_URL"

# Just the description
uvx yt-dlp --get-description "VIDEO_URL"

# Duration
uvx yt-dlp --get-duration "VIDEO_URL"

# Upload date
uvx yt-dlp --get-filename -o "%(upload_date)s" "VIDEO_URL"

# Channel/uploader
uvx yt-dlp --get-filename -o "%(uploader)s" "VIDEO_URL"
```

**Extract all metadata to JSON file**:
```bash
uvx yt-dlp --dump-json --skip-download "VIDEO_URL" > video-metadata.json
```

**Get video chapters/timestamps**:
```bash
# Chapters are included in --dump-json output
uvx yt-dlp --dump-json "VIDEO_URL" | jq '.chapters'
```

## Playlist operations

**Download entire playlist**:
```bash
uvx yt-dlp -o "~/Downloads/%(playlist)s/%(playlist_index)s-%(title)s.%(ext)s" "PLAYLIST_URL"
```

**Download playlist as audio only**:
```bash
uvx yt-dlp -x --audio-format mp3 -o "~/Library/CloudStorage/SynologyDrive-sync/music/%(playlist)s/%(title)s.%(ext)s" "PLAYLIST_URL"
```

**Download specific videos from playlist**:
```bash
# Videos 1-5
uvx yt-dlp --playlist-items 1-5 -o "~/Downloads/%(title)s.%(ext)s" "PLAYLIST_URL"

# Specific videos (1, 3, 5)
uvx yt-dlp --playlist-items 1,3,5 -o "~/Downloads/%(title)s.%(ext)s" "PLAYLIST_URL"
```

**Get playlist information without downloading**:
```bash
# Full playlist metadata
uvx yt-dlp --dump-json --flat-playlist "PLAYLIST_URL"

# Just list video titles
uvx yt-dlp --get-filename -o "%(title)s" --flat-playlist "PLAYLIST_URL"
```

**Download only new videos from playlist** (useful for subscriptions):
```bash
# Creates archive file to track downloaded videos
uvx yt-dlp --download-archive archive.txt -o "~/Downloads/%(title)s.%(ext)s" "PLAYLIST_URL"
```

## Thumbnail downloads

**Download thumbnail only**:
```bash
uvx yt-dlp --skip-download --write-thumbnail --convert-thumbnails png -o "~/Downloads/%(title)s" "VIDEO_URL"
```

**Download video with embedded thumbnail**:
```bash
uvx yt-dlp --embed-thumbnail -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**Get all available thumbnails**:
```bash
uvx yt-dlp --list-thumbnails "VIDEO_URL"
```

## Advanced options

**Download with speed limit**:
```bash
uvx yt-dlp --limit-rate 1M -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download age-restricted content** (requires cookies):
```bash
# Export cookies from browser first, then:
uvx yt-dlp --cookies cookies.txt -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download with custom filename**:
```bash
uvx yt-dlp -o "~/Downloads/my-custom-name.%(ext)s" "VIDEO_URL"
```

**Resume interrupted download**:
```bash
# yt-dlp resumes automatically if you run the same command
uvx yt-dlp -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**Download with date range filter**:
```bash
# Only videos uploaded after date
uvx yt-dlp --dateafter 20240101 "CHANNEL_URL"

# Only videos uploaded before date
uvx yt-dlp --datebefore 20241231 "CHANNEL_URL"
```

## Output filename templates

The `-o` flag uses templates for output filenames. Common variables:

- `%(title)s` - Video title
- `%(id)s` - Video ID
- `%(ext)s` - File extension
- `%(uploader)s` - Channel name
- `%(upload_date)s` - Upload date (YYYYMMDD)
- `%(playlist)s` - Playlist name
- `%(playlist_index)s` - Video position in playlist
- `%(duration)s` - Video duration in seconds
- `%(resolution)s` - Video resolution

**Example with multiple variables**:
```bash
uvx yt-dlp -o "~/Downloads/%(uploader)s/%(upload_date)s-%(title)s.%(ext)s" "VIDEO_URL"
```

## Common workflows

**Create audio podcast archive from YouTube channel**:
```bash
uvx yt-dlp --download-archive podcast-archive.txt -x --audio-format mp3 -o "~/Music/Podcasts/%(uploader)s/%(title)s.%(ext)s" "CHANNEL_URL"
```

**Extract transcripts for research**:
```bash
# Download all video transcripts from a playlist
uvx yt-dlp --skip-download --write-auto-subs --sub-lang en --sub-format srt -o "~/Documents/transcripts/%(title)s" "PLAYLIST_URL"
```

**Download video with all extras**:
```bash
# Video + subtitles + thumbnail + metadata
uvx yt-dlp --write-subs --embed-subs --write-thumbnail --embed-thumbnail --write-info-json -o "~/Downloads/%(title)s.%(ext)s" "VIDEO_URL"
```

**Monitor and archive a channel**:
```bash
# Run periodically to get only new uploads
uvx yt-dlp --download-archive channel-archive.txt -o "~/Videos/%(uploader)s/%(upload_date)s-%(title)s.%(ext)s" "CHANNEL_URL/videos"
```

## Rate limiting (HTTP 429 / bot check) — use --cookies-from-browser chrome

**Trigger**: after a batch of yt-dlp metadata pulls (e.g. `-j`/`--dump-json` across a channel playlist or a dozen videos), subsequent calls return EMPTY output (the exit code can still look fine when piping through jq/python, so the failure is SILENT) or fail with HTTP 429 + a bot-check page. Empty output from a `-j` pull is NOT a parse failure — check raw stderr first (`uvx yt-dlp <url> -j 2>&1 | head -c 500`) before blaming your parsing pipeline.

**Root cause**: YouTube rate-limits and bot-checks by IP; bulk metadata pulls from one IP trip it.

**Fix**: pass browser cookies so requests ride an authenticated session:

```bash
uvx yt-dlp --cookies-from-browser chrome -j "https://www.youtube.com/watch?v=VIDEO_ID"
```

Verified working 2026-08-22 (website talks-description task) after a 12-video metadata batch hit 429 + bot check.

**Gotchas**:

- A warning about an "n challenge" may print; it is BENIGN — the JSON still comes through. Verify with `head -c 300` on the output rather than assuming failure from the warning.
- On macOS, Chrome cookies work directly; Safari cookie access requires extra permissions (prefer chrome/firefox/arc in that order).
- `--cookies cookies.txt` (manual export, used above for age-restricted content) is a different, older flow; `--cookies-from-browser` needs no export step.
- Expect the SECOND bulk batch in a session to need the cookies flag even when the first batch (e.g. playlist pulls) worked without it.

## Follow-on failure: "Only images are available" / "Requested format is not available" (old videos, even with cookies)

**Trigger**: on OLD videos (2017-era conference talk uploads), even AFTER the cookies fix above, `-j`/`--dump-json` dies with "Only images are available for download" + "Requested format is not available".

**Root cause**: the video's format list comes back empty (the player response lacks stream formats; the n-challenge warning that is usually BENIGN — see gotcha above — becomes FATAL here). `-j` already implies simulate, so the failure is in format-table resolution, not download intent.

**Diagnose FIRST (cheap probes before any fix)**:

- `uvx yt-dlp -F "VIDEO_URL"` — enumerate which formats ARE actually available
- `uvx yt-dlp --version` — uvx CACHES environments, so a cached stale yt-dlp release is a candidate root cause; force `uvx yt-dlp@latest` to rule it out

**Dead-end ladder (all tried 2026-08-23 on s0S6HFdPtlA, PyData NYC 2017; NONE fixed it — do not re-walk blindly)**: `--js-runtimes node`, brew-installing deno (yt-dlp's default JS runtime), `--extractor-args "youtube:player_client=android|web_embedded|tv"`.

**Candidate fallback (untested — verify before relying on it)**: if only title/author are needed, the oEmbed endpoint `https://www.youtube.com/oembed?url=<url>&format=json` requires no format resolution at all.

**Debug discipline from the same spiral**: never suppress stderr (`2>/dev/null`) while diagnosing — it turned a clear yt-dlp error into mystery "empty output"; do not invent flag combinations (`--with-requirements /dev/null` is nonsense); run the cheap observational probe (`-F`, `--version`) BEFORE expensive speculative fixes (installing JS runtimes, swapping player clients).


**RESOLVED (2026-08-23, same task): the fix is `--remote-components ejs:github`.** yt-dlp ships its n/sig challenge solver as EJS components (github.com/yt-dlp/ejs); when the solver BUNDLED with your yt-dlp release is stale relative to YouTube's current player, format resolution dies with the errors above even with cookies, a fresh yt-dlp, and working JS runtimes. `--remote-components ejs:github` lets yt-dlp download the CURRENT solver from GitHub into `~/.cache/yt-dlp/challenge-solver/` — which is why the entire runtime/player_client dead-end ladder above failed: the runtime was never the problem, the stale solver was. Verified working invocation (unlocked the full 12-video batch with zero runtime installs, including s0S6HFdPtlA):

```bash
uvx yt-dlp --cookies-from-browser chrome --remote-components ejs:github -j "https://www.youtube.com/watch?v=VIDEO_ID"
```

Notes: `--remote-components ejs:npm` is the sibling option (solver from npm); the yt-dlp wiki recommends putting the flag in your yt-dlp config so solvers auto-update. Try remote-components FIRST when you see the n-challenge warning turn fatal — before installing any JS runtime or swapping player clients.

**Deno role (2026-08-23 session-summary cross-check): necessary-but-not-sufficient.** The remote EJS solver still needs a JS runtime to EXECUTE, and deno (yt-dlp's default runtime, brew-installed during the dead-end ladder above and left in place) was present in the session's final working stack — the session's own report attributed success to "chrome cookies + deno". Installing deno ALONE does not fix the stale-solver problem (that was the dead end); `--remote-components ejs:github` WITH a working JS runtime does. Keep a JS runtime installed when applying the fix — do not uninstall deno or dismiss it as pure dead weight.

## Notes

- The default video format is **webm** (YouTube's native best quality)
- The default download location is `~/Downloads` but can be changed
- **MP3 audio downloads go to `~/Library/CloudStorage/SynologyDrive-sync/music/`** (Synology NAS)
- `uvx` ensures you always have the latest `yt-dlp` version without manual updates
- YouTube URLs should be quoted to handle special characters
- Subtitle formats: `vtt` (WebVTT), `srt` (SubRip), `json3` (timestamped JSON)
- Auto-generated subtitles are often available even when manual ones aren't
- Use `--dump-json` to explore all available metadata fields
