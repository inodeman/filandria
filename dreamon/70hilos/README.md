# Dream On (muestra 78.7 s): Filandria de 70 cuerdas (diseño original)

Intro + estrofa 1 + pre-coro + primer coro, con `filandria.py` de 8f7e2ef (antes del rediseño de 12 filamentos), guardado aquí como `filandria_70hilos.py`.
El diff 8f7e2ef→5646d73 en `filandria.py` sólo cambia el docstring: el sonido es idéntico al de la versión de 12 filamentos.
Imagen: `filandria.jpg` (la misma en todo el historial). Master: -12.0 LUFS, -1.6 dBTP.

    mkdir old && git show 8f7e2ef:filandria.py > old/filandria.py && FILANDRIA=old python render_dreamon70.py
