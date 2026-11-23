"""Render frames -> H.264 video (no audio). Usage:
   python3 render.py still T1 T2 ...      (writes PNGs to ../frames)
   python3 render.py video START END OUT  (frame range, raw pipe to ffmpeg)
"""
import sys, os, subprocess, math
import skia
from gfx import *
import scenes
from scenes import TL, SHOTS, shot_at
from rig import SUB_COL

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOTAL = TL['total']
NF = TL['nframes']
SUBS = TL['subs']

_wrap_cache = {}


def wrap(text, f, maxw):
    words = text.split()
    lines = []
    cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if f.measureText(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # balance two lines
    if len(lines) == 2:
        best = None
        for i in range(1, len(words)):
            a, b = ' '.join(words[:i]), ' '.join(words[i:])
            wa, wb = f.measureText(a), f.measureText(b)
            if max(wa, wb) <= maxw:
                score = abs(wa - wb)
                if best is None or score < best[0]:
                    best = (score, [a, b])
        if best:
            lines = best[1]
    return lines


def sub_layout(text):
    if text not in _wrap_cache:
        size = 56
        while True:
            f = font(FONT_SUB, size)
            lines = wrap(text, f, 1540)
            if len(lines) <= 2 or size <= 40:
                break
            size -= 2
        _wrap_cache[text] = (size, lines)
    return _wrap_cache[text]


def draw_subs(c, T):
    for s in SUBS:
        if s['start'] <= T < s['end']:
            size, lines = sub_layout(s['text'])
            f = font(FONT_SUB, size)
            col = SUB_COL.get(s['speaker'], '#ffffff')
            a = min(ramp(T, s['start'], s['start'] + 0.08), 1 - ramp(T, s['end'] - 0.06, s['end']))
            lh = size * 1.22
            y0 = H - 64 - (len(lines) - 1) * lh
            for i, ln in enumerate(lines):
                y = y0 + i * lh
                # soft shadow
                draw_text(c, ln, W / 2 + 3, y + 4, f, '#000000', 'center', '#000000', 12, a * 0.35, a * 0.35)
                draw_text(c, ln, W / 2, y, f, col, 'center', '#0b0b0b', 9, a, a)
            break


def draw_label(c, T):
    if T < 4.0:
        a = 1 - ramp(T, 3.5, 4.0)
        f = font(FONT_UI, 26)
        txt = 'Based on a true story · dramatised'
        w = f.measureText(txt)
        draw(c, rrect(36, 34, w + 36, 46, 23), '#000000', None, 0, fa=0.38 * a)
        draw_text(c, txt, 54, 66, f, '#f4f1ea', 'left', a=0.92 * a)


def render_frame(c, fi):
    T = fi / FPS
    a, b, fn = shot_at(T)
    b = min(b, TOTAL)
    c.save()
    c.clear(hexc('#000000'))
    fn(c, T - a, b - a, T)
    c.restore()
    draw_label(c, T)
    draw_subs(c, T)


def main():
    mode = sys.argv[1]
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    if mode == 'still':
        od = os.path.join(OUT, 'frames')
        os.makedirs(od, exist_ok=True)
        for t in sys.argv[2:]:
            fi = int(round(float(t) * FPS))
            render_frame(c, fi)
            p = os.path.join(od, 'f_%06.2f.png' % (fi / FPS))
            surf.makeImageSnapshot().save(p)
            print(p)
    elif mode == 'video':
        f0, f1, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', '%dx%d' % (W, H), '-r', str(FPS),
               '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-threads', '1', outp]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            render_frame(c, fi)
            pr.stdin.write(surf.makeImageSnapshot().tobytes())
            if fi % 300 == 0:
                print('frame', fi, flush=True)
        pr.stdin.close()
        pr.wait()


if __name__ == '__main__':
    main()
