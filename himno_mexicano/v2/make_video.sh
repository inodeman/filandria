#!/usr/bin/env bash
# MP4 1920x1080 from ../thumb.jpg (or ./thumb.jpg) + the v2 WAV, trimmed exactly to the audio length.
set -euo pipefail
cd "$(dirname "$0")"
IMG=${1:-}
for c in "$IMG" thumb.jpg ../thumb.jpg placeholder.jpg; do [ -n "$c" ] && [ -f "$c" ] && { IMG=$c; break; }; done
WAV=himno_mexicano_filandria_v2.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WAV")
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i "$IMG" -i "$WAV" -t "$DUR" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p" \
  -c:v libx264 -tune stillimage -preset medium -crf 20 -c:a aac -b:a 192k -movflags +faststart himno_mexicano_filandria_v2.mp4
echo "built himno_mexicano_filandria_v2.mp4 from $IMG ($DUR s)"
