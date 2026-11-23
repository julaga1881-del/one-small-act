"""Original music bed + code-made SFX + final mix. Writes ../mix.wav (48 kHz stereo)."""
import json, os, subprocess, wave
import numpy as np
import pyloudnorm as pyln

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
AUD = os.path.join(os.path.dirname(OUT), 'audio')
SR = 48000
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
TOTAL = TL['nframes'] / 30.0
N = int(TOTAL * SR)
rng = np.random.default_rng(7)


def t_arr(dur):
    return np.arange(int(dur * SR)) / SR


def add(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lowpass(x, fc):
    # one-pole, applied twice
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    for _ in range(2):
        acc = 0.0
        # vectorised via lfilter-like recursion using cumulative approach is complex; use scipy if present
        try:
            from scipy.signal import lfilter
            y = lfilter([1 - a], [1, -a], x)
            x = y
            continue
        except Exception:
            pass
        for k in range(len(x)):
            acc = (1 - a) * x[k] + a * acc
            y[k] = acc
        x = y.copy()
    return x


def highpass(x, fc):
    return x - lowpass(x, fc)


# ------------------------------------------------------------ instruments
def piano(f, dur=2.5, vel=1.0):
    t = t_arr(dur)
    s = np.zeros_like(t)
    for h, amp in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)):
        fh = f * h * (1 + 0.0004 * h * h)
        s += amp * np.sin(2 * np.pi * fh * t) * np.exp(-t * (1.6 + 0.9 * h))
    env = np.minimum(1, t / 0.006)
    return s * env * vel * 0.22


def pluck(f, dur=1.2, vel=1.0):
    t = t_arr(dur)
    s = np.zeros_like(t)
    for h, amp in ((1, 1.0), (2, 0.6), (3, 0.35), (4, 0.2), (6, 0.08)):
        s += amp * np.sin(2 * np.pi * f * h * t) * np.exp(-t * (4 + 2.5 * h))
    return s * np.minimum(1, t / 0.003) * vel * 0.2


def pad(freqs, dur, vel=1.0):
    t = t_arr(dur)
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            s += np.sin(2 * np.pi * ff * t) + 0.18 * np.sin(2 * np.pi * 2 * ff * t)
    s /= (len(freqs) * 3)
    att = np.minimum(1, t / 1.2)
    rel = np.minimum(1, (dur - t) / 1.2)
    return s * att * np.clip(rel, 0, 1) * vel * 0.16


def bass(f, dur, vel=1.0):
    t = t_arr(dur)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.minimum(1, t / 0.02) * np.exp(-t * 0.8) * vel * 0.25


# chords as midi (root position triads) in F major
CH = {'F': [53, 57, 60], 'C': [48, 52, 55], 'Dm': [50, 53, 57], 'Bb': [46, 50, 53], 'Gm': [43, 46, 50],
      'Am': [45, 48, 52], 'C/E': [52, 55, 60]}

# sections: (start, end, progression, style, level)
SECTIONS = [
    (0.0, 17.5, ['F', 'C', 'Dm', 'Bb'], 'gentle', 0.75),
    (17.5, 36.0, ['F', 'Bb', 'F', 'C'], 'bright', 0.85),
    (36.0, 59.0, ['Dm', 'Bb', 'F', 'C'], 'sad', 0.6),
    (59.0, 75.0, ['F', 'C', 'Dm', 'Bb'], 'gentle', 0.75),
    (75.0, 106.3, ['Dm', 'Bb', 'Gm', 'C'], 'pulse', 0.7),
    (106.3, 128.0, ['F', 'C', 'Dm', 'Bb'], 'lift', 1.0),
    (128.0, 159.8, ['F', 'Bb', 'C', 'F'], 'happy', 0.95),
    (159.8, TOTAL, ['F', 'C', 'Dm', 'Bb'], 'finale', 1.0),
]
BPM = 80
BEAT = 60 / BPM
BAR = BEAT * 4


def music():
    L = np.zeros(N + SR * 4)
    R = np.zeros(N + SR * 4)
    bar_idx = 0
    t = 0.0
    while t < TOTAL - 0.5:
        sec = [s for s in SECTIONS if s[0] <= t < s[1]][0]
        prog, style, lvl = sec[2], sec[3], sec[4]
        # final resolve: last bars land on F
        name = prog[bar_idx % len(prog)]
        if t > TOTAL - 5.5:
            name = 'F'
        notes = CH[name]
        root = notes[0] - 12
        # pad
        p = pad([midi(n) for n in notes] + [midi(notes[0] + 12)], BAR + 1.2, 0.9 if style != 'sad' else 0.75)
        add(L, p, t, lvl)
        add(R, p, t, lvl)
        add(L, bass(midi(root), BAR), t, lvl * (0.6 if style in ('sad', 'gentle') else 0.9))
        add(R, bass(midi(root), BAR), t, lvl * (0.6 if style in ('sad', 'gentle') else 0.9))
        if style == 'pulse':
            for b in range(8):
                add(L, bass(midi(root), BEAT * 0.5, 0.5), t + b * BEAT / 2, lvl * 0.6)
                add(R, bass(midi(root), BEAT * 0.5, 0.5), t + b * BEAT / 2, lvl * 0.6)
        # arpeggio
        tones = [notes[0], notes[1], notes[2], notes[0] + 12, notes[1] + 12, notes[2], notes[0] + 12, notes[1]]
        tones = [n + 12 for n in tones]
        step = BEAT / 2
        if style == 'sad':
            pat = [0, 2, 3, 2]
            step = BEAT
        elif style == 'gentle':
            pat = [0, 1, 2, 3, 4, 3, 2, 1]
        else:
            pat = [0, 1, 2, 3, 4, 3, 2, 1]
        for k, idx in enumerate(pat):
            n = tones[idx]
            tt = t + k * step
            vel = 0.8 + 0.2 * (k == 0)
            pn = piano(midi(n), 2.2, vel)
            pan = 0.5 + 0.25 * np.sin(k)
            add(L, pn, tt, lvl * (1 - pan) * 1.6)
            add(R, pn, tt, lvl * pan * 1.6)
        # lift layers: high sparkle arpeggio + plucks
        if style in ('lift', 'finale'):
            for k in range(8):
                n = tones[[4, 3, 4, 2, 4, 3, 1, 2][k]] + 12
                pn = piano(midi(n), 1.6, 0.6)
                add(L, pn, t + k * BEAT / 2 + 0.02, lvl * 0.5)
                add(R, pn, t + k * BEAT / 2 + 0.05, lvl * 0.7)
        if style == 'happy':
            # bouncy plucked off-beats (generic folk-free pizzicato feel)
            for k in range(8):
                if k % 2 == 1:
                    for n in notes:
                        pl = pluck(midi(n + 12), 0.8, 0.7)
                        add(L, pl, t + k * BEAT / 2, lvl * 0.6)
                        add(R, pl, t + k * BEAT / 2 + 0.01, lvl * 0.6)
            for k in range(4):
                pl = pluck(midi(notes[0]), 1.0, 0.9)
                add(L, pl, t + k * BEAT, lvl * 0.5)
                add(R, pl, t + k * BEAT, lvl * 0.5)
        t += BAR
        bar_idx += 1
    # final tonic chord ringing out
    for n in CH['F'] + [65, 69, 72]:
        pn = piano(midi(n + 12), 4.0, 0.7)
        add(L, pn, TOTAL - 3.4, 0.9)
        add(R, pn, TOTAL - 3.4, 0.9)
    L, R = L[:N], R[:N]
    fade = np.ones(N)
    fe = int(1.2 * SR)
    fade[-fe:] = np.linspace(1, 0, fe) ** 1.5
    fi = int(0.3 * SR)
    fade[:fi] = np.linspace(0.3, 1, fi)
    # simple reverb-ish smear: add delayed, lowpassed copies
    out = []
    for ch, d in ((L, 0.031), (R, 0.037)):
        wet = np.zeros_like(ch)
        for k, (dl, g) in enumerate(((d, 0.35), (d * 2.7, 0.25), (d * 5.1, 0.18), (d * 8.3, 0.12))):
            i = int(dl * SR)
            wet[i:] += ch[:-i] * g
        out.append((ch + lowpass(wet, 3000)) * fade)
    return np.stack(out, 1)


# ------------------------------------------------------------ SFX
def noise(dur):
    return rng.standard_normal(int(dur * SR))


def phone_buzz(dur):
    t = t_arr(dur)
    s = np.sign(np.sin(2 * np.pi * 165 * t)) * 0.5 + np.sin(2 * np.pi * 330 * t) * 0.3
    s = lowpass(s, 1200)
    gate = ((t % 0.5) < 0.38).astype(float)
    gate = lowpass(gate, 60)
    return s * gate * 0.25


def river(dur, level=1.0):
    n = noise(dur)
    s = lowpass(n, 1400) - lowpass(n, 180)
    mod = 1 + 0.25 * np.sin(2 * np.pi * 0.23 * t_arr(dur)) + 0.15 * np.sin(2 * np.pi * 0.71 * t_arr(dur))
    # gentle burble: random short sine chirps
    out = s * mod * 0.08
    for k in range(int(dur * 6)):
        t0 = rng.uniform(0, dur - 0.1)
        f0 = rng.uniform(500, 1400)
        tt = t_arr(0.06)
        ch = np.sin(2 * np.pi * (f0 + 3000 * tt) * tt) * np.exp(-tt * 60) * 0.02
        add(out, ch, t0)
    return out * level


def underwater(dur):
    n = noise(dur)
    s = lowpass(n, 260)
    out = s * 0.25 * (1 + 0.3 * np.sin(2 * np.pi * 0.3 * t_arr(dur)))
    for k in range(int(dur * 3)):
        t0 = rng.uniform(0, dur - 0.2)
        f0 = rng.uniform(250, 600)
        tt = t_arr(0.12)
        add(out, np.sin(2 * np.pi * (f0 + 1500 * tt) * tt) * np.exp(-tt * 30) * 0.05, t0)
    return out


def splash_sfx(size=1.0):
    d = 0.9 * size
    n = noise(d)
    t = t_arr(d)
    s = (lowpass(n, 4000) - lowpass(n, 300)) * np.exp(-t * (6 / size)) * np.minimum(1, t / 0.01)
    for k in range(int(8 * size)):
        t0 = rng.uniform(0.05, d * 0.8)
        f0 = rng.uniform(700, 1800)
        tt = t_arr(0.05)
        add(s, np.sin(2 * np.pi * (f0 + 4000 * tt) * tt) * np.exp(-tt * 70) * 0.25, t0)
    return s * 0.5 * size


def ding():
    t = t_arr(2.4)
    s = np.zeros_like(t)
    for f, a, dcy in ((1568, 1.0, 1.8), (3136, 0.35, 3.0), (4310, 0.18, 4.0), (2350, 0.25, 2.4)):
        s += a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy)
    return s * np.minimum(1, t / 0.003) * 0.12


def knock():
    t = t_arr(0.25)
    n = noise(0.25)
    s = lowpass(n, 700) * np.exp(-t * 35) * 0.6 + np.sin(2 * np.pi * 110 * t) * np.exp(-t * 28) * 0.5
    return s * 0.6


def whoosh(dur, rise=True):
    n = noise(dur)
    t = t_arr(dur)
    env = np.sin(np.pi * t / dur) ** 2
    s = lowpass(n, 2500) - lowpass(n, 400)
    return s * env * 0.12


def tape_rewind(dur):
    t = t_arr(dur)
    f = 300 + 1600 * (t / dur) ** 2
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = 0.15 * np.sign(np.sin(ph)) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t))
    s = lowpass(s, 2500)
    env = np.minimum(1, t / 0.1) * np.minimum(1, (dur - t) / 0.2)
    return s * env * 0.35 + whoosh(dur) * 0.5


def clink():
    t = t_arr(0.8)
    s = (np.sin(2 * np.pi * 2600 * t) + 0.6 * np.sin(2 * np.pi * 3900 * t)) * np.exp(-t * 9)
    return s * 0.06


def bubbles_pot(dur):
    out = np.zeros(int(dur * SR))
    for k in range(int(dur * 9)):
        t0 = rng.uniform(0, dur - 0.1)
        f0 = rng.uniform(200, 500)
        tt = t_arr(0.07)
        add(out, np.sin(2 * np.pi * (f0 + 2500 * tt) * tt) * np.exp(-tt * 50) * 0.08, t0)
    return out


def sfx():
    m = np.zeros(N)

    def region(sig_fn, a, b, gain, xf=0.15):
        d = b - a
        s = sig_fn(d + xf * 2)
        e = np.ones(len(s))
        k = int(xf * SR)
        e[:k] = np.linspace(0, 1, k)
        e[-k:] = np.linspace(1, 0, k)
        add(m, s * e, a - xf, gain)

    # phone buzz (hook) and in the kitchen
    add(m, phone_buzz(0.9), 0.0, 1.0)
    add(m, phone_buzz(0.8), 1.4, 1.0)
    add(m, phone_buzz(1.6), 5.25, 0.8)
    add(m, tape_rewind(1.8), 17.6, 1.0)
    # river ambience
    for a, b in ((19.9, 38.3), (38.3, 41.6), (46.55, 84.9), (90.3, 94.9), (106.25, 111.2)):
        region(river, a, b, 1.0)
    for a, b in ((41.6, 46.55), (84.9, 90.3), (99.5, 106.25)):
        region(underwater, a, b, 1.0)
    # terrace & kitchen quiet room tone: nothing
    for tt in (32.8, 34.2, 35.6):
        add(m, splash_sfx(0.8), tt, 0.9)
    add(m, splash_sfx(0.5), 40.45, 0.8)
    add(m, ding(), 103.55, 1.0)
    add(m, splash_sfx(1.3), 106.3, 1.0)
    add(m, ding(), 106.9, 0.45)
    add(m, whoosh(1.4), 111.3, 1.0)
    add(m, bubbles_pot(4.5), 115.8, 1.0)
    add(m, whoosh(3.5), 123.5, 0.6)
    for k in range(3):
        add(m, knock(), 129.5 + k * 0.2, 1.0)
    add(m, clink(), 139.6, 1.0)
    return m


def read_voice():
    tmp = os.path.join(OUT, 'voice48.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(AUD, 'voiceover_full.wav'), '-ar', str(SR), '-ac', '1',
                    '-c:a', 'pcm_s16le', tmp], check=True)
    w = wave.open(tmp)
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    os.remove(tmp)
    v = np.zeros(N)
    v[:min(N, len(x))] = x[:N]
    return v


def main():
    meter = pyln.Meter(SR)
    voice = read_voice()
    print('voice LUFS', meter.integrated_loudness(voice))
    mus = music()
    # duck under speech
    env = np.abs(voice)
    env = lowpass(env, 8)
    act = (env > 0.01).astype(float)
    # attack fast, release slow
    g = np.empty_like(act)
    cur = 0.0
    a_att = np.exp(-1 / (0.05 * SR))
    a_rel = np.exp(-1 / (0.45 * SR))
    try:
        from scipy.signal import lfilter
        # approximate asymmetric smoothing: max of fast and slow follower
        fast = lfilter([1 - a_att], [1, -a_att], act)
        slow = lfilter([1 - a_rel], [1, -a_rel], act)
        g = np.maximum(fast, slow)
    except Exception:
        for i in range(len(act)):
            a = a_att if act[i] > cur else a_rel
            cur = a * cur + (1 - a) * act[i]
            g[i] = cur
    duck = 1 - 0.5 * np.clip(g, 0, 1)  # about -6 dB under speech
    mus = mus * duck[:, None]
    l = meter.integrated_loudness(mus)
    mus = mus * 10 ** ((-24 - l) / 20)
    print('bed LUFS', meter.integrated_loudness(mus))
    fx = sfx()
    fxs = np.stack([fx, fx], 1)
    v2 = np.stack([voice, voice], 1)
    lo, hi = -12.0, 6.0
    for _ in range(14):
        gd = (lo + hi) / 2
        mix = mus + fxs + v2 * 10 ** (gd / 20)
        lm = meter.integrated_loudness(mix)
        if lm > -16:
            hi = gd
        else:
            lo = gd
    print('voice gain dB', gd, 'voice-in-mix LUFS', meter.integrated_loudness(v2 * 10 ** (gd / 20)))
    pk = np.max(np.abs(mix))
    if pk > 0.89:
        # soft-clip peaks only
        mix = np.tanh(mix / 0.89) * 0.89
    print('mix LUFS', meter.integrated_loudness(mix), 'peak', np.max(np.abs(mix)))
    print('sfx-only LUFS', meter.integrated_loudness(fxs + 1e-9))
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    w = wave.open(os.path.join(OUT, 'mix.wav'), 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
    w.close()
    # also stems for checking
    pcm = (np.clip(mus, -1, 1) * 32767).astype(np.int16)
    w = wave.open(os.path.join(OUT, 'music_bed.wav'), 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
    w.close()


if __name__ == '__main__':
    main()
