#!/usr/bin/env python3
"""Dream On (Aerosmith — Steven Tyler, "Aerosmith" 1973), instrumental cover for
La Filandria, chromatic mode (F1..F6, A440, 70-string original design (pre-5646d73 filandria.py)). One continuous render
with the low-noise engine (render_v2_engine.py). Key F minor, 92 BPM.
Chords: GuitarTuna "Dream On (Official Version)" + guitaretab.com/a/aerosmith/228.html (sheet-music chords)
+ guitarx.com/chord/dream-on. Intro = Fm with chromatic descending line F-E-Eb-D (Fm, Fm/E, Fm/Eb, Fm/D), Db, C.
Bass doubles the roots (folded into F1..E2); the membrane follows the harmony (root + fifth)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.environ.get("FILANDRIA", os.path.dirname(HERE)))
import filandria as F
QPM = 92.0; Q = 60.0 / QPM; M = F.note_to_midi
NAMES = "C C# D D# E F F# G G# A A# B".split()
def nm(m): return f"{NAMES[m % 12]}{m // 12 - 1}"
# chord: (bass/line note, upper voices, root for bass+membrane, fifth interval)
CH = {
 "Fm":   ("F3", ["G#3", "C4", "F4"], "F", 7),  "Fm/E": ("E3", ["G#3", "C4", "F4"], "F", 7),
 "Fm/Eb":("D#3", ["G#3", "C4", "F4"], "F", 7), "Fm/D": ("D3", ["G#3", "C4", "F4"], "F", 7),
 "Db":   ("C#3", ["F3", "G#3", "C4"], "C#", 7), "Dbmaj7": ("C#3", ["F3", "G#3", "C4"], "C#", 7),
 "C":    ("C3", ["E3", "G3", "C4"], "C", 7),    "Csus": ("C3", ["F3", "G3", "C4"], "C", 7),
 "Bb7":  ("A#2", ["D3", "G#3", "D4"], "A#", 7), "Eb7": ("D#3", ["G3", "C#4", "G4"], "D#", 7),
 "Edim7":("E3", ["A#3", "C#4", "G4"], "E", 6),  "Eb": ("D#3", ["G3", "A#3", "D#4"], "D#", 7),
 "Dm7b5":("D3", ["G#3", "C4", "F4"], "D", 6),   "Bbm": ("A#2", ["F3", "A#3", "C#4"], "A#", 7),
 "Bb":   ("A#2", ["F3", "A#3", "D4"], "A#", 7), "D": ("D3", ["F#3", "A3", "D4"], "D", 7),
 "F":    ("F3", ["A3", "C4", "F4"], "F", 7),    "G": ("G3", ["B3", "D4", "G4"], "G", 7),
 "Ab":   ("G#3", ["C4", "D#4", "G#4"], "G#", 7),
}
ev = []; drone = []; pos = 0.0
def fold(pc_name): return 29 + (M(pc_name + "2") % 12 - 5) % 12
def chord(name, beats, style="arp", vel=0.6):
    """style arp: eighth-note arpeggio (bass, up, up, up, down...), pad: held chord, power: root+5th+oct."""
    b, up, r, f = CH[name]; bm = M(b); um = [M(u) for u in up]; root = fold(r)
    drone.append((pos, root, f))
    ev.append((pos, beats * 0.97, root, 0.5 * vel / 0.6, "bass"))
    if style == "arp":
        seq = [bm] + um + um[-2::-1] + um[1:]
        for i in range(int(beats * 2)):
            ev.append((pos + i * 0.5, 1.4, seq[i % len(seq)], vel * (1.0 if i % 4 == 0 else 0.82), "clean"))
    elif style == "pad":
        for n in [bm] + um: ev.append((pos, beats * 0.98, n, vel * 0.8, "clean"))
    else:
        rr = root + 12
        for i in range(int(beats)):
            for n in (rr, rr + f, rr + 12): ev.append((pos + i, 0.95, n, vel, "dist"))
def adv(beats):
    global pos; pos += beats
def mel(s, start, vel=0.85):
    """'C5:1 Ab4:.5 r:.5 ...' durations in beats, starting at beat offset start (absolute)."""
    t = start
    for tok in s.split():
        n, d = tok.split(":"); d = float(d)
        if n != "r": ev.append((t, d, M(n.replace("b", "#") if False else conv(n)), vel, "lead"))
        t += d
def conv(n):  # flats -> sharps
    fl = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    return fl.get(n[:2], n[:-1]) + n[-1] if n[:2] in fl else n
def prog(names, beats=2, style="arp", vel=0.6):
    for c in names: chord(c, beats, style, vel); adv(beats)

INTRO = ["Fm", "Fm/E", "Fm/Eb", "Fm/D", "Db", "Db", "Csus", "C"]
# ---------------- Intro (2 bars per chord-pair) + Bb7 Eb7 Edim7 Fm turnaround
prog(INTRO, 2, vel=0.5); prog(INTRO, 2, vel=0.56)
prog(["Bb7", "Eb7", "Edim7", "Fm"], 2, vel=0.56)
def verse(vel, lyr):
    s = pos
    prog(["Fm", "Fm/E", "Fm/Eb", "Fm/D"] * 4, 2, vel=vel)
    mel(lyr, s)
V1 = ("r:1 C5:.5 C5:.5 C5:.5 Ab4:.5 Bb4:.5 C5:.5 C5:1 Bb4:.5 Ab4:.5 G4:1 F4:1 "
      "r:1 C5:.5 C5:.5 C5:.5 Ab4:.5 Bb4:.5 C5:.5 C5:1 Bb4:.5 Ab4:.5 G4:1 F4:1 "
      "r:2 C5:1 Db5:1 C5:2 Bb4:1 Ab4:1 G4:4 "
      "r:1 C5:.5 C5:.5 Db5:1 C5:1 Bb4:1 Ab4:1 G4:1 F4:5")
def pre(vel):
    s = pos
    prog(["Dm7b5", "Dm7b5", "Csus", "C", "Dm7b5", "Dm7b5", "Dbmaj7", "Dbmaj7", "C", "C"], 2, vel=vel)
    mel("r:1 F4:.5 Ab4:.5 C5:2 Bb4:1 C5:1 C5:2 r:1 F4:.5 Ab4:.5 C5:1 C5:1 Db5:1 C5:1 Bb4:1 Ab4:1 G4:6 E4:2", s)
def chorus1(vel):
    s = pos
    prog(["Fm", "Eb", "Db", "Eb"] * 2, 2, vel=vel)
    mel("C5:1 Ab4:1 Bb4:1 G4:1 Ab4:.5 F4:.5 Ab4:.5 Bb4:.5 Bb4:1 G4:1 "
        "C5:1 Ab4:1 Bb4:1 G4:1 Ab4:.5 F4:.5 Ab4:.5 Bb4:.5 G4:2", s)
def sing(vel, style="arp"):
    s = pos
    prog(["Fm", "Eb", "Db", "Eb", "Fm", "Eb", "Dm7b5", "Dbmaj7", "C"], 4, style, vel=vel)
    mel("F5:1 Eb5:1 C5:2 Eb5:1 C5:1 Bb4:1 Ab4:1 F5:1 Eb5:1 C5:1 Bb4:1 C5:1 Bb4:1 Ab4:2 "
        "F5:1 Eb5:1 C5:2 Eb5:1 C5:1 Bb4:2 Ab4:1 C5:1 F5:1 Eb5:1 Db5:2 C5:1 Bb4:1 C5:8", s, 0.9)

verse(0.5, V1); pre(0.56); chorus1(0.6)
chord("Fm", 8, "pad", 0.45); mel("F4:8", pos, 0.6); adv(8)

VEL = {"lead": 1.0, "bass": 0.6, "dist": 0.62, "clean": 0.8}
events = []
for q, d, m, v, voice in ev:
    while m > 89: m -= 12
    while m < 29: m += 12
    e = {"note": nm(m), "start": round(1.0 + q * Q, 4), "bow": round(max(0.08, min(30, d * Q * 0.94)), 4),
         "vel": round(max(0.05, min(1, v * VEL[voice])), 3)}
    if voice not in ("lead", "clean"): e["breath"] = False
    events.append(e)
dr = [{"start": round(1.0 + q * Q, 4), "root": nm(r), "fifth": nm(r + f)} for q, r, f in drone]
total = 1.0 + pos * Q + 2.0
score = {"title": "Dream On (Aerosmith) — La Filandria cromática", "tuning": "cromatica", "seed": 1973,
         "gain": 0.4, "drone": dr, "drone_level": 0.2, "seconds": round(total, 3), "events": events}
json.dump(score, open(os.path.join(HERE, "dreamon_score.json"), "w"), indent=0)
print(len(events), "events", round(total, 2), "s", file=sys.stderr)
import render_v2_engine as E
F.write_wav(os.path.join(HERE, "dream_on_70_raw.wav"), E.render(score))
