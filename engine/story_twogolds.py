"""Short: "Two Golds" (2026-11-two-golds). Tokyo 2020 men's high jump: Barshim & Tamberi share gold.
Story-specific sets, cast and shots on top of shortkit + rig.
python3 story_twogolds.py audio | still t1 t2 ... | video | caps
No logos, rings, flags, scoreboards, numbers or prop text anywhere. Plain colours only; the cast is plain white.
"""
import os, sys, math, json, subprocess
import numpy as np
import skia
from gfx import *
import rig
from rig import draw_person, gesture
import shortkit as K
from shortkit import VCam, vlayer, vcam, VW, VH
from sets import glow, smooth_path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY = os.path.join(REPO, 'stories', '2026-11-two-golds')
AUD = os.path.join(STORY, 'vo')
MUSIC = os.path.join(REPO, 'assets', 'music_warm_folk.mp3')
OUT_MP4 = os.path.join(REPO, 'videos', '2026-11-two-golds-short.mp4')
WORK = os.environ.get('OSA_WORK', '/tmp/claude-0/-home-claude-one-small-act/020fac1c-f99a-5d5e-ab00-3a9a91c65777/scratchpad/twogolds/work')
os.makedirs(WORK, exist_ok=True)


def _fixed_timing():
    """timing.json was written for a 44.07 s track but voiceover_full.wav is 43.65 s (uniformly ~0.95% shorter:
    speech onsets measured in the wav match timing x 0.9905). Rescale so captions and mouths sit on the real speech."""
    src = os.path.join(STORY, 'timing.json')
    tm = json.load(open(src))
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                os.path.join(AUD, 'voiceover_full.wav')], capture_output=True, text=True).stdout)
    k = dur / tm['total_duration']
    for ln in tm['lines']:
        ln['start'] = round(ln['start'] * k, 3)
        ln['end'] = round(ln['end'] * k, 3)
    tm['total_duration'] = round(dur, 3)
    out = os.path.join(WORK, 'timing_fixed.json')
    json.dump(tm, open(out, 'w'), indent=1)
    return out


V = K.Voice(os.path.join(AUD, 'voiceover_full.wav'), _fixed_timing(), tail=0.4)
TOTAL, NF = V.total, V.nf
COLORS = {'NARRATOR': '#ffffff', 'BARSHIM': '#ffd6dc', 'TAMBERI': '#d6e8ff'}
HOOK = ('ONE ', 'GOLD.', 'TWO FRIENDS.')

# ------------------------------------------------------------------ cast
CAST = {
    'barshim': dict(name='barshim', skin='#a8754f', hair='short', hair_col='#1a1410', beard=True, top='vest', top_col='#7a1f35',
                    trim='#f4f1ea', shorts='#7a1f35', pants='#7a1f35', shoes='#f2f2f2', hs=1.0, seed=41),
    'tamberi': dict(name='tamberi', skin='#e8b890', hair='short', hair_col='#4a3324', stubble=True, top='vest', top_col='#2f6fd0',
                    shorts='#24489a', pants='#24489a', shoes='#f2f2f2', hs=1.0, seed=42),
    'official': dict(name='official', skin='#e2b48c', hair='short', hair_col='#a2a2a2', top='cardigan', top_col='#80858d',
                     inner_col='#f2f2f2', pants='#4a4d55', shoes='#2a2a2a', hs=1.0, seed=43),
}
TAMB_FLASH = dict(CAST['tamberi'], top='tee', top_col='#3a78d4', shorts=None, pants='#5a5f6a', shoes='#e8e8e8')
SPK = {'barshim': 'BARSHIM', 'tamberi': 'TAMBERI'}

# front-view stadium world (shots 1, 2c, 3, 6, 7b, 9, 10)
GY = 1720                      # athletes' ground line (foreground)
MAT_X0, MAT_X1, MAT_TOP, MAT_BOT = 170, 910, 1200, 1330
UPX, UP_TOP, BAR_Y = (130, 950), 600, 690
H = 640                        # athlete height in the front set
HOME = {'barshim': 360, 'tamberi': 720}
CAST_X = 870                   # Tamberi's old cast, standing on the track


def person(c, who, x, y, h, T, sp=None, gest='rhand', **st):
    s = dict(sp or CAST[who])
    spk = SPK.get(who)
    if spk:
        st.setdefault('mouth', V.mouth(spk, T))
        if V.speaking(spk, T) and gest:
            gx, gy = gesture(T, s.get('seed', 0))
            hx, hy = st.get(gest, (15, -31) if gest == 'rhand' else (-15, -31))
            st[gest] = (hx + gx, hy + gy)
    draw_person(c, s, x, y, h, st, T)


# ------------------------------------------------------------------ props
def cast_boot(c, x, yg, s=1.0, rot=0.0):
    """Plain white lower-leg cast shell standing on the ground (x = centre of the shin tube, yg = ground). No writing."""
    c.save()
    c.translate(x, yg)
    c.rotate(rot)
    tube = smooth_path([(-24 * s, -128 * s), (24 * s, -128 * s), (21 * s, -40 * s), (24 * s, -14 * s), (64 * s, -12 * s),
                        (70 * s, 0), (-26 * s, 0), (-25 * s, -40 * s)], True, 0.25)
    draw(c, tube, '#f4f2ec', INK, max(2.5, 4 * s))
    c.save()
    c.clipPath(tube, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeLTRB(8 * s, -140 * s, 40 * s, 4 * s), fillp('#c9c6be', 0.55))
    for k in range(5):  # faint gauze wrap texture (no marks)
        yy = -118 * s + k * 22 * s
        c.drawLine(-26 * s, yy, 26 * s, yy + 9 * s, strokep('#dcd8cf', 2.2 * s))
    c.restore()
    draw(c, oval(0, -128 * s, 24 * s, 7 * s), '#d9d5cc', INK, max(2, 3 * s))
    draw(c, oval(0, -128 * s, 17 * s, 4.5 * s), '#8f8a80', None, 0)
    c.restore()


def leg_cast(c, x, y, h):
    """white cast over the left lower leg + foot of a standing rig figure at (x, y, h)"""
    u = h / 90.0
    p = poly([(x - 5.7 * u, y - 13 * u), (x - 6.4 * u, y - 2 * u)], False)
    c.drawPath(p, strokep(INK, 8.2 * u + 3))
    c.drawPath(p, strokep('#f4f2ec', 8.2 * u))
    draw(c, oval(x - 4.6 * u, y - 1.6 * u, 6.2 * u, 3.0 * u), '#f4f2ec', INK, max(2, u * 0.8))
    c.drawLine(x - 8.5 * u, y - 12 * u, x - 9 * u, y - 4 * u, strokep('#cfcbc2', 1.4 * u))


def crutch(c, x, y, h, s):
    u = h / 90.0
    tx, ty = x + s * 17 * u, y - 50 * u
    bx, by = x + s * 20.5 * u, y
    c.drawLine(tx, ty, bx, by, strokep(INK, 2.6 * u + 3))
    c.drawLine(tx, ty, bx, by, strokep('#a7adb5', 2.6 * u))
    draw(c, rrect(tx - 4 * u, ty - 1.6 * u, 8 * u, 3.2 * u, 1.6 * u), '#5a5f68', INK, 2.5)
    gx, gy = lerp(tx, bx, 0.34), lerp(ty, by, 0.34)
    c.drawLine(gx - 3.2 * u, gy, gx + 3.2 * u, gy, strokep(INK, 2.2 * u + 3))
    c.drawLine(gx - 3.2 * u, gy, gx + 3.2 * u, gy, strokep('#5a5f68', 2.2 * u))
    draw(c, oval(bx, by - 1 * u, 2 * u, 1.2 * u), '#3a3a3a', INK, 2)


def bar_line(c, x0, y0, x1, y1, w=14):
    c.drawLine(x0, y0, x1, y1, strokep(INK, w + 6))
    c.drawLine(x0, y0, x1, y1, strokep('#f6f4ee', w))
    c.drawLine(x0, y0 - w * 0.18, x1, y1 - w * 0.18, strokep('#ffffff', w * 0.25, 0.8))


# ------------------------------------------------------------------ stadium pieces
SEAT_COLS = ['#6b4e3d', '#3e5a4a', '#7d6a52', '#4a4a5e', '#5d4a5a', '#56604a']


def night_sky(c, top='#04071a', bot='#1b2550'):
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp(None, 1, shader=lin(0, 0, 0, 1100, [top, bot])))


def floodlight(c, x, y, T, s=1.0, a=1.0, flare=0.0):
    fl = 1 + 0.03 * math.sin(T * 13 + x)
    glow(c, x, y, 420 * s * (1 + 0.5 * flare), '#dfe8ff', (0.38 + 0.3 * flare) * a * fl)
    c.drawLine(x, y + 40 * s, x + 10 * s, y + 900 * s, strokep('#0c1024', 26 * s))
    draw(c, rrect(x - 100 * s, y - 50 * s, 200 * s, 100 * s, 8 * s), '#20263c', INK, 3)
    for i in range(5):
        for j in range(2):
            cx, cy = x - 76 * s + i * 38 * s, y - 22 * s + j * 44 * s
            c.drawCircle(cx, cy, 15 * s, fillp('#ffffff', a))
            c.drawCircle(cx, cy, 24 * s, fillp('#eaf0ff', 0.35 * a))
    if flare > 0:
        c.drawRect(skia.Rect.MakeXYWH(x - 520 * s, y - 4 * s, 1040 * s, 8 * s), fillp('#cfe0ff', 0.35 * flare, blur=6))
        for k in range(4):
            ang = math.radians(25 + k * 40 + T * 6)
            c.drawLine(x, y, x + math.cos(ang) * 380 * s, y + math.sin(ang) * 380 * s, strokep('#eaf2ff', 5 * s, 0.18 * flare, blur=3))


def stands(c, y0, y1, T, x0=-500, x1=1600, a=1.0):
    """empty tiers with a muted mosaic of seat colours (no text, no logos)"""
    c.drawRect(skia.Rect.MakeLTRB(x0, y0 - 40, x1, y1), fillp('#151a33'))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0 - 60, x1, y0 - 30), fillp('#0b0e1e'))
    for k in range(int((x1 - x0) / 90)):
        c.drawCircle(x0 + 45 + k * 90, y0 - 45, 4, fillp('#fff2c8', 0.8 * a))
    rows = int((y1 - y0) / 26)
    for r in range(rows):
        yy = y0 + r * 26
        c.drawRect(skia.Rect.MakeLTRB(x0, yy + 18, x1, yy + 22), fillp('#0d1126', 0.9))
        for k in range(int((x1 - x0) / 22)):
            col = SEAT_COLS[int(hash01(k * 7 + r * 131, 5) * len(SEAT_COLS))]
            c.drawRect(skia.Rect.MakeXYWH(x0 + k * 22, yy + 4, 18, 13), fillp(col, 0.55 * a))
    c.drawRect(skia.Rect.MakeLTRB(x0, y1 - 30, x1, y1 + 30), fillp('#0e1228'))


def stadium_front(c, cam, T, bar='on', flare=0.0, pool=0.5, cast=True, bar_y=BAR_Y):
    night_sky(c)
    with vlayer(c, cam, 0.25):
        floodlight(c, 110, 250, T, 1.0, 1.0, flare)
        floodlight(c, 980, 300, T, 0.9, 1.0, flare)
    with vlayer(c, cam, 0.5):
        stands(c, 560, 1090, T)
    with vlayer(c, cam, 0.75):
        c.drawRect(skia.Rect.MakeLTRB(-600, 1070, 1700, 2600), fillp(None, 1, shader=lin(0, 1070, 0, 1400, ['#5a2a22', '#7c3828'])))
        # light beams falling on the apron
        for bx, s2 in ((110, 1), (980, -1)):
            c.drawPath(poly([(bx - 60, 250), (bx + 60, 250), (540 + s2 * 380, 1500), (540 - s2 * 120, 1500)]),
                       fillp('#dfe8ff', 0.045 + 0.04 * flare))
    with vlayer(c, cam, 1.0):
        # near apron / track
        c.drawRect(skia.Rect.MakeLTRB(-600, MAT_BOT - 20, 1700, 2600), fillp(None, 1, shader=lin(0, MAT_BOT, 0, 1950, ['#8e3e2b', '#a84a33'])))
        c.drawPath(smooth_path([(-600, 1560), (300, 1520), (900, 1515), (1700, 1540)], False), strokep('#f2ece2', 7, 0.45))
        c.drawPath(smooth_path([(-600, 1900), (300, 1850), (900, 1845), (1700, 1880)], False), strokep('#f2ece2', 9, 0.45))
        glow(c, 540, 1600, 620, '#ffe8c0', 0.18 * pool + 0.1 * flare)
        # landing mat (plain blue)
        draw(c, rrect(MAT_X0 + 14, MAT_TOP - 30, MAT_X1 - MAT_X0 - 28, 40, 10), '#4a80cc', INK, 4)
        draw(c, rect(MAT_X0, MAT_TOP, MAT_X1 - MAT_X0, MAT_BOT - MAT_TOP), '#2d5fa8', INK, 4)
        for k in range(1, 4):
            xx = MAT_X0 + k * (MAT_X1 - MAT_X0) / 4
            c.drawLine(xx, MAT_TOP + 6, xx, MAT_BOT - 6, strokep('#244e8c', 4))
        c.drawRect(skia.Rect.MakeLTRB(MAT_X0 + 3, MAT_BOT - 26, MAT_X1 - 3, MAT_BOT - 3), fillp('#1f4478'))
        c.drawOval(skia.Rect.MakeLTRB(MAT_X0 - 20, MAT_BOT - 8, MAT_X1 + 20, MAT_BOT + 18), fillp('#000000', 0.25))
        # uprights
        for ux in UPX:
            draw(c, rrect(ux - 40, MAT_BOT - 14, 80, 22, 6), '#3a3f4a', INK, 3)
            draw(c, rect(ux - 9, UP_TOP, 18, MAT_BOT - UP_TOP - 8), '#6a717e', INK, 3)
            c.drawLine(ux - 3, UP_TOP + 10, ux - 3, MAT_BOT - 20, strokep('#9aa1ad', 3))
            draw(c, rect(ux - 14, bar_y - 6, 28, 22), '#3a3f4a', INK, 3)
            draw(c, oval(ux, UP_TOP, 11, 6), '#3a3f4a', INK, 3)
        if bar == 'on':
            bar_line(c, UPX[0] + 12, bar_y, UPX[1] - 12, bar_y, 15)
            glow(c, 540, bar_y, 160, '#ffffff', 0.10 + 0.1 * flare)
        elif bar == 'fallen':
            bar_line(c, 230, 1352, 860, 1372, 15)
        if cast:
            cast_boot(c, CAST_X, GY + 4, 1.0)


def closeup_bg(c, cam, T, pan=0.0, streak=0.0, warm=0.0, flare=0.0):
    """defocused stadium behind a close-up: big soft floodlight bokeh, blurred stands band, warm apron at the bottom"""
    night_sky(c, '#060a20', '#1f2a5a')
    with vlayer(c, cam, 0.3):
        c.save()
        c.translate(pan, 0)
        c.drawRect(skia.Rect.MakeLTRB(-3000, 820, 4000, 1250), fillp('#262b4a', 1, blur=18))
        for k in range(46):
            x = -2400 + k * 130
            col = SEAT_COLS[k % len(SEAT_COLS)]
            c.drawCircle(x, 980 + 90 * math.sin(k * 1.7), 60, fillp(col, 0.35, blur=20))
        c.drawRect(skia.Rect.MakeLTRB(-3000, 1250, 4000, 2600), fillp(None, 1, shader=lin(0, 1250, 0, 1900, ['#5a2a22', '#8e3e2b'])))
        for k in range(14):
            x = -2200 + k * 420 + 120 * hash01(k, 3)
            y = 160 + 300 * hash01(k, 4)
            r = 70 + 70 * hash01(k, 5)
            fl = 0.8 + 0.2 * math.sin(T * 3 + k)
            c.drawCircle(x, y, r * (1 + 0.4 * flare), fillp('#eef2ff', (0.30 + 0.25 * flare) * fl, blur=8))
            c.drawCircle(x, y, r * 2.4, fillp('#9fb6ff', 0.10 + 0.08 * flare, blur=30))
        c.restore()
    if streak > 0:
        for k in range(18):
            y = 120 + k * 95
            x = (hash01(k, 9) * 1400 - 160)
            c.drawRect(skia.Rect.MakeXYWH(x - 300, y, 700, 10 + 16 * hash01(k, 8)), fillp('#dfe6ff', 0.16 * streak, blur=6))
    if warm > 0:
        c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#ffb070', 0.06 * warm))


# ------------------------------------------------------------------ hook text
def draw_hook(c, T):
    if T >= 2.2:
        return
    a = 1 - ramp(T, 1.85, 2.2)
    sz = 100
    while True:
        f = font(FONT_SUB, sz)
        w1 = f.measureText(HOOK[0] + HOOK[1])
        w2 = f.measureText(HOOK[2])
        if max(w1, w2) <= 720 or sz <= 50:
            break
        sz -= 2
    cx, cy = 470, 330
    pulse = 1 + 0.02 * math.sin(T * 7)
    c.save()
    c.translate(cx, cy)
    c.scale(pulse, pulse)
    W = max(w1, w2) + 64
    draw(c, rrect(-W / 2, -sz * 1.22, W, sz * 2.44, 30), '#000000', None, 0, fa=0.42 * a)
    wa = f.measureText(HOOK[0])
    x0 = -w1 / 2
    draw_text(c, HOOK[0], x0, -sz * 0.12, f, '#ffffff', 'left', '#0b0b0b', 11, a, a)
    draw_text(c, HOOK[1], x0 + wa, -sz * 0.12, f, '#ffd23a', 'left', '#0b0b0b', 11, a, a)
    draw_text(c, HOOK[2], 0, sz * 0.98, f, '#ffffff', 'center', '#0b0b0b', 11, a, a)
    c.restore()


# ------------------------------------------------------------------ shared poses
def home_pose(c, T, who):
    """both athletes at the mat edge looking up at the bar (shot 1 + the loop end in shot 10)"""
    if who == 'barshim':
        person(c, 'barshim', HOME['barshim'], GY, H, T, facing=0.35, tilt=-7, look=1.5, expr='neutral',
               lhand=(-15, -31), rhand=(14, -30), gest=None)
    else:
        person(c, 'tamberi', HOME['tamberi'], GY, H, T, facing=-0.35, tilt=7, look=1.5, expr='neutral',
               lhand=(-13, -27), rhand=(13, -27), gest=None)


CAM1 = ((540, 1010, 1.0), (540, 985, 1.08))
SHOT1_DUR = 7.0


def cam_shot1(lt):
    return vcam(lt, SHOT1_DUR, CAM1[0], CAM1[1], 'out', 0.4, 1)


# ------------------------------------------------------------------ shots  fn(c, lt, dur, T)
def sh_open(c, lt, dur, T):
    cam = cam_shot1(lt)
    stadium_front(c, cam, T)
    with vlayer(c, cam, 1.0):
        home_pose(c, T, 'barshim')
        home_pose(c, T, 'tamberi')
    K.vvignette(c, 0.45)


# --- line 2: side view misses
SG = 1520                         # ground in the side view
S_UP, S_UP2 = 470, 640            # near / far upright x
S_MAT = (500, 1100, 1330)         # mat x0, x1, top
SH = 400


def side_set(c, cam, T):
    night_sky(c)
    with vlayer(c, cam, 0.25):
        floodlight(c, 160, 260, T, 0.9)
        floodlight(c, 940, 220, T, 0.8)
    with vlayer(c, cam, 0.5):
        stands(c, 640, 1180, T)
    with vlayer(c, cam, 0.75):
        c.drawRect(skia.Rect.MakeLTRB(-800, 1160, 1900, 2600), fillp(None, 1, shader=lin(0, 1160, 0, 1500, ['#5a2a22', '#7c3828'])))
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-800, SG - 10, 1900, 2600), fillp(None, 1, shader=lin(0, SG, 0, 1950, ['#8e3e2b', '#a84a33'])))
        c.drawLine(-800, SG + 110, 1900, SG + 110, strokep('#f2ece2', 7, 0.4))
        glow(c, 520, 1400, 600, '#ffe8c0', 0.12)
        # far upright (behind the mat)
        draw(c, rect(S_UP2 - 6, 880, 12, 1430 - 880), '#4f5562', INK, 2.5)
        # mat
        x0, x1, mt = S_MAT
        draw(c, poly([(x0 + 10, mt), (x1, mt), (x1 + 30, mt - 26), (x0 + 40, mt - 26)]), '#4a80cc', INK, 4)
        draw(c, rect(x0, mt, x1 - x0, SG - mt), '#2d5fa8', INK, 4)
        for k in range(1, 4):
            xx = x0 + k * (x1 - x0) / 4
            c.drawLine(xx, mt + 6, xx, SG - 6, strokep('#244e8c', 4))
        c.drawRect(skia.Rect.MakeLTRB(x0 + 3, SG - 28, x1 - 3, SG - 3), fillp('#1f4478'))
        # near upright
        draw(c, rrect(S_UP - 40, SG - 14, 80, 22, 6), '#3a3f4a', INK, 3)
        draw(c, rect(S_UP - 9, 940, 18, SG - 940 - 8), '#6a717e', INK, 3)
        c.drawLine(S_UP - 3, 950, S_UP - 3, SG - 20, strokep('#9aa1ad', 3))
        draw(c, oval(S_UP, 940, 11, 6), '#3a3f4a', INK, 3)


def bar_state(tj, t_hit, by):
    """returns near/far bar end positions (x0,y0,x1,y1) after a knock at t_hit"""
    nx, ny, fx_, fy_ = S_UP + 8, by, S_UP2 - 8, by - 70
    if tj <= t_hit:
        return nx, ny, fx_, fy_, 0
    t = tj - t_hit
    g = 2600

    def fall(y0, ylimit, t, x0, dx):
        y = y0 + 0.5 * g * t * t
        land = math.sqrt(2 * (ylimit - y0) / g)
        if t >= land:
            tb = t - land
            y = ylimit - max(0, 60 * math.sin(min(math.pi, tb * 9))) * math.exp(-tb * 3)
        return x0 + dx * clamp(t / max(land, 1e-3)), y
    nx2, ny2 = fall(ny, 1318, t, nx, 80)
    fx2, fy2 = fall(fy_, 1290, max(0, t - 0.07), fx_, 60)
    return nx2, ny2, fx2, fy2, 1


J_RUN, J_FLY = 0.55, 0.70


def jumper_pose(tj, by):
    """Fosbury flop seen from the side: run in, take off, arc back-first over the bar, land on the mat.
    returns dict(fx, fy, rot, legs, phase, lhand, rhand, expr)"""
    u = SH / 90.0
    if tj < J_RUN:
        p = clamp(tj / J_RUN)
        fx = lerp(-160, 300, p ** 1.25)
        return dict(fx=fx, fy=SG, rot=-6, legs='walk', phase=tj * 22, lhand=(-18, -40), rhand=(18, -24), expr='determined')
    C0 = (300 + 45 * u * math.sin(math.radians(-6)), SG - 45 * u * math.cos(math.radians(-6)))
    C1 = (720, S_MAT[2] - 12 - 15 * u)
    A = 322 + (1010 - by)
    if tj < J_RUN + J_FLY:
        p = (tj - J_RUN) / J_FLY
        cx = lerp(C0[0], C1[0], p)
        cy = lerp(C0[1], C1[1], p) - A * 4 * p * (1 - p)
        rot = -6 + 101 * ease_io(clamp(p / 0.5)) + (8 * math.sin(math.pi * (p - 0.5) / 0.5) if p > 0.5 else 0)
        legs = 'jump'
        hands = ((-14, -30), (14, -30))
        expr = 'strain'
    else:
        tb = tj - J_RUN - J_FLY
        cx, cy = C1[0] + 10 * clamp(tb / 0.2), C1[1] - 26 * abs(math.sin(min(math.pi, tb * 10))) * math.exp(-tb * 5)
        rot = 95
        legs = 'stand'
        hands = ((-18, -40), (18, -40))
        expr = 'concerned'
    r = math.radians(rot)
    fx = cx - 45 * u * math.sin(r)
    fy = cy + 45 * u * math.cos(r)
    return dict(fx=fx, fy=fy, rot=rot, legs=legs, phase=0, lhand=hands[0], rhand=hands[1], expr=expr)


T_JUMP0 = 0.30                    # jump starts this long into each attempt shot
T_HIT = J_RUN + 0.37 * J_FLY      # body meets the bar


def sh_attempt(c, lt, dur, T, who, mirror, seed):
    cam = vcam(lt, dur, (590, 1200, 1.26), (620, 1185, 1.34), 'lin', 0.5, seed)
    by = lerp(1030, 1010, ease_out(ramp(lt, 0.0, 0.28))) if who == 'barshim' else 1010
    tj = lt - T_JUMP0
    ends = bar_state(tj, T_HIT, by)
    c.save()
    if mirror:
        c.translate(VW, 0)
        c.scale(-1, 1)
    side_set(c, cam, T)
    with vlayer(c, cam, 1.0):
        draw(c, rect(S_UP2 - 10, by - 76, 20, 16), '#3a3f4a', INK, 2.5)
        ps = jumper_pose(max(0.0, tj), by)
        nx, ny, fx_, fy_, fallen = ends
        if not fallen:
            bar_line(c, fx_, fy_, nx, ny, 13)
            draw(c, rect(S_UP - 14, by - 6, 28, 20), '#3a3f4a', INK, 3)
        else:
            draw(c, rect(S_UP - 14, by - 6, 28, 20), '#3a3f4a', INK, 3)
            bar_line(c, fx_, fy_, nx, ny, 13)
        lying = tj > J_RUN + J_FLY
        if fallen and lying:  # bar lies on the mat under/in front of the athlete
            pass
        person(c, who, ps['fx'], ps['fy'], SH, T, facing=0.55, rot=ps['rot'], legs=ps['legs'], phase=ps['phase'],
               lhand=ps['lhand'], rhand=ps['rhand'], expr=ps['expr'], shadow=(tj < J_RUN), gest=None,
               look=(-1.2 if lying else 0))
        if fallen:
            if tj - T_HIT < 0.18:  # impact sparks
                k = (tj - T_HIT) / 0.18
                for i in range(6):
                    a = i * 1.05
                    c.drawLine(S_UP + 10 + math.cos(a) * 30 * k, by + math.sin(a) * 30 * k,
                               S_UP + 10 + math.cos(a) * 70 * k, by + math.sin(a) * 70 * k, strokep('#ffffff', 5, 1 - k))
    c.restore()
    K.vvignette(c, 0.5)


def sh_miss_b(c, lt, dur, T):
    sh_attempt(c, lt, dur, T, 'barshim', False, 2)


def sh_miss_t(c, lt, dur, T):
    sh_attempt(c, lt, dur, T, 'tamberi', True, 3)


def sh_sit(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 1110, 1.2), (540, 1095, 1.28), 'lin', 0.4, 4)
    stadium_front(c, cam, T, bar='fallen', cast=False)
    with vlayer(c, cam, 1.0):
        h = 480
        person(c, 'barshim', 400, MAT_TOP + 24 * h / 90, h, T, legs='sit', facing=0.25, expr='sad', look=-1.6, tilt=4,
               lhand=(-10, -27), rhand=(14, -26), gest=None, shadow=False)
        person(c, 'tamberi', 690, MAT_TOP + 24 * h / 90, h, T, legs='sit', facing=-0.25, expr='sad', look=-1.6, tilt=-5,
               lhand=(-15, -27), rhand=(12, -27), gest=None, shadow=False)
    K.vvignette(c, 0.5)


OFF_H = 620


def sh_official(c, lt, dur, T):
    cam = vcam(lt, dur, (400, 1060, 1.0), (420, 1045, 1.05), 'io', 0.4, 5)
    stadium_front(c, cam, T)
    with vlayer(c, cam, 1.0):
        w = ease_out(ramp(lt, 0.0, 1.6))
        ox = lerp(-280, 30, w)
        walking = w < 0.999
        if lt < 1.8:
            rh, lh = (12, -32), (-12, -32)
        elif lt < 2.7:
            k = ease_out(ramp(lt, 1.8, 2.1))
            rh, lh = (lerp(12, 16, k), lerp(-32, -76, k)), (-12, -32)
        else:
            k = ease_io(ramp(lt, 2.7, 3.0))
            rh = (lerp(16, 11, k), lerp(-76, -46, k) + 2 * math.sin(T * 3))
            lh = (lerp(-12, -20, k), lerp(-32, -42, k))
        person(c, 'official', ox, GY, OFF_H, T, sp=CAST['official'], facing=0.45, legs='walk' if walking else 'stand',
               phase=T * 8, expr='neutral', lhand=lh, rhand=rh, gest=None)
        look_each = lt > 3.2
        person(c, 'barshim', HOME['barshim'], GY, H, T, facing=0.5 if look_each else -0.4, expr='thinking' if look_each else 'neutral',
               lhand=(-15, -31), rhand=(14, -30), gest=None)
        person(c, 'tamberi', HOME['tamberi'], GY, H, T, facing=-0.55, expr='concerned' if look_each else 'neutral',
               tilt=-4 if look_each else 0, lhand=(-13, -27), rhand=(13, -27), gest=None)
    K.vvignette(c, 0.45)


def sh_ask(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 960, 1.0), (520, 935, 1.07), 'io', 0.5, 6)
    closeup_bg(c, cam, T, pan=-40 * lt)
    with vlayer(c, cam, 1.0):
        person(c, 'barshim', 450, 2080, 1300, T, facing=0.35, tilt=8, expr='tender', lhand=(-15, -31), rhand=(12, -40),
               gest='rhand', shadow=False)
        # out-of-focus grey shoulder of the official at the right edge (intentional over-the-shoulder framing)
        c.drawCircle(1120, 1560, 300, fillp('#5f646c', 0.95, blur=22))
        c.drawCircle(1180, 1060, 190, fillp('#c9a283', 0.0, blur=30))
    K.vvignette(c, 0.5)


def defocus(c, fn, r=7):
    p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(r, r))
    c.saveLayer(None, p)
    fn()
    c.restore()


def sh_nod(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 960, 1.04), (560, 950, 1.1), 'io', 0.4, 7)
    closeup_bg(c, cam, T, pan=30 * lt)
    with vlayer(c, cam, 0.85):
        def tb():
            wide = lt > 0.6
            person(c, 'tamberi', 220, 1540, 600, T, facing=0.35, expr='surprised' if wide else 'concerned',
                   lhand=(-13, -27), rhand=(13, -27), gest=None, shadow=False)
        defocus(c, tb, 5)
    with vlayer(c, cam, 1.0):
        nod = math.sin(math.pi * clamp((lt - 0.25) / 1.1)) ** 2
        person(c, 'official', 640, 1980, 1250, T, sp=CAST['official'], facing=-0.3, expr='smile' if lt > 0.9 else 'neutral',
               nod=nod, lhand=(-15, -31), rhand=(15, -31), gest=None, shadow=False)
    K.vvignette(c, 0.5)


def sh_joy(c, lt, dur, T):
    # hand-slap -> Tamberi leaps into Barshim's arms -> whirling spin -> Tamberi flops onto the track, rolling and screaming
    u = H / 90.0
    BX, TX0 = 400, 680
    if lt < 1.15 or lt >= 2.35:
        camA = vcam(lt, dur, (540, 1080, 1.1), (545, 1070, 1.14), 'lin', 0.5, 8)
        camB = VCam(680, 1440, 1.15)
        k = ease_io(ramp(lt, 2.35, 2.8))
        cam = VCam(lerp(camA.cx, camB.cx, k), lerp(camA.cy, camB.cy, k), lerp(camA.z, camB.z, k))
        stadium_front(c, cam, T, flare=0.4 * k, pool=0.8)
        with vlayer(c, cam, 1.0):
            if lt < 0.6:
                s = ease_out(ramp(lt, 0.05, 0.35))
                bh = (lerp(15, 20, s), lerp(-31, -62, s))
                th = (lerp(-15, -20, s), lerp(-31, -62, s))
                person(c, 'barshim', BX, GY, H, T, facing=0.5, expr='happy', lhand=(-15, -31), rhand=bh, gest=None)
                person(c, 'tamberi', TX0, GY, H, T, facing=-0.5, expr='happy', lhand=th, rhand=(15, -31), gest=None)
                if 0.33 < lt < 0.55:
                    q = (lt - 0.33) / 0.22
                    for i in range(8):
                        a = i * math.pi / 4
                        c.drawLine(540 + math.cos(a) * 30 * (1 + q), 1280 + math.sin(a) * 30 * (1 + q),
                                   540 + math.cos(a) * 70 * (1 + q), 1280 + math.sin(a) * 70 * (1 + q), strokep('#fff6c0', 7, 1 - q))
            elif lt < 1.15:
                k2 = ease_out(ramp(lt, 0.6, 0.95))
                tx, ty = lerp(TX0, 650, k2), lerp(GY, 1578, k2)
                person(c, 'barshim', BX, GY, H, T, facing=0.5, expr='laugh', lhand=(-15, -31),
                       rhand=(lerp(20, 24, k2), lerp(-62, -44, k2)), gest=None)
                person(c, 'tamberi', tx, ty, H, T, facing=-0.4, expr='laugh', legs='jump' if k2 > 0.3 else 'stand',
                       lhand=(lerp(-20, -22, k2), lerp(-62, -33, k2)), rhand=(24, -66), gest=None, shadow=k2 < 0.3, mouth=3)
            else:
                # flop onto the track: rotate from held to lying on his back, then roll side to side, legs kicking
                f = ease_in(ramp(lt, 2.35, 2.7))
                lfx, lfy = 1080, GY - 15 * u
                roll = 10 * math.sin((lt - 2.7) * 9) if lt > 2.7 else 0
                tx, ty = lerp(650, lfx, f), lerp(1578, lfy, f)
                rot = lerp(0, -90, f) + roll
                person(c, 'barshim', BX, GY, H, T, facing=0.45, expr='laugh', lhand=(-20, -62), rhand=(20, -62), gest=None,
                       mouth=2 + int(T * 8) % 2)
                if f >= 1:
                    c.drawOval(skia.Rect.MakeLTRB(lfx - 72 * u - 40, GY - 14, lfx + 30, GY + 14), fillp('#000000', 0.28))
                person(c, 'tamberi', tx, ty, H, T, facing=0.2, expr='laugh', rot=rot, legs='walk' if f >= 1 else 'jump',
                       phase=T * 14, lhand=(-22, -68), rhand=(22, -68), gest=None, shadow=False, mouth=3 + int(T * 6) % 2)
    else:
        # spin: camera whirls around the pair (background races past, slight roll)
        s = ease_io(ramp(lt, 1.15, 2.35))
        cam = VCam(540, 1080, 1.14)
        closeup_bg(c, VCam(540, 960, 1.0), T, pan=-2600 * s, streak=math.sin(math.pi * s), warm=0.6)
        c.save()
        c.translate(540, 1300)
        c.rotate(6 * math.sin(2 * math.pi * s))
        c.translate(-540, -1300)
        with vlayer(c, cam, 1.0):
            bob = 14 * math.sin(lt * 10)
            person(c, 'barshim', BX, GY, H, T, facing=0.5, expr='laugh', lhand=(-15, -31), rhand=(24, -44), gest=None,
                   mouth=2 + int(T * 8) % 2)
            person(c, 'tamberi', 650, 1578 - bob, H, T, facing=-0.4, expr='laugh', legs='jump', lhand=(-22, -33),
                   rhand=(24, -66), gest=None, shadow=False, mouth=3)
        c.restore()
    K.vvignette(c, 0.45)


def sepia_layer(c, amt=0.6):
    S = [0.393, 0.769, 0.189, 0.349, 0.686, 0.168, 0.272, 0.534, 0.131]
    m = []
    for r in range(3):
        m += [lerp(1 if r == k else 0, S[r * 3 + k], amt) for k in range(3)] + [0, 0]
    m += [0, 0, 0, 1, 0]
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))


def flash_set(c, cam, T, gy=1700):
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp(None, 1, shader=lin(0, 0, 0, 1200, ['#a9cbe6', '#eef3f2'])))
    with vlayer(c, cam, 0.3):
        glow(c, 820, 360, 420, '#fff6d8', 0.6)
        c.drawCircle(820, 360, 70, fillp('#fffbe8'))
        for k in range(12):
            x = -300 + k * 150
            c.drawPath(smooth_path([(x - 90, 1120), (x - 50, 980 - 40 * hash01(k, 2)), (x + 40, 960 - 50 * hash01(k, 3)),
                                    (x + 90, 1120)]), fillp('#6f9a6a'))
    with vlayer(c, cam, 0.7):
        c.drawRect(skia.Rect.MakeLTRB(-600, 1100, 1700, 1240), fillp('#7fae6a'))
    with vlayer(c, cam, 1.0):
        c.drawRect(skia.Rect.MakeLTRB(-600, 1230, 1700, 2600), fillp(None, 1, shader=lin(0, 1230, 0, 1900, ['#b8664c', '#c87a5c'])))
        vx, vy = 540, 1000
        for k in range(-6, 8):
            xb = 540 + k * 360
            c.drawLine(lerp(vx, xb, 0.12), lerp(vy, 2400, 0.12), xb, 2400, strokep('#fbf4ea', 8, 0.8))


def flash_tint_over(c, a=1.0):
    c.drawRect(skia.Rect.MakeWH(VW, VH), fillp('#ffdca8', 0.14 * a))
    p = skia.Paint(AntiAlias=True)
    p.setShader(rad(VW / 2, VH / 2, math.hypot(VW / 2, VH / 2), [hexc('#fffaf0', 0), hexc('#fffaf0', 0), hexc('#fffaf0', 0.4 * a)],
                    [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(VW, VH), p)


def flash_crutches(c, lt, T):
    cam = vcam(lt, 3.6, (540, 1000, 1.0), (560, 980, 1.08), 'lin', 0.3, 9)
    flash_set(c, cam, T)
    with vlayer(c, cam, 1.0):
        h = 700
        u = h / 90.0
        x = 430 + 34 * lt + 6 * math.sin(lt * 3)
        y = 1700
        crutch(c, x, y, h, -1)
        crutch(c, x, y, h, 1)
        person(c, 'tamberi', x, y, h, T, sp=TAMB_FLASH, facing=0.15, expr='sad', look=-1.4, tilt=3,
               lhand=(-17.6, -33), rhand=(17.6, -33), gest=None)
        leg_cast(c, x, y, h)


def flash_holding(c, lt, T):
    cam = vcam(lt, 3.0, (540, 980, 1.04), (540, 960, 1.1), 'lin', 0.3, 10)
    flash_set(c, cam, T, 1600)
    with vlayer(c, cam, 1.0):
        h = 700
        u = h / 90.0
        x, y = 520, 1600
        person(c, 'tamberi', x, y, h, T, sp=TAMB_FLASH, facing=0.1, expr='tender', look=-1.6, tilt=4,
               lhand=(-9, -42), rhand=(10, -43), gest=None)
        # the plain white cast shell held across his hands (drawn in front)
        cast_boot(c, x - 20, y - 39 * u, 0.95, rot=-80)
        for s in (-1, 1):
            hx, hy = x + (-9 if s < 0 else 10) * u, y - (42 if s < 0 else 43) * u
            c.drawCircle(hx, hy, 3.0 * u, fillp(TAMB_FLASH['skin']))
            c.drawCircle(hx, hy, 3.0 * u, strokep(INK, 3))


def kneel_by_cast(c, lt, dur, T, cam=None):
    cam = cam or vcam(lt, dur, (760, 1430, 1.24), (745, 1405, 1.3), 'lin', 0.4, 11)
    stadium_front(c, cam, T, pool=0.9)
    with vlayer(c, cam, 1.0):
        person(c, 'tamberi', 740, GY, H, T, legs='kneel', facing=0.4, expr='tender', look=-1.0, tilt=6, tear=True,
               lhand=(-12, -28), rhand=(17.6, -29), gest=None)


def sh_cast(c, lt, dur, T):
    # line 7: flashback (crutches -> holding the old cast), dissolve to tonight: kneeling by the cast on the track
    t_hold, t_now = 3.25, 5.6
    if lt < t_now + 0.5:
        sepia_layer(c, 0.55)
        if lt < t_hold + 0.4:
            flash_crutches(c, lt, T)
        if lt > t_hold:
            a = ease_io(ramp(lt, t_hold, t_hold + 0.4))
            c.saveLayerAlpha(None, int(255 * a))
            flash_holding(c, lt - t_hold, T)
            c.restore()
        flash_tint_over(c)
        c.restore()
    if lt > t_now:
        a = ease_io(ramp(lt, t_now, t_now + 0.5))
        c.saveLayerAlpha(None, int(255 * a))
        kneel_by_cast(c, lt - t_now, dur - t_now, T)
        K.vvignette(c, 0.45)
        c.restore()


def sh_dream(c, lt, dur, T):
    cam = vcam(lt, dur, (540, 960, 1.0), (540, 935, 1.07), 'io', 0.5, 12)
    closeup_bg(c, cam, T, pan=-30 * lt, warm=0.5)
    with vlayer(c, cam, 1.0):
        h = 1300
        u = h / 90.0
        x, y = 500, 1880
        person(c, 'tamberi', x, y, h, T, facing=0.15, expr='tender', tears=True, tilt=-4, lhand=(-15, -31),
               rhand=(21, -38), gest='lhand', shadow=False)
        cast_boot(c, x + 23 * u, y - 30 * u, 1.4, rot=4)
        hx, hy = x + 21 * u, y - 38 * u
        c.drawCircle(hx, hy, 3.0 * u, fillp(CAST['tamberi']['skin']))
        c.drawCircle(hx, hy, 3.0 * u, strokep(INK, 5))
    K.vvignette(c, 0.5)


CAM9 = ((600, 1300, 1.3), (590, 1280, 1.36))
EMB = {'barshim': 470, 'tamberi': 700}


def embrace(c, T, k=1.0, flare=0.0):
    """B and T embracing, foreheads together (k=1), drawn in the front world"""
    u = H / 90.0
    bx, tx = EMB['barshim'], EMB['tamberi']
    # inner arms wrap around each other's backs: hidden behind the partner's torso, only the hand on the far side shows
    person(c, 'tamberi', tx, GY, H, T, facing=-0.7, tilt=-1.5, expr='happy', tear=True, lhand=None, rhand=(14, -30), gest=None)
    person(c, 'barshim', bx, GY, H, T, facing=0.7, tilt=1.5, expr='happy', tear=True, lhand=(-15, -31), rhand=None, gest=None)
    for hx, col in ((bx - 13.5 * u, CAST['tamberi']['skin']), (tx + 13.5 * u, CAST['barshim']['skin'])):
        hy = GY - 44 * u
        c.drawCircle(hx, hy, 3.0 * u, fillp(col))
        c.drawCircle(hx, hy, 3.0 * u, strokep(INK, 4))


def sh_embrace(c, lt, dur, T):
    cam = vcam(lt, dur, CAM9[0], CAM9[1], 'lin', 0.4, 13)
    flare = ease_io(ramp(lt, 1.4, 2.4)) * (0.8 + 0.2 * math.sin(T * 4))
    stadium_front(c, cam, T, flare=flare, pool=1.0)
    u = H / 90.0
    with vlayer(c, cam, 1.0):
        if lt < 1.5:
            w = ease_out(ramp(lt, 0.0, 0.7))
            bx = lerp(330, 480, w)
            up = ease_io(ramp(lt, 0.75, 1.35))
            # Tamberi: kneel -> half-up -> standing, taking Barshim's hand
            tx = lerp(740, 700, up)
            legs = 'kneel' if up < 0.35 else ('jump' if up < 0.8 else 'stand')
            ty = GY + (6 * u if legs == 'jump' else 0)
            th = (lerp(-24, -20, up), lerp(-40, -48, up)) if lt > 0.55 else (-12, -28)
            person(c, 'tamberi', tx, ty, H, T, legs=legs, facing=-0.5, expr='tender', tear=True, look=0.5 if lt > 0.5 else -1.0,
                   lhand=th, rhand=(17.6, -29) if up < 0.35 else (14, -30), gest=None)
            reach = ease_out(ramp(lt, 0.45, 0.75))
            person(c, 'barshim', bx, GY, H, T, legs='walk' if w < 0.98 else 'stand', phase=T * 9, facing=0.55, expr='happy',
                   lhand=(-15, -31), rhand=(lerp(14, 26, reach), lerp(-30, -40, reach)), gest=None, tear=lt > 0.8)
        else:
            embrace(c, T, 1.0, flare)
    K.vvignette(c, 0.42)


def sh_loop(c, lt, dur, T):
    # tilt up from the embrace to the empty-of-drama bar under the lights; the pair steps back into the opening pose,
    # and the camera settles exactly on the t=0 framing for a seamless loop.
    camA = vcam(DUR9, DUR9, CAM9[0], CAM9[1], 'lin', 0.4, 13)
    camB = VCam(540, 970, 1.12)  # tilt up to the bar while faces stay above the caption band
    camC = cam_shot1(0.0)
    p1 = ease_io(ramp(lt, 0.5, 2.5))
    p2 = ease_io(ramp(lt, 2.3, dur - 0.08))
    cx = lerp(lerp(camA.cx, camB.cx, p1), camC.cx, p2)
    cy = lerp(lerp(camA.cy, camB.cy, p1), camC.cy, p2)
    z = lerp(lerp(camA.z, camB.z, p1), camC.z, p2)
    cam = VCam(cx, cy, z)
    flare = (1 - ease_io(ramp(lt, 1.0, 3.2))) * 0.9
    stadium_front(c, cam, T, flare=flare, pool=lerp(1.0, 0.5, p2))
    q = ease_io(ramp(lt, 1.0, 3.0))
    with vlayer(c, cam, 1.0):
        if q <= 0:
            embrace(c, T, 1.0, flare)
        elif q >= 1:
            home_pose(c, T, 'barshim')
            home_pose(c, T, 'tamberi')
        else:
            u = H / 90.0
            e = q > 0.5
            person(c, 'tamberi', lerp(EMB['tamberi'], HOME['tamberi'], q), GY, H, T, facing=lerp(-0.7, -0.35, q), tilt=lerp(-1.5, 7, q),
                   look=lerp(0, 1.5, q), expr='neutral' if e else 'happy', tear=not e,
                   lhand=None if q < 0.3 else (-13, -27), rhand=(lerp(14, 13, q), lerp(-30, -27, q)), gest=None)
            person(c, 'barshim', lerp(EMB['barshim'], HOME['barshim'], q), GY, H, T, facing=lerp(0.7, 0.35, q), tilt=lerp(1.5, -7, q),
                   look=lerp(0, 1.5, q), expr='neutral' if e else 'happy', tear=not e,
                   lhand=(-15, -31), rhand=None if q < 0.3 else (14, -30), gest=None)
    K.vvignette(c, 0.45)


SHOTS = [
    (0.0, 7.0, sh_open), (7.0, 8.95, sh_miss_b), (8.95, 10.9, sh_miss_t), (10.9, 13.0, sh_sit),
    (13.0, 17.62, sh_official), (17.62, 19.5, sh_ask), (19.5, 21.05, sh_nod), (21.05, 24.55, sh_joy),
    (24.55, 33.85, sh_cast), (33.85, 36.9, sh_dream), (36.9, 40.05, sh_embrace), (40.05, 999, sh_loop),
]
DUR9 = 40.05 - 36.9


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
CUTS = [s[0] for s in SHOTS[1:]]


def sfx(n):
    from scipy.signal import lfilter, butter
    SR = K.SR
    rng = np.random.default_rng(37)
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

    def whoosh(d=0.32):
        t = t_(d)
        x = bp(rng.standard_normal(len(t)), 500, 5000)
        env = np.sin(np.pi * t / d) ** 2
        return x * env / np.abs(x).max() * 0.07

    def clatter():
        t = t_(0.9)
        s = np.zeros(len(t))
        for f0, dk in ((920, 9), (1460, 11), (2230, 14), (3110, 18)):
            s += np.sin(2 * np.pi * f0 * t + rng.uniform(0, 6)) * np.exp(-t * dk)
        s *= 0.16
        s += bp(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t * 30) * 0.4
        return s

    def rattle():
        out = np.zeros(int(0.8 * SR))
        for i, (t0, g) in enumerate(((0.0, 1.0), (0.17, 0.5), (0.29, 0.3), (0.37, 0.15))):
            K.place(out, clatter()[:int(0.4 * SR)] * g, t0)
        return out * 0.8

    def thud():
        t = t_(0.5)
        return (np.sin(2 * np.pi * 70 * t) * np.exp(-t * 14) * 0.6 + lp(rng.standard_normal(len(t)), 400) * np.exp(-t * 20) * 0.5)

    def slap():
        t = t_(0.18)
        return bp(rng.standard_normal(len(t)), 1200, 6500) * np.exp(-t * 45) * 0.9

    def steps(d, rate=7.0):
        out = np.zeros(int(d * SR))
        for k in range(int(d * rate)):
            t = t_(0.06)
            K.place(out, lp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 60) * 0.25, k / rate)
        return out

    def crowd(d, lo=300, hi=2600):
        t = t_(d)
        x = bp(rng.standard_normal(len(t)), lo, hi) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.4 * t))
        voices = np.zeros(len(t))
        for _ in range(30):
            f0 = rng.uniform(180, 420)
            ph = 2 * np.pi * np.cumsum(f0 * (1 + 0.05 * np.sin(2 * np.pi * rng.uniform(3, 6) * t))) / SR
            voices += np.sin(ph) * rng.uniform(0.3, 1.0)
        x = x / np.abs(x).max() + 0.5 * bp(voices, 300, 1500) / (np.abs(voices).max() + 1e-9)
        return x / np.abs(x).max()

    def chime():
        t = t_(1.6)
        s = np.zeros_like(t)
        for f0, t0 in ((784.0, 0.0), (1046.5, 0.12), (1318.5, 0.24)):
            tt = np.clip(t - t0, 0, None)
            s += np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 3.5) * (t >= t0)
        return s * 0.06

    # stadium air under the stadium shots
    amb = lp(rng.standard_normal(int((TOTAL + 1) * SR)), 260)
    amb = amb / np.abs(amb).max() * 0.02 * (1 + 0.25 * np.sin(2 * np.pi * 0.12 * np.arange(len(amb)) / SR))  # plain low air, no voices
    env = np.ones(n)
    a0, a1 = int(24.55 * SR), int(30.3 * SR)
    env[a0:a1] = 0.15
    rp = int(0.5 * SR)
    env[a0 - rp:a0] = np.linspace(1, 0.15, rp)
    env[a1:a1 + rp] = np.linspace(0.15, 1, rp)
    fx += amb[:n] * env
    for tc in CUTS:
        K.place(fx, whoosh(), tc - 0.16, 1.0)
    # line 2: run-up steps, bar knocked + clatter on the mat, body lands on the mat (both attempts)
    for t0 in (7.0, 8.95):
        K.place(fx, steps(J_RUN, 9), t0 + T_JUMP0, 0.9)
        K.place(fx, clatter(), t0 + T_JUMP0 + T_HIT, 0.9)
        K.place(fx, rattle(), t0 + T_JUMP0 + T_HIT + 0.30, 0.7)
        K.place(fx, thud(), t0 + T_JUMP0 + J_RUN + J_FLY, 0.6)
    K.place(fx, steps(1.6, 3.5), 13.0, 0.5)   # official walks up
    # line 6: slap, then the roar swells
    K.place(fx, slap(), 21.05 + 0.34, 1.0)
    K.place(fx, thud(), 21.05 + 2.7, 0.5)
    K.place(fx, chime(), 24.6, 1.0)        # into the flashback
    K.place(fx, chime(), 30.35, 0.7)       # back to tonight
    return fx


def build_audio():
    n = int(round(TOTAL * K.SR))
    voice = np.zeros(n)
    voice[:min(n, len(V.x))] = V.x[:n]
    x = K.load_track(MUSIC)
    B = 10 / 3
    # suspense (track bars 16-20 + 18-20) under lines 1-3, a hushed tender bar for lines 4-5, the lift for line 6's joy,
    # tender under the flashback (7-8), the resolve section to the end (9-10).
    segs = [(16 * B, 20 * B), (18 * B, 20 * B), (0.0, 1 * B), (20 * B, 21 * B), (4 * B, 7 * B), (41 * B, None)]
    mus, spl = K.fit_music(x, segs, n, start=17.6 - 6 * B, xf=1.5, fade_out=0.7)
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
