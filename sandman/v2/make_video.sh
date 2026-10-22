#!/usr/bin/env bash
# MP4 1920x1080: thumb.jpg if present (else placeholder.jpg) + WAV, trimmed to the audio length.
set -euo pipefail
cd "$(dirname "$0")"
IMG=thumb.jpg; [ -f "$IMG" ] || IMG=placeholder.jpg
WAV=enter_sandman_filandria.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WAV")
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i "$IMG" -i "$WAV" -t "$DUR" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:v libx264 -tune stillimage -crf 20 -c:a aac -b:a 192k -movflags +faststart enter_sandman_filandria.mp4
echo "built enter_sandman_filandria.mp4 from $IMG ($DUR s)"
