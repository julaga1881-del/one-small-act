"""9:16 YouTube Short cut from the hobbit episode.
python3 short.py audio            -> ../short_mix.wav + ../short_plan.json
python3 short.py still t1 t2 ...  -> ../short_frames/*.png
python3 short.py video f0 f1 out  -> raw render of frames [f0,f1)
"""
import sys, os, json, math, wave, subprocess
import numpy as np
import skia
from gfx import *
import gfx
import scenes as S
import sets as ST

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
VW, VH = 1080, 1920
SC = VH / 1080.0            # world->vertical scale (vector re-render, no upscaling)
CW = VW / SC                # crop width in world px (607.5)
LINES = [2, 3, 4, 7, 9, 16, 17, 21, 23]
GAP = 0.3
LEAD = 0.3
TAIL = 1.2
TLJ = json.load(open(os.path.join(HERE, 'timeline.json')))
L = {l['line']: l for l in TLJ['lines']}
ENV = np.array(TLJ['env'])
DB = 20 * np.log10(ENV + 1e-6)


def plan():
    segs = []
    t = LEAD
    for k in LINES:
        a, b = int(L[k]['start'] * 30), int(np.ceil(L[k]['end'] * 30))
        v = np.where(DB[a:b] > -40)[0]
        s = (a + v[0]) / 30 - 0.05
        e = (a + v[-1] + 1) / 30 + 0.12
        segs.append(dict(line=k, speaker=L[k]['speaker'], text=L[k]['text'], ns=t, ne=t + e - s, os=s, oe=e))
        t += e - s + GAP
    total = segs[-1]['ne'] + TAIL
    return segs, total


SEGS, TOTAL = plan()
NF = int(round(TOTAL * 30))

# ------------------------------------------------------------- visual mapping
def vis_map(V):
    """-> (kind, T_orig)"""
    if V < 1.8:
        return 'phone_top', V
    for i, s in enumerate(SEGS):
        lo = s['ns'] - GAP / 2 if i else 1.8
        hi = s['ne'] + GAP / 2 if i < len(SEGS) - 1 else 1e9
        if lo <= V < hi:
            To = V - s['ns'] + s['os']
            if s['line'] == 23 and To >= 147.10:
                return 'group', To
            return 'orig', To
    return 'orig', V


CROP = {  # world-x crop centre at shot start / end
    'sh_phone_pov': (960, 960), 'sh_patrick_frozen': (830, 820), 'sh_rewind': (960, 960),
    'sh_river_establish': (1250, 1220), 'sh_grab_hand': (900, 900), 'sh_ring_slip': (850, 1080),
    'sh_ring_tumble': (680, 1120), 'sh_joanne_turns': (960, 960), 'sh_joanne_runs': (800, 1000),
    'sh_nicola_search': (420, 470), 'sh_glint': (1010, 960), 'sh_surface': (960, 960), 'sh_door': (960, 960),
    'sh_filippo': (960, 960), 'sh_help': (1500, 1500),
}


def crop_x(fn, lt, dur):
    n = fn.__name__
    if n == 'sh_hobbits':
        cx = lerp(770, 1250, ease_io(ramp(lt, 1.0, 2.6)))
    else:
        a, b = CROP.get(n, (960, 960))
        cx = lerp(a, b, ease_io(clamp(lt / max(dur, 1e-3))))
    return clamp(cx, CW / 2, 1920 - CW / 2)


# vertical-only overlays are drawn by us; silence the 16:9 ones
S.vignette = lambda *a, **k: None
S.place_strip = lambda *a, **k: None
_hang = S.hang_tag
S.hang_tag = lambda *a, **k: None


def group_shot(c, lt, T):
    cam = cam_path(lt, 5.5, (960, 540, 1.0), (960, 560, 1.05), 'lin', 0.4, 50)
    ST.set_door(c, cam, T, 1.0, 1.0)
    with ST.layer(c, cam, 1.0):
        draw(c, rect(760, 400, 72, 440), shade('#2f7d4f', -0.15), INK, 5)
        back = [('edoardo', 752, True), ('joanne', 856, False), ('filippo', 960, True), ('patrick', 1064, False),
                ('nicola', 1168, True)]
        for n, x, cost in back:
            sp = S.spec(n, costume=cost)
            if n == 'patrick':
                sp['ring_on'] = True
            if n == 'filippo':
                sp['bracelet'] = True
            st = dict(facing=(960 - x) / 600.0, expr='happy' if n != 'filippo' else 'tender', gest_hand=None)
            if n == 'filippo':
                st.update(rhand=(14, -40), lhand=(-15, -32))
            else:
                st.update(lhand=(-15, -34), rhand=(15, -34))
            S.person(c, n, x, 1050, 250 * (0.94 if n == 'joanne' else 1.0), T, sp=sp, **st)
        for n, x in (('girl1', 800), ('girl3', 1012), ('girl2', 1120)):
            S.person(c, n, x, 1078, 250 * S.CAST[n]['hs'], T, expr='laugh', facing=0.0, gest_hand=None,
                     lhand=(-15, -40), rhand=(15, -40))
        S.music_notes(c, 700, 560, T, 3, 0.7)
    gfx.grade(c, '#ffb070', 0.10)


def render_world(c, V):
    kind, To = vis_map(V)
    c.save()
    c.scale(SC, SC)
    if kind == 'phone_top':
        c.translate(-(880 - CW / 2), 0)
        S.sh_phone_top(c, V, 2.7, V)
    elif kind == 'group':
        lt = V - (SEGS[-1]['ns'] + 147.10 - SEGS[-1]['os'])
        c.translate(-(960 - CW / 2), 0)
        group_shot(c, lt, To)
    else:
        a, b, fn = S.shot_at(To)
        dur = min(b, TLJ['total']) - a
        cx = crop_x(fn, To - a, dur)
        c.translate(-(cx - CW / 2), 0)
        fn(c, To - a, dur, To)
    c.restore()
    # vertical vignette
    p = skia.Paint(AntiAlias=True)
    p.setShader(rad(VW / 2, VH / 2, math.hypot(VW / 2, VH / 2), [hexc('#000000', 0), hexc('#000000', 0), hexc('#000000', 0.38)],
                    [0, 0.5, 1]))
    c.drawRect(skia.Rect.MakeWH(VW, VH), p)


# ------------------------------------------------------------- captions
def word_times():
    caps = []
    for s in SEGS:
        words = s['text'].replace('"', '').replace('“', '').replace('”', '').split()
        a, b = int(s['os'] * 30), int(math.ceil(s['oe'] * 30))
        vo = (DB[a:b] > -40).astype(float)
        cum = np.cumsum(vo)
        tot = cum[-1]
        wts = np.array([len(w.strip('.,!?…:')) + 1.5 for w in words])
        cw = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        # silence gaps (>=4 frames) inside the line
        gaps = []
        run = 0
        for i, v in enumerate(vo):
            if not v:
                run += 1
            else:
                if run >= 4 and i - run > 0:
                    gaps.append((a + i) / 30 - 0.03)
                run = 0
        st = []
        for i, w in enumerate(words):
            idx = int(np.searchsorted(cum, cw[i] * tot + 0.5))
            t = (a + idx) / 30
            if i > 0 and words[i - 1][-1] in '.,!?…:' and gaps:
                g = min(gaps, key=lambda q: abs(q - t))
                if abs(g - t) < 0.6:
                    t = g
            st.append(t)
        for i in range(1, len(st)):
            st[i] = max(st[i], st[i - 1] + 0.12)
        # group into 1-3 word chunks
        chunks = []
        cur = []
        for i, w in enumerate(words):
            cur.append(i)
            txt = ' '.join(words[j] for j in cur)
            brk = w[-1] in '.,!?…:' or len(cur) == 3 or (i + 1 < len(words) and len(txt + ' ' + words[i + 1]) > 15)
            if brk:
                chunks.append(list(cur))
                cur = []
        if cur:
            chunks.append(cur)
        off = s['ns'] - s['os']
        for k, ch in enumerate(chunks):
            t0 = st[ch[0]] + off - 0.04
            t1 = (st[chunks[k + 1][0]] + off - 0.04) if k + 1 < len(chunks) else s['ne'] + 0.15
            caps.append(dict(text=' '.join(words[j] for j in ch), start=round(t0, 3), end=round(t1, 3), speaker=s['speaker']))
    return caps


CAPS = word_times()


def draw_caption(c, V):
    for cp in CAPS:
        if cp['start'] <= V < cp['end']:
            size = 104
            f = font(FONT_SUB, size)
            while f.measureText(cp['text']) > 840 and size > 60:
                size -= 4
                f = font(FONT_SUB, size)
            col = S.SUB_COL.get(cp['speaker'], '#ffffff')
            pop = 1 + 0.08 * (1 - ease_out(ramp(V, cp['start'], cp['start'] + 0.12)))
            c.save()
            c.translate(500, 1152)
            c.scale(pop, pop)
            draw_text(c, cp['text'], 4, 6 + size * 0.35, f, '#000000', 'center', '#000000', 22, 0.45, 0.45)
            draw_text(c, cp['text'], 0, size * 0.35, f, col, 'center', '#0b0b0b', 16)
            c.restore()
            break


def draw_overlays(c, V):
    if V < 3.0:
        a = 1 - ramp(V, 2.6, 3.0)
        f = font(FONT_UI, 34)
        txt = 'Based on a true story'
        w = f.measureText(txt)
        draw(c, rrect(540 - w / 2 - 22, 128, w + 44, 58, 29), '#000000', None, 0, fa=0.4 * a)
        draw_text(c, txt, 540, 168, f, '#f4f1ea', 'center', a=0.95 * a)
    s4 = SEGS[2]['ns']
    _hang(c, '9 DAYS EARLIER', V - (s4 + 0.3), 540, 2.6)
    s21 = SEGS[7]['ns']
    _hang(c, 'DÚN LAOGHAIRE', V - (s21 + 0.2), 540, 2.6)


def frame(c, fi):
    V = fi / 30.0
    c.clear(hexc('#000000'))
    render_world(c, V)
    draw_overlays(c, V)
    draw_caption(c, V)


# ------------------------------------------------------------- audio
def build_audio():
    import audio as A
    import pyloudnorm as pyln
    from scipy.signal import lfilter
    import audio_v2 as M2
    SR = 48000
    n = int(round(TOTAL * SR))
    voice_o = A.read_voice()
    fx_o = A.sfx()
    voice = np.zeros(n)
    for s in SEGS:
        a, b = int(s['os'] * SR), int(s['oe'] * SR)
        clip = voice_o[a:b].copy()
        k = int(0.01 * SR)
        clip[:k] *= np.linspace(0, 1, k)
        clip[-k:] *= np.linspace(1, 0, k)
        i = int(s['ns'] * SR)
        voice[i:i + len(clip)] += clip[:max(0, n - i)]
    # SFX follow the picture mapping (with 30 ms crossfades at the cuts)
    fx = np.zeros(n)
    bounds = [(0.0, 1.8, 0.0)]
    for i, s in enumerate(SEGS):
        lo = s['ns'] - GAP / 2 if i else 1.8
        hi = s['ne'] + GAP / 2 if i < len(SEGS) - 1 else TOTAL
        bounds.append((lo, hi, s['os'] - s['ns']))
    xf = int(0.03 * SR)
    for lo, hi, off in bounds:
        i0, i1 = int(lo * SR), min(n, int(hi * SR))
        src0 = int((lo + off) * SR)
        seg = fx_o[max(0, src0 - xf): src0 + (i1 - i0) + xf].copy()
        if src0 - xf < 0:
            seg = np.concatenate([np.zeros(xf - src0), seg])
        e = np.ones(len(seg))
        e[:2 * xf] = np.linspace(0, 1, 2 * xf)
        e[-2 * xf:] = np.linspace(1, 0, 2 * xf)
        j0 = i0 - xf
        js, ss = max(0, j0), max(0, -j0)
        L_ = min(len(seg) - ss, n - js)
        fx[js:js + L_] += (seg * e)[ss:ss + L_]
    # music: bar-aligned sections of the ElevenLabs track
    BAR = 10 / 3
    x = M2.load_track()
    msegs = [(0.0, 5 * BAR, 1.0), (16 * BAR, 19 * BAR, None), (17 * BAR, 21 * BAR, None), (28 * BAR, 30 * BAR, None),
             (43 * BAR, None, None)]
    mus = np.zeros((n + SR * 10, 2))
    h = int(0.75 * SR)
    pos = int(1.0 * SR)
    spl = []
    for i, (s, e, _) in enumerate(msegs):
        d = 0
        if i:
            d, cc = M2.best_offset(x, msegs[i - 1][1], s)
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
        o1 = min(len(mus), o0 + len(ch))
        mus[o0:o1] += (ch * t[:, None])[:o1 - o0]
        if i:
            spl.append((round(pos / SR, 2), s))
        pos += ei - si
    mus = mus[:n]
    fe = int(0.6 * SR)
    mus[-fe:] *= np.linspace(1, 0, fe)[:, None]
    # duck under speech
    p8 = np.exp(-2 * np.pi * 8 / SR)
    env = lfilter([1 - p8], [1, -p8], lfilter([1 - p8], [1, -p8], np.abs(voice)))
    act = (env > 0.01).astype(float)
    aa, ar = np.exp(-1 / (0.05 * SR)), np.exp(-1 / (0.45 * SR))
    g = np.maximum(lfilter([1 - aa], [1, -aa], act), lfilter([1 - ar], [1, -ar], act))
    mus *= (1 - 0.5 * np.clip(g, 0, 1))[:, None]
    meter = pyln.Meter(SR)
    mus *= 10 ** ((-24 - meter.integrated_loudness(mus)) / 20)
    v2 = np.stack([voice, voice], 1)
    f2 = np.stack([fx, fx], 1)
    lo, hi = -10.0, 12.0
    for _ in range(14):
        gd = (lo + hi) / 2
        mix = (v2 + f2) * 10 ** (gd / 20) + mus * 10 ** (gd / 20) * 0 + mus
        if meter.integrated_loudness(mix) > -14:
            hi = gd
        else:
            lo = gd
    th = 10 ** (-3.0 / 20)
    o = np.abs(mix) > th
    mix[o] = np.sign(mix[o]) * (th + (1 - th) * np.tanh((np.abs(mix[o]) - th) / (1 - th)) * 0.3)
    print('music splices (video s, track s):', spl, ' lift (track 66.67) at', round(1.0 + 5 * BAR + 3 * BAR + (20 - 17) * BAR, 2),
          ' folk (track 93.33) at', spl[2][0])
    print('bed LUFS', round(meter.integrated_loudness(mus), 2), 'voice+fx gain', round(gd, 2), 'mix LUFS',
          round(meter.integrated_loudness(mix), 2))
    w = wave.open(os.path.join(OUT, 'short_mix.wav'), 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()


def main():
    mode = sys.argv[1]
    if mode == 'audio':
        for s in SEGS:
            print(s['line'], round(s['ns'], 2), round(s['ne'], 2))
        print('total', round(TOTAL, 2), 'frames', NF)
        build_audio()
        return
    surf = skia.Surface(VW, VH)
    c = surf.getCanvas()
    if mode == 'still':
        od = os.path.join(OUT, 'short_frames')
        os.makedirs(od, exist_ok=True)
        for t in sys.argv[2:]:
            fi = min(NF - 1, int(round(float(t) * 30)))
            frame(c, fi)
            p = os.path.join(od, 's_%05.2f.png' % (fi / 30))
            surf.makeImageSnapshot().save(p)
            print(p)
    elif mode == 'video':
        f0, f1, outp = int(sys.argv[2]), min(int(sys.argv[3]), NF), sys.argv[4]
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', '%dx%d' % (VW, VH), '-r', '30',
               '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-threads', '1', outp]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            frame(c, fi)
            pr.stdin.write(surf.makeImageSnapshot().tobytes())
        pr.stdin.close()
        pr.wait()


if __name__ == '__main__':
    main()
