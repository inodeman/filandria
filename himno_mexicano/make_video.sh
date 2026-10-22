#!/usr/bin/env bash
# Builds 1920x1080 MP4 from thumb.jpg (falls back to placeholder.jpg) + the WAV.
set -euo pipefail
cd "$(dirname "$0")"
IMG=thumb.jpg; [ -f "$IMG" ] || IMG=placeholder.jpg
ffmpeg -y -loglevel error -loop 1 -framerate 2 -i "$IMG" -i himno_mexicano_filandria.wav \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p" \
  -c:v libx264 -tune stillimage -r 30 -c:a aac -b:a 192k -shortest -movflags +faststart himno_mexicano_filandria.mp4
echo "built himno_mexicano_filandria.mp4 from $IMG"
