#!/usr/bin/env python3
"""La Filandria — compose and play original melodies.

Another program can import this file or call it from the shell.
Only these nine filaments can be bowed. D2 and A2 are the skin drone
and are not playable notes.

    python filandria.py notes
    python filandria.py compose --seconds 10 --seed 7 --out la-mano.wav --json la-mano.json
    python filandria.py play la-mano.json --out la-mano.wav

Melody JSON
-----------
{
  "title": "La mano",
  "seconds": 10,
  "seed": 7,
  "events": [
    {"note": "A4", "start": 0.2, "bow": 0.6, "vel": 0.8}
  ]
}

note   one of D3 F3 G3 A3 C4 D4 F4 A4 C5
start  seconds from the beginning, >= 0 and < seconds
bow    seconds the hair stays on that filament, 0.08 to 4
vel    0.05 to 1
events at most 64, in any order
seconds 4 to 60
seed   integer, changes bow noise only; the same seed is the same take

Chromatic mode (new filaments)
------------------------------
Add "tuning": "cromatica" to the melody to bow the extended set of glass
filaments: every semitone from F1 to F6, A4 = 440 Hz equal temperament.
Notes are names like "Bb4", "A#4", "Eb2", "F1" (or MIDI numbers 29..89).
Optional keys (chromatic and marea):
  "drone": "fixed" (default, D2/A2 skin) | "off" |
           [{"start": 0, "root": "Bb1", "fifth": "F2"}, ...]  (follows harmony)
  "drone_level": float, default 1.0 (0 silences the skin)
  "gain": float, default 1.0, scales the bowed filaments before the mix
Per event: "breath": false keeps that note out of the breath layer
(use it for harmony/bass so the air follows the melody).
There is no limit on seconds or number of events; bow up to 30 s.
"""
from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000

# Escala de marea. Uneven on purpose: not 12-tone equal temperament.
SCALE = {
    "D3": 146.15,
    "F3": 173.35,
    "G3": 194.55,
    "A3": 217.70,
    "C4": 258.20,
    "D4": 291.55,
    "F4": 345.85,
    "A4": 434.05,
    "C5": 514.55,
}
DRONE = {"D2": 73.08, "A2": 109.15}
ORDER = ["D3", "F3", "G3", "A3", "C4", "D4", "F4", "A4", "C5"]

# Filamentos cromaticos: F1..F6, A4 = 440 Hz equal temperament.
CHROMA_LOW, CHROMA_HIGH = 29, 89  # MIDI F1 .. F6
_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_to_midi(note) -> int:
    """'Bb4' / 'A#4' / 'Eb2' / 60 -> MIDI number."""
    if isinstance(note, (int, np.integer)) and not isinstance(note, bool):
        return int(note)
    if not isinstance(note, str) or len(note) < 2 or note[0].upper() not in _PC:
        raise MelodyError(f"bad note name {note!r}")
    pc = _PC[note[0].upper()]
    rest = note[1:]
    while rest and rest[0] in "#b":
        pc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    try:
        octave = int(rest)
    except ValueError as exc:
        raise MelodyError(f"bad note name {note!r}") from exc
    return 12 * (octave + 1) + pc


def chroma_hz(note) -> float:
    m = note_to_midi(note)
    if not CHROMA_LOW <= m <= CHROMA_HIGH:
        raise MelodyError(f"note {note!r} is outside the chromatic filaments F1..F6")
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


CHROMATIC = {m: 440.0 * 2.0 ** ((m - 69) / 12.0) for m in range(CHROMA_LOW, CHROMA_HIGH + 1)}

# The first phrase, kept so a bot can replay the original take.
MAREA_CORTA = {
    "title": "Marea corta",
    "seconds": 10,
    "seed": 11,
    "events": [
        {"note": "A4", "start": 0.16, "bow": 0.64, "vel": 0.76},
        {"note": "F4", "start": 0.82, "bow": 0.36, "vel": 0.62},
        {"note": "D4", "start": 1.20, "bow": 0.74, "vel": 0.84},
        {"note": "A3", "start": 1.98, "bow": 0.90, "vel": 0.70},
        {"note": "C4", "start": 2.94, "bow": 0.40, "vel": 0.64},
        {"note": "D4", "start": 3.40, "bow": 0.50, "vel": 0.80},
        {"note": "F4", "start": 3.96, "bow": 0.46, "vel": 0.72},
        {"note": "A4", "start": 4.48, "bow": 0.60, "vel": 0.88},
        {"note": "C5", "start": 5.14, "bow": 1.02, "vel": 0.94},
        {"note": "A4", "start": 6.22, "bow": 0.46, "vel": 0.68},
        {"note": "F4", "start": 6.72, "bow": 0.40, "vel": 0.58},
        {"note": "D4", "start": 7.18, "bow": 1.12, "vel": 0.78},
        {"note": "A3", "start": 8.40, "bow": 0.36, "vel": 0.50},
        {"note": "D4", "start": 8.84, "bow": 1.00, "vel": 0.60},
    ],
}


class MelodyError(ValueError):
    """The melody JSON does not match the contract above."""


def validate(melody: dict) -> dict:
    if not isinstance(melody, dict):
        raise MelodyError("melody must be an object")
    try:
        seconds = float(melody["seconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MelodyError("seconds must be a number") from exc
    tuning = str(melody.get("tuning", "marea"))
    if tuning not in ("marea", "cromatica"):
        raise MelodyError("tuning must be 'marea' or 'cromatica'")
    if not 1 <= seconds:
        raise MelodyError("seconds must be at least 1")
    seed = int(melody.get("seed", 1))
    events_in = melody.get("events")
    if not isinstance(events_in, list) or not events_in:
        raise MelodyError("events must be a non-empty list")
    events = []
    for i, event in enumerate(events_in):
        if not isinstance(event, dict):
            raise MelodyError(f"event {i} must be an object")
        note = event.get("note")
        if tuning == "cromatica":
            hz = chroma_hz(note)
        elif note not in SCALE:
            raise MelodyError(
                f"event {i} note {note!r} is not playable; use one of {ORDER}"
            )
        else:
            hz = SCALE[note]
        try:
            start = float(event["start"])
            bow = float(event["bow"])
            vel = float(event["vel"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MelodyError(f"event {i} needs numeric start, bow and vel") from exc
        if start < 0 or start >= seconds:
            raise MelodyError(f"event {i} start must be >= 0 and < seconds")
        if not 0.08 <= bow <= 30:
            raise MelodyError(f"event {i} bow must be between 0.08 and 30 seconds")
        if not 0.05 <= vel <= 1:
            raise MelodyError(f"event {i} vel must be between 0.05 and 1")
        events.append(
            {
                "note": note,
                "start": round(start, 4),
                "bow": round(bow, 4),
                "vel": round(vel, 4),
                "hz": hz,
                "breath": bool(event.get("breath", True)),
            }
        )
    events.sort(key=lambda e: e["start"])
    drone = melody.get("drone", "fixed")
    if isinstance(drone, list):
        changes = []
        for j, ch in enumerate(drone):
            try:
                root = chroma_hz(ch["root"]) if not isinstance(ch["root"], float) else ch["root"]
                fifth = ch.get("fifth")
                fifth = root * 1.5 if fifth is None else chroma_hz(fifth)
                changes.append((float(ch.get("start", 0)), root, fifth))
            except (KeyError, TypeError) as exc:
                raise MelodyError(f"drone change {j} needs start and root") from exc
        if not changes:
            raise MelodyError("drone list must not be empty")
        drone = sorted(changes)
    elif drone not in ("fixed", "off"):
        raise MelodyError("drone must be 'fixed', 'off' or a list of changes")
    out = {
        "title": str(melody.get("title") or "sin-titulo"),
        "seconds": seconds,
        "seed": seed,
        "events": events,
        "tuning": tuning,
        "drone": drone,
        "drone_level": float(melody.get("drone_level", 1.0)),
        "gain": float(melody.get("gain", 1.0)),
    }
    return out


def compose(seconds: float = 10.0, seed: int = 1, title: str | None = None) -> dict:
    """Write one original phrase on the nine filaments. Same seed, same phrase."""
    if not 4 <= float(seconds) <= 60:
        raise MelodyError("seconds must be between 4 and 60")
    rng = np.random.default_rng(int(seed))
    events = []
    t = 0.16
    idx = int(rng.integers(3, 7))
    climax_at = float(seconds) * 0.50
    climbed = False
    while t < float(seconds) - 1.15 and len(events) < 24:
        if not climbed and t >= climax_at:
            idx = min(8, idx + int(rng.integers(2, 4)))
            climbed = True
            vel = 0.92
            bow = 0.98
        else:
            step = int(rng.choice([-2, -1, -1, 1, 1, 2]))
            idx = int(np.clip(idx + step, 0, 8))
            # Longer bows in the lower half, shorter ones as it climbs.
            bow = float(rng.uniform(0.36, 0.78 if idx < 6 else 0.58))
            vel = 0.52 + 0.04 * idx
        if t + bow > float(seconds) - 0.3:
            bow = max(0.3, float(seconds) - 0.35 - t)
        events.append(
            {
                "note": ORDER[idx],
                "start": round(t, 3),
                "bow": round(bow, 3),
                "vel": round(min(vel, 0.96), 3),
            }
        )
        t += bow * float(rng.uniform(0.82, 0.94))
    cadence_at = min(t, float(seconds) - 1.05)
    if events and cadence_at <= events[-1]["start"]:
        cadence_at = events[-1]["start"] + 0.2
    events.append(
        {
            "note": "D4",
            "start": round(cadence_at, 3),
            "bow": round(min(1.05, float(seconds) - cadence_at - 0.02), 3),
            "vel": 0.62,
        }
    )
    return _public(validate(
        {
            "title": title or f"frase-{int(seed)}",
            "seconds": float(seconds),
            "seed": int(seed),
            "events": events,
        }
    ))


def _public(m: dict) -> dict:
    """Validated melody back to the original JSON shape (marea defaults hidden)."""
    out = {"title": m["title"], "seconds": m["seconds"], "seed": m["seed"],
           "events": [{k: e[k] for k in ("note", "start", "bow", "vel")} for e in m["events"]]}
    return out


try:  # fast, numerically equivalent filters; pure-python fallback below
    from scipy.signal import lfilter as _lfilter
except ImportError:  # pragma: no cover
    _lfilter = None


def _biquad_bandpass(x: np.ndarray, f0: float, q: float, sr: int) -> np.ndarray:
    w0 = 2.0 * np.pi * f0 / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2.0 * q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1.0 + alpha, -2.0 * cw, 1.0 - alpha
    b0, b1, b2 = b0 / a0, b1 / a0, b2 / a0
    a1, a2 = a1 / a0, a2 / a0
    if _lfilter is not None:
        return _lfilter([b0, b1, b2], [1.0, a1, a2], x)
    y = np.empty_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, xn in enumerate(x):
        yn = b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, xn
        y2, y1 = y1, yn
        y[i] = yn
    return y


def _biquad_lowpass(x: np.ndarray, f0: float, q: float, sr: int) -> np.ndarray:
    w0 = 2.0 * np.pi * min(f0, sr * 0.45) / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2.0 * q)
    b0 = (1.0 - cw) * 0.5
    b1 = 1.0 - cw
    b2 = (1.0 - cw) * 0.5
    a0, a1, a2 = 1.0 + alpha, -2.0 * cw, 1.0 - alpha
    b0, b1, b2 = b0 / a0, b1 / a0, b2 / a0
    a1, a2 = a1 / a0, a2 / a0
    if _lfilter is not None:
        return _lfilter([b0, b1, b2], [1.0, a1, a2], x)
    y = np.empty_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, xn in enumerate(x):
        yn = b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, xn
        y2, y1 = y1, yn
        y[i] = yn
    return y


def _place(buf: np.ndarray, start: int, sig: np.ndarray) -> None:
    if start >= len(buf) or start < 0:
        return
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start]


def _glass_note(f: float, bow: float, vel: float, sr: int, rng: np.random.Generator) -> np.ndarray:
    tail = 0.62 + 0.15 * (1.0 - min(vel, 1.0))
    n = int((bow + tail) * sr)
    t = np.arange(n) / sr
    bloom = 1.0 - np.exp(-t * 8.0)
    vib = (8.5 / 1200.0) * np.sin(2.0 * np.pi * (4.7 + 0.4 * vel) * t) * bloom
    tilt = (4.0 / 1200.0) * np.sin(2.0 * np.pi * 0.33 * t + f)
    inst = f * np.power(2.0, vib + tilt)
    phase = 2.0 * np.pi * np.cumsum(inst) / sr
    partials = (
        (1.000, 1.00, 0.00),
        (2.003, 0.22, 0.40),
        (2.410, 0.13, 1.70),
        (3.012, 0.055, 0.20),
        (1.498, 0.09, 2.10),
        (4.030, 0.028, 0.90),
    )
    tone = np.zeros(n)
    for ratio, amp, ph in partials:
        decay = np.exp(-t * (0.35 + 1.6 * (ratio - 1.0)))
        tone += amp * decay * np.sin(phase * ratio + ph)
    if f > 400 and vel > 0.8:
        tone += 0.16 * vel * np.exp(-t * 1.1) * np.sin(phase * 2.0 + 0.3)
    noise = rng.standard_normal(n)
    grit = _biquad_bandpass(noise, f * 1.5, 3.2, sr)
    grit += 0.45 * _biquad_bandpass(noise, f * 3.1, 2.2, sr)
    trem = 0.72 + 0.28 * np.sin(2.0 * np.pi * 5.4 * t + f)
    bow_env = np.ones(n)
    attack = max(1, int(0.045 * sr))
    release = max(1, int(0.07 * sr))
    bow_n = min(n, int(bow * sr))
    bow_env[:attack] = np.linspace(0, 1, attack) ** 1.5
    if bow_n + release < n:
        bow_env[bow_n : bow_n + release] = np.linspace(1, 0, release)
        bow_env[bow_n + release :] = 0
    elif bow_n < n:
        bow_env[bow_n:] *= np.linspace(1, 0, n - bow_n)
    grit *= trem * bow_env
    skin = 0.07 * np.sin(phase * 0.5 + 0.6) * np.exp(-t * 0.8)
    tick_n = int(0.07 * sr)
    tick_t = np.arange(tick_n) / sr
    tone[:tick_n] += 0.045 * vel * np.sin(2 * np.pi * (1800 + f) * tick_t) * np.exp(-tick_t * 70)
    sig = tone + 0.06 * vel * grit + skin
    env = np.ones(n)
    atk = max(1, int((0.05 + 0.03 * (1 - vel)) * sr))
    env[:atk] = np.linspace(0, 1, atk) ** 1.35
    if bow_n < n:
        env[bow_n:] *= np.linspace(1, 0, n - bow_n) ** 1.25
    sustain = 0.78 + 0.18 * vel
    if bow_n > atk + 10:
        env[atk:bow_n] *= np.linspace(1.0, sustain, bow_n - atk)
    return (sig * env * vel).astype(np.float64)


def _drone(n: int, sr: int, dur: float, rng: np.random.Generator, changes=None) -> np.ndarray:
    t = np.arange(n) / sr
    if changes is None:
        d, a = DRONE["D2"], DRONE["A2"]
        fund = np.sin(2 * np.pi * d * t) + 0.65 * np.sin(2 * np.pi * d * 1.004 * t + 0.4)
        fifth = 0.42 * np.sin(2 * np.pi * a * t + 1.1) + 0.2 * np.sin(2 * np.pi * a * 0.997 * t)
    else:
        # The skin is re-tensioned: root/fifth glide (~80 ms) to follow the harmony.
        d = np.full(n, changes[0][1])
        a = np.full(n, changes[0][2])
        for start, root, fif in changes:
            i0 = max(0, int(start * sr))
            d[i0:] = root
            a[i0:] = fif
        k = np.hanning(max(3, int(0.08 * sr)))
        k /= k.sum()
        pad = len(k)
        d = np.convolve(np.pad(d, pad, mode="edge"), k, mode="same")[pad:-pad]
        a = np.convolve(np.pad(a, pad, mode="edge"), k, mode="same")[pad:-pad]
        pd = 2 * np.pi * np.cumsum(d) / sr
        pa = 2 * np.pi * np.cumsum(a) / sr
        fund = np.sin(pd) + 0.65 * np.sin(pd * 1.004 + 0.4)
        fifth = 0.42 * np.sin(pa + 1.1) + 0.2 * np.sin(pa * 0.997)
    tide = 0.72 + 0.28 * np.sin(2 * np.pi * 0.18 * t - 0.6)
    air = _biquad_lowpass(rng.standard_normal(n), 180.0, 0.7, sr)
    air = _biquad_lowpass(air, 180.0, 0.7, sr)
    sig = ((0.55 * fund + fifth) * tide + 0.08 * air * tide) * 0.34
    fade_in = np.minimum(1.0, t / 0.7)
    fade_out = np.minimum(1.0, np.maximum(0.0, (dur - t) / 1.1))
    return sig * fade_in * fade_out


def _breath(pitch: np.ndarray, amp: np.ndarray, sr: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal(len(pitch))
    air = _biquad_bandpass(noise, 920.0, 1.4, sr)
    air = air + 0.5 * _biquad_bandpass(noise, 1400.0, 0.8, sr)
    phase = 2 * np.pi * np.cumsum(np.maximum(pitch, 40.0)) / sr
    edge = 0.55 * np.sin(phase) + 0.18 * np.sin(2 * phase + 0.5)
    return ((0.22 * air + edge) * amp) * 0.07


def _early(x: np.ndarray, sr: int) -> np.ndarray:
    y = x.copy()
    for delay_ms, gain in ((11.5, 0.18), (17.2, 0.12), (23.8, 0.08), (31.0, 0.05)):
        d = int(delay_ms * 0.001 * sr)
        if 0 < d < len(x):
            y[d:] += gain * x[:-d]
    return y


def _comb(x: np.ndarray, delay: int, feedback: float, damp: float) -> np.ndarray:
    if _lfilter is not None:
        n = len(x)
        y = np.zeros(n)
        w = np.zeros(n)
        zi = np.zeros(1)
        for k in range(0, n, delay):
            e = min(n, k + delay)
            if k >= delay:
                y[k:e] = w[k - delay : e - delay]
            lp, zi = _lfilter([1.0 - damp], [1.0, -damp], y[k:e], zi=zi)
            w[k:e] = x[k:e] + lp * feedback
        return y
    buf = np.zeros(delay)
    y = np.empty_like(x)
    idx = 0
    lp = 0.0
    for i, xn in enumerate(x):
        out = buf[idx]
        lp = (1.0 - damp) * out + damp * lp
        buf[idx] = xn + lp * feedback
        y[i] = out
        idx += 1
        if idx == delay:
            idx = 0
    return y


def _allpass(x: np.ndarray, delay: int, g: float) -> np.ndarray:
    if _lfilter is not None:
        n = len(x)
        d = np.zeros(n)
        w = np.zeros(n)
        for k in range(0, n, delay):
            e = min(n, k + delay)
            if k >= delay:
                d[k:e] = w[k - delay : e - delay]
            w[k:e] = x[k:e] + d[k:e] * g
        return d - g * x
    buf = np.zeros(delay)
    y = np.empty_like(x)
    idx = 0
    for i, xn in enumerate(x):
        delayed = buf[idx]
        buf[idx] = xn + delayed * g
        y[i] = delayed - g * xn
        idx += 1
        if idx == delay:
            idx = 0
    return y


def _reverb(x: np.ndarray, sr: int, stereo_bias: float) -> np.ndarray:
    combs = (
        (int(0.0297 * sr), 0.62, 0.28),
        (int(0.0371 * sr), 0.60, 0.32),
        (int(0.0413 * sr), 0.58, 0.30),
        (int(0.0437 * sr) + int(stereo_bias), 0.55, 0.34),
    )
    acc = np.zeros_like(x)
    for delay, fb, damp in combs:
        acc += _comb(x, max(8, delay), fb, damp)
    acc *= 0.25
    for delay, g in ((int(0.0050 * sr), 0.70), (int(0.0017 * sr), 0.70)):
        acc = _allpass(acc, max(8, delay), g)
    return acc


def render(melody: dict, sr: int = SR) -> np.ndarray:
    """Play a melody. Returns stereo float64 in [-1, 1], shape (frames, 2)."""
    melody = validate(melody)
    seconds = melody["seconds"]
    n = int(sr * seconds)
    rng = np.random.default_rng(melody["seed"])
    glass = np.zeros(n)
    pitch = np.zeros(n)
    amp = np.zeros(n)
    for event in melody["events"]:
        sig = _glass_note(event["hz"], event["bow"], event["vel"], sr, rng)
        i0 = int(event["start"] * sr)
        _place(glass, i0, sig * melody["gain"])
        if not event["breath"]:
            continue
        i1 = min(n, i0 + int((event["bow"] + 0.15) * sr))
        if i1 <= i0:
            continue
        pitch[i0:i1] = event["hz"]
        window = np.sin(np.linspace(0, np.pi, i1 - i0)) ** 0.6
        amp[i0:i1] = np.maximum(amp[i0:i1], event["vel"] * window)
    last = SCALE["A4"]
    for i in range(n):
        if pitch[i] > 0:
            last = pitch[i]
        else:
            pitch[i] = last
    kernel = np.hanning(max(3, int(0.06 * sr)))
    kernel /= kernel.sum()
    amp_s = np.convolve(amp, kernel, mode="same")
    if melody["drone"] == "off":
        _drone(min(n, 16), sr, seconds, rng)  # keep the noise stream identical
        drone = np.zeros(n)
    elif melody["drone"] == "fixed":
        drone = _drone(n, sr, seconds, rng) * melody["drone_level"]
    else:
        drone = _drone(n, sr, seconds, rng, melody["drone"]) * melody["drone_level"]
    breath = _breath(pitch, amp_s, sr, rng)
    wood = _biquad_bandpass(glass, 280.0, 1.0, sr) * 0.05
    dry = glass + wood
    reflected = _early(glass * 0.75 + breath * 0.35 + drone * 0.15, sr)
    wet_l = _reverb(reflected, sr, 0)
    wet_r = _reverb(reflected, sr, 180)
    delay = int(0.00115 * sr)
    glass_r = np.zeros_like(glass)
    glass_r[delay:] = glass[:-delay]
    left = dry + drone * 0.42 + breath * 0.30 + wet_l * 0.20
    right = glass_r * 0.9 + wood * 0.6 + drone * 0.42 + breath * 0.42 + wet_r * 0.22
    left = np.tanh(left * 0.92)
    right = np.tanh(right * 0.92)
    fin = int(0.04 * sr)
    fout = min(n // 3, int(0.45 * sr))
    if fin:
        left[:fin] *= np.linspace(0, 1, fin)
        right[:fin] *= np.linspace(0, 1, fin)
    if fout:
        left[-fout:] *= np.linspace(1, 0, fout) ** 1.1
        right[-fout:] *= np.linspace(1, 0, fout) ** 1.1
    peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))), 1e-9)
    gain = 0.89 / peak
    stereo = np.column_stack([left * gain, right * gain])
    return np.clip(stereo, -1.0, 1.0)


def write_wav(path: str | Path, audio: np.ndarray, sr: int = SR) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ints = (np.clip(audio, -1, 1) * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(ints.tobytes())


def _load(path: Path) -> dict:
    return validate(json.loads(path.read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compose and play La Filandria.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    notes = sub.add_parser("notes", help="print the nine playable filaments as JSON")
    notes.add_argument("--out", type=Path)

    play = sub.add_parser("play", help="render a melody JSON file to wav")
    play.add_argument("melody", type=Path)
    play.add_argument("--out", type=Path, required=True)

    comp = sub.add_parser("compose", help="invent a phrase, then render it")
    comp.add_argument("--seconds", type=float, default=10)
    comp.add_argument("--seed", type=int, default=1)
    comp.add_argument("--title", default=None)
    comp.add_argument("--out", type=Path, required=True)
    comp.add_argument("--json", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "notes":
            payload = {"playable": SCALE, "order": ORDER, "drone_only": DRONE, "sample_rate": SR,
                       "cromatica": {"range": ["F1", "F6"], "a4_hz": 440.0}}
            text = json.dumps(payload, indent=2)
            if args.out:
                args.out.write_text(text + "\n", encoding="utf-8")
            else:
                print(text)
            return 0
        if args.cmd == "play":
            melody = _load(args.melody)
            audio = render(melody)
            write_wav(args.out, audio)
        else:
            melody = compose(args.seconds, args.seed, args.title)
            args.json.write_text(json.dumps(melody, indent=2) + "\n", encoding="utf-8")
            audio = render(melody)
            write_wav(args.out, audio)
    except MelodyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: melody file is not valid JSON ({exc})", file=sys.stderr)
        return 2
    frames = audio.shape[0]
    print(f"wrote {args.out} {frames / SR:.3f}s {melody['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
