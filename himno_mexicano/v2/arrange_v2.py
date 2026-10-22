#!/usr/bin/env python3
"""Himno Nacional Mexicano (Jaime Nunó, 1854, public domain) on La Filandria,
chromatic filaments, B-flat major, one single render.
Source: flutetunes.com MIDI 'national-anthem-of-mexico.mid' (melody + piano,
C major) — transposed down a whole tone to the standard B-flat.
Form: intro (last chorus phrase) | chorus | stanza I | chorus, ritardando + fermata."""
import json, os, sys
import mido
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("FILANDRIA", os.path.join(HERE, "..", "..")))
import filandria as F

SRC = os.path.join(HERE, "src", "national-anthem-of-mexico.mid")
QPM, QPM_END = 84, 66
TRANS = -2
mid = mido.MidiFile(SRC); TPB = mid.ticks_per_beat; BAR = 4 * TPB
NAMES = "C Db D Eb E F Gb G Ab A Bb B".split()
def name(m): return f"{NAMES[m % 12]}{m // 12 - 1}"

def notes(track):
    t = 0; on = {}; out = []
    for x in track:
        t += x.time
        if x.type == "note_on" and x.velocity > 0: on[x.note] = (t, x.velocity)
        elif x.type in ("note_off", "note_on") and x.note in on:
            s, v = on.pop(x.note); out.append([s, t - s, x.note, v])
    return sorted(out)
mel, up, down = (notes(mid.tracks[i]) for i in (1, 2, 3))
MAIN0 = 3 * TPB; END = 42 * BAR + TPB
INTRO = (8 * BAR + 3 * TPB, 12 * BAR + TPB)
GAP = 2 * TPB

# score time (beats) -> seconds, ritardando over the last 6 beats
LAST = None
def build():
    seq = []  # (beat_start, beat_dur, midi, vel, voice)
    def take(lst, voice, a, b, off):
        for s, d, n, v in lst:
            if a <= s < b:
                seq.append([(s - a) / TPB + off, d / TPB, n + TRANS, v, voice])
    intro_len = (INTRO[1] - INTRO[0]) / TPB
    for lst, vc in ((mel, "mel"), (up, "har"), (down, "bas")):
        take(lst, vc, *INTRO, 0.0)
        take(lst, vc, MAIN0, END, intro_len + GAP / TPB)
    return seq, intro_len
seq, intro_len = build()
total_beats = max(s + d for s, d, *_ in seq)
fin = max(s for s, *_ in seq)
for e in seq:  # final chord: fermata
    if e[0] >= fin - 1e-6: e[1] = 4.0
def sec(b):
    rit0 = fin - 6
    if b <= rit0: return 0.6 + b * 60 / QPM
    # linear tempo change QPM -> QPM_END
    x = min(b, fin) - rit0
    slope = (QPM_END - QPM) / 6
    import math
    t = 0.6 + rit0 * 60 / QPM + 60 * math.log((QPM + slope * x) / QPM) / slope
    if b > fin: t += (b - fin) * 60 / QPM_END
    return t

events = []; drone = []
VEL = {"mel": (0.80, 0.18), "har": (0.30, 0.10), "bas": (0.46, 0.12)}
for s, d, n, v, vc in seq:
    if vc == "bas":
        while n < 34: n += 12   # nothing below B-flat 1
    if vc == "har" and n > 81: n -= 12
    t0, t1 = sec(s), sec(s + d)
    base, span = VEL[vc]
    events.append({"note": name(n), "start": round(t0, 4),
                   "bow": round(min(30, max(0.08, (t1 - t0) * (0.93 if vc == "mel" else 0.97))), 4),
                   "vel": round(min(1, base + span * (v - 64) / 63), 3),
                   **({} if vc == "mel" else {"breath": False})})
# membrane follows the bass on each beat's lowest note
by_beat = {}
for s, d, n, v, vc in seq:
    if vc == "bas": by_beat.setdefault(round(s, 3), []).append(n)
last = None
for b in sorted(by_beat):
    r = min(by_beat[b]) % 12
    if r != last:
        root = 34 + (r - 10) % 12   # Bb1..A2
        drone.append({"start": round(sec(b), 4), "root": name(root), "fifth": name(root + 7)})
        last = r
score = {"title": "Himno Nacional Mexicano (J. Nunó) — La Filandria, Si bemol mayor",
         "tuning": "cromatica", "seed": 1854, "gain": 0.42, "drone": drone, "drone_level": 0.55,
         "seconds": round(sec(total_beats + 4) + 2.5, 3), "events": events}
json.dump(score, open(os.path.join(HERE, "himno_v2_score.json"), "w"), indent=1, ensure_ascii=False)
print(len(events), "events", score["seconds"], "s; melody range",
      min(F.note_to_midi(e["note"]) for e in events), max(F.note_to_midi(e["note"]) for e in events))
audio = F.render(score)
F.write_wav(os.path.join(HERE, "himno_mexicano_filandria_v2.wav"), audio)
print("wav", audio.shape[0] / F.SR)
