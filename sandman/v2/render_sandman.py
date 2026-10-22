#!/usr/bin/env python3
"""Enter Sandman (Metallica — Hetfield/Ulrich/Hammett, "Metallica" 1991),
instrumental cover for La Filandria, chromatic mode (F1..F6, A440). One render. v2: low-noise engine (render_v2_engine.py).

Reference: Paddy McMullan, "Metallica - Enter Sandman" guitar tab v1.0 (2014),
pmtabs.net (copy in ref/pm.txt), cross-checked against the TabsBase/GuitarTwitt
intro tabs.  Real pitches (standard tuning, E2 = low E). Tempo 123 BPM.
Bass doubles the roots folded into F1..E2; the membrane follows the bar's root.
"""
import json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ.get("FILANDRIA", "/workspace/filandria"))
import filandria as F

QPM = 123.0; Q = 60.0 / QPM
M = F.note_to_midi
NAMES = "C C# D D# E F F# G G# A A# B".split()
def nm(m): return f"{NAMES[m % 12]}{m // 12 - 1}"
POWER = {"pE": "E2", "pF": "F2", "pF#": "F#2", "pG": "G2", "pA": "A2", "pBb": "A#2", "pB": "B2", "pC": "C3"}

ev = []; drone = []; pos = 0.0
def bass_of(m):
    pc = m % 12
    return 29 + (pc - 5) % 12          # fold into F1..E2

def notes_of(tok):
    if tok in POWER:
        r = M(POWER[tok]); return [r, r + 7]
    if isinstance(tok, tuple): return [M(t) for t in tok]
    return [M(tok)]

def play(tokens, voice="dist", vel=0.8, pm=(), ring=1.0, bass=True, t=0, start=0.0, length=4.0):
    """tokens: list over the bar (8 = eighths, 16 = sixteenths). None = hold/rest.
    pm: indices that are palm-muted (short, softer)."""
    slot = length / len(tokens)
    on = [i for i, x in enumerate(tokens) if x is not None and x != "-"]
    for k, i in enumerate(on):
        nxt = on[k + 1] if k + 1 < len(on) else len(tokens)
        d = (nxt - i) * slot
        tok = tokens[i]; ns = [n + t for n in notes_of(tok)]
        muted = i in pm
        dd = d * (0.45 if muted else ring)
        vv = vel * (0.7 if muted else 1.0)
        for n in ns:
            ev.append((pos + start + i * slot, dd, n, vv, voice))
        if bass and voice != "lead":
            ev.append((pos + start + i * slot, d * (0.5 if muted else 0.97), bass_of(min(ns)), 0.55 * (0.8 if muted else 1), "bass"))

def bar(root=None, fifth=7, n=1):
    global pos
    if root: drone.append((pos, M(root), fifth))
    pos += 4.0 * n

ALL = range(16)
# ------------------------------------------------------------- figures (8 slots)
INTRO = ["E2", "E3", "G3", "A#2", "A2", None, "E3", "E2"]
DIST_A = ["pE", "E2", "E2", "E2", "E2", "E2", "E2", "E3"]
DIST_B = ["E2", "E2", "E3", "A#2", "E2", "E2", "E2", "pF"]
DIST_C = ["E2", "E2", "E3", "A#2", "A2", "E2", "E2", "pF"]
DIST_D = ["E2", "E2", "E3", "A#2", "A2", "E2", "E2", "pE"]
RIFF   = ["pE", "E2", "E3", "A#2", "A2", None, "E2", "pE"]
RIFF_G = ["pE", "E2", "E3", "A#2", "A2", None, ("E2", "A2"), "pG"]
TURN   = ["pG", "E2", "pF#", "E2", "pF#", "pG", "pF#", "pE"]
VERSE  = ["pE", "pE", "pE", "pE", "pE", "pE", "pE", "pF"]
VERSE_G = ["pE", "pE", "pE", "pE", "pE", "pE", "pE", "pG"]
ARP    = ["F#2", "F#3", "A3", "C3", "B2", None, "F#3", "F#2"]
CH_A   = ["pF#", None, None, "pC", "pB", None, None, "pF#"]
CH_E   = ["pF#", None, None, "pC", "pB", None, None, "pE"]
CH_TURN = ["pG", "E2", "pF#", "E2", "pF#", "pG", None, "pE"]

def intro_clean(nbars, vel=0.62):
    for _ in range(nbars):
        play(INTRO, "clean", vel, ring=2.2, bass=False); bar("E2")

def riff_block(vel=0.84, end_turn=True):
    for b in (RIFF, RIFF, RIFF, RIFF_G):
        play(b, "dist", vel, pm=(1,)); bar("E2")
    play(TURN, "dist", vel, pm=(1, 3)); bar("G1")
    for b in (RIFF, RIFF, RIFF_G):
        play(b, "dist", vel, pm=(1,)); bar("E2")
    play(TURN, "dist", vel, pm=(1, 3)); bar("G1")

def verse(vel=0.82):
    for _ in range(2):
        play(VERSE, "dist", vel, pm=range(1, 7)); bar("E2")
        play(VERSE, "dist", vel, pm=range(1, 7)); bar("E2")
        play(VERSE_G, "dist", vel, pm=range(1, 7)); bar("E2")
        play(TURN, "dist", vel, pm=(1, 3)); bar("G1")

def prechorus(vel=0.6):
    for _ in range(4):
        play(ARP, "clean", vel, ring=2.0, bass=False)
        ev.append((pos, 3.9, bass_of(M("F#2")), 0.45, "bass")); bar("F#1", 6)
    play(TURN, "dist", 0.84, pm=(1, 3)); bar("G1")
    for _ in range(4):
        play(ARP, "dist", 0.78, ring=1.6); bar("F#1", 6)

FILL1 = [None, "E4", "G4", "E4", "A4", "E4", "B4", "G4"]
FILL2 = ["F#4", None, None, None, None, None, None, None]
FILL3 = [None, "E4", "F#4", "E4", "G4", "E4", "A4", "E4"]
def chorus(vel=0.88, fills=True, last=None):
    seq = [(CH_A, "F#1"), (CH_A, "F#1"), (CH_E, "F#1"), (["pE"] + [None] * 7, "E2"),
           (CH_E, "F#1"), (["pE"] + [None] * 7, "E2"), (CH_TURN, "G1"), (last or ["pE"] + [None] * 6 + ["pE"], "E2")]
    for i, (b, r) in enumerate(seq):
        play(b, "dist", vel)
        if fills and i == 3: play(FILL1, "lead", 0.8)
        if fills and i == 4: play(FILL2, "lead", 0.75)
        if fills and i == 5: play(FILL3, "lead", 0.8)
        bar(r, 7)

# ------------------------------------------------------------------- SONG
# Intro 1: clean riff (x8), wah rake enters on the last 4
intro_clean(4, 0.55)
for i in range(4):
    play(INTRO, "clean", 0.62, ring=2.2, bass=False)
    play([("E4", "B3", "G3", "E3")] + [None] * 7, "lead", 0.4)
    bar("E2")
# Intro 2: palm-muted build, second guitar adds Bb5/A5 hits
for _ in range(4): play(DIST_A, "dist", 0.78, pm=range(1, 7)); bar("E2")
for _ in range(4): play(DIST_B, "dist", 0.8, pm=(0, 1, 4, 5, 6)); bar("E2")
for i in range(7):
    play(DIST_C, "dist", 0.82, pm=(0, 1, 5, 6))
    play(["pE", None, None, "pBb", "pA", None, None, "pE"], "dist", 0.55, bass=False); bar("E2")
play(DIST_D, "dist", 0.85, pm=(0, 1, 5, 6)); bar("E2")
# Intro 3 / main riff
riff_block(0.86)
verse(0.82)
prechorus()
chorus(0.88)
riff_block(0.86)                       # post-chorus
verse(0.84)
prechorus()
chorus(0.9)

# Solo (condensed) over riff / arpeggio / chorus backing
S = [
 [None] * 6 + ["B4", "D5"],
 ["D5", "B4", "D5", None, "B4", "A4", "B4", "D5"],
 ["D5", "B4", "A4", None, "E5", None, "E5", "B3"],
 [("A4", "D4")] * 3 + [("G4", "C4")] * 3 + [("A4", "D4")] * 2,
 ["A4", "G4", "E4", "E4", "D4", "B3", "B3", "A3", "G3", "E3", None, None, "B3", "B4", "E5", None],
 ["D5", "E5"] * 4,
 ["D5", "E5", "E5", "A#4", "E5", "G5", "E5", "A#4", "E5", "G5", "E5", "E5", "A#4", "E5", "G5", "E5"],
 ["A5", "F#5", "D5", "A5", "F#5", "D5", "A5", "F#5", "B5", "G5", "E5", "B5", "G5", "E5", "B5", "G5"],
 ["C#6", "A5", "E4", "C#6", "A5", "E4", "E4", "C#6", "A5", "E4", "E6", None, None, None, None, None],
 [("A#4", "F#4"), None, ("A#4", "F#4"), None, ("A#4", "F#4"), None, ("A#4", "F#4"), None],
 ["A4", "A4", "G4", "F#4", "E4", "F#4", "G4", "F#4", "E4", "F#4", "E4", "D4", "E4", "D4", "B3", None],
 ["C#6", "A5", "E4", "E4", "C#6", "C#6", "A5", "E4", "E4", "C#6", "A5", "E4", "E4", "C#6", "C#6", "A5"],
 ["E6", None, None, None, "E6", "E6", "D6", None, "E6", None, None, None, None, None, None, None],
 ["A4", "G4", "F#4", "E4", None, "E4", "D4", None, "B3", None, "B3", "A3", "G3", None, "B3", None],
 ["G3", "E3", None, None, None, None, None, None, "D3", "E3", "D3", None, "B2", None, None, None],
 ["E3"] + [None] * 7,
]
backing = [RIFF, RIFF, RIFF, RIFF_G, TURN, RIFF, RIFF_G, TURN, ARP, ARP, ARP, ARP]
broots = ["E2", "E2", "E2", "E2", "G1", "E2", "E2", "G1", "F#1", "F#1", "F#1", "F#1"]
for i, (b, r) in enumerate(zip(backing, broots)):
    play(b, "dist", 0.74, pm=(1,) if b is not TURN else (1, 3), ring=1.4 if b is ARP else 1.0)
    play(S[i], "lead", 0.86); bar(r, 6 if r == "F#1" else 7)
for i, b in enumerate([CH_A, CH_A, CH_E, ["pE"] + [None] * 7]):
    play(b, "dist", 0.76); play(S[12 + i], "lead", 0.86); bar("F#1" if i < 3 else "E2")

# Break: soft clean intro, quiet arpeggios, then distorted arpeggios
intro_clean(4, 0.5)
for _ in range(6):
    play(ARP, "clean", 0.45, ring=2.0, bass=False)
    ev.append((pos, 3.9, bass_of(M("F#2")), 0.35, "bass")); bar("F#1", 6)
for _ in range(4):
    play(ARP, "dist", 0.8, ring=1.6); bar("F#1", 6)

# Chorus 3 + riff
chorus(0.92, last=["pE"] + [None] * 7)
play(TURN, "dist", 0.9, pm=(1, 3)); bar("G1")
play(["pE"] + [None] * 7, "dist", 0.85); bar("E2")
for b in (RIFF, RIFF, RIFF, TURN):
    play(b, "dist", 0.88, pm=(1,) if b is RIFF else (1, 3)); bar("E2" if b is RIFF else "G1")

# Outro: clean riff, then palm-muted build with lead fills, fading
intro_clean(2, 0.55)
O = [
 [None] * 4 + [("G4", "E4"), ("F#4", "D4"), "G4", ("E4", "A3")],
 ["D4", "E4", "D4", "B3", "A3", "F#3", ("D4", "A3"), ("E4", "B3")],
 [("E4", "B3")] + [None] * 7,
 [("E4", "B3")] + [None] * 7,
 [None] * 4 + ["G4", "E4", "G4", ("E4", "D4")],
 ["D4", "E4", "D4", "B3", "D4", "B3", "G3", "A3"],
 [("D4", "D3")] + [None] * 6 + ["D4"],
 ["A4", "G4", "D4", "A4", "G4", "D4", "A4", ("B4", "F#4", "D4")],
 [("B4", "F#4"), None, ("E5", "B4"), None, ("D5", "A4"), None, None, None],
 [("D5", "A4")] + [None] * 7,
]
OUT_A = ["pE", "E2", "E3", "A#2", "A2", "E2", "E2", "pF"]
OUT_B = ["E2", "E2", "E3", "A#2", "E2", "E2", "E2", "pF"]
OUT_C = ["E2", "E2", "E3", "E2", "E2", "E2", "E2", "E2"]
plan = [OUT_A] * 4 + [OUT_B] * 4 + [OUT_C] * 4
for i, b in enumerate(plan):
    v = 0.84 if i < 8 else 0.84 - 0.1 * (i - 7)
    play(b, "dist", v, pm=(1, 5, 6) if b is not OUT_C else (0, 1, 3, 4, 5, 6, 7))
    if i >= 2 and i - 2 < len(O): play(O[i - 2], "lead", 0.8 if i < 9 else 0.65)
    bar("E2")
play(["pE"] + [None] * 7, "dist", 0.7, ring=2.0); bar("E2", n=2)

# ------------------------------------------------------------------ RENDER
VEL = {"lead": 1.0, "bass": 0.6, "dist": 0.78, "clean": 0.95}  # v2: lighter bass/low chords
events = []
for q, d, m, v, voice in ev:
    while m > 89: m -= 12
    while m < 29: m += 12
    e = {"note": nm(m), "start": round(1.0 + q * Q, 4),
         "bow": round(max(0.08, min(30, d * Q * 0.94)), 4), "vel": round(max(0.05, min(1, v * VEL[voice])), 3)}
    if voice not in ("lead", "clean"): e["breath"] = False
    events.append(e)
dr = []
for q, r, f in drone:
    rr = bass_of(r)
    dr.append({"start": round(1.0 + q * Q, 4), "root": nm(rr), "fifth": nm(rr + f)})
total = 1.0 + pos * Q + 1.0
score = {"title": "Enter Sandman (Metallica) — La Filandria cromática", "tuning": "cromatica", "seed": 1991,
         "gain": 0.4, "drone": dr, "drone_level": 0.2, "seconds": round(total, 3), "events": events}
json.dump(score, open(os.path.join(HERE, "v2", "sandman_score.json"), "w"), indent=0)
print(len(events), "events", round(total, 2), "s", file=sys.stderr)
import render_v2_engine as E
F.write_wav(os.path.join(HERE, "v2", "enter_sandman_filandria.wav"), E.render(score))
