"""v2 low-noise engine for the Sandman cover (reuses filandria helpers).
Changes vs filandria.render: bow grit -75% and low-passed, breath air -80%,
drone without noise 'air' and quieter, inharmonic partials tamed on low notes,
no tanh drive (linear mix + slow peak limiter), 30 Hz HPF, gentle 9 kHz LPF,
low-mid de-mud, peak normalised to -1 dBFS."""
import numpy as np, sys, os
sys.path.insert(0, os.environ.get("FILANDRIA", "/workspace/filandria"))
import filandria as F
from scipy.signal import butter, sosfiltfilt, lfilter

def glass_note(f, bow, vel, sr, rng):
    tail = 0.62 + 0.15 * (1.0 - min(vel, 1.0)); n = int((bow + tail) * sr); t = np.arange(n) / sr
    bloom = 1.0 - np.exp(-t * 8.0)
    vib = (6.0 / 1200.0) * np.sin(2*np.pi*(4.7+0.4*vel)*t) * bloom
    tilt = (3.0 / 1200.0) * np.sin(2*np.pi*0.33*t + f)
    phase = 2*np.pi*np.cumsum(f*np.power(2.0, vib+tilt))/sr
    low = f < 200            # low notes: inharmonic partials beat against the bass/drone -> roughness
    partials = ((1.0,1.0,0.0),(2.003,0.22,0.4),(2.41,0.13*(0.25 if low else 0.7),1.7),(3.012,0.055,0.2),
                (1.498,0.09*(0.2 if low else 0.7),2.1),(4.03,0.028,0.9))
    tone = np.zeros(n)
    for r,a,ph in partials:
        tone += a*np.exp(-t*(0.35+1.6*(r-1.0)))*np.sin(phase*r+ph)
    if f > 400 and vel > 0.8: tone += 0.12*vel*np.exp(-t*1.1)*np.sin(phase*2.0+0.3)
    noise = rng.standard_normal(n)
    grit = F._biquad_bandpass(noise, f*1.5, 6.0, sr) + 0.3*F._biquad_bandpass(noise, f*3.1, 4.0, sr)
    grit = F._biquad_lowpass(grit, 3000.0, 0.7, sr)
    bow_env = np.ones(n); atk = int(0.045*sr); rel = int(0.07*sr); bow_n = min(n, int(bow*sr))
    bow_env[:atk] = np.linspace(0,1,atk)**1.5
    if bow_n+rel < n: bow_env[bow_n:bow_n+rel] = np.linspace(1,0,rel); bow_env[bow_n+rel:] = 0
    elif bow_n < n: bow_env[bow_n:] *= np.linspace(1,0,n-bow_n)
    grit *= (0.72+0.28*np.sin(2*np.pi*5.4*t+f))*bow_env
    skin = 0.05*np.sin(phase*0.5+0.6)*np.exp(-t*0.8)
    tn = int(0.07*sr); tt = np.arange(tn)/sr
    tone[:tn] += 0.025*vel*np.sin(2*np.pi*(1800+f)*tt)*np.exp(-tt*90)
    sig = tone + 0.015*vel*grit + skin
    env = np.ones(n); a2 = max(1, int((0.05+0.03*(1-vel))*sr)); env[:a2] = np.linspace(0,1,a2)**1.35
    if bow_n < n: env[bow_n:] *= np.linspace(1,0,n-bow_n)**1.25
    if bow_n > a2+10: env[a2:bow_n] *= np.linspace(1.0, 0.78+0.18*vel, bow_n-a2)
    return sig*env*vel

def drone(n, sr, dur, changes):
    t = np.arange(n)/sr
    d = np.full(n, changes[0][1]); a = np.full(n, changes[0][2])
    for s,r,fi in changes:
        i0 = max(0,int(s*sr)); d[i0:] = r; a[i0:] = fi
    k = np.hanning(int(0.08*sr)); k /= k.sum(); p = len(k)
    d = np.convolve(np.pad(d,p,mode="edge"),k,mode="same")[p:-p]; a = np.convolve(np.pad(a,p,mode="edge"),k,mode="same")[p:-p]
    pd = 2*np.pi*np.cumsum(d)/sr; pa = 2*np.pi*np.cumsum(a)/sr
    sig = (0.55*(np.sin(pd)+0.4*np.sin(pd*1.001+0.4)) + 0.42*np.sin(pa+1.1)) * (0.8+0.2*np.sin(2*np.pi*0.18*t)) * 0.34
    return sig*np.minimum(1,t/0.7)*np.minimum(1,np.maximum(0,(dur-t)/1.1))

def render(melody, sr=F.SR):
    m = F.validate(melody); secs = m["seconds"]; n = int(sr*secs); rng = np.random.default_rng(m["seed"])
    glass = np.zeros(n); pitch = np.zeros(n); amp = np.zeros(n)
    for e in m["events"]:
        i0 = int(e["start"]*sr); F._place(glass, i0, glass_note(e["hz"], e["bow"], e["vel"], sr, rng)*m["gain"])
        if not e["breath"]: continue
        i1 = min(n, i0+int((e["bow"]+0.15)*sr))
        if i1 <= i0: continue
        pitch[i0:i1] = e["hz"]; amp[i0:i1] = np.maximum(amp[i0:i1], e["vel"]*np.sin(np.linspace(0,np.pi,i1-i0))**0.6)
    last = 440.0
    for i in np.flatnonzero(pitch == 0): pass
    idx = np.where(pitch > 0, np.arange(n), 0); np.maximum.accumulate(idx, out=idx)
    pitch = np.where(idx > 0, pitch[idx], last); pitch[pitch == 0] = last
    k = np.hanning(int(0.06*sr)); k /= k.sum(); amp_s = np.convolve(amp, k, mode="same")
    dr = drone(n, sr, secs, m["drone"]) * m["drone_level"] if isinstance(m["drone"], list) else np.zeros(n)
    noise = rng.standard_normal(n)
    air = F._biquad_bandpass(noise, 920.0, 1.4, sr)
    ph = 2*np.pi*np.cumsum(np.maximum(pitch,40.0))/sr
    breath = ((0.04*air + 0.55*np.sin(ph) + 0.18*np.sin(2*ph+0.5))*amp_s)*0.07
    wood = F._biquad_bandpass(glass, 280.0, 1.0, sr)*0.04
    refl = F._early(glass*0.75 + breath*0.35 + dr*0.1, sr)
    wl = F._reverb(refl, sr, 0); wr = F._reverb(refl, sr, 180)
    dly = int(0.00115*sr); gr = np.zeros_like(glass); gr[dly:] = glass[:-dly]
    L = glass + wood + dr*0.42 + breath*0.30 + wl*0.20
    R = gr*0.9 + wood*0.6 + dr*0.42 + breath*0.42 + wr*0.22
    x = np.column_stack([L, R])
    x = sosfiltfilt(butter(2, 30, "high", fs=sr, output="sos"), x, axis=0)
    x = sosfiltfilt(butter(2, 9000, "low", fs=sr, output="sos"), x, axis=0)
    # de-mud: cut ~3 dB of the 50-110 Hz band where bass+drone+low chords pile up
    band = sosfiltfilt(butter(2, [50, 110], "band", fs=sr, output="sos"), x, axis=0)
    x = x - 0.3*band
    # slow, transparent peak limiter instead of tanh drive (no harmonic distortion)
    lvl = np.abs(x).max(1); thr = np.percentile(lvl, 99.5)
    g = np.minimum(1.0, thr/np.maximum(lvl, 1e-9))
    a_rel = np.exp(-1/(0.25*sr)); g = np.minimum.accumulate(g[::-1])[::-1]*0 + g  # keep g
    g = -lfilter([1-a_rel],[1,-a_rel], -g)  # smooth release
    w = int(0.005*sr); g = np.array([g]).ravel()
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(g, w*2+1)          # lookahead: catch attacks
    g = np.convolve(g, np.ones(w)/w, mode="same")
    x = x*g[:,None]
    fin = int(0.04*sr); fout = int(0.45*sr)
    x[:fin] *= np.linspace(0,1,fin)[:,None]; x[-fout:] *= (np.linspace(1,0,fout)**1.1)[:,None]
    return x * (10**(-1/20) / np.abs(x).max())
