"""Stick-figure character rig: big round head, egg torso, line limbs, mitten hands."""
import math
import skia
from gfx import *

# ---------------------------------------------------------------- cast
SKIN_IR = '#f3cba8'
CAST = {
    'patrick': dict(skin=SKIN_IR, hair='short', hair_col='#6b5240', beard=True, glasses=True,
                    top='jumper', top_col='#3f8a4f', pants='#2f3c55', shoes='#3a2a20', hs=1.0, seed=1),
    'joanne': dict(skin=SKIN_IR, hair='long', hair_col='#a8482a', scarf='#e3a93c', top='blouse',
                   top_col='#7b4f86', pants='#3b3a4f', shoes='#5a2e2e', hs=0.94, seed=2),
    'girl1': dict(skin=SKIN_IR, hair='long', hair_col='#7a5236', top='dress', top_col='#e2668d',
                  pants='#e2668d', shoes='#c94f6f', hs=0.66, seed=3, kid=True),
    'girl2': dict(skin=SKIN_IR, hair='pony', hair_col='#b0532f', top='dress', top_col='#33b0a3',
                  pants='#33b0a3', shoes='#23786f', hs=0.57, seed=4, kid=True),
    'girl3': dict(skin=SKIN_IR, hair='bunches', hair_col='#e0b45a', top='dress', top_col='#f2c14e',
                  pants='#f2c14e', shoes='#c9962e', hs=0.48, seed=5, kid=True),
    # three friends: blue / yellow / red
    'filippo': dict(skin='#e2b088', hair='wavy', hair_col='#3a2a1e', top='tee', top_col='#2f6fd0',
                    cap='#2f6fd0', pants='#d9cdb4', shoes='#f2f2f2', hs=1.0, seed=6),
    'nicola': dict(skin='#d6a077', hair='curly', hair_col='#1f1712', top='tee', top_col='#f0b726',
                   cap=None, shades=True, pants='#39506e', shoes='#f2f2f2', hs=1.02, seed=7),
    'edoardo': dict(skin='#c98d64', hair='buzz', hair_col='#2a1f19', top='tee', top_col='#d23b35',
                    cap='#d23b35', pants='#4a4a4a', shoes='#222222', hs=0.98, seed=8, stubble=True),
}

SUB_COL = {'NARRATOR': '#ffffff', 'PATRICK': '#c9f2c4', 'JOANNE': '#ffd0b5', 'FILIPPO': '#c9ddff',
           'NICOLA': '#fff0a6', 'EDOARDO': '#ffc4c0'}
SPEAKER_KEY = {'PATRICK': 'patrick', 'JOANNE': 'joanne', 'FILIPPO': 'filippo', 'NICOLA': 'nicola',
               'EDOARDO': 'edoardo', 'FRIEND1': 'filippo', 'FRIEND2': 'nicola', 'FRIEND3': 'edoardo'}


def hobbit(spec):
    """Generic storybook halfling costume: short cloak, waistcoat in signature colour, curly hair, bare feet."""
    s = dict(spec)
    s['costume'] = True
    s['top'] = 'waistcoat'
    s['vest_col'] = spec['top_col']
    s['top_col'] = '#f1e6cc'
    s['cloak'] = {'filippo': '#5d6b3a', 'nicola': '#7a5230', 'edoardo': '#6a3b2c'}.get(spec.get('name', ''), '#6b4a2e')
    s['hair'] = 'curly'
    s['hair_col'] = {'filippo': '#7a4a26', 'nicola': '#3a2414', 'edoardo': '#a0632c'}.get(spec.get('name', ''), '#6b4a2e')
    s['cap'] = None
    s['shades'] = False
    s['pants'] = '#7a6248'
    s['shoes'] = None
    return s


for k, v in CAST.items():
    v['name'] = k

EXPR = {
    #          brow tilt (deg, + = inner up/worried), brow lift, eyes, mouth
    'neutral': (0, 0, 'dot', 'smile0'),
    'smile': (0, 0.3, 'dot', 'smile'),
    'happy': (-4, 0.8, 'happy', 'grin'),
    'laugh': (-4, 1.0, 'happy', 'laugh'),
    'surprised': (6, 2.2, 'wide', 'o'),
    'sad': (16, 0.3, 'dot', 'frown'),
    'concerned': (12, 0.6, 'dot', 'flat'),
    'determined': (-14, -0.4, 'dot', 'flat'),
    'thinking': (8, 0.8, 'side', 'flat'),
    'strain': (-16, -0.6, 'squint', 'teeth'),
    'tender': (8, 0.4, 'soft', 'smile'),
}


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 1e-3)
    d = max(d, 1e-3)
    a = math.atan2(dy, dx)
    cosb = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    b = math.acos(cosb)
    ea = a + b * bend
    ex, ey = sx + l1 * math.cos(ea), sy + l1 * math.sin(ea)
    hx, hy = sx + (l1 + l2) * math.cos(a) * 0 + dx / math.hypot(dx, dy) * d if math.hypot(dx, dy) > 0 else tx, 0
    # recompute hand at reachable distance
    nx, ny = (dx / max(math.hypot(dx, dy), 1e-6), dy / max(math.hypot(dx, dy), 1e-6))
    hx, hy = sx + nx * d, sy + ny * d
    return (ex, ey), (hx, hy)


def blink_amt(T, seed):
    if T < 0.25:
        return 0.0
    ph = (T + seed * 1.37) % 3.3
    if ph < 0.13:
        return 1.0 - abs(ph - 0.065) / 0.065 * 0.6
    return 0.0


def draw_person(c, spec, x, y, h, st=None, T=0.0):
    """x,y = feet centre in current canvas coords; h = approx full height in px."""
    st = st or {}
    u = h / 90.0
    sw = clamp(u * 1.05, 2.2, 5.0)  # outline weight
    face = st.get('facing', 0.0)
    expr = st.get('expr', 'smile')
    mouth = st.get('mouth', 0)
    tilt = st.get('tilt', 0.0)
    legs = st.get('legs', 'stand')
    phase = st.get('phase', 0.0)
    bob = st.get('bob', True)
    seed = spec.get('seed', 0)
    skin = spec['skin']
    breath = math.sin(T * 2.1 + seed) * 0.6 if bob else 0
    if mouth:
        tilt += math.sin(T * 7.0 + seed) * 2.0
    c.save()
    c.translate(x, y)
    if st.get('flip'):
        c.scale(-1, 1)
        face = -face
    if st.get('rot'):
        c.rotate(st['rot'])
    if st.get('shadow', True):
        c.drawOval(skia.Rect.MakeLTRB(-20 * u + 5 * u, -3.2 * u, 20 * u + 5 * u, 3.2 * u),
                   fillp('#000000', st.get('shadow_a', 0.25)))
    hip_y = -24 * u
    lift = 0
    if legs == 'jump':
        lift = 0
    # ---- legs
    lc = spec.get('pants', '#333')
    def leg(x0, y0, x1, y1, x2=None, y2=None):
        pts = [(x0, y0), (x1, y1)] + ([(x2, y2)] if x2 is not None else [])
        p = poly(pts, close=False)
        c.drawPath(p, strokep(INK, 4.2 * u + sw * 1.6))
        c.drawPath(p, strokep(lc, 4.2 * u))
        return pts[-1]
    feet = []
    if legs == 'walk':
        for s, off in ((-1, 0), (1, math.pi)):
            a = math.sin(phase + off) * 0.42
            fx = s * 3 * u + math.sin(a) * 24 * u
            fy = hip_y + math.cos(a) * 24 * u
            feet.append(leg(s * 4 * u, hip_y, fx, fy))
    elif legs == 'sit':
        d = 1 if face >= 0 else -1
        for s in (-1, 1):
            feet.append(leg(s * 5 * u, hip_y, s * 5 * u + d * 13 * u, hip_y + 1 * u, s * 5 * u + d * 14 * u, 0))
    elif legs == 'jump':
        for s in (-1, 1):
            feet.append(leg(s * 5 * u, hip_y, s * 9 * u, hip_y + 10 * u, s * 4 * u, hip_y + 18 * u))
    elif legs == 'brace':
        feet.append(leg(-5 * u, hip_y, -16 * u, 0))
        feet.append(leg(5 * u, hip_y, 10 * u, -2 * u))
    elif legs == 'none':
        pass
    else:
        for s in (-1, 1):
            feet.append(leg(s * 5 * u, hip_y, s * 6.5 * u, 0))
    for (fx, fy) in feet:
        if spec.get('shoes'):
            draw(c, oval(fx + 1.5 * u * (1 if face >= 0 else -1), fy - 0.8 * u, 4.2 * u, 2.3 * u),
                 spec['shoes'], INK, sw * 0.8)
        else:  # bare feet
            draw(c, oval(fx + 2 * u * (1 if face >= 0 else -1), fy - 0.9 * u, 4.8 * u, 2.4 * u),
                 skin, INK, sw * 0.8)
            for k in range(3):
                c.drawCircle(fx + (3.6 + k * 1.3) * u * (1 if face >= 0 else -1), fy - 2.2 * u, 0.5 * u,
                             fillp(shade(skin, -0.3)))
    c.translate(0, breath * u * 0.4)
    # ---- cloak (behind)
    if spec.get('cloak'):
        cl = spec['cloak']
        sway = math.sin(T * 1.6 + seed) * 1.5 * u
        p = smooth_path([(-11 * u, -57 * u), (11 * u, -57 * u), (19 * u + sway, -20 * u), (14 * u + sway, -15 * u),
                         (0 + sway, -17 * u), (-14 * u + sway, -15 * u), (-19 * u + sway, -20 * u)], True, 0.35)
        draw(c, p, cl, INK, sw)
        c.drawLine(-6 * u, -45 * u, -9 * u + sway, -19 * u, strokep(shade(cl, -0.25), sw * 0.6))
        c.drawLine(6 * u, -45 * u, 9 * u + sway, -19 * u, strokep(shade(cl, -0.25), sw * 0.6))
    # ---- long hair back
    hc = spec['hair_col']
    hy = -72 * u
    hx = face * 1.0 * u
    if spec['hair'] == 'long':
        sway = math.sin(T * 1.8 + seed) * 0.8 * u
        p = smooth_path([(-15.5 * u + hx, hy - 4 * u), (15.5 * u + hx, hy - 4 * u), (17 * u + hx + sway, hy + 16 * u),
                         (12 * u + hx + sway, hy + 22 * u), (-12 * u + hx + sway, hy + 22 * u),
                         (-17 * u + hx + sway, hy + 16 * u)], True, 0.4)
        draw(c, p, shade(hc, -0.12), INK, sw)
    # ---- torso
    tc = spec['top_col']
    top = spec['top']
    ty0, ty1 = -58 * u, -22 * u
    if top == 'dress':
        body = smooth_path([(-9 * u, -57 * u), (9 * u, -57 * u), (12 * u, -40 * u), (17 * u, -16 * u),
                            (0, -14.5 * u), (-17 * u, -16 * u), (-12 * u, -40 * u)], True, 0.3)
    else:
        body = smooth_path([(0, -58.5 * u), (11 * u, -55 * u), (14.5 * u, -42 * u), (13 * u, -27 * u),
                            (0, -22 * u), (-13 * u, -27 * u), (-14.5 * u, -42 * u), (-11 * u, -55 * u)], True, 0.5)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.drawPaint(fillp(None, 1, shader=lin(-15 * u, -58 * u, 15 * u, -22 * u, [shade(tc, 0.12), tc, shade(tc, -0.18)])))
    # shade crescent right
    c.drawOval(skia.Rect.MakeLTRB(6 * u, -62 * u, 26 * u, -16 * u), fillp('#000000', 0.12))
    if top == 'jumper':
        hem = shade(tc, -0.22)
        c.drawRect(skia.Rect.MakeLTRB(-20 * u, -29 * u, 20 * u, -20 * u), fillp(hem))
        for k in range(-6, 7):
            c.drawLine(k * 2.2 * u, -29 * u, k * 2.2 * u, -20 * u, strokep(shade(hem, -0.2), u * 0.5))
        for k in (-1, 1):
            c.drawPath(smooth_path([(k * 9 * u, -50 * u), (k * 6 * u, -42 * u), (k * 8 * u, -34 * u)], False),
                       strokep(shade(tc, -0.25), u * 0.6))
        # cable-knit centre
        for k in range(5):
            yy = -52 * u + k * 5 * u
            c.drawPath(smooth_path([(-2 * u, yy), (0, yy + 2.5 * u), (2 * u, yy)], False), strokep(shade(tc, -0.2), u * 0.6))
    elif top == 'tee':
        hem = shade(tc, -0.2)
        c.drawRect(skia.Rect.MakeLTRB(-20 * u, -26 * u, 20 * u, -20 * u), fillp(hem))
        c.drawLine(-6 * u, -45 * u, -3 * u, -40 * u, strokep(shade(tc, -0.25), u * 0.5))
        if spec['name'] == 'filippo':  # stripe
            c.drawRect(skia.Rect.MakeLTRB(-20 * u, -44 * u, 20 * u, -41 * u), fillp('#ffffff', 0.85))
        elif spec['name'] == 'nicola':  # small sun print
            c.drawCircle(-5 * u, -44 * u, 3 * u, fillp('#ffffff', 0.8))
        elif spec['name'] == 'edoardo':  # number
            c.drawString('7', -3 * u, -36 * u, font(FONT_HAND, 12 * u), fillp('#ffffff', 0.9))
    elif top == 'blouse':
        hem = shade(tc, -0.2)
        c.drawRect(skia.Rect.MakeLTRB(-20 * u, -27 * u, 20 * u, -20 * u), fillp(hem))
        for k in range(3):
            c.drawCircle(0, -48 * u + k * 6 * u, 0.8 * u, fillp('#f6eadd'))
    elif top == 'dress':
        c.drawRect(skia.Rect.MakeLTRB(-20 * u, -19 * u, 20 * u, -12 * u), fillp(shade(tc, -0.2)))
        for k in range(-3, 4):
            c.drawCircle(k * 4.5 * u, -30 * u + (k % 2) * 4 * u, 0.9 * u, fillp('#ffffff', 0.7))
    elif top == 'waistcoat':
        vc = spec['vest_col']
        for s in (-1, 1):
            p = poly([(s * 2 * u, -55 * u), (s * 16 * u, -55 * u), (s * 16 * u, -20 * u), (s * 1 * u, -24 * u),
                      (s * 1 * u, -44 * u)])
            draw(c, p, vc, INK, sw * 0.7)
        for k in range(3):
            c.drawCircle(-2.4 * u, -42 * u + k * 5.5 * u, 1.0 * u, fillp('#e8c25a'))
        c.drawRect(skia.Rect.MakeLTRB(-20 * u, -28 * u, 20 * u, -25 * u), fillp('#5a3b22'))
    elif top == 'plaid':
        dk = shade(tc, -0.35)
        for k in range(-5, 6):
            c.drawLine(k * 4.2 * u, -60 * u, k * 4.2 * u, -20 * u, strokep(dk, 1.1 * u, 0.7))
        for k in range(10):
            c.drawLine(-20 * u, -58 * u + k * 4.2 * u, 20 * u, -58 * u + k * 4.2 * u, strokep(dk, 1.1 * u, 0.7))
        for k in range(-2, 3):
            c.drawLine(k * 8.4 * u + 2 * u, -60 * u, k * 8.4 * u + 2 * u, -20 * u, strokep('#f1e6cc', 0.5 * u, 0.5))
        for k in range(3):
            c.drawCircle(0, -48 * u + k * 7 * u, 0.8 * u, fillp('#f1e6cc'))
    elif top == 'cardigan':
        inner = spec.get('inner_col', '#efe6d4')
        c.drawRect(skia.Rect.MakeLTRB(-5 * u, -60 * u, 5 * u, -20 * u), fillp(inner))
        for s2 in (-1, 1):
            c.drawLine(s2 * 5 * u, -57 * u, s2 * 5 * u, -21 * u, strokep(INK, 0.6 * u))
            c.drawRect(skia.Rect.MakeLTRB(s2 * 7 * u - 3 * u, -36 * u, s2 * 7 * u + 3 * u, -31 * u), strokep(shade(tc, -0.3), 0.5 * u))
        for k in range(4):
            c.drawCircle(-6.2 * u, -50 * u + k * 6.5 * u, 0.8 * u, fillp('#e8d6a0'))
        c.drawRect(skia.Rect.MakeLTRB(-20 * u, -26 * u, 20 * u, -20 * u), fillp(shade(tc, -0.18)))
        for k in range(-6, 7):
            c.drawLine(k * 2.4 * u, -26 * u, k * 2.4 * u, -20 * u, strokep(shade(tc, -0.35), 0.4 * u))
    elif top == 'pjs':
        for k in range(-4, 5):
            c.drawLine(k * 4 * u, -60 * u, k * 4 * u, -20 * u, strokep('#ffffff', 1.3 * u, 0.35))
    c.restore()
    c.drawPath(body, strokep(INK, sw))
    # collar
    if top in ('jumper', 'tee', 'pjs'):
        draw(c, oval(0, -57.5 * u, 6 * u, 2.2 * u), shade(tc, -0.2), INK, sw * 0.7)
    elif top in ('plaid', 'cardigan'):
        c.drawPath(poly([(-6 * u, -58 * u), (-1 * u, -50 * u), (0, -57 * u), (1 * u, -50 * u), (6 * u, -58 * u)], False),
                   strokep(INK, sw * 0.7))
    elif top == 'blouse':
        c.drawPath(poly([(-5 * u, -57 * u), (0, -50 * u), (5 * u, -57 * u)], False), strokep(INK, sw * 0.7))
    elif top == 'waistcoat':
        c.drawPath(poly([(-5 * u, -57 * u), (0, -52 * u), (5 * u, -57 * u)], False), strokep(INK, sw * 0.7))
    if spec.get('cloak'):
        c.drawCircle(-7 * u, -55 * u, 1.6 * u, fillp('#c9a24a'))
        c.drawCircle(-7 * u, -55 * u, 1.6 * u, strokep(INK, sw * 0.5))
    if spec.get('scarf'):
        sc = spec['scarf']
        sway = math.sin(T * 2.0 + seed) * 1.2 * u
        draw(c, rrect(-8 * u, -60 * u, 16 * u, 5 * u, 2.5 * u), sc, INK, sw * 0.8)
        draw(c, poly([(2 * u, -57 * u), (7 * u, -57 * u), (8 * u + sway, -42 * u), (3 * u + sway, -43 * u)]), sc, INK, sw * 0.8)
        for k in range(3):
            c.drawLine(3 * u + k * 1.6 * u + sway, -43 * u, 3.4 * u + k * 1.6 * u + sway, -40.5 * u, strokep(sc, u * 0.6))
        c.drawLine(-6 * u, -59 * u, 6 * u, -59 * u, strokep(shade(sc, -0.25), u * 0.7))
    # ---- arms
    lh = st.get('lhand', (-15 * u / u, -31))
    rh = st.get('rhand', (15, -31))
    hold = st.get('hold')
    arm_w = clamp(u * 1.25, 2.0, 6.5)
    hands = []
    for s, hand in ((-1, lh), (1, rh)):
        if hand is None:
            hands.append(None)
            continue
        sx, sy = s * 11.5 * u, -52 * u
        tx, ty = hand[0] * u, hand[1] * u
        (ex, ey), (hx2, hy2) = ik(sx, sy, tx, ty, 13 * u, 13 * u, bend=-s if ty > sy - 6 * u else s)
        if top == 'tee' or top == 'waistcoat':
            # little sleeve
            draw(c, oval(s * 12.5 * u, -51 * u, 3.6 * u, 3.6 * u), tc if top == 'tee' else spec['top_col'], INK, sw * 0.7)
        elif top in ('jumper', 'blouse', 'plaid', 'cardigan', 'pjs'):
            # sleeve: thick coloured upper arm
            pth = poly([(sx, sy), (ex, ey)], False)
            c.drawPath(pth, strokep(INK, 5.2 * u + sw * 1.4))
            c.drawPath(pth, strokep(tc, 5.2 * u))
        p = poly([(sx, sy), (ex, ey), (hx2, hy2)], False)
        c.drawPath(p, strokep(INK, arm_w))
        if spec.get('bracelet') and s == 1:
            bx, by = lerp(ex, hx2, 0.8), lerp(ey, hy2, 0.8)
            c.drawCircle(bx, by, 2.6 * u, strokep('#e6ebef', 1.8 * u))
            c.drawCircle(bx, by, 2.6 * u, strokep(INK, 0.5 * u))
            c.drawArc(skia.Rect.MakeXYWH(bx - 2.6 * u, by - 2.6 * u, 5.2 * u, 5.2 * u), 200, 60, False, strokep('#ffffff', 0.9 * u))
        hands.append((hx2, hy2))
        c.drawCircle(hx2, hy2, 3.0 * u, fillp(skin))
        c.drawCircle(hx2, hy2, 3.0 * u, strokep(INK, sw * 0.8))
        if spec.get('ring_on') and s == -1:
            c.drawCircle(hx2 + 1.6 * u, hy2 + 0.6 * u, 1.0 * u, strokep('#e8b833', 0.8 * u))
    if hold:
        hold(c, hands, u)
    # ---- head
    c.save()
    c.translate(0, hy)
    c.rotate(tilt)
    R = 15.5 * u
    head = oval(0, 0, R, R)
    c.save()
    c.clipPath(head, doAntiAlias=True)
    c.drawPaint(fillp(shade(skin, -0.22)))
    c.drawCircle(-0.16 * R, -0.12 * R, R * 1.0, fillp(None, 1, shader=rad(-0.25 * R, -0.3 * R, R * 1.25,
                                                                           [shade(skin, 0.1), skin, shade(skin, -0.06)])))
    c.restore()
    c.drawArc(skia.Rect.MakeLTRB(-R * 0.86, -R * 0.86, R * 0.86, R * 0.86), 195, 70, False,
              strokep('#ffffff', u * 0.9, 0.55))
    c.drawPath(head, strokep(INK, sw))
    fx = face * 4.2 * u
    # beard / stubble
    if spec.get('beard'):
        bc = shade(hc, -0.05)
        p = skia.Path()
        p.moveTo(-14.8 * u, 1 * u)
        p.cubicTo(-14 * u, 12 * u, -6 * u, 16 * u, 0 + fx * 0.3, 16 * u)
        p.cubicTo(6 * u, 16 * u, 14 * u, 12 * u, 14.8 * u, 1 * u)
        p.cubicTo(11 * u, 4.5 * u, 6 * u, 3.6 * u, fx, 3.4 * u)
        p.cubicTo(-6 * u, 3.6 * u, -11 * u, 4.5 * u, -14.8 * u, 1 * u)
        p.close()
        c.save()
        c.clipPath(head, doAntiAlias=True)
        draw(c, p, bc, INK, sw * 0.6)
        for k in range(7):
            ax = -9 * u + k * 3 * u
            c.drawLine(ax, 8 * u, ax + 0.6 * u, 11 * u, strokep(shade(bc, -0.3), 0.5 * u))
        c.restore()
    if spec.get('stubble'):
        c.save()
        c.clipPath(head, doAntiAlias=True)
        c.drawOval(skia.Rect.MakeLTRB(-13 * u + fx, 1 * u, 13 * u + fx, 17 * u), fillp('#3a2a22', 0.16))
        c.restore()
    # eyes
    bt, bl, eyes, mclosed = EXPR.get(expr, EXPR['smile'])
    bk = blink_amt(T, seed) if not st.get('noblink') else 0
    ey = -2.2 * u
    for s in (-1, 1):
        ex = fx + s * 5.4 * u
        if bk > 0.5 or eyes == 'closed':
            c.drawLine(ex - 1.8 * u, ey, ex + 1.8 * u, ey, strokep(INK, u * 0.8))
        elif eyes == 'happy':
            c.drawArc(skia.Rect.MakeLTRB(ex - 2.0 * u, ey - 1.6 * u, ex + 2.0 * u, ey + 2.0 * u), 200, 140, False,
                      strokep(INK, u * 0.9))
        elif eyes == 'wide':
            c.drawOval(skia.Rect.MakeLTRB(ex - 2.2 * u, ey - 2.9 * u, ex + 2.2 * u, ey + 2.9 * u), fillp(INK))
            c.drawCircle(ex - 0.7 * u, ey - 1.3 * u, 0.7 * u, fillp('#ffffff'))
        elif eyes == 'squint':
            c.drawLine(ex - 2 * u, ey - s * 0.0, ex + 2 * u, ey + 0.6 * u * 0, strokep(INK, u * 1.0))
        elif eyes == 'soft':
            c.drawOval(skia.Rect.MakeLTRB(ex - 1.5 * u, ey - 1.4 * u, ex + 1.5 * u, ey + 1.6 * u), fillp(INK))
            c.drawCircle(ex - 0.5 * u, ey - 0.6 * u, 0.5 * u, fillp('#ffffff'))
        else:
            look = 0.9 * u if eyes == 'side' else 0
            c.drawOval(skia.Rect.MakeLTRB(ex - 1.6 * u + look, ey - 2.2 * u, ex + 1.6 * u + look, ey + 2.2 * u), fillp(INK))
            c.drawCircle(ex - 0.5 * u + look, ey - 1.0 * u, 0.55 * u, fillp('#ffffff'))
        # brows
        byy = ey - 5.2 * u - bl * u
        ang = math.radians(bt) * s * -1
        bx0, bx1 = ex - 2.6 * u, ex + 2.6 * u
        cy = byy
        dy = math.tan(ang) * 2.6 * u
        c.drawLine(bx0, cy - dy * (-1 if s < 0 else 1) * -1, bx1, cy + dy * (-1 if s < 0 else 1) * -1,
                   strokep(shade(hc, -0.35), u * 1.0))
    # glasses
    if spec.get('glasses'):
        for s in (-1, 1):
            ex = fx + s * 5.4 * u
            c.drawCircle(ex, ey, 3.9 * u, strokep(INK, u * 0.85))
            c.drawCircle(ex, ey, 3.9 * u, fillp('#ffffff', 0.10))
        c.drawLine(fx - 1.5 * u, ey - 0.5 * u, fx + 1.5 * u, ey - 0.5 * u, strokep(INK, u * 0.8))
    if spec.get('shades'):
        # sunglasses pushed up on the head
        for s in (-1, 1):
            c.drawOval(skia.Rect.MakeLTRB(fx + s * 5.4 * u - 3.4 * u, -13.6 * u, fx + s * 5.4 * u + 3.4 * u, -9.4 * u),
                       fillp('#222831'))
        c.drawLine(fx - 2 * u, -11.6 * u, fx + 2 * u, -11.6 * u, strokep(INK, u * 0.7))
    # blush
    for s in (-1, 1):
        c.drawOval(skia.Rect.MakeLTRB(fx + s * 9 * u - 2.4 * u, 2.6 * u, fx + s * 9 * u + 2.4 * u, 4.6 * u),
                   fillp('#ff7a7a', 0.18))
    # mouth
    my = 6.4 * u
    mx = fx
    if mouth and mouth > 0:
        shapes = {1: (2.0, 1.6), 2: (2.4, 3.0), 3: (4.0, 3.4), 4: (4.6, 2.6)}
        rx, ry = shapes.get(int(mouth), (3, 2.5))
        if int(mouth) == 4:
            p = skia.Path()
            p.moveTo(mx - rx * u, my - 0.6 * u)
            p.cubicTo(mx - rx * u, my + ry * 1.6 * u, mx + rx * u, my + ry * 1.6 * u, mx + rx * u, my - 0.6 * u)
            p.close()
        else:
            p = oval(mx, my + 0.6 * u, rx * u, ry * u)
        c.save()
        c.clipPath(p, doAntiAlias=True)
        c.drawPaint(fillp('#5b1d22'))
        c.drawOval(skia.Rect.MakeLTRB(mx - rx * u, my + ry * 0.5 * u, mx + rx * u, my + ry * 2.4 * u), fillp('#e0707a'))
        c.restore()
        c.drawPath(p, strokep(INK, u * 0.8))
    else:
        if mclosed in ('smile', 'smile0'):
            wv = 3.6 if mclosed == 'smile' else 2.6
            c.drawArc(skia.Rect.MakeLTRB(mx - wv * u, my - 2.6 * u, mx + wv * u, my + 1.6 * u), 20, 140, False,
                      strokep(INK, u * 0.9))
        elif mclosed in ('grin', 'laugh'):
            p = skia.Path()
            p.moveTo(mx - 4.4 * u, my - 0.8 * u)
            p.cubicTo(mx - 4 * u, my + 4.8 * u, mx + 4 * u, my + 4.8 * u, mx + 4.4 * u, my - 0.8 * u)
            p.close()
            draw(c, p, '#5b1d22', INK, u * 0.8)
            c.drawRect(skia.Rect.MakeLTRB(mx - 3.6 * u, my - 0.6 * u, mx + 3.6 * u, my + 0.8 * u), fillp('#ffffff'))
        elif mclosed == 'frown':
            c.drawArc(skia.Rect.MakeLTRB(mx - 3 * u, my + 0.6 * u, mx + 3 * u, my + 4.6 * u), 200, 140, False,
                      strokep(INK, u * 0.9))
        elif mclosed == 'o':
            draw(c, oval(mx, my + 1 * u, 1.8 * u, 2.2 * u), '#5b1d22', INK, u * 0.8)
        elif mclosed == 'teeth':
            draw(c, rrect(mx - 4 * u, my - 1 * u, 8 * u, 3.2 * u, 1 * u), '#ffffff', INK, u * 0.8)
            c.drawLine(mx - 4 * u, my + 0.6 * u, mx + 4 * u, my + 0.6 * u, strokep(INK, u * 0.5))
        else:
            c.drawLine(mx - 2.8 * u, my + 0.8 * u, mx + 2.8 * u, my + 0.8 * u, strokep(INK, u * 0.9))
    if st.get('tear'):
        c.drawPath(smooth_path([(fx + 7 * u, 1 * u), (fx + 8.2 * u, 4 * u), (fx + 7 * u, 5 * u), (fx + 5.8 * u, 4 * u)]),
                   fillp('#8fd0ff', 0.9))
    if st.get('sweat'):
        draw(c, smooth_path([(13 * u, -12 * u), (15 * u, -7 * u), (13 * u, -5 * u), (11 * u, -7 * u)]), '#9fd8ff', INK, u * 0.5)
    # hair front
    hs = spec['hair']
    if hs == 'bun':
        draw(c, oval(0, -R * 1.12, R * 0.42, R * 0.36), shade(hc, -0.05), INK, sw)
        c.drawArc(skia.Rect.MakeLTRB(-R * 0.3, -R * 1.4, R * 0.2, -R * 1.0), 200, 80, False, strokep(shade(hc, 0.35), u, 0.7))
    if hs in ('short', 'wavy', 'long', 'pony', 'bunches', 'buzz', 'bun'):
        if hs == 'pony':
            sw2 = math.sin(T * 3 + seed) * 2 * u
            draw(c, smooth_path([(-R * 0.6 - face * 4 * u, -R * 0.5), (-R * 1.3 - face * 4 * u + sw2, -R * 0.1),
                                 (-R * 1.25 - face * 4 * u + sw2, R * 0.6), (-R * 0.9 - face * 4 * u, R * 0.1)]),
                 shade(hc, -0.05), INK, sw)
        if hs == 'bunches':
            for s in (-1, 1):
                draw(c, oval(s * R * 1.05, -R * 0.15, R * 0.32, R * 0.36), hc, INK, sw)
        cap_lo = {'short': -0.35, 'wavy': -0.25, 'long': -0.15, 'pony': -0.3, 'bunches': -0.3, 'buzz': -0.55, 'bun': -0.3}[hs]
        p = skia.Path()
        p.moveTo(-R * 1.02, R * cap_lo + R * 0.25)
        p.cubicTo(-R * 1.1, -R * 1.25, R * 1.1, -R * 1.25, R * 1.02, R * cap_lo + R * 0.25)
        # fringe line
        if hs in ('long', 'pony', 'bunches', 'bun'):
            p.cubicTo(R * 0.7, -R * 0.55, R * 0.1 + fx, -R * 0.75, -R * 0.1 + fx, -R * 0.45)
            p.cubicTo(-R * 0.4 + fx, -R * 0.7, -R * 0.8, -R * 0.55, -R * 1.02, R * cap_lo + R * 0.25)
        elif hs == 'wavy':
            p.cubicTo(R * 0.7, -R * 0.5, R * 0.5, -R * 0.75, R * 0.2 + fx, -R * 0.55)
            p.cubicTo(-R * 0.1 + fx, -R * 0.8, -R * 0.6, -R * 0.5, -R * 1.02, R * cap_lo + R * 0.25)
        else:
            p.cubicTo(R * 0.8, -R * 0.55, R * 0.3 + fx, -R * 0.7, -R * 0.2 + fx, -R * 0.62)
            p.cubicTo(-R * 0.6, -R * 0.6, -R * 0.9, -R * 0.3, -R * 1.02, R * cap_lo + R * 0.25)
        p.close()
        c.save()
        c.clipPath(oval(0, -R * 0.05, R * 1.12, R * 1.15), doAntiAlias=True)
        draw(c, p, hc, INK, sw)
        c.drawArc(skia.Rect.MakeLTRB(-R * 0.7, -R * 0.98, R * 0.5, -R * 0.4), 200, 80, False,
                  strokep(shade(hc, 0.35), u * 1.4, 0.8))
        for k in range(3):
            a0 = -0.4 * R + k * 0.3 * R
            c.drawLine(a0, -R * 0.95, a0 + 0.12 * R, -R * 0.7, strokep(shade(hc, -0.3), u * 0.5))
        c.restore()
        if spec.get('hair_grey'):
            pass
    elif hs == 'curly':
        rng = [(-1.0, -0.15), (-0.92, -0.55), (-0.62, -0.9), (-0.22, -1.08), (0.22, -1.08), (0.62, -0.9),
               (0.92, -0.55), (1.0, -0.15)]
        if spec.get('costume'):
            rng += [(-1.06, 0.2), (1.06, 0.2)]
        for (ax, ay) in rng:
            draw(c, oval(ax * R, ay * R, R * 0.36, R * 0.36), hc, INK, sw * 0.8)
        draw(c, oval(0, -R * 0.62, R * 0.8, R * 0.42), hc, None, 0)
        for (ax, ay) in rng[1:7]:
            c.drawArc(skia.Rect.MakeLTRB(ax * R - R * 0.18, ay * R - R * 0.18, ax * R + R * 0.18, ay * R + R * 0.18),
                      200, 160, False, strokep(shade(hc, 0.3), u * 0.6, 0.8))
    # cap
    if spec.get('cap'):
        cc = spec['cap']
        d = 1 if face >= 0 else -1
        p = skia.Path()
        p.moveTo(-R * 1.02, -R * 0.28)
        p.cubicTo(-R * 1.05, -R * 1.3, R * 1.05, -R * 1.3, R * 1.02, -R * 0.28)
        p.close()
        draw(c, p, cc, INK, sw)
        c.drawLine(-R * 1.0, -R * 0.36, R * 1.0, -R * 0.36, strokep(shade(cc, -0.3), u * 1.2))
        brim = smooth_path([(d * R * 0.2, -R * 0.4), (d * R * 1.55, -R * 0.42), (d * R * 1.5, -R * 0.24),
                            (d * R * 0.2, -R * 0.24)], True, 0.2)
        draw(c, brim, shade(cc, -0.15), INK, sw * 0.9)
        c.drawCircle(0, -R * 1.0, 1.2 * u, fillp(shade(cc, -0.3)))
        c.drawArc(skia.Rect.MakeLTRB(-R * 0.7, -R * 1.05, R * 0.3, -R * 0.5), 200, 70, False,
                  strokep('#ffffff', u * 1.2, 0.4))
    c.restore()  # head
    c.restore()


def gesture(T, seed=0, amp=1.0):
    """small talking-hand oscillation"""
    return (math.sin(T * 5.0 + seed) * 2.5 * amp, math.sin(T * 3.3 + seed * 2) * 3.0 * amp)
