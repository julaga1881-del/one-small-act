"""Shot list and per-shot staging for 'One Small Act' - the ring in the river."""
import json, math, os
import skia
from gfx import *
from rig import *
from sets import *

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
MOUTH = TL['mouth']
LINES = TL['lines']


def spec(name, costume=False, **over):
    s = dict(CAST[name])
    if costume:
        s = hobbit(s)
    s.update(over)
    return s


def mouth_for(name, T):
    m = MOUTH.get(str(int(T * FPS)))
    if m and SPEAKER_KEY.get(m[0]) == name:
        return m[1]
    return 0


def speaking(name, T):
    for ln in LINES:
        if SPEAKER_KEY.get(ln['speaker']) == name and ln['start'] - 0.05 <= T <= ln['end'] + 0.1:
            return True
    return False


def person(c, name, x, y, h, T, costume=False, gest_hand='rhand', sp=None, **st):
    s = sp or spec(name, costume)
    st.setdefault('mouth', mouth_for(name, T))
    if speaking(name, T) and gest_hand and not st.get('nogest'):
        gx, gy = gesture(T, s.get('seed', 0), 1.0)
        hx, hy = st.get(gest_hand, (15, -31) if gest_hand == 'rhand' else (-15, -31))
        st[gest_hand] = (hx + gx, hy + gy)
    draw_person(c, s, x, y, h, st, T)


# ------------------------------------------------------------- overlays
def place_strip(c, text, lt, dur=3.0, corner='tr'):
    if lt < 0 or lt > dur:
        return
    a = min(ramp(lt, 0, 0.25), 1 - ramp(lt, dur - 0.3, dur))
    f = font(FONT_SUB, 34)
    n = int(len(text) * clamp(lt / 0.5))
    w = f.measureText(text) + 60
    x = W - w - 48 if corner == 'tr' else 48
    y = 48
    c.saveLayerAlpha(skia.Rect.MakeXYWH(x - 10, y - 10, w + 20, 90), int(255 * a))
    draw(c, rrect(x, y, w, 64, 6), '#14161a', None, 0, fa=0.82)
    c.drawRect(skia.Rect.MakeXYWH(x, y, 10, 64), fillp('#e8b833'))
    draw_text(c, text[:n], x + 32, y + 45, f, '#f4f1ea')
    c.restore()


def hang_tag(c, text, lt, x=1660, dur=3.0, col='#f2c94c'):
    if lt < 0 or lt > dur:
        return
    a = 1 - ramp(lt, dur - 0.3, dur)
    drop = ease_out(ramp(lt, 0, 0.35))
    ang = 9 * math.exp(-lt * 2.2) * math.sin(lt * 9)
    c.save()
    c.translate(x, -20 + 0 * drop)
    c.rotate(ang)
    L = 70 + 30 * drop
    c.drawLine(0, 0, 0, L, strokep(INK, 3, a))
    f = font(FONT_HAND, 40)
    w = f.measureText(text) + 50
    c.saveLayerAlpha(skia.Rect.MakeXYWH(-w, -10, 2 * w, 260), int(255 * a))
    p = poly([(-w / 2 + 16, L), (w / 2, L), (w / 2, L + 76), (-w / 2 + 16, L + 76), (-w / 2, L + 38)])
    draw(c, p, col, INK, 4)
    c.drawCircle(-w / 2 + 22, L + 38, 6, fillp('#ffffff'))
    c.drawCircle(-w / 2 + 22, L + 38, 6, strokep(INK, 2))
    draw_text(c, text, 12, L + 52, f, INK, 'center')
    c.restore()
    c.restore()


def name_tag(c, text, x, y, lt, col='#f4f1ea'):
    """in-world name plate on a string, dropped in"""
    if lt < 0:
        return
    e = ease_out(ramp(lt, 0, 0.25))
    ang = 6 * math.exp(-lt * 3) * math.sin(lt * 10)
    c.save()
    c.translate(x, y - 260 * (1 - e))
    c.rotate(ang)
    f = font(FONT_HAND, 30)
    w = f.measureText(text) + 36
    c.drawLine(-w * 0.3, -60, -w * 0.3, 0, strokep(INK, 3))
    c.drawLine(w * 0.3, -60, w * 0.3, 0, strokep(INK, 3))
    draw(c, rrect(-w / 2, 0, w, 56, 8), col, INK, 4)
    draw_text(c, text, 0, 40, f, INK, 'center')
    c.restore()


def thought(c, x, y, lt, fn, r=150):
    if lt < 0:
        return
    s = ease_out(ramp(lt, 0, 0.3)) * (1 + 0.06 * math.sin(lt * 12) * math.exp(-lt * 4))
    for k, (dx, dy, rr) in enumerate(((-r * 0.9, r * 1.05, 10), (-r * 0.7, r * 0.82, 16))):
        c.drawCircle(x + dx, y + dy, rr * s, fillp('#ffffff'))
        c.drawCircle(x + dx, y + dy, rr * s, strokep(INK, 3))
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = skia.Path()
    for k in range(9):
        a = k / 9 * 2 * math.pi
        p.addCircle(math.cos(a) * r * 0.85, math.sin(a) * r * 0.55, r * 0.38)
    p.addOval(skia.Rect.MakeLTRB(-r * 0.95, -r * 0.6, r * 0.95, r * 0.6))
    c.drawPath(p, fillp('#ffffff'))
    c.drawPath(p, strokep(INK, 4))
    c.clipPath(oval(0, 0, r * 0.95, r * 0.62))
    fn(c, r)
    c.restore()


def big_hand(c, x, y, s, ang, skin=SKIN_IR, ring=False, pale=False, ring_slide=0.0, sparkle=0.0, ring_tilt=0.32):
    """Cartoon hand in close-up, fingers pointing along +x before rotation."""
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    sw = 5
    # wrist/sleeve
    draw(c, rrect(-260 * s, -55 * s, 200 * s, 110 * s, 30 * s), '#3f8a4f', INK, sw)
    for k in range(4):
        c.drawLine((-250 + k * 14) * s, -50 * s, (-250 + k * 14) * s, 50 * s, strokep('#2f6a3c', 3))
    palm = rrect(-80 * s, -60 * s, 130 * s, 120 * s, 40 * s)
    draw(c, palm, skin, INK, sw)
    fingers = [(-42, 96, 22), (-14, 112, 22), (14, 104, 22), (40, 84, 20)]  # y offset, length, width
    ring_pos = None
    for i, (fy, L, fw) in enumerate(fingers):
        p = rrect(30 * s, (fy - fw / 2) * s, L * s, fw * s, fw * 0.5 * s)
        draw(c, p, skin, INK, sw)
        c.drawLine((30 + L * 0.55) * s, (fy - fw / 2 + 4) * s, (30 + L * 0.55) * s, (fy + fw / 2 - 4) * s,
                   strokep(shade(skin, -0.25), 2))
        if i == 2:
            ring_pos = (30 + 26, fy, L)
    # thumb
    draw(c, rrect(-20 * s, -88 * s, 80 * s, 26 * s, 13 * s), skin, INK, sw)
    if pale:
        rx, ry, L = ring_pos
        c.drawRect(skia.Rect.MakeXYWH((rx - 6) * s, (ry - 11) * s, 12 * s, 22 * s), fillp('#fff3e6'))
        c.drawRect(skia.Rect.MakeXYWH((rx - 6) * s, (ry - 11) * s, 12 * s, 22 * s), strokep(shade(skin, -0.2), 1.5))
    rp = None
    if ring:
        rx, ry, L = ring_pos
        px = rx + ring_slide * (L + 30)
        rp = (px * s, ry * s)
        c.save()
        c.translate(px * s, ry * s)
        c.rotate(90)
        gold_ring(c, 0, 0, 21 * s, 0, ring_tilt, 3.5, sparkle)
        c.restore()
    c.restore()
    return rp


def ukulele(c, x, y, s, ang):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    p = skia.Path()
    p.addCircle(0, 0, 34 * s)
    p.addCircle(36 * s, 0, 26 * s)
    c.drawPath(p, fillp('#c98a4a'))
    c.drawPath(p, strokep(INK, 3))
    c.drawCircle(18 * s, 0, 9 * s, fillp('#3a2414'))
    draw(c, rect(56 * s, -6 * s, 80 * s, 12 * s), '#7a4e2c', INK, 3)
    c.restore()


def note(c, x, y, s, a, double=False):
    c.drawOval(skia.Rect.MakeXYWH(x - 14 * s, y - 9 * s, 26 * s, 18 * s), fillp(INK, a))
    c.drawLine(x + 10 * s, y - 2 * s, x + 10 * s, y - 52 * s, strokep(INK, 5 * s, a))
    if double:
        c.drawOval(skia.Rect.MakeXYWH(x + 26 * s, y - 17 * s, 26 * s, 18 * s), fillp(INK, a))
        c.drawLine(x + 50 * s, y - 10 * s, x + 50 * s, y - 60 * s, strokep(INK, 5 * s, a))
        c.drawLine(x + 10 * s, y - 52 * s, x + 50 * s, y - 60 * s, strokep(INK, 8 * s, a))
    else:
        c.drawPath(smooth_path([(x + 10 * s, y - 52 * s), (x + 26 * s, y - 40 * s), (x + 24 * s, y - 26 * s)], False),
                   strokep(INK, 5 * s, a))


def music_notes(c, x, y, T, n=4, a=1.0):
    for k in range(n):
        ph = (T * 0.5 + k / n) % 1
        nx = x + k * 30 + math.sin(ph * 6 + k) * 30 + ph * 140
        ny = y - ph * 260
        note(c, nx, ny, 0.9, a * math.sin(ph * math.pi), k % 2 == 1)


# =============================================================== SHOTS
# each: fn(c, lt, dur, T)

def sh_phone_top(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 540, 1.04), (960, 520, 1.16), 'lin', 0.4)
    with layer(c, cam, 0.9):
        # wooden counter top seen from above
        c.drawRect(skia.Rect.MakeLTRB(-200, -200, 2200, 1300), fillp('#9c6a40'))
        for k in range(14):
            y = -200 + k * 110
            c.drawLine(-200, y, 2200, y, strokep('#7a4e2c', 4))
            for j in range(6):
                gx = (j * 420 + k * 170) % 2400 - 200
                c.drawArc(skia.Rect.MakeXYWH(gx, y + 30, 160, 40), 200, 140, False, strokep('#8a5a34', 3))
        # props: chopping board with basil, garlic, wooden spoon, tomatoes, tea towel
        draw(c, rrect(1260, 180, 520, 340, 30), '#d9a868', INK, 5)
        for k in range(5):
            draw(c, oval(1380 + k * 70, 300 + 30 * math.sin(k), 34, 20), '#4f9a3d', INK, 3)
        for k in range(3):
            draw(c, oval(1350 + k * 120, 440, 46, 42), '#d9432f', INK, 4)
            c.drawLine(1350 + k * 120, 400, 1350 + k * 120 + 10, 390, strokep('#3f7a2a', 6))
        draw(c, oval(300, 820, 70, 62), '#f4ecdd', INK, 4)
        for k in range(3):
            c.drawLine(300 + (k - 1) * 22, 770, 300 + (k - 1) * 18, 870, strokep('#d8ccb6', 3))
        draw(c, rrect(120, 140, 560, 50, 25), '#c79a5c', INK, 5)
        draw(c, oval(720, 165, 70, 46), '#c79a5c', INK, 5)
        draw(c, rrect(1300, 700, 520, 380, 20), '#f2ece0', INK, 5)
        for k in range(5):
            c.drawLine(1300, 740 + k * 26, 1820, 740 + k * 26, strokep('#c33631', 8))
        # steam drifting in from the pot (off-frame left)
        steam(c, 120, 1000, T, 1.6, 6, 0.35, 2)
    with layer(c, cam, 1.0):
        buzz = 1.0 if (lt < 0.9 or 1.4 < lt < 2.2) else 0.0
        phone(c, 700, 230, 360, 700, T, 'lock', reveal=0.85 + 0.15 * ramp(lt, 0, 0.3), glow_a=1.0, buzz=buzz)
    vignette(c, 0.45)
    grade(c, '#ffb070', 0.18)


def kitchen_people(c, T, lt, patrick_face=0.6, head_turn_t=None, expr='smile', spoon=True, h=560, px=640):
    def hold(cv, hands, u):
        if spoon and hands[1]:
            hx, hy = hands[1]
            cv.drawLine(hx, hy, hx + 22 * u, hy + 14 * u, strokep('#a9733f', 2.4 * u))
            cv.drawLine(hx, hy, hx + 22 * u, hy + 14 * u, strokep(INK, 0.6 * u))
            draw(cv, oval(hx + 23 * u, hy + 15 * u, 3.2 * u, 2 * u), '#a9733f', INK, 0.6 * u)
    a = T * 3.2
    rh = (26 + 4 * math.cos(a), -46 + 2 * math.sin(a))
    face = patrick_face
    if head_turn_t is not None:
        face = lerp(patrick_face, 0.0, ease_io(ramp(lt, head_turn_t, head_turn_t + 0.4)))
    person(c, 'patrick', px, 960, h, T, rhand=rh, lhand=(-14, -32), facing=face, expr=expr, hold=hold, gest_hand=None)


def sh_kitchen_wide(c, lt, dur, T):
    # starts on Patrick stirring, pans to the phone as it buzzes (phone buzzed ~5.4s)
    turn = 2.55
    if lt < turn:
        cam = cam_path(lt, turn, (860, 560, 1.18), (900, 560, 1.22), 'lin', 1, 2)
    else:
        cam = cam_path(lt - turn, dur - turn, (900, 560, 1.22), (1240, 540, 1.3), 'out', 1, 2)
    buzz = 1.0 if lt > 2.55 else 0.0
    set_kitchen(c, cam, T, phone_on=lt > 2.5, phone_buzz=buzz, steam_a=0.55)
    with layer(c, cam, 0.92):
        kitchen_people(c, T, lt, 0.6, 3.0, 'smile' if lt < 3.0 else 'surprised')
    with layer(c, cam, 1.3):
        # foreground: hanging tea towel at right edge, blurred
        p = rrect(1840, -100, 160, 520, 20)
        c.drawPath(p, fillp('#f2ece0', 1, blur=6))
        for k in range(5):
            c.drawLine(1840, 0 + k * 30, 2000, 0 + k * 30, strokep('#c33631', 10, 1, blur=6))
    vignette(c, 0.4)
    grade(c, '#ffa860', 0.22)


def bokeh_bg(c, T, warm=True):
    sky(c, ['#3a2a22', '#5a3a2a', '#2a1d15'])
    for k in range(16):
        x = W * hash01(k, 3) + math.sin(T * 0.3 + k) * 20
        y = H * hash01(k, 4)
        r = 60 + 90 * hash01(k, 5)
        col = ['#ffcf7a', '#ff9f5a', '#ffe6b0'][k % 3]
        c.drawCircle(x, y, r, fillp(col, 0.12 + 0.08 * hash01(k, 6)))


def sh_phone_pov(c, lt, dur, T):
    bokeh_bg(c, T)
    steam(c, 300, 1100, T, 2.0, 6, 0.25, 4)
    # camera pushes from whole phone to the photo, then to the message
    if lt < 3.6:
        cam = cam_path(lt, 3.6, (960, 540, 1.0), (960, 470, 1.12), 'io', 0.5, 3)
    else:
        cam = cam_path(lt - 3.6, dur - 3.6, (960, 470, 1.12), (960, 640, 1.26), 'out', 0.5, 3)
    with layer(c, cam, 1.0):
        pw, ph = 470, 930
        px, py = 960 - pw / 2, 90
        # hand holding phone (mittens + thumb)
        draw(c, rrect(px - 70, py + 560, 160, 420, 60), SKIN_IR, INK, 5)
        draw(c, rrect(px + pw - 90, py + 600, 160, 400, 60), SKIN_IR, INK, 5)
        phone(c, px, py, pw, ph, T, 'chat', reveal=ramp(lt, 1.5, 2.0), glow_a=0.6,
              typed=ramp(lt, 4.3, 5.9) if lt > 4.3 else 0.0)
        draw(c, rrect(px + pw - 40, py + 640, 70, 150, 35), SKIN_IR, INK, 5)
        draw(c, rrect(px - 30, py + 660, 70, 150, 35), SKIN_IR, INK, 5)
    vignette(c, 0.5)
    grade(c, '#ffb070', 0.12)


def sh_patrick_frozen(c, lt, dur, T):
    cam = cam_path(lt, dur, (720, 520, 1.55), (700, 470, 1.75), 'lin', 0.6, 4)
    set_kitchen(c, cam, T, phone_on=None, steam_a=0.7)

    def hold(cv, hands, u):
        if hands[1]:
            hx, hy = hands[1]
            cv.drawLine(hx, hy, hx + 4 * u, hy - 20 * u, strokep('#a9733f', 2.4 * u))
            draw(cv, oval(hx + 4.5 * u, hy - 22 * u, 2.2 * u, 3.2 * u), '#a9733f', INK, 0.6 * u)
        if hands[0]:
            hx, hy = hands[0]
            draw(cv, rrect(hx - 5 * u, hy - 16 * u, 10 * u, 18 * u, 2 * u), '#1c1d22', INK, 0.7 * u)
            cv.drawRect(skia.Rect.MakeXYWH(hx - 4 * u, hy - 15 * u, 8 * u, 15 * u), fillp('#cfe6ff'))
            glow(cv, hx, hy - 8 * u, 18 * u, '#d9ecff', 0.4)
    with layer(c, cam, 0.92):
        person(c, 'patrick', 640, 960, 560, T, rhand=(24, -60), lhand=(-6, -56), facing=0.15, expr='surprised',
               hold=hold, gest_hand=None, noblink=True)
        steam(c, 960, 480, T + 3, 1.3, 6, 0.6)
    vignette(c, 0.45)
    grade(c, '#ffa860', 0.22)


def sh_rewind(c, lt, dur, T):
    c.clear(hexc('#0e0d0c'))
    # film strip scrolling right (rewind), accelerating, then the river frame grows to full
    grow = ease_io(ramp(lt, dur - 0.75, dur))
    sp = 300 + 2200 * ease_in(ramp(lt, 0, 1.3))
    off = (lt * sp) % 640
    fw, fh = 560, 315
    y0 = 540 - fh / 2
    if grow < 1:
        c.save()
        c.drawRect(skia.Rect.MakeXYWH(-50, y0 - 60, W + 100, fh + 120), fillp('#191714'))
        for k in range(-2, 40):
            x = k * 52 + (off % 52)
            c.drawRect(skia.Rect.MakeXYWH(x, y0 - 45, 26, 22), fillp('#e8e2d4', 0.9))
            c.drawRect(skia.Rect.MakeXYWH(x, y0 + fh + 23, 26, 22), fillp('#e8e2d4', 0.9))
        shots = [(sh_patrick_frozen, 15.0, 1.0), (sh_phone_pov, 12.0, 5.0), (sh_kitchen_wide, 5.0, 2.3),
                 (sh_river_establish, 21.5, 1.6)]
        for k in range(-1, 4):
            x = k * 640 + off - 320
            idx = int(math.floor(-(k - (lt * sp) // 640))) % 4
            fn, tt, ll = shots[idx]
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(x, y0, fw, fh))
            c.translate(x, y0)
            c.scale(fw / W, fh / H)
            fn(c, ll, 3.0, tt)
            c.restore()
            c.drawRect(skia.Rect.MakeXYWH(x, y0, fw, fh), strokep('#000000', 6))
        c.restore()
        # rewind streaks
        for k in range(6):
            yy = (k * 197 + lt * 900) % H
            c.drawRect(skia.Rect.MakeXYWH(0, yy, W, 3), fillp('#ffffff', 0.08))
        ga = 0.6 + 0.4 * math.sin(lt * 10)
        for k in range(2):
            c.drawPath(poly([(150 + k * 44, 110), (150 + k * 44, 170), (110 + k * 44, 140)]), fillp('#f4f1ea', ga))
    else:
        pass
    if grow > 0:
        # river frame scales up from the strip centre to fill
        s = lerp(fw / W, 1.0, grow)
        c.save()
        c.translate(960 - W * s / 2, 540 - H * s / 2)
        c.scale(s, s)
        c.clipRect(skia.Rect.MakeWH(W, H))
        sh_river_establish(c, 0.0, 3.6, 19.9)
        c.restore()
    hang_tag(c, '9 DAYS EARLIER', lt - 0.3, 1600, 2.4)


def sh_river_establish(c, lt, dur, T):
    cam = cam_path(lt, dur, (1000, 420, 1.22), (1060, 540, 1.0), 'io', 0.6, 5)
    set_river_bg(c, cam, T)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    with layer(c, cam, 0.85):
        boulder(c, 1250, 740, 300, 170, '#8a8f93', 2, 4.5, wet=1)
        foam(c, 1250, 742, 300, T)
    fg_rocks(c, cam, T, 1.35, 'both')
    vignette(c, 0.18)


def family_walk(c, T, xs, y, h, phase, facing=0.7):
    order = [('girl1', 0.66), ('girl3', 0.48), ('joanne', 0.94), ('girl2', 0.57), ('patrick', 1.0)]
    for (n, hs), x in zip(order, xs):
        sp = spec(n)
        if n == 'patrick':
            sp['top'] = 'tee'
        draw_person(c, sp, x, y, h * hs, {'legs': 'walk', 'phase': phase * (1.2 if hs < 0.7 else 1.0) + x * 0.01,
                                          'facing': facing, 'expr': 'happy' if hs < 0.7 else 'smile',
                                          'lhand': (-12, -30 + 3 * math.sin(phase + x)), 'rhand': (12, -30 - 3 * math.sin(phase + x))}, T)


def sh_family_walk_a(c, lt, dur, T):
    walk = lt * 150
    cam = cam_path(lt, dur, (700 + 0, 560, 1.05), (700 + dur * 150, 560, 1.08), 'lin', 0.5, 6)
    set_river_bg(c, cam, T, village_x=1000)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    with layer(c, cam, 1.0):
        base = 380 + walk
        family_walk(c, T, [base + 420, base + 560, base + 300, base + 160, base], 960, 430, T * 5.5)
    fg_rocks(c, cam, T, 1.35, 'left', 1100)
    vignette(c, 0.2)
    place_strip(c, 'PATRICK MOHR · DÚN LAOGHAIRE', lt - 0.1, 2.7)


def sh_family_walk_b(c, lt, dur, T):
    walk = lt * 120
    cam = cam_path(lt, dur, (1320, 560, 1.28), (1320 + dur * 120, 540, 1.36), 'lin', 0.5, 7)
    set_river_bg(c, cam, T, village_x=1500)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    with layer(c, cam, 1.0):
        base = 1000 + walk
        family_walk(c, T, [base + 520, base + 660, base + 340, base + 170, base], 980, 500, T * 5.0)
    fg_rocks(c, cam, T, 1.4, 'right', 1100)
    vignette(c, 0.2)
    place_strip(c, 'BAGNI DI LUCCA · TUSCANY', lt + 0.0, 3.4)


def water_front(c, x0, x1, y, T, depth_px=400, a=0.62):
    """semi-transparent front water over waist-deep people"""
    c.drawRect(skia.Rect.MakeLTRB(x0, y, x1, y + depth_px), fillp(None, a, shader=lin(0, y, 0, y + depth_px, ['#4fa3c8', '#2a6f97'])))
    c.drawLine(x0, y, x1, y, strokep('#e8f8ff', 4, 0.9))
    for k in range(int((x1 - x0) / 120)):
        xx = x0 + ((k * 120 + T * 80) % (x1 - x0))
        c.drawLine(xx, y + 20 + (k % 3) * 30, xx + 60, y + 20 + (k % 3) * 30, strokep('#ffffff', 3, 0.5))


def sh_jumps(c, lt, dur, T):
    cam = cam_path(lt, dur, (1000, 540, 1.12), (1040, 520, 1.2), 'lin', 0.6, 8)
    set_river_bg(c, cam, T, water_y=600, village_x=700)
    with layer(c, cam, 0.85):
        water_band(c, -1500, 4500, 600, 1300, T, 1.0, ('#5aa7c9', '#3b8bb3', '#2e7aa2'), 14, 80)
    with layer(c, cam, 1.0):
        bx, by = 620, 760
        boulder(c, bx, by, 460, 330, '#8a8f93', 2, 5, wet=1)
        foam(c, bx, by - 5, 460, T)
        # Joanne on the far bank (behind) cheering
        person(c, 'joanne', 1500, 590, 300, T, rhand=(16, -80), lhand=(-16, -80), expr='happy', facing=-0.5)
        # Patrick waist-deep, arms out to catch
        px, py = 1000, 1010
        jumps = [(0.5, 'girl1', 0.66), (1.9, 'girl2', 0.57), (3.3, 'girl3', 0.48)]
        caught = None
        for (t0, n, hs) in jumps:
            u = (lt - t0) / 0.8
            if 0 <= u <= 1:
                caught = (n, hs, u)
        arm_up = caught is not None
        sp = spec('patrick')
        sp['top'] = 'tee'
        draw_person(c, sp, px, py, 520, {'lhand': (-22, -62) if arm_up else (-20, -44), 'rhand': (22, -62) if arm_up else (20, -44),
                                         'expr': 'happy', 'facing': -0.4, 'mouth': 0}, T)
        # girls waiting on the boulder / jumping
        waiting_x = [560, 640, 720]
        for i, (t0, n, hs) in enumerate(jumps):
            u = (lt - t0) / 0.8
            if u < 0:
                draw_person(c, spec(n), waiting_x[i] - 40, by - 300, 520 * hs * 0.82, {'expr': 'happy', 'facing': 0.6,
                                                                                    'rhand': (14, -60) if i == 0 else (14, -30)}, T)
            elif u <= 1:
                e = u
                x = lerp(waiting_x[i] - 40, px - 10, e)
                y = lerp(by - 300, py - 300, e) - math.sin(e * math.pi) * 160
                draw_person(c, spec(n), x, y, 520 * hs * 0.82, {'expr': 'laugh', 'legs': 'jump', 'facing': 0.6,
                                                               'lhand': (-16, -80), 'rhand': (16, -80), 'shadow': False}, T)
            else:
                # splash then bobbing beside dad
                bxx = px + (-150, 170, 280)[i]
                draw_person(c, spec(n), bxx, py - 120 + math.sin(T * 3 + i) * 6, 520 * hs * 0.82,
                            {'expr': 'laugh', 'facing': -0.5 if i else 0.5, 'shadow': False, 'lhand': (-16, -60), 'rhand': (16, -60)}, T)
        water_front(c, -600, 2600, 820, T, 600, 0.6)
        for (t0, n, hs) in jumps:
            splash(c, px - 10, 820, 1.0, lt - t0 - 0.8, 0.8)
    vignette(c, 0.2)


def sh_grab_hand(c, lt, dur, T):
    cam = cam_path(lt, dur, (900, 520, 1.35), (930, 560, 1.55), 'io', 0.5, 9)
    set_river_bg(c, cam, T, water_y=600, village_x=400)
    with layer(c, cam, 0.85):
        water_band(c, -1500, 4500, 600, 1300, T, 1.0, ('#5aa7c9', '#3b8bb3', '#2e7aa2'), 14, 80)
    with layer(c, cam, 1.0):
        boulder(c, 520, 780, 500, 340, '#8a8f93', 2, 5, wet=1)
        boulder(c, 760, 800, 300, 110, '#7f868a', 4, 5, wet=1)
        pull = ease_io(ramp(lt, 0.3, 1.2))
        tug = math.sin(lt * 9) * 2 * pull
        sp = spec('patrick')
        sp['top'] = 'tee'
        draw_person(c, sp, 960, 1010, 520, {'lhand': (-21 + tug, -78), 'rhand': (16, -40),
                                            'expr': 'happy' if lt < 1.4 else 'surprised', 'facing': -0.5}, T)
        draw_person(c, spec('girl3'), 760, 700, 330, {'rhand': (22 + tug * 0.5, -38), 'lhand': (-16, -60), 'expr': 'laugh',
                                                      'facing': 0.6}, T)
        water_front(c, -600, 2600, 820, T, 600, 0.6)
    vignette(c, 0.22)


def sh_ring_slip(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 470, 1.0), (960, 560, 1.08), 'io', 0.4, 10)
    bgc = Cam(900 + lt * 20, 420, 1.9)
    set_river_bg(c, bgc, T, water_y=600, village_x=600)
    with layer(c, bgc, 0.85):
        water_band(c, -1500, 4500, 600, 1400, T, 1.0, ('#5aa7c9', '#3b8bb3', '#2e7aa2'), 10, 80)
    c.drawRect(skia.Rect.MakeWH(W, H), fillp('#dff1f7', 0.35))
    with layer(c, cam, 1.0):
        water_band(c, -500, 2500, 830, 1500, T, 1.0, ('#4f9fc4', '#2f7aa3', '#245f86'), 10, 160)
        slide = ease_in(ramp(lt, 1.35, 1.75))
        wob = math.sin(lt * 8) * 6 * (1 - ramp(lt, 0, 1.6))
        tug = math.sin(lt * 7) * 14 * (1 - ramp(lt, 1.6, 2.0))
        hx, hy = 700 + wob, 360
        rp = big_hand(c, hx + tug, hy, 1.8, 22, ring=lt < 1.75, ring_slide=slide)
        # child's small hand gripping his index finger (thin arm line, mitten hand)
        a = math.radians(22)
        fx = hx + tug + math.cos(a) * 150 * 1.8 - math.sin(a) * (-42) * 1.8
        fy = hy + math.sin(a) * 150 * 1.8 + math.cos(a) * (-42) * 1.8
        c.drawPath(smooth_path([(fx - 40, fy + 520), (fx - 120, fy + 260), (fx - 20, fy + 30)], False), strokep(INK, 10))
        c.drawCircle(fx - 10, fy + 10, 48, fillp(SKIN_IR))
        c.drawCircle(fx - 10, fy + 10, 48, strokep(INK, 5))
        # ring falling to the water
        if lt >= 1.75:
            u = lt - 1.75
            x0, y0 = hx + 400, hy + 230
            fy2 = y0 + 1400 * u * u + 150 * u
            if fy2 < 840:
                gold_ring(c, x0 + 60 * u, fy2, 34, u * 400, 0.3 + 0.3 * math.sin(u * 20), 3)
        splash(c, hx + 440, 840, 1.3, lt - 2.15, 0.9)
    vignette(c, 0.25)


def swirl(c, x, y, r, T, a=0.5, k=0):
    p = skia.Path()
    for i in range(40):
        t = i / 39
        ang = t * 4.5 + T * 3 + k
        rr = r * (0.2 + t)
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr * 0.6
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    c.drawPath(p, strokep('#d8f6ff', 3.5, a))


def sh_ring_tumble(c, lt, dur, T):
    rx = 500 + lt * 420
    ry = 300 + lt * 90 + math.sin(lt * 3) * 40
    cam = cam_path(lt, dur, (760, 470, 1.12), (760 + dur * 330, 600, 1.0), 'lin', 0.6, 11)
    set_underwater(c, cam, T, 900, 0.0, True, 1.6)
    with layer(c, cam, 1.0):
        for k in range(8):
            swirl(c, 300 + k * 330 + (T * 160) % 330, 380 + 160 * math.sin(k * 1.7), 90 + 30 * hash01(k, 3), T, 0.35, k)
        gold_ring(c, rx, ry, 30, lt * 260, 0.25 + 0.3 * abs(math.sin(lt * 2.5)), 3)
        bubbles(c, None, T, rx - 30, ry + 40, 5, 0.6, 1.0, 3, 30)
    current_lines(c, cam, T, 26, 900, 0.4, 1.0)
    murk = ramp(lt, dur - 1.5, dur) * 0.5
    if murk:
        c.drawRect(skia.Rect.MakeWH(W, H), fillp('#0b2c3c', murk))
    vignette(c, 0.45)
    place_strip(c, '16 YEARS OF MARRIAGE', lt - 0.3, 3.0)


def sh_paralysed(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 520, 1.05), (1000, 470, 1.4), 'lin', 0.4, 12)
    set_river_bg(c, cam, T, water_y=600, village_x=-200)
    with layer(c, cam, 0.85):
        water_band(c, -1500, 4500, 600, 1300, T * 1.4, 1.0, ('#5aa7c9', '#3b8bb3', '#2e7aa2'), 14, 140)
    with layer(c, cam, 1.0):
        boulder(c, 420, 780, 400, 260, '#8a8f93', 2, 5, wet=1)
        sp = spec('patrick')
        sp['top'] = 'tee'
        person(c, 'patrick', 1000, 1020, 540, T, sp=sp, lhand=(-12, -34), rhand=(12, -34), expr='sad', facing=0.05,
               gest_hand=None)
        water_front(c, -600, 2600, 830, T * 1.4, 600, 0.62)
        # water rushing lines past him
        for k in range(10):
            ph = (T * 1.2 + k / 10) % 1
            xx = -100 + ph * 2200
            yy = 850 + (k % 4) * 40
            c.drawLine(xx, yy, xx + 120, yy, strokep('#ffffff', 4, 0.6))
        foam(c, 1000, 832, 200, T, 0.9)
    vignette(c, 0.3)
    grade(c, '#4a6b8a', 0.18)


def friends_sitting(c, T, xs, y, h, lt=0.0, stand_t=None):
    for i, n in enumerate(('filippo', 'nicola', 'edoardo')):
        up = 0.0 if stand_t is None else ease_out(ramp(lt, stand_t + i * 0.12, stand_t + 0.35 + i * 0.12))
        if up < 0.5:
            draw(c, None, None, None, 0) if False else None
            boulder(c, xs[i] + 10, y + 6, 150, 70, '#9a968c', i + 4, 4)
            person(c, n, xs[i], y - 50, h, T, legs='sit', facing=-0.5, expr='smile' if stand_t is None else 'surprised',
                   lhand=(-12, -30), rhand=(14, -34), gest_hand=None)
        else:
            boulder(c, xs[i] + 10, y + 6, 150, 70, '#9a968c', i + 4, 4)
            person(c, n, xs[i] - 40, y + 60 - 30 * (1 - up), h, T, facing=-0.5, expr='surprised',
                   lhand=(-16, -40), rhand=(16, -40), gest_hand=None)


def sh_joanne_turns(c, lt, dur, T):
    cam = cam_path(lt, dur, (900, 470, 1.6), (880, 450, 1.75), 'lin', 0.5, 13)
    set_river_bg(c, cam, T, village_x=500)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    with layer(c, cam, 1.0):
        turn = ease_io(ramp(lt, 0.2, 0.7))
        person(c, 'joanne', 900, 960, 480, T, facing=lerp(-0.7, 0.8, turn), expr='concerned' if lt < 0.5 else 'determined',
               lhand=(-14, -34), rhand=(14, -34), tilt=lerp(-6, 4, turn))
    vignette(c, 0.25)


def sh_joanne_runs(c, lt, dur, T):
    run = ease_io(clamp(lt / dur)) * 1300
    cam = cam_path(lt, dur, (900, 560, 1.12), (2050, 560, 1.12), 'io', 0.6, 14)
    set_river_bg(c, cam, T, village_x=800)
    set_river_water(c, cam, T, flow=1.0)
    set_river_near(c, cam, T)
    with layer(c, cam, 1.0):
        pebbles(c, 300, 3300, 900, 940, 30, 44)
        friends_sitting(c, T, [2280, 2440, 2600], 930, 400)
        person(c, 'joanne', 750 + run, 980, 440, T, legs='walk', phase=T * 11, facing=0.9, expr='determined',
               lhand=(-18, -44 + 8 * math.sin(T * 11)), rhand=(18, -44 - 8 * math.sin(T * 11)), tilt=6)
        # dust puffs behind her heels
        for k in range(3):
            ph = (T * 3 + k / 3) % 1
            c.drawCircle(750 + run - 60 - ph * 80, 975 - ph * 20, 10 + 14 * ph, fillp('#e8e0d0', 0.6 * (1 - ph)))
    fg_rocks(c, cam, T, 1.35, 'left', 1120)
    vignette(c, 0.2)


def sh_help(c, lt, dur, T):
    cam = cam_path(lt, dur, (1600, 540, 1.08), (1650, 540, 1.1), 'lin', 0.5, 15)
    set_river_bg(c, cam, T, village_x=900)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    with layer(c, cam, 1.0):
        friends_sitting(c, T, [1680, 1880, 2080], 950, 430, lt, 0.9)
        person(c, 'joanne', 1180, 980, 450, T, facing=0.8, expr='concerned', gest_hand=None,
               lhand=(-26, -62) if lt > 2.1 else (-14, -40), rhand=(18, -46) if lt < 2.1 else (16, -36))
        # arrow of urgency: she points upstream (left) on "it's in the river"
    vignette(c, 0.2)


def friends_row(c, T, xs, y, h, exprs=('smile', 'smile', 'smile'), costume=False, hands=None, facing=(0.3, 0, -0.3), **kw):
    for i, n in enumerate(('filippo', 'nicola', 'edoardo')):
        st = dict(facing=facing[i], expr=exprs[i])
        if hands and hands[i]:
            st['lhand'], st['rhand'] = hands[i]
        st.update(kw)
        person(c, n, xs[i], y, h, T, costume=costume, **st)


def sh_names(c, lt, dur, T):
    cam = cam_path(lt, dur, (720, 500, 1.32), (1200, 500, 1.32), 'lin', 0.4, 16)
    set_river_bg(c, cam, T, village_x=600)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    xs = [560, 960, 1360]
    with layer(c, cam, 1.0):
        friends_row(c, T, xs, 980, 500, ('happy', 'smile', 'smile'),
                    hands=[((-16, -36), (22, -70)), ((-15, -32), (15, -32)), ((-15, -32), (15, -32))])
        for i, (txt, t0) in enumerate((('FILIPPO PALAGI', 0.1), ('NICOLA MALLOGGI', 1.3), ('EDOARDO POGGI', 2.5))):
            name_tag(c, txt, xs[i], 250 + (i % 2) * 70, lt - t0, ['#d9e6ff', '#fff2b8', '#ffd9d6'][i])
    vignette(c, 0.2)


def sh_swap(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 520, 1.3), (960, 500, 1.42), 'io', 0.4, 17)
    set_river_bg(c, cam, T, village_x=1300)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    sw_ = ease_io(ramp(lt, 0.4, 1.6))

    def ph_hold(col):
        def f(cv, hands, u):
            if hands[1]:
                hx, hy = hands[1]
                draw(cv, rrect(hx - 4 * u, hy - 12 * u, 8 * u, 14 * u, 1.5 * u), '#1c1d22', INK, 0.6 * u)
                cv.drawRect(skia.Rect.MakeXYWH(hx - 3 * u, hy - 11 * u, 6 * u, 11 * u), fillp(col))
        return f
    with layer(c, cam, 1.0):
        person(c, 'joanne', 760, 980, 470, T, facing=0.7, expr='smile', rhand=(lerp(18, 30, sw_), -48), hold=ph_hold('#cfe6ff'),
               gest_hand=None)
        person(c, 'filippo', 1170, 980, 500, T, facing=-0.7, expr='happy', flip=True, rhand=(lerp(18, 30, sw_), -48),
               hold=ph_hold('#ffe6a0'), gest_hand=None)
        person(c, 'nicola', 1450, 985, 510, T, facing=-0.6, expr='smile', gest_hand=None)
        # number bubbles crossing
        if 0.3 < lt < 2.8:
            f = font(FONT_HAND, 30)
            for k, (a, b, txt) in enumerate(((880, 1050, '+353 ...'), (1050, 880, '+39 ...'))):
                u = ramp(lt, 0.5 + k * 0.3, 1.6 + k * 0.3)
                x = lerp(a, b, ease_io(u))
                y = 520 - math.sin(u * math.pi) * 90 - k * 70
                draw(c, rrect(x - 70, y - 30, 140, 46, 23), '#ffffff', INK, 3)
                draw_text(c, txt, x, y + 2, f, INK, 'center')
    vignette(c, 0.2)


def mini_quest(cv, r):
    # three tiny cloaked figures walking along a winding path toward a tiny ring
    cv.drawRect(skia.Rect.MakeLTRB(-r, -r, r, r), fillp('#eaf4dc'))
    ridge(cv, -r, r, r * 0.15, r * 0.12, 2, 6, '#9cc47a', True, r, 2)
    cv.drawPath(smooth_path([(-r, r * 0.45), (-r * 0.3, r * 0.25), (r * 0.2, r * 0.38), (r, r * 0.1)], False), strokep('#d9c49a', 10))
    for k in range(3):
        x = -r * 0.55 + k * r * 0.22
        y = r * 0.32 - k * r * 0.03
        cv.drawPath(poly([(x - 10, y), (x + 10, y), (x + 6, y - 30), (x - 6, y - 30)]), fillp(['#5d6b3a', '#7a5230', '#6a3b2c'][k]))
        cv.drawCircle(x, y - 38, 10, fillp('#e2b088'))
        cv.drawCircle(x, y - 38, 10, strokep(INK, 2))
        cv.drawCircle(x, y - 46, 8, fillp('#5a3a22'))
    gold_ring(cv, r * 0.55, -r * 0.1, 18, 0, 0.5, 2)


def sh_quest_joke(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 500, 1.18), (960, 500, 1.22), 'lin', 0.5, 18)
    set_river_bg(c, cam, T, village_x=300)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    nud = math.sin(lt * 6) * 8
    with layer(c, cam, 1.0):
        friends_row(c, T, [640, 960, 1280], 990, 500, ('laugh', 'laugh', 'happy'),
                    hands=[((-15, -32), (24 + nud * 0.3, -46)), ((-24, -46), (15, -60)), ((-26, -46), (15, -32))],
                    tilt=nud * 0.6)
        thought(c, 1290, 250, lt - 1.0, mini_quest, 170)
    vignette(c, 0.2)


def kayak(c, x, y, col, who, T, lt, peer=0.0, shake=0.0, paddle=True):
    bob = math.sin(T * 2 + x * 0.01) * 6
    y = y + bob
    s = spec(who)
    tilt = math.sin(T * 10) * 12 * shake
    person(c, who, x, y + 10, 330, T, sp=s, legs='none', shadow=False, facing=0.4 + 0.4 * peer,
           expr='concerned' if shake > 0 else 'thinking', tilt=tilt + peer * 14, lhand=(-14, -40), rhand=(22, -48), gest_hand=None)
    if paddle:
        a = math.sin(T * 1.5 + x) * 0.3
        c.drawLine(x - 90, y - 150 + a * 60, x + 110, y - 110 - a * 60, strokep('#d9c49a', 8))
        c.drawLine(x - 90, y - 150 + a * 60, x + 110, y - 110 - a * 60, strokep(INK, 2))
        for (px, py) in ((x - 100, y - 152 + a * 60), (x + 120, y - 108 - a * 60)):
            draw(c, oval(px, py, 24, 10), '#333333', INK, 3)
    hull = smooth_path([(x - 230, y - 30), (x + 230, y - 30), (x + 160, y + 20), (x - 160, y + 20)], True, 0.25)
    draw(c, hull, col, INK, 5)
    c.drawLine(x - 200, y - 18, x + 200, y - 18, strokep(shade(col, 0.3), 4, 0.8))
    draw(c, oval(x, y - 32, 60, 10), '#222222', INK, 3)


def sh_mission(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 560, 1.05), (960, 520, 1.2), 'out', 0.5, 19)
    set_river_bg(c, cam, T, village_x=1500)
    set_river_water(c, cam, T)
    set_river_near(c, cam, T)
    with layer(c, cam, 1.0):
        for i, col in enumerate(('#2f6fd0', '#f0b726', '#d23b35')):
            draw(c, smooth_path([(400 + i * 520 - 200, 1000), (400 + i * 520 + 200, 1000), (400 + i * 520 + 140, 1040),
                                 (400 + i * 520 - 140, 1040)], True, 0.3), col, INK, 5)

        def paddle_hold(cv, hands, u):
            if hands[1]:
                hx, hy = hands[1]
                cv.drawLine(hx, hy + 30 * u, hx, hy - 40 * u, strokep('#d9c49a', 2 * u))
                draw(cv, oval(hx, hy - 44 * u, 3.4 * u, 8 * u), '#333333', INK, 0.6 * u)
        for i, n in enumerate(('filippo', 'nicola', 'edoardo')):
            step = ease_out(ramp(lt, 0.1 + i * 0.2, 0.7 + i * 0.2))
            person(c, n, 560 + i * 400, 980 + 40 * (1 - step), 520, T, facing=0.2 - i * 0.2, expr='determined',
                   rhand=(20, -48), lhand=(-15, -32), hold=paddle_hold, gest_hand=None)
    vignette(c, 0.22)


def sh_kayaks(c, lt, dur, T):
    cam = cam_path(lt, dur, (900, 520, 1.05), (1250, 520, 1.1), 'lin', 0.4, 20)
    set_river_bg(c, cam, T, water_y=560, village_x=600)
    with layer(c, cam, 0.9):
        water_band(c, -1500, 4500, 560, 1400, T, 1.0, ('#5aa7c9', '#3b8bb3', '#2a6f97'), 14, 70)
    drift = lt * 60
    shake = ramp(lt, 3.6, 3.8)
    with layer(c, cam, 1.0):
        kayak(c, 480 + drift, 760, '#e8743a', 'filippo', T, lt, ramp(lt, 0.5, 1.0), shake)
        kayak(c, 1020 + drift * 0.9, 880, '#3fae6a', 'nicola', T, lt, ramp(lt, 0.7, 1.2), shake)
        kayak(c, 1520 + drift * 1.1, 760, '#e8c43a', 'edoardo', T, lt, ramp(lt, 0.9, 1.4), shake)
        for k, x in enumerate((480, 1020, 1520)):
            c.drawOval(skia.Rect.MakeXYWH(x + drift - 260, (760, 880, 760)[k] + 18, 520, 30), strokep('#ffffff', 3, 0.5))
    vignette(c, 0.22)
    hang_tag(c, 'DAY 1' if lt < 1.9 else 'DAY 2', lt if lt < 1.9 else lt - 1.9, 1700, 1.9 if lt < 1.9 else 3.0)


def sh_tie_ropes(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 500, 1.15), (960, 480, 1.28), 'io', 0.4, 21)
    set_river_bg(c, cam, T, water_y=620, village_x=200)
    with layer(c, cam, 0.88):
        water_band(c, -1500, 4500, 620, 1400, T * 1.3, 1.0, ('#4f9fc4', '#2f7aa3', '#245f86'), 14, 140)
    with layer(c, cam, 1.0):
        boulder(c, 960, 900, 900, 330, '#8a8f93', 7, 5, wet=1)
        foam(c, 960, 905, 900, T)
        # rope wrapped around boulder and running to each friend's waist
        for i, x in enumerate((620, 960, 1300)):
            y = 600 + abs(i - 1) * 40
            person(c, ('filippo', 'nicola', 'edoardo')[i], x, y, 430, T, facing=0.2 * (1 - i), expr='determined',
                   lhand=(-6, -36), rhand=(8, -38), gest_hand=None)
            c.drawPath(smooth_path([(x - 40, y - 100), (x, y - 92), (x + 40, y - 100)], False), strokep('#e8d6a0', 8))
            c.drawPath(smooth_path([(x + 30, y - 98), (x + 120, y + 40), (x + 80, y + 140)], False), strokep('#e8d6a0', 8))
            c.drawPath(smooth_path([(x + 30, y - 98), (x + 120, y + 40), (x + 80, y + 140)], False), strokep(INK, 2, 0.6))
            # mask pulled on at 1.3s
            if lt > 1.3 + i * 0.2:
                mask(c, x + 0.2 * (1 - i) * 4.2 * 430 / 90, y - 72 * 430 / 90 - 2 * 430 / 90, 430 / 90)
        c.drawPath(smooth_path([(420, 880), (960, 830), (1500, 880)], False), strokep('#e8d6a0', 10))
        c.drawPath(smooth_path([(420, 880), (960, 830), (1500, 880)], False), strokep(INK, 2, 0.6))
    vignette(c, 0.25)


def swimmer(c, name, x, y, h, T, ang=-80, expr='determined', masked=True, kick=1.0, hands=None, mouth=None):
    st = dict(rot=ang, facing=0.3, expr=expr, legs='walk', phase=T * 8 * kick, shadow=False,
              lhand=(-20, -78), rhand=(20, -78))
    if hands:
        st['lhand'], st['rhand'] = hands
    if mouth is not None:
        st['mouth'] = mouth
    person(c, name, x, y, h, T, gest_hand=None, **st)
    if masked:
        u = h / 90
        a = math.radians(ang)
        # head centre after rotation (head at (0,-72u) rotated)
        hx = x + 72 * u * math.sin(a) * 1 + 0.3 * 4.2 * u * math.cos(a)
        hy = y - 72 * u * math.cos(a) + 0.3 * 4.2 * u * math.sin(a)
        c.save()
        c.translate(hx, hy)
        c.rotate(ang)
        mask(c, 0, -2.2 * u, u)
        c.restore()


def sh_dive(c, lt, dur, T):
    cam = cam_path(lt, dur, (900, 560, 1.05), (1100, 540, 1.15), 'lin', 0.6, 22)
    set_underwater(c, cam, T, 860, 0.0, True, 2.0)
    with layer(c, cam, 1.0):
        bpos = [(520, 860), (1000, 880), (1480, 860)]
        for i, (bx, by) in enumerate(bpos):
            boulder(c, bx, by, 360, 220, '#4f6f78', i + 2, 5)
        for i, (bx, by) in enumerate(bpos):
            n = ('filippo', 'nicola', 'edoardo')[i]
            x = bx + 170 + math.sin(T * 2 + i) * 12
            y = by - 260 + math.sin(T * 1.5 + i) * 10
            # rope from boulder to waist
            c.drawPath(smooth_path([(bx + 60, by - 150), (bx + 120, by - 210 + math.sin(T * 3 + i) * 10), (x - 30, y - 40)], False),
                       strokep('#e8d6a0', 7))
            swimmer(c, n, x, y, 300, T, ang=-75 + math.sin(T * 2 + i) * 6, hands=((-24, -80), (-10, -40)), kick=1.2)
        bubbles(c, None, T, 700, 500, 6, 0.6, 1.0, 1)
        bubbles(c, None, T, 1200, 520, 6, 0.6, 1.0, 2)
    current_lines(c, cam, T, 30, 1100, 0.45, 1.0)
    vignette(c, 0.4)


def sh_edoardo_rope(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 520, 1.12), (930, 470, 1.22), 'lin', 0.5, 23)
    wy = 600
    # top half: above water; bottom: underwater cross-section
    sky(c, ['#8fc6e2', '#cfe6ef'])
    with layer(c, cam, 0.25):
        ridge(c, -1500, 4500, 420, 80, 2, 1, '#7fa865', True, 1500, 2.5)
        for k in range(10):
            cypress(c, -900 + k * 350, 470, 140, '#2f5a35', T, k)
    with layer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-1500, wy, 4500, 2000), fillp(None, 1, shader=lin(0, wy, 0, 1300, ['#2f8fa8', '#164b63'])))
        for k in range(6):
            x = -200 + k * 420 + 60 * math.sin(T * 0.5 + k)
            c.drawPath(poly([(x, wy), (x + 100, wy), (x + 300, 1400), (x + 150, 1400)]), fillp('#bff3ff', 0.07))
        c.drawRect(skia.Rect.MakeLTRB(-1500, 1150, 4500, 2000), fillp('#9c8457'))
        # boulder spanning above and below water
        boulder(c, 760, 1150, 620, 700, '#7f878b', 9, 5)
        c.drawRect(skia.Rect.MakeLTRB(-1500, wy - 8, 4500, wy + 8), fillp('#ffffff', 0.5))
        water_band(c, -1500, 4500, wy - 6, wy + 30, T * 1.5, 1.0, ('#7cc4e0', '#5aa7c9', '#3b8bb3'), 2, 220, a=0.85)
        # Edoardo braced on the boulder top, gripping taut rope
        ex, ey = 700, 460
        tug = math.sin(T * 6) * 4
        def rope_hold(cv, hands, u):
            pass
        person(c, 'edoardo', ex, ey, 360, T, legs='brace', facing=0.6, expr='strain', lhand=(14, -40), rhand=(24, -36),
               tilt=-10 + tug * 0.5, gest_hand=None, sweat=True, rot=-8)
        # taut rope from his hands down into the water to Nicola
        nx, ny = 1300 + math.sin(T * 2) * 20, 930 + math.sin(T * 1.6) * 14
        c.drawPath(poly([(ex + 90, ey - 140), (nx - 40, ny - 60)], False), strokep('#e8d6a0', 9))
        c.drawPath(poly([(ex + 90, ey - 140), (nx - 40, ny - 60)], False), strokep(INK, 2, 0.6))
        swimmer(c, 'nicola', nx, ny, 300, T, ang=-60 + math.sin(T * 3) * 8, hands=((-24, -82), (20, -78)), kick=1.4)
        bubbles(c, None, T, nx + 40, ny - 200, 6, 0.6, 1.0, 5)
    current_lines(c, cam, T, 16, 1300, 0.5, 1.0, 640, 1150, 3)
    vignette(c, 0.3)


def sh_terrace(c, lt, dur, T):
    if lt >= 2.0:
        return terrace_close(c, lt - 2.0, dur - 2.0, T)
    cam = cam_path(lt, 2.0, (960, 520, 1.12), (930, 480, 1.25), 'lin', 0.4, 24)
    set_terrace(c, cam, T)

    def finger(cv, hands, u):
        if hands[0]:
            hx, hy = hands[0]
            # raised finger with a pale band where the ring was
            draw(cv, rrect(hx - 1.4 * u, hy - 9 * u, 2.8 * u, 9 * u, 1.4 * u), SKIN_IR, INK, 0.5 * u)
            cv.drawRect(skia.Rect.MakeXYWH(hx - 1.4 * u, hy - 5.6 * u, 2.8 * u, 1.4 * u), fillp('#fff4e8'))
            cv.drawCircle(hx, hy, 3.0 * u, fillp(SKIN_IR))
            cv.drawCircle(hx, hy, 3.0 * u, strokep(INK, 0.8 * u))
    with layer(c, cam, 1.0):
        person(c, 'patrick', 900, 1000, 600, T, facing=-0.35, expr='sad', lhand=(-8, -62), rhand=(14, -34), hold=finger,
               gest_hand='rhand')
        glow(c, 1300, 760, 300, '#ffcf8a', 0.25)
    vignette(c, 0.35)
    grade(c, '#d07a6a', 0.15)


def terrace_close(c, lt, dur, T):
    cam = cam_path(lt, dur, (1060, 470, 1.7), (1080, 450, 1.82), 'lin', 0.3, 44)
    set_terrace(c, cam, T)
    with layer(c, cam, 1.0):
        person(c, 'patrick', 1180, 1000, 600, T, facing=-0.45, expr='sad', lhand=(-15, -32), rhand=(14, -34), gest_hand=None)
    # his hand in the foreground: the pale band where the ring used to be
    big_hand(c, 560 + math.sin(T * 1.3) * 6, 830, 2.1, -62 + math.sin(T) * 2, pale=True)
    vignette(c, 0.35)
    grade(c, '#d07a6a', 0.15)


def sh_nicola_search(c, lt, dur, T):
    x = 400 + lt * 240
    cam = cam_path(lt, dur, (700, 560, 1.15), (700 + dur * 240, 600, 1.2), 'lin', 0.5, 25)
    set_underwater(c, cam, T, 880, 0.15, True, 1.0)
    with layer(c, cam, 1.0):
        swimmer(c, 'nicola', x, 660 + math.sin(T * 1.5) * 12, 330, T, ang=-95, hands=((-28, -80), (-20, -60)), kick=0.8,
                expr='thinking')
        bubbles(c, None, T, x + 150, 520, 5, 0.6, 1.0, 7)
        # tiny glint far ahead on the sand (foreshadow)
        gx = 1650
        tw = 0.5 + 0.5 * math.sin(T * 5)
        if lt > 2.0:
            gold_ring(c, gx, 905, 8, 0, 0.3, 1.5, sparkle=0.6 * tw)
    current_lines(c, cam, T, 14, 500, 0.25, 1.0)
    vignette(c, 0.45)


def sh_glint(c, lt, dur, T):
    # creep, then punch-in on "glint"
    if lt < 0.55:
        cam = cam_path(lt, 0.55, (960, 560, 1.0), (960, 580, 1.08), 'lin', 0.3, 26)
    else:
        cam = cam_path(lt - 0.55, 0.45, (960, 580, 1.08), (1010, 610, 1.45), 'out', 0.3, 26)
    with layer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-500, -500, 2500, 1600), fillp(None, 1, shader=lin(0, 0, 0, 1080, ['#3a7f8f', '#c4ad7c', '#a3895a'], [0, 0.35, 1])))
        for k in range(50):
            x = -300 + (k * 97) % 2500
            y = 420 + (k * 53) % 700
            draw(c, oval(x, y, 30 + (k % 4) * 10, 18 + (k % 3) * 6), ['#8d8073', '#a39a8a', '#6f6458', '#b3a898'][k % 4], INK, 2.5)
        for k in range(14):
            xx = -200 + (k * 211 + T * 40) % 2400
            c.drawOval(skia.Rect.MakeXYWH(xx, 500 + (k % 6) * 90, 180, 30), strokep('#f2e4b6', 4, 0.4))
        # half-buried ring
        rx, ry = 1010, 610
        sp = ramp(lt, 0.55, 0.75) * (1 - 0.4 * ramp(lt, 1.6, 2.4)) * (0.8 + 0.2 * math.sin(T * 9))
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(-500, -500, 2500, ry + 6))
        gold_ring(c, rx, ry - 4, 46, -12, 0.42, 4)
        c.restore()
        draw(c, smooth_path([(rx - 80, ry + 4), (rx - 20, ry - 6), (rx + 50, ry + 2), (rx + 90, ry + 12), (rx - 90, ry + 16)]),
             '#c4ad7c', None, 0)
        if sp > 0:
            gold_ring(c, rx, ry - 4, 0.001, 0, 0.4, 0.1, 0)
            s = 60 * sp
            for ang in (0, 90, 45, 135):
                L = s if ang in (0, 90) else s * 0.5
                c.save()
                c.translate(rx - 24, ry - 20)
                c.rotate(ang + T * 20)
                c.drawPath(poly([(-L, 0), (-L * 0.1, -L * 0.1), (0, -L), (L * 0.1, -L * 0.1), (L, 0), (L * 0.1, L * 0.1), (0, L),
                                 (-L * 0.1, L * 0.1)]), fillp('#ffffff', 0.95))
                c.restore()
        # Nicola's hand reaches in to pick it up
        reach = ease_out(ramp(lt, 2.3, 3.0))
        if reach > 0:
            hx = lerp(1700, 1090, reach)
            hy = lerp(200, 560, reach)
            c.drawLine(hx + 300, hy - 300, hx, hy, strokep(INK, 16))
            c.drawCircle(hx, hy, 60, fillp('#d6a077'))
            c.drawCircle(hx, hy, 60, strokep(INK, 5))
        bubbles(c, None, T, 700, 900, 6, 0.5, 1.0, 9)
    vignette(c, 0.4)


def sh_surface(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 470, 1.15), (960, 450, 1.28), 'out', 0.5, 27)
    set_river_bg(c, cam, T, water_y=640, village_x=1400)
    with layer(c, cam, 0.88):
        water_band(c, -1500, 4500, 640, 1400, T, 1.0, ('#5aa7c9', '#3b8bb3', '#2a6f97'), 14, 90)
    with layer(c, cam, 1.0):
        boulder(c, 420, 800, 520, 300, '#8a8f93', 3, 5, wet=1)
        boulder(c, 1560, 820, 480, 280, '#8a8f93', 6, 5, wet=1)
        rise = ease_out(ramp(lt, 0.0, 0.45))
        cheer = ramp(lt, 0.8, 1.0)
        person(c, 'filippo', 420, 560, 380, T, facing=0.5, expr='laugh' if cheer else 'surprised',
               lhand=(-18, -82) if cheer else (-15, -32), rhand=(18, -82) if cheer else (15, -32), gest_hand=None,
               legs='walk' if cheer else 'stand', phase=T * 9)
        person(c, 'edoardo', 1560, 580, 380, T, facing=-0.5, expr='laugh' if cheer else 'surprised',
               lhand=(-18, -82) if cheer else (-15, -32), rhand=(18, -82) if cheer else (15, -32), gest_hand=None)

        def ring_palm(cv, hands, u):
            if hands[1]:
                hx, hy = hands[1]
                gold_ring(cv, hx + 2 * u, hy - 6 * u, 6.0 * u, -10, 0.45, 0.6 * u, sparkle=0.6 + 0.4 * math.sin(T * 6))
        ny = 1300 - rise * 290
        person(c, 'nicola', 960, ny, 520, T, facing=0.0, expr='laugh', lhand=(-24, -70), rhand=(30, -80), hold=ring_palm,
               gest_hand=None, shadow=False)
        mask(c, 960, ny - 72 * 520 / 90 - 13 * 520 / 90, 520 / 90 * 0.9)
        water_front(c, -600, 2600, 860, T, 600, 0.65)
        splash(c, 960, 860, 1.8, lt - 0.05, 1.0)
        foam(c, 960, 862, 260, T, 0.9)
        # droplets dripping
        for k in range(5):
            ph = (T * 1.5 + k / 5) % 1
            c.drawCircle(900 + k * 30, ny - 380 + ph * 300, 6, fillp('#dff6ff', 0.8 * (1 - ph)))
    vignette(c, 0.2)


def sh_text_fly(c, lt, dur, T):
    u = ease_io(clamp(lt / dur))
    cam = Cam(lerp(700, 4300, u) + math.sin(lt) * 6, 540 - math.sin(u * math.pi) * 60, 1.0)
    sky(c, ['#5a6fa8', '#e09a7a', '#f6c48a'], [0, 0.6, 1])
    with layer(c, cam, 0.15):
        glow(c, 2400, 500, 400, '#fff0b0', 0.5)
    clouds(c, cam, T, 160, 8, 10, 0.2, '#ffe0c8', 0.7, 9, 6000)
    with layer(c, cam, 0.4):
        ridge(c, -1500, 6000, 560, 110, 1.4, 0.7, '#7a8f6a', True, 1500, 3)
        village(c, 1700, 520, 1.1, T)
    with layer(c, cam, 0.7):
        ridge(c, -1500, 7000, 700, 90, 3.3, 1.0, '#5f7f4f', True, 1500, 3)
        for k in range(18):
            x = -800 + k * 420
            cypress(c, x, ridge_y(x, 700, 90, 3.3, 1.0) + 40, 170, '#2f4a35', T, k)
    with layer(c, cam, 1.0):
        # river at the start
        water_band(c, -1500, 1800, 820, 1300, T, 1.0, ('#5aa7c9', '#3b8bb3', '#2a6f97'), 8, 90)
        c.drawRect(skia.Rect.MakeLTRB(1800, 820, 6500, 1400), fillp('#7f9a5a'))
        c.drawLine(1800, 820, 6500, 820, strokep(INK, 4, 0.7))
        for k in range(3):
            person(c, ('filippo', 'nicola', 'edoardo')[k], 300 + k * 170, 900, 260, T, expr='laugh', rhand=(18, -80),
                   lhand=(-15, -32), gest_hand=None)
        # the stone house with the lit kitchen window
        hx = 4300
        stone_wall(c, hx - 360, 260, hx + 420, 900, '#cfa679', 3, 50)
        c.drawPath(poly([(hx - 420, 270), (hx + 30, 60), (hx + 480, 270)]), fillp('#b5583a'))
        c.drawPath(poly([(hx - 420, 270), (hx + 30, 60), (hx + 480, 270)]), strokep(INK, 5))
        c.drawRect(skia.Rect.MakeXYWH(hx - 120, 420, 300, 240), fillp('#ffd38a'))
        glow(c, hx + 30, 540, 300, '#ffd38a', 0.5)
        draw(c, rect(hx - 120, 420, 300, 240), None, '#f1e8d6', 12)
        # silhouette of Patrick at the stove inside
        c.drawCircle(hx + 40, 520, 50, fillp('#6b4a3a', 0.7))
        c.drawOval(skia.Rect.MakeXYWH(hx - 10, 570, 100, 120), fillp('#3f8a4f', 0.7))
        steam(c, hx + 120, 640, T, 0.6, 4, 0.4)
        # bubble flying ahead of the camera
        bx = lerp(600, 4250, ease_io(clamp((lt - 0.2) / (dur - 0.6))))
        by = 700 - math.sin(clamp((lt - 0.2) / (dur - 0.6)) * math.pi) * 420 + (u > 0.95) * 0
        if lt < dur - 0.25:
            for k in range(6):
                tx = bx - (k + 1) * 50
                c.drawCircle(tx, by + 30 + math.sin(k + T * 4) * 10, 10 - k, fillp('#ffffff', 0.6 - k * 0.09))
            c.save()
            c.translate(bx, by)
            c.rotate(math.sin(T * 4) * 5)
            draw(c, rrect(-130, -80, 260, 160, 30), '#ffffff', INK, 5)
            c.drawPath(poly([(-40, 78), (-70, 120), (0, 78)]), fillp('#ffffff'))
            c.drawPath(poly([(-40, 80), (-70, 120), (0, 80)], False), strokep(INK, 5))
            ring_photo(c, -110, -62, 120, 124, T)
            draw_text(c, '1 new', 60, -10, font(FONT_SUB, 30), INK, 'center')
            draw_text(c, 'message', 60, 26, font(FONT_UI, 26), '#555555', 'center')
            c.restore()
    vignette(c, 0.25)
    hang_tag(c, 'DAY 9', lt - 1.2, 1720, 2.6)


def sh_celebrate(c, lt, dur, T):
    cam = cam_path(lt, dur, (1000, 540, 1.1), (1020, 540, 1.13), 'lin', 0.7, 29)
    set_kitchen(c, cam, T, phone_on=None, bubbling=1.0 * ramp(lt, 1.0, 1.6), steam_a=0.7)
    with layer(c, cam, 0.92):
        # pot boiling over: foam drips
        over = ramp(lt, 1.6, 3.0)
        if over > 0:
            fp = skia.Path()
            for k in range(7):
                fp.addCircle(880 + k * 27, 470 + 6 * math.sin(T * 6 + k), 20 + 6 * hash01(k, 2))
            for k in (0, 2, 5, 6):
                fp.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(872 + k * 27, 470, 22, 20 + over * (30 + 40 * hash01(k, 3))), 11, 11))
            c.drawPath(fp, fillp('#fff6e0'))
            c.drawPath(fp, strokep(INK, 3))

        def phone_up(cv, hands, u):
            if hands[1]:
                hx, hy = hands[1]
                draw(cv, rrect(hx - 4.5 * u, hy - 15 * u, 9 * u, 16 * u, 2 * u), '#1c1d22', INK, 0.6 * u)
                cv.drawRect(skia.Rect.MakeXYWH(hx - 3.5 * u, hy - 14 * u, 7 * u, 13 * u), fillp('#cfe6ff'))
        jump = abs(math.sin(T * 7)) * 30
        person(c, 'patrick', 600, 960 - jump * 0.5, 560, T, facing=0.3, expr='laugh', rhand=(18, -92), lhand=(-20, -60),
               hold=phone_up, gest_hand='lhand', tear=True)
        enter = ease_out(ramp(lt, 0.3, 1.2))
        person(c, 'joanne', lerp(1900, 1250, enter), 960, 520, T, facing=-0.6, expr='laugh', lhand=(-20, -80), rhand=(20, -80),
               legs='walk' if enter < 1 else 'stand', phase=T * 10)
        for i, (n, hs) in enumerate((('girl1', 0.66), ('girl2', 0.57), ('girl3', 0.48))):
            e = ease_out(ramp(lt, 0.6 + i * 0.25, 1.4 + i * 0.25))
            j = abs(math.sin(T * 8 + i * 1.3)) * 50 * e
            person(c, n, lerp(2000, 1450 + i * 150, e), 960 - j, 560 * hs, T, facing=-0.5, expr='laugh',
                   lhand=(-18, -80), rhand=(18, -80), shadow_a=0.2)
        steam(c, 960, 470, T, 1.3, 6, 0.6)
    vignette(c, 0.35)
    grade(c, '#ffa860', 0.2)


def sh_post_no(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 540, 1.0), (960, 540, 1.1), 'lin', 0.3, 30)
    with layer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-300, -300, 2300, 1400), fillp('#8a5a34'))
        for k in range(12):
            c.drawLine(-300, -300 + k * 130, 2300, -300 + k * 130, strokep('#6e4726', 4))
        # padded envelope addressed to Ireland
        out = ease_in(ramp(lt, 0.9, 1.4))
        ex = 600 - out * 1400
        draw(c, rrect(ex - 300, 320, 600, 420, 16), '#e8cf9a', INK, 6)
        draw(c, rrect(ex + 150, 350, 110, 130, 6), '#c33631', INK, 4)
        f = font(FONT_HAND, 40)
        draw_text(c, 'The Mohrs', ex - 230, 520, f, INK)
        draw_text(c, 'Dún Laoghaire', ex - 230, 580, f, INK)
        draw_text(c, 'IRELAND', ex - 230, 640, f, INK)
        # small ring box stays
        draw(c, rrect(1220, 460, 260, 200, 20), '#7a1f33', INK, 6)
        draw(c, rrect(1240, 400, 220, 90, 18), '#8f2a40', INK, 6)
        c.drawOval(skia.Rect.MakeXYWH(1300, 520, 100, 60), fillp('#4a1020'))
        gold_ring(c, 1350, 535, 40, 0, 0.45, 4)
        if lt > 0.55:
            s = 1.7 - 0.7 * ease_out(ramp(lt, 0.55, 0.75))
            c.save()
            c.translate(ex, 520)
            c.scale(s, s)
            c.rotate(-8)
            c.drawLine(-200, -150, 200, 150, strokep('#c33631', 26))
            c.drawLine(200, -150, -200, 150, strokep('#c33631', 26))
            c.restore()
    vignette(c, 0.35)


def plane(c, x, y, ang, s=1.0):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    draw(c, rrect(-60, -12, 120, 24, 12), '#ffffff', INK, 4)
    draw(c, poly([(-10, -8), (20, -8), (-10, -70), (-30, -70)]), '#e8e2d4', INK, 4)
    draw(c, poly([(-10, 8), (20, 8), (-10, 70), (-30, 70)]), '#e8e2d4', INK, 4)
    draw(c, poly([(-60, -6), (-45, -6), (-60, -30), (-70, -30)]), '#c33631', INK, 3)
    c.restore()


def sh_map(c, lt, dur, T):
    a = map_xy(10.6, 44.0)
    b = map_xy(-6.1, 53.3)
    fly = ease_io(ramp(lt, 0.9, dur - 1.0))
    mx, my = lerp(a[0], b[0], fly), lerp(a[1], b[1], fly) - math.sin(fly * math.pi) * 120
    cam = cam_path(lt, dur, (a[0] - 100, a[1] - 80, 1.6), (b[0] + 120, b[1] + 60, 1.7), 'io', 0.3, 31)
    cam.z = lerp(1.6, 1.25, math.sin(fly * math.pi)) if 0 < fly < 1 else cam.z
    set_map(c, cam, T)
    with layer(c, cam, 1.0):
        # dotted route
        n = 40
        for k in range(int(n * fly)):
            t = k / n
            x = lerp(a[0], b[0], t)
            y = lerp(a[1], b[1], t) - math.sin(t * math.pi) * 120
            c.drawCircle(x, y, 5, fillp('#ffffff'))
            c.drawCircle(x, y, 5, strokep(INK, 1.5))
        for (p, t0, lab) in ((a, 0.1, 'Bagni di Lucca'), (b, dur - 1.1, 'Dún Laoghaire')):
            d = ease_out(ramp(lt, t0, t0 + 0.3))
            if d > 0:
                py = p[1] - 60 * (1 - d)
                draw(c, smooth_path([(p[0], py), (p[0] - 18, py - 30), (p[0], py - 52), (p[0] + 18, py - 30)]), '#c33631', INK, 3)
                c.drawCircle(p[0], py - 32, 7, fillp('#ffffff'))
                draw_text(c, lab, p[0] + 26, py - 20, font(FONT_HAND, 28), INK, 'left', '#ffffff', 6)
        if 0 < fly < 1:
            t2 = min(fly + 0.01, 1)
            nx, ny = lerp(a[0], b[0], t2), lerp(a[1], b[1], t2) - math.sin(t2 * math.pi) * 120
            ang = math.degrees(math.atan2(ny - my, nx - mx))
            plane(c, mx, my, ang, 0.55)
        elif fly <= 0:
            plane(c, a[0], a[1] - 10, -60, 0.55)
    vignette(c, 0.3)


def sh_door(c, lt, dur, T):
    # music drifts in; knock at ~1.5s (130.0); door opens 2.4s; Patrick appears
    if lt < 2.0:
        cam = cam_path(lt, 2.0, (960, 520, 1.0), (960, 560, 1.18), 'io', 0.4, 32)
    else:
        cam = cam_path(lt - 2.0, dur - 2.0, (960, 560, 1.18), (960, 580, 1.25), 'lin', 0.4, 32)
    op = ramp(lt, 2.4, 3.1)
    set_door(c, cam, T, op, op)
    with layer(c, cam, 1.0):
        if op > 0.2:
            person(c, 'patrick', 990, 880, 420, T, facing=0.2, expr='surprised', lhand=(-15, -32), rhand=(18, -46),
                   gest_hand=None)
            # redraw the open door leaf on top (hinge side)
            e = ease_io(op)
            lw = 400 * (1 - 0.82 * e)
            draw(c, rect(760, 400, lw, 440), shade('#2f7d4f', -0.15 * e), INK, 5)
        # knocker shake
        if 1.4 < lt < 2.1:
            for k in range(3):
                if abs(lt - (1.45 + k * 0.2)) < 0.07:
                    for s in (-1, 1):
                        c.drawLine(960 + s * 50, 560, 960 + s * 80, 560, strokep(INK, 5))
        music_notes(c, 200, 900, T, 5, 1.0)
    vignette(c, 0.22)
    place_strip(c, 'DÚN LAOGHAIRE · IRELAND', lt - 0.1, 3.2)


def sh_hobbits(c, lt, dur, T):
    if lt < 2.75:
        cam = cam_path(lt, 2.75, (1180, 600, 1.05), (1240, 600, 1.12), 'lin', 0.4, 33)
    else:
        # punch-in on "dressed as hobbits"
        cam = cam_path(lt - 2.75, dur - 2.75, (1300, 560, 1.32), (1320, 560, 1.38), 'lin', 0.4, 33)
    set_door(c, cam, T, 1.0, 1.0)
    with layer(c, cam, 1.0):
        person(c, 'patrick', 990, 880, 420, T, facing=0.5, expr='surprised' if lt < 3.2 else 'laugh', lhand=(-20, -70),
               rhand=(20, -70), gest_hand=None)
        draw(c, rect(760, 400, 72, 440), shade('#2f7d4f', -0.15), INK, 5)

        def uke(cv, hands, u):
            if hands[0]:
                ukulele(cv, hands[0][0] + 6 * u, hands[0][1] + 2 * u, u * 0.28, -20)

        def ring_up(cv, hands, u):
            if hands[1]:
                hx, hy = hands[1]
                gold_ring(cv, hx, hy - 5 * u, 4.4 * u, 0, 0.5, 0.6 * u)
        strum = math.sin(T * 14) * 3
        person(c, 'filippo', 1310, 935, 420, T, costume=True, facing=-0.4, expr='happy', lhand=(-8, -40), rhand=(10 + strum, -44),
               hold=uke, gest_hand=None)
        person(c, 'nicola', 1520, 940, 430, T, costume=True, facing=-0.5, expr='laugh', lhand=(-15, -32), rhand=(18, -92),
               hold=ring_up, gest_hand=None)
        person(c, 'edoardo', 1730, 935, 420, T, costume=True, facing=-0.6, expr='happy', lhand=(-24, -66), rhand=(15, -32),
               gest_hand=None)
        music_notes(c, 1280, 560, T, 4, 0.9)
    vignette(c, 0.22)


def sh_glendalough(c, lt, dur, T):
    cam = cam_path(lt, dur, (900, 520, 1.1), (1100, 540, 1.15), 'lin', 0.5, 34)
    sky(c, ['#b8c4c8', '#dde3e0'])
    with layer(c, cam, 0.15):
        ridge(c, -1500, 4500, 500, 200, 1.0, 0.6, '#5f7a62', True, 1500, 2.5)
    with layer(c, cam, 0.35):
        ridge(c, -1500, 4500, 600, 120, 4.0, 0.9, '#3f5f45', True, 1500, 3)
        # round tower
        tx = 1500
        draw(c, rect(tx, 300, 60, 330), '#b9b4a8', INK, 4)
        draw(c, poly([(tx - 6, 300), (tx + 30, 230), (tx + 66, 300)]), '#8f8a80', INK, 4)
        c.drawRect(skia.Rect.MakeXYWH(tx + 22, 330, 16, 26), fillp('#3a3a3a'))
        for k in range(14):
            tree(c, -1000 + k * 330, 640, 120, '#2f5a3a', T, k)
    with layer(c, cam, 0.7):
        water_band(c, -1500, 4500, 660, 900, T * 0.4, 1.0, ('#9fb4b8', '#7f989c', '#6a8388'), 8, 40, ripple_a=0.35)
    with layer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-1500, 880, 4500, 1600), fillp('#6f8a4f'))
        c.drawLine(-1500, 880, 4500, 880, strokep(INK, 4, 0.7))
        for k in range(60):
            x = -1400 + k * 100
            c.drawLine(x, 900 + (k % 3) * 30, x + 10, 880 + (k % 3) * 30, strokep('#4f6a35', 4))
        walk = lt * 90
        for i, n in enumerate(('patrick', 'filippo', 'nicola', 'edoardo')):
            person(c, n, 600 + i * 190 + walk, 980, 380, T, legs='walk', phase=T * 6 + i, facing=0.7, expr='smile',
                   lhand=(-12, -30), rhand=(12, -30), gest_hand=None)
    # mist bands
    for k in range(4):
        y = 560 + k * 90
        x = (T * 30 * (k + 1)) % 600 - 600
        c.drawRect(skia.Rect.MakeXYWH(x, y, W + 1200, 50), fillp('#ffffff', 0.18, blur=20))
    vignette(c, 0.3)
    place_strip(c, 'GLENDALOUGH · CO. WICKLOW', lt, 2.4)


def pint(cv, x, y, u, tilt=0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(tilt)
    p = poly([(-5 * u, -16 * u), (5 * u, -16 * u), (4 * u, 2 * u), (-4 * u, 2 * u)])
    draw(cv, p, '#1d120c', INK, 0.6 * u)
    cv.drawRect(skia.Rect.MakeLTRB(-5 * u, -16 * u, 5 * u, -12.5 * u), fillp('#f3e6c8'))
    cv.drawPath(p, strokep(INK, 0.6 * u))
    cv.restore()


def sh_pub(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 560, 1.12), (960, 520, 1.2), 'io', 0.5, 35)
    sky(c, ['#3a2418', '#2a1a12'])
    with layer(c, cam, 0.9):
        c.drawRect(skia.Rect.MakeLTRB(-400, -300, 2400, 1400), fillp('#5a3420'))
        for k in range(30):
            c.drawLine(-400 + k * 100, -300, -400 + k * 100, 700, strokep('#4a2a18', 4))
        for r in range(3):
            draw(c, rect(-300, 140 + r * 150, 2600, 16), '#7a4e2c', INK, 3)
            for k in range(40):
                bx = -280 + k * 66
                col = ['#3f6a3a', '#8a3a2a', '#c9a24a', '#2a3a5a'][k % 4]
                draw(c, rrect(bx, 70 + r * 150, 30, 70, 6), col, INK, 2.5)
        for x in (300, 960, 1620):
            lamp_pendant(c, x, -300, 40, T, '#c9a24a')
        draw(c, rect(-300, 700, 2600, 400), '#6e4726', INK, 5)
        draw(c, rect(-300, 680, 2600, 30), '#8a5a34', INK, 5)
        for k in range(14):
            draw(c, rect(-260 + k * 190, 740, 150, 300), '#7a5030', INK, 3)
    clink = ease_out(ramp(lt, 0.4, 0.9))
    with layer(c, cam, 1.0):
        names = ('filippo', 'patrick', 'nicola', 'edoardo')
        for i, n in enumerate(names):
            x = 540 + i * 280
            cx = 960
            hx = lerp(22, (cx - x) / (430 / 90) * 0.35, clink)
            person(c, n, x, 1000, 430, T, facing=0.3 if x < cx else -0.3, expr='laugh',
                   rhand=(hx, lerp(-50, -96, clink)), lhand=(-15, -32), gest_hand=None,
                   hold=lambda cv, hands, u: pint(cv, hands[1][0], hands[1][1] + 2 * u, u, 0) if hands[1] else None)
        if lt > 0.9:
            a = 1 - ramp(lt, 0.9, 1.5)
            for k in range(6):
                ang = k / 6 * 2 * math.pi
                c.drawLine(960 + math.cos(ang) * 40, 520 + math.sin(ang) * 40, 960 + math.cos(ang) * 80, 520 + math.sin(ang) * 80,
                           strokep('#fff4c0', 5, a))
    vignette(c, 0.45)
    grade(c, '#ff9a50', 0.18)


def set_dining(c, cam, T):
    with layer(c, cam, 0.92):
        c.drawRect(skia.Rect.MakeLTRB(-400, -300, 2400, 1400), fillp('#2f5f5a'))
        for r in range(20):
            for k in range(30):
                x = -380 + k * 90 + (r % 2) * 45
                y = -280 + r * 80
                c.drawCircle(x, y, 7, fillp('#e6d9b8', 0.35))
        window_view(c, 200, 120, 340, 320, T, 'night', None)
        draw(c, rect(1400, 140, 220, 170), '#d9a85a', INK, 5)
        c.drawRect(skia.Rect.MakeXYWH(1420, 160, 180, 130), fillp('#7fa8c8'))
        ridge(c, 1420, 1600, 260, 20, 2, 5, '#4f7a4a', False, 290)
        lamp_pendant(c, 960, -300, 160, T)
        c.drawRect(skia.Rect.MakeLTRB(-400, 900, 2400, 1400), fillp('#6e4726'))


def table_front(c, x0, x1, y, T):
    draw(c, rect(x0, y, x1 - x0, 360), '#f1e8d6', INK, 5)
    for k in range(int((x1 - x0) / 60)):
        c.drawLine(x0 + k * 60, y + 10, x0 + k * 60, y + 360, strokep('#e0d4bc', 3))
    draw(c, rect(x0 - 10, y - 14, x1 - x0 + 20, 24), '#e8dcc4', INK, 4)


def sh_dinner(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 540, 1.05), (960, 540, 1.1), 'lin', 0.5, 36)
    set_dining(c, cam, T)
    with layer(c, cam, 1.0):
        seats = [('girl3', 260), ('joanne', 470), ('filippo', 680), ('patrick', 900), ('nicola', 1120), ('girl1', 1340),
                 ('edoardo', 1550), ('girl2', 1740)]
        for i, (n, x) in enumerate(seats):
            hs = CAST[n]['hs']
            lift = 0 if not CAST[n].get('kid') else 80
            person(c, n, x, 960 - lift * 0 + (1 - hs) * 0, 470 * (hs if not CAST[n].get('kid') else hs * 1.25), T,
                   facing=0.3 if x < 960 else -0.3, expr='laugh' if (i + int(T * 1.5)) % 3 == 0 else 'happy', legs='none',
                   lhand=(-15, -50 + 6 * math.sin(T * 3 + i)), rhand=(15, -50), gest_hand=None)
        table_front(c, 120, 1820, 760, T)
        for k in range(8):
            draw(c, oval(260 + k * 212, 752, 60, 12), '#ffffff', INK, 3)
        draw(c, oval(960, 742, 110, 26), '#c9a24a', INK, 4)
        steam(c, 960, 720, T, 0.6, 4, 0.4)
        for k in range(3):
            draw(c, rrect(560 + k * 400, 690, 20, 60, 6), '#fff4dc', INK, 3)
            glow(c, 570 + k * 400, 682, 50, '#ffcf7a', 0.7 + 0.1 * math.sin(T * 8 + k))
    vignette(c, 0.4)
    grade(c, '#ffa860', 0.15)


def sh_bracelets(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 540, 1.0), (960, 560, 1.12), 'lin', 0.3, 37)
    with layer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-300, -300, 2300, 1400), fillp('#5a2a3a'))
        for k in range(20):
            c.drawLine(-300, -300 + k * 90, 2300, -300 + k * 90 + 40, strokep('#4a2030', 3))
        for i, (nm, t0) in enumerate((('FILIPPO', 0.1), ('NICOLA', 0.9), ('EDOARDO', 1.7))):
            e = ease_out(ramp(lt, t0, t0 + 0.2))
            if e <= 0:
                continue
            x = 960 + (i - 1) * 560 + (1 - e) * 2200
            y = 540 + (i - 1) * 30
            c.drawOval(skia.Rect.MakeXYWH(x - 230, y - 120, 460, 240), strokep('#9aa3aa', 40))
            c.drawOval(skia.Rect.MakeXYWH(x - 230, y - 120, 460, 240), strokep('#e3e8ec', 30))
            c.drawArc(skia.Rect.MakeXYWH(x - 220, y - 112, 300, 160), 200, 50, False, strokep('#ffffff', 8, 0.9))
            c.drawOval(skia.Rect.MakeXYWH(x - 250, y - 140, 500, 280), strokep(INK, 4))
            c.drawOval(skia.Rect.MakeXYWH(x - 210, y - 100, 420, 200), strokep(INK, 4))
            # engraved plate on the band
            draw(c, rrect(x - 130, y + 82, 260, 56, 28), '#d4dade', INK, 4)
            draw_text(c, nm, x, y + 122, font(FONT_SUB, 34), '#4a5258', 'center')
    vignette(c, 0.4)


def sh_filippo(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 640, 1.3), (960, 610, 1.48), 'lin', 0.4, 38)
    set_dining(c, cam, T)
    with layer(c, cam, 1.0):
        look = ease_io(ramp(lt, 0.2, 1.0))
        sp = spec('filippo')

        def band(cv, hands, u):
            if hands[1]:
                hx, hy = hands[1]
                bx, by = hx + 3.2 * u, hy + 2.4 * u
                cv.drawOval(skia.Rect.MakeXYWH(bx - 3.6 * u, by - 1.8 * u, 7.2 * u, 3.6 * u), strokep('#9aa3aa', 2.2 * u))
                cv.drawOval(skia.Rect.MakeXYWH(bx - 3.6 * u, by - 1.8 * u, 7.2 * u, 3.6 * u), strokep('#eef2f5', 1.4 * u))
                cv.drawArc(skia.Rect.MakeXYWH(bx - 3.4 * u, by - 1.7 * u, 4 * u, 2 * u), 200, 60, False, strokep('#ffffff', 0.8 * u))
                tw = 0.5 + 0.5 * math.sin(T * 4)
                gold_ring(cv, bx - 2 * u, by - 1.2 * u, 0.01, 0, 0.5, 0.1, sparkle=0.0)
                cv.drawLine(bx - 2 * u - 2 * u * tw, by - 1.6 * u, bx - 2 * u + 2 * u * tw, by - 1.6 * u, strokep('#ffffff', 0.5 * u, tw))
                cv.drawLine(bx - 2 * u, by - 1.6 * u - 2 * u * tw, bx - 2 * u, by - 1.6 * u + 2 * u * tw, strokep('#ffffff', 0.5 * u, tw))
        person(c, 'filippo', 960, 1000, 560, T, sp=sp, facing=lerp(0.5, 0.15, ramp(lt, 2.0, 2.6)),
               expr='tender', rhand=(lerp(15, 4, look), lerp(-32, -46, look)), lhand=(-15, -32), gest_hand='lhand', hold=band)
        # soft background figures at the table
        table_front(c, 120, 1820, 1000, T)
    vignette(c, 0.4)
    grade(c, '#ffa860', 0.14)


def set_harbour(c, cam, T):
    sky(c, ['#3d2a5a', '#b8607a', '#f0a070', '#f6cf8a'], [0, 0.4, 0.75, 1])
    with layer(c, cam, 0.05):
        glow(c, 1300, 640, 380, '#ffe6a0', 0.7)
        c.drawCircle(1300, 640, 60, fillp('#fff0c0'))
    clouds(c, cam, T, 200, 5, 6, 0.08, '#f0a8a0', 0.55, 12)
    with layer(c, cam, 0.25):
        c.drawRect(skia.Rect.MakeLTRB(-1500, 660, 4500, 1600), fillp(None, 1, shader=lin(0, 660, 0, 1100, ['#e09a7a', '#6a4a7a'])))
        for k in range(20):
            y = 680 + k * 18
            x = 1300 - 40 - k * 8 + math.sin(T * 2 + k) * 10
            c.drawLine(x, y, x + 80 + k * 16, y, strokep('#ffe6a0', 3, 0.6))
        # East Pier with lighthouse
        draw(c, poly([(-1500, 650), (1700, 650), (1700, 676), (-1500, 676)]), '#5a4a5a', INK, 3)
        draw(c, rect(1640, 560, 50, 92), '#e8e0d0', INK, 3)
        draw(c, rect(1632, 540, 66, 22), '#c33631', INK, 3)
        glow(c, 1665, 548, 60, '#ffe6a0', 0.6 + 0.3 * math.sin(T * 2))
        # boats with masts
        for k in range(4):
            bx = 300 + k * 260
            by = 700 + math.sin(T * 1.4 + k) * 4
            draw(c, poly([(bx - 50, by), (bx + 50, by), (bx + 34, by + 18), (bx - 34, by + 18)]), '#f4efe4', INK, 2.5)
            c.drawLine(bx, by, bx, by - 110, strokep(INK, 3))
    with layer(c, cam, 1.0):
        draw(c, rect(-600, 820, 3200, 18), '#3a3a40', INK, 3)
        for k in range(50):
            c.drawLine(-600 + k * 70, 838, -600 + k * 70, 960, strokep('#3a3a40', 6))
        c.drawRect(skia.Rect.MakeLTRB(-600, 960, 2600, 1400), fillp('#8a7f78'))
        for k in range(30):
            c.drawLine(-600 + k * 120, 960, -650 + k * 120, 1400, strokep('#6d645e', 3))
        c.drawLine(-600, 960, 2600, 960, strokep(INK, 4))


def sh_patrick_ring(c, lt, dur, T, close=False):
    if not close:
        cam = cam_path(lt, dur, (960, 520, 1.1), (930, 460, 1.3), 'lin', 0.4, 39)
    else:
        cam = cam_path(lt, dur, (900, 420, 1.55), (880, 400, 1.7), 'lin', 0.4, 40)
    set_harbour(c, cam, T)
    with layer(c, cam, 1.0):
        sp = spec('patrick', ring_on=True)
        turn = math.sin(T * 2.2) * 2
        person(c, 'patrick', 880, 1040, 600, T, sp=sp, facing=0.35, expr='tender', lhand=(-4, -50 + turn), rhand=(6, -46),
               gest_hand=None, tilt=4)
        # the ring caught by warm evening light
        u = 600 / 90
        rx, ry = 880 - 4 * u + 1.6 * u, 1040 - 50 * u + turn * u + 0.6 * u
        gold_ring(c, rx, ry, 1.8 * u, turn * 20, 0.5, 0.5 * u, sparkle=0.35 + 0.25 * math.sin(T * 3))
    vignette(c, 0.35)
    grade(c, '#f0a070', 0.15)


def sh_patrick_ring_close(c, lt, dur, T):
    cam = cam_path(lt, dur, (1080, 440, 1.7), (1100, 420, 1.85), 'lin', 0.3, 40)
    set_harbour(c, cam, T)
    with layer(c, cam, 1.0):
        person(c, 'patrick', 1190, 1040, 600, T, facing=-0.4, expr='tender', lhand=(-15, -32), rhand=(14, -34), gest_hand=None)
    turn = ease_io(ramp(lt, 0.3, 2.4))
    big_hand(c, 600 + math.sin(T * 1.1) * 5, 860, 2.1, -60, ring=True, ring_slide=0.18 * (1 - turn) + 0.02 * math.sin(T * 4),
             sparkle=0.25 + 0.2 * math.sin(T * 3), ring_tilt=0.22 + 0.2 * abs(math.sin(lt * 1.8)))
    vignette(c, 0.35)
    grade(c, '#f0a070', 0.15)


def sh_hill(c, lt, dur, T):
    pull = ease_io(clamp(lt / dur))
    cam = Cam(lerp(915, 940, pull) + math.sin(lt) * 5, lerp(600, 530, pull), lerp(1.3, 0.98, pull))
    sky(c, ['#48296a', '#c46a7a', '#f0b789', '#f8dca0'], [0, 0.35, 0.7, 1])
    with layer(c, cam, 0.05):
        glow(c, 1500, 700, 500, '#ffe6a0', 0.7)
        c.drawCircle(1500, 720, 80, fillp('#fff0c0'))
    clouds(c, cam, T, 220, 6, 8, 0.1, '#f4b8a0', 0.6, 14)
    with layer(c, cam, 0.25):
        c.drawRect(skia.Rect.MakeLTRB(-1500, 700, 4500, 1600), fillp('#c08080'))
        for k in range(14):
            y = 710 + k * 10
            c.drawLine(1400 - k * 6, y, 1600 + k * 6, y, strokep('#ffe6a0', 3, 0.5))
        ridge(c, -1500, 4500, 740, 30, 2, 1.5, '#6a5a7a', True, 1600, 2)
    with layer(c, cam, 0.6):
        ridge(c, -1500, 4500, 830, 50, 5, 1.2, '#7a8f4a', True, 1600, 3)
    with layer(c, cam, 1.0):
        ridge(c, -1500, 4500, 940, 60, 1.5, 0.6, '#9aab52', True, 1700, 4)
        for k in range(70):
            x = -800 + k * 50
            yy = ridge_y(x, 940, 60, 1.5, 0.6)
            sw_ = math.sin(T * 2 + k * 0.5) * 6
            c.drawLine(x, yy + 20, x + sw_, yy - 10, strokep('#6f8a3a', 4))
        group = [('edoardo', 330), ('nicola', 530), ('girl1', 700), ('joanne', 850), ('patrick', 1030), ('girl3', 1190),
                 ('girl2', 1320), ('filippo', 1500)]
        for i, (n, x) in enumerate(group):
            y = ridge_y(x, 940, 60, 1.5, 0.6) + 20
            sp = spec(n, ring_on=(n == 'patrick'))
            hs = sp['hs']
            if n == 'patrick':
                st = dict(lhand=(-18, -72), rhand=(16, -40))
            elif n == 'joanne':
                st = dict(lhand=(-16, -40), rhand=(22, -54))
            else:
                st = dict(lhand=(-16, -40), rhand=(16, -40))
            person(c, n, x, y, 330 * hs, T, sp=sp, facing=0.0, expr='happy', gest_hand=None, **st)
        # ring glint on Patrick's raised hand ("A ring is small")
        px = 1030
        py = ridge_y(px, 940, 60, 1.5, 0.6) + 20
        u = 330 / 90
        gx, gy = px - 18 * u, py - 72 * u
        tw = ramp(lt, 0.4, 0.7) * (1 - ramp(lt, 2.0, 3.0)) * 0.9 + 0.25
        gold_ring(c, gx + 1.6 * u, gy + 0.6 * u, 1.4 * u, 0, 0.5, 0.5, sparkle=tw * (0.8 + 0.2 * math.sin(T * 7)))
    vignette(c, 0.3)


def sh_endcard(c, lt, dur, T):
    cam = cam_path(lt, dur, (960, 540, 1.08), (960, 540, 1.0), 'lin', 0.3, 41)
    sky(c, ['#3a2558', '#b05a78', '#f09a6a', '#f8d090'], [0, 0.4, 0.75, 1])
    with layer(c, cam, 0.05):
        glow(c, 960, 560, 520, '#ffe6a0', 0.7)
        c.drawCircle(960, 580, 90, fillp('#fff0c0'))
    clouds(c, cam, T, 220, 6, 6, 0.08, '#f4a8a0', 0.5, 15)
    with layer(c, cam, 0.2):
        ridge(c, -1500, 4500, 600, 90, 3.0, 0.8, '#5a3a62', True, 1500, 2.5)
    with layer(c, cam, 0.4):
        ridge(c, -1500, 4500, 660, 60, 6.0, 1.4, '#3f2a4f', True, 1500, 2.5)
        for k in range(12):
            x = -700 + k * 330
            cypress(c, x, ridge_y(x, 660, 60, 6.0, 1.4) + 30, 150, '#2a1d38', T, k)
    with layer(c, cam, 0.8):
        c.drawRect(skia.Rect.MakeLTRB(-1500, 680, 4500, 1600), fillp(None, 1, shader=lin(0, 680, 0, 1080, ['#e8a07a', '#8a5a7a', '#3a2a50'])))
        for k in range(26):
            y = 690 + k * 15
            w = 60 + k * 14
            x = 960 - w / 2 + math.sin(T * 1.5 + k) * 12
            c.drawLine(x, y, x + w, y, strokep('#ffe6a0', 3 + k * 0.1, 0.55))
        for k in range(16):
            xx = -200 + ((k * 170 + T * 25) % 2400)
            c.drawLine(xx, 760 + (k % 5) * 60, xx + 90, 760 + (k % 5) * 60, strokep('#ffffff', 2, 0.25))
    with layer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-600, 980, 2600, 1400), fillp('#2a1d2a'))
        ridge(c, -600, 2600, 990, 14, 2, 4, '#2a1d2a', True, 1400, 3)
        for k in range(40):
            x = -500 + k * 70
            c.drawLine(x, 1000, x + math.sin(T * 2 + k) * 8, 940 - (k % 3) * 20, strokep('#1f1620', 5))
    # logo
    a = ease_out(ramp(lt, 2.2, 3.0))
    if a > 0:
        f = font(FONT_SERIF, 150, 700)
        y = 470 - 20 * (1 - a)
        c.drawRect(skia.Rect.MakeXYWH(0, y - 190, W, 360), fillp(None, a, shader=lin(0, y - 190, 0, y + 170,
                   [hexc('#1a0f24', 0), hexc('#1a0f24', 0.45), hexc('#1a0f24', 0.45), hexc('#1a0f24', 0)], [0, 0.3, 0.75, 1])))
        draw_text(c, 'One Small Act', 960, y, f, '#fff6e6', 'center', '#3a2040', 10, a, a * 0.7)
        c.drawLine(960 - 260 * a, y + 50, 960 + 260 * a, y + 50, strokep('#ffe6a0', 4, a))
        draw_text(c, 'true stories of everyday kindness', 960, y + 110, font(FONT_UI, 40), '#fff0dc', 'center', '#3a2040', 6, a * 0.95, a * 0.6)
    vignette(c, 0.35)


# ------------------------------------------------------------------ timeline
SHOTS = [
    (0.00, 2.70, sh_phone_top),
    (2.70, 7.25, sh_kitchen_wide),
    (7.25, 13.60, sh_phone_pov),
    (13.60, 17.55, sh_patrick_frozen),
    (17.55, 19.90, sh_rewind),
    (19.90, 23.50, sh_river_establish),
    (23.50, 27.30, sh_family_walk_a),
    (27.30, 31.50, sh_family_walk_b),
    (31.50, 36.00, sh_jumps),
    (36.00, 38.30, sh_grab_hand),
    (38.30, 41.60, sh_ring_slip),
    (41.60, 46.55, sh_ring_tumble),
    (46.55, 52.60, sh_paralysed),
    (52.60, 54.00, sh_joanne_turns),
    (54.00, 59.00, sh_joanne_runs),
    (59.00, 65.00, sh_help),
    (65.00, 68.60, sh_names),
    (68.60, 71.50, sh_swap),
    (71.50, 75.00, sh_quest_joke),
    (75.00, 77.30, sh_mission),
    (77.30, 82.30, sh_kayaks),
    (82.30, 84.90, sh_tie_ropes),
    (84.90, 90.30, sh_dive),
    (90.30, 94.90, sh_edoardo_rope),
    (94.90, 99.50, sh_terrace),
    (99.50, 103.00, sh_nicola_search),
    (103.00, 106.25, sh_glint),
    (106.25, 111.20, sh_surface),
    (111.20, 115.30, sh_text_fly),
    (115.30, 120.40, sh_celebrate),
    (120.40, 122.20, sh_post_no),
    (122.20, 128.05, sh_map),
    (128.05, 131.50, sh_door),
    (131.50, 136.20, sh_hobbits),
    (136.20, 138.70, sh_glendalough),
    (138.70, 140.45, sh_pub),
    (140.45, 142.45, sh_dinner),
    (142.45, 145.42, sh_bracelets),
    (145.42, 151.30, sh_filippo),
    (151.30, 155.40, sh_patrick_ring),
    (155.40, 159.80, sh_patrick_ring_close),
    (159.80, 168.25, sh_hill),
    (168.25, 999.0, sh_endcard),
]


def shot_at(T):
    for (a, b, fn) in SHOTS:
        if a <= T < b:
            return a, b, fn
    return SHOTS[-1]
