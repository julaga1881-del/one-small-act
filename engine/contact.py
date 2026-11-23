import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
files = sys.argv[2:]
out = sys.argv[1]
cols = 3
w, h = 640, 360
rows = (len(files)+cols-1)//cols
sheet = Image.new('RGB', (cols*w, rows*(h+30)), (30,30,30))
d = ImageDraw.Draw(sheet)
fnt = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', 20)
for i,f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((w,h))
    x, y = (i%cols)*w, (i//cols)*(h+30)
    sheet.paste(im, (x, y+30))
    d.text((x+8, y+3), os.path.basename(f), fill=(255,255,0), font=fnt)
sheet.save(out)
