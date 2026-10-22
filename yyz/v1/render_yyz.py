#!/usr/bin/env python3
"""YYZ (Rush, Lee/Lifeson/Peart) - instrumental cover arranged for La Filandria's 9 filaments.
Transcribed by ear-memory, transposed into the tide scale (D F G A C). Rendered with filandria.render
in <=64-event chunks, overlap-added."""
import sys, json, numpy as np
sys.path.insert(0, "/workspace/filandria"); import filandria as fl
E = 60/138/2   # eighth note at ~150 bpm quarter
ev=[]; t=1.0
def n(note, eighths, vel=0.75, gap=0.9, dyad=None):
    global t
    bow=max(0.08,min(4.0,eighths*E*gap))
    ev.append((t,note,bow,vel))
    if dyad: ev.append((t,dyad,bow,vel*0.8))
    t+=eighths*E
def rest(e):
    global t; t+=e*E
MORSE={"Y":"-.--","Z":"--.."}
def morse(word, vel, hi="C4", lo="F3"):
    for ch in word:
        for s in MORSE[ch]:
            n(hi if s=="-" else lo, 2 if s=="-" else 1, vel, 0.8, dyad=(lo if s=="-" else None))
        rest(1)
# INTRO: Y Y Z morse, building
for v in (0.45,0.55,0.65,0.75): morse("YYZ", v)
for v in (0.8,0.85): morse("YYZ", v, "D4","A3")
rest(2)
# MAIN RIFF (approx., 1 bar ostinato + answer)
RIFF=[("D3",1),("D3",1),("A3",1),("D3",1),("C4",1),("D3",1),("A3",1),("G3",1),("F3",1),("G3",1)]
ANS =[("D3",1),("D3",1),("A3",1),("D3",1),("D4",2),("C4",1),("A3",1),("G3",2)]
def riff(k,vel=0.8):
    for _ in range(k):
        for x in RIFF: n(*x,vel)
        for x in ANS: n(*x,vel)
riff(4)
# THEME (unison melody)
TH=[("A4",2),("F4",1),("D4",1),("C4",2),("D4",2),("F4",3),("D4",1),("C4",2),("A3",2),
    ("A4",2),("C5",1),("A4",1),("F4",2),("D4",2),("F4",2),("G3",1),("A3",1),("D4",4)]
for _ in range(2):
    for x in TH: n(*x,0.82)
riff(2,0.85)
# BRIDGE: fast runs up/down
RUN=["D3","F3","G3","A3","C4","D4","F4","A4","C5","A4","F4","D4","C4","A3","G3","F3"]
for _ in range(3):
    for x in RUN: n(x,1,0.78)
# MIDDLE: slow, bowed (ballad section)
SL=[("D4",6),("F4",4),("A4",6),("C5",4),("A4",4),("F4",4),("G3",4),("A3",6),("C4",4),("D4",8),
    ("A3",6),("C4",4),("F4",6),("D4",4),("C4",4),("A3",4),("F3",4),("G3",6),("A3",4),("D3",10)]
for x in SL: n(x[0],x[1],0.62,0.98)
rest(2)
# Morse return + riff + theme
for v in (0.6,0.75): morse("YYZ",v)
riff(2,0.85)
for x in TH: n(*x,0.86)
# SOLO-ish trading phrases
SOLO=[("C5",1),("A4",1),("F4",1),("A4",1),("C5",2),("A4",1),("F4",1),("D4",2),("F4",1),("D4",1),("C4",2),("A3",2)]
for _ in range(4):
    for x in SOLO: n(*x,0.8)
riff(4,0.88)
for x in TH: n(*x,0.88)
# OUTRO: YYZ morse, decaying, final long D
for v in (0.85,0.7,0.55): morse("YYZ",v,"D4","A3")
n("D3",12,0.7,0.98,dyad="A3")
total=t+3
print(f"{len(ev)} events, {total:.1f}s", file=sys.stderr)
# chunk
SR=fl.SR; out=np.zeros((int(total*SR)+SR*30,2)); CH=18.0; TAIL=4.0
c0=0.0; k=0; chunks=[]
while c0<total:
    sel=[e for e in ev if c0<=e[0]<c0+CH]
    # enforce <=64 by splitting
    sub=[sel[i:i+64] for i in range(0,len(sel),64)] or [[]]
    for s in sub:
        if not s: continue
        m={"title":"YYZ","seconds":min(60,CH+TAIL),"seed":11+k,
           "events":[{"note":nn,"start":round(st-c0,4),"bow":b,"vel":round(v,3)} for st,nn,b,v in s]}
        a=fl.render(m)*0.0+fl.render(m) if False else fl.render(m)
        a*=0.6  # chunk gains roughly normalized; loudnorm later
        i0=int(c0*SR); out[i0:i0+len(a)]+=a; k+=1; chunks.append(m)
    c0+=CH
out=out[:int(total*SR)]
out/=np.max(np.abs(out))*1.05
fl.write_wav("yyz_raw.wav",out); json.dump(chunks,open("yyz_score.json","w"))
