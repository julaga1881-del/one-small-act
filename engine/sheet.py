import skia, sys
from gfx import *
from rig import *
s=skia.Surface(W,H); c=s.getCanvas()
c.clear(hexc('#e9e2d0'))
names=['patrick','joanne','girl1','girl2','girl3','filippo','nicola','edoardo']
x=110
for i,n in enumerate(names):
    sp=CAST[n]
    h=380*sp['hs']
    draw_person(c,sp,x+i*160,470,h,{'expr':'smile','mouth':0},T=1.0)
    draw_text(c,n,x+i*160,510,font(FONT_HAND,28),INK,'center')
for i,n in enumerate(['filippo','nicola','edoardo']):
    sp=hobbit(CAST[n])
    draw_person(c,sp,1450+i*160,470,380,{'expr':'happy','rhand':(12,-80) if i==1 else (15,-31)},T=1.0)
exprs=['neutral','happy','surprised','sad','concerned','determined','strain','tender']
for i,e in enumerate(exprs):
    draw_person(c,CAST['patrick'],110+i*160,1000,380,{'expr':e,'mouth':(i%5) if e=='neutral' else 0,'facing':0.5 if i%2 else 0},T=1.0)
    draw_text(c,e,110+i*160,1040,font(FONT_HAND,24),INK,'center')
for i,n in enumerate(['joanne','nicola']):
    draw_person(c,CAST[n],1450+i*200,1000,380,{'expr':'smile','legs':'walk','phase':1.0,'mouth':3,'facing':0.8},T=1.0)
s.makeImageSnapshot().save('/tmp/claude-0/-home-claude/cec319aa-a116-5716-8373-5faeca7260eb/scratchpad/hobbit/out/character_sheet.png')
