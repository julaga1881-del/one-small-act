"""1280x720 thumbnail."""
import os, math
import skia
from gfx import *
from rig import *
from sets import *

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
surf = skia.Surface(1280, 720)
c = surf.getCanvas()
c.save()
c.scale(1280 / 1920, 720 / 1080)
T = 2.0
cam = Cam(1000, 520, 1.25)
set_door(c, cam, T, 1.0, 1.0)
with layer(c, cam, 1.0):
    c.drawRect(skia.Rect.MakeXYWH(760, 400, 400, 440), fillp('#ffd38a'))
    glow(c, 960, 620, 360, '#fff1c0', 0.8)
    draw(c, rect(760, 400, 72, 440), '#2f7d4f', INK, 5)
c.restore()

c.save()
c.scale(1280 / 1920, 720 / 1080)
# three friends in generic storybook costumes, left side
def ring_up(cv, hands, u):
    if hands[1]:
        hx, hy = hands[1]
        glow(cv, hx, hy - 7 * u, 14 * u, '#fff3c0', 0.0)
        glow(cv, hx + 2 * u, hy - 9 * u, 22 * u, '#fff6d0', 0.55)
        gold_ring(cv, hx + 2 * u, hy - 9 * u, 9 * u, -8, 0.5, 0.9 * u, sparkle=1.0)
for i, (n, x, ex, hands) in enumerate((('filippo', 230, 'happy', ((-28, -60), (15, -34))),
                                      ('edoardo', 830, 'happy', ((-15, -34), (28, -60))),
                                      ('nicola', 530, 'laugh', ((-15, -34), (30, -78))))):
    sp = hobbit(CAST[n])
    draw_person(c, sp, x, 1250, 640, {'expr': ex, 'facing': 0.3, 'lhand': hands[0], 'rhand': hands[1],
                                      'hold': ring_up if n == 'nicola' else None, 'noblink': True}, T)
# Patrick's big surprised face, right
c.save()
c.translate(0, 0)
draw_person(c, CAST['patrick'], 1560, 1500, 1350, {'expr': 'surprised', 'facing': -0.35, 'noblink': True, 'mouth': 2,
                                                   'lhand': (-26, -46), 'rhand': (26, -46)}, T)
c.restore()
c.restore()

# big text
f = font(FONT_SUB, 108)
txt1, txt2 = 'THEY ', 'FOUND IT!'
w1 = f.measureText(txt1)
for (s, x, y, col) in ((txt1, 46, 128, '#ffffff'), (txt2, 46 + w1, 128, '#ffd23f')):
    draw_text(c, s, x + 6, y + 8, f, '#000000', 'left', '#000000', 26, 0.6, 0.6)
    draw_text(c, s, x, y, f, col, 'left', '#111111', 22)
# small ring arrow

# vignette
c.drawRect(skia.Rect.MakeWH(1280, 720), fillp(None, 1, shader=rad(640, 360, 760, [hexc('#000000', 0), hexc('#000000', 0), hexc('#000000', 0.45)], [0, 0.55, 1])))
surf.makeImageSnapshot().save(os.path.join(OUT, 'thumbnail.png'))
print('ok')
