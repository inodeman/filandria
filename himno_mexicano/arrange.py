#!/usr/bin/env python3
"""Himno Nacional Mexicano (Jaime Nunó, public domain) - approximate pentatonic
arrangement for La Filandria (unchanged instrument; only its nine filaments).
Thought in F major; missing Bb/E (and low C, high G) mapped to nearest playable filament."""
import json, sys, numpy as np
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__file__), ".."))
import filandria as F
BEAT = 60/66
# degree -> filament; ambiguous degrees list options (choose one differing from previous note)
MAP = {"5,":["D3"],"1":["F3"],"2":["G3"],"3":["A3"],"4":["A3","C4"],"5":["C4"],"6":["D4"],
       "7":["D4","F4"],"1'":["F4"],"2'":["A4","F4"],"3'":["A4"]}
BASS = {"1":"F3","3":"F3","5":"F3","1'":"F3","5,":"F3","2":"G3","4":"D3","6":"D3","7":"G3","2'":"G3","3'":"F3"}
def line(pick, bar1, bar2):
    return (pick, bar1, bar2)
CH = [  # chorus lines (pickup, bar1, bar2)
 (["5","5"], ["1","1","1","2","3","4"], ["5","3"]),
 (["5","5"], ["4","4","4","3","2","3"], ["1"]),
 (["5","5"], ["6","6","6","5","4","5"], ["6"]),
 (["6","6"], ["5","4","3","2","1","2"], ["1"]),
 (["5","5"], ["6","6","6","5","4","5"], ["6"]),
 (["6","6"], ["5","4","3","2","1","2"], ["1"]),
]
ST = [  # stanza "Ciña ¡oh Patria!..."
 (["3","3"], ["3","4","5","5","4","3"], ["2"]),
 (["2","2"], ["2","3","4","4","3","2"], ["1"]),
 (["5","5"], ["6","5","4","3","2","1"], ["7"]),
 (["5","5"], ["5","6","7","1'","2'","7"], ["1'"]),
 (["5","5"], ["6","5","4","3","2","1"], ["7"]),
 (["5","5"], ["5","6","7","1'","2'","7"], ["1'"]),
]
INTRO = CH[4:6]
R1 = [0.75,0.25,0.75,0.25,1,1]
def section(lines, title, seed, base_vel):
    ev=[]; t=0.6; prev=None
    def put(d, start, beats, vel):
        nonlocal prev
        opts=[o for o in MAP[d] if o!=prev] or MAP[d]
        n=opts[0]; prev=n
        ev.append({"note":n,"start":round(start,3),"bow":round(max(0.08,min(4,beats*BEAT*0.92)),3),"vel":vel})
    for i,(pick,b1,b2) in enumerate(lines):
        v=base_vel+(0.08 if i>=len(lines)-2 else 0)
        put(pick[0],t,0.75,v*0.85); put(pick[1],t+0.75*BEAT,0.25,v*0.8)
        t+=BEAT; bar=t
        for d,du in zip(b1,R1): put(d,t,du,v); t+=du*BEAT
        ev.append({"note":BASS[b1[0]],"start":round(bar,3),"bow":round(3.8*BEAT,3),"vel":round(v*0.5,3)})
        bar2=t
        if len(b2)==2: put(b2[0],t,2,v); put(b2[1],t+2*BEAT,1,v*0.9)
        else: put(b2[0],t,3,v)
        ev.append({"note":BASS[b2[0]],"start":round(bar2,3),"bow":round(min(4,2.9*BEAT),3),"vel":round(v*0.5,3)})
        t=bar2+3*BEAT
    return {"title":title,"seconds":round(t+1.6,3),"seed":seed,"events":ev}
secs=[section(INTRO,"Introduccion",3,0.62),section(CH[:3],"Coro a",5,0.76),section(CH[3:],"Coro b",6,0.80),
      section(ST[:3],"Estrofa I a",7,0.66),section(ST[3:],"Estrofa I b",8,0.74),
      section(CH[:3],"Coro final a",9,0.84),section(CH[3:],"Coro final b",10,0.90)]
json.dump(secs,open("himno_filandria_score.json","w"),indent=1,ensure_ascii=False)
XF=int(1.3*F.SR); out=None
for s in secs:
    a=F.render(s); print(s["title"],len(s["events"]),"events",s["seconds"],"s")
    if out is None: out=a; continue
    r=np.linspace(0,1,XF)[:,None]
    out=np.concatenate([out[:-XF], out[-XF:]*(1-r)+a[:XF]*r, a[XF:]])
F.write_wav("himno_mexicano_filandria.wav", out)
print("total", out.shape[0]/F.SR)
