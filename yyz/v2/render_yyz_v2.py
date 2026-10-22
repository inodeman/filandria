#!/usr/bin/env python3
"""YYZ (Rush — Lee/Peart, Moving Pictures 1981), instrumental cover for
La Filandria, chromatic mode (F1..F6, A440). One single render.

Reference transcription: C. D. Bruce, "Rush: YYZ" guitar tab rev. 04 (2002),
chords-and-tabs.net/song/name/rush-yyz-4 (copy in ref/), cross-checked with the
BassCamera bass tab (intro C/F# tritone in 10/8).  Real pitches (guitar sounds
as written in tab; bass doubles an octave lower like Geddy).
Form: Morse intro (10/8) | run | main riff x2 | theme | B7/C7 chord section |
B5/C5 | solo descent (B Spanish Phrygian) | slow section | main riff | theme | ending.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("FILANDRIA", os.path.join(HERE, "..", "..")))
import filandria as F

QPM = 140.0
Q = 60.0 / QPM
M = F.note_to_midi
NAMES = "C C# D D# E F F# G G# A A# B".split()
def nm(m): return f"{NAMES[m % 12]}{m // 12 - 1}"

ev = []        # (q_start, q_dur, midi, vel, voice)
drone = []     # (q_start, root, fifth)
pos = 0.0      # current bar start in quarters

def add(q, d, n, v, voice):
    ev.append((pos + q, d, M(n) if isinstance(n, str) else n, v, voice))

def seq(notes, v, voice="lead", t=0, start=0.0, bass=False, bv=0.5):
    """notes: list of (name|None, dur_q). Sequential."""
    q = start
    for n, d in notes:
        if n is not None:
            m = M(n) + t
            add(q, d, m, v, voice)
            if bass:
                b = m - 12
                while b < 29: b += 12
                add(q, d, b, bv, "bass")
        q += d
    return q

def bar(length=4.0):
    global pos
    pos += length

def set_drone(root, fifth=None):
    r = M(root); drone.append((pos, nm(r), nm(r + 7 if fifth is None else M(fifth))))

def chord(names, q, d, v, t=0):
    for n in names: add(q, d, M(n) + t, v, "chord")

# ---------------------------------------------------------------- INTRO 10/8
# Morse Y Y Z = -.-- -.-- --..  over two 10/8 bars (q = dash, e = dot)
MORSE = [(2, "-"), (1, "."), (2, "-"), (2, "-"), (2, "-"), (1, "."),      # bar 1 (10 eighths)
         (2, "-"), (2, "-"), (2, "-"), (2, "-"), (1, "."), (1, ".")]      # bar 2
def morse_cycle(crot_v, guitar_v=None):
    global pos
    q = 0.0
    for eighths, s in MORSE:
        d = eighths / 2
        add(q, min(d, 0.5), "C6", crot_v, "crot")              # crotale
        if guitar_v:
            n = "C3" if s == "-" else "F#2"                     # tab: A3 / E2 frets
            add(q, d * 0.95, n, guitar_v, "lead")
            add(q, d * 0.95, M(n) - 12, guitar_v * 0.7, "bass")
        q += d
    pos += 10.0   # two bars of 10/8 = 10 quarters
set_drone("F#1", "C2")                                          # the tritone of the intro
for v in (0.35, 0.45): morse_cycle(v)
for v in (0.55, 0.62, 0.68, 0.72, 0.76, 0.80): morse_cycle(0.30, v)

# ------------------------------------------------------- RUN into the riff
set_drone("B1")
chord(["F#3", "B3"], 0, 2, 0.8); chord(["B1"], 0, 2, 0.6); bar(2)
run = [("C3", 1/6), ("C3", 1/6), ("C#3", 1/6)] + [(n, .25) for n in
      ["D#3", "E3", "F#3", "G#3", "A3", "B3", "C#4", "D#4", "E4", "D#4", "C#4"]] + [("C4", .75)]
seq(run, 0.85, bass=True); bar()
add(0, 2, "C4", 0.8, "lead")
seq([("B3", .25), ("C4", .25), ("B3", .25), ("G3", .25), ("F#3", 1)], 0.82, start=2.0, bass=True); bar()
seq([("D4", .25), ("D4", .25), ("D4", .5), ("C4", .25), ("D4", .25), ("C4", .25), ("B3", .25),
     ("A3", .25), ("G3", .25), ("F#3", 1.0), ("F#3", .5)], 0.85, bass=True); bar()

# ------------------------------------------------------------- MAIN RIFF
R1  = [("A3", .25), ("A3", .25), ("F#3", .25), ("A3", .25), ("F#3", .25), ("F3", .25), ("E3", .5), ("C#3", 2)]
R2  = [("A3", .25), ("A3", .25), ("F#3", .25), ("A3", .25), ("F#3", .25), ("E3", .25), ("C#3", .5),
       ("B2", .75), ("C#3", .75), ("F#2", .5)]
R2b = [("A3", .25), ("A3", .25), ("F#3", .25), ("A3", .25), ("F#3", .25), ("E3", .25), ("C#3", .25), ("C3", .25),
       ("B2", .75), ("C#3", .75), ("F#2", .5)]
END1 = [("C4", .25), ("C4", .25), ("A3", .25), ("C4", .25), ("A3", .25), ("G3", .25), ("E3", .5),
        ("G3", .25), ("G3", .25), ("E3", .25), ("G3", .5), ("G3", .25), ("E3", .5)]
END2 = [("C4", .25), ("C4", .25), ("A3", .25), ("C4", .25), ("A3", .25), ("G3", .25), ("E3", .5),
        ("G3", .25), ("G3", .25), ("E3", .25), ("G3", .5), ("E3", .75)]
def riff_bar(notes, t=0, v=0.82):
    set_drone("A1" if t == 3 else "F#1", "E2" if t == 3 else "C#2")
    seq(notes, v, t=t, bass=True, bv=0.55); bar()
def riff_block(last, v=0.82):
    for a, b, t in ((R1, R2, 0), (R1, R2b, 0), (R1, R2b, 3)):
        riff_bar(a, t, v); riff_bar(b, t, v)
    riff_bar(R1, 3, v)
    if last is None: riff_bar(R2b, 3, v)
    else:
        set_drone("A1", "E2"); seq(last, v, bass=True, bv=0.55); bar()
riff_block(END1, 0.80)
riff_block(None, 0.86)

# ----------------------------------------------------------------- THEME
T1 = [("D#4", .75), ("E4", .75), ("F#4", .5), ("A3", 2.5)]
T2 = [("D#4", .5), ("E4", .5), ("F#4", .5), ("G#4", 1), ("F#4", 1)]
T3 = [("D#4", .75), ("E4", .75), ("F#4", .5), ("A3", .25), ("A3", .25), ("A3", .25), ("A3", .25), ("A3", .25), ("B3", 1.25)]
T5 = [("C4", .75), ("D4", .5), ("E4", .5), ("D4", .25), ("E4", .25), ("D4", .25), ("E4", .25), ("G4", 1.25)]
T6 = [(None, .5), ("C4", .75), ("D4", .25), ("E4", .5), ("D4", .25), ("E4", .25), ("D4", .25), ("G4", .25),
      ("E4", .25), ("G4", .25), ("E4", .5)]
def pulse(root, v=0.42):
    r = M(root)
    for i in range(8):
        add(i * .5, .42, r + (12 if i % 4 == 2 else 0), v, "bass")
def theme_bars(bars, v=0.9):
    """bars: list of (notes, start_offset, root). Notes may spill over the barline."""
    for notes, off, root in bars:
        set_drone(root); pulse(root)
        seq(notes, v, start=off); bar()
def theme(v=0.9, final=False):
    B = [(T1, 0, "B1"), (T2, 0.5, "B1"), (T3, 0, "B1"), (T2, 0.5, "B1"),
         (T5, 0, "C2"), (T6, 0, "C2"), (T5, 0, "C2"), (T6, 0, "C2")]
    theme_bars(B, v)

theme(0.9)

# -------------------------------------------------------- CHORD SECTION
B7 = ["B2", "F#3", "A3", "D#4", "F#4", "B4"]
C7 = ["C3", "G3", "A#3", "E4", "G4", "C5"]
def stabs(ch, root, onsets, durs, v=0.62):
    set_drone(root)
    for q, d in zip(onsets, durs):
        chord(ch, q, d, v); add(q, d, root, 0.55, "bass")
    bar()
def fill(root_seq, v=0.6):
    seq([(n, .5) for n in root_seq], v, voice="bass"); bar()
P1 = ([0, .75, 1.5, 2.5, 3.5], [.7, .7, .95, .95, .5])
for _ in range(2):
    stabs(B7, "B1", *P1); stabs(B7, "B1", *P1); stabs(C7, "C2", *P1)
    chord(C7, 0, .5, .62); fill(["C2", "C2", "E2", "G2", "A#2", "C3", "A#2", "G2"][1:] + ["F#2"])
for ch, root in ((B7, "B1"), (B7, "B1"), (C7, "C2")):     # chord + arpeggio
    set_drone(root)
    chord(ch, 0, .45, .62); chord(ch, .5, .45, .62); add(0, 2, root, .55, "bass")
    seq([(ch[0], .5), (ch[1], .5), (ch[2], 1)], .6, voice="chord", start=2.0); bar()
chord(C7, 0, .5, .62); fill(["C2", "D2", "E2", "F#2", "G2", "A2", "B2", "A#2"])
for ch, root in ((B7, "B1"), (B7, "B1"), (C7, "C2")):     # muted 16ths + two stabs
    set_drone(root)
    for i in range(16):
        if i in (4, 12): chord(ch, i * .25, .45, .66)
        else: add(i * .25, .09, ch[0], .22, "chord"); add(i * .25, .09, ch[1], .18, "chord")
    add(0, 4, root, .5, "bass"); bar()
chord(C7, 0, .5, .62); set_drone("C2"); add(0, 4, "C2", .5, "bass"); bar()
for ch, root in ((B7, "B1"), (B7, "B1"), (C7, "C2"), (C7, "C2")):
    set_drone(root)
    for q in (0, 2): add(q, .7, ch[0], .6, "chord"); add(q, .7, ch[1], .55, "chord"); add(q, .7, root, .55, "bass")
    for q in (.75, 2.75): chord(ch[2:], q, 1.1, .58)
    bar()
chord(C7, 0, .5, .62); fill(["C2", "E2", "G2", "C3", "B2", "A2", "G2", "F#2"])
B5 = ["B2", "F#3", "B3", "D#4", "F#4"]; C5 = ["C3", "G3", "C4", "E4", "G4"]
for ch, root in ((B5, "B1"), (B5, "B1"), (C5, "C2")):
    set_drone(root)
    for q, d in ((0, .7), (.75, .25), (1.0, 2.9)): chord(ch, q, d, .7); add(q, d, root, .55, "bass")
    bar()
chord(C5, 0, .5, .66); fill(["C2", "C2", "D2", "D#2", "E2", "F#2", "G2", "A2"])

# ------------------------------------------------- SOLO descent (B Spanish Phrygian)
set_drone("B1")
desc = []
for a, b in (("A4", "B4"), ("A4", "B4"), ("G4", "A4"), ("G4", "A4"), ("F#4", "G4"), ("E4", "F#4"), ("D#4", "E4"), ("C4", "D#4")):
    desc += [(a, .25), (b, .25), (a, .25), ("B3", .25)]
pulse("B1", .45); seq(desc[:16], .82); bar()
pulse("B1", .45); seq(desc[16:], .82); bar()
add(0, 8, "A4", .7, "lead"); add(0, 8, "B1", .5, "bass"); bar(); bar()   # feedback A
# slow section
SLOW = [[("A3", 3), ("E4", 5)], [], [("E5", 2), ("A4", 1.5), ("C5", 4.5)], [],
        [("E5", 1.5), ("F#5", .5), ("E5", 1.5), ("B4", 4.5)], [], [("A3", 3), ("C4", 5)], [], [("E4", 4)]]
for b in SLOW:
    set_drone("B1"); add(0, 3.95, "B1", .45, "bass"); add(2, 1.9, "F#2", .35, "bass")
    if b: seq(b, .7)
    bar()

# --------------------------------------------------- RETURN: riff + theme
riff_block(END2, 0.84)
riff_block(None, 0.88)
theme(0.92)

# ---------------------------------------------------------------- ENDING
set_drone("F#1", "C2")
chord(["C4", "A#3"], 0, 4, .7); seq([("C3", 1), ("C3", 1), ("F#2", 2)], .8, bass=True); bar()
chord(["C#4", "A#3"], 0, 8, .7); seq([("C3", 1), ("C3", 1), ("C3", 1), ("F#2", 5)], .8, bass=True); bar(); bar()
chord(["C#4", "A#3"], 0, 2, .62); seq([("F#3", .5), ("E3", .5), ("D3", .5), ("F#2", 6)], .8, start=2.0, bass=True)
bar(8)

# ---------------------------------------------------------------- RENDER
VEL = {"lead": 1.0, "bass": 1.0, "chord": 0.75, "crot": 0.9}
events = []
for q, d, m, v, voice in ev:
    while m > 89: m -= 12
    while m < 29: m += 12
    e = {"note": nm(m), "start": round(1.0 + q * Q, 4),
         "bow": round(max(0.08, min(30, d * Q * (0.92 if voice == "lead" else 0.96))), 4),
         "vel": round(max(0.05, min(1.0, v * VEL[voice])), 3)}
    if voice != "lead": e["breath"] = False
    events.append(e)
dr = [{"start": round(1.0 + q * Q, 4), "root": r, "fifth": f} for q, r, f in drone]
total = 1.0 + pos * Q + 1.5
score = {"title": "YYZ (Rush) — La Filandria cromática", "tuning": "cromatica", "seed": 1981,
         "gain": 0.36, "drone": dr, "drone_level": 0.5, "seconds": round(total, 3), "events": events}
json.dump(score, open(os.path.join(HERE, "yyz_v2_score.json"), "w"), indent=0)
print(len(events), "events", round(total, 2), "s", file=sys.stderr)
audio = F.render(score)
F.write_wav(os.path.join(HERE, "yyz_v2.wav"), audio)
