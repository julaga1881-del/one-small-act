"""Reusable YouTube-Short toolkit (1080x1920): voice analysis, word captions, mouths, vertical camera,
bar-aligned music fitting, ducked mix with true-peak limiter, parallel render + mux.
A story module supplies the shots (frame drawing), SFX and music plan; see story_wrongturn.py."""
import json, math, os, subprocess, wave
import multiprocessing as mp
import numpy as np
import skia
from gfx import *

VW, VH = 1080, 1920
SR = 48000
FPS = 30


# ------------------------------------------------------------------ camera
class VCam:
    """Vertical camera looking at world point (cx, cy) with zoom z; world units = output px at z=1."""

    def __init__(self, cx=540, cy=960, z=1.0):
        self.cx, self.cy, self.z = cx, cy, z

    def apply(self, c, depth=1.0):
        z = 1 + (self.z - 1) * depth
        c.translate(VW / 2, VH / 2)
        c.scale(z, z)
        c.translate(-(VW / 2 + (self.cx - VW / 2) * depth), -(VH / 2 + (self.cy - VH / 2) * depth))


class vlayer:
    def __init__(self, c, cam, depth=1.0):
        self.c, self.cam, self.depth = c, cam, depth

    def __enter__(self):
        self.c.save()
        self.cam.apply(self.c, self.depth)
        return self.c

    def __exit__(self, *a):
        self.c.restore()


def vcam(lt, dur, a, b, mode='io', drift=1.0, seed=0):
    u = clamp(lt / max(dur, 1e-6))
    e = {'io': ease_io(u), 'out': ease_out(u), 'lin': u, 'in': ease_in(u)}[mode]
    cx = lerp(a[0], b[0], e) + drift * (5 * math.sin(lt * 0.9 + seed) + 2 * math.sin(lt * 2.1 + seed * 2))
    cy = lerp(a[1], b[1], e) + drift * (4 * math.sin(lt * 0.7 + seed * 3) + 2 * math.sin(lt * 1.7 + seed))
    return VCam(cx, cy, lerp(a[2], b[2], e))


def vvignette(c, a=0.38):
    p = skia.Paint(AntiAlias=True)
    p.setShader(rad(VW / 2, VH / 2, math.hypot(VW / 2, VH / 2), [hexc('#000000', 0), hexc('#000000', 0), hexc('#000000', a)],
                    [0, 0.5, 1]))
    c.drawRect(skia.Rect.MakeWH(VW, VH), p)


# ------------------------------------------------------------------ voice
class Voice:
    def __init__(self, wav_path, timing_path, tail=1.0):
        self.timing = json.load(open(timing_path))
        self.lines = self.timing['lines']
        tmp = wav_path + '.48k.tmp.wav'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav_path, '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', tmp],
                       check=True)
        w = wave.open(tmp)
        self.x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        os.remove(tmp)
        self.total = len(self.x) / SR + tail
        self.nf = int(round(self.total * FPS))
        hop = SR // FPS
        n = self.nf
        pad = np.zeros(n * hop)
        pad[:min(len(pad), len(self.x))] = self.x[:n * hop]
        self.env = np.sqrt((pad.reshape(n, hop) ** 2).mean(1))
        self.db = 20 * np.log10(self.env + 1e-6)
        self.mouths = self._mouths()
        self.caps = self._captions()

    def _mouths(self):
        m = {}
        for ln in self.lines:
            if ln['speaker'] == 'NARRATOR':
                continue
            fa, fb = int(ln['start'] * FPS), int(math.ceil(ln['end'] * FPS))
            seg = self.db[fa:fb]
            peak = np.percentile(seg[seg > -60], 95) if np.any(seg > -60) else -20
            prev = 0
            for k in range(fa, fb, 2):
                lv = self.db[k] - peak
                shp = 0 if self.db[k] < -40 else 3 if lv > -4 else 2 if lv > -8 else (4 if (k // 2) % 3 == 0 else 1) if lv > -14 else 1
                if shp and shp == prev:
                    shp = {1: 2, 2: 1, 3: 4, 4: 3}[shp]
                prev = shp
                m[k] = m[k + 1] = (ln['speaker'], shp)
        return m

    def mouth(self, speaker, T):
        v = self.mouths.get(int(T * FPS))
        return v[1] if v and v[0] == speaker else 0

    def speaking(self, speaker, T):
        return any(l['speaker'] == speaker and l['start'] - 0.05 <= T <= l['end'] + 0.1 for l in self.lines)

    def _captions(self):
        caps = []
        P = '.,!?…:'
        for ln in self.lines:
            words = ln['text'].replace('"', '').replace('“', '').replace('”', '').split()
            a, b = int(ln['start'] * FPS), int(math.ceil(ln['end'] * FPS))
            vo = (self.db[a:b] > -40).astype(float)
            if vo.sum() == 0:
                continue
            idxv = np.where(vo)[0]
            sp_end = (a + idxv[-1] + 1) / FPS
            cum = np.cumsum(vo)
            wts = np.array([len(w.strip(P)) + 1.5 for w in words])
            cw = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
            gaps, run = [], 0
            for i, v in enumerate(vo):
                if not v:
                    run += 1
                else:
                    if run >= 4 and i - run > 0:
                        gaps.append((a + i) / FPS - 0.03)
                    run = 0
            st = []
            for i, w in enumerate(words):
                t = (a + int(np.searchsorted(cum, cw[i] * cum[-1] + 0.5))) / FPS
                if i > 0 and words[i - 1][-1] in P and gaps:
                    g = min(gaps, key=lambda q: abs(q - t))
                    if abs(g - t) < 0.6:
                        t = g
                st.append(t)
            for i in range(1, len(st)):
                st[i] = max(st[i], st[i - 1] + 0.12)
            chunks = []
            sent, cur = [], []
            for i, w in enumerate(words):
                cur.append(i)
                if w[-1] in P or i == len(words) - 1:
                    sent.append(cur)
                    cur = []
            for sw_ in sent:
                chunks += balance_chunks(sw_, words)
            for k, ch in enumerate(chunks):
                t0 = st[ch[0]] - 0.04
                t1 = st[chunks[k + 1][0]] - 0.04 if k + 1 < len(chunks) else sp_end + 0.15
                caps.append(dict(text=' '.join(words[j] for j in ch), start=t0, end=t1, speaker=ln['speaker']))
        for i in range(len(caps) - 1):
            caps[i]['end'] = min(caps[i]['end'], caps[i + 1]['start'])
        return caps


def balance_chunks(idx, words, max_words=5, max_chars=34):
    """split one sentence (word indices) into the fewest balanced chunks of <=max_words words"""
    import itertools
    n = len(idx)
    L = [len(words[i]) for i in idx]
    best = None
    for k in range(max(1, math.ceil(n / max_words)), n + 1):
        for cuts in itertools.combinations(range(1, n), k - 1):
            parts = [idx[a:b] for a, b in zip((0,) + cuts, cuts + (n,))]
            if any(len(p) > max_words for p in parts):
                continue
            widths = [sum(len(words[i]) for i in p) + len(p) - 1 for p in parts]
            score = max(widths) + 14 * k
            if best is None or score < best[0]:
                best = (score, parts)
        if best and max(sum(len(words[i]) for i in p) + len(p) - 1 for p in best[1]) <= max_chars:
            break
    return best[1]


def _wrap2(text, f, maxw):
    words = text.split()
    if f.measureText(text) <= maxw or len(words) < 2:
        return [text]
    best = None
    for i in range(1, len(words)):
        l1, l2 = ' '.join(words[:i]), ' '.join(words[i:])
        w = max(f.measureText(l1), f.measureText(l2))
        if best is None or w < best[0]:
            best = (w, [l1, l2])
    return best[1]


def draw_caption(c, caps, T, colors, x=500, y=1420, maxw=760, size=60, y_max=1530, pill=True):
    """Lower-third Shorts caption: bold, thin outline, soft dark pill; block centred at (x, y), never below y_max,
    max two lines within maxw (keeps clear of the bottom UI band and the right-edge buttons)."""
    for cp in caps:
        if cp['start'] <= T < cp['end']:
            sz = size
            while True:
                f = font(FONT_SUB, sz)
                lines = _wrap2(cp['text'], f, maxw)
                if max(f.measureText(l) for l in lines) <= maxw or sz <= 40:
                    break
                sz -= 2
            lh = sz * 1.2
            bh = lh * len(lines)
            cy = min(y, y_max - bh / 2 - 14)
            col = colors.get(cp['speaker'], '#ffffff')
            a = ease_out(ramp(T, cp['start'], cp['start'] + 0.1))
            c.save()
            c.translate(x, cy + (1 - a) * 8)
            if pill:
                bw = max(f.measureText(l) for l in lines) + 44
                draw(c, rrect(-bw / 2, -bh / 2 - 10, bw, bh + 20, 22), '#000000', None, 0, fa=0.42 * a)
            for i, l in enumerate(lines):
                yy = -bh / 2 + lh * (i + 0.5) + sz * 0.35
                draw_text(c, l, 0, yy, f, col, 'center', '#0b0b0b', 7, a, a)
            c.restore()
            return


def draw_true_story(c, T, dur=3.0, text='Based on a true story'):
    if T < dur:
        a = 1 - ramp(T, dur - 0.4, dur)
        f = font(FONT_UI, 34)
        w = f.measureText(text)
        draw(c, rrect(540 - w / 2 - 22, 128, w + 44, 58, 29), '#000000', None, 0, fa=0.4 * a)
        draw_text(c, text, 540, 168, f, '#f4f1ea', 'center', a=0.95 * a)


# ------------------------------------------------------------------ audio
def load_track(path):
    tmp = path + '.48k.tmp.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', tmp], check=True)
    w = wave.open(tmp)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
    os.remove(tmp)
    return x


def _best_offset(x, a_end, b_start, search=0.04, win=0.5):
    ia, ib, w = int(a_end * SR), int(b_start * SR), int(win * SR)
    ref = x[ia - w // 2: ia + w // 2].mean(1)
    best, bo = -1e9, 0
    for d in range(-int(search * SR), int(search * SR) + 1, 24):
        seg = x[ib + d - w // 2: ib + d + w // 2].mean(1)
        if len(seg) != len(ref):
            continue
        cc = float(np.dot(ref, seg) / (np.linalg.norm(ref) * np.linalg.norm(seg) + 1e-9))
        if cc > best:
            best, bo = cc, d
    return bo


def fit_music(x, segs, n, start=0.0, xf=1.5, fade_out=1.0):
    """segs: [(m0, m1|None), ...] played back to back from video time `start` with equal-power crossfades.
    Returns (stereo array of n samples, list of (video_s, track_s) splice points)."""
    out = np.zeros((n + SR * 12, 2))
    h = int(xf * SR / 2)
    pos = int(start * SR)
    spl = []
    for i, (s, e) in enumerate(segs):
        d = _best_offset(x, segs[i - 1][1], s) if i else 0
        si = int(s * SR) + d
        ei = len(x) if e is None else int(e * SR)
        a = max(0, si - (h if i else 0))
        b = min(len(x), ei + (h if e is not None else 0))
        ch = x[a:b].copy()
        t = np.ones(len(ch))
        if i:
            t[:2 * h] = np.sin(np.arange(2 * h) / (2 * h) * np.pi / 2)
        if e is not None:
            t[-2 * h:] *= np.cos(np.arange(2 * h) / (2 * h) * np.pi / 2)
        o0 = pos - (si - a)
        o1 = min(len(out), o0 + len(ch))
        if o0 < 0:
            ch, t, o0 = ch[-o0:], t[-o0:], 0
        out[o0:o1] += (ch * t[:, None])[:o1 - o0]
        if i:
            spl.append((round(pos / SR, 2), round(s, 2)))
        pos += ei - si
    out = out[:n]
    fe = int(fade_out * SR)
    out[-fe:] *= (np.cos(np.linspace(0, np.pi / 2, fe)) ** 2)[:, None]
    return out, spl


def mix(voice, fx, music, out_wav, target=-14.0, bed=-24.0, tp=-3.0, duck_db=6.0):
    import pyloudnorm as pyln
    from scipy.signal import lfilter, resample_poly
    from scipy.ndimage import minimum_filter1d
    n = len(voice)
    p8 = np.exp(-2 * np.pi * 8 / SR)
    env = lfilter([1 - p8], [1, -p8], lfilter([1 - p8], [1, -p8], np.abs(voice)))
    act = (env > 0.01).astype(float)
    aa, ar = np.exp(-1 / (0.05 * SR)), np.exp(-1 / (0.45 * SR))
    g = np.maximum(lfilter([1 - aa], [1, -aa], act), lfilter([1 - ar], [1, -ar], act))
    music = music * (1 - (1 - 10 ** (-duck_db / 20)) * np.clip(g, 0, 1))[:, None]
    meter = pyln.Meter(SR)
    music = music * 10 ** ((bed - meter.integrated_loudness(music)) / 20)
    bed_l = meter.integrated_loudness(music)
    vf = np.stack([voice + fx, voice + fx], 1)
    lo, hi = -12.0, 14.0
    for _ in range(14):
        gd = (lo + hi) / 2
        m = vf * 10 ** (gd / 20) + music
        if meter.integrated_loudness(m) > target:
            hi = gd
        else:
            lo = gd
    # true-peak limiter (4x oversampled detection, 6 ms hold, 80 ms release)
    th = 10 ** (tp / 20)
    up = np.abs(resample_poly(m, 4, 1, axis=0)).max(1)[:n * 4].reshape(-1, 4).max(1)
    gr = minimum_filter1d(np.minimum(1, th / np.maximum(up, 1e-9)), int(0.006 * SR))
    rel = np.exp(-1 / (0.08 * SR))
    gs = np.empty_like(gr)
    cur = 1.0
    for i in range(len(gr)):
        cur = gr[i] if gr[i] < cur else rel * cur + (1 - rel) * gr[i]
        gs[i] = cur
    m = m * gs[:, None]
    m *= 10 ** ((target - meter.integrated_loudness(m)) / 20)
    w = wave.open(out_wav, 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(m, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()
    return dict(bed_lufs=round(bed_l, 2), voice_gain_db=round(gd, 2), mix_lufs=round(meter.integrated_loudness(m), 2),
                limited_pct=round(100 * float((gs < 0.999).mean()), 1))


def place(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    s0 = max(0, -i)
    i = max(0, i)
    j = min(len(buf), i + len(sig) - s0)
    buf[i:j] += sig[s0:s0 + j - i] * gain


# ------------------------------------------------------------------ render
def _worker(args):
    frame_fn, f0, f1, outp = args
    surf = skia.Surface(VW, VH)
    c = surf.getCanvas()
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', '%dx%d' % (VW, VH), '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-threads', '1', outp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        c.clear(hexc('#000000'))
        frame_fn(c, fi / FPS)
        pr.stdin.write(surf.makeImageSnapshot().tobytes())
    pr.stdin.close()
    pr.wait()
    return outp


def render(frame_fn, nf, audio_wav, out_mp4, workers=2, tmpdir=None):
    tmpdir = tmpdir or os.path.dirname(os.path.abspath(out_mp4))
    step = int(math.ceil(nf / workers))
    jobs = [(frame_fn, k * step, min(nf, (k + 1) * step), os.path.join(tmpdir, '_part%d.mp4' % k)) for k in range(workers)]
    with mp.get_context('fork').Pool(workers) as pool:
        parts = pool.map(_worker, jobs)
    lst = os.path.join(tmpdir, '_parts.txt')
    open(lst, 'w').write(''.join("file '%s'\n" % p for p in parts))
    vid = os.path.join(tmpdir, '_video.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-i', audio_wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', '%.3f' % (nf / FPS), '-movflags', '+faststart',
                    out_mp4], check=True)
    for p in parts + [lst, vid]:
        os.remove(p)


def stills(frame_fn, times, outdir, prefix='f'):
    os.makedirs(outdir, exist_ok=True)
    surf = skia.Surface(VW, VH)
    c = surf.getCanvas()
    paths = []
    for t in times:
        c.clear(hexc('#000000'))
        frame_fn(c, t)
        p = os.path.join(outdir, '%s_%05.2f.png' % (prefix, t))
        surf.makeImageSnapshot().save(p)
        paths.append(p)
    return paths


def contact(paths, out, cols=5, w=270, h=480):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(FONT_SUB, 22)
    rows = (len(paths) + cols - 1) // cols
    sh = Image.new('RGB', (w * cols, (h + 28) * rows), (30, 30, 30))
    d = ImageDraw.Draw(sh)
    for i, p in enumerate(paths):
        x, y = (i % cols) * w, (i // cols) * (h + 28)
        sh.paste(Image.open(p).convert('RGB').resize((w, h)), (x, y + 28))
        d.text((x + 5, y + 2), os.path.basename(p)[:-4], fill=(255, 255, 0), font=fnt)
    sh.save(out)
