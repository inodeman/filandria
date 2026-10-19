# La Filandria

Instrumento inventado: nueve hilos de vidrio, una membrana ahumada y una hendidura en madera de olivo. Se toca con un arco de crin guardado en cobre.

La escala de marea no es temperamento igual. Solo se pueden frotar estos nueve hilos:

| Nota | Hz |
|---|---|
| D3 | 146.15 |
| F3 | 173.35 |
| G3 | 194.55 |
| A3 | 217.70 |
| C4 | 258.20 |
| D4 | 291.55 |
| F4 | 345.85 |
| A4 | 434.05 |
| C5 | 514.55 |

D2 (73.08 Hz) y A2 (109.15 Hz) son el zumbido de la membrana. No son notas.

## Videos

| Archivo | Qué es |
|---|---|
| [filandria-marea-corta.mp4](filandria-marea-corta.mp4) | El instrumento, con la frase *Marea corta* |
| [filandria-la-mano.mp4](filandria-la-mano.mp4) | Alguien tocándolo. La frase es *La mano* (semilla 7) |
| [marea-corta.mp3](marea-corta.mp3) | Audio de *Marea corta* |
| [la-mano.mp3](la-mano.mp3) | Audio de *La mano* |

## Para otro bot

Todo el instrumento está en [`filandria.py`](filandria.py). Hace falta Python 3 y `numpy` (`pip install -r requirements.txt`).

Componer una frase nueva y grabarla:

```bash
python filandria.py compose --seconds 10 --seed 7 --title "La mano" --json la-mano.json --out la-mano.wav
```

La misma semilla produce la misma frase. Otra semilla, otra melodía.

Tocar una melodía ya escrita:

```bash
python filandria.py play marea-corta.json --out marea-corta.wav
```

Desde Python:

```python
import filandria

melody = filandria.compose(seconds=10, seed=21, title="Otra")
audio = filandria.render(melody)          # float64, forma (frames, 2), 48000 Hz
filandria.write_wav("otra.wav", audio)
```

Para imponer una melodía, pasa este objeto a `filandria.render` o a `play`:

```json
{
  "title": "La mano",
  "seconds": 10,
  "seed": 7,
  "events": [
    {"note": "A4", "start": 0.2, "bow": 0.6, "vel": 0.8}
  ]
}
```

- `note`: una de las nueve notas de la tabla.
- `start`: segundos desde el inicio. `>= 0` y menor que `seconds`.
- `bow`: segundos que el arco permanece en ese hilo. Entre 0.08 y 4.
- `vel`: fuerza del arco, entre 0.05 y 1.
- `seconds`: entre 4 y 60.
- `seed`: entero. Solo cambia el roce del arco; la misma semilla es la misma toma.
- `events`: de 1 a 64. El orden no importa.

Si el JSON no cumple el contrato, el programa termina con código 2 y escribe `error: ...` en stderr. No genera wav.
