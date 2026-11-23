"""Flat, lit, layered sets and props. All coordinates are world px (1920x1080 frame at zoom 1)."""
import math
import skia
from gfx import *


class layer:
    def __init__(self, c, cam, depth):
        self.c, self.cam, self.depth = c, cam, depth

    def __enter__(self):
        self.c.save()
        if self.cam is not None:
            self.cam.apply(self.c, self.depth)
        return self.c

    def __exit__(self, *a):
        self.c.restore()


def sky(c, cols, pos=None):
    c.drawRect(skia.Rect.MakeWH(W, H), fillp(None, 1, shader=lin(0, 0, 0, H, cols, pos)))


def cloud(c, x, y, s, col='#ffffff', a=0.9):
    p = skia.Path()
    for dx, dy, r in ((0, 0, 40), (45, -18, 48), (95, -5, 38), (130, 8, 28), (-38, 10, 26)):
        p.addCircle(x + dx * s, y + dy * s, r * s)
    p2 = skia.Path()
    p2.addRect(skia.Rect.MakeLTRB(x - 70 * s, y + 18 * s, x + 170 * s, y + 60 * s))
    p = skia.Op(p, p2, skia.PathOp.kDifference_PathOp) or p
    c.drawPath(p, fillp(col, a))
    c.drawPath(p, strokep(INK, 2.5, 0.35))


def clouds(c, cam, T, y=180, n=6, speed=8, depth=0.08, col='#ffffff', a=0.85, seed=0, span=4200):
    with layer(c, cam, depth):
        for i in range(n):
            x = (-800 + i * span / n + T * speed * (0.7 + 0.5 * hash01(i, seed))) % span - 900
            cloud(c, x, y + 70 * hash01(i, seed + 3), 0.8 + 0.7 * hash01(i, seed + 5), col, a)


def ridge(c, x0, x1, base, amp, seed, freq=1.0, col='#6f9a52', outline=True, bottom=2000, sw=3.0):
    pts = [(x0, bottom)]
    n = 60
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = base - amp * (0.55 * math.sin(x * 0.0021 * freq + seed) + 0.3 * math.sin(x * 0.0057 * freq + seed * 2.3)
                          + 0.15 * math.sin(x * 0.013 * freq + seed * 4.1))
        pts.append((x, y))
    pts.append((x1, bottom))
    p = poly(pts)
    c.drawPath(p, fillp(col))
    if outline:
        c.drawPath(p, strokep(INK, sw, 0.55))
    return p


def ridge_y(x, base, amp, seed, freq=1.0):
    return base - amp * (0.55 * math.sin(x * 0.0021 * freq + seed) + 0.3 * math.sin(x * 0.0057 * freq + seed * 2.3)
                         + 0.15 * math.sin(x * 0.013 * freq + seed * 4.1))


def cypress(c, x, y, h, col='#2f5a35', T=0.0, seed=0):
    sway = math.sin(T * 1.3 + seed) * h * 0.015
    p = skia.Path()
    p.moveTo(x, y)
    p.cubicTo(x - h * 0.16, y - h * 0.3, x - h * 0.12 + sway, y - h * 0.8, x + sway * 1.5, y - h)
    p.cubicTo(x + h * 0.12 + sway, y - h * 0.8, x + h * 0.16, y - h * 0.3, x, y)
    p.close()
    draw(c, p, col, INK, max(2, h * 0.012))
    c.drawPath(smooth_path([(x - h * 0.05, y - h * 0.15), (x - h * 0.07 + sway, y - h * 0.5), (x + sway, y - h * 0.85)], False),
               strokep(shade(col, 0.25), max(1.5, h * 0.015), 0.7))


def bush(c, x, y, r, col='#4f8a3d', seed=0, T=0.0):
    p = skia.Path()
    for k in range(5):
        a = k / 5 * math.pi
        p.addCircle(x + math.cos(a + math.pi) * r * 0.9, y - math.sin(a) * r * 0.55 - r * 0.2, r * (0.55 + 0.2 * hash01(k, seed)))
    c.drawPath(p, fillp(col))
    c.drawPath(p, strokep(INK, max(2, r * 0.05), 0.6))
    c.drawCircle(x - r * 0.3, y - r * 0.7, r * 0.25, fillp(shade(col, 0.2), 0.7))


def tree(c, x, y, h, col='#4f8a3d', T=0.0, seed=0):
    c.drawLine(x, y, x, y - h * 0.45, strokep('#5b3d26', h * 0.06))
    c.drawLine(x, y, x, y - h * 0.45, strokep(INK, 2.5, 0.6))
    sway = math.sin(T * 1.2 + seed) * h * 0.02
    p = skia.Path()
    for k in range(6):
        a = k / 6 * 2 * math.pi
        p.addCircle(x + sway + math.cos(a) * h * 0.2, y - h * 0.68 + math.sin(a) * h * 0.14, h * 0.2)
    p.addCircle(x + sway, y - h * 0.7, h * 0.24)
    c.drawPath(p, fillp(col))
    c.drawPath(p, strokep(INK, max(2, h * 0.012), 0.6))
    c.drawCircle(x + sway - h * 0.1, y - h * 0.82, h * 0.08, fillp(shade(col, 0.22), 0.8))


def house(c, x, y, w, h, wall='#e8d3a8', roof='#b5583a', seed=0, win=2, sw=2.5):
    draw(c, rect(x, y - h, w, h), wall, INK, sw)
    rp = poly([(x - w * 0.08, y - h), (x + w * 0.5, y - h - h * 0.35), (x + w * 1.08, y - h)])
    draw(c, rp, roof, INK, sw)
    for k in range(win):
        wx = x + w * (0.2 + 0.6 * k / max(1, win - 1)) - w * 0.07 if win > 1 else x + w * 0.43
        draw(c, rect(wx, y - h * 0.72, w * 0.14, h * 0.25), '#3d3a3a', INK, sw * 0.6)
        c.drawRect(skia.Rect.MakeXYWH(wx - w * 0.03, y - h * 0.72, w * 0.03, h * 0.25), fillp('#5d7b5a'))
    if hash01(seed, 9) > 0.5:
        draw(c, rect(x + w * 0.4, y - h * 0.32, w * 0.18, h * 0.32), '#6e4726', INK, sw * 0.6)


def village(c, x0, base, scale=1.0, T=0.0):
    """Stone hill village cluster with a bell tower (Tuscan)."""
    cols = ['#e8d3a8', '#d9b98a', '#efe0bf', '#cfa77a', '#e3c79a']
    for i in range(14):
        hx = x0 + (i % 7) * 70 * scale + (i // 7) * 30 * scale
        hy = base - (i // 7) * 55 * scale - 20 * scale * math.sin(i * 1.7)
        house(c, hx, hy, 62 * scale, 48 * scale, cols[i % 5], '#b5583a', i, 2, 2)
    # bell tower
    tx = x0 + 240 * scale
    ty = base - 120 * scale
    draw(c, rect(tx, ty - 120 * scale, 38 * scale, 120 * scale), '#d6bd92', INK, 2.5)
    draw(c, rect(tx + 10 * scale, ty - 105 * scale, 18 * scale, 26 * scale), '#3d3a3a', INK, 1.5)
    draw(c, poly([(tx - 5 * scale, ty - 120 * scale), (tx + 19 * scale, ty - 150 * scale), (tx + 43 * scale, ty - 120 * scale)]),
         '#b5583a', INK, 2.5)


def boulder(c, x, y, w, h, col='#8a8f93', seed=0, sw=4.0, wet=0.0):
    n = 12
    pts = []
    for i in range(n):
        a = math.pi + i / (n - 1) * math.pi
        rr = 1 + 0.08 * math.sin(i * 2.3 + seed) + 0.05 * math.sin(i * 5.1 + seed)
        pts.append((x + math.cos(a) * w / 2 * rr, y + math.sin(a) * h * rr))
    pts.append((x + w / 2, y + h * 0.15))
    pts.append((x - w / 2, y + h * 0.15))
    p = smooth_path(pts, True, 0.6)
    c.drawPath(p, fillp(None, 1, shader=lin(x - w / 2, y - h, x + w / 2, y, [shade(col, 0.18), col, shade(col, -0.25)])))
    c.save()
    c.clipPath(p, doAntiAlias=True)
    c.drawOval(skia.Rect.MakeLTRB(x - w * 0.35, y - h * 0.95, x + w * 0.05, y - h * 0.6), fillp('#ffffff', 0.18))
    for k in range(4):
        cx = x + (hash01(k, seed) - 0.5) * w * 0.7
        cy = y - h * (0.2 + 0.5 * hash01(k, seed + 2))
        c.drawArc(skia.Rect.MakeXYWH(cx - 18, cy - 8, 36, 16), 200, 120, False, strokep(shade(col, -0.35), 2.2, 0.7))
    if wet:
        c.drawRect(skia.Rect.MakeLTRB(x - w, y - h * 0.18, x + w, y + h), fillp('#1d3a46', 0.25 * wet))
    c.restore()
    c.drawPath(p, strokep(INK, sw))
    return p


def pebbles(c, x0, x1, y0, y1, n, seed=0, cols=('#b9b2a5', '#9d9488', '#cfc6b6', '#8b8277')):
    for i in range(n):
        x = x0 + (x1 - x0) * hash01(i, seed)
        y = y0 + (y1 - y0) * hash01(i, seed + 1)
        r = 6 + 16 * hash01(i, seed + 2) * (0.6 + 0.6 * (y - y0) / max(1, y1 - y0))
        draw(c, oval(x, y, r * 1.5, r), cols[i % len(cols)], INK, 2.0, sa=0.7)


def water_band(c, x0, x1, y0, y1, T, flow=1.0, cols=('#3f8fb7', '#2f7aa3', '#245f86'), rows=12, speed=90, seed=0,
               a=1.0, ripple_a=0.55):
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fillp(None, a, shader=lin(0, y0, 0, y1, list(cols))))
    span = x1 - x0
    for r in range(rows):
        f = (r + 0.5) / rows
        y = y0 + (y1 - y0) * (f ** 1.2)
        L = 30 + 70 * f
        gap = 140 + 120 * f
        sp = speed * (0.5 + f) * flow
        n = int(span / gap) + 2
        for k in range(n):
            ph = hash01(k + r * 31, seed)
            x = x0 + ((k * gap + ph * gap + T * sp) % (n * gap)) - gap * 0.5
            wob = math.sin(T * 3 + k + r) * 2
            c.drawLine(x, y + wob, x + L, y + wob, strokep('#ffffff', 2.0 + 2.2 * f, ripple_a * (0.5 + 0.5 * ph)))
    # sparkles
    for k in range(10):
        ph = (T * 0.8 + hash01(k, seed + 7)) % 1.0
        sx = x0 + span * hash01(k, seed + 8)
        sy = y0 + (y1 - y0) * hash01(k, seed + 9) * 0.8
        s = math.sin(ph * math.pi) * 6
        if s > 0.5:
            c.drawLine(sx - s, sy, sx + s, sy, strokep('#ffffff', 2, 0.8))
            c.drawLine(sx, sy - s, sx, sy + s, strokep('#ffffff', 2, 0.8))


def foam(c, x, y, w, T, a=0.8):
    for k in range(5):
        ph = T * 2 + k
        c.drawOval(skia.Rect.MakeXYWH(x - w / 2 + k * w / 5 + math.sin(ph) * 6, y - 6 + math.cos(ph) * 3, w / 4, 12),
                   fillp('#ffffff', a * 0.7))


def splash(c, x, y, s, age, dur=0.7):
    """droplet burst; age in seconds"""
    if age < 0 or age > dur:
        return
    u = age / dur
    for k in range(10):
        a = math.pi * (0.1 + 0.8 * k / 9)
        v = 260 * s * (0.6 + 0.4 * hash01(k, 3))
        px = x + math.cos(a) * v * u * (1 if k % 2 else -1) * 0.8
        py = y - math.sin(a) * v * u + 600 * s * u * u
        r = 7 * s * (1 - u * 0.6)
        c.drawCircle(px, py, r, fillp('#e9f7ff', 0.9 * (1 - u)))
        c.drawCircle(px, py, r, strokep(INK, 1.5, 0.5 * (1 - u)))
    # ring ripple
    c.drawOval(skia.Rect.MakeXYWH(x - 60 * s * (0.4 + u), y - 12 * s * (0.4 + u), 120 * s * (0.4 + u), 24 * s * (0.4 + u)),
               strokep('#ffffff', 3, 0.8 * (1 - u)))


def steam(c, x, y, T, s=1.0, n=5, a=0.5, seed=0):
    for k in range(n):
        ph = (T * 0.45 + k / n + hash01(k, seed)) % 1.0
        px = x + math.sin(ph * 6 + k) * 22 * s + (k - n / 2) * 10 * s
        py = y - ph * 260 * s
        r = (14 + 30 * ph) * s
        c.drawCircle(px, py, r, fillp('#ffffff', a * math.sin(ph * math.pi) * 0.6))


def glow(c, x, y, r, col='#ffd98a', a=0.5):
    c.drawCircle(x, y, r, fillp(None, 1, shader=rad(x, y, r, [hexc(col, a), hexc(col, a * 0.4), hexc(col, 0)], [0, 0.45, 1])))


def lamp_pendant(c, x, y_top, y, T, col='#e9b44c'):
    sway = math.sin(T * 0.8) * 4
    glow(c, x + sway, y + 30, 260, '#ffcf7a', 0.45)
    c.drawLine(x, y_top, x + sway, y, strokep(INK, 3))
    p = poly([(x + sway - 50, y + 40), (x + sway - 18, y), (x + sway + 18, y), (x + sway + 50, y + 40)])
    draw(c, p, col, INK, 4)
    c.drawOval(skia.Rect.MakeXYWH(x + sway - 16, y + 34, 32, 16), fillp('#fff4cf'))


# ---------------------------------------------------------------- the ring
def gold_ring(c, x, y, r, angle=0.0, tilt=0.35, sw=None, sparkle=0.0):
    """plain gold band seen at an angle. tilt = minor/major ratio."""
    sw = sw if sw is not None else max(1.5, r * 0.08)
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    th = r * 0.32
    ry = max(r * tilt, th * 0.6)
    outer = oval(0, 0, r, ry)
    inner = oval(0, -th * 0.15, r - th, max(ry - th * 0.9, 1))
    band = skia.Op(outer, inner, skia.PathOp.kDifference_PathOp)
    c.drawPath(band, fillp(None, 1, shader=lin(-r, -ry, r, ry, ['#fff1b0', '#f0c43c', '#b8861c', '#f7d76a', '#9a6c12'],
                                              [0, 0.3, 0.55, 0.75, 1])))
    c.drawPath(band, strokep('#4a330c', sw))
    c.drawArc(skia.Rect.MakeLTRB(-r * 0.85, -ry * 0.92, r * 0.2, ry * 0.4), 190, 60, False, strokep('#ffffff', sw * 1.2, 0.85))
    c.restore()
    if sparkle > 0:
        sx, sy = x - r * 0.5, y - r * tilt * 0.8
        s = r * 0.9 * sparkle
        for ang in (0, 90):
            c.save()
            c.translate(sx, sy)
            c.rotate(ang + 20)
            p = poly([(-s, 0), (-s * 0.12, -s * 0.12), (0, -s), (s * 0.12, -s * 0.12), (s, 0), (s * 0.12, s * 0.12), (0, s),
                      (-s * 0.12, s * 0.12)])
            c.drawPath(p, fillp('#ffffff', 0.95))
            c.restore()


def ring_photo(c, x, y, w, h, T=0.0):
    """The photo in the text: fingers hold a gold ring above a sandy riverbed."""
    c.save()
    c.clipPath(rrect(x, y, w, h, w * 0.04), doAntiAlias=True)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fillp(None, 1, shader=lin(x, y, x, y + h, ['#cdb27c', '#b89a63', '#a3854f'])))
    # water caustics
    for k in range(18):
        cx = x + w * hash01(k, 1)
        cy = y + h * hash01(k, 2)
        c.drawOval(skia.Rect.MakeXYWH(cx, cy, w * 0.16, h * 0.05), strokep('#f3e2b0', w * 0.008, 0.6))
    for k in range(14):
        draw(c, oval(x + w * hash01(k, 4), y + h * (0.5 + 0.5 * hash01(k, 5)), w * 0.03, w * 0.02),
             ['#8d8073', '#b3a898', '#6f6458'][k % 3], INK, w * 0.003)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h * 0.25), fillp(None, 1, shader=lin(x, y, x, y + h * 0.25,
                                                                                [hexc('#4fa0c0', 0.6), hexc('#4fa0c0', 0)])))
    # fingers (olive) from the top-right
    sk = '#d6a077'
    for k, (dx, dy) in enumerate(((0.62, 0.0), (0.72, 0.02))):
        p = rrect(x + w * dx, y - h * 0.1 + h * dy, w * 0.11, h * 0.52, w * 0.055)
        draw(c, p, sk, INK, w * 0.008)
    gold_ring(c, x + w * 0.62, y + h * 0.48, w * 0.15, -18, 0.62, w * 0.008)
    # thumb over the ring
    draw(c, rrect(x + w * 0.42, y + h * 0.33, w * 0.24, h * 0.12, h * 0.06), sk, INK, w * 0.008)
    c.restore()
    c.drawPath(rrect(x, y, w, h, w * 0.04), strokep(INK, max(2, w * 0.008)))


def phone(c, x, y, w, h, T, mode='lock', reveal=1.0, glow_a=1.0, typed=1.0, buzz=0.0):
    """Phone with screen. (x,y) top-left. mode lock|chat."""
    bx = math.sin(T * 90) * 4 * buzz
    c.save()
    c.translate(bx, 0)
    if glow_a > 0:
        glow(c, x + w / 2, y + h / 2, w * 1.3, '#d9ecff', 0.35 * glow_a)
    draw(c, rrect(x, y, w, h, w * 0.12), '#1c1d22', INK, max(3, w * 0.02))
    sx, sy, sw_, sh = x + w * 0.05, y + w * 0.05, w * 0.9, h - w * 0.1
    scr = rrect(sx, sy, sw_, sh, w * 0.09)
    c.save()
    c.clipPath(scr, doAntiAlias=True)
    if mode == 'lock':
        c.drawRect(skia.Rect.MakeXYWH(sx, sy, sw_, sh), fillp(None, 1, shader=lin(sx, sy, sx, sy + sh, ['#2a3c66', '#5a4a7a', '#c98a6a'])))
        f = font(FONT_UI, sw_ * 0.2)
        draw_text(c, '19:42', sx + sw_ / 2, sy + sh * 0.2, f, '#ffffff', 'center')
        # notification card
        ny = sy + sh * 0.33
        e = ease_out(reveal)
        nyy = ny - (1 - e) * sh * 0.1
        c.saveLayerAlpha(skia.Rect.MakeXYWH(sx, sy, sw_, sh), int(255 * e))
        draw(c, rrect(sx + sw_ * 0.05, nyy, sw_ * 0.9, sh * 0.5, sw_ * 0.06), '#f4f1ea', None, 0, fa=0.96)
        f3 = font(FONT_SUB, sw_ * 0.06)
        draw_text(c, '+39 3•• ••• ••••', sx + sw_ * 0.1, nyy + sh * 0.05, f3, '#222222')
        draw_text(c, 'now', sx + sw_ * 0.9, nyy + sh * 0.05, font(FONT_UI, sw_ * 0.05), '#777777', 'right')
        draw_text(c, 'Photo', sx + sw_ * 0.1, nyy + sh * 0.09, font(FONT_UI, sw_ * 0.05), '#555555')
        ring_photo(c, sx + sw_ * 0.1, nyy + sh * 0.11, sw_ * 0.8, sh * 0.36, T)
        c.restore()
    else:
        c.drawRect(skia.Rect.MakeXYWH(sx, sy, sw_, sh), fillp('#ece6dc'))
        # pattern
        for k in range(30):
            c.drawCircle(sx + sw_ * hash01(k, 3), sy + sh * hash01(k, 4), sw_ * 0.012, fillp('#d8d0c2'))
        draw(c, rect(sx, sy, sw_, sh * 0.11), '#3c6e5a', None, 0)
        draw(c, oval(sx + sw_ * 0.17, sy + sh * 0.065, sw_ * 0.06, sw_ * 0.06), '#b9c7c0', None, 0)
        draw_text(c, '+39 3•• ••• ••••', sx + sw_ * 0.27, sy + sh * 0.075, font(FONT_SUB, sw_ * 0.058), '#ffffff')
        # photo bubble
        e = ease_out(reveal)
        if e > 0:
            c.saveLayerAlpha(skia.Rect.MakeXYWH(sx, sy, sw_, sh), int(255 * e))
            by = sy + sh * 0.15 + (1 - e) * 30
            draw(c, rrect(sx + sw_ * 0.05, by, sw_ * 0.78, sh * 0.42, sw_ * 0.05), '#ffffff', None, 0)
            ring_photo(c, sx + sw_ * 0.08, by + sw_ * 0.03, sw_ * 0.72, sh * 0.37, T)
            c.restore()
        if typed > 0:
            msg = 'Hi Sméagol... look what we found.'
            n = int(round(len(msg) * clamp(typed)))
            by = sy + sh * 0.6
            f = font(FONT_UI, sw_ * 0.072)
            lines = ['Hi Sméagol...', 'look what we found.']
            draw(c, rrect(sx + sw_ * 0.05, by, sw_ * 0.8, sh * 0.15, sw_ * 0.05), '#ffffff', None, 0)
            shown = msg[:n]
            l1 = shown[:len(lines[0])]
            l2 = shown[len(lines[0]) + 1:] if n > len(lines[0]) else ''
            draw_text(c, l1, sx + sw_ * 0.1, by + sh * 0.06, f, '#202020')
            draw_text(c, l2, sx + sw_ * 0.1, by + sh * 0.115, f, '#202020')
            draw_text(c, '19:42', sx + sw_ * 0.8, by + sh * 0.14, font(FONT_UI, sw_ * 0.04), '#888888', 'right')
    # screen glare
    c.drawPath(poly([(sx, sy), (sx + sw_ * 0.4, sy), (sx, sy + sh * 0.3)]), fillp('#ffffff', 0.06))
    c.restore()
    c.drawPath(scr, strokep('#000000', 2))
    # buzz lines
    if buzz > 0.05:
        for s in (-1, 1):
            for k in range(3):
                xx = x + w / 2 + s * (w / 2 + 20 + k * 16)
                c.drawLine(xx, y + h * 0.35, xx, y + h * 0.65 - k * 10, strokep(INK, 4, buzz))
    c.restore()


# ---------------------------------------------------------------- kitchen (Tuscan rental, evening)
def stone_wall(c, x0, y0, x1, y1, base='#cfa679', seed=0, rowh=60):
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fillp(base))
    r = 0
    y = y0
    while y < y1:
        x = x0 - (r % 2) * 60
        while x < x1:
            w = 90 + 60 * hash01(int(x) + r * 17, seed)
            col = shade(base, (hash01(int(x) * 3 + r, seed) - 0.5) * 0.12)
            p = rrect(x + 3, y + 3, w - 6, rowh - 6, 12)
            c.drawPath(p, fillp(col))
            c.drawPath(p, strokep(shade(base, -0.3), 2.2, 0.8))
            x += w
        y += rowh
        r += 1


def tiles(c, x0, y0, x1, y1, a='#b4603f', b='#9b4f33', n=14, rows=5):
    rh = (y1 - y0) / rows
    for r in range(rows):
        tw = (x1 - x0) / n
        for k in range(n + 1):
            col = a if (k + r) % 2 == 0 else b
            c.drawRect(skia.Rect.MakeXYWH(x0 + k * tw - (r % 2) * tw * 0.5, y0 + r * rh, tw, rh), fillp(col))
        c.drawLine(x0, y0 + r * rh, x1, y0 + r * rh, strokep(shade(b, -0.35), 2.2, 0.8))


def window_view(c, x, y, w, h, T, kind='dusk', shutters='#6f8f7d'):
    c.save()
    c.clipPath(rect(x, y, w, h))
    if kind == 'dusk':
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fillp(None, 1, shader=lin(x, y, x, y + h, ['#6b4d8a', '#e08a7a', '#f6c48a'])))
        glow(c, x + w * 0.7, y + h * 0.62, w * 0.4, '#fff0b0', 0.7)
        ridge(c, x - 50, x + w + 50, y + h * 0.7, h * 0.12, 1.3, 2.0, '#7a5a7a', True, y + h + 50, 2)
        ridge(c, x - 50, x + w + 50, y + h * 0.85, h * 0.1, 4.0, 2.4, '#4f3e5a', True, y + h + 50, 2)
        for k in range(4):
            cypress(c, x + w * (0.15 + 0.22 * k), y + h * 0.9, h * (0.3 + 0.1 * hash01(k, 3)), '#2c2a3a', T, k)
    elif kind == 'night':
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fillp(None, 1, shader=lin(x, y, x, y + h, ['#121a35', '#2a3566'])))
        for k in range(14):
            c.drawCircle(x + w * hash01(k, 2), y + h * 0.6 * hash01(k, 3), 2, fillp('#ffffff', 0.5 + 0.5 * math.sin(T * 2 + k)))
        ridge(c, x - 50, x + w + 50, y + h * 0.85, h * 0.08, 1, 2.0, '#0c1024', False, y + h + 50)
    elif kind == 'day':
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fillp(None, 1, shader=lin(x, y, x, y + h, ['#9ccbe4', '#dcecf0'])))
        ridge(c, x - 50, x + w + 50, y + h * 0.8, h * 0.1, 2, 2.0, '#86a86a', True, y + h + 50, 2)
    c.restore()
    # frame + mullions
    draw(c, rect(x, y, w, h), None, '#f1e8d6', 14)
    c.drawLine(x + w / 2, y, x + w / 2, y + h, strokep('#f1e8d6', 10))
    c.drawLine(x, y + h * 0.45, x + w, y + h * 0.45, strokep('#f1e8d6', 10))
    draw(c, rect(x - 7, y - 7, w + 14, h + 14), None, INK, 4)
    draw(c, rect(x - 20, y + h + 4, w + 40, 22), '#e8dcc4', INK, 4)
    if shutters:
        for s in (-1, 1):
            sx = x - 110 if s < 0 else x + w + 14
            draw(c, rect(sx, y - 10, 96, h + 20), shutters, INK, 4)
            for k in range(1, 12):
                c.drawLine(sx + 8, y - 10 + k * (h + 20) / 12, sx + 88, y - 10 + k * (h + 20) / 12, strokep(shade(shutters, -0.3), 2.5))


def pot(c, x, y, w, h, col='#b9bec4', T=0.0, bubbling=0.0):
    """y = bottom"""
    draw(c, rrect(x - w / 2, y - h, w, h, 14), None, None, 0)
    c.drawPath(rrect(x - w / 2, y - h, w, h, 14), fillp(None, 1, shader=lin(x - w / 2, 0, x + w / 2, 0, [shade(col, 0.3), col, shade(col, -0.3)])))
    c.drawPath(rrect(x - w / 2, y - h, w, h, 14), strokep(INK, 4.5))
    draw(c, rrect(x - w / 2 - 10, y - h - 8, w + 20, 16, 8), shade(col, 0.1), INK, 4.5)
    for s in (-1, 1):
        draw(c, rrect(x + s * (w / 2 + 6) - 14, y - h + 18, 28, 12, 6), '#333333', INK, 3)
    if bubbling > 0:
        for k in range(6):
            ph = (T * 2.5 + hash01(k, 4)) % 1
            bx = x - w * 0.35 + w * 0.7 * hash01(k, 5)
            r = 8 + 10 * ph
            c.drawCircle(bx, y - h - 8 - ph * 26 * bubbling, r * bubbling, fillp('#fff6e0', 0.9 * (1 - ph)))
            c.drawCircle(bx, y - h - 8 - ph * 26 * bubbling, r * bubbling, strokep(INK, 2, 0.6 * (1 - ph)))


def set_kitchen(c, cam, T, night=False, phone_on=False, phone_buzz=0.0, bubbling=0.0, steam_a=0.5):
    with layer(c, cam, 0.92):
        stone_wall(c, -400, -200, 2400, 950, '#cfa679', 1)
        # lower cupboards left of the stove
        draw(c, rect(-300, 640, 1100, 300), '#8a5a34', INK, 5)
        for k in range(4):
            draw(c, rect(-280 + k * 270, 670, 245, 240), '#9c6a40', INK, 4)
            c.drawCircle(-280 + k * 270 + 220, 790, 7, fillp('#e2c27a'))
        draw(c, rect(-310, 620, 1110, 26), '#c9a46c', INK, 5)
        window_view(c, 1180, 150, 380, 330, T, 'dusk')
        # window light bands on wall
        for k in range(3):
            c.drawPath(poly([(1180 - 40 * k - 160, 720), (1180 - 40 * k - 60, 720), (1220 + 100 * k, 480), (1180 + 100 * k, 480)]),
                       fillp('#ffd9a0', 0.08))
        # shelf with jars
        draw(c, rect(260, 300, 460, 22), '#7a4e2c', INK, 4)
        for k, (lab, col) in enumerate((('PASTA', '#f2e3b8'), ('SALE', '#e8eef0'), ('CAFFÈ', '#7a5a42'), ('', '#c7a24a'))):
            jx = 290 + k * 110
            draw(c, rrect(jx, 210, 80, 90, 12), col, INK, 4)
            draw(c, rect(jx - 4, 198, 88, 18), '#b7824a', INK, 3)
            if lab:
                draw(c, rect(jx + 8, 240, 64, 30), '#fbf7ee', INK, 2)
                draw_text(c, lab, jx + 40, 263, font(FONT_HAND, 17), INK, 'center')
        # hanging copper pans
        c.drawLine(760, 110, 1080, 110, strokep('#3a2a20', 7))
        for k in range(4):
            px = 790 + k * 82
            sw_ = math.sin(T * 1.1 + k) * 2
            c.drawLine(px, 110, px + sw_, 150, strokep(INK, 3))
            r = 34 + k * 4
            draw(c, oval(px + sw_, 150 + r + 40, r, r), '#c27a45', INK, 4)
            c.drawLine(px + sw_, 150, px + sw_, 150 + 40, strokep('#5a3a22', 8))
            c.drawArc(skia.Rect.MakeXYWH(px + sw_ - r * 0.6, 150 + 40 + r * 0.4, r * 0.8, r * 0.8), 180, 70, False,
                      strokep('#ffd9b0', 4, 0.7))
        # calendar / framed picture
        draw(c, rect(120, 160, 110, 140), '#fbf7ee', INK, 4)
        draw(c, rect(120, 160, 110, 34), '#c33631', INK, 4)
        draw_text(c, 'LUGLIO', 175, 186, font(FONT_HAND, 20), '#ffffff', 'center')
        for r in range(4):
            for k in range(5):
                c.drawRect(skia.Rect.MakeXYWH(130 + k * 19, 205 + r * 22, 12, 12), fillp('#c9c0b0'))
        # garlic string
        for k in range(4):
            draw(c, oval(1640, 230 + k * 50, 26, 24), '#f4ecdd', INK, 3)
        c.drawLine(1640, 190, 1640, 400, strokep('#8a6a3a', 3))
        # stove (cream range)
        draw(c, rect(800, 610, 360, 330), '#efe4c8', INK, 5)
        draw(c, rect(830, 700, 300, 170), '#e2d4b0', INK, 4)
        c.drawLine(850, 690, 1110, 690, strokep('#888888', 6))
        for k in range(4):
            draw(c, oval(850 + k * 85, 650, 14, 14), '#3a3a3a', INK, 3)
        draw(c, rect(780, 590, 400, 24), '#3a3a3a', INK, 4)
        # counter with cupboard
        draw(c, rect(1180, 640, 700, 300), '#8a5a34', INK, 5)
        for k in range(3):
            draw(c, rect(1205 + k * 225, 670, 200, 240), '#9c6a40', INK, 4)
            c.drawCircle(1215 + k * 225 + 180, 790, 7, fillp('#e2c27a'))
        draw(c, rect(1170, 620, 720, 26), '#c9a46c', INK, 5)
        # chopping board, tomatoes, bottle
        draw(c, rrect(1560, 600, 200, 22, 8), '#d9a868', INK, 3)
        for k in range(3):
            draw(c, oval(1590 + k * 40, 588, 18, 16), '#d9432f', INK, 3)
        draw(c, rrect(1800, 470, 46, 150, 12), '#4d7a3a', INK, 4)
        draw(c, rect(1812, 440, 22, 34), '#2a2a2a', INK, 3)
        # phone on counter
        if phone_on is not None:
            bx = math.sin(T * 90) * 3 * phone_buzz
            if phone_on:
                glow(c, 1390 + bx, 600, 160, '#d9ecff', 0.45)
            draw(c, poly([(1330 + bx, 618), (1450 + bx, 618), (1430 + bx, 600), (1350 + bx, 600)]),
                 '#a9d0ff' if phone_on else '#1c1d22', INK, 4)
            if phone_buzz > 0.05:
                for s in (-1, 1):
                    for k in range(2):
                        xx = 1390 + s * (80 + k * 16)
                        c.drawLine(xx, 585, xx, 610, strokep(INK, 4, phone_buzz))
        lamp_pendant(c, 980, -200, 120, T)
        # floor
        tiles(c, -400, 940, 2400, 1300, n=22, rows=4)
    with layer(c, cam, 0.92):
        pot(c, 960, 590, 170, 110, '#b9bec4', T, bubbling)
        steam(c, 960, 480, T, 1.1, 6, steam_a)


# ---------------------------------------------------------------- river (Bagni di Lucca)
def set_river_bg(c, cam, T, water_y=640, near_y=860, village_x=1100, haze=True):
    sky(c, ['#7fbde0', '#bfe0ef', '#e9f3f0'], [0, 0.55, 1])
    with layer(c, cam, 0.05):
        glow(c, 1600, 120, 260, '#fff6c8', 0.6)
    clouds(c, cam, T, 120, 6, 10, 0.08)
    with layer(c, cam, 0.18):
        ridge(c, -1500, 4500, 400, 90, 1.0, 0.8, '#8fb07a', True, 1500, 2.5)
        village(c, village_x, 380, 1.0, T)
        c.drawRect(skia.Rect.MakeLTRB(-1500, 300, 4500, 1500), fillp('#dfeef2', 0.25))
    with layer(c, cam, 0.35):
        ridge(c, -1500, 4500, 500, 70, 3.1, 1.3, '#6c9a4f', True, 1500, 3)
        for k in range(16):
            x = -1200 + k * 340 + 80 * hash01(k, 2)
            y = ridge_y(x, 500, 70, 3.1, 1.3) + 30
            if k % 3 == 0:
                cypress(c, x, y + 20, 150, '#2f5a35', T, k)
            else:
                tree(c, x, y + 30, 130, '#4f8a3d', T, k)
        c.drawRect(skia.Rect.MakeLTRB(-1500, 380, 4500, 1500), fillp('#e6f2ef', 0.12))
    with layer(c, cam, 0.65):
        # far bank
        c.drawRect(skia.Rect.MakeLTRB(-1500, water_y - 70, 4500, water_y + 10), fillp('#9a9a7e'))
        ridge(c, -1500, 4500, water_y - 60, 18, 7, 3.0, '#5f8f45', True, water_y + 20, 2.5)
        pebbles(c, -1500, 4500, water_y - 30, water_y + 5, 70, 11)
        for k in range(12):
            bush(c, -1200 + k * 470, water_y - 50, 46, '#4f8a3d', k, T)


def set_river_water(c, cam, T, water_y=640, near_y=860, depth=0.85, flow=1.0):
    with layer(c, cam, depth):
        water_band(c, -1500, 4500, water_y, near_y, T, flow, ('#5aa7c9', '#3b8bb3', '#2e7aa2'), 12, 90)


def set_river_near(c, cam, T, near_y=860, depth=1.0):
    with layer(c, cam, depth):
        c.drawRect(skia.Rect.MakeLTRB(-1500, near_y, 4500, 1600), fillp(None, 1, shader=lin(0, near_y, 0, 1200, ['#c9bda6', '#b3a68d'])))
        c.drawLine(-1500, near_y, 4500, near_y, strokep(INK, 4, 0.8))
        for k in range(40):
            x = -1500 + k * 150
            foam(c, x + 40 * math.sin(k), near_y - 4, 70, T + k, 0.7)
        pebbles(c, -1500, 4500, near_y + 30, 1150, 120, 5)


def fg_rocks(c, cam, T, depth=1.35, side='both', y=1080):
    with layer(c, cam, depth):
        if side in ('both', 'left'):
            boulder(c, -60, y + 60, 460, 200, '#7f7a70', 3, 6)
            for k in range(6):
                c.drawLine(140 + k * 22, y - 40, 120 + k * 28 + math.sin(T * 2 + k) * 8, y - 160 - k * 10, strokep('#4f7a32', 8))
        if side in ('both', 'right'):
            boulder(c, 2000, y + 70, 520, 230, '#8a8478', 5, 6)


# ---------------------------------------------------------------- underwater
def set_underwater(c, cam, T, sand_y=840, murk=0.0, rays=True, current=1.0, boulders=True):
    sky(c, ['#2f8fa8', '#1d6884', '#0e3b52'], [0, 0.5, 1])
    with layer(c, cam, 0.15):
        if rays:
            for k in range(6):
                x = -200 + k * 420 + 80 * math.sin(T * 0.4 + k)
                p = poly([(x, -100), (x + 120, -100), (x + 420, 1300), (x + 200, 1300)])
                c.drawPath(p, fillp('#bff3ff', 0.08 + 0.03 * math.sin(T + k)))
    with layer(c, cam, 0.4):
        ridge(c, -1500, 4500, sand_y - 140, 60, 2, 1.5, '#2d5f6a', True, 1600, 2.5)
        for k in range(10):
            boulder(c, -1000 + k * 520, sand_y - 100, 240, 130, '#3f6670', k, 3)
    with layer(c, cam, 0.8):
        c.drawRect(skia.Rect.MakeLTRB(-1500, sand_y, 4500, 1700), fillp(None, 1, shader=lin(0, sand_y, 0, 1200, ['#b9a274', '#9c8457'])))
        ridge(c, -1500, 4500, sand_y + 10, 14, 5, 4, '#c4ad7c', True, 1700, 3)
        pebbles(c, -1500, 4500, sand_y + 40, 1150, 120, 21, ('#8d8073', '#6f7a78', '#a39a8a', '#5e6766'))
        # caustics on sand
        for k in range(40):
            x = -1500 + (k * 157 + T * 30) % 6000
            c.drawOval(skia.Rect.MakeXYWH(x, sand_y + 30 + (k % 5) * 40, 90, 16), strokep('#f2e4b6', 3, 0.35))
        # weeds
        for k in range(30):
            x = -1400 + k * 200 + 60 * hash01(k, 7)
            sw_ = math.sin(T * 1.6 * current + k) * 30 * current + 30 * current
            c.drawPath(smooth_path([(x, sand_y + 20), (x + sw_ * 0.4, sand_y - 60), (x + sw_, sand_y - 130)], False),
                       strokep('#3f7a4a', 9))
    if murk:
        c.drawRect(skia.Rect.MakeWH(W, H), fillp('#0b2c3c', murk))


def current_lines(c, cam, T, n=26, speed=900, a=0.35, depth=1.0, y0=-100, y1=1100, seed=0):
    with layer(c, cam, depth):
        for k in range(n):
            y = y0 + (y1 - y0) * hash01(k, seed)
            L = 120 + 200 * hash01(k, seed + 1)
            x = -1500 + (hash01(k, seed + 2) * 6000 + T * speed * (0.6 + 0.8 * hash01(k, seed + 3))) % 6000
            wob = math.sin(T * 4 + k) * 10
            c.drawPath(smooth_path([(x, y), (x + L * 0.5, y + wob), (x + L, y)], False), strokep('#d8f6ff', 3.5, a))


def bubbles(c, cam, T, x, y, n=8, a=0.7, depth=1.0, seed=0, spread=60):
    with layer(c, cam, depth):
        for k in range(n):
            ph = (T * 0.7 + hash01(k, seed)) % 1
            bx = x + math.sin(ph * 8 + k) * 12 + (hash01(k, seed + 1) - 0.5) * spread
            by = y - ph * 500
            r = 4 + 8 * hash01(k, seed + 2)
            c.drawCircle(bx, by, r, strokep('#e6fbff', 2.5, a * (1 - ph)))
            c.drawCircle(bx - r * 0.3, by - r * 0.3, r * 0.25, fillp('#ffffff', a * (1 - ph)))


def mask(c, x, y, u):
    """diving mask over a face; x,y head centre"""
    draw(c, rrect(x - 13 * u, y - 7 * u, 26 * u, 11 * u, 4 * u), '#9fdcef', INK, 1.2 * u, fa=0.55)
    c.drawLine(x - 15.5 * u, y - 2 * u, x + 15.5 * u, y - 2 * u, strokep('#222222', 1.6 * u))
    c.drawLine(x - 9 * u, y - 5 * u, x - 4 * u, y - 5 * u, strokep('#ffffff', 1.0 * u, 0.7))


# ---------------------------------------------------------------- terrace at dusk
def set_terrace(c, cam, T):
    sky(c, ['#48296a', '#9c4f7a', '#db747a', '#f0b789'], [0, 0.35, 0.65, 1])
    with layer(c, cam, 0.05):
        glow(c, 1400, 700, 420, '#ffe2a0', 0.6)
        c.drawCircle(1400, 700, 70, fillp('#ffe7b0'))
    clouds(c, cam, T, 160, 5, 6, 0.08, '#f6b8a8', 0.6, 3)
    with layer(c, cam, 0.2):
        ridge(c, -1500, 4500, 680, 80, 2.2, 1.0, '#6a3f6a', True, 1500, 2.5)
    with layer(c, cam, 0.4):
        ridge(c, -1500, 4500, 760, 60, 5.2, 1.6, '#4a2c55', True, 1500, 2.5)
        for k in range(10):
            x = -600 + k * 380
            cypress(c, x, ridge_y(x, 760, 60, 5.2, 1.6) + 40, 170, '#2b1f3a', T, k)
    with layer(c, cam, 1.0):
        # string lights
        p = smooth_path([(-300, 140), (500, 230), (1300, 150), (2200, 240)], False)
        c.drawPath(p, strokep(INK, 3))
        for k in range(16):
            x = -250 + k * 150
            y = 140 + 50 * math.sin((x + 300) / 800 * math.pi) + 20
            glow(c, x, y + 10, 40, '#ffd98a', 0.6 + 0.2 * math.sin(T * 3 + k))
            draw(c, oval(x, y + 10, 9, 12), '#ffe8a8', INK, 2)
        # terrace floor + balustrade
        c.drawRect(skia.Rect.MakeLTRB(-600, 900, 2600, 1400), fillp('#b97a5a'))
        tiles(c, -600, 900, 2600, 1300, '#b97a5a', '#a86b4e', 26, 4)
        draw(c, rect(-600, 760, 3200, 30), '#e7d6bb', INK, 4)
        for k in range(40):
            bx = -580 + k * 80
            p = smooth_path([(bx, 790), (bx + 22, 790), (bx + 30, 830), (bx + 20, 880), (bx + 26, 900), (bx - 4, 900),
                             (bx + 2, 880), (bx - 8, 830)], True, 0.3)
            draw(c, p, '#ead9be', INK, 3)
        draw(c, rect(-600, 895, 3200, 14), '#e7d6bb', INK, 4)
        # table with candle and glass
        draw(c, oval(1320, 820, 140, 26), '#f1e8d6', INK, 4)
        c.drawLine(1320, 840, 1320, 960, strokep(INK, 8))
        draw(c, rrect(1290, 760, 18, 50, 4), '#fff4dc', INK, 3)
        glow(c, 1299, 750, 70, '#ffcf7a', 0.7 + 0.15 * math.sin(T * 9))
        draw(c, oval(1299, 748, 5, 10), '#ffd36a', None, 0)
        draw(c, poly([(1350, 770), (1380, 770), (1374, 800), (1356, 800)]), '#7a1f33', INK, 3, fa=0.85)
        c.drawLine(1365, 800, 1365, 815, strokep(INK, 3))
        # potted geranium
        draw(c, poly([(250, 900), (370, 900), (350, 800), (270, 800)]), '#c0603a', INK, 4)
        bush(c, 310, 800, 70, '#3f7a3a', 3, T)
        for k in range(6):
            c.drawCircle(270 + k * 16, 740 + 10 * math.sin(k * 2), 10, fillp('#e8384f'))


# ---------------------------------------------------------------- Dún Laoghaire terrace house
def brick(c, x0, y0, x1, y1, base='#a5533e', seed=0):
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fillp(base))
    bh = 26
    r = 0
    y = y0
    while y < y1:
        off = (r % 2) * 40
        c.drawLine(x0, y, x1, y, strokep('#d8c3a8', 2.5, 0.8))
        x = x0 - off
        while x < x1:
            c.drawLine(x, y, x, y + bh, strokep('#d8c3a8', 2.5, 0.8))
            if hash01(int(x) + r * 13, seed) > 0.8:
                c.drawRect(skia.Rect.MakeXYWH(x + 2, y + 2, 76, bh - 4), fillp(shade(base, -0.1)))
            x += 80
        y += bh
        r += 1


def sash_window(c, x, y, w, h, T, lit=False):
    draw(c, rect(x - 14, y - 14, w + 28, h + 28), '#efe9dc', INK, 4)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fillp('#ffd98a' if lit else '#3c4a5a'))
    if not lit:
        c.drawPath(poly([(x, y + h * 0.6), (x + w * 0.5, y), (x + w * 0.7, y), (x, y + h)]), fillp('#ffffff', 0.12))
    for k in (1, 2):
        c.drawLine(x + w * k / 3, y, x + w * k / 3, y + h, strokep('#efe9dc', 6))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, strokep('#efe9dc', 10))
    draw(c, rect(x - 24, y + h + 12, w + 48, 18), '#efe9dc', INK, 4)


def set_door(c, cam, T, open_amt=0.0, interior_glow=0.0):
    sky(c, ['#9fb3c4', '#cdd8de', '#e7ebe8'])
    clouds(c, cam, T, 100, 6, 12, 0.08, '#f4f6f6', 0.9, 5)
    with layer(c, cam, 1.0):
        brick(c, -900, 60, 2900, 900, '#a5533e', 1)
        # neighbouring door (red) for terrace rhythm
        draw(c, rect(-560, 400, 220, 420), '#b73b33', INK, 5)
        # windows
        for x in (180, 1480):
            sash_window(c, x, 330, 260, 330, T, False)
        for x in (-400, 400, 1260, 2050):
            sash_window(c, x, 20, 220, 200, T, x == 400)
        # door surround
        dx, dy, dw, dh = 760, 400, 400, 440
        draw(c, rect(dx - 60, dy - 220, dw + 120, dh + 220), '#efe9dc', INK, 5)
        # fanlight
        c.save()
        fp = skia.Path()
        fp.addArc(skia.Rect.MakeXYWH(dx, dy - 200, dw, 400), 180, 180)
        fp.close()
        c.drawPath(fp, fillp('#ffd98a' if interior_glow > 0.1 else '#33404c'))
        c.clipPath(fp, doAntiAlias=True)
        for k in range(9):
            a = math.pi + k / 8 * math.pi
            c.drawLine(dx + dw / 2, dy, dx + dw / 2 + math.cos(a) * 240, dy + math.sin(a) * 240, strokep('#efe9dc', 6))
        c.restore()
        c.drawPath(fp, strokep(INK, 5))
        draw(c, oval(dx + dw / 2, dy, 50, 50), '#efe9dc', INK, 4)
        # pillars
        for s in (dx - 50, dx + dw + 10):
            draw(c, rect(s, dy, 40, dh), '#f4efe4', INK, 4)
        # interior
        c.drawRect(skia.Rect.MakeXYWH(dx, dy, dw, dh), fillp('#ffd38a'))
        glow(c, dx + dw / 2, dy + dh * 0.5, 300, '#fff1c0', 0.7)
        draw(c, rect(dx + 120, dy + 60, 120, 160), '#d9a85a', INK, 3)  # picture in hall
        # door leaf swings inward (shrinks to the left hinge)
        e = ease_io(open_amt)
        lw = dw * (1 - 0.82 * e)
        green = '#2f7d4f'
        draw(c, rect(dx, dy, lw, dh), shade(green, -0.15 * e), INK, 5)
        if lw > 60:
            for r in range(3):
                for k in range(2):
                    px = dx + lw * (0.12 + 0.44 * k)
                    py = dy + 30 + r * 135
                    draw(c, rect(px, py, lw * 0.32, 110), shade(green, 0.08), shade(green, -0.4), 3)
            # brass knocker + letterbox + handle
            kx = dx + lw * 0.5
            draw(c, rect(kx - lw * 0.18, dy + 228, lw * 0.36, 20), '#d8b04a', INK, 3)
            c.drawCircle(kx, dy + 170, 22, strokep('#d8b04a', 7))
            c.drawCircle(kx, dy + 170, 22, strokep(INK, 2))
            c.drawCircle(dx + lw * 0.85, dy + 260, 10, fillp('#d8b04a'))
        # number plaque
        draw(c, rrect(dx + dw + 70, dy + 80, 70, 50, 8), '#f4efe4', INK, 3)
        draw_text(c, '23', dx + dw + 105, dy + 116, font(FONT_HAND, 30), INK, 'center')
        # steps + railings + pavement
        draw(c, rect(dx - 100, dy + dh, dw + 200, 40), '#b9b6ae', INK, 4)
        draw(c, rect(dx - 150, dy + dh + 40, dw + 300, 40), '#a9a59c', INK, 4)
        c.drawRect(skia.Rect.MakeLTRB(-900, 920, 2900, 1500), fillp('#8f8c86'))
        for k in range(30):
            c.drawLine(-900 + k * 150, 920, -1000 + k * 150 - 60, 1500, strokep('#6d6a64', 3))
        c.drawLine(-900, 920, 2900, 920, strokep(INK, 4))
        for k in range(-12, 34):
            x = -900 + k * 60
            if dx - 160 < x < dx + dw + 160:
                continue
            c.drawLine(x, 920, x, 760, strokep('#1e2326', 6))
            c.drawPath(poly([(x - 8, 768), (x, 744), (x + 8, 768)]), fillp('#1e2326'))
        c.drawLine(-900, 790, dx - 160, 790, strokep('#1e2326', 6))
        c.drawLine(dx + dw + 160, 790, 2900, 790, strokep('#1e2326', 6))
        # potted plant by door
        draw(c, poly([(dx + dw + 120, 920), (dx + dw + 220, 920), (dx + dw + 205, 850), (dx + dw + 135, 850)]), '#5a5a5a', INK, 4)
        bush(c, dx + dw + 170, 850, 60, '#3f7a3a', 4, T)


# ---------------------------------------------------------------- map
EUROPE = {
    'ireland': [(-6.0, 52.2), (-6.4, 53.6), (-5.9, 54.6), (-7.3, 55.3), (-8.4, 55.2), (-10.0, 54.2), (-9.9, 53.4),
                (-10.3, 52.1), (-9.4, 51.5), (-7.6, 52.0)],
    'gb': [(-5.7, 50.0), (-3.0, 50.7), (0.3, 50.8), (1.4, 51.2), (1.7, 52.6), (0.3, 53.4), (-0.3, 54.5), (-1.6, 55.6),
           (-2.0, 56.1), (-2.8, 56.5), (-1.8, 57.6), (-3.2, 58.6), (-5.0, 58.6), (-6.2, 57.5), (-5.6, 56.3),
           (-6.0, 55.4), (-4.9, 54.8), (-3.0, 54.0), (-3.1, 53.3), (-4.6, 53.3), (-4.2, 52.3), (-5.2, 51.7), (-3.2, 51.4), (-4.5, 51.1)],
    'iberia': [(-9.0, 43.2), (-1.8, 43.4), (3.2, 42.3), (3.0, 41.8), (0.5, 40.6), (-0.3, 39.4), (0.2, 38.8), (-0.8, 37.6),
               (-2.2, 36.7), (-5.6, 36.0), (-6.4, 36.9), (-8.9, 37.0), (-8.8, 38.7), (-9.5, 39.0), (-8.6, 41.0), (-8.9, 42.2)],
    'mainland': [(-1.8, 43.4), (-1.2, 46.2), (-2.4, 47.1), (-4.6, 47.9), (-4.4, 48.6), (-1.6, 48.7), (-1.4, 49.7),
                 (1.6, 50.3), (2.6, 51.1), (4.0, 51.9), (4.7, 53.1), (7.0, 53.6), (8.6, 54.0), (8.5, 55.5), (8.1, 56.8),
                 (10.0, 57.6), (10.5, 56.3), (10.9, 54.4), (14.0, 54.0), (18.5, 54.7), (21.0, 55.5), (24.0, 57.5),
                 (28.0, 59.5), (32.0, 60.0), (32.0, 40.0), (26.0, 40.6), (23.0, 39.0), (22.4, 36.6), (21.0, 38.5),
                 (19.4, 41.8), (16.0, 43.5), (13.6, 45.7), (12.3, 45.4), (13.0, 44.0), (12.0, 44.3), (6.5, 43.1),
                 (3.2, 43.3), (3.0, 42.3)],
    'italy': [(7.5, 43.8), (8.8, 44.4), (10.2, 43.9), (10.5, 43.0), (11.1, 42.4), (12.6, 41.4), (14.0, 40.8), (15.6, 40.0),
              (16.0, 38.9), (15.7, 38.0), (16.1, 37.9), (17.1, 39.0), (17.2, 40.4), (18.5, 40.1), (18.0, 40.7), (16.0, 41.5),
              (14.2, 42.5), (13.6, 43.5), (12.3, 44.5), (12.3, 45.4), (13.6, 45.7), (13.7, 46.5), (12.0, 47.0), (10.4, 46.6),
              (8.4, 46.4), (7.0, 45.9), (6.7, 45.0), (7.5, 43.8)],
    'sicily': [(12.4, 37.8), (15.6, 38.3), (15.1, 36.7), (12.4, 37.8)],
    'sardinia': [(8.4, 41.0), (9.7, 41.0), (9.7, 39.2), (8.4, 39.0)],
    'corsica': [(8.6, 42.9), (9.5, 43.0), (9.4, 41.4), (8.6, 41.8)],
    'norway': [(5.0, 58.5), (8.0, 58.0), (11.0, 59.0), (11.5, 61.0), (13.0, 64.0), (5.0, 62.5)],
}


def map_xy(lon, lat):
    # simple equirectangular centred on Europe, scaled for 1920x1080 world
    x = 960 + (lon - 3.0) * 52
    y = 540 - (lat - 47.5) * 74
    return x, y


def set_map(c, cam, T):
    c.drawRect(skia.Rect.MakeWH(W, H), fillp('#a9d3e6'))
    with layer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-1000, -1000, 3000, 2200), fillp('#a9d3e6'))
        for k in range(-20, 40):
            y = -600 + k * 60
            c.drawLine(-1000, y, 3000, y, strokep('#9ccbe0', 2))
        for name, pts in EUROPE.items():
            p = smooth_path([map_xy(*q) for q in pts], True, 0.3)
            col = '#efe2c2'
            if name == 'italy':
                col = '#5aa05a'
            if name == 'ireland':
                col = '#3f9a5a'
            c.drawPath(p, fillp(col))
            c.drawPath(p, strokep(INK, 4))
        for (lon, lat, lab) in ((-8.0, 53.0, 'IRELAND'), (12.5, 42.6, 'ITALY'), (2.5, 46.8, 'FRANCE')):
            x, y = map_xy(lon, lat)
            draw_text(c, lab, x, y, font(FONT_HAND, 30), '#2a2a2a', 'center', '#ffffff', 6)
