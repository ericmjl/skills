#!/usr/bin/env bash
set -euo pipefail

# Verify a rendered motion graphics video: duration, streams, loudness, poster.
# Usage: verify_render.sh VIDEO EXPECTED_DURATION_SECONDS [TOLERANCE] [POSTER_OUT]
#   VIDEO                       rendered mp4
#   EXPECTED_DURATION_SECONDS   duration from the composition definition
#   TOLERANCE                   allowed duration drift in seconds (default 0.5)
#   POSTER_OUT                  optional path for a mid-video poster frame PNG

VIDEO="${1:-}"
EXPECTED="${2:-}"
TOLERANCE="${3:-0.5}"
POSTER="${4:-}"

[[ -n "$VIDEO" ]]    || { echo "Error: video path required (arg 1)" >&2; exit 1; }
[[ -n "$EXPECTED" ]] || { echo "Error: expected duration in seconds required (arg 2)" >&2; exit 1; }
[[ -f "$VIDEO" ]]    || { echo "Error: video not found: $VIDEO" >&2; exit 1; }

command -v ffprobe >/dev/null 2>&1 || { echo "Error: ffprobe not on PATH (brew install ffmpeg)" >&2; exit 1; }
command -v ffmpeg  >/dev/null 2>&1 || { echo "Error: ffmpeg not on PATH (brew install ffmpeg)" >&2; exit 1; }

FAILED=0

# --- Duration ---
ACTUAL=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$VIDEO")
DELTA=$(awk -v a="$ACTUAL" -v e="$EXPECTED" 'BEGIN { d = a - e; if (d < 0) d = -d; printf "%.3f", d }')
WITHIN=$(awk -v d="$DELTA" -v t="$TOLERANCE" 'BEGIN { print (d <= t) ? 1 : 0 }')
if [[ "$WITHIN" == "1" ]]; then
  echo "OK   duration ${ACTUAL}s (expected ${EXPECTED}s, delta ${DELTA}s)"
else
  echo "FAIL duration ${ACTUAL}s (expected ${EXPECTED}s, delta ${DELTA}s > ${TOLERANCE}s)" >&2
  FAILED=1
fi

# --- Streams ---
VSTREAMS=$(ffprobe -v error -select_streams v -show_entries stream=codec_type -of default=nw=1:nk=1 "$VIDEO" | wc -l | tr -d ' ')
ASTREAMS=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of default=nw=1:nk=1 "$VIDEO" | wc -l | tr -d ' ')
echo "     streams: video=${VSTREAMS} audio=${ASTREAMS}"
if [[ "$VSTREAMS" -lt 1 ]]; then echo "FAIL no video stream" >&2; FAILED=1; fi
if [[ "$ASTREAMS" -lt 1 ]]; then echo "FAIL no audio stream (silent video)" >&2; FAILED=1; fi

# --- Loudness (integrated, LUFS) ---
LOUDNESS=$(ffmpeg -hide_banner -nostats -i "$VIDEO" -af loudnorm=print_format=json -f null - 2>&1 \
  | sed -n 's/.*"input_i" : "\{0,1\}\(-\{0,1\}[0-9.]*\)"\{0,1\}.*/\1/p' | head -1)
if [[ -n "$LOUDNESS" ]]; then
  DRIFT=$(awk -v l="$LOUDNESS" 'BEGIN { d = l - (-14); if (d < 0) d = -d; printf "%.2f", d }')
  if awk -v d="$DRIFT" 'BEGIN { exit (d <= 3) ? 0 : 1 }'; then
    echo "OK   loudness ${LOUDNESS} LUFS (target -14, drift ${DRIFT})"
  else
    echo "FAIL loudness ${LOUDNESS} LUFS (target -14, drift ${DRIFT} > 3); remix with loudnorm" >&2
    FAILED=1
  fi
else
  echo "WARN could not measure loudness (corrupt audio?)"
fi

# --- Poster frame ---
if [[ -n "$POSTER" ]]; then
  MID=$(awk -v a="$ACTUAL" 'BEGIN { printf "%.3f", a / 2 }')
  ffmpeg -hide_banner -loglevel error -y -ss "$MID" -i "$VIDEO" -frames:v 1 "$POSTER"
  echo "OK   poster frame: $POSTER (t=${MID}s)"
fi

exit "$FAILED"
