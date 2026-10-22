#!/usr/bin/env bash
# MP4 1920x1080 from background.jpg (same image as v1 yyz.mp4: f95.jpg) + yyz_v2.wav, trimmed to audio length.
set -euo pipefail
cd "$(dirname "$0")"
IMG=${1:-background.jpg}; WAV=yyz_v2.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WAV")
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i "$IMG" -i "$WAV" -t "$DUR" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:v libx264 -tune stillimage -crf 20 -c:a aac -b:a 192k -movflags +faststart yyz_v2.mp4
echo "built yyz_v2.mp4 ($DUR s)"
