# Dream On (Aerosmith): La Filandria cromática, nuevo diseño de 12 filamentos

Cover instrumental de "Dream On" (Steven Tyler, álbum *Aerosmith*, 1973), tocado en la Filandria de 12 filamentos de vidrio con clavijas de cobre de octava (`"tuning": "cromatica"`, F1–F6, A440). Es un solo render continuo de 4:24 a 92 negras por minuto, en fa menor, hecho con el motor de bajo ruido `render_v2_engine.py` (el mismo de sandman/v2). No tiene cortes ni crossfades.

Estructura: intro (Fm, Fm/E, Fm/Eb, Fm/D, Db, Csus–C, luego Bb7, Eb7, Edim7, Fm), estrofa 1, pre-coro (Dm7b5, Csus–C, Dbmaj7, C), coro (Fm, Eb, Db, Eb), interludio, estrofa 2, pre-coro, "Sing with me" (Fm, Eb, Db, Eb, Fm, Eb, Dm7b5, Dbmaj7, C) x2, la subida "Dream on" (Bb, C, Db, Eb, Fm x2; después Bb, C, D, Eb, F, G, Ab, Bb), el clímax Bbm–C, el último coro y el final sobre el arpegio. El bajo dobla las fundamentales y la membrana sigue la raíz y la quinta de cada acorde.

Master: -11.2 LUFS integrados, -1.6 dBTP (igual que YYZ v2), sin clipping.

Referencias de acordes y melodía:
- GuitarTuna, "Dream On chords by Aerosmith (Official Version)": https://guitartuna.com/chords/dream-on-aerosmith-original-guitar-chords-61c0e982773c491a5b7848d0
- Acordes de la partitura (piano/voz/guitarra): https://www.guitaretab.com/a/aerosmith/228.html
- https://guitarx.com/chord/dream-on/

La melodía vocal es una transcripción aproximada para voz principal, hecha sobre esa armonía.

```bash
FILANDRIA=.. python render_dreamon.py   # dreamon_score.json + dream_on_filandria_raw.wav
ffmpeg -i dream_on_filandria_raw.wav -af "volume=3.1dB,alimiter=limit=0.83:level=false:attack=4:release=120:asc=1" -ar 44100 -c:a pcm_s16le dream_on_filandria.wav
./make_video.sh                          # MP4 1920x1080 con background.jpg (c.jpg) y título
```

MP4 y MP3: release [`dreamon-v1`](https://github.com/inodeman/filandria/releases/tag/dreamon-v1).
