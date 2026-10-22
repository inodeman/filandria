#!/usr/bin/env python3
"""Render Beethoven's "Ode to Joy" (9th Symphony, 4th mvt theme, public domain)
on La Filandria using the repo's own engine (filandria.render), unmodified.

The Filandria's nine playable filaments are D3 F3 G3 A3 C4 D4 F4 A4 C5
(a D-minor / F-major pentatonic "tide scale"). Ode to Joy in F major needs
F3 G3 A3 Bb3 C4 -- everything exists except Bb3. Two modes:

  default   : adds ONE extra filament, Bb3, in memory only (repo untouched).
              Same _glass_note/drone/breath/reverb code, just at 230.6 Hz
              (one ET semitone above the instrument's own A3 = 217.70 Hz).
  --strict  : nine original filaments only; every Bb3 is played as A3.

Usage: python render_beethoven.py --repo /workspace/filandria --out x.wav [--strict]
"""
import argparse, json, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default="/workspace/filandria")
ap.add_argument("--out", required=True)
ap.add_argument("--json", default=None)
ap.add_argument("--strict", action="store_true")
ap.add_argument("--beat", type=float, default=0.45)   # seconds per quarter (~133 bpm)
args = ap.parse_args()
sys.path.insert(0, args.repo)
import filandria as fl

if not args.strict:
    fl.SCALE["Bb3"] = round(fl.SCALE["A3"] * 2 ** (1 / 12), 2)  # 230.64 Hz
BB = "A3" if args.strict else "Bb3"

# (note, beats). Theme in F major: F3=1 G3=2 A3=3 Bb3=4 C4=5
A_ = [("A3",1),("A3",1),(BB,1),("C4",1), ("C4",1),(BB,1),("A3",1),("G3",1),
      ("F3",1),("F3",1),("G3",1),("A3",1)]
P1 = A_ + [("A3",1.5),("G3",0.5),("G3",2)]
P2 = A_ + [("G3",1.5),("F3",0.5),("F3",2)]
BR = [("G3",1),("G3",1),("A3",1),("F3",1),
      ("G3",1),("A3",0.5),(BB,0.5),("A3",1),("F3",1),
      ("G3",1),("A3",0.5),(BB,0.5),("A3",1),("G3",1),
      ("F3",1),("G3",1),("C4",2)]   # low C3 isn't on the instrument -> C4
score = P1 + P2 + BR + P2

beat, t, events = args.beat, 0.25, []
for i, (note, beats) in enumerate(score):
    dur = beats * beat
    # phrase-shaped dynamics: gentle downbeat accent, louder bridge peak
    vel = 0.70 + (0.06 if abs((t - 0.25) / beat % 4) < 1e-6 else 0.0)
    if score[i:] and 30 <= i < 47:
        vel += 0.04
    events.append({"note": note, "start": round(t, 4),
                   "bow": round(max(0.08, min(4.0, dur * 0.93 if beats < 2 else dur * 0.97)), 4),
                   "vel": round(min(1.0, vel), 3)})
    t += dur
events[-1]["bow"] = 1.6  # let the final F ring
melody = {"title": "Ode to Joy (Beethoven)", "seconds": 30.0, "seed": 9, "events": events}
print(f"{len(events)} events, theme ends at {t:.2f}s", file=sys.stderr)
if args.json:
    Path(args.json).write_text(json.dumps(melody, indent=2) + "\n")
audio = fl.render(melody)
fl.write_wav(args.out, audio)
print(f"wrote {args.out} {audio.shape[0] / fl.SR:.3f}s")
