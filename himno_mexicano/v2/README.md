# Himno Nacional Mexicano v2: La Filandria cromática

Música de Jaime Nunó (1854), dominio público. Está en **si bemol mayor**, con melodía, armonía (acordes del acompañamiento) y bajo, todo en los hilos cromáticos de vidrio. La membrana se retensa y sigue al bajo. Es **un solo render** de 2:17, sin fundidos entre secciones.

Forma: introducción (la última frase del coro), coro, estrofa I («Ciña ¡oh Patria!…») y coro, con ritardando y calderón al final. Tempo: negra = 84.

Fuente de la transcripción: el MIDI y el PDF de flutetunes.com (`src/`, Jaime Nunó, en do mayor), transportados un tono abajo a si bemol. La melodía se revisó contra la partitura.

```bash
python arrange_v2.py   # escribe himno_v2_score.json y el WAV (necesita mido)
./make_video.sh        # MP4 1920x1080 con thumb.jpg, recortado a la duración del audio
```

WAV y MP4: release [`himno-mexicano-v2`](https://github.com/inodeman/filandria/releases/tag/himno-mexicano-v2).
