"""Short: "Thanks to Arsenal" (2026-11-arsenal-mud). Story-specific sets, cast and shots on top of shortkit + rig.
python3 story_arsenalmud.py audio | still t1 t2 ... | video | caps
No logos, crests, scoreboards or prop text anywhere, except the card's verbatim line.
"""
import os, sys, math
import numpy as np
import skia
from gfx import *
import rig
from rig import draw_person, gesture
import shortkit as K
from shortkit import VCam, vlayer, vcam, VW, VH
from sets import glow, smooth_path, tree, bush

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY = os.path.join(REPO, 'stories', '2026-11-arsenal-mud')
AUD = os.path.join(STORY, 'vo')
MUSIC = os.path.join(REPO, 'assets', 'music_warm_folk.mp3')
OUT_MP4 = os.path.join(REPO, 'videos', '2026-11-arsenal-mud-short.mp4')
WORK = os.environ.get('OSA_WORK', '/tmp/claude-0/-home-claude-one-small-act/98b0ddb6-e03a-5b23-b611-77e6891d4e9c/scratchpad/arsenalmud/work')
os.makedirs(WORK, exist_ok=True)

V = K.Voice(os.path.join(AUD, 'voiceover_full.wav'), os.path.join(AUD, 'timing.json'), tail=1.0)
TOTAL, NF = V.total, V.nf
rig.EXPR['fedup'] = (-16, -0.6, 'dot', 'teeth')  # brows down, open eyes, gritted teeth
COLORS = {'NARRATOR': '#ffffff', 'CASS': '#d6e8ff', 'SALLIE': '#ffd6e6'}
HOOK = ('HIS TEAM LOST…', 'THEN "HELP!"')
CARD_LINES = ('Thanks to Arsenal', 'for being rubbish', 'at football!')  # verbatim: "Thanks to Arsenal for being rubbish at football!"

# ------------------------------------------------------------------ cast
CAST = {
    'cass': dict(name='cass', skin='#eec4a0', hair='short', hair_col='#6a4a32', stubble=True, top='jumper', top_col='#3c5a7a',
                 pants='#4a4638', shoes='#3a2a20', hs=1.0, seed=31),
    'sallie': dict(name='sallie', skin='#f0c8a8', hair='long', hair_col='#8a5a34', top='blouse', top_col='#3f8f8a',
                   pants='#3b3a4f', shoes='#4a3a30', hs=0.94, seed=32),
}
SALLIE_MUD = dict(CAST['sallie'], pants='#5a3e26', shoes='#5a3e26')
SPK = {'cass': 'CASS', 'sallie': 'SALLIE'}
MUD, MUD_D, MUD_L = '#5a3e26', '#3e2a18', '#8a6a48'


def person(c, who, x, y, h, T, sp=None, gest='rhand', **st):
    s = dict(sp or CAST[who])
    spk = SPK.get(who)
    if spk:
        m = V.mouth(spk, T)
        if spk == 'CASS' and T < 4.45 and m == 4:  # line 1: no grin-like D shape, keep it a frustrated shout
            m = 2
        st.setdefault('mouth', m)
        if V.speaking(spk, T) and gest:
            gx, gy = gesture(T, s.get('seed', 0))
            hx, hy = st.get(gest, (15, -31) if gest == 'rhand' else (-15, -31))
            st[gest] = (hx + gx, hy + gy)
    draw_person(c, s, x, y, h, st, T)


def crew_spec(i, kind='fire'):
    sk = ['#e9bf98', '#b9835e', '#d6a077', '#8a5a3c'][i % 4]
    hc = ['#3a2a1e', '#1f1712', '#6a4a32', '#2a1f19'][i % 4]
    if kind == 'fire':
        return dict(name='ff%d' % i, skin=sk, hair='short', hair_col=hc, top='jumper', top_col='#2a2d38', cap='#e2b51e',
                    pants='#2a2d38', shoes='#141414', seed=40 + i)
    if kind == 'police':
        return dict(name='pc%d' % i, skin=sk, hair='short', hair_col=hc, top='jumper', top_col='#cfdc3a', cap='#1a2340',
                    pants='#1a2340', shoes='#141414', seed=50 + i)
    return dict(name='pm%d' % i, skin=sk, hair='short', hair_col=hc, top='jumper', top_col='#3a7a52', pants='#2a3a30',
                shoes='#141414', seed=60 + i)


def crew(c, i, x, y, h, T, kind='fire', **st):
    draw_person(c, crew_spec(i, kind), x, y, h, st, T)
    if kind == 'fire':  # reflective bands
        u = h / 90.0
        for yy in (-34, -28.5):
            c.drawLine(x - 12.5 * u, y + yy * u, x + 12.5 * u, y + yy * u, strokep('#eef07a', 1.7 * u, 0.95))


def blanket(c, x, y, h, col, T, seed=0, a=1.0):
    u = h / 90.0
    sway = math.sin(T * 2 + seed) * 0.8 * u
    p = smooth_path([(-14 * u, -61 * u), (14 * u, -61 * u), (20 * u + sway, -36 * u), (17 * u + sway, -15 * u),
                     (-17 * u + sway, -15 * u), (-20 * u + sway, -36 * u)], True, 0.35)
    c.save()
    c.translate(x, y)
    draw(c, p, col, INK, max(2, u * 1.0), fa=a, sa=a)
    for k in range(3):
        c.drawLine(-8 * u + k * 7 * u, -50 * u, -10 * u + k * 7 * u + sway, -20 * u, strokep(shade(col, -0.25), 0.7 * u, a))
    c.drawLine(-12 * u, -56 * u, 12 * u, -56 * u, strokep(shade(col, 0.25), 1.2 * u, 0.8 * a))
    c.restore()


def sallie_mud(c, x, mud_y, h, T, rise=0.0, shiver=True, blanket_a=0.0, **st):
    """Sallie standing in mud: everything below the mud line is hidden; rise 0 = chest-deep, 1 = feet on the surface."""
    u = h / 90.0
    jit = math.sin(T * 37) * 0.45 * u if shiver else 0.0
    fy = mud_y + 46 * u * (1 - rise)
    st.setdefault('facing', -0.3)
    st.setdefault('expr', 'concerned')
    st.setdefault('lhand', (-24, -49))
    st.setdefault('rhand', (24, -49))
    st.setdefault('shadow', False)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-3000, -3000, 4000, mud_y + 3))
    person(c, 'sallie', x + jit, fy, h, T, sp=SALLIE_MUD, **st)
    c.restore()
    # mud smudges on cheek and hands
    fx = st['facing'] * 4.2 * u
    c.drawCircle(x + jit + fx + 8 * u, fy - 69 * u, 1.5 * u, fillp(MUD, 0.65))
    c.drawCircle(x + jit + fx - 6 * u, fy - 76 * u, 1.0 * u, fillp(MUD, 0.5))
    if rise < 0.97:
        ring = oval(x, mud_y + 1.5 * u, 21 * u, 4.2 * u)
        draw(c, ring, MUD_D, None, 0, fa=0.9)
        c.drawArc(skia.Rect.MakeLTRB(x - 19 * u, mud_y - 2 * u, x + 19 * u, mud_y + 5 * u), 200, 140, False,
                  strokep(MUD_L, 0.9 * u, 0.7))
    if blanket_a > 0:
        blanket(c, x + jit, fy, h, '#c9863e', T, 3, blanket_a)


# ------------------------------------------------------------------ props
def tv(c, x, y, w, h, T, glow_a=1.0):
    """generic green pitch, tiny generic players, no scoreboard/graphics. (x,y) = screen top-left"""
    glow(c, x + w / 2, y + h / 2, w * 0.95, '#8fe09a', 0.22 * glow_a)
    draw(c, rrect(x - 16, y - 16, w + 32, h + 32, 14), '#141418', INK, 5)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    for k in range(8):
        c.drawRect(skia.Rect.MakeXYWH(x + k * w / 8, y, w / 8 + 1, h), fillp('#3f9a4a' if k % 2 else '#378c42'))
    lp = strokep('#e8f2e8', 2.5, 0.85)
    c.drawRect(skia.Rect.MakeXYWH(x + 12, y + 12, w - 24, h - 24), lp)
    c.drawLine(x + w / 2, y + 12, x + w / 2, y + h - 12, lp)
    c.drawCircle(x + w / 2, y + h / 2, h * 0.17, lp)
    for s in (0, 1):
        bx = x + 12 if s == 0 else x + w - 12 - w * 0.13
        c.drawRect(skia.Rect.MakeXYWH(bx, y + h * 0.28, w * 0.13, h * 0.44), lp)
    for k in range(10):
        col = '#f2c94c' if k % 2 else '#2a2f5a'
        px = x + w * (0.12 + 0.76 * hash01(k, 7)) + math.sin(T * (0.6 + hash01(k, 8)) + k) * w * 0.06
        py = y + h * (0.18 + 0.64 * hash01(k, 9)) + math.cos(T * (0.5 + hash01(k, 3)) + k) * h * 0.05
        c.drawCircle(px, py - 6, 3.2, fillp(col))
        c.drawLine(px, py - 3, px, py + 5, strokep(col, 3.5))
    bxp = x + w * (0.5 + 0.3 * math.sin(T * 0.9))
    c.drawCircle(bxp, y + h * (0.5 + 0.2 * math.sin(T * 1.3)), 3, fillp('#ffffff'))
    c.drawPath(poly([(x, y), (x + w * 0.45, y), (x, y + h * 0.5)]), fillp('#ffffff', 0.06))
    c.restore()


def door_leaf(c, o):
    """back door leaf hinged at x=1050 (right jamb), o: 0 closed .. 1 open toward camera"""
    a = o * math.radians(78)
    w = 220 * math.cos(a)
    grow = 26 * math.sin(a)
    x0 = 1050 - w
    p = poly([(x0, 560 - grow), (1050, 560), (1050, 1340), (x0, 1340 + grow)])
    draw(c, p, '#6a4630', INK, 5)
    if w > 40:
        c.drawPath(poly([(x0 + w * 0.15, 620 - grow * 0.8), (1050 - w * 0.12, 625), (1050 - w * 0.12, 900),
                         (x0 + w * 0.15, 900 - grow * 0.2)]), strokep('#4a3020', 4))
        c.drawPath(poly([(x0 + w * 0.15, 980), (1050 - w * 0.12, 980), (1050 - w * 0.12, 1280),
                         (x0 + w * 0.15, 1280 + grow * 0.7)]), strokep('#4a3020', 4))
        c.drawCircle(x0 + w * 0.12, 960, 9, fillp('#c9a24a'))


def living_room(c, cam, T, door_o=0.0):
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#2a2030'))
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-400, -300, 1500, 1345), fillp(None, 1, shader=lin(0, 0, 0, 1345, ['#8a6a58', '#b48a68'])))
        for k in range(-6, 20):
            c.drawLine(k * 90, -300, k * 90, 1345, strokep('#a07a5c', 10, 0.35))
        # window with dusk outside
        draw(c, rect(110, 250, 300, 330), None, None, 0)
        c.drawRect(skia.Rect.MakeXYWH(110, 250, 300, 330), fillp(None, 1, shader=lin(0, 250, 0, 580, ['#4a5a8a', '#f0a070'])))
        c.drawPath(smooth_path([(110, 520), (200, 480), (300, 500), (410, 470), (410, 580), (110, 580)]), fillp('#3a4a3a'))
        c.drawRect(skia.Rect.MakeXYWH(110, 250, 300, 330), strokep('#efe6d4', 14))
        c.drawLine(260, 250, 260, 580, strokep('#efe6d4', 8))
        c.drawLine(110, 415, 410, 415, strokep('#efe6d4', 8))
        # blank picture frame + wall lamp glow
        draw(c, rect(560, 380, 160, 120), '#d8c8a8', '#7a5a3a', 8)
        c.drawPath(smooth_path([(575, 485), (620, 430), (660, 470), (705, 420), (705, 485)]), fillp('#8aa86a'))
        glow(c, 640, 700, 380, '#ffd38a', 0.28)
        # back door frame + outside view (dusk garden)
        c.drawRect(skia.Rect.MakeXYWH(830, 560, 220, 780), fillp(None, 1, shader=lin(0, 560, 0, 1340, ['#5a6a9a', '#e8a070'])))
        c.drawPath(smooth_path([(830, 1100), (940, 1060), (1050, 1080), (1050, 1340), (830, 1340)]), fillp('#3f5a36'))
        draw(c, rect(812, 540, 256, 24), '#4a3020', INK, 4)
        c.drawLine(822, 560, 822, 1345, strokep('#4a3020', 18))
        c.drawLine(1058, 560, 1058, 1345, strokep('#4a3020', 18))
        # sofa against the wall
        draw(c, rrect(470, 1010, 330, 200, 40), '#5a6a4a', INK, 5)
        draw(c, rrect(450, 1120, 370, 200, 34), '#66784f', INK, 5)
        # TV on its cabinet
        draw(c, rrect(50, 1060, 420, 280, 14), '#6a4a34', INK, 5)
        c.drawLine(260, 1080, 260, 1320, strokep(INK, 3, 0.6))
        c.drawCircle(235, 1200, 7, fillp('#c9a24a'))
        c.drawCircle(285, 1200, 7, fillp('#c9a24a'))
        c.drawLine(260, 1010, 260, 1060, strokep('#141418', 22))
        tv(c, 80, 760, 360, 230, T)
        # skirting + floor
        c.drawRect(skia.Rect.MakeLTRB(-400, 1330, 1500, 1350), fillp('#e8dcc4'))
        c.drawRect(skia.Rect.MakeLTRB(-400, 1350, 1500, 2600), fillp('#6a4a34'))
        for k in range(14):
            c.drawLine(-400, 1350 + k * 70 + k * k * 2, 1500, 1350 + k * 70 + k * k * 2, strokep('#5a3c28', 3))
        draw(c, oval(560, 1560, 470, 90), '#8a3c3a', None, 0, fa=0.75)
        draw(c, oval(560, 1560, 420, 70), None, '#c98a5a', 4)
    if door_o > 0:
        pass


def coffee_table(c, x, y):
    draw(c, rrect(x - 190, y - 40, 380, 40, 10), '#7a5236', INK, 5)
    for s in (-1, 1):
        c.drawLine(x + s * 160, y, x + s * 160, y + 110, strokep('#5a3c28', 16))


def standing_card(c, x, y, s=1.0):
    """closed greetings card standing on a table: cover doodle only, no text"""
    draw(c, poly([(x - 70 * s, y), (x - 60 * s, y - 190 * s), (x + 70 * s, y - 180 * s), (x + 74 * s, y)]), '#f6efe0', INK, 4)
    draw(c, poly([(x + 74 * s, y), (x + 70 * s, y - 180 * s), (x + 100 * s, y - 172 * s), (x + 104 * s, y - 6 * s)]), '#d8cfbe', INK, 3)
    heart(c, x + 4 * s, y - 100 * s, 34 * s, '#e0606a')
    for k in range(5):
        a = k / 5 * 2 * math.pi
        c.drawCircle(x + 4 * s + math.cos(a) * 58 * s, y - 100 * s + math.sin(a) * 58 * s, 6 * s, fillp('#f2c14e'))


def heart(c, x, y, r, col):
    p = skia.Path()
    p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.4, y - r * 0.1, x - r * 0.7, y - r * 1.2, x, y - r * 0.45)
    p.cubicTo(x + r * 0.7, y - r * 1.2, x + r * 1.4, y - r * 0.1, x, y + r * 0.9)
    p.close()
    draw(c, p, col, INK, max(2, r * 0.08))


def quad(c, x, y, s, T, facing=1, rot=0.0, rider=True, light=1.0, moving=True, rider_expr='determined'):
    """farm quad bike, side view. (x,y) ground point under its centre; local +x = forward."""
    c.save()
    c.translate(x, y)
    if facing < 0:
        c.scale(-1, 1)
    c.rotate(rot)
    c.scale(s, s)
    if light > 0:
        c.drawPath(poly([(150, -92), (700, -230), (700, 40), (150, -66)]),
                   fillp(None, 1, shader=lin(150, 0, 700, 0, [hexc('#fff2c0', 0.5 * light), hexc('#fff2c0', 0)])))
    for wx in (-95, 100):
        draw(c, oval(wx + 14, -50, 44, 44), '#141418', INK, 4)
    draw(c, rrect(-60, -84, 125, 44, 10), '#2a2a2e', INK, 4)
    draw(c, rrect(-150, -112, 305, 34, 14), '#3d6a3a', INK, 5)
    for wx in (-95, 100):
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(wx - 62, -120, wx + 62, -10), 180, 180)
        p.close()
        draw(c, p, '#4a7a42', INK, 5)
    c.drawLine(-150, -126, -60, -126, strokep('#2a2a2e', 7))
    c.drawLine(120, -126, 160, -126, strokep('#2a2a2e', 7))
    draw(c, rrect(-85, -134, 120, 26, 12), '#1e1e22', INK, 4)
    if rider:
        u = 330 / 90.0
        draw_person(c, CAST['cass'], -30, -34, 330, dict(legs='sit', facing=0.5, expr=rider_expr, lhand=(29, -36), rhand=(31, -37),
                                                          shadow=False, mouth=0), T)
    c.drawLine(78, -110, 92, -168, strokep('#1e1e22', 9))
    c.drawLine(80, -168, 104, -168, strokep('#1e1e22', 11))
    draw(c, oval(150, -94, 12, 9), '#fff6c8' if light else '#c8c0a0', INK, 3)
    for wx in (-95, 100):
        draw(c, oval(wx, -46, 46, 46), '#222226', INK, 5)
        draw(c, oval(wx, -46, 18, 18), '#8a8a90', INK, 3)
        a = (T * 14 if moving else 0.4)
        for k in range(6):
            ang = a + k * math.pi / 3
            c.drawLine(wx + math.cos(ang) * 30, -46 + math.sin(ang) * 30, wx + math.cos(ang) * 44, -46 + math.sin(ang) * 44,
                       strokep('#3a3a40', 5))
    c.restore()


def dust(c, x, y, T, t0, s=1.0, n=7, a=0.6):
    age = T - t0
    if age < 0 or age > 1.2:
        return
    u = age / 1.2
    for k in range(n):
        px = x - (20 + 120 * hash01(k, 5)) * s * (0.4 + u)
        py = y - (10 + 60 * hash01(k, 6)) * s * u
        c.drawCircle(px, py, (20 + 30 * hash01(k, 7)) * s * (0.5 + u), fillp('#b8a07a', a * (1 - u)))


def farmhouse(c, x, yb, w, lit=1.0):
    h = w * 0.5
    draw(c, rect(x - w / 2, yb - h, w, h), '#c8b89a', INK, 4)
    for k in range(1, 6):
        c.drawLine(x - w / 2, yb - h + k * h / 6, x + w / 2, yb - h + k * h / 6, strokep('#a89878', 2))
    draw(c, poly([(x - w * 0.56, yb - h), (x - w * 0.36, yb - h * 1.6), (x + w * 0.36, yb - h * 1.6), (x + w * 0.56, yb - h)]),
         '#4a4a58', INK, 4)
    draw(c, rect(x + w * 0.2, yb - h * 1.85, w * 0.08, h * 0.35), '#8a6a5a', INK, 3)
    for fx, fy in ((-0.3, 0.75), (0.3, 0.75), (-0.3, 0.35), (0.3, 0.35)):
        wx, wy = x + fx * w - w * 0.07, yb - h * fy
        if lit:
            glow(c, wx + w * 0.07, wy + h * 0.1, w * 0.2, '#ffd98a', 0.35 * lit)
        draw(c, rect(wx, wy, w * 0.14, h * 0.2), '#ffd98a' if lit else '#2a3048', INK, 3)
    draw(c, rect(x - w * 0.07, yb - h * 0.45, w * 0.14, h * 0.45), '#6a4630', INK, 3)


def barn(c, x, yb, w):
    h = w * 0.7
    draw(c, rect(x - w / 2, yb - h, w, h), '#8a4a36', INK, 5)
    for k in range(1, 10):
        c.drawLine(x - w / 2 + k * w / 10, yb - h, x - w / 2 + k * w / 10, yb, strokep('#6e3a2a', 3))
    draw(c, poly([(x - w * 0.58, yb - h), (x, yb - h * 1.55), (x + w * 0.58, yb - h)]), '#5a5a62', INK, 5)
    draw(c, rect(x - w * 0.22, yb - h * 0.62, w * 0.44, h * 0.62), '#6e3a2a', INK, 4)
    c.drawLine(x - w * 0.22, yb - h * 0.62, x + w * 0.22, yb, strokep('#efe6d4', 6))
    c.drawLine(x + w * 0.22, yb - h * 0.62, x - w * 0.22, yb, strokep('#efe6d4', 6))


def reeds(c, x, y, h, T, n=7, seed=0, col='#4a6a32', a=1.0):
    for k in range(n):
        xx = x + (k - n / 2) * h * 0.09 + hash01(k, seed) * h * 0.05
        hh = h * (0.7 + 0.3 * hash01(k, seed + 1))
        sw_ = math.sin(T * 1.4 + k + seed) * h * 0.03
        p = smooth_path([(xx, y), (xx + sw_ * 0.5, y - hh * 0.5), (xx + sw_, y - hh)], False)
        c.drawPath(p, strokep(shade(col, -0.3), h * 0.035 + 2, a))
        c.drawPath(p, strokep(col, h * 0.025, a))
        if k % 2 == 0:
            draw(c, rrect(xx + sw_ - h * 0.018, y - hh - h * 0.02, h * 0.036, h * 0.11, h * 0.018), '#6a4a2e', None, 0, fa=a)


def mist(c, T, y0, y1, a=0.2, n=5, seed=0):
    for k in range(n):
        y = y0 + (y1 - y0) * (k + 0.5) / n
        x = (T * (12 + 8 * hash01(k, seed)) + hash01(k, seed + 2) * 900) % 1600 - 500
        c.drawOval(skia.Rect.MakeXYWH(x - 300, y - 30, 900, 70), fillp('#e8eef4', a, blur=18))


def sky(c, night=0.0):
    top = mix('#33407a', '#070b1c', night)
    bot = mix('#f0a070', '#18223e', night)
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp(None, 1, shader=lin(0, 0, 0, VH * 0.75, [top, mix(top, bot, 0.55), bot])))


def stars(c, T, n=50, y1=700, a=1.0):
    for k in range(n):
        x = VW * hash01(k, 31) * 1.6 - VW * 0.3
        y = y1 * hash01(k, 32) - 100
        tw = 0.5 + 0.5 * math.sin(T * (1 + hash01(k, 33) * 3) + k)
        c.drawCircle(x, y, 1.5 + 2 * hash01(k, 34), fillp('#ffffff', a * (0.35 + 0.6 * tw)))


def ditch_set(c, cam, T, night=0.0, mud_y=1180, cx=620, rx=430, spot=None, tree_off=0):
    """valley floor by the river: distant hillside, mist, near ground with a mud-filled ditch (mud surface at mud_y)"""
    sky(c, night)
    if night > 0.5:
        with vlayer(c, cam, 0.15):
            stars(c, T, 40, 500, 0.8)
    with vlayer(c, cam, 0.5):
        hp = smooth_path([(-500, 760), (0, 600), (400, 560), (800, 610), (1100, 540), (1600, 600), (1600, 1400), (-500, 1400)], True, 0.4)
        c.drawPath(hp, fillp(mix('#4a6a3e', '#121c1a', night)))
        for k in range(4):
            yy = 660 + k * 70
            c.drawPath(smooth_path([(-500, yy + 40), (300, yy - 10 + k * 8), (900, yy + 20), (1600, yy - 20)], False),
                       strokep(mix('#2f4a2c', '#0c1412', night), 10, 0.8))
        for k in range(7 if tree_off is not None else 0):
            tree(c, -200 + (tree_off or 0) + k * 230, 700 + (k % 3) * 25, 150, mix('#2f5a35', '#0e1814', night), T, k)
    with vlayer(c, cam, 0.75):
        c.drawRect(skia.Rect.MakeLTRB(-500, 860, 1600, 1500), fillp(mix('#5a7a40', '#16221a', night)))
        c.drawPath(smooth_path([(-500, 910), (200, 880), (600, 920), (1000, 885), (1600, 910), (1600, 950), (1000, 930), (600, 965),
                                (200, 925), (-500, 955)], True, 0.4), fillp(mix('#7a9ac0', '#1e2c48', night)))
        mist(c, T, 840, 960, 0.22 * (1 - 0.4 * night), 3, 4)
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-500, 990, 1700, 2600), fillp(None, 1, shader=lin(0, 990, 0, 1900, [
            mix('#5f7c3a', '#1a2818', night), mix('#4a6430', '#121c12', night)])))
        for k in range(70):
            x = -450 + k * 32
            yy = 1010 + (k * 37 % 5) * 120
            c.drawLine(x, yy, x + 8, yy - 26, strokep(mix('#7a9a4a', '#22341e', night), 4))
        # ditch: dark rim, mud body with sheen
        rim = smooth_path([(cx - rx - 30, mud_y + 10), (cx - rx * 0.6, mud_y - 34), (cx, mud_y - 44), (cx + rx * 0.6, mud_y - 36),
                           (cx + rx + 30, mud_y + 6), (cx + rx * 0.7, mud_y + 150), (cx, mud_y + 175), (cx - rx * 0.7, mud_y + 150)], True, 0.45)
        draw(c, rim, mix('#3a2a1a', '#140e0a', night), None, 0)
        body = smooth_path([(cx - rx, mud_y + 8), (cx - rx * 0.6, mud_y - 14), (cx, mud_y - 22), (cx + rx * 0.6, mud_y - 14),
                            (cx + rx, mud_y + 6), (cx + rx * 0.68, mud_y + 132), (cx, mud_y + 152), (cx - rx * 0.68, mud_y + 132)], True, 0.45)
        c.drawPath(body, fillp(None, 1, shader=lin(0, mud_y - 20, 0, mud_y + 150, [mix(MUD, '#2a1c12', night * 0.7),
                                                                                    mix(MUD_D, '#1a120c', night * 0.7)])))
        for k in range(6):
            hx = cx + (hash01(k, 21) - 0.5) * rx * 1.4
            hy = mud_y + 20 + hash01(k, 22) * 100
            c.drawOval(skia.Rect.MakeXYWH(hx - 40, hy - 5, 80, 10), fillp(MUD_L, 0.35 * (1 - 0.5 * night)))
        if spot:
            sx, sy, sr = spot
            c.drawOval(skia.Rect.MakeXYWH(sx - sr, sy - sr * 0.3, sr * 2, sr * 0.6), fillp('#fff6d8', 0.22, blur=30))
        reeds(c, cx - rx - 40, mud_y + 30, 330, T, 8, 1, mix('#5a7a38', '#1e2e1a', night))
        reeds(c, cx + rx + 30, mud_y + 20, 300, T, 7, 5, mix('#5a7a38', '#1e2e1a', night))


# ------------------------------------------------------------------ hook text
def draw_hook(c, T):
    if T >= 2.45:
        return
    a = 1 - ramp(T, 2.05, 2.45)
    sz = 92
    while True:
        f = font(FONT_SUB, sz)
        w1 = f.measureText(HOOK[0])
        w2 = f.measureText(HOOK[1])
        if max(w1, w2) <= 740 or sz <= 50:
            break
        sz -= 2
    cx, cy = 480, 330
    pulse = 1 + 0.025 * math.sin(T * 7)
    c.save()
    c.translate(cx, cy)
    c.scale(pulse, pulse)
    W = max(w1, w2) + 64
    draw(c, rrect(-W / 2, -sz * 1.25, W, sz * 2.5, 30), '#000000', None, 0, fa=0.42 * a)
    draw_text(c, HOOK[0], 0, -sz * 0.12, f, '#ffffff', 'center', '#0b0b0b', 11, a, a)
    pre, hl = 'THEN ', '"HELP!"'
    wp, wh = f.measureText(pre), f.measureText(hl)
    x0 = -(wp + wh) / 2
    draw_text(c, pre, x0, sz * 0.98, f, '#ffffff', 'left', '#0b0b0b', 11, a, a)
    draw_text(c, hl, x0 + wp, sz * 0.98, f, '#ffd23a', 'left', '#0b0b0b', 11, a, a)
    c.restore()


# ------------------------------------------------------------------ shots  fn(c, lt, dur, T)
CAM0 = ((560, 900, 1.08), (690, 930, 1.0))


def sh_storm(c, lt, dur, T):
    cam = vcam(lt, dur, CAM0[0], CAM0[1], 'io', 0.6, 1)
    door_o = ease_out(ramp(lt, 2.55, 2.95)) * (1 - ease_in(ramp(lt, 3.85, 4.2)))
    living_room(c, cam, T, door_o)
    if lt < 2.25:  # closed door behind him while he is in front of it
        with vlayer(c, cam, 1.0):
            door_leaf(c, door_o)
    with vlayer(c, cam, 1.0):
        if lt < 2.25:
            r = ease_out(ramp(lt, -0.7, 0.25))
            shake = math.sin(T * 15) * 2.2 * ramp(lt, 0.0, 0.3) * (1 - ramp(lt, 0.9, 1.0))
            if lt < 0.95:
                lh = (lerp(-24, -26, r) + shake, lerp(-50, -74, r))
                rh = (lerp(24, 26, r) - shake, lerp(-50, -74, r))
            elif lt < 1.6:
                e = ease_io(ramp(lt, 0.95, 1.2))
                lh = (lerp(-26, -18, e), lerp(-74, -77, e))
                rh = (lerp(26, 18, e), lerp(-74, -77, e))
            else:
                e = ease_out(ramp(lt, 1.6, 1.85))
                lh = (lerp(-18, -22, e), lerp(-77, -30, e))
                rh = (lerp(18, 22, e), lerp(-77, -30, e))
            mouth = 3 if lt < 0.2 else None
            st = dict(facing=-0.35 + 0.9 * ease_io(ramp(lt, 1.9, 2.25)), expr='fedup', lhand=lh, rhand=rh,
                      tilt=-6 + 4 * math.sin(T * 3), gest=None)
            if mouth:
                st['mouth'] = mouth
            person(c, 'cass', 680, 1420 - 18 * math.sin(math.pi * clamp(lt / 0.45)) * (lt < 0.45), 700, T, **st)
            if lt < 0.7:
                fa = 1 - ramp(lt, 0.3, 0.7)
                u = 700 / 90
                for s in (-1, 1):
                    hx = 680 + s * 26 * u
                    hy = 1420 - 74 * u
                    for k in range(3):
                        c.drawLine(hx + s * (40 + k * 6), hy - 20 + k * 34, hx + s * (78 + k * 8), hy - 40 + k * 34,
                                   strokep('#ffffff', 6, 0.85 * fa))
        elif lt < 4.2:
            e = ease_io(ramp(lt, 2.25, 3.65))
            x = lerp(680, 945, e)
            y = lerp(1420, 1345, ease_in(ramp(lt, 3.0, 3.65)))
            h = lerp(700, 640, e)
            if lt > 3.2:
                c.save()
                c.clipRect(skia.Rect.MakeLTRB(830, 300, 1050, 1346))
            person(c, 'cass', x, y, h, T, facing=0.6, expr='fedup', legs='walk' if lt < 3.7 else 'stand', phase=T * 10,
                   lhand=(-16, -34), rhand=(18, -32), gest=None)
            if lt > 3.2:
                c.restore()
        if lt >= 2.25:
            door_leaf(c, door_o)
    K.vvignette(c, 0.4)


def ridge_at(x, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return lerp(y0, y1, (x - x0) / (x1 - x0))
    return pts[-1][1]


HILL = [(250, 2000), (420, 1520), (560, 1310), (760, 1250), (1600, 1210)]


def sh_barn(c, lt, dur, T):
    u = ease_io(ramp(lt, 1.5, dur))
    cam = VCam(lerp(560, 300, u) + 3 * math.sin(lt * 0.8), lerp(980, 1300, u), lerp(1.0, 2.0, u ** 1.3))
    sky(c, 0.15)
    with vlayer(c, cam, 0.25):
        glow(c, 200, 760, 300, '#ffd090', 0.5)
        c.drawCircle(200, 780, 60, fillp('#ffe0a8', 0.9))
    with vlayer(c, cam, 0.55):
        c.drawPath(smooth_path([(-600, 980), (-100, 860), (300, 900), (700, 840), (1200, 900), (1700, 870), (1700, 1500), (-600, 1500)]),
                   fillp('#56704a'))
        for k in range(8):
            tree(c, -400 + k * 260, 930 + (k % 2) * 20, 120, '#3a5a36', T, k)
    with vlayer(c, cam, 0.8):
        c.drawRect(skia.Rect.MakeLTRB(-800, 1080, 1800, 1900), fillp('#4f6c3a'))
        c.drawPath(smooth_path([(-800, 1300), (-200, 1270), (200, 1330), (500, 1290), (900, 1340), (1800, 1300), (1800, 1350),
                                (900, 1385), (500, 1335), (200, 1375), (-200, 1315), (-800, 1345)], True, 0.4), fillp('#7a9ac0'))
        mist(c, T, 1190, 1420, 0.3, 4, 7)
        reeds(c, 300, 1360, 70, T, 9, 3)
        reeds(c, 120, 1350, 60, T, 7, 8)
    with vlayer(c, cam, 1.12):
        p = poly(HILL + [(1600, 2600), (250, 2600)])
        c.drawPath(p, fillp(None, 1, shader=lin(0, 1200, 0, 2000, ['#6a8a44', '#3e5a2a'])))
        c.drawPath(poly(HILL, False), strokep('#2e4220', 5))
        barn(c, 1010, 1222, 330)
        e = ease_out(ramp(lt, 0.0, 1.3))
        x = lerp(560, 720, e)
        y = ridge_at(x, HILL) + 6
        stop = lt > 1.3
        person(c, 'cass', x, y, 480, T, facing=0.5 if not stop else lerp(0.5, -0.7, ease_io(ramp(lt, 1.3, 1.7))),
               legs='walk' if not stop else 'stand', phase=T * 9, expr='neutral' if not stop else 'thinking',
               tilt=10 * ease_io(ramp(lt, 1.4, 1.8)), lhand=(-16, -32) if not stop else (-17, -74), rhand=(16, -32), gest=None)
        for k in range(14):
            gx = 300 + k * 90
            gy = ridge_at(gx, HILL)
            c.drawLine(gx, gy + 4, gx - 6, gy - 22, strokep('#7a9a4a', 5))
    K.vvignette(c, 0.4)


def ripples(c, x, y, T, t0, a=1.0):
    for k in range(3):
        ph = ((T - t0) * 0.9 + k / 3) % 1
        r = 60 + ph * 360
        c.drawArc(skia.Rect.MakeLTRB(x - r, y - r * 0.8, x + r, y + r * 0.8), 215, 110, False,
                  strokep('#ffffff', 7 * (1 - ph) + 2, a * 0.8 * math.sin(ph * math.pi)))


def sh_help(c, lt, dur, T):
    cam = vcam(lt, dur, (600, 1060, 1.25), (620, 1060, 1.42), 'lin', 0.4, 3)
    ditch_set(c, cam, T, 0.35, 1180)
    with vlayer(c, cam, 1.0):
        sallie_mud(c, 620, 1180, 500, T, facing=-0.1, expr='concerned', tilt=-6, lhand=(-24, -48), rhand=(26, -92))
        reeds(c, 380, 1300, 260, T, 6, 11, '#3e5a2e')
        ripples(c, 620, 860, T, 8.42)
    K.vvignette(c, 0.55)


def slope_y(x):
    return 1300 - 0.55 * (x - 540)


def slope_bg(c, cam, T, night=0.0, house=False):
    sky(c, night)
    with vlayer(c, cam, 0.2):
        if night < 0.5:
            glow(c, 820, 700, 300, '#ffd090', 0.4)
        else:
            stars(c, T, 40, 700, 0.7)
    with vlayer(c, cam, 0.5):
        c.drawPath(smooth_path([(-1500, 1100), (-500, 900), (300, 860), (1000, 760), (2000, 700), (2600, 700), (2600, 2600),
                                (-1500, 2600)]), fillp(mix('#56704a', '#18241c', night)))
        for k in range(10):
            tree(c, -1200 + k * 360, 980 - k * 30, 140, mix('#3a5a36', '#0e1814', night), T, k)


def slope_fg(c, T, x0, x1, night=0.0):
    pts = [(x, slope_y(x)) for x in np.linspace(x0, x1, 8)]
    p = poly(pts + [(x1, 4000), (x0, 4000)])
    c.drawPath(p, fillp(mix('#5f7c3a', '#1c2a18', night)))
    c.drawPath(poly(pts, False), strokep(mix('#2e4220', '#0a120a', night), 5))
    for k in range(int(x0 // 70), int(x1 // 70)):
        gx = k * 70
        gy = slope_y(gx)
        c.drawLine(gx, gy + 4, gx - 8, gy - 26, strokep(mix('#86a650', '#2a3c22', night), 5))
        if k % 5 == 0:
            c.drawLine(gx + 20, gy + 2, gx + 20, gy - 90, strokep('#6a5038', 10))
        if k % 3 == 0:
            c.drawLine(gx, gy + 60 + (k % 4) * 50, gx + 30, gy + 50 + (k % 4) * 50, strokep(mix('#4a6430', '#121c12', night), 6))


def sh_quad_down(c, lt, dur, T):
    u = clamp(lt / dur)
    qx = lerp(1250, -350, u)
    qy = slope_y(qx)
    cam = VCam(qx + 60, qy - 300, 1.0)
    slope_bg(c, cam, T, 0.3)
    with vlayer(c, cam, 1.0):
        slope_fg(c, T, qx - 900, qx + 900, 0.3)
        bounce = abs(math.sin(T * 8.5)) * 16
        quad(c, qx, qy - bounce, 0.95, T, -1, math.degrees(math.atan(0.55)) + 3 * math.sin(T * 8.5), light=1.0)
        for k in range(4):
            dust(c, qx + 160, qy - 10, T, 9.72 + k * 0.6 + (T - 9.72) // 0.6 * 0 , 0.8, 5, 0.4)
        for k in range(6):
            ph = (T * 2.5 + k / 6) % 1
            c.drawLine(qx + 200 + ph * 300, qy - 100 - k * 30 - ph * 160, qx + 280 + ph * 300, qy - 140 - k * 30 - ph * 160,
                       strokep('#ffffff', 4, 0.5 * math.sin(ph * math.pi)))
    K.vvignette(c, 0.45)


def sh_found(c, lt, dur, T):
    cam = vcam(lt, dur, (500, 1010, 1.05), (560, 1020, 1.13), 'io', 0.5, 5)
    ditch_set(c, cam, T, 0.4, 1180, 650, 380, spot=(680, 1180, 260))
    with vlayer(c, cam, 1.0):
        e = ease_out(ramp(lt, 0.0, 0.9))
        qx = lerp(-260, 200, e)
        quad(c, qx, 1090, 0.72, T, 1, -3 * (1 - e), rider=lt < 1.1, light=1.0, moving=e < 1)
        dust(c, qx - 40, 1085, T, 12.5 + 0.7, 1.0, 8, 0.55)
        if lt >= 1.1:
            j = ease_out(ramp(lt, 1.1, 1.5))
            x = lerp(200, 400, j)
            y = lerp(1060, 1110, j) - math.sin(math.pi * j) * 40
            person(c, 'cass', x, y, 470, T, facing=0.55, expr='surprised', legs='jump' if j < 1 else 'stand',
                   lhand=(-18, -40), rhand=(24, -56) if j >= 1 else (20, -40), gest=None)
        wave = lt < 1.6
        sallie_mud(c, 690, 1180, 520, T, facing=-0.45, expr='concerned', tilt=-5,
                   rhand=(26, -90 + 4 * math.sin(T * 9)) if wave else (24, -49), lhand=(-24, -49))
    K.vvignette(c, 0.5)


def sh_kneel(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 980, 1.0), (520, 960, 1.08), 'lin', 0.5, 6)
    ditch_set(c, cam, T, 0.45, 1190, 760, 360, spot=(760, 1190, 230))
    with vlayer(c, cam, 1.0):
        person(c, 'cass', 330, 1300, 640, T, facing=0.45, expr='surprised', legs='none', lhand=(-17, -82), rhand=(17, -82),
               gest=None, shadow=False, tilt=4)
        lip = smooth_path([(-200, 1185), (100, 1150), (360, 1160), (560, 1200), (600, 1290), (500, 1400), (-200, 1400)], True, 0.4)
        c.drawPath(lip, fillp('#3e5a2a'))
        c.drawPath(smooth_path([(-200, 1185), (100, 1150), (360, 1160), (560, 1200), (600, 1290)], False), strokep('#22341a', 5))
        for k in range(16):
            gx = -150 + k * 45
            gy = 1160 + (k * 13 % 4) * 6 + (0 if gx < 380 else (gx - 380) * 0.3)
            c.drawLine(gx, gy + 10, gx - 6 + 3 * math.sin(T * 2 + k), gy - 24, strokep('#5a7a38', 6))
        sallie_mud(c, 780, 1190, 600, T, facing=-0.55, expr='concerned', tilt=-10, lhand=(-25, -49), rhand=(24, -50))
    K.vvignette(c, 0.5)


def rot_pt(px, py, deg):
    a = math.radians(deg)
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)


def sh_rope(c, lt, dur, T):
    cam = vcam(lt, dur, (560, 1000, 1.06), (580, 1010, 1.0), 'lin', 0.5, 7)
    mud_y = 1170
    ditch_set(c, cam, T, 0.5, mud_y, 690, 380, spot=(700, mud_y, 240))
    with vlayer(c, cam, 1.0):
        # boards laid over the mud towards her
        for k, (bx, by, ang) in enumerate(((470, mud_y + 14, -4), (600, mud_y + 30, 3), (430, mud_y + 52, 8))):
            c.save()
            c.translate(bx, by)
            c.rotate(ang)
            draw(c, rect(-120, -9, 240, 18), '#b08a5a', INK, 4)
            c.drawLine(-110, 0, 110, 0, strokep('#8a6a40', 2))
            c.restore()
        pulling = lt < 2.5
        tug = max(0.0, math.sin(T * 4.2)) if pulling else 0.0
        rot = -12 - 7 * tug if pulling else lerp(-12, 0, ease_out(ramp(lt, 2.5, 2.9)))
        h, fx, fy = 520, 250, 1120
        uu = h / 90
        rh = (24, -44) if pulling else (lerp(24, 18, ramp(lt, 2.5, 2.9)), lerp(-44, -30, ramp(lt, 2.5, 2.9)))
        person(c, 'cass', fx, fy, h, T, facing=0.5, expr='strain' if pulling else 'concerned', legs='brace' if pulling else 'stand',
               rot=rot, lhand=(20, -46), rhand=rh, gest=None)
        hx, hy = rot_pt(rh[0] * uu, rh[1] * uu, rot)
        hx, hy = fx + hx, fy + hy
        sx, sy = 740, mud_y - 6
        if pulling:
            c.drawLine(hx, hy, sx - 40, sy, strokep('#c8a868', 7))
            c.drawLine(hx, hy, sx - 40, sy, strokep('#8a6a3a', 2))
            if tug > 0.6:
                for k in range(3):
                    mx, my = lerp(hx, sx, 0.3 + k * 0.2), lerp(hy, sy, 0.3 + k * 0.2)
                    c.drawLine(mx - 10, my - 22, mx + 10, my - 30, strokep('#ffffff', 4, 0.7))
        else:
            sag = 120 * ease_out(ramp(lt, 2.5, 3.0))
            c.drawPath(smooth_path([(hx, hy), ((hx + sx) / 2, (hy + sy) / 2 + sag), (sx - 40, sy)], False), strokep('#c8a868', 7))
        sallie_mud(c, 740, mud_y, 540, T, rise=0.04 * tug, facing=-0.5, expr='concerned', tilt=-6 + 4 * tug,
                   lhand=(-22, -50), rhand=(22, -50))
        u2 = 540 / 90
        c.drawOval(skia.Rect.MakeXYWH(740 - 15 * u2, mud_y - 9 * u2, 30 * u2, 7 * u2), strokep('#c8a868', 7))
    K.vvignette(c, 0.5)


def phone_nosig(c, x, y, w, h, T):
    """phone whose only content is empty signal bars (no words, no numbers)"""
    glow(c, x + w / 2, y + h / 2, w * 1.2, '#cfe4ff', 0.3)
    draw(c, rrect(x, y, w, h, w * 0.13), '#1c1d22', INK, 5)
    sx, sy, sw_, sh = x + w * 0.06, y + w * 0.06, w * 0.88, h - w * 0.12
    c.drawPath(rrect(sx, sy, sw_, sh, w * 0.09), fillp(None, 1, shader=lin(sx, sy, sx, sy + sh, ['#24324e', '#3a3a5a'])))
    pulse = 0.55 + 0.45 * math.sin(T * 5)
    bw = sw_ * 0.13
    base = sy + sh * 0.56
    bh = sh * 0.07
    bx = sx + sw_ * 0.22
    c.drawPath(rrect(bx, base - bh, bw, bh, 5), fillp('#9aa2ae'))
    xc, yc, r = sx + sw_ * 0.66, base - sh * 0.17, sw_ * 0.16
    for d in (1, -1):
        c.drawLine(xc - r, yc - d * r, xc + r, yc + d * r, strokep('#ff6a5a', 12, 0.7 + 0.3 * pulse))
    c.drawPath(poly([(sx, sy), (sx + sw_ * 0.4, sy), (sx, sy + sh * 0.3)]), fillp('#ffffff', 0.06))


def sh_nosignal(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 980, 1.0), (580, 960, 1.1), 'lin', 0.5, 8)
    sky(c, 0.6)
    with vlayer(c, cam, 0.4):
        c.drawPath(smooth_path([(-400, 1150), (300, 1000), (900, 1060), (1500, 980), (1500, 2600), (-400, 2600)]), fillp('#1e2c22'))
        mist(c, T, 1050, 1250, 0.15, 3, 2)
    with vlayer(c, cam, 1.0):
        bob = math.sin(T * 2.4) * 14 + lerp(30, -30, ease_io(clamp(lt / dur)))
        px, py = 420, 1700
        u = 1350 / 90
        phx, phy = 770, 1060 + bob
        person(c, 'cass', px, py, 1350, T, facing=0.35, expr='concerned', lhand=(-16, -30),
               rhand=((phx - px) / u, (phy + 80 - py) / u), gest=None, shadow=False, tilt=6)
        phone_nosig(c, phx - 120, phy - 220, 240, 420, T)
        c.drawCircle(phx - 112, phy + 80, 26, fillp(CAST['cass']['skin']))
        c.drawCircle(phx - 112, phy + 80, 26, strokep(INK, 5))
    K.vvignette(c, 0.5)


def slope2_y(x):
    return 1360 - 0.5 * (x - 200)


def sh_race_home(c, lt, dur, T):
    u = clamp(lt / dur)
    qx = lerp(60, 640, u)
    qy = slope2_y(qx)
    cam = VCam(lerp(470, 620, u), lerp(1060, 920, u), 1.0)
    sky(c, 0.55)
    with vlayer(c, cam, 0.3):
        stars(c, T, 30, 600, 0.5)
    with vlayer(c, cam, 1.0):
        pts = [(x, slope2_y(x)) for x in np.linspace(-500, 1600, 8)]
        c.drawPath(poly(pts + [(1600, 3000), (-500, 3000)]), fillp('#1f2e1c'))
        c.drawPath(poly(pts, False), strokep('#0e160c', 5))
        farmhouse(c, 1000, slope2_y(1000) + 30, 300, 1.0)
        for k in range(-6, 22):
            gx = k * 80
            gy = slope2_y(gx)
            c.drawLine(gx, gy + 4, gx + 8, gy - 24, strokep('#3a5030', 5))
        bounce = abs(math.sin(T * 9)) * 14
        quad(c, qx, qy - bounce, 0.78, T, 1, -math.degrees(math.atan(0.5)) + 3 * math.sin(T * 9), light=1.0)
        for k in range(6):
            ph = (T * 2.8 + k / 6) % 1
            c.drawLine(qx - 160 - ph * 260, qy - 60 - k * 26 + ph * 120, qx - 240 - ph * 260, qy - 30 - k * 26 + ph * 120,
                       strokep('#ffffff', 4, 0.45 * math.sin(ph * math.pi)))
    K.vvignette(c, 0.5)


def helicopter(c, x, y, s, T):
    c.save()
    c.translate(x, y + math.sin(T * 1.3) * 8)
    c.rotate(math.sin(T * 0.7) * 2)
    c.scale(s, s)
    draw(c, poly([(-70, -10), (-280, -34), (-280, -12), (-70, 22)]), '#c9ced6', INK, 4)
    draw(c, poly([(-282, -36), (-300, -86), (-268, -86), (-262, -30)]), '#c9ced6', INK, 4)
    c.drawCircle(-282, -52, 30, fillp('#ffffff', 0.15))
    c.drawCircle(-282, -52, 30, strokep('#ffffff', 2, 0.4))
    draw(c, oval(0, 0, 115, 64), '#dfe3e8', INK, 5)
    draw(c, smooth_path([(20, -48), (100, -24), (108, 10), (40, 6)], True, 0.4), '#3a4a66', INK, 4)
    c.drawLine(-50, 30, 70, 30, strokep('#e0b030', 8))
    for sx in (-50, 60):
        c.drawLine(sx, 58, sx - 10, 88, strokep(INK, 5))
    c.drawLine(-90, 88, 110, 88, strokep(INK, 6))
    c.drawLine(0, -64, 0, -82, strokep(INK, 7))
    c.drawOval(skia.Rect.MakeLTRB(-300, -92, 300, -76), fillp('#ffffff', 0.18))
    a = T * 31
    for k in range(2):
        L = 290 * math.cos(a + k * math.pi / 2)
        c.drawLine(-L, -84, L, -84, strokep('#2a2a30', 7, 0.85))
    on = math.sin(T * 9) > 0.3
    c.drawCircle(0, -68, 7, fillp('#ff4040' if on else '#5a1010'))
    if on:
        glow(c, 0, -68, 60, '#ff3030', 0.6)
    c.restore()


def searchlight(c, x0, y0, x1, y1, w1, a=1.0):
    p = poly([(x0 - 14, y0), (x0 + 14, y0), (x1 + w1, y1), (x1 - w1, y1)])
    c.drawPath(p, fillp(None, 1, shader=lin(0, y0, 0, y1, [hexc('#fff8dc', 0.45 * a), hexc('#fff8dc', 0.12 * a)])))
    c.drawOval(skia.Rect.MakeXYWH(x1 - w1, y1 - w1 * 0.28, w1 * 2, w1 * 0.56), fillp('#fff8dc', 0.3 * a, blur=20))


def rim_vehicle(c, x, y, s, T, col, k):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawPath(smooth_path([(-120, 0), (-120, -110), (60, -110), (110, -60), (120, 0)], True, 0.15), fillp('#0e1118'))
    for wx in (-70, 70):
        c.drawCircle(wx, 0, 24, fillp('#06070a'))
    for j, lx in enumerate((-60, 0)):
        on = math.sin(T * 11 + k * 1.7 + j * math.pi) > 0
        glow(c, lx, -118, 170, col, 0.75 if on else 0.12)
        c.drawCircle(lx, -116, 11, fillp(col if on else shade(col, -0.6)))
    glow(c, 120, -40, 140, '#fff2c0', 0.3)
    c.restore()


def sh_rescue(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 880, 1.1), (540, 990, 1.0), 'io', 0.5, 10)
    sky(c, 1.0)
    with vlayer(c, cam, 0.15):
        stars(c, T, 50, 600, 0.8)
    with vlayer(c, cam, 0.6):
        c.drawPath(smooth_path([(-500, 660), (200, 610), (700, 640), (1600, 600), (1600, 2400), (-500, 2400)]), fillp('#141e18'))
        for k, (vx, col) in enumerate(((-40, '#ff3030'), (220, '#3a6aff'), (470, '#3a6aff'), (720, '#ffb030'), (980, '#ff3030'))):
            rim_vehicle(c, vx, 640 - 10 * math.sin(vx * 0.004), 0.55, T, col, k)
    with vlayer(c, cam, 1.0):
        pts = [(-500, 760), (100, 760), (600, 900), (1000, 1080), (1600, 1150)]
        c.drawPath(smooth_path(pts + [(1600, 2600), (-500, 2600)], True, 0.3), fillp('#1c2a1a'))
        # zig-zag path down the slope
        c.drawPath(smooth_path([(120, 780), (500, 880), (260, 980), (620, 1100), (420, 1190)], False, 0.4), strokep('#2c3a26', 26))
        # ditch at the bottom, lit by the searchlight
        cx, my = 640, 1230
        draw(c, oval(cx, my + 20, 260, 50), '#24180e', None, 0)
        draw(c, oval(cx, my + 14, 240, 40), '#3a2818', None, 0)
        # boat team on the river
        c.drawRect(skia.Rect.MakeLTRB(-500, 1300, 1600, 1390), fillp('#1c2c48'))
        draw(c, smooth_path([(860, 1300), (1010, 1300), (1030, 1275), (840, 1275)], True, 0.3), '#e0702a', INK, 4)
        crew(c, 7, 910, 1288, 90, T, 'fire', legs='none', shadow=False)
        crew(c, 8, 975, 1288, 90, T, 'fire', legs='none', shadow=False)
        sallie_mud(c, cx, my, 170, T, facing=0.0, expr='concerned', lhand=(-24, -49), rhand=(24, -49))
        # firefighters carrying a board down; police at the top; paramedics with a bag
        e = ease_io(clamp(lt / dur))
        for j, (x0, y0, x1, y1) in enumerate(((140, 790, 380, 860), (420, 870, 300, 960), (260, 990, 520, 1080))):
            xx, yy = lerp(x0, x1, e), lerp(y0, y1, e)
            d = 1 if x1 > x0 else -1
            crew(c, j * 2, xx, yy, 190, T, 'fire', legs='walk', phase=T * 8 + j, facing=0.4 * d, expr='determined',
                 lhand=(18 * d, -50), rhand=(24 * d, -50))
            crew(c, j * 2 + 1, xx + 120 * d, yy + 18, 190, T, 'fire', legs='walk', phase=T * 8 + j + 2, facing=0.4 * d,
                 expr='determined', lhand=(-20 * d, -50), rhand=(-14 * d, -50))
            b0 = (xx + 20 * d * 190 / 90, yy - 50 * 190 / 90)
            b1 = (xx + 120 * d - 18 * d * 190 / 90, yy + 18 - 50 * 190 / 90)
            c.drawLine(b0[0], b0[1], b1[0], b1[1], strokep('#b08a5a', 12))
        crew(c, 1, 60, 762, 170, T, 'police', facing=0.3, expr='concerned', rhand=(28, -50))
        glow(c, 60 + 28 * 170 / 90 + 10, 762 - 50 * 170 / 90, 60, '#fff6c8', 0.7)
        crew(c, 2, 820, 1040, 180, T, 'para', facing=-0.4, expr='determined', legs='walk', phase=T * 8,
             rhand=(14, -30))
        draw(c, rrect(820 + 10, 1040 - 60, 36, 28, 6), '#e04040', INK, 3)
        searchlight(c, 470, 420, cx, my, 210, 0.9 + 0.1 * math.sin(T * 3))
        helicopter(c, 470, 360, 0.95, T)
    K.vvignette(c, 0.5)


def sh_free(c, lt, dur, T):
    cam = vcam(lt, dur, (560, 1010, 1.1), (540, 960, 1.0), 'io', 0.5, 11)
    mud_y = 1120
    ditch_set(c, cam, T, 1.0, mud_y, 560, 420, spot=(560, mud_y, 320), tree_off=None)  # no trunks behind her head
    with vlayer(c, cam, 1.0):
        searchlight(c, 640, -300, 560, mud_y, 330, 0.7)
        for bx, by, ang in ((560, mud_y + 6, 0), (330, mud_y + 18, 6), (790, mud_y + 16, -5)):
            c.save()
            c.translate(bx, by)
            c.rotate(ang)
            draw(c, rect(-150, -10, 300, 20), '#b08a5a', INK, 4)
            c.restore()
        rise = ease_io(ramp(lt, 0.15, 1.6))
        h = 470
        uu = h / 90
        sy_head = mud_y + 46 * uu * (1 - rise) - 52 * uu
        crew(c, 0, 330, mud_y, 500, T, 'fire', facing=0.5, expr='strain' if rise < 1 else 'smile',
             lhand=(28, (sy_head - mud_y) / (500 / 90) + 6), rhand=(34, (sy_head - mud_y) / (500 / 90) + 4))
        crew(c, 3, 800, mud_y, 500, T, 'fire', facing=-0.5, expr='strain' if rise < 1 else 'smile',
             lhand=(-34, (sy_head - mud_y) / (500 / 90) + 4), rhand=(-28, (sy_head - mud_y) / (500 / 90) + 6))
        ba = 1.0 if lt >= 1.9 else 0.0  # hard cut: blanket is on, fully opaque
        sallie_mud(c, 565, mud_y, h, T, rise=rise, shiver=lt < 2.2, blanket_a=ba, facing=0.0,
                   expr='concerned' if lt < 1.8 else 'tender', lhand=(-20, -46) if ba < 0.5 else (-6, -46),
                   rhand=(20, -46) if ba < 0.5 else (6, -46))
        person(c, 'cass', 110, mud_y - 150, 330, T, facing=0.5, expr='happy' if lt > 1.8 else 'concerned',
               lhand=(-16, -32), rhand=(22, -60) if lt > 2.0 else (16, -32), gest=None)
    K.vvignette(c, 0.45)


def sh_sallie_writes(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 960, 1.04), (520, 940, 1.12), 'lin', 0.4, 12)
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp(None, 1, shader=lin(0, 0, 0, VH, ['#efdcc8', '#e2c4a8'])))
    with vlayer(c, cam, 1.0):
        draw(c, rect(620, 300, 320, 360), '#bfe0f0', '#ffffff', 16)
        c.drawPath(smooth_path([(620, 560), (760, 520), (940, 560), (940, 660), (620, 660)]), fillp('#8ab86a'))
        glow(c, 780, 480, 420, '#fff6d0', 0.4)
        c.drawLine(300, 300, 300, 560, strokep(INK, 3))
        draw(c, poly([(230, 640), (370, 640), (330, 560), (270, 560)]), '#e8b44c', INK, 4)
        glow(c, 300, 660, 260, '#ffcf7a', 0.35)
        person(c, 'sallie', 520, 1330, 640, T, facing=0.3, expr='tender', legs='none', shadow=False,
               lhand=(-10, -40), rhand=(14 + 2 * math.sin(T * 9), -38 + 1.5 * math.sin(T * 13)), gest=None, mouth=0)
        draw(c, rrect(-200, 1130, 1500, 50, 12), '#a8784a', INK, 5)
        c.drawRect(skia.Rect.MakeLTRB(-200, 1180, 1500, 2400), fillp('#8a5e3a'))
        c.save()
        c.translate(600, 1112)
        c.rotate(-8)
        draw(c, rect(-120, -24, 240, 30), '#f6efe0', INK, 4)
        c.restore()
        pxn = 520 + 14 * 640 / 90 + 2 * math.sin(T * 9) * 640 / 90
        c.drawLine(pxn, 1050, pxn + 30, 1106, strokep('#2a3a8a', 8))
    K.vvignette(c, 0.3)


def kitchen(c, cam, T):
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp(None, 1, shader=lin(0, 0, 0, VH, ['#f2e4c8', '#e6d0a8'])))
    with vlayer(c, cam, 1.0):
        draw(c, rect(120, 280, 380, 380), '#bfe0f0', '#ffffff', 16)
        c.drawPath(smooth_path([(120, 560), (260, 500), (400, 540), (500, 500), (500, 660), (120, 660)]), fillp('#7aa85a'))
        c.drawLine(310, 280, 310, 660, strokep('#ffffff', 10))
        glow(c, 320, 480, 460, '#fff6d0', 0.45)
        for k in range(4):
            draw(c, rrect(640 + k * 90, 380, 70, 110, 10), ['#c96a4a', '#e0b04a', '#6a9ac0', '#8ab86a'][k], INK, 4)
        c.drawLine(600, 500, 1040, 500, strokep('#8a5e3a', 14))


def sh_envelope(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 980, 1.08), (540, 950, 1.0), 'lin', 0.4, 13)
    kitchen(c, cam, T)
    with vlayer(c, cam, 1.0):
        person(c, 'cass', 540, 1380, 700, T, facing=0.0, expr='smile', legs='none', shadow=False,
               lhand=(-14, -40), rhand=(14, -40), gest=None)
        draw(c, rrect(-200, 1150, 1500, 50, 12), '#a8784a', INK, 5)
        c.drawRect(skia.Rect.MakeLTRB(-200, 1200, 1500, 2400), fillp('#8a5e3a'))
        ex, ey = 540, 1060
        o = ease_out(ramp(lt, 0.15, 0.6))
        cs = ease_out(ramp(lt, 0.5, 1.0))
        draw(c, rect(ex - 70, ey - 120 - 70 * cs, 140, 100), '#f6efe0', INK, 4)
        heart(c, ex, ey - 75 - 70 * cs, 18, '#e0606a')
        draw(c, rect(ex - 130, ey - 80, 260, 160), '#f2ead8', INK, 5)
        c.drawPath(poly([(ex - 130, ey - 80), (ex, ey + 10 - 0 * o), (ex + 130, ey - 80)], False), strokep('#c8bca4', 3))
        fy = ey - 80 - 90 * o
        draw(c, poly([(ex - 130, ey - 80), (ex, ey - 80 + 90 * (1 - 2 * o)), (ex + 130, ey - 80)]), '#e6dcc6', INK, 4)
        for s in (-1, 1):
            c.drawCircle(ex + s * 120, ey + 10, 30, fillp(CAST['cass']['skin']))
            c.drawCircle(ex + s * 120, ey + 10, 30, strokep(INK, 5))
    K.vvignette(c, 0.3)


def sh_card(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 900, 1.0), (540, 880, 1.06), 'lin', 0.4, 14)
    kitchen(c, cam, T)
    with vlayer(c, cam, 1.0):
        person(c, 'cass', 540, 1308, 1100, T, facing=0.0, expr='happy', legs='none', shadow=False,
               lhand=(-25, -33), rhand=(25, -33), gest=None)
        op = ease_out(ramp(lt, 0.0, 0.35))
        c.save()
        c.translate(540, 920)
        c.rotate(-2.5 + 1.0 * math.sin(T * 1.1))
        c.scale(lerp(0.92, 1.0, op), lerp(0.92, 1.0, op))
        draw(c, rect(-312, -282, 624, 564), '#f8f2e4', INK, 6)
        c.drawRect(skia.Rect.MakeXYWH(-312, -282, 624, 22), fillp('#e8c86a'))
        f = font(FONT_HAND, 60)
        mw = max(f.measureText(l) for l in CARD_LINES)
        sz = 60 if mw <= 560 else 60 * 560 / mw
        f = font(FONT_HAND, sz)
        for i, l in enumerate(CARD_LINES):
            draw_text(c, l, 0, -130 + i * sz * 1.35, f, '#22306a', 'center')
        heart(c, 0, 175, 38, '#e0606a')
        c.restore()
        for s in (-1, 1):
            c.drawCircle(540 + s * 300, 940, 34, fillp(CAST['cass']['skin']))
            c.drawCircle(540 + s * 300, 940, 34, strokep(INK, 6))
    # Sallie's voice: small warm inset with her speaking
    ia = ease_out(ramp(lt, 0.0, 0.3)) * (1 - ramp(lt, dur - 0.25, dur))
    if ia > 0:
        ix, iy, ir = 190, 330, 135
        c.save()
        clip = oval(ix, iy, ir, ir)
        c.saveLayerAlpha(skia.Rect.MakeXYWH(ix - ir - 20, iy - ir - 20, ir * 2 + 40, ir * 2 + 40), int(255 * ia))
        c.save()
        c.clipPath(clip, doAntiAlias=True)
        c.drawPaint(fillp(None, 1, shader=lin(0, iy - ir, 0, iy + ir, ['#f6dcc0', '#e8b88a'])))
        glow(c, ix + 40, iy - 40, 160, '#fff6d0', 0.5)
        person(c, 'sallie', ix, iy + 300, 420, T, facing=0.2, expr='happy', legs='none', shadow=False,
               lhand=(-14, -32), rhand=(16, -36))
        c.restore()
        c.drawPath(clip, strokep('#ffffff', 8))
        c.drawPath(clip, strokep(INK, 3))
        c.restore()
        c.restore()
    K.vvignette(c, 0.3)


def sh_loop(c, lt, dur, T):
    u = ease_io(clamp(lt / (dur - 0.25)))
    end = vcam(0, 1, CAM0[0], CAM0[1], 'io', 0.6, 1)
    cam = VCam(lerp(540, end.cx, u), lerp(1000, end.cy, u), lerp(1.6, end.z, u))
    living_room(c, cam, T, 0.0)
    with vlayer(c, cam, 1.0):
        person(c, 'cass', 680, 1420, 700, T, facing=-0.35, expr='smile', lhand=(-15, -31), rhand=(15, -31), gest=None)
        door_leaf(c, 0.0)
        standing_card(c, 370, 1062, 0.55)
    K.vvignette(c, 0.4)


SHOTS = [
    (0.0, 4.45, sh_storm), (4.45, 8.42, sh_barn), (8.42, 9.72, sh_help), (9.72, 12.5, sh_quad_down), (12.5, 16.72, sh_found),
    (16.72, 19.72, sh_kneel), (19.72, 23.45, sh_rope), (23.45, 24.75, sh_nosignal), (24.75, 27.05, sh_race_home),
    (27.05, 32.2, sh_rescue), (32.2, 35.1, sh_free), (35.1, 36.4, sh_sallie_writes), (36.4, 37.45, sh_envelope),
    (37.45, 41.75, sh_card), (41.75, 999, sh_loop),
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
    draw_hook(c, T)
    K.draw_caption(c, V.caps, T, COLORS)


# ------------------------------------------------------------------ audio
def sfx(n):
    from scipy.signal import lfilter, butter
    SR = K.SR
    rng = np.random.default_rng(23)
    fx = np.zeros(n)
    t_ = lambda d: np.arange(int(d * SR)) / SR

    def lp(x, fc):
        a = np.exp(-2 * np.pi * fc / SR)
        return lfilter([1 - a], [1, -a], lfilter([1 - a], [1, -a], x))

    def bp(x, lo, hi):
        b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band')
        return lfilter(b, a, x)

    def fade(x, fi=0.3, fo=0.3):
        x = x.copy()
        a, b = int(fi * SR), int(fo * SR)
        if a:
            x[:a] *= np.linspace(0, 1, a)
        if b:
            x[-b:] *= np.linspace(1, 0, b)
        return x

    def crowd_groan(d=2.6):
        t = t_(d)
        out = np.zeros(len(t))
        for _ in range(40):
            f0 = rng.uniform(120, 300)
            glide = f0 * (1 - 0.22 * np.clip(t / d, 0, 1)) * (1 + 0.01 * np.sin(2 * np.pi * rng.uniform(4, 7) * t))
            ph = 2 * np.pi * np.cumsum(glide) / SR + rng.uniform(0, 6)
            v = np.sign(np.sin(ph)) * 0.3 + np.sin(ph)
            out += v * rng.uniform(0.5, 1.0)
        out = bp(out, 350, 1300) + 0.6 * bp(rng.standard_normal(len(t)), 300, 2500)
        env = np.clip(t / 0.08, 0, 1) * np.exp(-np.clip(t - 0.4, 0, None) * 1.3)
        return out * env / np.abs(out).max() * 0.35

    def crowd_bed(d):
        t = t_(d)
        x = bp(rng.standard_normal(len(t)), 300, 2200) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t))
        return x / np.abs(x).max() * 0.06

    def slam():
        t = t_(0.6)
        return lp(rng.standard_normal(len(t)), 700) * np.exp(-t * 16) * 1.4 + np.sin(2 * np.pi * 62 * t) * np.exp(-t * 12) * 0.8

    def engine(d, rpm0=38, rpm1=46):
        t = t_(d)
        f = np.linspace(rpm0, rpm1, len(t)) * (1 + 0.06 * np.sin(2 * np.pi * 1.7 * t))
        ph = 2 * np.pi * np.cumsum(f) / SR
        saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
        x = lp(saw, 900) * (1 + 0.4 * lp(rng.standard_normal(len(t)), 30)) + 0.3 * lp(rng.standard_normal(len(t)), 500)
        return x / np.abs(x).max() * 0.3

    def squelch(big=False):
        d = 0.45 if big else 0.28
        t = t_(d)
        f = (380 if big else 300) * np.exp(-t * 9) + 70
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph) * np.exp(-t * (7 if big else 11)) + 0.5 * lp(rng.standard_normal(len(t)), 600) * np.exp(-t * 14)
        return s * (0.45 if big else 0.3)

    def siren(d):
        t = t_(d)
        f = np.where((t % 1.4) < 0.7, 640, 840).astype(float)
        f = lp(f, 20)
        ph = 2 * np.pi * np.cumsum(f) / SR
        return lp(np.sin(ph) + 0.3 * np.sin(2 * ph), 1800) * 0.035

    def rotor(d):
        t = t_(d)
        thump = (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t)) ** 3
        x = lp(rng.standard_normal(len(t)), 260) * thump * 2.0 + lp(rng.standard_normal(len(t)), 1500) * 0.15
        return x / np.abs(x).max() * 0.12

    def rustle(d=0.5):
        t = t_(d)
        x = bp(rng.standard_normal(len(t)), 1500, 7000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 7 * t)))
        return fade(x, 0.03, 0.15) * 0.10

    def wind(d):
        t = t_(d)
        x = lp(rng.standard_normal(len(t)), 300) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.15 * t))
        return x / np.abs(x).max() * 0.05

    K.place(fx, crowd_groan(), -0.15, 1.0)
    K.place(fx, fade(crowd_bed(4.3), 0.0, 0.6), 0.0, 1.0)
    K.place(fx, slam(), 4.18, 0.9)
    K.place(fx, fade(wind(23.0), 0.6, 1.0), 4.4, 1.0)
    K.place(fx, fade(engine(2.9, 40, 48), 0.15, 0.3), 9.65, 1.0)
    K.place(fx, fade(engine(1.4, 44, 30), 0.0, 0.5), 12.5, 0.8)
    K.place(fx, squelch(), 15.2, 0.6)
    for t0 in (20.2, 20.95, 21.7, 22.45):
        K.place(fx, squelch(), t0, 0.8)
    K.place(fx, fade(engine(2.4, 44, 54), 0.15, 0.4), 24.7, 1.0)
    K.place(fx, fade(siren(5.4), 0.8, 1.2), 26.9, 1.0)
    K.place(fx, fade(rotor(8.4), 0.8, 1.6), 27.0, 1.0)
    K.place(fx, squelch(True), 32.45, 0.8)
    K.place(fx, squelch(True), 33.3, 0.9)
    K.place(fx, rustle(0.7), 35.4, 1.0)
    K.place(fx, rustle(0.5), 36.55, 1.2)
    K.place(fx, rustle(0.35), 37.45, 1.0)
    K.place(fx, fade(crowd_bed(3.6), 1.2, 1.0), 41.8, 0.6)
    return fx


def build_audio():
    n = int(round(TOTAL * K.SR))
    voice = np.zeros(n)
    voice[:min(n, len(V.x))] = V.x[:n]
    x = K.load_track(MUSIC)
    B = 10 / 3
    # suspense (track 16-20 bars, played twice) under lines 1-6, lift for line 7, resolve under 8-10
    segs = [(16 * B, 20 * B), (16 * B, 20 * B), (20 * B, 23 * B), (40 * B, None)]
    mus, spl = K.fit_music(x, segs, n, start=-1.0, xf=1.5, fade_out=1.0)
    st = K.mix(voice, sfx(n), mus, os.path.join(WORK, 'mix.wav'), target=-14.0, bed=-24.0, tp=-3.0)
    print('music splices (video s, track s):', spl)
    print(st)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'audio':
        build_audio()
    elif mode == 'caps':
        print('total', TOTAL, 'nf', NF)
        for cp in V.caps:
            print('%6.2f %6.2f %-8s %s' % (cp['start'], cp['end'], cp['speaker'], cp['text']))
    elif mode == 'still':
        ps = K.stills(frame, [float(t) for t in sys.argv[2:]], os.path.join(WORK, 'frames'))
        K.contact(ps, os.path.join(WORK, 'contact_%s.png' % sys.argv[2]))
        print('\n'.join(ps))
    elif mode == 'video':
        K.render(frame, NF, os.path.join(WORK, 'mix.wav'), OUT_MP4, workers=2, tmpdir=WORK)
        print('rendered', OUT_MP4)
