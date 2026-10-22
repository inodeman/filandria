#!/usr/bin/env bash
# MP4 1920x1080: c.jpg (12-filament Filandria) + WAV + subtle title overlay, trimmed to the audio.
set -euo pipefail
cd "$(dirname "$0")"
IMG=${IMG:-background.jpg}; WAV=dream_on_filandria.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WAV")
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i "$IMG" -i "$WAV" -t "$DUR" \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='Dream On (Aerosmith) – La Filandria':fontsize=40:fontcolor=white@0.75:shadowcolor=black@0.6:shadowx=2:shadowy=2:x=60:y=h-100,format=yuv420p" \
  -c:v libx264 -tune stillimage -crf 20 -c:a aac -b:a 192k -movflags +faststart dream_on_filandria.mp4
echo "built dream_on_filandria.mp4 ($DUR s)"
