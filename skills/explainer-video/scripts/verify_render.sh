#!/usr/bin/env bash
set -euo pipefail

# Check a rendered explainer: duration, pixel size, and that audio exists.
# Usage: verify_render.sh VIDEO EXPECTED_SECONDS [WIDTH] [HEIGHT] [TOLERANCE]

VIDEO="${1:-}"
EXPECTED="${2:-}"
WIDTH="${3:-1080}"
HEIGHT="${4:-1920}"
TOLERANCE="${5:-0.5}"

if [[ -z "$VIDEO" ]]; then
  echo "Error: video path required (arg 1)." >&2
  exit 1
fi
if [[ -z "$EXPECTED" ]]; then
  echo "Error: expected duration in seconds required (arg 2)." >&2
  exit 1
fi
if [[ ! -f "$VIDEO" ]]; then
  echo "Error: video not found: $VIDEO" >&2
  exit 1
fi
if ! command -v ffprobe >/dev/null 2>&1; then
  echo "Error: ffprobe is not on PATH. Install ffmpeg." >&2
  exit 1
fi

FAILED=0

ACTUAL="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$VIDEO")"
DELTA="$(awk -v a="$ACTUAL" -v e="$EXPECTED" 'BEGIN { d = a - e; if (d < 0) d = -d; printf "%.3f", d }')"
WITHIN="$(awk -v d="$DELTA" -v t="$TOLERANCE" 'BEGIN { print (d <= t) ? 1 : 0 }')"
if [[ "$WITHIN" == "1" ]]; then
  echo "OK   duration ${ACTUAL}s (expected ${EXPECTED}s, delta ${DELTA}s)"
else
  echo "FAIL duration ${ACTUAL}s (expected ${EXPECTED}s, delta ${DELTA}s > ${TOLERANCE}s)" >&2
  FAILED=1
fi

READ_W="$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=nw=1:nk=1 "$VIDEO")"
READ_H="$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=nw=1:nk=1 "$VIDEO")"
if [[ "$READ_W" == "$WIDTH" && "$READ_H" == "$HEIGHT" ]]; then
  echo "OK   frame ${READ_W}x${READ_H}"
else
  echo "FAIL frame ${READ_W}x${READ_H} (expected ${WIDTH}x${HEIGHT})" >&2
  FAILED=1
fi

AUDIO_COUNT="$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of default=nw=1:nk=1 "$VIDEO" | wc -l | tr -d ' ')"
if [[ "$AUDIO_COUNT" -ge 1 ]]; then
  echo "OK   audio streams ${AUDIO_COUNT}"
else
  echo "FAIL no audio stream" >&2
  FAILED=1
fi

exit "$FAILED"
