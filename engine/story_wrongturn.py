"""Short: "The Wrong Turn" (2026-11). Story-specific sets, cast and shots on top of shortkit + rig.
python3 story_wrongturn.py audio | still t1 t2 ... | video
"""
import os, sys, math
import numpy as np
import skia
from gfx import *
import rig
from rig import draw_person, gesture
import shortkit as K
from shortkit import VCam, vlayer, vcam, VW, VH
from sets import glow, smooth_path

AUD = '/tmp/claude-0/-home-claude/cec319aa-a116-5716-8373-5faeca7260eb/scratchpad/wrongturn/audio'
MUSIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'music_warm_folk.mp3')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MP4 = os.path.join(REPO, 'videos', '2026-11-wrong-turn-short.mp4')
WORK = '/tmp/claude-0/-home-claude/cec319aa-a116-5716-8373-5faeca7260eb/scratchpad/wrongturn/work'
os.makedirs(WORK, exist_ok=True)

V = K.Voice(os.path.join(AUD, 'voiceover_full.wav'), os.path.join(AUD, 'timing.json'), tail=1.0)
TOTAL, NF = V.total, V.nf
COLORS = {'NARRATOR': '#ffffff', 'CASEY': '#ffd0c4', 'LARITA': '#ffd6e6', 'JAMES': '#d6e8ff'}
rig.EXPR['asleep'] = (0, 0, 'closed', 'smile0')

# ------------------------------------------------------------------ cast
SKIN_A, SKIN_B = '#e9bf98', '#b9835e'
CAST = {
    'casey': dict(name='casey', skin=SKIN_A, hair='short', hair_col='#5a4030', top='plaid', top_col='#b0352b', cap='#24476b',
                  pants='#3a4a66', shoes='#2a2a2a', hs=1.0, seed=11, stubble=True),
    'son': dict(name='son', skin=SKIN_A, hair='short', hair_col='#6a4a32', top='tee', top_col='#2f9e8a', pants='#3a4a66',
                shoes='#f2f2f2', hs=0.55, seed=12),
    'james': dict(name='james', skin=SKIN_B, hair='short', hair_col='#bdbdb6', beard=True, top='cardigan', top_col='#7a5a3c',
                  inner_col='#d9d0bc', pants='#4a4a52', shoes='#3a2a20', hs=1.0, seed=13),
    'larita': dict(name='larita', skin=SKIN_B, hair='bun', hair_col='#2e2420', top='cardigan', top_col='#b8708a',
                   inner_col='#efe6d4', pants='#3f3a55', shoes='#5a2e2e', hs=0.94, seed=14),
}
KID_LOOKS = [('#e9bf98', 'pony', '#7a5236', '#e2668d'), ('#b9835e', 'short', '#2a1f19', '#3f7fd0'),
             ('#d6a077', 'bunches', '#3a2414', '#f2c14e'), ('#8a5a3c', 'short', '#1f1712', '#6fbf5a'),
             ('#e9bf98', 'short', '#c9963a', '#9a6ad0'), ('#b9835e', 'long', '#2a1f19', '#3fb3a8'),
             ('#d6a077', 'short', '#5a3a22', '#e8743a'), ('#8a5a3c', 'pony', '#1f1712', '#d23b6a')]
BLANKETS = ['#c9b37a', '#8fa8c8', '#c98a8a', '#9ab88a', '#d9c4a0', '#a89ac8', '#c8a07a', '#8ac0c0']


def kid_spec(i, hs):
    sk, hr, hc, col = KID_LOOKS[i % len(KID_LOOKS)]
    return dict(name='kid%d' % i, skin=sk, hair=hr, hair_col=hc, top='pjs', top_col=col, pants=col, shoes=None, hs=hs,
                seed=20 + i)


SPK = {'casey': 'CASEY', 'larita': 'LARITA', 'james': 'JAMES'}


def person(c, who, x, y, h, T, sp=None, gest='rhand', **st):
    s = dict(sp or CAST[who])
    spk = SPK.get(who)
    if spk:
        st.setdefault('mouth', V.mouth(spk, T))
        if V.speaking(spk, T) and gest and not st.get('nogest'):
            gx, gy = gesture(T, s.get('seed', 0))
            hx, hy = st.get(gest, (15, -31) if gest == 'rhand' else (-15, -31))
            st[gest] = (hx + gx, hy + gy)
    draw_person(c, s, x, y, h, st, T)


def blanket(c, x, y, h, col, T, seed=0):
    u = h / 90.0
    sway = math.sin(T * 2 + seed) * 0.8 * u
    p = smooth_path([(-13 * u, -60 * u), (13 * u, -60 * u), (17 * u + sway, -36 * u), (15 * u + sway, -16 * u),
                     (-15 * u + sway, -16 * u), (-17 * u + sway, -36 * u)], True, 0.35)
    c.save()
    c.translate(x, y)
    draw(c, p, col, INK, max(2, u * 1.0))
    for k in range(3):
        c.drawLine(-8 * u + k * 7 * u, -50 * u, -10 * u + k * 7 * u + sway, -20 * u, strokep(shade(col, -0.25), 0.7 * u))
    c.drawLine(-12 * u, -56 * u, 12 * u, -56 * u, strokep(shade(col, 0.25), 1.2 * u, 0.8))
    c.restore()


def kid(c, i, x, y, h, T, wrap=True, walking=False, **st):
    s = kid_spec(i, h / 380.0)
    st.setdefault('expr', 'neutral')
    st.setdefault('facing', 0.3)
    if walking:
        st.update(legs='walk', phase=T * 9 + i)
    draw_person(c, s, x, y, h, st, T)
    if wrap:
        blanket(c, x, y, h, BLANKETS[i % len(BLANKETS)], T, i)
        # head drawn again on top of the blanket edge is unnecessary: blanket stops below the chin


def baby_hold(cv, hands, u):
    if hands[0] and hands[1]:
        hx = (hands[0][0] + hands[1][0]) / 2
        hy = (hands[0][1] + hands[1][1]) / 2
        draw(cv, oval(hx, hy - 2 * u, 9 * u, 6.5 * u), '#f1e6cc', INK, 0.8 * u)
        cv.drawCircle(hx - 5 * u, hy - 7 * u, 4.2 * u, fillp(SKIN_B))
        cv.drawCircle(hx - 5 * u, hy - 7 * u, 4.2 * u, strokep(INK, 0.7 * u))
        cv.drawLine(hx - 6.5 * u, hy - 7.5 * u, hx - 5 * u, hy - 7.5 * u, strokep(INK, 0.5 * u))
        cv.drawLine(hx - 3.6 * u, hy - 7.5 * u, hx - 2.2 * u, hy - 7.5 * u, strokep(INK, 0.5 * u))


# ------------------------------------------------------------------ set pieces
def night_sky(c, glow=0.0, dawn=0.0):
    top = mix('#070a1c', '#f0a070', dawn * 0.0) if dawn == 0 else mix('#2a2c5a', '#7f8fc0', dawn)
    bot = mix('#1d2448', '#e8a070', dawn)
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp(None, 1, shader=lin(0, 0, 0, VH, [top, bot])))


def stars(c, T, n=70, y1=900, a=1.0):
    for k in range(n):
        x = VW * hash01(k, 31) * 1.6 - VW * 0.3
        y = y1 * hash01(k, 32) - 100
        tw = 0.5 + 0.5 * math.sin(T * (1 + hash01(k, 33) * 3) + k)
        c.drawCircle(x, y, 1.5 + 2 * hash01(k, 34), fillp('#ffffff', a * (0.35 + 0.6 * tw)))


def fire_glow(c, x, y, r, T, a=1.0):
    fl = 0.85 + 0.15 * math.sin(T * 9) * math.sin(T * 5.3 + 1)
    c.drawCircle(x, y, r * fl, fillp(None, 1, shader=rad(x, y, r * fl, [hexc('#ffb050', 0.75 * a), hexc('#ff6a20', 0.35 * a),
                                                                         hexc('#ff4a10', 0)], [0, 0.4, 1])))


def flame(c, x, y, w, h, T, seed=0, a=1.0):
    for k, (col, s) in enumerate((('#e8401c', 1.0), ('#ff8a2a', 0.72), ('#ffd45a', 0.42))):
        ww = w * s
        hh = h * s * (0.85 + 0.15 * math.sin(T * 11 + seed + k))
        sw_ = math.sin(T * 7 + seed * 2 + k) * ww * 0.25
        p = skia.Path()
        p.moveTo(x - ww / 2, y)
        p.cubicTo(x - ww / 2, y - hh * 0.5, x + sw_ - ww * 0.1, y - hh * 0.7, x + sw_, y - hh)
        p.cubicTo(x + sw_ + ww * 0.1, y - hh * 0.6, x + ww / 2, y - hh * 0.5, x + ww / 2, y)
        p.close()
        c.drawPath(p, fillp(col, a))
        if k == 0:
            c.drawPath(p, strokep('#7a1c0c', 2, 0.6 * a))


def smoke(c, x, y, T, s=1.0, n=6, a=0.5, seed=0, dark=True):
    for k in range(n):
        ph = (T * 0.25 + k / n + hash01(k, seed)) % 1.0
        px = x + math.sin(ph * 5 + k) * 30 * s + ph * 80 * s
        py = y - ph * 420 * s
        r = (30 + 60 * ph) * s
        c.drawCircle(px, py, r, fillp('#3a3a44' if dark else '#9a9aa4', a * math.sin(ph * math.pi)))


def farmhouse(c, x, yb, w, T, fire=0.0, lit=0.0):
    """x = centre, yb = ground line. fire: 0..1 flames in windows. lit: warm light."""
    h = w * 0.55
    wall = '#d8cdb4'
    if fire > 0:
        fire_glow(c, x, yb - h * 0.9, w * 0.95, T, fire)
        smoke(c, x + w * 0.1, yb - h * 1.2, T, w / 700, 7, 0.55 * fire, 3)
    draw(c, rect(x - w / 2, yb - h, w, h), wall, INK, 5)
    for k in range(1, 9):
        c.drawLine(x - w / 2, yb - h + k * h / 9, x + w / 2, yb - h + k * h / 9, strokep(shade(wall, -0.2), 2.5))
    roof = poly([(x - w * 0.58, yb - h), (x - w * 0.3, yb - h * 1.55), (x + w * 0.3, yb - h * 1.55), (x + w * 0.58, yb - h)])
    draw(c, roof, '#5a4a52', INK, 5)
    draw(c, rect(x + w * 0.2, yb - h * 1.75, w * 0.08, h * 0.3), '#8a5a4a', INK, 4)
    # porch
    draw(c, poly([(x - w * 0.5, yb - h * 0.55), (x + w * 0.5, yb - h * 0.55), (x + w * 0.56, yb - h * 0.45), (x - w * 0.56, yb - h * 0.45)]),
         '#6a5a52', INK, 4)
    for k in range(6):
        px = x - w * 0.48 + k * w * 0.192
        c.drawLine(px, yb - h * 0.45, px, yb, strokep('#efe6d4', 7))
        c.drawLine(px, yb - h * 0.45, px, yb, strokep(INK, 1.5))
    # door
    draw(c, rect(x - w * 0.06, yb - h * 0.38, w * 0.12, h * 0.38), '#7a2e2a' if fire == 0 else '#ffb050', INK, 4)
    wins = [(-0.34, 0.78), (-0.12, 0.78), (0.12, 0.78), (0.34, 0.78), (-0.32, 0.3), (0.32, 0.3)]
    for i, (fx, fy) in enumerate(wins):
        wx, wy, ww, wh = x + fx * w - w * 0.06, yb - h * fy, w * 0.12, h * 0.2
        on = fire > 0 and (i in (0, 1, 2, 4) or fire > 0.6)
        col = '#ffb050' if on else ('#ffd98a' if lit else '#2a3048')
        draw(c, rect(wx, wy, ww, wh), col, INK, 4)
        if on:
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
            flame(c, wx + ww / 2, wy + wh, ww * 0.9, wh * 1.1, T, i, fire)
            c.restore()
        c.drawLine(wx + ww / 2, wy, wx + ww / 2, wy + wh, strokep('#efe6d4', 3))
    if fire > 0.5:
        for k in range(3):
            flame(c, x - w * 0.2 + k * w * 0.2, yb - h * 1.45 + 10 * k % 2, w * 0.1, h * 0.35, T, 10 + k, fire - 0.3)


def burnt_frame(c, x, yb, w, T, a=1.0):
    h = w * 0.55
    col = '#2a2224'
    for fx in (-0.5, -0.25, 0.0, 0.25, 0.5):
        c.drawLine(x + fx * w, yb, x + fx * w, yb - h * (0.9 + 0.1 * math.cos(fx * 7)), strokep(col, 14, a))
    c.drawLine(x - w * 0.5, yb - h, x + w * 0.1, yb - h * 1.05, strokep(col, 12, a))
    c.drawLine(x - w * 0.5, yb - h, x - w * 0.3, yb - h * 1.5, strokep(col, 12, a))
    c.drawLine(x - w * 0.3, yb - h * 1.5, x - w * 0.05, yb - h * 1.5, strokep(col, 10, a))
    c.drawPath(smooth_path([(x - w * 0.6, yb), (x - w * 0.3, yb - 30), (x, yb - 18), (x + w * 0.4, yb - 36), (x + w * 0.6, yb)]),
               fillp('#3a3436', a))
    smoke(c, x + w * 0.1, yb - h, T, w / 900, 4, 0.18 * a, 5, False)


def house_outline_paths(x, yb, w):
    h = w * 0.55
    segs = [((x - w / 2, yb), (x - w / 2, yb - h)), ((x - w / 2, yb - h), (x + w / 2, yb - h)), ((x + w / 2, yb - h), (x + w / 2, yb)),
            ((x - w * 0.58, yb - h), (x - w * 0.3, yb - h * 1.55)), ((x - w * 0.3, yb - h * 1.55), (x + w * 0.3, yb - h * 1.55)),
            ((x + w * 0.3, yb - h * 1.55), (x + w * 0.58, yb - h)),
            ((x - w * 0.06, yb), (x - w * 0.06, yb - h * 0.38)), ((x - w * 0.06, yb - h * 0.38), (x + w * 0.06, yb - h * 0.38)),
            ((x + w * 0.06, yb - h * 0.38), (x + w * 0.06, yb))]
    for fx, fy in ((-0.34, 0.78), (0.34, 0.78), (-0.32, 0.3), (0.32, 0.3)):
        wx, wy, ww, wh = x + fx * w - w * 0.06, yb - h * fy, w * 0.12, h * 0.2
        segs += [((wx, wy), (wx + ww, wy)), ((wx + ww, wy), (wx + ww, wy + wh)), ((wx + ww, wy + wh), (wx, wy + wh)), ((wx, wy + wh), (wx, wy))]
    return segs


def pencil_house(c, x, yb, w, prog, T):
    segs = house_outline_paths(x, yb, w)
    n = len(segs)
    done = prog * n
    for i, ((x0, y0), (x1, y1)) in enumerate(segs):
        f = clamp(done - i)
        if f <= 0:
            break
        xe, ye = lerp(x0, x1, f), lerp(y0, y1, f)
        wob = math.sin(i * 3.1) * 2
        c.drawLine(x0, y0 + wob, xe, ye + wob, strokep('#fff6e0', 7, 0.9))
        c.drawLine(x0, y0 + wob, xe, ye + wob, strokep('#4a3a30', 3, 0.9))
        if f < 1:  # pencil tip
            c.save()
            c.translate(xe, ye)
            c.rotate(-35)
            draw(c, poly([(0, 0), (14, -8), (90, -8), (90, 8), (14, 8)]), '#f2c14e', INK, 3)
            c.drawPath(poly([(0, 0), (14, -8), (14, 8)]), fillp('#e8d6b0'))
            c.restore()


def car_side(c, x, y, s, T, lights=True, moving=True, facing=1):
    c.save()
    c.translate(x, y)
    c.scale(s * facing, s)
    if lights:
        p = poly([(150, -40), (520, -90), (520, 40), (150, -10)])
        c.drawPath(p, fillp(None, 1, shader=lin(150, 0, 520, 0, [hexc('#fff2c0', 0.55), hexc('#fff2c0', 0)])))
    body = smooth_path([(-160, -10), (-150, -50), (-90, -60), (-50, -105), (60, -108), (110, -62), (155, -52), (162, -12),
                        (150, 0), (-150, 0)], True, 0.25)
    draw(c, body, '#3a4a5e', INK, 5)
    draw(c, smooth_path([(-40, -98), (52, -100), (92, -64), (-62, -62)], True, 0.2), '#7fa0c0', INK, 4)
    c.drawLine(10, -100, 6, -62, strokep(INK, 5))
    draw(c, oval(152, -36, 9, 7), '#fff6c8', INK, 3)
    draw(c, rect(-160, -34, 12, 10), '#d23b35', INK, 2)
    for wx in (-95, 95):
        draw(c, oval(wx, 0, 30, 30), '#222226', INK, 4)
        a = (T * 12 if moving else 0)
        for k in range(3):
            ang = a + k * 2.094
            c.drawLine(wx, 0, wx + math.cos(ang) * 18, math.sin(ang) * 18, strokep('#8a8a90', 3))
    c.restore()


def hwy_sign(c, x, y, s=1.0):
    c.drawLine(x, y, x, y - 230 * s, strokep('#6a6a70', 10 * s))
    draw(c, rrect(x - 90 * s, y - 330 * s, 180 * s, 110 * s, 12 * s), '#2f6f4a', '#ffffff', 5 * s)
    c.drawPath(rrect(x - 90 * s, y - 330 * s, 180 * s, 110 * s, 12 * s), strokep(INK, 2))
    draw_text(c, 'HWY 114', x, y - 258 * s, font(FONT_SUB, 38 * s), '#ffffff', 'center')


def gps(c, x, y, w, h, T, turn=0.0):
    """dashboard GPS: map lines + route + position arrow, no text"""
    glow(c, x + w / 2, y + h / 2, w * 0.9, '#8fd0ff', 0.28)
    draw(c, rrect(x - 14, y - 14, w + 28, h + 28, 26), '#101014', INK, 5)
    scr = rrect(x, y, w, h, 16)
    c.save()
    c.clipPath(scr, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fillp('#0f2636'))
    scroll = (T * 40) % 120
    for k in range(-1, 6):
        yy = y + k * 120 + scroll
        c.drawLine(x, yy, x + w, yy - 40, strokep('#244a60', 6))
    for k in range(4):
        xx = x + 60 + k * w / 3.5
        c.drawLine(xx, y, xx + 30, y + h, strokep('#244a60', 6))
    c.drawPath(smooth_path([(x + w * 0.1, y + h * 0.15), (x + w * 0.65, y + h * 0.3), (x + w * 0.3, y + h * 0.55)], False),
               strokep('#3a6a3a', 22, 0.5))
    route = smooth_path([(x + w * 0.5, y + h * 1.05), (x + w * 0.5, y + h * 0.6), (x + w * 0.55 + turn * w * 0.2, y + h * 0.35),
                         (x + w * 0.8 + turn * w * 0.1, y + h * 0.05)], False)
    c.drawPath(route, strokep('#1d6fd0', 18))
    c.drawPath(route, strokep('#5fb8ff', 10))
    pu = 1 + 0.08 * math.sin(T * 5)
    c.save()
    c.translate(x + w * 0.5, y + h * 0.78)
    c.scale(pu, pu)
    c.drawCircle(0, 0, 34, fillp('#5fb8ff', 0.3))
    draw(c, poly([(0, -26), (20, 18), (0, 8), (-20, 18)]), '#ffffff', '#1d6fd0', 4)
    c.restore()
    c.drawPath(poly([(x, y), (x + w * 0.5, y), (x, y + h * 0.4)]), fillp('#ffffff', 0.05))
    c.restore()


def interior(c, T, cam, glow_amt=1.0, gps_turn=0.0):
    """car interior at night, GPS glowing, orange glow over a hill through the windshield (hook / loop frame)"""
    night_sky(c)
    with vlayer(c, cam, 0.3):
        stars(c, T, 60, 800)
        gx, gy = 640, 830
        fire_glow(c, gx, gy, 520, T, glow_amt)
        smoke(c, gx + 30, gy - 60, T, 0.8, 5, 0.35 * glow_amt, 1)
        p = poly([(-300, 900), (100, 840), (380, 800), (640, 860), (900, 790), (1400, 880), (1400, 1400), (-300, 1400)])
        c.drawPath(p, fillp('#0b0d16'))
        c.drawPath(p, strokep('#ff9a50', 3, 0.5 * glow_amt))
    with vlayer(c, cam, 0.55):
        # road lit by headlights
        c.drawPath(poly([(140, 1300), (940, 1300), (600, 880), (520, 880)]), fillp(None, 1, shader=lin(0, 880, 0, 1300, [
            hexc('#3a3a40', 0.6), hexc('#5a5a5e', 0.95)])))
        for k in range(6):
            ph = (T * 0.9 + k / 6) % 1
            yy = lerp(890, 1300, ph ** 2)
            ww = lerp(3, 18, ph ** 2)
            c.drawRect(skia.Rect.MakeXYWH(560 - ww / 2, yy, ww, lerp(8, 60, ph ** 2)), fillp('#e8d6a0', 0.9))
        c.drawPath(poly([(140, 1300), (940, 1300), (600, 880), (520, 880)]), fillp(None, 1, shader=rad(560, 1300, 520, [
            hexc('#fff2c0', 0.35), hexc('#fff2c0', 0)])))
    with vlayer(c, cam, 1.0):
        # cabin frame: roof, pillars, mirror
        c.drawPath(poly([(-200, -200), (1300, -200), (1300, 170), (900, 120), (180, 120), (-200, 170)]), fillp('#0d0e12'))
        c.drawPath(poly([(-200, 170), (180, 120), (-60, 1200), (-200, 1300)]), fillp('#111216'))
        c.drawPath(poly([(1300, 170), (900, 120), (1140, 1200), (1300, 1300)]), fillp('#111216'))
        draw(c, rrect(440, 140, 200, 60, 20), '#1a1b20', INK, 4)
        c.drawLine(540, 120, 540, 140, strokep('#1a1b20', 8))
        # dashboard
        dash = smooth_path([(-200, 1240), (300, 1180), (800, 1180), (1300, 1240), (1300, 2100), (-200, 2100)], True, 0.3)
        c.drawPath(dash, fillp(None, 1, shader=lin(0, 1180, 0, 1920, ['#202128', '#0c0c10'])))
        c.drawPath(smooth_path([(-200, 1240), (300, 1180), (800, 1180), (1300, 1240)], False), strokep('#ff9a50', 3, 0.35 * glow_amt))
        gps(c, 420, 1300, 420, 250, T, gps_turn)
        # steering wheel (driver side, left)
        c.drawArc(skia.Rect.MakeXYWH(-180, 1300, 560, 560), 190, 160, False, strokep('#16171c', 46))
        c.drawArc(skia.Rect.MakeXYWH(-180, 1300, 560, 560), 200, 120, False, strokep('#3a3b44', 6, 0.7))
        # Casey: dark silhouette leaning forward, rim-lit by the glow and the GPS
        c.save()
        c.translate(170 + math.sin(T * 0.7) * 4, 1050)
        c.drawPath(smooth_path([(-260, 500), (-200, 200), (-40, 120), (140, 160), (230, 420), (240, 600)], True, 0.4), fillp('#08090c'))
        c.drawCircle(0, 0, 175, fillp('#08090c'))
        c.drawPath(poly([(-190, -40), (-160, -140), (60, -190), (170, -110), (290, -70), (290, -40)]), fillp('#0d1830'))
        c.drawArc(skia.Rect.MakeXYWH(-175, -175, 350, 350), 290, 60, False, strokep('#ff9a50', 6, 0.7 * glow_amt))
        c.drawArc(skia.Rect.MakeXYWH(-175, -175, 350, 350), 20, 40, False, strokep('#8fd0ff', 5, 0.5))
        c.restore()
        # son asleep in the passenger seat (small silhouette)
        c.save()
        c.translate(930, 1130)
        c.rotate(14)
        c.drawCircle(0, 0, 85, fillp('#0a0b0e'))
        c.drawPath(smooth_path([(-120, 260), (-90, 90), (60, 80), (120, 260)], True, 0.4), fillp('#0a0b0e'))
        c.drawArc(skia.Rect.MakeXYWH(-85, -85, 170, 170), 250, 70, False, strokep('#ff9a50', 4, 0.5 * glow_amt))
        c.restore()


def living_room(c, cam, T, door_open=0.0, smoke_a=0.5):
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#10131f'))
    with vlayer(c, cam, 0.95):
        c.drawRect(skia.Rect.MakeLTRB(-400, -200, 1500, 1350), fillp('#232a45'))
        for r in range(16):
            for k in range(14):
                c.drawCircle(-380 + k * 140 + (r % 2) * 70, -180 + r * 100, 6, fillp('#3a4468', 0.7))
        # window with moonlight
        draw(c, rect(60, 300, 300, 380), '#1a2a50', '#5a5a70', 12)
        c.drawCircle(260, 400, 40, fillp('#e8eef8', 0.9))
        c.drawLine(210, 300, 210, 680, strokep('#5a5a70', 8))
        c.drawPath(poly([(60, 1350), (360, 1350), (520, 700), (220, 700)]), fillp('#9fb4e0', 0.07))
        # picture frames (blank), clock without numerals
        for k, (fx, fy) in enumerate(((480, 360), (640, 420))):
            draw(c, rect(fx, fy, 120, 100), '#3a3048', '#c9a24a', 6)
        draw(c, oval(560, 240, 46, 46), '#e8e2d4', INK, 5)
        c.drawLine(560, 240, 560, 212, strokep(INK, 4))
        c.drawLine(560, 240, 580, 250, strokep(INK, 4))
        # hallway door (right) with smoke curling under / through it
        dx = 760
        c.drawRect(skia.Rect.MakeXYWH(dx, 560, 240, 790), fillp('#ff8a3a' if door_open > 0 else '#0e0f16'))
        if door_open > 0:
            fire_glow(c, dx + 120, 900, 420, T, door_open)
        lw = 240 * (1 - 0.85 * ease_io(door_open))
        draw(c, rect(dx, 560, lw, 790), '#5a3a2a', INK, 5)
        if lw > 60:
            c.drawCircle(dx + lw - 30, 960, 10, fillp('#c9a24a'))
        draw(c, rect(dx - 20, 540, 280, 24), '#3a2a22', INK, 4)
        for k in range(5):
            ph = (T * 0.3 + k / 5) % 1
            c.drawCircle(dx + 40 + k * 40 + ph * 60, 1340 - ph * 220, 16 + 40 * ph, fillp('#6a6a74', smoke_a * math.sin(ph * math.pi)))
        # lamp (off) and floor
        c.drawLine(110, 1350, 110, 980, strokep('#2a2a30', 8))
        draw(c, poly([(50, 990), (170, 990), (140, 900), (80, 900)]), '#5a5040', INK, 4)
        c.drawRect(skia.Rect.MakeLTRB(-400, 1350, 1500, 2200), fillp('#2a1f1c'))
        for k in range(12):
            c.drawLine(-400, 1350 + k * 60, 1500, 1350 + k * 60, strokep('#221815', 3))
        draw(c, oval(500, 1500, 420, 70), '#4a2a3a', None, 0, fa=0.8)


def recliner(c, x, y, s=1.0):
    draw(c, rrect(x - 200 * s, y - 470 * s, 120 * s, 470 * s, 50 * s), '#6a4a3a', INK, 6)
    draw(c, rrect(x - 190 * s, y - 180 * s, 380 * s, 160 * s, 40 * s), '#7a5a46', INK, 6)
    draw(c, rrect(x - 120 * s, y - 300 * s, 70 * s, 140 * s, 30 * s), '#6a4a3a', INK, 5)
    draw(c, rrect(x + 140 * s, y - 150 * s, 160 * s, 80 * s, 30 * s), '#7a5a46', INK, 5)
    c.drawLine(x - 140 * s, y - 20 * s, x - 140 * s, y + 20 * s, strokep(INK, 10 * s))
    c.drawLine(x + 150 * s, y - 20 * s, x + 150 * s, y + 20 * s, strokep(INK, 10 * s))


def zzz(c, x, y, T):
    f = font(FONT_HAND, 54)
    for k in range(3):
        ph = (T * 0.5 + k / 3) % 1
        draw_text(c, 'z', x + ph * 80 + k * 10, y - ph * 160, f, '#cfd8ff', 'center', a=math.sin(ph * math.pi) * 0.9)


def lawn_night(c, cam, T, fire=1.0, red=0.0):
    night_sky(c)
    with vlayer(c, cam, 0.2):
        stars(c, T, 50, 600, 0.7)
    with vlayer(c, cam, 0.5):
        c.drawPath(poly([(-500, 820), (300, 760), (900, 800), (1600, 740), (1600, 1500), (-500, 1500)]), fillp('#141a22'))
        for k in range(8):
            rig_tree(c, -300 + k * 240, 800 + (k % 2) * 20, 200)
    with vlayer(c, cam, 0.8):
        farmhouse(c, 560, 1060, 820, T, fire)
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-500, 1050, 1600, 2400), fillp(None, 1, shader=lin(0, 1050, 0, 1920, ['#2a3a24', '#162014'])))
        for k in range(60):
            x = -450 + k * 36
            c.drawLine(x, 1100 + (k % 4) * 180, x + 8, 1070 + (k % 4) * 180, strokep('#3f5a32', 4))
        c.drawRect(skia.Rect.MakeLTRB(-500, 1050, 1600, 2400), fillp('#ff7a30', 0.10 * fire))
    if red > 0:
        on = (math.sin(T * 12) > 0)
        c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#ff2020' if on else '#3050ff', 0.08 * red))


def rig_tree(c, x, y, h):
    c.drawPath(smooth_path([(x - h * 0.3, y), (x - h * 0.25, y - h * 0.6), (x, y - h), (x + h * 0.25, y - h * 0.6), (x + h * 0.3, y)]),
               fillp('#0c1210'))


def fire_truck(c, x, y, s, T):
    """silhouette only, with flashing red lights"""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawPath(poly([(-240, 0), (-240, -150), (40, -150), (40, -220), (200, -220), (250, -120), (250, 0)]), fillp('#0a0a0e'))
    for wx in (-160, 160):
        c.drawCircle(wx, 0, 40, fillp('#050507'))
    for k, lx in enumerate((60, 180)):
        on = math.sin(T * 14 + k * math.pi) > 0
        glow(c, lx, -235, 140, '#ff2a2a', 0.8 if on else 0.15)
        c.drawCircle(lx, -232, 14, fillp('#ff5050' if on else '#5a1010'))
    glow(c, 250, -60, 120, '#fff2c0', 0.4)
    c.restore()


# ------------------------------------------------------------------ shots  fn(c, lt, dur, T)
def sh_hook(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 960, 1.0), (600, 880, 1.13), 'io', 0.4, 1)
    interior(c, T, cam, 0.55 + 0.45 * ease_io(ramp(lt, 3.5, 5.8)))


def sh_driving(c, lt, dur, T):
    # medium two-shot inside the car: Casey (cap, plaid) driving, his son asleep beside him
    cam = vcam(lt, dur, (540, 1000, 1.0), (540, 960, 1.08), 'lin', 0.5, 2)
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#0b0d18'))
    with vlayer(c, cam, 0.4):
        c.drawRect(skia.Rect.MakeLTRB(-300, 200, 1400, 900), fillp('#141a30'))
        stars(c, T, 30, 800, 0.6)
        for k in range(4):
            ph = (T * 0.6 + k / 4) % 1
            rig_tree(c, 1300 - ph * 1800, 900, 240)
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-300, 900, 1400, 2200), fillp('#16171d'))
        draw(c, rrect(-200, 820, 1500, 120, 40), '#1c1d24', INK, 5)
        person(c, 'casey', 330, 1440, 640, T, facing=0.45, expr='neutral', lhand=(8, -44), rhand=(26, -42), gest=None, legs='none', shadow=False)
        draw(c, oval(560, 1150, 150, 150), None, None, 0)
        c.drawArc(skia.Rect.MakeXYWH(390, 760, 300, 300), 150, 240, False, strokep('#2a2b32', 24))
        person(c, 'son', 820, 1400, 640 * 0.6, T, sp=CAST['son'], facing=-0.3, expr='asleep', tilt=-14, lhand=(-14, -30),
               rhand=(14, -30), legs='none', shadow=False)
        zzz(c, 880, 940, T)
        glow(c, 560, 1300, 260, '#8fd0ff', 0.25)
        draw(c, rrect(-200, 1330, 1500, 700, 30), '#101116', INK, 5)
        gps(c, 410, 1390, 280, 170, T, ramp(lt, 1.6, 2.4))
    K.vvignette(c, 0.5)


def sh_wrong_way(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1000, 1.05), (560, 940, 1.15), 'io', 0.5, 3)
    night_sky(c)
    with vlayer(c, cam, 0.2):
        stars(c, T, 60, 700)
    with vlayer(c, cam, 0.5):
        c.drawPath(poly([(-500, 900), (200, 820), (700, 860), (1600, 800), (1600, 1500), (-500, 1500)]), fillp('#10141c'))
        for k in range(7):
            rig_tree(c, -300 + k * 300, 870, 220)
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-500, 1000, 1600, 2400), fillp('#141a16'))
        # fork: straight road and the side road up the hill
        c.drawPath(poly([(160, 2000), (920, 2000), (600, 1000), (500, 1000)]), fillp('#2c2c32'))
        c.drawPath(poly([(520, 1300), (640, 1300), (1300, 1080), (1300, 1020)]), fillp('#2a2a30'))
        for k in range(8):
            yy = 1050 + k * 130
            c.drawRect(skia.Rect.MakeXYWH(548, yy, 8 + k * 2, 40 + k * 6), fillp('#e8d6a0', 0.7))
        hwy_sign(c, 860, 1330, 1.1)
        # car turning onto the dark road (headlight cone)
        u = ease_io(ramp(lt, 0.3, dur))
        cx, cy = lerp(520, 980, u), lerp(1760, 1150, u)
        s = lerp(0.95, 0.45, u)
        c.drawPath(poly([(cx, cy - 60 * s), (cx + 520 * s + 200 * u, cy - 300 * s), (cx + 420 * s, cy + 40 * s)]),
                   fillp('#fff2c0', 0.18))
        car_side(c, cx, cy, s, T, False, True)
    K.vvignette(c, 0.5)


def sh_hilltop(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 900, 1.0), (560, 1000, 1.12), 'io', 0.4, 4)
    night_sky(c)
    with vlayer(c, cam, 0.15):
        stars(c, T, 90, 900)
    with vlayer(c, cam, 0.5):
        c.drawPath(poly([(-500, 1000), (300, 940), (900, 980), (1600, 920), (1600, 2000), (-500, 2000)]), fillp('#0e131c'))
        farmhouse(c, 600, 1240, 420, T, 0.85)
        c.drawRect(skia.Rect.MakeLTRB(-500, 1240, 1600, 2000), fillp('#121a14'))
    with vlayer(c, cam, 1.0):
        c.drawPath(smooth_path([(-400, 1560), (300, 1480), (900, 1530), (1500, 1500), (1500, 2400), (-400, 2400)]),
                   fillp('#0a0d0e'))
        car_side(c, 250, 1600, 0.85, T, True, False)
        person(c, 'casey', 760, 1640, 420, T, facing=-0.4, expr='surprised', lhand=(-15, -32), rhand=(24, -60), gest=None,
               shadow=False)
        glow(c, 760, 1400, 240, '#ff9a50', 0.25)
    K.vvignette(c, 0.45)


def sh_asleep_james(c, lt, dur, T):
    cam = vcam(lt, dur, (520, 1050, 1.0), (480, 1080, 1.12), 'lin', 0.4, 5)
    living_room(c, cam, T, 0.0, 0.45)
    with vlayer(c, cam, 1.0):
        recliner(c, 430, 1500, 1.2)
        person(c, 'james', 430, 1430, 560, T, legs='sit', facing=0.4, expr='asleep', tilt=-10, lhand=(-12, -30), rhand=(14, -30),
               shadow=False, noblink=True)
        zzz(c, 520, 900, T)
    K.vvignette(c, 0.55)


def sh_asleep_kids(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1000, 1.08), (540, 960, 1.0), 'lin', 0.4, 6)
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#0f1220'))
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-300, -200, 1400, 1500), fillp('#1f2642'))
        for r in range(18):
            c.drawLine(-300, -200 + r * 90, 1400, -200 + r * 90, strokep('#262e50', 3))
        draw(c, rect(700, 160, 260, 300), '#1a2a50', '#5a5a70', 12)
        c.drawCircle(860, 250, 36, fillp('#e8eef8'))
        c.drawPath(poly([(700, 1500), (960, 1500), (1000, 460), (700, 460)]), fillp('#9fb4e0', 0.05))
        c.drawRect(skia.Rect.MakeLTRB(-300, 1500, 1400, 2300), fillp('#2a1f1c'))
        # bunk beds with sleeping children (heads on pillows)
        for (bx, by, bw) in ((60, 760, 560), (60, 1150, 560)):
            draw(c, rect(bx, by, bw, 60), '#6a4a3a', INK, 5)
            for k in range(3):
                hx = bx + 110 + k * 170
                draw(c, oval(hx, by - 20, 60, 26), '#efe6d4', INK, 3)
                sp = kid_spec(k + (0 if by < 1000 else 3), 0.5)
                c.drawCircle(hx, by - 40, 46, fillp(sp['skin']))
                c.drawCircle(hx, by - 40, 46, strokep(INK, 4))
                c.drawArc(skia.Rect.MakeXYWH(hx - 46, by - 86, 92, 92), 180, 180, False, strokep(sp['hair_col'], 18))
                for s2 in (-1, 1):
                    c.drawArc(skia.Rect.MakeXYWH(hx + s2 * 16 - 8, by - 46, 16, 10), 20, 140, False, strokep(INK, 3))
                draw(c, rrect(hx + 30, by - 50, 120, 50, 20), BLANKETS[k + (0 if by < 1000 else 3)], INK, 4)
        for x in (60, 620):
            c.drawLine(x, 500, x, 1500, strokep('#5a3a2a', 18))
        # Larita asleep with the little one, in the doorway's room beyond (right)
        draw(c, rect(700, 1250, 340, 70), '#6a4a3a', INK, 5)
        draw(c, oval(780, 1235, 60, 24), '#efe6d4', INK, 3)
        c.drawCircle(780, 1210, 52, fillp(SKIN_B))
        c.drawCircle(780, 1210, 52, strokep(INK, 4))
        draw(c, oval(780, 1160, 30, 22), '#2e2420', INK, 3)
        for s2 in (-1, 1):
            c.drawArc(skia.Rect.MakeXYWH(780 + s2 * 18 - 9, 1205, 18, 10), 20, 140, False, strokep(INK, 3))
        c.drawCircle(860, 1225, 28, fillp(SKIN_B))
        c.drawCircle(860, 1225, 28, strokep(INK, 3))
        draw(c, rrect(820, 1215, 200, 50, 20), '#b8708a', INK, 4)
        zzz(c, 300, 600, T)
        # faint smoke at the door crack
        smoke(c, 600, 1500, T, 0.5, 4, 0.3, 8)
    K.vvignette(c, 0.55)


def sh_wake(c, lt, dur, T):
    cam = vcam(lt, dur, (560, 1060, 1.05), (560, 1020, 1.12), 'out', 0.6, 7)
    door = ease_out(ramp(lt, 0.0, 0.25))
    living_room(c, cam, T, door, 0.7)
    with vlayer(c, cam, 1.0):
        recliner(c, 330, 1500, 1.15)
        jolt = ease_out(ramp(lt, 0.5, 0.8))
        person(c, 'james', 330, 1430 - 30 * jolt, 540, T, legs='sit', facing=0.5, expr='asleep' if lt < 0.5 else 'surprised',
               tilt=lerp(-10, 4, jolt), lhand=(-14, -30) if jolt < 0.5 else (-22, -58), rhand=(14, -30) if jolt < 0.5 else (24, -60),
               shadow=False, gest=None)
        if jolt > 0.5:
            for s2 in (-1, 1):
                c.drawLine(330 + s2 * 130, 760, 330 + s2 * 170, 720, strokep('#ffffff', 6, 0.8))
        ent = ease_out(ramp(lt, 0.05, 0.45))
        person(c, 'casey', lerp(880, 690, ent), 1520, 600, T, facing=-0.6, expr='concerned', legs='walk' if ent < 1 else 'stand',
               phase=T * 10, lhand=(-28, -52), rhand=(-10, -40), gest='rhand', rot=-4)
    K.vvignette(c, 0.5)


def sh_escape(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1080, 1.05), (520, 1120, 1.12), 'lin', 0.5, 8)
    lawn_night(c, cam, T, 1.0)
    with vlayer(c, cam, 1.0):
        # everyone hurrying from the porch toward the camera / left, children wrapped in blankets
        u = lt / dur
        movers = [('larita', 470, 1260, 820, 1500), ('kid', 620, 1200, 900, 1380), ('kid', 520, 1180, 760, 1340),
                  ('kid', 700, 1220, 1000, 1420), ('james', 560, 1220, 640, 1620), ('casey', 760, 1220, 980, 1700)]
        for i, (who, x0, y0, x1, y1) in enumerate(movers):
            e = ease_io(clamp(u * 1.2 - i * 0.05))
            x, y = lerp(x0, x1, e), lerp(y0, y1, e)
            if who == 'kid':
                kid(c, i, x, y, lerp(220, 300, e), T, True, True, facing=0.2)
            elif who == 'larita':
                person(c, 'larita', x - 150, y, lerp(360, 440, e), T, facing=0.2, legs='walk', phase=T * 9, expr='concerned',
                       lhand=(-6, -46), rhand=(8, -44), hold=baby_hold, gest=None)
            elif who == 'james':
                person(c, 'james', x - 330, y, lerp(380, 470, e), T, facing=0.3, legs='walk', phase=T * 9 + 1, expr='concerned',
                       lhand=(-8, -48), rhand=(8, -48), gest=None)
                kid(c, 7, x - 330, y - lerp(380, 470, e) * 0.28, lerp(150, 180, e), T, True, False, legs='none', shadow=False)
            else:
                person(c, 'casey', x, y, lerp(400, 500, e), T, facing=-0.4, legs='walk', phase=T * 9 + 2, expr='determined',
                       lhand=(-26, -50), rhand=(14, -32), gest=None)
    K.vvignette(c, 0.45)


def sh_trucks(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1000, 1.0), (560, 980, 1.08), 'lin', 0.5, 9)
    red = ease_out(ramp(lt, 0.1, 0.8))
    lawn_night(c, cam, T, 0.9, red)
    with vlayer(c, cam, 1.0):
        u = ease_out(ramp(lt, 0.0, dur))
        fire_truck(c, lerp(1500, 860, u), 1470, 0.9, T)
        for i, x in enumerate((180, 300, 410)):
            kid(c, i, x, 1480, 260, T, True, False, facing=0.6)
        person(c, 'larita', 560, 1500, 420, T, facing=0.4, expr='concerned', lhand=(-6, -46), rhand=(8, -44), hold=baby_hold, gest=None)
    K.vvignette(c, 0.45)


def huddle(c, T, xs_off=0, h=420, casey=True):
    # back row (heads well above the lower-third caption band), small ones in front below it
    group = [('kid', 0, 160, 1450, 230), ('james', None, 300, 1440, h), ('kid', 1, 420, 1430, 250), ('larita', None, 540, 1450, h * 0.94),
             ('kid', 2, 660, 1440, 240), ('kid', 3, 760, 1430, 210)]
    for who, i, x, y, hh in group:
        if who == 'kid':
            kid(c, i, x + xs_off, y, hh, T, True, False, facing=0.0, expr='neutral')
        elif who == 'james':
            person(c, 'james', x + xs_off, y, hh, T, facing=0.2, expr='sad', lhand=(-15, -32), rhand=(24, -52), gest=None)
        else:
            person(c, 'larita', x + xs_off, y, hh, T, facing=0.2, expr='sad', lhand=(-6, -46), rhand=(8, -44), hold=baby_hold, gest=None)
    for i, (x, y, hh) in enumerate(((240, 1700, 180), (470, 1705, 190), (650, 1700, 170))):
        kid(c, 4 + i, x + xs_off, y, hh, T, True, False, facing=0.0)
    if casey:
        person(c, 'casey', 880 + xs_off, 1440, 440, T, facing=-0.5, expr='sad', lhand=(-15, -32), rhand=(15, -32), gest=None)


def sh_huddle(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1080, 1.12), (540, 1040, 1.0), 'lin', 0.4, 10)
    lawn_night(c, cam, T, 0.75, 0.6)
    with vlayer(c, cam, 1.0):
        huddle(c, T)
        c.drawRect(skia.Rect.MakeLTRB(-300, 900, 1400, 2000), fillp('#ff8a3a', 0.06 + 0.03 * math.sin(T * 7)))
    K.vvignette(c, 0.45)


def sh_larita(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1000, 1.0), (540, 940, 1.1), 'lin', 0.3, 11)
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#120c14'))
    with vlayer(c, cam, 0.4):
        for k in range(14):
            x = VW * hash01(k, 41)
            y = 300 + 900 * hash01(k, 42)
            col = '#ff8a3a' if k % 3 else '#ff3030'
            pulse = 0.5 + 0.5 * math.sin(T * (2 + k % 3) + k)
            c.drawCircle(x, y, 60 + 70 * hash01(k, 43), fillp(col, 0.10 + 0.08 * pulse))
    with vlayer(c, cam, 1.0):
        person(c, 'larita', 540, 2000, 1250, T, facing=0.15, expr='sad', lhand=(-6, -46), rhand=(8, -44), hold=baby_hold, gest=None,
               tear=True, tilt=-4)
        c.drawRect(skia.Rect.MakeLTRB(-300, 0, 1400, 2200), fillp('#ff7a30', 0.06))
    K.vvignette(c, 0.5)


def sh_fostered(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 960, 1.0), (540, 960, 1.08), 'lin', 0.3, 12)
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp(None, 1, shader=lin(0, 0, 0, VH, ['#f6e6c8', '#f0d2a0'])))
    with vlayer(c, cam, 1.0):
        # long family table in warm daylight, small silhouettes fill in, row by row
        draw(c, rect(100, 300, 880, 300), '#bfe0f0', '#ffffff', 14)
        glow(c, 540, 450, 500, '#fff6d0', 0.5)
        draw(c, rrect(60, 1180, 960, 70, 20), '#a8784a', INK, 5)
        c.drawLine(140, 1250, 140, 1500, strokep('#7a5030', 18))
        c.drawLine(940, 1250, 940, 1500, strokep('#7a5030', 18))
        rows = [(700, 9, 62), (880, 10, 54), (1060, 11, 48)]
        k = 0
        for r, (y, n, s) in enumerate(rows):
            for j in range(n):
                t0 = 0.1 + (k * 0.07) * (0.92 ** (k / 6))
                k += 1
                a = ease_out(ramp(lt, t0, t0 + 0.2))
                if a <= 0:
                    continue
                x = 140 + (j + 0.5) * (800 / n)
                yy = y + 30 * (1 - a)
                col = shade(KID_LOOKS[(j + r) % 8][3], -0.15)
                c.drawCircle(x, yy - s * 1.25, s * 0.5, fillp(col, a))
                c.drawPath(smooth_path([(x - s * 0.55, yy), (x - s * 0.45, yy - s * 0.7), (x + s * 0.45, yy - s * 0.7), (x + s * 0.55, yy)]),
                           fillp(col, a))
        for j in range(6):
            draw(c, oval(200 + j * 140, 1192, 40, 10), '#ffffff', INK, 3)
    K.vvignette(c, 0.3)


def sh_rebuild(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1000, 1.08), (540, 960, 1.0), 'lin', 0.3, 13)
    night_sky(c, dawn=0.9)
    with vlayer(c, cam, 0.1):
        glow(c, 860, 1000, 500, '#ffe6a0', 0.7)
        c.drawCircle(860, 1010, 80, fillp('#fff0c0'))
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-300, 1300, 1400, 2300), fillp(None, 1, shader=lin(0, 1300, 0, 1920, ['#7a8a5a', '#5a6a42'])))
        burnt_frame(c, 540, 1320, 780, T, 1.0)
        pencil_house(c, 540, 1320, 780, ease_io(ramp(lt, 0.3, dur - 0.2)), T)
    K.vvignette(c, 0.3)


def sh_morning(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1000, 1.0), (540, 980, 1.08), 'lin', 0.4, 14)
    night_sky(c, dawn=1.0)
    with vlayer(c, cam, 0.1):
        glow(c, 900, 880, 520, '#ffe6a0', 0.75)
        c.drawCircle(900, 900, 90, fillp('#fff0c0'))
    with vlayer(c, cam, 0.6):
        c.drawRect(skia.Rect.MakeLTRB(-300, 1100, 1400, 2300), fillp('#7a8a5a'))
        burnt_frame(c, 560, 1180, 700, T, 0.9)
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-300, 1450, 1400, 2300), fillp(None, 1, shader=lin(0, 1450, 0, 1920, ['#8a9a5a', '#6a7a42'])))
        for i, (x, y, hh) in enumerate(((140, 1700, 230), (920, 1700, 250), (240, 1760, 200), (840, 1770, 190))):
            kid(c, i, x, y, hh, T, False, False, facing=0.0, expr='smile')
        person(c, 'james', 450, 1700, 520, T, facing=0.3, expr='tender', lhand=(-15, -32), rhand=(26, -48), gest='lhand')
        person(c, 'larita', 640, 1705, 490, T, facing=-0.3, expr='smile', lhand=(-26, -48), rhand=(8, -44), gest=None)
    K.vvignette(c, 0.3)


def sh_road_look(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1000, 1.0), (600, 940, 1.1), 'lin', 0.4, 15)
    night_sky(c, dawn=1.0)
    with vlayer(c, cam, 0.5):
        c.drawPath(smooth_path([(-400, 980), (300, 900), (760, 860), (1100, 900), (1500, 960), (1500, 2000), (-400, 2000)]),
                   fillp('#7f9a5a'))
        c.drawPath(poly([(380, 2000), (1000, 2000), (790, 880), (740, 880)]), fillp('#6a6a6e'))
        for k in range(7):
            yy = 900 + k * 150
            c.drawRect(skia.Rect.MakeXYWH(760 + k * 6, yy, 6 + k * 2, 30 + k * 8), fillp('#e8d6a0'))
    with vlayer(c, cam, 1.0):
        person(c, 'james', 330, 1720, 760, T, facing=0.8, expr='thinking', lhand=(-15, -32), rhand=(18, -40), gest='rhand')
    K.vvignette(c, 0.3)


def sh_push_hill(c, lt, dur, T):
    # night again: push up the road to the hilltop where the car first appeared
    z = lerp(1.0, 2.2, ease_in(clamp(lt / dur)))
    cam = VCam(560, lerp(1000, 900, clamp(lt / dur)), z)
    night_sky(c)
    with vlayer(c, cam, 0.2):
        stars(c, T, 70, 800)
        fire_glow(c, 640, 860, 380, T, 0.6)
    with vlayer(c, cam, 0.6):
        c.drawPath(poly([(-500, 900), (300, 860), (640, 880), (1000, 840), (1600, 900), (1600, 2400), (-500, 2400)]), fillp('#0e121a'))
        c.drawPath(poly([(200, 2400), (1000, 2400), (600, 880), (560, 880)]), fillp('#26262c'))
        for k in range(8):
            ph = (T * 0.8 + k / 8) % 1
            yy = lerp(890, 2300, ph ** 2)
            c.drawRect(skia.Rect.MakeXYWH(578, yy, 4 + 14 * ph ** 2, 10 + 70 * ph ** 2), fillp('#e8d6a0', 0.8))
        car_side(c, 610, 880, 0.12, T, True, False)
    K.vvignette(c, 0.5)


def sh_loop_end(c, lt, dur, T):
    # back inside the car, settling exactly on the opening frame (T=0 composition) for a seamless loop
    u = ease_out(clamp(lt / dur))
    cam = VCam(lerp(600, 540, u), lerp(880, 960, u), lerp(1.25, 1.0, u))
    interior(c, T, cam, lerp(1.0, 0.55, u))


SHOTS = [
    (0.0, 6.9, sh_hook), (6.9, 10.0, sh_driving), (10.0, 12.5, sh_wrong_way), (12.5, 15.9, sh_hilltop),
    (15.9, 19.7, sh_asleep_james), (19.7, 23.8, sh_asleep_kids), (23.8, 27.7, sh_wake), (27.7, 30.3, sh_escape),
    (30.3, 31.9, sh_trucks), (31.9, 35.9, sh_huddle), (35.9, 41.0, sh_larita), (41.0, 44.3, sh_fostered),
    (44.3, 46.6, sh_rebuild), (46.6, 49.2, sh_morning), (49.2, 52.7, sh_road_look), (52.7, 55.2, sh_push_hill),
    (55.2, 999, sh_loop_end),
]


def frame(c, T):
    for a, b, fn in SHOTS:
        if a <= T < b:
            break
    b = min(b, TOTAL)
    c.save()
    fn(c, T - a, b - a, T)
    c.restore()
    K.draw_true_story(c, T)
    K.draw_caption(c, V.caps, T, COLORS)


# ------------------------------------------------------------------ audio
def sfx(n):
    from scipy.signal import lfilter
    SR = K.SR
    rng = np.random.default_rng(11)
    fx = np.zeros(n)
    t_ = lambda d: np.arange(int(d * SR)) / SR

    def lp(x, fc):
        a = np.exp(-2 * np.pi * fc / SR)
        return lfilter([1 - a], [1, -a], lfilter([1 - a], [1, -a], x))

    def chime():
        t = t_(1.2)
        s = np.zeros_like(t)
        for f0, t0 in ((1046.5, 0.0), (1318.5, 0.16)):
            tt = np.clip(t - t0, 0, None)
            s += np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 5) * (t >= t0)
        return s * 0.10

    def engine(d):
        t = t_(d)
        nz = lp(rng.standard_normal(len(t)), 140)
        return (nz * 0.5 + 0.12 * np.sin(2 * np.pi * 48 * t) + 0.06 * np.sin(2 * np.pi * 96 * t)) * 0.35

    def crackle(d, dens=25):
        t = t_(d)
        out = lp(rng.standard_normal(len(t)), 400) * 0.06
        for _ in range(int(d * dens)):
            i = rng.integers(0, len(t) - 400)
            k = np.arange(300)
            out[i:i + 300] += rng.standard_normal(300) * np.exp(-k / 40) * rng.uniform(0.05, 0.25)
        return out

    def bang():
        t = t_(0.5)
        return (lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 18) * 0.9 + np.sin(2 * np.pi * 70 * t) * np.exp(-t * 14) * 0.7)

    def siren(d):
        t = t_(d)
        f = 760 + 180 * np.sign(np.sin(2 * np.pi * 0.8 * t))
        f = lp(f, 6)
        ph = 2 * np.pi * np.cumsum(f) / SR
        return lp(np.sin(ph) + 0.3 * np.sin(2 * ph), 1800) * 0.05

    def birds(d):
        out = np.zeros(int(d * SR))
        for _ in range(int(d * 2.5)):
            t0 = rng.uniform(0, d - 0.4)
            for j in range(rng.integers(2, 5)):
                tt = t_(0.08)
                f0 = rng.uniform(2800, 4200)
                ch = np.sin(2 * np.pi * (f0 + 9000 * tt * rng.choice([-1, 1])) * tt) * np.sin(np.pi * tt / 0.08) * 0.04
                K.place(out, ch, t0 + j * 0.11)
        return out

    def fade(x, fi=0.3, fo=0.3):
        x = x.copy()
        a, b = int(fi * SR), int(fo * SR)
        x[:a] *= np.linspace(0, 1, a)
        x[-b:] *= np.linspace(1, 0, b)
        return x

    K.place(fx, chime(), 0.02)
    K.place(fx, fade(engine(10.0), 0.05, 0.4), 0.0, 1.0)
    K.place(fx, fade(engine(2.6), 0.2, 0.3), 10.0, 0.7)
    K.place(fx, fade(crackle(3.6, 12), 0.6, 0.3), 12.4, 0.5)
    K.place(fx, fade(crackle(8.0, 8), 0.4, 0.4), 15.9, 0.25)
    K.place(fx, bang(), 23.85, 1.0)
    K.place(fx, fade(crackle(12.2, 30), 0.1, 1.0), 23.85, 0.9)
    K.place(fx, fade(siren(6.5), 1.0, 1.5), 29.8, 1.0)
    K.place(fx, fade(crackle(5.0, 6), 0.3, 1.0), 36.0, 0.3)
    K.place(fx, fade(birds(11.5), 0.8, 1.0), 41.0, 1.0)
    K.place(fx, fade(engine(5.2), 0.8, 0.6), 52.7, 0.8)
    K.place(fx, chime(), 55.3, 0.9)
    return fx


def build_audio():
    n = int(round(TOTAL * K.SR))
    voice = np.zeros(n)
    voice[:min(n, len(V.x))] = V.x[:n]
    x = K.load_track(MUSIC)
    B = 10 / 3
    # suspense (track 53.3-63.3, looped) under the drive + fire, tender opening under lines 6-8, warm lift for 9-11
    segs = [(55.0, 19 * B), (16 * B, 19 * B), (16 * B, 19 * B), (18 * B, 19 * B), (0.0, 4 * B), (20 * B, None)]
    mus, spl = K.fit_music(x, segs, n, start=0.0, xf=1.5, fade_out=1.0)
    st = K.mix(voice, sfx(n), mus, os.path.join(WORK, 'mix.wav'), target=-14.0, bed=-24.0, tp=-3.0)
    print('music splices (video s, track s):', spl)
    print(st)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'audio':
        build_audio()
    elif mode == 'still':
        ps = K.stills(frame, [float(t) for t in sys.argv[2:]], os.path.join(WORK, 'frames'))
        K.contact(ps, os.path.join(WORK, 'contact_%s.png' % sys.argv[2]))
        print('\n'.join(ps))
    elif mode == 'video':
        K.render(frame, NF, os.path.join(WORK, 'mix.wav'), OUT_MP4, workers=2, tmpdir=WORK)
        print('rendered', OUT_MP4)
