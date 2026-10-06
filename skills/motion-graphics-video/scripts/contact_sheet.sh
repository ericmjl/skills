#!/usr/bin/env bash
set -euo pipefail

# Extract one frame per story beat from a rendered video and tile them into a
# contact sheet PNG for the critique loop (see references/render-and-critique.md).
#
# Usage: contact_sheet.sh VIDEO DURATION_SECONDS [NUM_FRAMES] [OUTPUT] [COLUMNS]
#   VIDEO             rendered mp4 (any resolution)
#   DURATION_SECONDS  video duration (verify_render.sh prints it if unknown)
#   NUM_FRAMES        frames to sample, rounded up to a multiple of COLUMNS (default 12)
#   OUTPUT            output PNG path (default contact.png)
#   COLUMNS           grid columns (default 3)

VIDEO="${1:-}"
DURATION="${2:-}"
NUM_FRAMES="${3:-12}"
OUTPUT="${4:-contact.png}"
COLS="${5:-3}"

[[ -n "$VIDEO" ]]    || { echo "Error: video path required (arg 1)" >&2; exit 1; }
[[ -n "$DURATION" ]] || { echo "Error: video duration in seconds required (arg 2)" >&2; exit 1; }
[[ -f "$VIDEO" ]]    || { echo "Error: video not found: $VIDEO" >&2; exit 1; }

command -v ffmpeg >/dev/null 2>&1 || { echo "Error: ffmpeg not on PATH (brew install ffmpeg)" >&2; exit 1; }

ROWS=$(( (NUM_FRAMES + COLS - 1) / COLS ))
TOTAL=$(( ROWS * COLS ))
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

for (( i = 0; i < TOTAL; i++ )); do
  # Midpoint of each equal slice of the video
  T=$(awk -v d="$DURATION" -v n="$TOTAL" -v i="$i" 'BEGIN { printf "%.3f", d * (i + 0.5) / n }')
  FRAME="$(printf '%s/frame_%03d.png' "$WORKDIR" "$i")"
  if ! ffmpeg -hide_banner -loglevel error -ss "$T" -i "$VIDEO" -frames:v 1 -vf scale=480:-2 "$FRAME"; then
    echo "Error: frame extraction failed at t=${T}s (is duration correct?)" >&2
    exit 1
  fi
done

ffmpeg -hide_banner -loglevel error -y \
  -start_number 0 -i "$WORKDIR/frame_%03d.png" \
  -filter_complex "tile=${COLS}x${ROWS}" \
  -frames:v 1 "$OUTPUT"

echo "Contact sheet written: $OUTPUT (${TOTAL} frames, ${COLS}x${ROWS} grid)"
