"""Small drawing helpers on top of skia-python. Everything is deterministic."""
import math
import skia

W, H = 1920, 1080
FPS = 30
INK = "#1a1612"

_tf_cache = {}
FONT_SUB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FONT_HAND = "/usr/share/fonts/truetype/google-fonts/ofl/comicrelief/ComicRelief-Bold.ttf"
FONT_HAND_R = "/usr/share/fonts/truetype/google-fonts/ofl/comicrelief/ComicRelief-Regular.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
FONT_UI = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"


def typeface(path, weight=None):
    key = (path, weight)
    if key not in _tf_cache:
        tf = skia.Typeface.MakeFromFile(path)
        if weight is not None:
            try:
                tag = skia.FourByteTag('w', 'g', 'h', 't')
                coords = skia.FontArguments.VariationPosition.Coordinates([
                    skia.FontArguments.VariationPosition.Coordinate(tag, float(weight))])
                pos = skia.FontArguments.VariationPosition(coords)
                args = skia.FontArguments()
                args.setVariationDesignPosition(pos)
                tf = tf.makeClone(args)
            except Exception:
                pass
        _tf_cache[key] = tf
    return _tf_cache[key]


def font(path, size, weight=None):
    f = skia.Font(typeface(path, weight), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def hexc(h, a=1.0):
    h = h.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, max(0, min(255, int(round(a * 255)))))


def rgb(h):
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(h1, h2, t):
    a, b = rgb(h1), rgb(h2)
    t = max(0.0, min(1.0, t))
    return '#%02x%02x%02x' % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(h, k):
    """k<0 darker, k>0 lighter"""
    return mix(h, '#000000', -k) if k < 0 else mix(h, '#ffffff', k)


def fillp(color, a=1.0, shader=None, blur=0):
    p = skia.Paint(AntiAlias=True)
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(a)
    else:
        p.setColor(hexc(color, a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def strokep(color=INK, w=4.0, a=1.0, cap='round', blur=0):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setColor(hexc(color, a))
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == 'round' else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)],
                                          [hexc(c) if isinstance(c, str) else c for c in cols], pos)


def rad(x, y, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 0.1),
                                          [hexc(c) if isinstance(c, str) else c for c in cols], pos)


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth_path(pts, close=True, k=0.5):
    """Catmull-Rom through points -> cubic path."""
    p = skia.Path()
    n = len(pts)
    if n < 3:
        return poly(pts, close)
    p.moveTo(*pts[0])
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 3, p1[1] + (p2[1] - p0[1]) * k / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 3, p2[1] - (p3[1] - p1[1]) * k / 3)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        p.close()
    return p


def draw(c, path, fill=None, stroke=INK, sw=4.0, fa=1.0, shader=None, sa=1.0):
    if shader is not None:
        c.drawPath(path, fillp(None, fa, shader=shader))
    elif fill is not None:
        c.drawPath(path, fillp(fill, fa))
    if stroke is not None and sw > 0:
        c.drawPath(path, strokep(stroke, sw, sa))


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return p


def rect(x, y, w, h):
    p = skia.Path()
    p.addRect(skia.Rect.MakeXYWH(x, y, w, h))
    return p


def line(c, x0, y0, x1, y1, color=INK, w=4.0, a=1.0):
    c.drawLine(x0, y0, x1, y1, strokep(color, w, a))


# ---------------- easing / timing ----------------

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def ease_io(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ramp(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def hash01(i, seed=0):
    x = math.sin(i * 127.1 + seed * 311.7) * 43758.5453
    return x - math.floor(x)


# ---------------- text ----------------

def text_w(s, f):
    return f.measureText(s)


def draw_text(c, s, x, y, f, color='#ffffff', align='left', outline=None, ow=0, a=1.0, oa=1.0):
    w = f.measureText(s)
    if align == 'center':
        x -= w / 2
    elif align == 'right':
        x -= w
    blob = skia.TextBlob.MakeFromString(s, f)
    if blob is None:
        return w
    if outline:
        p = strokep(outline, ow, oa)
        c.drawTextBlob(blob, x, y, p)
    c.drawTextBlob(blob, x, y, fillp(color, a))
    return w


# ---------------- camera ----------------

class Cam:
    """Camera looking at world point (cx,cy) with zoom z. World = 1920x1080 at z=1."""

    def __init__(self, cx=960, cy=540, z=1.0, rot=0.0):
        self.cx, self.cy, self.z, self.rot = cx, cy, z, rot

    def apply(self, c, depth=1.0):
        z = 1 + (self.z - 1) * depth
        c.translate(W / 2, H / 2)
        if self.rot:
            c.rotate(self.rot)
        c.scale(z, z)
        c.translate(-(W / 2 + (self.cx - W / 2) * depth), -(H / 2 + (self.cy - H / 2) * depth))


def cam_path(lt, dur, a, b, mode='io', drift=1.0, seed=0):
    """a,b = (cx,cy,z). mode io|out|lin|punch"""
    u = clamp(lt / max(dur, 1e-6))
    if mode == 'io':
        e = ease_io(u)
    elif mode == 'out':
        e = ease_out(u)
    elif mode == 'lin':
        e = u
    elif mode == 'settle':
        e = ease_out(clamp(u * 2.2))
    else:
        e = ease_io(u)
    cx = lerp(a[0], b[0], e)
    cy = lerp(a[1], b[1], e)
    z = lerp(a[2], b[2], e)
    # hand-held drift
    cx += drift * (6 * math.sin(lt * 0.9 + seed) + 3 * math.sin(lt * 2.3 + seed * 2))
    cy += drift * (4 * math.sin(lt * 0.7 + seed * 3) + 2 * math.sin(lt * 1.9 + seed))
    return Cam(cx, cy, z)


_vig_cache = {}


def vignette(c, strength=0.35):
    key = round(strength, 2)
    if key not in _vig_cache:
        hd = math.hypot(W / 2, H / 2)
        sh = rad(W / 2, H / 2, hd, [hexc('#000000', 0), hexc('#000000', 0), hexc('#000000', strength)],
                 [0.0, 0.45, 1.0])
        _vig_cache[key] = sh
    p = skia.Paint(AntiAlias=True)
    p.setShader(_vig_cache[key])
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def grade(c, color, a, mode='softlight'):
    p = skia.Paint()
    p.setColor(hexc(color, a))
    p.setBlendMode({'softlight': skia.BlendMode.kSoftLight, 'multiply': skia.BlendMode.kMultiply,
                    'screen': skia.BlendMode.kScreen, 'overlay': skia.BlendMode.kOverlay,
                    'normal': skia.BlendMode.kSrcOver}[mode])
    c.drawRect(skia.Rect.MakeWH(W, H), p)
