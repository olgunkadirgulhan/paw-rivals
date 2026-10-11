"""Kanal görselleri: banner (2560x1440), profil (800x800), filigran (150x150) — karakterler motorla çizilir."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paws
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(paws.HERE, 'channel'); os.makedirs(OUT, exist_ok=True)
paws.configure(dict(format='catdog', cat='ginger', dog='goldie', gags=['doorbell'], room='living', seed=1))
F = paws.FONT


def char(sp, f, o=None):
    img = Image.new('RGBA', (paws.L(paws.W), paws.L(paws.PH)), (0, 0, 0, 0))
    base = dict(t=0.3, f=f, x=540, look=(0.35 * f, 0.0), tail='up', wag=0)
    base.update(dict(eyes='half', mouth='smile') if sp == 'cat' else dict(eyes='wide', mouth='tongue', ears='perk'))
    base.update(o or {})
    paws.pet(img, sp, base)
    return img.crop(img.getbbox())


def fit(im, h):
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


def grad(w, h, c1, c2):
    g = Image.new('RGB', (w, h)); d = ImageDraw.Draw(g)
    for x in range(w):
        d.line([(x, 0), (x, h)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * x / w) for i in range(3)))
    return g


def text(d, xy, s, size, fill, anchor='mm'):
    f = ImageFont.truetype(F, size)
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=max(3, size // 11), stroke_fill=(28, 22, 40))


cat, dog = char('cat', 1), char('dog', -1)
# banner: güvenli alan ortada 1546x423
b = grad(2560, 1440, (250, 150, 60), (80, 140, 235))
d = ImageDraw.Draw(b)
d.polygon([(1180, 0), (1380, 0), (1380, 1440), (1180, 1440)], fill=(255, 210, 50))
c2, g2 = fit(cat, 330), fit(dog, 330)
b.paste(c2, (1280 - 790, 720 - 165 + 20), c2); b.paste(g2, (1280 + 790 - g2.width, 720 - 165 + 20), g2)
text(d, (1280, 640), 'PAW RIVALS', 150, (255, 255, 255))
text(d, (1280, 790), 'CAT vs DOG', 76, (255, 230, 70))
text(d, (1280, 880), 'NEW SHORTS EVERY DAY', 46, (255, 255, 255))
b.save(os.path.join(OUT, 'banner_2560x1440.png'))
# profil: kedi + köpek kafa kafaya
p = grad(800, 800, (250, 150, 60), (80, 140, 235)); d = ImageDraw.Draw(p)
c3, g3 = fit(cat, 440), fit(dog, 440)
p.paste(c3, (-70, 330), c3); p.paste(g3, (870 - g3.width, 330), g3)
text(d, (400, 130), 'VS', 170, (255, 230, 70))
p.save(os.path.join(OUT, 'profile_800.png'))
# filigran
w = Image.new('RGBA', (150, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(w)
d.ellipse([4, 4, 146, 146], fill=(255, 210, 50), outline=(28, 22, 40), width=6)
text(d, (75, 80), 'SUB', 44, (255, 255, 255))
w.save(os.path.join(OUT, 'watermark_150.png'))
b.resize((1280, 720)).save(os.path.join(paws.HERE, 'output', 'banner_preview.png'))
print('ok')
