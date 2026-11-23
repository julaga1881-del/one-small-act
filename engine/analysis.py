"""Voice analysis: per-frame loudness, subtitle chunks timed to speech, mouth shapes per frame."""
import json, wave, re, os
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../hobbit
AUD = os.path.join(BASE, 'audio')
FPS = 30


def load_voice():
    w = wave.open(os.path.join(AUD, 'voiceover_full.wav'))
    sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def frame_env(x, sr, nframes):
    hop = sr / FPS
    env = np.zeros(nframes)
    for i in range(nframes):
        a = int(i * hop)
        b = int((i + 1) * hop)
        seg = x[a:b]
        env[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    return env


def split_chunks(text, maxc=84):
    t = text.replace('"', '').strip()
    t = t.replace('“', '').replace('”', '')
    # sentence-ish split keeping punctuation
    parts = re.findall(r'[^.!?]+(?:\.\.\.|[.!?])?\s*', t)
    parts = [p.strip() for p in parts if p.strip()]
    # merge "..." continuations and short bits
    out = []
    for p in parts:
        if out and (len(out[-1]) + 1 + len(p) <= 48 or len(p) < 14):
            if len(out[-1]) + 1 + len(p) <= maxc:
                out[-1] = out[-1] + ' ' + p
                continue
        out.append(p)
    final = []
    for p in out:
        while len(p) > maxc:
            # split at comma nearest middle
            idx = [m.end() for m in re.finditer(r',\s', p)]
            if not idx:
                idx = [m.end() for m in re.finditer(r'\s', p)]
            mid = len(p) / 2
            cut = min(idx, key=lambda k: abs(k - mid))
            final.append(p[:cut].strip())
            p = p[cut:].strip()
        final.append(p)
    return final


def main():
    tj = json.load(open(os.path.join(AUD, 'timing.json')))
    x, sr = load_voice()
    dur = len(x) / sr
    total = dur + 1.55
    nframes = int(round(total * FPS))
    env = frame_env(x, sr, nframes)
    db = 20 * np.log10(env + 1e-6)
    voiced = db > -38
    subs = []
    mouth = {}  # frame -> (speaker, shape)
    for ln in tj['lines']:
        s, e = ln['start'], ln['end']
        fa, fb = int(s * FPS), int(np.ceil(e * FPS))
        v = voiced[fa:fb]
        idx = np.where(v)[0]
        if len(idx):
            sp0 = (fa + idx[0]) / FPS
            sp1 = (fa + idx[-1] + 1) / FPS
        else:
            sp0, sp1 = s, e
        chunks = split_chunks(ln['text'])
        # cumulative voiced time
        vf = v.astype(float)
        cum = np.cumsum(vf)
        tot = cum[-1] if len(cum) else 1
        lens = np.array([len(cname) for cname in chunks], dtype=float)
        fr = np.cumsum(lens) / lens.sum()
        bounds = [sp0]
        # silence gaps within the line (>=0.15s)
        gaps = []
        run = 0
        for i, vv in enumerate(v):
            if not vv:
                run += 1
            else:
                if run >= 4:
                    gaps.append((fa + i - run / 2) / FPS)
                run = 0
        for f in fr[:-1]:
            target_i = int(np.searchsorted(cum, f * tot))
            tt = (fa + target_i) / FPS
            if gaps:
                g = min(gaps, key=lambda q: abs(q - tt))
                if abs(g - tt) < 0.9:
                    tt = g
            bounds.append(tt)
        bounds.append(sp1)
        for k, ch in enumerate(chunks):
            subs.append(dict(speaker=ln['speaker'], text=ch, start=round(bounds[k] - 0.08, 3),
                             end=round(bounds[k + 1] + (0.35 if k == len(chunks) - 1 else 0.0), 3), line=ln['line']))
        if ln['speaker'] != 'NARRATOR':
            seg = db[fa:fb]
            peak = np.percentile(seg[seg > -60], 95) if np.any(seg > -60) else -20
            prev = 0
            for k in range(fa, fb, 2):
                lv = db[k] - peak
                if db[k] < -40:
                    shp = 0
                elif lv > -4:
                    shp = 3
                elif lv > -8:
                    shp = 2
                elif lv > -14:
                    shp = 4 if (k // 2) % 3 == 0 else 1
                else:
                    shp = 1
                if shp and shp == prev:
                    shp = {1: 2, 2: 1, 3: 4, 4: 3}[shp]
                prev = shp
                for q in (k, k + 1):
                    mouth[q] = (ln['speaker'], shp)
    # clamp subtitle overlaps
    subs.sort(key=lambda d: d['start'])
    for i in range(len(subs) - 1):
        if subs[i]['end'] > subs[i + 1]['start'] - 0.02:
            subs[i]['end'] = subs[i + 1]['start'] - 0.02
    json.dump(dict(duration=dur, total=total, nframes=nframes, subs=subs,
                   mouth={str(k): v for k, v in mouth.items()}, env=[round(float(q), 5) for q in env],
                   lines=tj['lines']),
              open(os.path.join(BASE, 'out', 'src', 'timeline.json'), 'w'), ensure_ascii=False)
    for s in subs:
        print('%6.2f %6.2f %-8s %s' % (s['start'], s['end'], s['speaker'], s['text']))
    print('frames', nframes, 'total', total)


if __name__ == '__main__':
    main()
