"""v2 mix: ElevenLabs music track fitted to the 174.5 s video with bar-aligned crossfaded edits.
Voice + SFX identical to v1 (audio.py). Writes ../mix_v2.wav and ../music_v2_bed.wav."""
import os, wave, subprocess
import numpy as np
import pyloudnorm as pyln
from scipy.signal import lfilter
import audio as A   # reuse sfx(), read_voice(), constants (SR=48000, N)

SR, N = A.SR, A.N
OUT = A.OUT
BAR = 10.0 / 3.0  # 72 BPM, 4/4 (measured by onset autocorrelation: 3.33 s)
XF = 1.5          # equal-power crossfade length (s)

# music segments (start, end) in track seconds, all on bar boundaries
SEGS = [(0.0, 12 * BAR), (5 * BAR, 19 * BAR), (16 * BAR, 19 * BAR), (17 * BAR, 24 * BAR),
        (25 * BAR, 34 * BAR), (36 * BAR, 41 * BAR), (43 * BAR, None)]


def load_track():
    tmp = os.path.join(OUT, 'm11.wav')
    if not os.path.exists(tmp):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(A.AUD, 'music_eleven.mp3'), '-ar', '48000',
                        '-ac', '2', '-c:a', 'pcm_s16le', tmp], check=True)
    w = wave.open(tmp)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768


def best_offset(x, a_end, b_start, search=0.04, win=0.5):
    """small shift of the destination so the waveforms around the splice line up best"""
    ia, ib = int(a_end * SR), int(b_start * SR)
    w = int(win * SR)
    ref = x[ia - w // 2: ia + w // 2].mean(1)
    best, bo = -1e9, 0
    for d in range(-int(search * SR), int(search * SR) + 1, 24):
        seg = x[ib + d - w // 2: ib + d + w // 2].mean(1)
        if len(seg) != len(ref):
            continue
        cc = float(np.dot(ref, seg) / (np.linalg.norm(ref) * np.linalg.norm(seg) + 1e-9))
        if cc > best:
            best, bo = cc, d
    return bo, best


def fit(x):
    out = np.zeros((N + SR * 6, 2))
    pos = 0  # output sample of current segment start (splice centre)
    h = int(XF * SR / 2)
    log = []
    segs = [list(s) for s in SEGS]
    shift = [0] * len(segs)
    for i in range(1, len(segs)):
        d, cc = best_offset(x, segs[i - 1][1], segs[i][0])
        shift[i] = d
        log.append((segs[i - 1][1], segs[i][0] + d / SR, cc))
    splices = []
    for i, (s, e) in enumerate(segs):
        s_i = int(s * SR) + shift[i]
        e_i = len(x) if e is None else int(e * SR)
        a = max(0, s_i - (h if i > 0 else 0))
        b = min(len(x), e_i + (h if e is not None else 0))
        chunk = x[a:b].copy()
        n = len(chunk)
        t = np.ones(n)
        if i > 0:  # fade in (equal power)
            k = np.arange(2 * h) / (2 * h)
            t[:2 * h] = np.sin(k * np.pi / 2)
        if e is not None:
            k = np.arange(2 * h) / (2 * h)
            t[-2 * h:] *= np.cos(k * np.pi / 2)
        o0 = pos - (s_i - a)
        o1 = min(len(out), o0 + n)
        out[o0:o1] += (chunk * t[:, None])[:o1 - o0]
        if i > 0:
            splices.append(pos / SR)
        pos += e_i - s_i
    out = out[:N]
    # final 2 s fade-out
    fe = int(2.0 * SR)
    out[-fe:] *= (np.cos(np.linspace(0, np.pi / 2, fe)) ** 2)[:, None]
    return out, splices, log


def v_of(m):
    """map a track time to video time (for reporting)"""
    pos = 0.0
    for (s, e) in SEGS:
        ee = 1e9 if e is None else e
        if s <= m < ee:
            return pos + (m - s)
        pos += (ee - s)
    return None


def main():
    meter = pyln.Meter(SR)
    x = load_track()
    mus, splices, log = fit(x)
    print('splice points (video s):', [round(s, 2) for s in splices])
    for a, b, cc in log:
        print('  track %.2f -> %.3f  (match %.2f)' % (a, b, cc))
    for name, m in (('suspense start', 53.0), ('lift', 66.0), ('folk', 92.0), ('resolve', 132.0), ('track fade', 149.0)):
        # first occurrence after the last splice that contains it
        occ = []
        pos = 0.0
        for (s, e) in SEGS:
            ee = 1e9 if e is None else e
            if s <= m < ee:
                occ.append(round(pos + m - s, 2))
            pos += ee - s
        print('  %-15s track %.1f s -> video %s' % (name, m, occ))
    voice = A.read_voice()
    # duck under speech (same sidechain as v1)
    env = lfilter([1 - np.exp(-2 * np.pi * 8 / SR)], [1, -np.exp(-2 * np.pi * 8 / SR)], np.abs(voice))
    env = lfilter([1 - np.exp(-2 * np.pi * 8 / SR)], [1, -np.exp(-2 * np.pi * 8 / SR)], env)
    act = (env > 0.01).astype(float)
    a_att, a_rel = np.exp(-1 / (0.05 * SR)), np.exp(-1 / (0.45 * SR))
    g = np.maximum(lfilter([1 - a_att], [1, -a_att], act), lfilter([1 - a_rel], [1, -a_rel], act))
    mus = mus * (1 - 0.5 * np.clip(g, 0, 1))[:, None]
    mus *= 10 ** ((-24 - meter.integrated_loudness(mus)) / 20)
    print('bed LUFS', round(meter.integrated_loudness(mus), 2))
    fx = A.sfx()
    fxs = np.stack([fx, fx], 1)
    v2 = np.stack([voice, voice], 1)
    lo, hi = -12.0, 6.0
    for _ in range(14):
        gd = (lo + hi) / 2
        mix = mus + fxs + v2 * 10 ** (gd / 20)
        if meter.integrated_loudness(mix) > -16:
            hi = gd
        else:
            lo = gd
    # peak safety: soft-knee limit above -3 dBFS so true peak after AAC stays < -1.5
    th = 10 ** (-3.0 / 20)
    over = np.abs(mix) > th
    mix[over] = np.sign(mix[over]) * (th + (1 - th) * np.tanh((np.abs(mix[over]) - th) / (1 - th)) * 0.3)
    print('voice gain dB', round(gd, 2), 'mix LUFS', round(meter.integrated_loudness(mix), 2), 'sample peak dBFS',
          round(20 * np.log10(np.max(np.abs(mix))), 2))
    for p, arr in (('mix_v2.wav', mix), ('music_v2_bed.wav', mus)):
        w = wave.open(os.path.join(OUT, p), 'wb')
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(arr, -1, 1) * 32767).astype(np.int16).tobytes())
        w.close()


if __name__ == '__main__':
    main()
