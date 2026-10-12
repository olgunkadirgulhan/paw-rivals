#!/usr/bin/env python3
"""Paw Rivals video motoru: kedi ve köpek aynı duruma nasıl tepki verir? Bölünmüş ekran "CAT vs DOG" Shorts.

Telif yok: hayvanlar, odalar, müzik ve efektlerin hepsi kodla üretilir (yardımcılar Bloop Bonkers motorundan).
Bir video = plan (format + kedi + köpek + durum listesi + oda + müzik tohumu). Planı run.py seçer.

  python paws.py --preview 3,7 [--gags doorbell,vacuum] [--cat ginger] [--dog goldie]
"""
import math, os, random, subprocess, sys, wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, S = 1080, 1920, 30, 2
TOP, PH = 170, 875
FONT = os.path.join(HERE, 'fonts', 'LuckiestGuy-Regular.ttf')
INTRO, GAG, OUTRO, NDUR = 1.4, 8.0, 3.2, 4.0
SR = 44100

DARK = (28, 22, 40)
CX, GY = 410, 800
FLOOR, TX0, TX1, TTOP = 600, 640, 1030, 540

# kediler ve köpekler: renk, ikinci renk (göğüs/ağız), göz rengi, desen
CATS = {
    'ginger': dict(name='Ginger', color=(240, 150, 60), light=(255, 225, 190), eye=(120, 200, 80), mark='tabby'),
    'shadow': dict(name='Shadow', color=(58, 56, 70), light=(95, 92, 110), eye=(250, 205, 50), mark=None),
    'mochi': dict(name='Mochi', color=(242, 240, 236), light=(255, 255, 255), eye=(90, 170, 240), mark=None),
    'smokey': dict(name='Smokey', color=(150, 152, 168), light=(220, 222, 232), eye=(250, 180, 60), mark='tabby'),
    'patches': dict(name='Patches', color=(245, 240, 230), light=(255, 255, 255), eye=(120, 200, 80), mark='calico'),
    'tux': dict(name='Tux', color=(45, 45, 55), light=(250, 250, 250), eye=(130, 210, 110), mark='tux'),
    'luna': dict(name='Luna', color=(238, 226, 205), light=(250, 245, 235), eye=(80, 150, 240), mark='points', point=(95, 70, 55)),
    'oreo': dict(name='Oreo', color=(248, 248, 248), light=(255, 255, 255), eye=(120, 200, 80), mark='cow'),
    'cocoa': dict(name='Cocoa', color=(135, 90, 60), light=(210, 175, 140), eye=(240, 190, 60), mark='tabby'),
    'pumpkin': dict(name='Pumpkin', color=(250, 175, 90), light=(255, 240, 215), eye=(100, 180, 230), mark='tux'),
}
DOGS = {
    'goldie': dict(name='Goldie', color=(228, 172, 92), light=(250, 225, 180), eye=(70, 45, 30), mark=None),
    'bruno': dict(name='Bruno', color=(140, 88, 52), light=(205, 160, 120), eye=(45, 30, 20), mark=None),
    'pepper': dict(name='Pepper', color=(245, 245, 245), light=(255, 255, 255), eye=(50, 35, 25), mark='spots'),
    'husky': dict(name='Koda', color=(120, 125, 140), light=(245, 245, 250), eye=(110, 180, 245), mark='mask'),
    'biscuit': dict(name='Biscuit', color=(210, 150, 100), light=(250, 240, 225), eye=(55, 38, 25), mark='patch'),
    'max': dict(name='Max', color=(50, 42, 38), light=(150, 100, 65), eye=(60, 40, 25), mark='mask'),
    'corgi': dict(name='Waffles', color=(235, 150, 70), light=(255, 248, 238), eye=(55, 35, 25), mark='mask'),
    'shiba': dict(name='Kenji', color=(196, 96, 46), light=(255, 240, 220), eye=(55, 35, 25), mark='mask'),
    'beagle': dict(name='Rocky', color=(200, 140, 80), light=(255, 255, 255), eye=(55, 35, 25), mark='saddle'),
    'cloud': dict(name='Cloud', color=(250, 250, 252), light=(255, 255, 255), eye=(45, 35, 30), mark=None),
}

# (üst etiket, alt etiket, kapanış sorusu, üst panel türü, alt panel türü)
FORMATS = {
    'catdog': ('CAT', 'DOG', 'TEAM CAT OR TEAM DOG?', 'cat', 'dog'),
}

PLAN = {}


def configure(plan):
    global PLAN
    PLAN = plan


def pet_def(sp):
    return CATS[PLAN.get('cat', 'ginger')] if sp == 'cat' else DOGS[PLAN.get('dog', 'goldie')]


# ---------------------------------------------------------------- yardımcılar (Bloop Bonkers motorundan)
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def seg(t, a, b): return clamp((t - a) / (b - a))
def sm(u): u = clamp(u); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def lerpc(c1, c2, u): return tuple(int(round(lerp(a, b, u))) for a, b in zip(c1, c2))
def lp(a, b, u): return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
def back(u):
    u = clamp(u); c = 1.7; v = u - 1
    return 1 + (c + 1) * v ** 3 + c * v ** 2
def spring(t, amp=1.0, f=9.0, damp=6.0):
    return amp * math.exp(-damp * t) * math.sin(f * t) if t > 0 else 0.0
def rotv(x, y, ang):  # saat yönünde (ekran koordinatı)
    a = math.radians(ang)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))
def L(v): return int(round(v * S))
def box(x0, y0, x1, y1): return [L(x0), L(y0), L(x1), L(y1)]


# ---------------------------------------------------------------- 3B sprite'lar
LIGHT = np.array([-0.45, -0.6, 0.66]); LIGHT /= np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1.0]); HALF /= np.linalg.norm(HALF)


@lru_cache(64)
def sphere_base(color, spec=0.5):
    n = 640
    y, x = np.mgrid[0:n, 0:n].astype(float)
    x = (x + 0.5) / n * 2 - 1; y = (y + 0.5) / n * 2 - 1
    d = x * x + y * y; z = np.sqrt(np.clip(1 - d, 0, 1))
    lam = np.clip(x * LIGHT[0] + y * LIGHT[1] + z * LIGHT[2], 0, 1)
    shade = 0.40 + 0.68 * lam
    rim = np.clip(1 - z, 0, 1) ** 3 * 0.15
    bounce = np.clip(y, 0, 1) * (1 - z) * 0.22
    sp = np.clip(x * HALF[0] + y * HALF[1] + z * HALF[2], 0, 1) ** 60 * spec
    c = np.array(color, float) / 255
    rgb = c * shade[..., None] + (bounce + rim)[..., None] * np.array([1.0, 0.95, 0.9]) * c + sp[..., None]
    a = np.clip((1 - np.sqrt(d)) * n * 0.5, 0, 1)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8))


def sphere(color, w, h, spec=0.5):
    return sphere_base(tuple(color), spec).resize((max(1, L(w)), max(1, L(h))), Image.BILINEAR)


@lru_cache(None)
def cyl(color, w, h, rad=0, spec=0.35):
    pw, ph = L(w), L(h)
    x = (np.arange(pw) + 0.5) / pw * 2 - 1
    z = np.sqrt(np.clip(1 - x * x, 0, 1))
    lam = np.clip(x * LIGHT[0] + z * LIGHT[2] + 0.25, 0, 1)
    shade = 0.42 + 0.6 * lam
    sp = np.clip(x * HALF[0] + z * HALF[2], 0, 1) ** 30 * spec
    row = np.clip(np.array(color, float) / 255 * shade[:, None] + sp[:, None], 0, 1)
    vy = np.linspace(1.06, 0.9, ph)[:, None, None]
    rgb = np.clip(row[None, :, :] * vy, 0, 1) * 255
    m = Image.new('L', (pw, ph), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=L(rad), fill=255)
    im = Image.fromarray(rgb.astype(np.uint8)).convert('RGBA'); im.putalpha(m)
    return im


@lru_cache(None)
def shadow_base():
    m = Image.new('L', (256, 128), 0); ImageDraw.Draw(m).ellipse([24, 24, 232, 104], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(14))
    im = Image.new('RGBA', (256, 128), (0, 0, 0, 0)); im.putalpha(m.point(lambda a: int(a * 0.4)))
    return im


def put(img, spr, cx, cy):
    img.paste(spr, (int(round(cx * S - spr.width / 2)), int(round(cy * S - spr.height / 2))), spr)
def put_sphere(img, color, cx, cy, w, h, spec=0.5): put(img, sphere(color, w, h, spec), cx, cy)
def put_rot(img, spr, cx, cy, ang):
    put(img, spr.rotate(-ang, resample=Image.BICUBIC, expand=True) if ang else spr, cx, cy)
def put_shadow(img, cx, cy, w, h):
    put(img, shadow_base().resize((max(1, L(w)), max(1, L(h))), Image.BILINEAR), cx, cy)
def fade(spr, k):
    s = spr.copy(); s.putalpha(spr.getchannel('A').point(lambda a: int(a * k))); return s
def scaled(spr, s):
    return spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.BILINEAR)


def particles(img, seed, t0, tt, n, origin, vx, vy, g, colors, size, life=2.0, emit=0.0):
    """Basit fizik parçacıkları. emit>0 ise parçacıklar emit saniye boyunca sırayla çıkar."""
    rnd = random.Random(seed)
    for k in range(n):
        te = t0 + (emit * k / n if emit else 0)
        c = rnd.choice(colors); ux, uy = rnd.uniform(*vx), rnd.uniform(*vy); s = rnd.uniform(*size)
        age = tt - te
        if 0 <= age < life:
            x = origin[0] + ux * age; y = origin[1] + uy * age + 0.5 * g * age * age
            if -60 < y < PH + 60: put_sphere(img, c, x, y, s, s, 0.6)


# ---------------------------------------------------------------- yazı
@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, sz)


@lru_cache(None)
def text_spr(txt, sz, fill, stroke=DARK):
    sw = max(2, sz // 9); f = font(sz); bb = f.getbbox(txt, stroke_width=sw)
    im = Image.new('RGBA', (bb[2] - bb[0] + 6, bb[3] - bb[1] + 6), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((3 - bb[0], 3 - bb[1]), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return im


def put_text_px(img, txt, x, y, sz, fill, scale=1.0, rot=0, max_w=None):
    if scale <= 0.02: return
    spr = text_spr(txt, sz, fill)
    if max_w and spr.width > max_w: scale *= max_w / spr.width
    if scale != 1: spr = scaled(spr, scale)
    if rot: spr = spr.rotate(-rot, resample=Image.BICUBIC, expand=True)
    img.paste(spr, (int(x - spr.width / 2), int(y - spr.height / 2)), spr)


def put_text(img, txt, cx, cy, sz, fill, scale=1.0, rot=0, max_w=None):
    put_text_px(img, txt, L(cx), L(cy), L(sz), fill, scale, rot, L(max_w) if max_w else None)


# ---------------------------------------------------------------- sahne
ROOMS = ('living', 'kitchen', 'bedroom', 'office', 'bathroom', 'garage', 'cafe', 'library', 'gym', 'diner', 'arcade', 'studio', 'greenhouse', 'spaceship', 'hotel')
FLOORS = {'living': (196, 138, 88), 'kitchen': (214, 204, 186), 'bedroom': (176, 120, 150), 'office': (150, 152, 165),
          'bathroom': (225, 228, 238), 'garage': (128, 128, 134), 'cafe': (150, 100, 70),
          'library': (120, 80, 55), 'gym': (70, 72, 80), 'diner': (235, 235, 235),
          'arcade': (60, 42, 80), 'studio': (105, 90, 82), 'greenhouse': (150, 132, 100), 'spaceship': (140, 145, 158), 'hotel': (150, 40, 52)}


@lru_cache(None)
def background(wall, room='living'):
    w, h = L(W), L(PH)
    yy = np.arange(h)[:, None] / S; xx = np.arange(w)[None, :] / S
    k = 0.84 + 0.2 * (yy / FLOOR)
    if room == 'bedroom':      # puantiyeli duvar kâğıdı
        stripe = ((((xx + 30 * ((yy // 60) % 2)) % 60 - 30) ** 2 + ((yy % 60) - 30) ** 2) < 49) * 0.06
    elif room == 'office':
        stripe = 0.0 * xx
    elif room == 'bathroom':   # tam duvar fayans
        stripe = (((xx % 60) < 3) | ((yy % 60) < 3)) * -0.10 + 0.0 * yy
    elif room == 'garage':     # beton paneller
        stripe = ((xx // 160) % 2) * -0.03 + (((xx % 160) < 3) * -0.08) + 0.0 * yy
    elif room == 'arcade':     # karanlık + neon şeritler
        stripe = -0.5 + (((yy % 120) < 6) * 0.9) + 0.0 * xx
    elif room == 'studio':     # akustik sünger
        stripe = ((((xx % 50) - 25) ** 2 + ((yy % 50) - 25) ** 2) < 200) * -0.12 - 0.15
    elif room == 'greenhouse': # cam paneller
        stripe = (((xx % 140) < 5) | ((yy % 140) < 5)) * 0.18 + 0.05 + 0.0 * yy
    elif room == 'spaceship':  # metal paneller + perçin
        stripe = (((xx % 180) < 4) | ((yy % 120) < 4)) * -0.2 + ((((xx % 180) - 14) ** 2 + ((yy % 120) - 14) ** 2) < 20) * -0.3 - 0.1
    elif room == 'hotel':      # geniş altın çizgiler
        stripe = (((xx // 45) % 3) == 0) * 0.08 + ((yy > 420) & (yy < 430)) * -0.3
    elif room == 'library':    # ahşap lambri
        stripe = ((xx % 90) < 4) * -0.18 + (yy > 380) * -0.10
    elif room == 'gym':
        stripe = ((yy > 360) & (yy < 400)) * 0.25 + 0.0 * xx
    elif room == 'diner':      # alt duvar dama
        stripe = ((yy > 380) & (((xx // 50) + (yy // 50)) % 2 == 0)) * -0.35 + 0.0 * xx
    elif room == 'cafe':       # tuğla
        stripe = (((yy % 40) < 4) | (((xx + 40 * ((yy // 40) % 2)) % 80) < 4)) * -0.16 + ((xx * 7 + (yy // 40) * 13) % 5 == 0) * 0.0
    elif room == 'kitchen':    # alt duvarda fayans
        stripe = ((yy > 380) & (((xx % 70) < 3) | ((yy % 70) < 3))) * -0.12
    else:
        stripe = ((xx // 60) % 2 == 0) * 0.035
    rgb_w = np.array(wall, float) * (k + stripe)[..., None]
    fy = np.clip((yy - FLOOR) / (PH - FLOOR), 0, 1)
    rgb_f = np.array(FLOORS.get(room, FLOORS['living']), float) * (0.8 + 0.28 * fy)[..., None] * np.ones_like(xx)[..., None]
    rgb = np.where((yy < FLOOR)[..., None], rgb_w, rgb_f)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(img)
    for y in (628, 662, 706, 760, 826):
        d.line(box(0, y, W, y), fill=(150, 100, 60), width=L(2))
    d.rectangle(box(0, FLOOR - 18, W, FLOOR + 2), fill=(246, 240, 232))
    d.line(box(0, FLOOR + 2, W, FLOOR + 2), fill=(170, 150, 130), width=L(3))
    d.rounded_rectangle(box(660, 60, 960, 330), radius=L(14), fill=(250, 250, 248))
    for i in range(0, 250):
        d.line(box(676, 76 + i, 944, 76 + i), fill=lerpc((120, 190, 250), (205, 235, 255), i / 250))
    for cx_, cy_, s in ((740, 150, 1.0), (880, 230, 0.7)):
        for dx, dy, r in ((-30, 8, 26), (0, 0, 36), (32, 8, 26)):
            d.ellipse(box(cx_ + dx * s - r * s, cy_ + dy * s - r * s, cx_ + dx * s + r * s, cy_ + dy * s + r * s), fill=(255, 255, 255))
    if room == 'office':       # pencerede şehir
        for k_, (bx, bh) in enumerate(((690, 120), (740, 170), (800, 90), (850, 150), (905, 110))):
            d.rectangle(box(bx, 326 - bh, bx + 44, 326), fill=(150, 165, 190))
            for wy in range(int(326 - bh + 12), 316, 26):
                d.rectangle(box(bx + 10, wy, bx + 18, wy + 10), fill=(255, 240, 170)); d.rectangle(box(bx + 26, wy, bx + 34, wy + 10), fill=(255, 240, 170))
    d.rectangle(box(806, 76, 814, 314), fill=(250, 250, 248)); d.rectangle(box(676, 195, 944, 203), fill=(250, 250, 248))
    if room == 'kitchen':      # üst dolap
        for x0 in (40, 190):
            d.rounded_rectangle(box(x0, 50, x0 + 140, 260), radius=L(8), fill=(245, 245, 240), outline=(170, 160, 150), width=L(3))
            d.rounded_rectangle(box(x0 + 110, 140, x0 + 120, 190), radius=L(4), fill=(150, 150, 160))
    elif room == 'bedroom':    # yıldızlı poster
        d.rounded_rectangle(box(70, 80, 250, 300), radius=L(6), fill=(60, 50, 110))
        for sx_, sy_, r_ in ((120, 140, 10), (200, 120, 7), (160, 220, 14), (220, 260, 6), (100, 270, 8)):
            d.ellipse(box(sx_ - r_, sy_ - r_, sx_ + r_, sy_ + r_), fill=(255, 230, 120))
        d.ellipse(box(170, 140, 230, 200), fill=(250, 245, 220)); d.ellipse(box(188, 132, 244, 188), fill=(60, 50, 110))
    elif room == 'bathroom':   # ayna
        d.ellipse(box(60, 60, 260, 320), fill=(200, 200, 205)); d.ellipse(box(74, 74, 246, 306), fill=(200, 230, 245))
        d.line(box(110, 120, 150, 90), fill=(255, 255, 255), width=L(8)); d.line(box(110, 170, 190, 100), fill=(255, 255, 255), width=L(6))
    elif room == 'garage':     # alet panosu
        d.rectangle(box(40, 70, 300, 330), fill=(175, 140, 100))
        for yh in range(85, 330, 24):
            for xh in range(55, 300, 24): d.ellipse(box(xh - 3, yh - 3, xh + 3, yh + 3), fill=(120, 95, 70))
        d.rectangle(box(80, 110, 92, 230), fill=(120, 80, 50)); d.rectangle(box(62, 100, 110, 130), fill=(110, 110, 120))
        d.rectangle(box(170, 110, 182, 260), fill=(150, 150, 160)); d.ellipse(box(158, 92, 194, 128), outline=(150, 150, 160), width=L(10))
        d.rounded_rectangle(box(220, 120, 280, 280), radius=L(8), fill=(220, 60, 50))
    elif room == 'arcade':     # oyun makinesi
        d.rounded_rectangle(box(60, 60, 280, 360), radius=L(16), fill=(30, 20, 60), outline=(80, 220, 255), width=L(6))
        d.rectangle(box(90, 100, 250, 220), fill=(20, 200, 140)); d.rectangle(box(110, 130, 140, 150), fill=(255, 230, 60))
        d.ellipse(box(180, 150, 210, 180), fill=(255, 80, 150))
        for x in (110, 150, 190, 230): d.ellipse(box(x - 12, 260, x + 12, 284), fill=(255, 80, 150) if x % 80 else (80, 220, 255))
    elif room == 'studio':     # ON AIR
        d.rounded_rectangle(box(70, 150, 300, 250), radius=L(14), fill=(200, 30, 40), outline=(255, 120, 120), width=L(6))
        f_ = font(L(54)); tw = d.textlength('ON AIR', font=f_); d.text((L(185) - tw / 2, L(176)), 'ON AIR', font=f_, fill=(255, 255, 255))
    elif room == 'greenhouse': # asılı saksılar
        for x, yb in ((110, 210), (230, 260)):
            d.line(box(x, 40, x, yb - 40), fill=(90, 70, 50), width=L(4))
            d.rounded_rectangle(box(x - 40, yb - 40, x + 40, yb + 10), radius=L(10), fill=(200, 100, 60))
            for k in range(5): d.ellipse(box(x - 60 + k * 26, yb - 70 + (k % 2) * 16, x - 20 + k * 26, yb - 30 + (k % 2) * 16), fill=(70, 170, 80))
    elif room == 'spaceship':  # lomboz + kontrol paneli
        d.ellipse(box(684, 64, 936, 336), fill=(12, 12, 32), outline=(170, 175, 190), width=L(16))
        for k in range(14):
            r_ = random.Random(k); sx_, sy_ = r_.uniform(720, 900), r_.uniform(100, 300); rr = r_.uniform(2, 5)
            d.ellipse(box(sx_ - rr, sy_ - rr, sx_ + rr, sy_ + rr), fill=(255, 255, 230))
        d.ellipse(box(820, 220, 880, 280), fill=(230, 120, 70))
        d.rounded_rectangle(box(50, 120, 300, 280), radius=L(12), fill=(50, 55, 70))
        for k in range(8): d.ellipse(box(75 + (k % 4) * 55, 150 + (k // 4) * 60, 105 + (k % 4) * 55, 180 + (k // 4) * 60), fill=[(255, 80, 80), (80, 220, 120), (255, 220, 60), (80, 170, 255)][k % 4])
    elif room == 'hotel':      # altın çerçeveli tablo
        d.rectangle(box(60, 80, 290, 300), fill=(200, 160, 60)); d.rectangle(box(78, 98, 272, 282), fill=(70, 110, 150))
        d.polygon([(L(78), L(282)), (L(150), L(170)), (L(200), L(230)), (L(272), L(150)), (L(272), L(282))], fill=(60, 130, 90))
    elif room == 'library':    # büyük kitaplık
        d.rectangle(box(30, 40, 320, 360), fill=(95, 60, 40))
        for shelf in (40, 120, 200, 280):
            d.rectangle(box(30, shelf + 72, 320, shelf + 80), fill=(70, 45, 30))
            x = 40
            for j in range(9):
                bw = 20 + (j * 7 + shelf) % 12; bh = 50 + (j * 13 + shelf) % 18
                d.rectangle(box(x, shelf + 72 - bh, x + bw, shelf + 72), fill=[(150, 50, 50), (50, 90, 150), (190, 150, 60), (60, 120, 80), (110, 70, 140)][(j + shelf // 40) % 5])
                x += bw + 4
    elif room == 'gym':        # motivasyon posteri
        d.rounded_rectangle(box(50, 70, 290, 320), radius=L(8), fill=(30, 30, 35), outline=(255, 210, 50), width=L(6))
        for i_, (tx, sz_) in enumerate((('NO', 40), ('PAIN', 46), ('NO', 40), ('GAIN', 46))):
            f_ = font(L(sz_)); tw = d.textlength(tx, font=f_)
            d.text((L(170) - tw / 2, L(95 + i_ * 54)), tx, font=f_, fill=(255, 210, 50) if i_ % 2 else (255, 255, 255))
    elif room == 'diner':      # neon tabela
        d.rounded_rectangle(box(70, 150, 310, 290), radius=L(20), fill=(40, 30, 50), outline=(255, 80, 150), width=L(8))
        f_ = font(L(76)); tw = d.textlength('EAT', font=f_)
        d.text((L(190) - tw / 2, L(176)), 'EAT', font=f_, fill=(255, 120, 190))
    elif room == 'cafe':       # tebeşir menü
        d.rounded_rectangle(box(40, 70, 300, 330), radius=L(8), fill=(120, 80, 50))
        d.rectangle(box(54, 84, 286, 316), fill=(40, 50, 45))
        bloop_menu = [(170, 120, 'MENU'), (170, 190, 'coffee ~ 3'), (170, 240, 'cake ~ 4'), (170, 290, 'tea ~ 2')]
        for x_, y_, tx in bloop_menu:
            f_ = font(L(30 if tx == 'MENU' else 22)); tw = d.textlength(tx, font=f_)
            d.text((L(x_) - tw / 2, L(y_) - L(16)), tx, font=f_, fill=(235, 235, 225))
    elif room == 'office':     # kitaplık
        d.rectangle(box(50, 60, 280, 340), fill=(130, 90, 60))
        for shelf in (60, 150, 240):
            d.rectangle(box(50, shelf + 82, 280, shelf + 90), fill=(100, 65, 40))
            x = 62
            for j in range(7):
                bw = 22 + (j * 7) % 13; bh = 58 + (j * 11) % 20
                d.rectangle(box(x, shelf + 82 - bh, x + bw, shelf + 82), fill=[(200, 70, 70), (70, 120, 200), (240, 190, 60), (90, 170, 110), (160, 100, 190)][(j + shelf) % 5])
                x += bw + 5
    else:
        d.rounded_rectangle(box(60, 90, 240, 240), radius=L(6), fill=(120, 80, 50))
        d.rectangle(box(74, 104, 226, 226), fill=(170, 220, 240))
        d.polygon([(L(74), L(226)), (L(130), L(150)), (L(170), L(200)), (L(200), L(170)), (L(226), L(226))], fill=(90, 170, 90))
        d.ellipse(box(180, 118, 210, 148), fill=(255, 210, 60))
    put_shadow(img, (TX0 + TX1) / 2, GY + 6, 470, 46)
    for x in (TX0 + 30, TX1 - 30):
        put(img, cyl((120, 72, 40), 26, 250, 6), x, 690)
    d.rounded_rectangle(box(TX0 - 12, TTOP - 10, TX1 + 12, TTOP + 14), radius=L(10), fill=(212, 148, 92))
    d.rounded_rectangle(box(TX0 - 12, TTOP + 8, TX1 + 12, TTOP + 40), radius=L(8), fill=(150, 90, 50))
    d.line(box(TX0 - 4, TTOP + 10, TX1 + 4, TTOP + 10), fill=(230, 175, 120), width=L(3))
    return img




def bg(wall, v):
    room = PLAN.get('room', 'living') if PLAN else 'living'
    return background(wall if v == 'cat' else lerpc(wall, (90, 120, 170), 0.18), room).copy()


# ---------------------------------------------------------------- hayvan
def lighten(c, k): return lerpc(c, (255, 255, 255), k)
def darken(c, k): return lerpc(c, (0, 0, 0), k)


def tail(img, sp, base, f, k, o, col):
    cat = sp == 'cat'
    mode = o.get('tail', 'up'); t = o.get('t', 0.0); wag = o.get('wag', 0.0); ws = o.get('ws', 14.0)
    puff = o.get('puff', 0.0)
    a0, curl = {'up': (72, 45) if cat else (58, 12), 'down': (-25, -25), 'tuck': (-70, -70),
                'puff': (88, 6)}[mode if mode in ('up', 'down', 'tuck', 'puff') else 'up']
    n, step, rad = (30, 6.5, 26) if cat else (18, 6.5, 34)
    rad *= k * (1 + 1.1 * puff); step *= k
    x, y = base
    for i in range(n):
        u = i / (n - 1)
        a = math.radians(a0 + curl * u + wag * math.sin(t * ws - u * 1.6) * (0.3 + u))
        x += -f * math.cos(a) * step; y += -math.sin(a) * step
        r = rad * (1 - 0.25 * u) if cat else rad * (1 - 0.45 * u)
        put_sphere(img, col if not (cat and o.get('tip') and i > n - 4) else o['tip'], x, y, r, r, 0.3)
    return (x, y)


def leg(img, col, x, top, bottom, ang, w):
    h = max(10, bottom - top)
    put_rot(img, cyl(col, w, h, w / 2 - 1), x, (top + bottom) / 2, ang)
    dx = math.sin(math.radians(ang)) * h / 2
    put_sphere(img, lighten(col, 0.12), x - dx, bottom - 4, w * 1.25, w * 0.7, 0.3)


def eye(img, sp, ex, ey, k, mode, look, iris, headc):
    d = ImageDraw.Draw(img)
    lx, ly = look
    if mode == 'closed':
        d.arc(box(ex - 26 * k, ey - 18 * k, ex + 26 * k, ey + 18 * k), 20, 160, fill=DARK, width=L(6 * k)); return
    if mode == 'happy':
        d.arc(box(ex - 26 * k, ey - 8 * k, ex + 26 * k, ey + 30 * k), 200, 340, fill=DARK, width=L(7 * k)); return
    if mode == 'hearts':
        for dx in (-11, 11):
            put_sphere(img, (235, 50, 80), ex + dx * k, ey - 6 * k, 30 * k, 30 * k, 0.6)
        d.polygon([(L(ex - 26 * k), L(ey - 2 * k)), (L(ex + 26 * k), L(ey - 2 * k)), (L(ex), L(ey + 28 * k))], fill=(235, 50, 80))
        return
    big = mode in ('wide', 'tiny')
    ew, eh = (68, 76) if big else (58, 66)
    put_sphere(img, (252, 252, 252), ex, ey, ew * k, eh * k, 0.25)
    if mode == 'tiny':
        put_sphere(img, DARK, ex + lx * 8 * k, ey + ly * 8 * k, 13 * k, 15 * k, 0.1)
    else:
        ix, iy = ex + lx * 9 * k, ey + ly * 9 * k
        put_sphere(img, iris, ix, iy, (52 if big else 44) * k, (58 if big else 50) * k, 0.5)
        if sp == 'cat' and not big:
            put_sphere(img, DARK, ix, iy, 13 * k, 40 * k, 0.1)
        else:
            put_sphere(img, DARK, ix, iy, (38 if big else 28) * k, (42 if big else 32) * k, 0.1)
        put_sphere(img, (255, 255, 255), ix - 9 * k, iy - 12 * k, 13 * k, 13 * k, 0.0)
        if big: put_sphere(img, (255, 255, 255), ix + 9 * k, iy + 9 * k, 7 * k, 7 * k, 0.0)
    if mode in ('half', 'angry'):
        top = ey - eh * k / 2 - 4 * k
        if mode == 'half':
            d.chord(box(ex - ew * k / 2 - 4, ey - eh * k / 2 - 4, ex + ew * k / 2 + 4, ey + eh * k / 2 + 4), 180, 360, fill=headc)
            d.line(box(ex - ew * k / 2 - 2, ey, ex + ew * k / 2 + 2, ey), fill=DARK, width=L(5 * k))
        else:
            s = 1 if ex > o_cx[0] else -1
            pts = [(ex - ew * k / 2 - 4, top - 6), (ex + ew * k / 2 + 4, top - 6),
                   (ex + ew * k / 2 + 4, ey - (14 if s < 0 else -4) * k), (ex - ew * k / 2 - 4, ey - (-4 if s < 0 else 14) * k)]
            d.polygon([(L(a), L(b)) for a, b in pts], fill=headc)
            d.line([(L(pts[3][0]), L(pts[3][1])), (L(pts[2][0]), L(pts[2][1]))], fill=DARK, width=L(6 * k))


o_cx = [0.0]


def pet(img, sp, o):
    """Kedi/köpek çizer. o: x, gy, jump, f (yön), sx, sy, eyes, look, mouth, mo, ears, tail, wag, puff,
    walk (faz), run (0-1), paw (ön pati kaldırma 0-1), lie (yatış 0-1), wet, head_dx/dy, scale, t."""
    df = pet_def(sp); cat = sp == 'cat'
    k = o.get('scale', 1.0); f = o.get('f', 1); x = o.get('x', CX); gy = o.get('gy', GY); jump = o.get('jump', 0.0)
    sx, sy = o.get('sx', 1.0), o.get('sy', 1.0); puff = o.get('puff', 0.0); wet = o.get('wet', 0.0)
    lie = o.get('lie', 0.0); t = o.get('t', 0.0)
    if SPEAKER[0] == sp:   # dudak senkronu: replik sırasında ağız sesle açılır
        lvl = speaking(t)
        if lvl > 0.12: o = dict(o, mouth='open', mo=min(1.0, 0.35 + 0.9 * lvl))
    col, light = df['color'], df['light']
    if wet:
        col = lerpc(col, (70, 85, 110), 0.35 * wet); light = lerpc(light, (150, 165, 190), 0.35 * wet)
    pf = 1 + 0.16 * puff
    bw, bh = 290 * k * sx * pf, (148 if cat else 165) * k * sy * pf
    legh = 74 * k * (1 - lie)
    by = gy - legh - bh * 0.42 - jump + (bh * 0.1 * lie)
    put_shadow(img, x, gy + 4, bw * 1.1 * max(0.35, 1 - jump / 600), 42 * k)
    tcol = df.get('point', col) if df.get('mark') == 'points' else col
    tip = df['light'] if df.get('mark') in ('tux',) else None
    tail(img, sp, (x - f * bw * 0.42, by - bh * 0.12), f, k, dict(o, tip=tip), tcol)
    # bacaklar (uzak çift koyu, arkada)
    ph = o.get('walk'); run = o.get('run', 0.0); paw = o.get('paw', 0.0)
    sw = (lambda s: 22 * math.sin(ph + s)) if ph is not None else (lambda s: 0.0)
    lw = 50 * k
    feet = gy - jump
    top = by + bh * 0.05
    legs = []  # (x, ang, near, front)
    for front in (1, -1):
        lx = x + f * front * bw * 0.30
        for near in (0, 1):
            s = (0 if front > 0 else math.pi) + (math.pi if near else 0)
            ang = f * (sw(s) + front * 32 * run)
            legs.append((lx + f * (10 if not near else -6) * k, ang, near, front))
    if legh > 8:
        for lx, ang, near, front in legs:
            if not near: leg(img, darken(col, 0.18), lx, top, feet - (2 if jump else 0), ang, lw)
    if puff > 0.05:  # kabarmış tüyler
        rnd = random.Random(7)
        for j in range(26):
            a = j / 26 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
            r0x, r0y = bw / 2 * 0.86, bh / 2 * 0.86
            cxs, cys = x + math.cos(a) * r0x, by + math.sin(a) * r0y
            tipx, tipy = x + math.cos(a) * (r0x + 46 * k * puff), by + math.sin(a) * (r0y + 46 * k * puff)
            n_ = (-math.sin(a) * 16 * k, math.cos(a) * 16 * k)
            ImageDraw.Draw(img).polygon([(L(cxs + n_[0]), L(cys + n_[1])), (L(tipx), L(tipy)),
                                         (L(cxs - n_[0]), L(cys - n_[1]))], fill=col)
    put_sphere(img, col, x, by, bw, bh, 0.35)
    mark = df.get('mark')
    put_sphere(img, light, x + f * bw * 0.24, by + bh * 0.16, bw * (0.5 if mark == 'tux' else 0.4), bh * 0.56, 0.2)
    if mark == 'spots':
        for dx, dy, r in ((-0.25, -0.2, 34), (0.05, -0.28, 26), (-0.05, 0.08, 22), (-0.32, 0.12, 20), (0.18, -0.05, 18)):
            put_sphere(img, (40, 40, 45), x + f * dx * bw, by + dy * bh, r * k, r * k * 0.85, 0.2)
    elif mark == 'calico':
        put_sphere(img, (235, 140, 60), x - f * bw * 0.2, by - bh * 0.15, bw * 0.38, bh * 0.5, 0.2)
        put_sphere(img, (50, 45, 50), x + f * bw * 0.05, by - bh * 0.3, bw * 0.24, bh * 0.3, 0.2)
    elif mark == 'cow':
        for dx, dy, r in ((-0.22, -0.18, 70), (0.12, -0.25, 46), (-0.34, 0.1, 40)):
            put_sphere(img, (40, 40, 48), x + f * dx * bw, by + dy * bh, r * k, r * k * 0.8, 0.2)
    elif mark == 'saddle':
        put_sphere(img, (40, 36, 34), x - f * bw * 0.08, by - bh * 0.22, bw * 0.62, bh * 0.5, 0.25)
    elif mark == 'tabby':
        d = ImageDraw.Draw(img)
        for j in range(4):
            sxj = x - f * bw * (0.32 - j * 0.15)
            d.arc(box(sxj - 26 * k, by - bh * 0.5, sxj + 26 * k, by - bh * 0.05), 200 if f > 0 else 250, 290 if f > 0 else 340,
                  fill=darken(col, 0.28), width=L(9 * k))
    if legh > 8:
        for lx, ang, near, front in legs:
            if near:
                if front > 0 and paw > 0:
                    px, py = lx + f * 70 * k * paw, feet - 110 * k * paw
                    leg(img, col, (lx + px) / 2, top, py, f * -55 * paw, lw)
                else:
                    leg(img, col, lx, top, feet - (2 if jump else 0), ang, lw)
    # kafa
    hw, hh = (236 if cat else 240) * k, (214 if cat else 222) * k
    hx = x + f * bw * 0.40 + o.get('head_dx', 0.0) * k
    hy = by - bh * 0.5 - 46 * k + o.get('head_dy', 0.0) * k + lie * 30 * k
    o_cx[0] = hx
    ears = o.get('ears', 'up')
    d = ImageDraw.Draw(img)
    if cat:
        for s in (-1, 1):
            if ears == 'flat': tipx, tipy = hx + s * 132 * k, hy - 64 * k
            elif ears == 'back': tipx, tipy = hx + s * 118 * k, hy - 118 * k
            else: tipx, tipy = hx + s * 84 * k, hy - 172 * k
            b1 = (hx + s * 22 * k, hy - 88 * k); b2 = (hx + s * 102 * k, hy - 38 * k)
            d.polygon([(L(b1[0]), L(b1[1])), (L(tipx), L(tipy)), (L(b2[0]), L(b2[1]))], fill=df.get('point', darken(col, 0.06)))
            ix_, iy_ = lerp(b1[0], b2[0], 0.5), lerp(b1[1], b2[1], 0.5)
            d.polygon([(L(lerp(b1[0], ix_, 0.35)), L(lerp(b1[1], iy_, 0.35))), (L(lerp(ix_, tipx, 0.72)), L(lerp(iy_, tipy, 0.72))),
                       (L(lerp(b2[0], ix_, 0.35)), L(lerp(b2[1], iy_, 0.35)))], fill=(250, 170, 185))
    put_sphere(img, col, hx, hy, hw, hh, 0.35)
    if mark == 'calico':
        put_sphere(img, (235, 140, 60), hx - 50 * k, hy - 50 * k, 110 * k, 90 * k, 0.2)
    if mark == 'points':
        put_sphere(img, df['point'], hx + f * 6 * k, hy + 26 * k, 170 * k, 150 * k, 0.2)
    if mark == 'cow':
        put_sphere(img, (40, 40, 48), hx + 52 * k, hy - 46 * k, 100 * k, 84 * k, 0.2)
    if mark == 'patch':
        put_sphere(img, darken(col, 0.35), hx + 48 * k, hy - 10 * k, 96 * k, 92 * k, 0.2)
    if mark in ('mask', 'tux') or not cat:
        put_sphere(img, light, hx + f * 6 * k, hy + 52 * k, (150 if cat else 172) * k, (96 if cat else 112) * k, 0.2)
    if mark == 'tabby':
        for dx in (-22, 0, 22):
            d.line(box(hx + dx * k, hy - 100 * k, hx + dx * 0.6 * k, hy - 64 * k), fill=darken(col, 0.28), width=L(8 * k))
    look = o.get('look', (0.25 * f, 0.0)); em = o.get('eyes', 'open')
    for s in (-1, 1):
        eye(img, sp, hx + s * 50 * k + f * 6 * k, hy - 8 * k, k, em, look, df['eye'], col)
    if not cat:  # sarkık kulaklar
        flop = o.get('flop', 0.0) + (8 * math.sin(t * 20) if jump > 5 else 0) + (-35 if ears == 'perk' else 0)
        for s in (-1, 1):
            spr = sphere(darken(col, 0.22) if mark != 'spots' else (45, 45, 50), 78 * k, 150 * k, 0.25)
            put_rot(img, spr, hx + s * 112 * k, hy + 6 * k + (flop if ears == 'perk' else 0) * k, s * (18 + flop))
    my = hy + 66 * k
    mouth = o.get('mouth', 'smile'); mo = o.get('mo', 1.0)
    nx = hx + f * 6 * k
    if cat:
        d.polygon([(L(nx - 13 * k), L(hy + 30 * k)), (L(nx + 13 * k), L(hy + 30 * k)), (L(nx), L(hy + 44 * k))], fill=(240, 120, 150))
        for s in (-1, 1):
            for j, dy in enumerate((-4, 8, 20)):
                d.line(box(nx + s * 48 * k, hy + 42 * k + dy * 0.4 * k, nx + s * 128 * k, hy + 28 * k + dy * k * 1.4),
                       fill=(250, 250, 250) if col[0] < 120 else (70, 60, 60), width=L(3 * k))
        my = hy + 60 * k
    else:
        put_sphere(img, (30, 26, 30), nx, hy + 30 * k, 56 * k, 40 * k, 0.8)
        my = hy + 76 * k
    if mouth == 'smile':
        for s in (-1, 1):
            d.arc(box(nx + (s - 1) * 15 * k, my - 18 * k, nx + (s + 1) * 15 * k, my + 10 * k), 10, 170, fill=DARK, width=L(5 * k))
    elif mouth == 'flat':
        d.line(box(nx - 20 * k, my, nx + 20 * k, my), fill=DARK, width=L(5 * k))
    elif mouth in ('open', 'tongue', 'hiss', 'o'):
        mw, mh = {'open': (46, 52), 'tongue': (56, 46), 'hiss': (82, 50), 'o': (26, 28)}[mouth]
        mw, mh = mw * k * (0.5 + 0.5 * mo), mh * k * mo
        put_sphere(img, (90, 25, 40), nx, my + mh * 0.2, mw, max(4, mh), 0.1)
        if mouth in ('open', 'hiss'):
            put_sphere(img, (240, 110, 140), nx, my + mh * 0.45, mw * 0.6, max(3, mh * 0.35), 0.3)
        if mouth == 'hiss':
            for s in (-1, 1):
                d.polygon([(L(nx + s * 26 * k), L(my - mh * 0.28)), (L(nx + s * 14 * k), L(my - mh * 0.28)),
                           (L(nx + s * 20 * k), L(my + 6 * k))], fill=(255, 255, 255))
        if mouth == 'tongue':
            put_sphere(img, (245, 105, 135), nx + f * 4 * k, my + 30 * k + 4 * math.sin(t * 18) * k, 34 * k, 50 * k, 0.4)
    if wet:
        rnd = random.Random(int(t * 3))
        for j in range(6):
            dx = rnd.uniform(-bw / 2, bw / 2); age = (t * 2.2 + j * 0.17) % 1
            put_sphere(img, (120, 190, 250), x + dx, by + bh * 0.4 + age * (gy - by), 12 * k, 18 * k, 0.8)
    return dict(hx=hx, hy=hy, my=my, by=by, bw=bw, bh=bh, nose=(nx, hy + 30 * k),
                paw=(x + f * bw * 0.30 + f * 70 * k * paw, feet - 110 * k * paw))


# ---------------------------------------------------------------- ortak efektler
def pop(img, txt, x, y, t0, tt, col=(255, 255, 255), size=96, rot=-8, life=99.0):
    if t0 <= tt < t0 + life:
        put_text(img, txt, x, y, size, col, scale=back(seg(tt, t0, t0 + 0.22)), rot=rot)


def zzz(img, tt, x, y):
    for j in range(3):
        u = (tt * 0.6 + j / 3) % 1
        put_text(img, 'Z', x + 30 * u + j * 10, y - 120 * u, 40 + 30 * u, (255, 255, 255), scale=min(1, u * 4) * (1 - u) * 1.6)


def stars(img, tt, x, y):
    for j in range(5):
        a = tt * 5 + j / 5 * 2 * math.pi
        put_sphere(img, (255, 225, 60), x + math.cos(a) * 90, y + math.sin(a) * 26, 22, 22, 0.8)


def lines(img, x, y, tt, n=3, col=(255, 255, 255)):
    d = ImageDraw.Draw(img)
    for j in range(n):
        a = math.radians(-60 + j * 30 + 6 * math.sin(tt * 30))
        d.line(box(x + math.cos(a) * 30, y + math.sin(a) * 30, x + math.cos(a) * 70, y + math.sin(a) * 70), fill=col, width=L(7))


def idle(sp, gt):
    br = math.sin(gt * 3) * 0.015
    return dict(t=gt, sy=1 + br, tail='up', wag=8 if sp == 'cat' else 20, ws=3 if sp == 'cat' else 10,
                eyes='open', look=(0.3, 0.0), mouth='smile' if sp == 'cat' else 'tongue')


# ---------------------------------------------------------------- durumlar
def gag_doorbell(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if t >= 0: pop(img, 'DING DONG!', 760, 200, 0.15, tt, (255, 225, 70), 84, -6, 1.3)
    if sp == 'cat':
        o = dict(t=gt, lie=1.0, eyes='closed', tail='down', mouth='flat', sy=1 + 0.02 * math.sin(gt * 2.5))
        if 0.6 <= tt < 1.9: o.update(eyes='half', look=(0.6, -0.2), ears='back' if tt < 0.9 else 'up')
        info = pet(img, sp, o)
        if not (0.6 <= tt < 1.9): zzz(img, gt, info['hx'] + 90, info['hy'] - 80)
        if tt > 2.4: pop(img, 'NOT MY PROBLEM', 560, 260, 2.4, tt, (255, 255, 255), 62, -4)
    else:
        if t < 0:
            pet(img, sp, dict(idle(sp, gt), lie=1.0, eyes='closed', mouth='flat', tail='down')); return 0.0
        jumps = abs(math.sin(tt * 7.5)) * 120 if 0.3 <= tt < 3.6 else 0.0
        x = CX + 120 * math.sin(tt * 3.2) if tt >= 0.3 else CX
        f = 1 if math.cos(tt * 3.2) >= 0 else -1
        o = dict(t=gt, x=x, f=f, jump=jumps, eyes='wide', tail='up', wag=40, ws=26, ears='perk', run=0.6,
                 mouth='open' if (tt * 4) % 1 < 0.55 else 'tongue', mo=1.0, walk=gt * 22)
        if tt < 0.3: o = dict(t=gt, lie=1.0, eyes='tiny', mouth='o', ears='perk', tail='down')
        info = pet(img, sp, o)
        for j, t0 in enumerate((0.45, 1.2, 1.95, 2.7, 3.3)):
            pop(img, 'WOOF!', info['hx'] + 140 * (1 if j % 2 else -1), info['hy'] - 150, t0, tt, (255, 255, 255), 78,
                -10 if j % 2 else 10, 0.6)
        if 0.3 <= tt: shake = 4.0
    return shake


def vacuum(img, x, y, ang=0.0, on=False, gt=0.0):
    spr = Image.new('RGBA', (L(300), L(260)), (0, 0, 0, 0))
    put(spr, cyl((210, 60, 80), 170, 120, 40), 150, 190)
    put_sphere(spr, (60, 60, 70), 90, 245, 40, 40); put_sphere(spr, (60, 60, 70), 210, 245, 40, 40)
    d = ImageDraw.Draw(spr)
    d.line(box(150, 130, 150, 10), fill=(90, 90, 100), width=L(16))
    d.rounded_rectangle(box(115, 0, 185, 26), radius=L(10), fill=(60, 60, 70))
    put_sphere(spr, (250, 220, 80) if on else (120, 120, 120), 150, 175, 30, 30, 0.8)
    put_rot(img, spr, x, y, ang)
    if on:
        rnd = random.Random(int(gt * 20))
        for j in range(5):
            put_sphere(img, (200, 200, 205), x - 120 - rnd.uniform(0, 80), y + 90 + rnd.uniform(-10, 10), 10, 10, 0.2)


def gag_vacuum(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    vx = lerp(1150, 830, sm(seg(tt, 0.0, 0.9))) if t >= 0 else 1150
    on = 0.5 <= tt
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); vacuum(img, vx, 700); return 0.0
        vacuum(img, vx, 700, 0, on, gt)
        if tt < 0.9:
            o = dict(idle(sp, gt), eyes='open' if tt < 0.55 else 'tiny', ears='up' if tt < 0.55 else 'flat', look=(1, 0))
            pet(img, sp, o)
        elif tt < 2.0:
            u = seg(tt, 0.9, 2.0)
            o = dict(t=gt, puff=1.0, eyes='tiny', ears='flat', tail='puff', mouth='hiss', look=(1, -0.3),
                     jump=230 * math.sin(math.pi * u), x=CX - 60 * u)
            pet(img, sp, o)
            if tt < 1.3: shake = 10.0
            pop(img, 'HSSSS!', 560, 240, 0.95, tt, (255, 90, 90), 90, 6, 1.0)
        else:
            u = seg(tt, 2.0, 2.7)
            x = lerp(CX - 60, -320, sm(u))
            pet(img, sp, dict(t=gt, x=x, f=-1, puff=1.0, eyes='tiny', ears='flat', tail='puff', mouth='hiss', run=1.0, walk=gt * 30))
            for j in range(10):
                particles(img, 3, 2.0, tt, 14, (CX - 60, GY - 120), (-300, 300), (-400, -100), 900, [pet_def('cat')['color']], (8, 14), 2.0)
            pop(img, 'NOPE.', 300, 360, 2.6, tt, (255, 255, 255), 120, -6)
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); vacuum(img, vx, 700); return 0.0
        knocked = tt >= 2.9
        ang = -lerp(0, 82, back(seg(tt, 2.9, 3.2))) if knocked else 0
        vacuum(img, vx, 700 + (40 if knocked else 0) * seg(tt, 2.9, 3.2), ang, on and not knocked, gt)
        if tt < 0.9:
            pet(img, sp, dict(idle(sp, gt), ears='perk', look=(1, 0), eyes='wide'))
        elif tt < 2.9:
            lunge = abs(math.sin((tt - 0.9) * 5.5))
            pet(img, sp, dict(t=gt, x=CX + 230 * lunge, jump=60 * lunge, eyes='angry', ears='perk', tail='up', wag=30, ws=22,
                              mouth='open' if (tt * 5) % 1 < 0.5 else 'flat', look=(1, 0), run=lunge))
            for j, t0 in enumerate((1.0, 1.55, 2.1, 2.6)):
                pop(img, 'WOOF!' if j % 2 else 'GRRR!', 600, 230 + 40 * (j % 2), t0, tt, (255, 255, 255), 76, -8 if j % 2 else 8, 0.5)
            shake = 3.0
        else:
            pet(img, sp, dict(t=gt, x=CX + 120, eyes='happy', tail='up', wag=45, ws=24, mouth='tongue', ears='perk', jump=20 * abs(math.sin(gt * 8))))
            pop(img, 'VICTORY!', 560, 250, 3.15, tt, (255, 225, 70), 90, -5)
            if tt < 3.4: shake = 9.0
    return shake


def bowl(img, x, y, full, spin=0.0):
    put_shadow(img, x, y + 26, 190, 26)
    if full > 0:
        put_sphere(img, (160, 95, 50), x, y - 26 - 10 * full, 140 * (0.6 + 0.4 * full), 50 * full + 8, 0.3)
        rnd = random.Random(4)
        for j in range(int(9 * full)):
            put_sphere(img, (130, 75, 40), x + rnd.uniform(-55, 55) * full, y - 28 - rnd.uniform(0, 26) * full, 22, 18, 0.4)
    spr = cyl((70, 140, 230), 180, 56, 22, 0.6)
    put_rot(img, spr, x, y, 6 * math.sin(spin * 12) * min(1, spin))


def gag_food(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0; bx, byy = 720, 770
    if sp == 'cat':
        if t < 0: bowl(img, bx, byy, 1.0); pet(img, sp, idle(sp, gt)); return 0.0
        walk = tt < 1.2
        x = lerp(CX, 520, sm(seg(tt, 0.2, 1.2)))
        bowl(img, bx, byy, 1.0)
        o = dict(t=gt, x=x, walk=gt * 12 if 0.2 < tt < 1.2 else None, tail='up', wag=6, ws=3, eyes='open', look=(1, 0.3))
        if 1.2 <= tt < 2.0: o.update(head_dy=40, head_dx=20, eyes='closed', mouth='o')
        if tt >= 2.0: o.update(eyes='half', look=(0, 0.1), mouth='flat', tail='down')
        pet(img, sp, o)
        if 1.2 <= tt < 2.0: pop(img, 'sniff sniff', 760, 520, 1.3, tt, (255, 255, 255), 50, 0, 0.7)
        if tt >= 2.4: pop(img, '...MEH.', 560, 250, 2.4, tt, (255, 255, 255), 100, -4)
    else:
        if t < 0: bowl(img, bx, byy, 1.0); pet(img, sp, idle(sp, gt)); return 0.0
        x = lerp(CX, 520, sm(seg(tt, 0.1, 0.5)))
        eaten = seg(tt, 0.5, 1.7)
        bowl(img, bx + 30 * math.sin(tt * 9) * seg(tt, 1.7, 2.6) * (tt < 2.6), byy, 1 - eaten, seg(tt, 1.7, 2.6) * (tt < 2.6))
        o = dict(t=gt, x=x, tail='up', wag=45, ws=26, eyes='wide', mouth='tongue', ears='perk', look=(1, 0.4), run=0.4 if tt < 0.5 else 0)
        if 0.5 <= tt < 2.6:
            o.update(head_dy=48 + 10 * math.sin(tt * 30), head_dx=26, eyes='closed', mouth='open', mo=0.6 + 0.4 * abs(math.sin(tt * 24)))
            shake = 3.0
            particles(img, 9, 0.5, tt, 30, (bx - 40, byy - 50), (-160, 160), (-420, -120), 1800, [(130, 75, 40)], (10, 16), 0.5, emit=1.2)
        if tt >= 2.6: o.update(eyes='wide', look=(-0.2, -0.3), mouth='tongue', head_dy=-10)
        pet(img, sp, o)
        if 0.6 <= tt < 2.6: pop(img, 'NOM NOM NOM', 640, 250, 0.6, tt, (255, 225, 70), 80, -6)
        if tt >= 2.7: pop(img, 'MORE?', 600, 250, 2.7, tt, (255, 255, 255), 110, 5)
    return shake


def stand(img):
    put(img, cyl((150, 100, 65), 220, 190, 10), 730, 708)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box(610, 600, 850, 622), radius=L(8), fill=(185, 130, 85))
    d.rounded_rectangle(box(650, 650, 810, 700), radius=L(6), outline=(120, 80, 50), width=L(4))


def glass(img, x, y, ang=0.0):
    spr = Image.new('RGBA', (L(90), L(120)), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    d.polygon([(L(10), L(6)), (L(80), L(6)), (L(70), L(114)), (L(20), L(114))], fill=(200, 230, 250, 170))
    d.polygon([(L(16), L(40)), (L(74), L(40)), (L(70), L(110)), (L(20), L(110))], fill=(110, 180, 245, 210))
    d.line(box(24, 14, 28, 100), fill=(255, 255, 255, 220), width=L(6))
    put_rot(img, spr, x, y, ang)


def shards(img, tt, t0, x, y):
    if tt >= t0:
        particles(img, 21, t0, tt, 16, (x, y), (-380, 380), (-520, -160), 2200, [(200, 230, 250), (150, 200, 245)], (10, 20), 1.0)
        particles(img, 22, t0, tt, 12, (x, y), (-250, 250), (-300, -80), 1800, [(110, 180, 245)], (14, 24), 0.8)


def gag_cup(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    stand(img)
    if sp == 'cat':
        if t < 0: glass(img, 700, 545); pet(img, sp, dict(idle(sp, gt), x=440)); return 0.0
        fall = seg(tt, 2.2, 2.75)
        gx = 700 + 80 * sm(seg(tt, 1.4, 2.2)) + 60 * fall
        gy_ = 545 if tt < 2.2 else 545 + 250 * fall * fall
        o = dict(t=gt, x=440, tail='up', wag=10, ws=4, eyes='open', look=(1, -0.2), mouth='smile')
        if 0.4 <= tt < 1.4: o.update(look=(0, 0.1), eyes='half')                     # kameraya bakış
        if 1.0 <= tt < 2.3: o.update(paw=sm(seg(tt, 1.0, 1.3)), look=(0, 0.1), eyes='half')
        if tt >= 2.75: o.update(eyes='happy', mouth='smile', look=(0, 0))
        pet(img, sp, o)
        if tt < 2.75: glass(img, gx, gy_, 200 * fall)
        shards(img, tt, 2.75, 850, 790)
        if 2.75 <= tt < 3.1: shake = 12.0
        pop(img, 'CRASH!', 780, 330, 2.75, tt, (255, 120, 90), 100, 8)
        if 0.5 <= tt < 1.4: pop(img, '*stares*', 360, 260, 0.5, tt, (255, 255, 255), 56, -4, 0.9)
    else:
        if t < 0: glass(img, 700, 545); pet(img, sp, dict(idle(sp, gt), x=520, f=-1)); return 0.0
        fall = seg(tt, 1.6, 2.2)
        hit = tt >= 1.6
        gx = 700 - 40 * fall; gy_ = 545 + 250 * fall * fall
        o = dict(t=gt, x=520, f=-1, tail='up', wag=55 if tt < 2.2 else 10, ws=30, eyes='wide', mouth='tongue', look=(-0.6, 0), ears='perk')
        if tt >= 2.2: o.update(eyes='tiny', mouth='o', look=(0.8, 0.3), ears='back', tail='tuck', head_dx=0)
        pet(img, sp, o)
        if tt < 2.2: glass(img, gx, gy_, -150 * fall)
        shards(img, tt, 2.2, 680, 790)
        if 2.2 <= tt < 2.5: shake = 12.0
        pop(img, 'CRASH!', 680, 330, 2.2, tt, (255, 120, 90), 100, -8)
        if tt >= 2.7: pop(img, 'OOPS...', 300, 240, 2.7, tt, (255, 255, 255), 100, 5)
        if tt < 1.6: pop(img, 'wag wag', 640, 470, 0.3, tt, (255, 255, 255), 50, 0, 1.2)
    return shake


def tub(img, back_only=False, front_only=False, splash=0.0, gt=0.0):
    d = ImageDraw.Draw(img)
    if not front_only:
        d.rounded_rectangle(box(600, 610, 1060, 650), radius=L(16), fill=(235, 240, 248))
        d.ellipse(box(620, 620, 1040, 660), fill=(120, 190, 240))
    if not back_only:
        put(img, cyl((245, 248, 252), 460, 190, 50), 830, 735)
        for x in (650, 1010):
            put_sphere(img, (200, 170, 90), x, 830, 40, 30)


def gag_bath(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        tub(img, back_only=True)
        if t < 0: tub(img, front_only=True); pet(img, sp, idle(sp, gt)); return 0.0
        tub(img, front_only=True)
        # duş: su damlaları kediye
        if 0.4 <= tt < 1.6:
            for j in range(18):
                u = ((tt - 0.4) * 2.5 + j / 18) % 1
                put_sphere(img, (120, 190, 250), CX - 120 + (j * 37) % 240, 80 + u * 600, 12, 22, 0.8)
        wet = sm(seg(tt, 0.6, 1.4))
        o = dict(t=gt, wet=wet, eyes='tiny' if tt < 1.6 else 'angry', puff=sm(seg(tt, 0.6, 1.0)), ears='flat', tail='puff',
                 mouth='hiss' if 0.7 <= tt < 2.6 else 'flat', look=(0, -0.6) if tt < 1.6 else (0, 0.1))
        if 1.6 <= tt < 2.6: o.update(paw=abs(math.sin((tt - 1.6) * 9)))
        pet(img, sp, o)
        if 0.7 <= tt < 1.8: pop(img, 'HSSSS!', 620, 240, 0.7, tt, (255, 90, 90), 96, 6); shake = 6.0
        if tt >= 2.6: pop(img, 'NEVER AGAIN.', 540, 250, 2.6, tt, (255, 255, 255), 84, -4)
    else:
        tub(img, back_only=True)
        if t < 0: tub(img, front_only=True); pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 1.2:  # küvete zıplar
            u = seg(tt, 0.3, 1.1)
            x = lerp(CX, 820, sm(u)); jump = 300 * math.sin(math.pi * u) if tt < 1.1 else 0
            gyy = lerp(GY, 760, u)
            pet(img, sp, dict(t=gt, x=x, gy=gyy, jump=jump, eyes='wide', mouth='tongue', tail='up', wag=40, ws=26, run=1.0 if 0.3 < tt < 1.1 else 0))
            tub(img, front_only=True)
        elif tt < 2.4:  # içinde oynuyor
            pet(img, sp, dict(t=gt, x=820, gy=760, eyes='happy', mouth='tongue', wet=1.0, tail='up', wag=50, ws=30, jump=20 * abs(math.sin(gt * 9))))
            tub(img, front_only=True)
            particles(img, 31, 1.1, tt, 40, (820, 640), (-500, 500), (-900, -300), 2200, [(150, 210, 255), (200, 235, 255)], (12, 22), 0.9, emit=1.2)
            pop(img, 'SPLASH!', 560, 240, 1.15, tt, (120, 200, 255), 100, -6)
            shake = 5.0
        else:  # çıkıp silkelenir
            x = lerp(820, 470, sm(seg(tt, 2.4, 2.8)))
            wig = 22 * math.sin(gt * 50) if tt > 2.8 else 0
            pet(img, sp, dict(t=gt, x=x + wig, eyes='closed', mouth='tongue', wet=1.0, tail='up', wag=60, ws=40))
            tub(img, front_only=True)
            if tt > 2.8:
                particles(img, 33, 2.8, tt, 50, (x, GY - 170), (-900, 900), (-700, 100), 900, [(150, 210, 255)], (10, 18), 1.2, emit=1.0)
                pop(img, 'SHAKE SHAKE!', 560, 240, 2.85, tt, (255, 255, 255), 84, 4)
    return shake


def cardbox(img, x, gy, part, w=300, h=210, open_=1.0, shake=0.0, torn=0.0):
    """part: 'back' (iç arka duvar), 'front' (ön yüz + kapaklar)."""
    c = (205, 160, 105); d = ImageDraw.Draw(img); x += shake
    if part == 'back':
        d.rectangle(box(x - w / 2, gy - h - 26, x + w / 2, gy - h + 30), fill=darken(c, 0.35))
        return
    if torn >= 1: return
    put(img, cyl(c, w, h, 6, 0.2), x, gy - h / 2)
    d.line(box(x - w / 2 + 6, gy - h + 8, x + w / 2 - 6, gy - h + 8), fill=darken(c, 0.2), width=L(4))
    d.rectangle(box(x - 30, gy - h, x + 30, gy - h + 60), fill=(225, 205, 160))
    for s in (-1, 1):
        a = math.radians(-60 * open_)
        x0 = x + s * w / 2; y0 = gy - h
        x1 = x0 + s * math.cos(a) * 110; y1 = y0 + math.sin(a) * 110
        d.polygon([(L(x0), L(y0)), (L(x1), L(y1)), (L(x1 - s * 8), L(y1 + 14)), (L(x0 - s * 8), L(y0 + 12))], fill=darken(c, 0.1))
    if torn > 0:
        rnd = random.Random(5)
        for j in range(int(8 * torn)):
            d.polygon([(L(x + rnd.uniform(-w / 2, w / 2)), L(gy - rnd.uniform(0, h)))] * 0 +
                      [(L(x - 30 + j * 9), L(gy - h + 10)), (L(x - 10 + j * 9), L(gy - h + 40)), (L(x - 40 + j * 9), L(gy - h + 60))],
                      fill=darken(c, 0.4))


def gag_box(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0; bx = 720
    if sp == 'cat':
        if t < 0:
            cardbox(img, bx, GY + 10, 'back'); cardbox(img, bx, GY + 10, 'front'); pet(img, sp, idle(sp, gt)); return 0.0
        cardbox(img, bx, GY + 10, 'back')
        if tt < 1.6:
            u = seg(tt, 0.7, 1.5)
            x = lerp(CX, bx - 116, sm(u)); jump = 330 * math.sin(math.pi * u) if 0.7 < tt < 1.5 else 0
            o = dict(t=gt, x=x, jump=jump, eyes='wide', look=(1, 0.2), tail='up', wag=20, ws=8, mouth='smile')
            if tt < 0.7: o.update(sy=0.9, sx=1.05)
            if tt >= 1.5: o.update(gy=GY - 10)
            pet(img, sp, o)
        else:
            sink = sm(seg(tt, 1.6, 1.9))
            pet(img, sp, dict(t=gt, x=bx - 70, scale=0.82, gy=lerp(GY - 10, 668, sink), eyes='wide' if tt < 2.6 else 'happy', look=(0, 0.1), mouth='smile',
                              lie=1.0, tail='down'))
        cardbox(img, bx, GY + 10, 'front', shake=8 * spring(tt - 1.5, 1, 30, 6) if tt > 1.5 else 0)
        if tt >= 2.3: pop(img, 'IF I FITS, I SITS', 540, 240, 2.3, tt, (255, 225, 70), 74, -4)
        if 1.5 <= tt < 1.7: shake = 5.0
    else:
        if t < 0:
            cardbox(img, bx, GY + 10, 'front'); pet(img, sp, idle(sp, gt)); return 0.0
        torn = sm(seg(tt, 1.2, 2.8))
        sh = 18 * math.sin(gt * 40) if 1.0 <= tt < 2.8 else 0
        cardbox(img, bx, GY + 10, 'front', shake=sh, torn=1.0 if tt >= 2.8 else torn)
        x = lerp(CX, 520, sm(seg(tt, 0.2, 0.8)))
        o = dict(t=gt, x=x, eyes='wide', tail='up', wag=50, ws=28, mouth='tongue', ears='perk', run=0.5 if tt < 0.8 else 0)
        if 1.0 <= tt < 2.8: o.update(eyes='angry', mouth='open', head_dy=30, head_dx=30 + 15 * math.sin(gt * 40), mo=0.8)
        if tt >= 2.8: o.update(eyes='happy', mouth='tongue', head_dy=0)
        info = pet(img, sp, o)
        if 1.0 <= tt:
            particles(img, 41, 1.0, tt, 40, (bx - 40, GY - 120), (-500, 500), (-800, -200), 1600, [(205, 160, 105), (180, 135, 85)], (16, 30), 1.5, emit=1.8)
        if tt >= 2.8:
            put_rot(img, cyl((205, 160, 105), 90, 40, 6), info['nose'][0] + 40, info['my'] + 10, 20)
            pop(img, 'BOX DESTROYED', 560, 240, 2.9, tt, (255, 225, 70), 80, 4)
        if 1.0 <= tt < 2.8: shake = 5.0
    return shake


def dot(img, x, y):
    for r, a in ((110, 70), (60, 140), (28, 255)):
        put_sphere(img, (255, 40, 40), x, y, r, r, 0.0) if a == 255 else put(img, fade(sphere((255, 60, 60), r, r, 0.0), a / 255), x, y)


def gag_laser(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        path = [(0.0, 760, 780), (0.9, 760, 780), (1.5, 260, 760), (2.4, 260, 760), (2.9, 820, 790)]
        dx, dy = path[-1][1:]
        for (a, x0, y0), (b, x1, y1) in zip(path, path[1:]):
            if a <= tt < b: dx, dy = lerp(x0, x1, sm(seg(tt, a, b))), lerp(y0, y1, sm(seg(tt, a, b))); break
        if tt < 0.9:
            pet(img, sp, dict(t=gt, sy=0.86, sx=1.06, eyes='wide', look=(1, 0.5), tail='up', wag=35, ws=20, ears='up'))
        elif tt < 1.5:
            u = seg(tt, 0.9, 1.5)
            pet(img, sp, dict(t=gt, x=lerp(CX, 700, u), jump=260 * math.sin(math.pi * u), eyes='wide', look=(1, 0.6), run=1.0, tail='up'))
        elif tt < 2.4:
            pet(img, sp, dict(t=gt, x=700, f=-1, eyes='wide', look=(-1, 0.5), sy=0.86, tail='up', wag=35, ws=20))
        else:
            u = seg(tt, 2.4, 2.9)
            x = lerp(700, 330, sm(u))
            if tt < 2.9: pet(img, sp, dict(t=gt, x=x, f=-1, jump=200 * math.sin(math.pi * u), eyes='wide', run=1.0, tail='up'))
            else:
                pet(img, sp, dict(t=gt, x=330, f=-1, eyes='tiny', mouth='o', tail='down', sy=0.9))
                stars(img, gt, 214, 470); pop(img, 'BONK', 300, 300, 2.9, tt, (255, 225, 70), 100, -10)
                if tt < 3.2: shake = 10.0
        dot(img, dx, dy)
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        dot(img, 760, 780)
        if tt < 0.8:
            pet(img, sp, dict(idle(sp, gt), eyes='open', look=(1, 0.5), head_dy=10))
            pop(img, '?', 520, 380, 0.3, tt, (255, 255, 255), 120, 0)
        else:
            spin = (tt - 0.8) * 9
            f = 1 if math.cos(spin) > 0 else -1
            pet(img, sp, dict(t=gt, x=CX + 40 * math.sin(spin), f=f, eyes='wide' if tt < 3 else 'happy', mouth='tongue', tail='up',
                              wag=60, ws=30, run=0.6, walk=gt * 25))
            pop(img, 'MUST. CATCH. TAIL.', 540, 240, 1.0, tt, (255, 255, 255), 70, -4)
            shake = 2.0
    return shake


def cucumber(img, x, y, ang=0.0):
    spr = Image.new('RGBA', (L(230), L(80)), (0, 0, 0, 0))
    put(spr, cyl((60, 150, 60), 210, 62, 30, 0.5).rotate(90, expand=True).rotate(-90, expand=True), 115, 40)
    d = ImageDraw.Draw(spr)
    for j in range(7): d.ellipse(box(30 + j * 26, 22 + (j % 2) * 18, 36 + j * 26, 28 + (j % 2) * 18), fill=(120, 200, 110))
    put_rot(img, spr, x, y, ang)


def gag_cucumber(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0; bx, byy = 640, 770
    if sp == 'cat':
        if t < 0: bowl(img, bx, byy, 1.0); pet(img, sp, dict(idle(sp, gt), x=420)); return 0.0
        bowl(img, bx, byy, 1.0)
        cx_ = lerp(-150, 200, sm(seg(tt, 0.3, 0.9)))
        if tt < 1.6:
            cucumber(img, cx_, 785)
            o = dict(t=gt, x=420, head_dy=44, head_dx=24, eyes='closed', mouth='o', tail='up', wag=8, ws=4)
            if tt > 1.3: o.update(head_dy=0, head_dx=0, eyes='open', look=(-1, 0.3), mouth='flat', f=1)
            pet(img, sp, o)
            if tt < 1.3: pop(img, 'nom nom', 700, 520, 0.3, tt, (255, 255, 255), 50, 0, 1.0)
        else:
            cucumber(img, 200, 785)
            u = seg(tt, 1.6, 2.6)
            x = lerp(420, 700, sm(u)); jump = 420 * math.sin(math.pi * u) if tt < 2.6 else 0
            gyy = lerp(GY, TTOP + 4, sm(seg(tt, 2.2, 2.6)))
            pet(img, sp, dict(t=gt, x=x, gy=gyy, jump=jump, puff=1.0, eyes='tiny', ears='flat', tail='puff', mouth='hiss', look=(-1, 0.2)))
            pop(img, 'AAAAH!', 520, 230, 1.6, tt, (255, 90, 90), 110, 8)
            if tt < 2.0: shake = 12.0
        if tt >= 2.8: pop(img, 'SNAKE!!', 260, 420, 2.8, tt, (255, 255, 255), 90, -6)
    else:
        if t < 0: bowl(img, bx, byy, 1.0); pet(img, sp, dict(idle(sp, gt), x=420)); return 0.0
        bowl(img, bx, byy, 1.0)
        eaten = seg(tt, 1.6, 2.6)
        cx_ = lerp(-150, 200, sm(seg(tt, 0.3, 0.9)))
        o = dict(t=gt, x=420, eyes='open', mouth='tongue', tail='up', wag=30, ws=20)
        if 0.9 <= tt < 1.6: o.update(f=-1, x=lerp(420, 380, seg(tt, 0.9, 1.2)), head_dy=40, eyes='closed', mouth='o')
        if 1.6 <= tt: o.update(f=-1, x=380, eyes='happy', mouth='open', mo=0.5 + 0.5 * abs(math.sin(tt * 20)), head_dy=30)
        if tt >= 2.6: o.update(mouth='tongue', head_dy=0, wag=50, ws=30, eyes='wide', look=(0, 0))
        if eaten < 1: cucumber(img, cx_ if tt < 0.9 else 200 + 40 * eaten, 785 - 40 * eaten, 0)
        pet(img, sp, o)
        if 1.6 <= tt < 2.6:
            particles(img, 51, 1.6, tt, 20, (230, 700), (-200, 200), (-400, -100), 1800, [(60, 150, 60), (150, 220, 140)], (10, 16), 0.6, emit=0.9)
            pop(img, 'CRUNCH!', 560, 250, 1.6, tt, (120, 220, 110), 90, -6)
        if tt >= 2.7: pop(img, 'YUMMY!', 600, 250, 2.7, tt, (255, 225, 70), 100, 5)
    return shake


def ball(img, x, y, r=46):
    put_sphere(img, (240, 220, 60), x, y, r * 2, r * 2, 0.6)
    ImageDraw.Draw(img).arc(box(x - r * 0.8, y - r, x + r * 0.5, y + r), 300, 60, fill=(255, 255, 255), width=L(6))


def ball_path(tt, t0, x0, x1, y0=780):
    u = seg(tt, t0, t0 + 1.0)
    x = lerp(x0, x1, u); y = y0 - 420 * math.sin(math.pi * min(1, u * 1.4)) * (1 if u < 0.72 else 0) - (60 * abs(math.sin(u * 14)) * (1 - u) if u >= 0.72 else 0)
    return x, y


def gag_ball(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        bxy = ball_path(tt, 0.3, -60, 860) if tt >= 0.3 else (-200, 0)
        o = dict(t=gt, eyes='open', look=((bxy[0] - CX) / 500, (bxy[1] - 600) / 400), tail='up', wag=6, ws=3)
        if 1.7 <= tt < 2.6: o.update(eyes='closed', mouth='open', mo=1.0)
        if tt >= 2.6: o.update(lie=1.0, eyes='closed', tail='down', mouth='flat')
        info = pet(img, sp, o)
        ball(img, *bxy)
        if 1.7 <= tt < 2.6: pop(img, '*yawn*', 360, 300, 1.7, tt, (255, 255, 255), 60, -4)
        if tt >= 2.6: zzz(img, gt, info['hx'] + 90, info['hy'] - 80); pop(img, 'GET IT YOURSELF.', 560, 250, 2.7, tt, (255, 255, 255), 66, -4)
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 1.3:
            bxy = ball_path(tt, 0.3, -60, 860) if tt >= 0.3 else (-200, 0)
            u = seg(tt, 0.35, 1.3)
            pet(img, sp, dict(t=gt, x=lerp(CX, 760, sm(u)), run=1.0, walk=gt * 30, eyes='wide', mouth='tongue', tail='up', wag=50, ws=30,
                              jump=40 * abs(math.sin(gt * 14)), look=(1, -0.3)))
            ball(img, *bxy)
        elif tt < 2.3:
            u = seg(tt, 1.3, 2.3)
            info = pet(img, sp, dict(t=gt, x=lerp(760, 420, sm(u)), f=-1, run=1.0, walk=gt * 30, eyes='wide', mouth='open', mo=0.5,
                                     tail='up', wag=50, ws=30, jump=40 * abs(math.sin(gt * 14))))
            ball(img, info['nose'][0] - 10, info['my'] + 14, 36)
        else:
            info = pet(img, sp, dict(t=gt, x=420, f=1, eyes='wide', look=(0, 0), mouth='tongue', tail='up', wag=60, ws=34, ears='perk',
                                     jump=26 * abs(math.sin(gt * 10))))
            ball(img, 640, 780)
            pop(img, 'AGAIN! AGAIN!', 560, 250, 2.4, tt, (255, 225, 70), 86, -4)
    return shake


MIRX, MIRY, MIRW, MIRH = 800, 470, 300, 560


def mirror(img, sp, o):
    d = ImageDraw.Draw(img)
    d.ellipse(box(MIRX - MIRW / 2 - 16, MIRY - MIRH / 2 - 16, MIRX + MIRW / 2 + 16, MIRY + MIRH / 2 + 16), fill=(190, 150, 80))
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer)
    d2.rectangle([0, 0, layer.width, layer.height], fill=(200, 225, 240, 255))
    o2 = dict(o); o2['x'] = MIRX + 70; o2['f'] = -o.get('f', 1); o2['scale'] = 0.82; o2['gy'] = GY - 30
    lk = o.get('look', (0.3, 0)); o2['look'] = (-lk[0], lk[1])
    pet(layer, sp, o2)
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).ellipse(box(MIRX - MIRW / 2, MIRY - MIRH / 2, MIRX + MIRW / 2, MIRY + MIRH / 2), fill=225)
    tint = Image.new('RGBA', img.size, (210, 235, 250, 60))
    layer = Image.alpha_composite(layer, tint)
    img.paste(layer, (0, 0), m)
    d.line(box(MIRX - 80, MIRY - 200, MIRX - 20, MIRY - 250), fill=(255, 255, 255), width=L(10))


def gag_mirror(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        o = dict(idle(sp, gt), x=480)
        if t >= 0:
            if 0.6 <= tt: o.update(puff=sm(seg(tt, 0.6, 0.9)), eyes='angry' if tt > 1.4 else 'tiny', ears='flat', tail='puff', mouth='hiss', look=(1, 0))
            if 1.5 <= tt < 3.0: o.update(paw=abs(math.sin((tt - 1.5) * 8)))
            if tt >= 3.0: o.update(paw=0.0)
        mirror(img, sp, o)
        pet(img, sp, o)
        if t >= 0:
            if 0.7 <= tt: pop(img, 'HSSSS!', 380, 240, 0.7, tt, (255, 90, 90), 90, -6, 1.0)
            if 1.6 <= tt: pop(img, 'WHO ARE YOU?!', 560, 240, 1.7, tt, (255, 255, 255), 74, 4)
            if 1.5 <= tt < 3.0: shake = 4.0
    else:
        o = dict(idle(sp, gt), x=480)
        if t >= 0:
            if 0.4 <= tt < 1.8: o.update(eyes='wide', mouth='open' if (tt * 4) % 1 < 0.5 else 'flat', ears='perk', tail='up', wag=40, ws=24, look=(1, 0))
            if 1.8 <= tt: o.update(sy=0.8, head_dy=50, eyes='happy', mouth='tongue', tail='up', wag=60, ws=30)
            if tt >= 2.8: o.update(sy=1.0, head_dy=0, head_dx=30, eyes='closed', mouth='tongue')
        mirror(img, sp, o)
        pet(img, sp, o)
        if t >= 0:
            if 0.5 <= tt < 1.8: pop(img, 'WOOF?!', 420, 240, 0.5, tt, (255, 255, 255), 90, -6, 1.3)
            if 1.9 <= tt: pop(img, 'NEW BEST FRIEND!', 560, 240, 2.0, tt, (255, 225, 70), 70, 4)
            if tt >= 2.8:
                for j in range(3): put_sphere(img, (245, 170, 190), MIRX - 110 + j * 26, MIRY + 170 + 10 * math.sin(j), 30, 18, 0.3)
    return shake


def toy(img, x, y, squash=0.0):
    put_sphere(img, (255, 210, 40), x, y - 4 * squash, 120 * (1 + 0.3 * squash), 90 * (1 - 0.35 * squash), 0.6)
    put_sphere(img, (255, 210, 40), x + 46, y - 50 + 10 * squash, 70, 64, 0.6)
    put_sphere(img, (255, 130, 30), x + 82, y - 46 + 10 * squash, 34, 20, 0.5)
    put_sphere(img, DARK, x + 52, y - 60 + 10 * squash, 12, 14, 0.1)


def gag_squeaky(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        if t < 0: toy(img, 680, 780); pet(img, sp, idle(sp, gt)); return 0.0
        sq = 1.0 if 0.8 <= tt < 1.0 else 0.0
        toy(img, 680, 780, sq)
        o = dict(t=gt, x=420, eyes='open', look=(1, 0.5), tail='up', wag=10, ws=5)
        if 0.6 <= tt < 1.0: o.update(paw=sm(seg(tt, 0.6, 0.8)))
        if 1.0 <= tt < 1.8: o.update(x=lerp(420, 300, sm(seg(tt, 1.0, 1.2))), jump=120 * math.sin(math.pi * seg(tt, 1.0, 1.5)),
                                    eyes='tiny', puff=0.6, ears='flat', mouth='o', tail='puff')
        if tt >= 1.8: o.update(x=300, paw=0.85, head_dy=20, eyes='closed', mouth='tongue', look=(0, 0), tail='down')
        pet(img, sp, o)
        pop(img, 'SQUEAK!', 700, 560, 0.8, tt, (255, 225, 70), 70, 8, 0.8)
        if tt >= 2.2: pop(img, '*licks paw*', 560, 250, 2.2, tt, (255, 255, 255), 66, -4)
    else:
        if t < 0: toy(img, 680, 780); pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 0.5:
            toy(img, 680, 780); pet(img, sp, dict(idle(sp, gt), eyes='wide', ears='perk', look=(1, 0.5)))
        else:
            info = pet(img, sp, dict(t=gt, x=500, eyes='happy' if tt > 3 else 'wide', mouth='open', mo=0.6 + 0.4 * abs(math.sin(tt * 14)),
                                     tail='up', wag=60, ws=34, head_dx=18 * math.sin(gt * 26), head_dy=6, ears='perk'))
            toy(img, info['nose'][0] + 30, info['my'] + 34, abs(math.sin(tt * 14)))
            for j in range(6):
                pop(img, 'SQUEAK!', 300 + (j % 3) * 260, 220 + (j // 3) * 120, 0.6 + j * 0.42, tt, (255, 225, 70), 64, -12 + j * 5, 0.5)
            shake = 3.0
    return shake


def petbed(img, x, y, torn=0.0):
    if torn >= 1: return
    put(img, cyl((90, 160, 220), 300 * (1 - 0.2 * torn), 90, 40, 0.3), x, y - 30)
    put_sphere(img, (230, 240, 250), x, y - 66, 220 * (1 - 0.3 * torn), 60, 0.2)


def gag_bed(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        bx_ = 790
        if t < 0:
            petbed(img, 500, 800); cardbox(img, bx_, GY + 10, 'back'); cardbox(img, bx_, GY + 10, 'front', w=230, h=170)
            pet(img, sp, dict(idle(sp, gt), x=300)); return 0.0
        petbed(img, 500, 800)
        cardbox(img, bx_, GY + 10, 'back', w=230, h=170)
        if tt < 1.0:
            pet(img, sp, dict(idle(sp, gt), x=300, look=(1, 0.3)))
            pop(img, 'NEW BED!', 560, 520, 0.2, tt, (255, 255, 255), 60, 0, 0.8)
        elif tt < 1.9:
            u = seg(tt, 1.0, 1.9)
            pet(img, sp, dict(t=gt, x=lerp(300, bx_ - 116, sm(u)), jump=360 * math.sin(math.pi * u), eyes='wide', tail='up', run=0.8,
                              gy=lerp(GY, 712, seg(tt, 1.7, 1.9))))
        else:
            pet(img, sp, dict(t=gt, x=bx_ - 60, scale=0.75, gy=712, lie=1.0, eyes='happy', mouth='smile', tail='down'))
        cardbox(img, bx_, GY + 10, 'front', w=230, h=170)
        if tt >= 2.2: pop(img, 'THE BOX IS BETTER', 540, 250, 2.2, tt, (255, 225, 70), 70, -4)
    else:
        if t < 0: petbed(img, 680, 800); pet(img, sp, idle(sp, gt)); return 0.0
        torn = sm(seg(tt, 0.8, 2.6))
        petbed(img, 680 + (14 * math.sin(gt * 40) if tt < 2.6 else 0), 800, torn)
        if tt < 2.6:
            pet(img, sp, dict(t=gt, x=lerp(CX, 520, sm(seg(tt, 0.2, 0.7))), eyes='angry' if tt > 0.8 else 'wide', mouth='open', mo=0.8,
                              head_dy=30 if tt > 0.8 else 0, head_dx=20 * math.sin(gt * 38) if tt > 0.8 else 0, tail='up', wag=50, ws=30))
            if tt > 0.8:
                particles(img, 61, 0.8, tt, 60, (640, 720), (-600, 600), (-900, -300), 1300, [(250, 250, 250), (235, 240, 248)], (20, 38), 2.0, emit=1.8)
                shake = 4.0
        else:
            rnd = random.Random(3)
            for j in range(26):
                put_sphere(img, (250, 250, 252), 380 + rnd.uniform(-260, 520), 790 - rnd.uniform(0, 70), rnd.uniform(40, 70), rnd.uniform(30, 50), 0.2)
            pet(img, sp, dict(t=gt, x=560, gy=GY - 20, lie=1.0, eyes='happy', mouth='tongue', tail='up', wag=40, ws=20))
            pop(img, 'BEST BED EVER', 560, 250, 2.7, tt, (255, 225, 70), 80, 4)
    return shake


# events: (saniye, ses[, süre]) — panel başına göre
GAGS = {
    'doorbell': dict(fn=gag_doorbell, title='WHEN THE DOORBELL RINGS', name='Doorbell', wall=(170, 200, 230),
                     cat=[(0.15, 'dingdong'), (2.4, 'purr', 1.2)], dog=[(0.15, 'dingdong')] + [(t0, 'bark') for t0 in (0.45, 1.2, 1.95, 2.7, 3.3)]),
    'vacuum': dict(fn=gag_vacuum, title='WHEN THE VACUUM TURNS ON', name='Vacuum', wall=(205, 225, 200),
                   cat=[(0.5, 'vacuum', 3.4), (0.95, 'hiss'), (2.0, 'whoosh'), (2.6, 'pop')],
                   dog=[(0.5, 'vacuum', 2.4), (1.0, 'growl'), (1.55, 'bark'), (2.1, 'growl'), (2.6, 'bark'), (2.9, 'bonk'), (3.15, 'ding')]),
    'food': dict(fn=gag_food, title='WHEN DINNER IS SERVED', name='Dinner', wall=(245, 215, 175),
                 cat=[(0.0, 'pour'), (1.3, 'sniff'), (2.4, 'meow_flat')],
                 dog=[(0.0, 'pour'), (0.6, 'chomp', 1.9), (1.8, 'lick'), (2.2, 'lick'), (2.7, 'whine')]),
    'cup': dict(fn=gag_cup, title='WHEN THERE IS A GLASS ON THE TABLE', name='Glass', wall=(215, 200, 235),
                cat=[(1.2, 'meow'), (2.75, 'crash')], dog=[(0.3, 'wag', 1.3), (2.2, 'crash'), (2.7, 'whine')]),
    'bath': dict(fn=gag_bath, title='BATH TIME', name='Bath', wall=(190, 225, 235),
                 cat=[(0.4, 'shower', 1.2), (0.7, 'hiss'), (1.7, 'yowl'), (2.6, 'meow_flat')],
                 dog=[(0.4, 'bark'), (1.1, 'splash'), (1.6, 'splash'), (2.85, 'shake', 1.0)]),
    'box': dict(fn=gag_box, title='WHEN AN EMPTY BOX ARRIVES', name='Box', wall=(235, 210, 190),
                cat=[(0.7, 'whoosh_s'), (1.5, 'thud'), (2.3, 'purr', 1.5)], dog=[(0.3, 'bark'), (1.0, 'rip', 1.8), (2.9, 'bark')]),
    'laser': dict(fn=gag_laser, title='THE RED DOT', name='Laser', wall=(225, 225, 240),
                  cat=[(0.9, 'whoosh_s'), (2.4, 'whoosh_s'), (2.9, 'bonk'), (3.2, 'meow_small')], dog=[(0.3, 'boing'), (0.9, 'spin', 2.8)]),
    'cucumber': dict(fn=gag_cucumber, title='CUCUMBER BEHIND THEM', name='Cucumber', wall=(210, 235, 210),
                     cat=[(0.3, 'slide'), (1.6, 'yowl'), (2.6, 'thud'), (2.8, 'hiss')],
                     dog=[(0.3, 'slide'), (1.0, 'sniff'), (1.6, 'crunch'), (1.9, 'crunch'), (2.2, 'crunch'), (2.7, 'bark')]),
    'ball': dict(fn=gag_ball, title='PLAYING FETCH', name='Fetch', wall=(200, 220, 245),
                 cat=[(0.3, 'whoosh'), (1.1, 'boing'), (1.7, 'yawn')],
                 dog=[(0.3, 'whoosh'), (0.4, 'zoom'), (1.1, 'boing'), (2.3, 'thud'), (2.4, 'bark'), (2.9, 'bark')]),
    'mirror': dict(fn=gag_mirror, title='MEETING THEIR REFLECTION', name='Mirror', wall=(240, 220, 225),
                   cat=[(0.7, 'hiss'), (1.6, 'swipe'), (2.1, 'swipe'), (2.6, 'yowl')],
                   dog=[(0.5, 'bark'), (1.0, 'bark'), (1.9, 'whine'), (2.8, 'lick'), (3.1, 'lick')]),
    'squeaky': dict(fn=gag_squeaky, title='THE SQUEAKY TOY', name='Squeaky Toy', wall=(250, 235, 180),
                    cat=[(0.8, 'squeak'), (1.0, 'hiss'), (2.2, 'lick'), (2.6, 'lick')],
                    dog=[(0.6 + j * 0.42, 'squeak') for j in range(7)]),
    'bed': dict(fn=gag_bed, title='WHEN THEY GET A NEW BED', name='New Bed', wall=(225, 205, 240),
                cat=[(1.0, 'whoosh_s'), (1.9, 'thud'), (2.2, 'purr', 1.5)], dog=[(0.8, 'rip', 1.8), (1.2, 'growl'), (2.6, 'whine')]),
}


# ---------------------------------------------------------------- durumlar 13-20 (2026-10-11)
def flash(img, a):
    if a > 0.01:
        img.alpha_composite(Image.new('RGBA', img.size, (255, 255, 255, int(170 * a))))


def storm(img, tt):
    d = ImageDraw.Draw(img)
    d.rectangle(box(676, 76, 944, 314), fill=(60, 70, 95))
    d.rectangle(box(806, 76, 814, 314), fill=(250, 250, 248)); d.rectangle(box(676, 195, 944, 203), fill=(250, 250, 248))
    rnd = random.Random(1)
    for j in range(26):
        x0 = rnd.uniform(680, 940); y0 = 76 + ((rnd.uniform(0, 238) + tt * 700) % 238)
        d.line(box(x0, y0, x0 - 6, min(314, y0 + 22)), fill=(170, 190, 225), width=L(3))


def bolt_a(tt, hits=(0.5, 2.2)):
    """Şimşek parlaklığı: her vuruşta tek kısa parlama (saniyede 3'ten az, ışığa duyarlılık)."""
    return max((1 - seg(tt, h, h + 0.35)) if tt >= h else 0.0 for h in hits)


def gag_thunder(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    storm(img, gt)
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 0.5:
            pet(img, sp, dict(idle(sp, gt), look=(1, -0.5)))
        elif tt < 1.4:
            u = seg(tt, 0.6, 1.3)
            pet(img, sp, dict(t=gt, x=lerp(CX, 760, sm(u)), puff=1.0, eyes='tiny', ears='flat', tail='puff', mouth='hiss',
                              run=1.0, walk=gt * 30, jump=60 * math.sin(math.pi * u)))
        else:
            pet(img, sp, dict(t=gt, x=760, scale=0.85, lie=1.0, puff=0.4, eyes='wide', look=(-0.6, 0.2), ears='flat', tail='tuck', mouth='flat'))
            pop(img, 'NOT COMING OUT.', 520, 240, 2.5, tt, (255, 255, 255), 74, -4)
        flash(img, bolt_a(tt))
        pop(img, 'BOOM!', 800, 380, 0.5, tt, (255, 230, 90), 110, 8, 0.8)
        if 0.5 <= tt < 0.9 or 2.2 <= tt < 2.6: shake = 10.0
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        scared = tt >= 0.5
        o = dict(idle(sp, gt))
        if scared:
            o = dict(t=gt, x=CX + 6 * math.sin(gt * 70), eyes='wide', look=(0, -0.7), ears='back', tail='tuck', mouth='o',
                     sy=0.92, head_dy=12)
        pet(img, sp, o)
        flash(img, bolt_a(tt))
        pop(img, 'BOOM!', 800, 380, 0.5, tt, (255, 230, 90), 110, 8, 0.8)
        if tt >= 1.2: pop(img, '*whimper*', 560, 520, 1.2, tt, (255, 255, 255), 56, 0, 1.0)
        if tt >= 2.5: pop(img, 'HOLD ME...', 560, 240, 2.5, tt, (255, 255, 255), 96, 4)
        if 0.5 <= tt < 0.9 or 2.2 <= tt < 2.6: shake = 10.0
    return shake


def treat_bone(img, x, y, ang=0.0, s=1.0):
    spr = Image.new('RGBA', (L(140 * s), L(70 * s)), (0, 0, 0, 0))
    c = (215, 160, 95)
    put(spr, cyl(c, 90 * s, 26 * s, 12 * s), 70 * s, 35 * s)
    for dx in (-48, 48):
        for dy in (-12, 12): put_sphere(spr, c, 70 * s + dx * s, 35 * s + dy * s, 30 * s, 30 * s, 0.3)
    put_rot(img, spr, x, y, ang)


def hand(img, x, y):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box(x - 46, -20, x + 46, y - 50), radius=L(30), fill=(70, 110, 190))
    put_sphere(img, (240, 195, 160), x, y - 20, 104, 92, 0.3)


def gag_treat(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    hx_, hy_ = 700, lerp(-60, 420, sm(seg(tt, 0.0, 0.5))) if t >= 0 else -60
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        fly = seg(tt, 1.7, 2.1)
        o = dict(t=gt, x=CX + 80, eyes='half', look=(0.4, -0.5), tail='up', wag=8, ws=3, mouth='flat')
        if 1.4 <= tt < 1.8: o.update(paw=sm(seg(tt, 1.4, 1.6)), eyes='angry')
        if tt >= 2.1: o.update(head_dy=20, mouth='open' if (tt * 4) % 1 < 0.5 else 'smile', mo=0.5, eyes='happy')
        info = pet(img, sp, o)
        hand(img, hx_, hy_ - (300 * seg(tt, 1.9, 2.4)))
        if tt < 1.7: treat_bone(img, hx_, hy_ + 20)
        elif tt < 2.1: treat_bone(img, lerp(hx_, info['nose'][0] + 30, fly), hy_ + 20 + 380 * fly * fly, 400 * fly)
        if 0.6 <= tt < 1.4: pop(img, 'SIT!', 860, 560, 0.6, tt, (255, 255, 255), 70, 0, 0.8)
        if 1.6 <= tt < 1.9: pop(img, 'SLAP!', 760, 520, 1.6, tt, (255, 120, 90), 80, 8)
        if tt >= 2.4: pop(img, 'I DO NOT DO TRICKS.', 540, 240, 2.4, tt, (255, 255, 255), 64, -4)
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        o = dict(t=gt, x=CX + 80, eyes='wide', look=(0.4, -0.5), tail='up', wag=50, ws=28, mouth='tongue', ears='perk')
        label = None
        if 0.5 <= tt < 1.0: o.update(sy=0.82, head_dy=-6); label = 'SIT!'
        elif 1.0 <= tt < 1.7:
            o.update(f=1 if math.cos((tt - 1.0) * 18) > 0 else -1); label = 'SPIN!'
        elif 1.7 <= tt < 2.2: o.update(paw=1.0); label = 'PAW!'
        elif 2.2 <= tt < 2.6: o.update(jump=150 * math.sin(math.pi * seg(tt, 2.2, 2.6))); label = 'JUMP!'
        elif tt >= 2.6: o.update(eyes='hearts', mouth='open' if (tt * 4) % 1 < 0.5 else 'tongue', head_dy=10)
        pet(img, sp, o)
        hand(img, hx_, hy_ - 300 * seg(tt, 2.8, 3.2))
        if tt < 2.6: treat_bone(img, hx_, hy_ + 20)
        if label: pop(img, label, 860, 560, {'SIT!': 0.5, 'SPIN!': 1.0, 'PAW!': 1.7, 'JUMP!': 2.2}[label], tt, (255, 225, 70), 74, 6)
        if tt >= 2.8: pop(img, 'GOOD BOY!', 540, 240, 2.8, tt, (255, 225, 70), 100, -4)
    return shake


def cake(img, x, y, lit=True, eaten=0.0, gt=0.0):
    put(img, cyl((250, 160, 190), 200, 90, 12), x, y - 45)
    put(img, cyl((255, 235, 240), 150, 70, 12), x, y - 120)
    if eaten > 0:
        put_sphere(img, (120, 70, 45), x + 30, y - 120, 110 * eaten, 50 * eaten, 0.2)
    for j in range(6): put_sphere(img, (230, 40, 70), x - 60 + j * 24, y - 154, 16, 16, 0.6)
    d = ImageDraw.Draw(img)
    d.rectangle(box(x - 6, y - 210, x + 6, y - 156), fill=(120, 190, 255))
    if lit:
        fl = 1 + 0.15 * math.sin(gt * 30)
        put_sphere(img, (255, 200, 60), x, y - 226, 26, 40 * fl, 0.2); put_sphere(img, (255, 250, 200), x, y - 222, 12, 20, 0.0)


def gag_cake(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0; cx_ = 730
    stand(img)
    if sp == 'cat':
        if t < 0: cake(img, cx_, 604, True, 0, gt); pet(img, sp, dict(idle(sp, gt), x=440)); return 0.0
        lit = tt < 1.8
        cake(img, cx_, 604, lit, 0, gt)
        o = dict(t=gt, x=440, eyes='open', look=(1, -0.6), tail='up', wag=10, ws=4)
        if 0.6 <= tt < 1.7: o.update(head_dx=26, head_dy=-16, eyes='closed', mouth='o')
        if 1.7 <= tt < 2.1: o.update(eyes='closed', mouth='open', mo=1.0, head_dy=10)
        if tt >= 2.1: o.update(eyes='half', look=(0, 0.1), mouth='smile')
        pet(img, sp, o)
        if tt >= 1.8:
            for j in range(4):
                u = (tt - 1.8 + j * 0.2) % 1.2
                put(img, fade(sphere((200, 200, 205), 40 + 50 * u, 40 + 50 * u, 0.0), max(0, 0.7 - 0.6 * u)), cx_ + 20 * math.sin(u * 6), 380 - 160 * u)
        pop(img, 'ACHOO!', 600, 300, 1.75, tt, (255, 255, 255), 90, -8, 1.0)
        if tt >= 2.4: pop(img, 'YOU ARE WELCOME.', 540, 240, 2.4, tt, (255, 225, 70), 70, 4)
    else:
        if t < 0: cake(img, cx_, 604, True, 0, gt); pet(img, sp, dict(idle(sp, gt), x=440)); return 0.0
        eaten = seg(tt, 1.0, 2.4)
        cake(img, cx_, 604, tt < 1.0, eaten, gt)
        o = dict(t=gt, x=lerp(440, 520, seg(tt, 0.3, 0.9)), eyes='wide', mouth='tongue', tail='up', wag=55, ws=30, look=(1, -0.3))
        if 1.0 <= tt < 2.4: o.update(head_dx=50, head_dy=-30, eyes='closed', mouth='open', mo=0.7 + 0.3 * abs(math.sin(tt * 20)))
        info = pet(img, sp, o)
        if tt >= 1.0:
            for j, (dx, dy, r) in enumerate(((-30, 30, 34), (24, 50, 28), (0, 70, 40), (40, -10, 24))):
                if tt >= 1.0 + j * 0.25: put_sphere(img, (255, 240, 245), info['hx'] + dx, info['hy'] + dy, r, r * 0.8, 0.3)
            particles(img, 71, 1.0, tt, 24, (cx_ - 20, 480), (-300, 300), (-500, -150), 1800, [(250, 160, 190), (255, 235, 240)], (12, 22), 0.8, emit=1.4)
            shake = 3.0 if tt < 2.4 else 0.0
        if tt >= 2.5: pop(img, 'BEST BIRTHDAY EVER!', 540, 240, 2.5, tt, (255, 225, 70), 70, -4)
    return shake


def letter(img, x, y, ang=0.0):
    spr = Image.new('RGBA', (L(110), L(76)), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    d.rectangle(box(2, 2, 108, 74), fill=(250, 248, 240), outline=(170, 160, 140), width=L(3))
    d.line(box(2, 2, 55, 40), fill=(170, 160, 140), width=L(3)); d.line(box(108, 2, 55, 40), fill=(170, 160, 140), width=L(3))
    d.rectangle(box(82, 10, 100, 28), fill=(230, 80, 80))
    put_rot(img, spr, x, y, ang)


LETTERS = [(560, 770, -12), (650, 790, 18), (720, 760, -30), (610, 740, 40), (690, 800, 5)]


def gag_mail(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    for j, (lx, ly, la) in enumerate(LETTERS):
        u = seg(tt, 0.2 + j * 0.12, 0.6 + j * 0.12) if t >= 0 else 0
        if t >= 0 and u > 0 and not (sp == 'dog' and tt >= 1.5):
            letter(img, lerp(lx - 200, lx, u), lerp(100, ly, u * u), la * u)
    if t >= 0: pop(img, 'MAIL!', 300, 300, 0.2, tt, (255, 255, 255), 80, -6, 0.8)
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 1.3: pet(img, sp, dict(idle(sp, gt), look=(1, 0.5)))
        elif tt < 2.0:
            u = seg(tt, 1.3, 2.0); pet(img, sp, dict(t=gt, x=lerp(CX, 560, sm(u)), walk=gt * 12, eyes='open', look=(1, 0.5), tail='up'))
        else:
            pet(img, sp, dict(t=gt, x=560, gy=GY - 10, lie=1.0, eyes='half', look=(0, 0.1), mouth='smile', tail='down'))
            pop(img, 'MINE NOW.', 540, 250, 2.2, tt, (255, 225, 70), 96, -4)
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 1.5:
            pet(img, sp, dict(t=gt, x=CX + 30 * seg(tt, 0.3, 1.0), eyes='angry', mouth='open' if (tt * 4) % 1 < 0.5 else 'flat', ears='perk',
                              tail='up', wag=30, ws=20, look=(1, 0)))
            for j, t0 in enumerate((0.4, 0.9)): pop(img, 'WOOF!', 560, 260 + 50 * j, t0, tt, (255, 255, 255), 80, 8 - 16 * j, 0.5)
        else:
            info = pet(img, sp, dict(t=gt, x=560, eyes='happy' if tt > 2.8 else 'angry', mouth='open', mo=0.7, head_dy=30 if tt < 2.8 else 0,
                                     head_dx=20 * math.sin(gt * 36) if tt < 2.8 else 0, tail='up', wag=50, ws=30))
            particles(img, 81, 1.5, tt, 50, (650, 740), (-500, 500), (-800, -200), 1300, [(250, 248, 240), (235, 230, 220)], (14, 28), 2.0, emit=1.3)
            if tt >= 2.8:
                letter(img, info['nose'][0] + 30, info['my'] + 16, 20)
                pop(img, 'MAIL DELIVERED.', 540, 240, 2.9, tt, (255, 225, 70), 80, 4)
            else: shake = 4.0
    return shake


def sunbeam(img, x, a=1.0):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon([(L(x - 160), L(840)), (L(x + 200), L(840)), (L(x + 130), L(700)), (L(x - 90), L(700))],
                                  fill=(255, 235, 140, int(160 * a)))
    layer = layer.filter(ImageFilter.GaussianBlur(L(10)))
    img.alpha_composite(layer)


def gag_sunbeam(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    sx_ = lerp(600, 520, tt / 4)
    sunbeam(img, sx_)
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 1.0:
            pet(img, sp, dict(t=gt, x=lerp(CX, sx_, sm(seg(tt, 0.1, 1.0))), walk=gt * 12, eyes='half', tail='up', look=(1, 0.5)))
        else:
            melt = sm(seg(tt, 1.0, 2.2))
            pet(img, sp, dict(t=gt, x=sx_, lie=1.0, sx=1 + 0.25 * melt, sy=1 - 0.22 * melt, eyes='closed', mouth='smile', tail='down',
                              head_dy=20 * melt))
            if tt > 1.4: zzz(img, gt, sx_ + 200, 560)
            if tt >= 2.2: pop(img, 'PURE BLISS.', 540, 250, 2.2, tt, (255, 225, 70), 96, -4)
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 1.6:
            pet(img, sp, dict(t=gt, x=sx_, lie=1.0, eyes='closed' if tt < 0.9 else 'open', mouth='smile' if tt < 0.9 else 'tongue', tail='down'))
        else:
            info = pet(img, sp, dict(t=gt, x=lerp(sx_, 330, sm(seg(tt, 1.6, 2.4))), eyes='wide', mouth='tongue', tail='up', wag=20, ws=10,
                                     f=-1, walk=gt * 14 if tt < 2.4 else None, sy=1 + 0.03 * math.sin(gt * 20)))
            for j in range(3):
                put_sphere(img, (120, 190, 250), info['hx'] + 60 - j * 50, info['hy'] - 90 + 8 * math.sin(gt * 6 + j), 16, 24, 0.8)
            pop(img, 'TOO HOT!', 600, 250, 1.8, tt, (255, 120, 90), 100, 5)
    return shake


BUBBLES = [(0.0, 560, 1.0), (0.4, 720, 0.8), (0.8, 640, 1.2), (1.2, 820, 0.9), (1.6, 520, 1.1), (2.0, 700, 1.0), (2.4, 600, 0.9)]


def bubble_pos(b, tt):
    t0, x0, s = b
    a = tt - t0
    return x0 + 60 * math.sin(a * 2 + x0), 760 - 140 * a, 70 * s


def bubble(img, x, y, r):
    d = ImageDraw.Draw(img)
    d.ellipse(box(x - r / 2, y - r / 2, x + r / 2, y + r / 2), outline=(200, 230, 255), width=L(4))
    d.arc(box(x - r / 2 + 8, y - r / 2 + 8, x + r / 2 - 8, y + r / 2 - 8), 200, 250, fill=(255, 255, 255), width=L(5))
    put_sphere(img, (255, 255, 255), x - r * 0.18, y - r * 0.2, r * 0.18, r * 0.12, 0.0)


def gag_bubbles(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        o = dict(t=gt, x=CX + 60, eyes='wide', look=(1, -0.6), tail='up', wag=25, ws=14)
        if 0.8 <= tt < 1.6: o.update(paw=abs(math.sin((tt - 0.8) * 7)))
        if 1.9 <= tt < 2.4: o.update(eyes='closed', mouth='open', mo=1.0)
        if tt >= 2.4: o.update(eyes='half', look=(0, 0.1), mouth='flat', tail='down')
        info = pet(img, sp, o)
        for b in BUBBLES:
            x, y, r = bubble_pos(b, tt)
            if tt >= b[0] and y > 80 and not (b[0] == 0.8 and tt > 1.85): bubble(img, x, y, r)
        if 1.6 <= tt < 1.85: bubble(img, lerp(640, info['nose'][0], seg(tt, 1.6, 1.85)), lerp(560, info['nose'][1], seg(tt, 1.6, 1.85)), 70)
        pop(img, 'POP!', info['nose'][0] + 60, info['nose'][1] - 80, 1.85, tt, (255, 255, 255), 70, 8, 0.6)
        pop(img, 'ACHOO!', 560, 260, 1.95, tt, (255, 255, 255), 96, -6, 0.9)
        if tt >= 2.5: pop(img, 'BETRAYED.', 540, 250, 2.5, tt, (255, 255, 255), 100, 4)
    else:
        if t < 0: pet(img, sp, idle(sp, gt)); return 0.0
        snap = abs(math.sin(tt * 6))
        o = dict(t=gt, x=CX + 120 + 60 * math.sin(tt * 2), jump=110 * snap if 0.4 < tt < 3 else 0, eyes='wide', look=(0.6, -0.7),
                 mouth='open' if snap > 0.6 else 'tongue', mo=0.8, tail='up', wag=55, ws=30, ears='perk')
        if tt >= 3.0: o.update(eyes='happy', mouth='tongue', jump=0)
        info = pet(img, sp, o)
        for k, b in enumerate(BUBBLES):
            x, y, r = bubble_pos(b, tt)
            if tt >= b[0] and y > 80 and tt < b[0] + 0.55 + 0.1 * k: bubble(img, x, y, r)
            elif b[0] + 0.55 + 0.1 * k <= tt < b[0] + 0.75 + 0.1 * k: pop(img, 'POP!', x, y, b[0] + 0.55 + 0.1 * k, tt, (255, 255, 255), 54, 10, 0.25)
        if tt >= 3.0:
            bubble(img, info['nose'][0], info['nose'][1] - 30, 60)
            pop(img, 'BEST DAY EVER!', 540, 240, 3.0, tt, (255, 225, 70), 84, -4)
    return shake


def fishbowl(img, x, y, gt, water=1.0, splash=False):
    put_sphere(img, (110, 180, 240), x, y + 20 * (1 - water), 230, 200 * water + 10, 0.4)
    fx = x + 50 * math.sin(gt * 1.6); ff = 1 if math.cos(gt * 1.6) > 0 else -1
    put_sphere(img, (255, 140, 40), fx, y + 10, 70, 44, 0.6)
    ImageDraw.Draw(img).polygon([(L(fx - ff * 30), L(y + 10)), (L(fx - ff * 62), L(y - 12)), (L(fx - ff * 62), L(y + 32))], fill=(255, 120, 30))
    put_sphere(img, DARK, fx + ff * 18, y + 2, 10, 10, 0.1)
    d = ImageDraw.Draw(img)
    d.ellipse(box(x - 130, y - 120, x + 130, y + 120), outline=(210, 235, 250), width=L(6))
    d.ellipse(box(x - 70, y - 128, x + 70, y - 108), fill=(150, 200, 240))
    d.arc(box(x - 100, y - 90, x - 20, y + 60), 140, 220, fill=(255, 255, 255), width=L(8))


def gag_fish(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    stand(img)
    if sp == 'cat':
        if t < 0: fishbowl(img, 730, 470, gt); pet(img, sp, dict(idle(sp, gt), x=470)); return 0.0
        fishbowl(img, 730, 470, gt, 1.0 - 0.15 * seg(tt, 1.6, 1.8))
        wet = sm(seg(tt, 1.6, 1.9))
        o = dict(t=gt, x=470, eyes='wide', look=(1, -0.2), tail='up', wag=30, ws=16, mouth='smile')
        if 0.8 <= tt < 1.6: o.update(paw=sm(seg(tt, 0.8, 1.2)), eyes='wide')
        if tt >= 1.6: o.update(wet=wet, eyes='tiny' if tt < 2.3 else 'angry', puff=0.7, ears='flat', mouth='o' if tt < 2.3 else 'flat', tail='puff')
        pet(img, sp, o)
        if 1.6 <= tt: particles(img, 91, 1.6, tt, 30, (660, 420), (-520, 100), (-500, -100), 1800, [(150, 210, 255)], (12, 22), 0.9)
        pop(img, 'SPLASH!', 640, 260, 1.6, tt, (120, 200, 255), 96, -6, 0.9)
        if tt >= 2.5: pop(img, 'THIS IS WAR.', 540, 240, 2.5, tt, (255, 255, 255), 90, 4)
        if 1.6 <= tt < 1.9: shake = 8.0
    else:
        if t < 0: fishbowl(img, 730, 470, gt); pet(img, sp, dict(idle(sp, gt), x=470)); return 0.0
        fishbowl(img, 730, 470, gt)
        o = dict(t=gt, x=470, eyes='wide', look=(1, -0.2), ears='perk', tail='up', wag=40, ws=24, mouth='tongue')
        if 0.3 <= tt < 1.3: o.update(mouth='open' if (tt * 5) % 1 < 0.5 else 'flat', eyes='angry')
        if 1.3 <= tt < 2.6: o.update(head_dx=-20, head_dy=-10, eyes='open', look=(1, -0.3), mouth='o')
        if tt >= 2.6: o.update(head_dx=60, head_dy=-30, eyes='closed', mouth='tongue')
        pet(img, sp, o)
        for j, t0 in enumerate((0.35, 0.85)): pop(img, 'WOOF!', 560, 250 + 40 * j, t0, tt, (255, 255, 255), 80, -8 + 16 * j, 0.45)
        if 1.3 <= tt < 2.6:
            bubble(img, 760 + 10 * math.sin(gt * 3), 420 - 140 * seg(tt, 1.3, 2.3), 34)
            pop(img, '???', 520, 300, 1.5, tt, (255, 255, 255), 110, 0)
        if tt >= 2.7:
            for j in range(3): put_sphere(img, (240, 170, 190), 640 + j * 22, 470 + 8 * math.sin(j * 2), 26, 16, 0.3)
            pop(img, 'FRIEND?', 540, 250, 2.8, tt, (255, 225, 70), 100, -4)
    return shake


def yarn(img, x, y, r=60):
    put_sphere(img, (225, 50, 70), x, y, r * 2, r * 2, 0.5)
    d = ImageDraw.Draw(img)
    for j in range(4):
        d.arc(box(x - r + 8 + j * 6, y - r + 4, x + r - 8 - j * 6, y + r - 4), 200 + j * 30, 340 + j * 30, fill=(250, 110, 130), width=L(5))


def tangle(img, x, y, w, h, n, seed):
    d = ImageDraw.Draw(img); rnd = random.Random(seed)
    for j in range(n):
        pts = [(L(x + rnd.uniform(-w, w)), L(y + rnd.uniform(-h, h))) for _ in range(4)]
        d.line(pts, fill=(225, 50, 70), width=L(6), joint='curve')


def gag_yarn(img, sp, t, gt):
    tt = max(t, 0.0); shake = 0.0
    if sp == 'cat':
        if t < 0: yarn(img, 700, 770); pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 1.2:
            yarn(img, 700 - 120 * seg(tt, 0.6, 1.2), 770)
            pet(img, sp, dict(t=gt, x=CX + 60 * seg(tt, 0.2, 0.8), eyes='wide', look=(1, 0.5), paw=abs(math.sin(tt * 6)) * (tt > 0.6), tail='up', wag=30, ws=18))
        else:
            roll = seg(tt, 1.2, 2.2)
            info = pet(img, sp, dict(t=gt, x=CX + 80 + 60 * math.sin(roll * 6) * (1 - roll), lie=1.0, eyes='tiny' if tt >= 2.2 else 'wide',
                                     look=(0, -0.3), mouth='o' if tt >= 2.2 else 'smile', tail='down'))
            tangle(img, info['hx'] - 100, info['by'] - 30, 210, 110, int(4 + 14 * roll), 5)
            yarn(img, 640, 790, 30)
            if tt >= 2.4: pop(img, 'HELP.', 540, 250, 2.4, tt, (255, 255, 255), 110, -4)
    else:
        if t < 0: yarn(img, 700, 770); pet(img, sp, idle(sp, gt)); return 0.0
        if tt < 0.8:
            yarn(img, 700, 770); pet(img, sp, dict(idle(sp, gt), look=(1, 0.5), eyes='wide', ears='perk'))
        else:
            u = seg(tt, 0.8, 3.0)
            x = CX + 260 * math.sin(u * 7) if tt < 3.0 else CX + 120
            f = 1 if math.cos(u * 7) >= 0 else -1
            info = pet(img, sp, dict(t=gt, x=x, f=f if tt < 3.0 else 1, run=0.8 if tt < 3.0 else 0, walk=gt * 26 if tt < 3.0 else None,
                                     eyes='happy', mouth='open', mo=0.5, tail='up', wag=55, ws=30))
            d = ImageDraw.Draw(img)
            pts = [(L(700), L(790))] + [(L(CX + 260 * math.sin(v * 7)), L(760 - 40 * math.sin(v * 13))) for v in np.linspace(0, u, 20)]
            d.line(pts + [(L(info['nose'][0]), L(info['my'] + 10))], fill=(225, 50, 70), width=L(6), joint='curve')
            yarn(img, info['nose'][0] + 10, info['my'] + 26, 28)
            if tt >= 3.0: pop(img, 'REDECORATED!', 540, 240, 3.0, tt, (255, 225, 70), 90, 4)
    return shake


GAGS.update({
    'thunder': dict(fn=gag_thunder, title='WHEN THE THUNDER STARTS', name='Thunder', wall=(160, 170, 195),
                    cat=[(0.0, 'rain', 4.0), (0.5, 'thunder'), (0.7, 'hiss'), (2.2, 'thunder')],
                    dog=[(0.0, 'rain', 4.0), (0.5, 'thunder'), (1.2, 'whine'), (2.2, 'thunder'), (2.6, 'whine')]),
    'treat': dict(fn=gag_treat, title='WHEN THEY SEE A TREAT', name='Treat', wall=(250, 225, 200),
                  cat=[(0.6, 'meow_flat'), (1.6, 'swipe'), (1.7, 'whoosh_s'), (2.2, 'crunch')],
                  dog=[(0.5, 'boing'), (1.0, 'spin', 0.7), (1.7, 'pop'), (2.2, 'boing'), (2.6, 'crunch'), (2.9, 'bark')]),
    'cake': dict(fn=gag_cake, title='BIRTHDAY CAKE', name='Birthday Cake', wall=(250, 215, 230),
                 cat=[(0.6, 'sniff'), (1.75, 'sneeze'), (2.4, 'purr', 1.4)], dog=[(0.3, 'bark'), (1.0, 'chomp', 1.4), (2.5, 'bark')]),
    'mail': dict(fn=gag_mail, title='WHEN THE MAIL ARRIVES', name='Mail', wall=(215, 230, 205),
                 cat=[(0.2, 'slide'), (1.3, 'whoosh_s'), (2.1, 'purr', 1.6)],
                 dog=[(0.2, 'slide'), (0.4, 'bark'), (0.9, 'bark'), (1.5, 'rip', 1.3), (2.9, 'bark')]),
    'sunbeam': dict(fn=gag_sunbeam, title='A SUNNY SPOT ON THE FLOOR', name='Sunbeam', wall=(250, 240, 200),
                    cat=[(1.0, 'purr', 2.8)], dog=[(0.9, 'pant', 2.5), (1.8, 'whine')]),
    'bubbles': dict(fn=gag_bubbles, title='BUBBLES!', name='Bubbles', wall=(205, 230, 250),
                    cat=[(0.8, 'swipe'), (1.2, 'swipe'), (1.85, 'pop'), (1.95, 'sneeze')],
                    dog=[(0.95 + 0.1 * k + BUBBLES[k][0], 'pop') for k in range(7)] + [(0.5, 'bark'), (3.0, 'bark')]),
    'fish': dict(fn=gag_fish, title='MEETING THE GOLDFISH', name='Goldfish', wall=(200, 225, 240),
                 cat=[(0.8, 'meow_small'), (1.6, 'splash'), (1.8, 'yowl')], dog=[(0.35, 'bark'), (0.85, 'bark'), (1.4, 'boing'), (2.7, 'lick'), (3.0, 'lick')]),
    'yarn': dict(fn=gag_yarn, title='A BALL OF YARN', name='Yarn', wall=(235, 215, 245),
                 cat=[(0.6, 'swipe'), (1.2, 'whoosh_s'), (2.3, 'meow_small')], dog=[(0.4, 'bark'), (0.8, 'zoom'), (1.8, 'zoom'), (3.0, 'bark')]),
})

rng = np.random.default_rng(1)
def t_arr(d): return np.arange(int(SR * d)) / SR
def noise(d): return rng.uniform(-1, 1, int(SR * d))
def dec(d, k): return np.exp(-t_arr(d) * k)
def lpf(x, k): return np.convolve(x, np.ones(k) / k, mode='same') if k > 1 else x
def bell(d, p=1.0): return np.sin(np.linspace(0, np.pi, int(SR * d))) ** p
def osc(freq, shape='sine'):
    ph = 2 * np.pi * np.cumsum(freq) / SR
    if shape == 'saw': return 2 * ((ph / (2 * np.pi)) % 1) - 1
    return np.sin(ph)
def sweep(f0, f1, d, shape='sine'): return osc(np.geomspace(f0, f1, int(SR * d)), shape)


def sfx(name, dur=None):
    if name == 'pop': x, g = sweep(900, 240, 0.09) * dec(0.09, 35), 0.6
    elif name == 'crunch':
        n = noise(0.18); m = (rng.uniform(0, 1, len(n) // 220 + 1) > 0.45).repeat(220)[:len(n)]
        x, g = lpf(n, 2) * m * dec(0.18, 14), 0.55
    elif name == 'gulp': x, g = sweep(420, 140, 0.16) * bell(0.16), 0.7
    elif name == 'burp':
        s = sweep(95, 70, 0.7, 'saw') * (1 + 0.5 * noise(0.7)); x, g = lpf(s, 18) * bell(0.7, 0.5), 1.0
    elif name == 'ring':
        tt = t_arr(dur); x = (np.sin(2 * np.pi * 1750 * tt) + 0.6 * np.sin(2 * np.pi * 2630 * tt)) * (np.sin(2 * np.pi * 22 * tt) > 0); g = 0.22
    elif name == 'ring_weak':
        x = osc(np.linspace(1500, 1000, int(SR * 0.3))) * (np.sin(2 * np.pi * 18 * t_arr(0.3)) > 0) * dec(0.3, 5); g = 0.12
    elif name == 'click': x, g = np.diff(noise(0.02), prepend=0) * dec(0.02, 200), 0.5
    elif name in ('smash', 'bonk'):
        d = 0.6 if name == 'smash' else 0.35
        th = sweep(110 if name == 'smash' else 160, 40, d) * dec(d, 6)
        nz = lpf(noise(d), 3) * dec(d, 9)
        cl = sum(np.sin(2 * np.pi * f * t_arr(d)) * dec(d, k) for f, k in ((523, 7), (787, 9), (1187, 11)))
        x, g = th + 0.7 * nz + 0.25 * cl, 1.0 if name == 'smash' else 0.85
    elif name in ('whoosh', 'whoosh_s'):
        d = 0.4 if name == 'whoosh' else 0.22; x = lpf(noise(d), 10) * bell(d, 2); g = 0.6 if name == 'whoosh' else 0.3
    elif name == 'squirt': x, g = lpf(noise(0.2), 5) * dec(0.2, 10) + 0.3 * sweep(700, 250, 0.2) * dec(0.2, 15), 0.5
    elif name == 'slurp':
        tt = t_arr(dur); n = lpf(noise(dur), 6) * (0.6 + 0.4 * np.sin(2 * np.pi * 8 * tt))
        s = osc(220 + 70 * np.sin(2 * np.pi * 6 * tt)); x, g = (n * 1.5 + 0.35 * s) * bell(dur, 0.3), 0.55
    elif name == 'ahh':
        tt = t_arr(0.8); f = 170 * (1 - 0.15 * tt / 0.8) + 4 * np.sin(2 * np.pi * 5.5 * tt)
        x, g = lpf(osc(f, 'saw'), 9) * bell(0.8, 0.4), 0.7
    elif name == 'inhale': x, g = lpf(noise(dur), 4) * np.linspace(0, 1, int(SR * dur)) ** 2, 0.6
    elif name == 'blow': x, g = lpf(noise(dur), 12) * bell(dur, 0.5), 0.8
    elif name == 'splat': x, g = sweep(80, 40, 0.5) * dec(0.5, 8) + 3 * lpf(noise(0.5), 20) * dec(0.5, 10), 1.0
    elif name == 'horn':
        tt = t_arr(0.55); x, g = lpf(osc(520 + 30 * np.sin(2 * np.pi * 6 * tt), 'saw'), 5) * bell(0.55, 0.3), 0.3
    elif name == 'clap': x, g = np.diff(noise(0.08), prepend=0) * dec(0.08, 60), 0.45
    elif name == 'sting':
        x = lpf(osc(np.full(int(SR * 0.9), 110.0), 'saw') + osc(np.full(int(SR * 0.9), 55.6), 'saw'), 6) * dec(0.9, 3.5)
        x += 0.5 * np.sin(2 * np.pi * 55 * t_arr(0.9)) * dec(0.9, 3); g = 0.55
    elif name == 'ding':
        x = np.sin(2 * np.pi * 1320 * t_arr(0.9)) * dec(0.9, 5) + 0.4 * np.sin(2 * np.pi * 2640 * t_arr(0.9)) * dec(0.9, 8); g = 0.35
    elif name == 'boing':
        tt = t_arr(0.5); x, g = osc(180 + 300 * tt + 40 * np.sin(2 * np.pi * 18 * tt)) * dec(0.5, 5), 0.4
    elif name == 'yawn':
        tt = t_arr(0.9); f = np.linspace(330, 190, len(tt)) + 6 * np.sin(2 * np.pi * 5 * tt)
        x, g = (osc(f) + 0.3 * lpf(noise(0.9), 8)) * bell(0.9, 0.6), 0.3
    elif name == 'psst': x, g = np.diff(noise(0.25), prepend=0) * dec(0.25, 9), 0.4
    elif name == 'fizz': x, g = np.diff(noise(dur), prepend=0) * (rng.uniform(0, 1, int(SR * dur)) > 0.6) * dec(dur, 1.5), 0.45
    elif name == 'rattle':
        tt = t_arr(dur); x, g = lpf(noise(dur), 3) * (np.sin(2 * np.pi * 15 * tt) > 0.3), 0.45
    elif name == 'lick': x, g = lpf(noise(0.14), 4) * bell(0.14) + 0.4 * sweep(300, 700, 0.14) * bell(0.14), 0.45
    elif name == 'freeze':
        tt = t_arr(1.2); x = sum(np.sin(2 * np.pi * f * (1 - 0.25 * tt / 1.2) * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * (9 + j) * tt))
                                for j, f in enumerate((2100, 2650, 3150, 3700))) * dec(1.2, 2); g = 0.3
    elif name == 'bang': x, g = sweep(150, 40, 0.4) * dec(0.4, 8) + lpf(noise(0.4), 2) * dec(0.4, 14), 1.0
    elif name == 'carve':
        tt = t_arr(0.28); x, g = lpf(noise(0.28), 3) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * tt)) * bell(0.28), 0.4
    else: raise ValueError(name)
    return x / (np.abs(x).max() + 1e-9) * g


def music(dur, seed):
    rnd = random.Random(seed)
    bpm = rnd.choice([116, 120, 124, 128, 132]); beat = 60 / bpm; key = rnd.randint(-3, 3)
    out = np.zeros(int(SR * dur) + SR)
    def mf(m): return 440 * 2 ** ((m + key - 69) / 12)
    def pluck(f, d, k, bright):
        tt = t_arr(d); return (np.sin(2 * np.pi * f * tt) + bright * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt * k)
    def add(t0, x):
        i0 = int(t0 * SR); out[i0:i0 + len(x)] += x[:max(0, len(out) - i0)]
    prog = rnd.choice([[48, 45, 41, 43], [48, 43, 45, 41], [45, 41, 48, 43], [48, 41, 43, 48]])
    penta = [60, 62, 64, 67, 69, 72, 74, 76]; bright = rnd.uniform(0.2, 0.5)
    motif = [None if rnd.random() < 0.3 else rnd.choice(penta) for _ in range(16)]
    motif2 = [m if (m is None or rnd.random() < 0.6) else rnd.choice(penta) for m in motif]
    for b in range(int(dur / beat) + 1):
        t0 = b * beat; bar = b // 4; root = prog[bar % 4]
        add(t0, 0.9 * pluck(mf(root if b % 2 == 0 else root + 7), 0.35, 7, 0.35))
        if b % 2 == 0: add(t0, 0.8 * sweep(130, 45, 0.18) * dec(0.18, 18))
        else: add(t0, 0.25 * lpf(noise(0.12), 2) * dec(0.12, 30))
        add(t0 + beat / 2, 0.12 * np.diff(noise(0.03), prepend=0) * dec(0.03, 120))
        mot = motif if (bar // 2) % 2 == 0 else motif2
        for h in (0, 1):
            n = mot[(b * 2 + h) % 16]
            if n is not None: add(t0 + h * beat / 2, 0.32 * pluck(mf(n), 0.25, 11, bright))
    out = out[:int(SR * dur)]
    out *= np.clip((dur - t_arr(dur)) / 0.6, 0, 1)
    return out / np.abs(out).max() * 0.22




def psfx(name, dur=None):
    """Evcil hayvan sesleri (kodla sentez) + Bloop motorunun genel efektleri."""
    if name in ('meow', 'meow_small', 'meow_flat', 'yowl'):
        d = {'meow': 0.55, 'meow_small': 0.35, 'meow_flat': 0.6, 'yowl': 1.0}[name]
        tt = t_arr(d); u = tt / d
        f0 = {'meow': 560, 'meow_small': 820, 'meow_flat': 430, 'yowl': 620}[name]
        f = f0 * (0.85 + 0.45 * np.sin(np.pi * u) ** (1.5 if name != 'meow_flat' else 0.6)) + 12 * np.sin(2 * np.pi * 6 * tt)
        if name == 'yowl': f = f * (1 + 0.25 * np.sin(2 * np.pi * 3 * tt))
        s = osc(f, 'saw'); s = lpf(s, 4) - 0.6 * lpf(s, 22)
        x, g = s * bell(d, 0.6), 0.55 if name != 'yowl' else 0.75
    elif name == 'hiss':
        n = noise(0.75); x, g = np.diff(np.diff(n, prepend=0), prepend=0) * bell(0.75, 0.4) * (1 - 0.3 * np.sin(2 * np.pi * 9 * t_arr(0.75))), 0.55
    elif name in ('bark', 'growl', 'whine'):
        if name == 'bark':
            d = 0.22; f = np.geomspace(330, 180, int(SR * d)); s = osc(f, 'saw') + 0.6 * noise(d)
            x, g = lpf(s, 6) * dec(d, 9) * np.clip(t_arr(d) * 80, 0, 1), 0.9
        elif name == 'growl':
            d = 0.7; tt = t_arr(d); s = osc(np.full(len(tt), 95.0), 'saw') * (0.6 + 0.4 * np.sin(2 * np.pi * 28 * tt)) + 0.4 * noise(d)
            x, g = lpf(s, 10) * bell(d, 0.4), 0.7
        else:
            d = 0.8; tt = t_arr(d); f = 900 + 250 * np.sin(np.pi * tt / d) + 30 * np.sin(2 * np.pi * 7 * tt)
            x, g = osc(f) * bell(d, 0.7) * 0.8 + 0.1 * lpf(noise(d), 4) * bell(d), 0.35
    elif name == 'purr':
        tt = t_arr(dur); s = lpf(noise(dur), 30) * (0.5 + 0.5 * np.sin(2 * np.pi * 26 * tt)) + 0.3 * osc(np.full(len(tt), 52.0), 'saw') * (np.sin(2 * np.pi * 26 * tt) > 0)
        x, g = lpf(s, 8) * bell(dur, 0.3), 0.5
    elif name == 'squeak':
        d = 0.18; n_ = int(SR * d); n1 = int(n_ * 0.4)
        x, g = osc(np.concatenate([np.geomspace(1500, 2700, n1), np.geomspace(2700, 1700, n_ - n1)])) * bell(d, 0.5), 0.35
    elif name == 'crash':
        d = 0.9; tt = t_arr(d)
        x = np.diff(noise(d), prepend=0) * dec(d, 7) + sum(np.sin(2 * np.pi * fr * tt) * dec(d, k) * 0.3 for fr, k in ((2300, 9), (3100, 11), (4200, 14), (5100, 8)))
        x = x * (rng.uniform(0, 1, len(tt)) > 0.2); g = 0.8
    elif name in ('splash', 'shower', 'shake'):
        d = dur or (0.7 if name == 'splash' else 1.0); tt = t_arr(d)
        n = lpf(noise(d), 3 if name != 'splash' else 6)
        env = dec(d, 5) if name == 'splash' else bell(d, 0.3) * (0.6 + 0.4 * np.sin(2 * np.pi * (22 if name == 'shake' else 4) * tt))
        x, g = n * env, 0.6 if name == 'splash' else 0.4
    elif name == 'dingdong':
        tt = t_arr(1.2); a = (tt < 0.55)
        x = (np.sin(2 * np.pi * 660 * tt) * a * np.exp(-tt * 3) + np.sin(2 * np.pi * 523 * tt) * (~a) * np.exp(-(tt - 0.55) * 3) * (tt >= 0.55)) ; g = 0.45
    elif name == 'vacuum':
        tt = t_arr(dur); s = lpf(noise(dur), 5) + 0.4 * osc(np.full(len(tt), 120.0), 'saw')
        x, g = s * np.clip(tt / 0.3, 0, 1) * np.clip((dur - tt) / 0.2, 0, 1), 0.3
    elif name in ('rip', 'chomp', 'wag', 'spin'):
        tt = t_arr(dur); rate = {'rip': 11, 'chomp': 8, 'wag': 9, 'spin': 4}[name]
        n = lpf(noise(dur), {'rip': 2, 'chomp': 3, 'wag': 14, 'spin': 12}[name])
        x, g = n * (np.sin(2 * np.pi * rate * tt) > 0.2) * bell(dur, 0.2), {'rip': 0.5, 'chomp': 0.5, 'wag': 0.25, 'spin': 0.3}[name]
    elif name in ('pour', 'slide', 'sniff', 'swipe', 'zoom', 'thud'):
        if name == 'pour': x, g = lpf(noise(0.6), 2) * (rng.uniform(0, 1, int(SR * 0.6)) > 0.7) * bell(0.6, 0.3), 0.4
        elif name == 'slide': x, g = lpf(noise(0.5), 18) * bell(0.5), 0.4
        elif name == 'sniff':
            tt = t_arr(0.6); x, g = lpf(noise(0.6), 6) * (np.sin(2 * np.pi * 5 * tt) > 0.3) * bell(0.6, 0.3), 0.35
        elif name == 'swipe': x, g = lpf(noise(0.18), 3) * bell(0.18, 2), 0.5
        elif name == 'zoom': x, g = sweep(300, 1400, 0.5) * bell(0.5) * 0.4 + lpf(noise(0.5), 8) * bell(0.5, 2), 0.5
        else: x, g = sweep(140, 50, 0.25) * dec(0.25, 14), 0.8
    elif name == 'rain':
        x, g = lpf(noise(dur), 2) * (0.7 + 0.3 * rng.uniform(0, 1, int(SR * dur))) * np.clip(t_arr(dur) / 0.3, 0, 1), 0.18
    elif name == 'thunder':
        d = 1.8; tt = t_arr(d)
        x = lpf(noise(d), 40) * (np.exp(-tt * 2.2) + 0.6 * np.exp(-np.abs(tt - 0.35) * 8)) + 0.6 * np.diff(noise(d), prepend=0) * np.exp(-tt * 30)
        g = 1.0
    elif name == 'sneeze':
        d1, d2 = 0.3, 0.25
        a = osc(np.geomspace(500, 900, int(SR * d1)), 'saw') * bell(d1, 0.8) * 0.4
        b = np.diff(noise(d2), prepend=0) * dec(d2, 12)
        x, g = np.concatenate([lpf(a, 6), b]), 0.6
    elif name == 'pant':
        tt = t_arr(dur); x, g = lpf(noise(dur), 5) * (np.sin(2 * np.pi * 4.5 * tt) > 0.1) * bell(dur, 0.2), 0.35
    else:
        return sfx(name, dur)
    return x / (np.abs(x).max() + 1e-9) * g


def total(plan=None):
    return INTRO + GAG * len((plan or PLAN)['gags']) + OUTRO


# ---------------------------------------------------------------- kare
def finish_panel(p, shake, gt, dim):
    z = 1.15; cx, cy = L(560), L(470)
    dx = math.sin(gt * 90) * shake * S if shake > 0.5 else 0.0
    dy = math.cos(gt * 77) * shake * S if shake > 0.5 else 0.0
    p = p.transform(p.size, Image.AFFINE, (1 / z, 0, cx - p.width / 2 / z + dx, 0, 1 / z, cy - p.height / 2 / z + dy), resample=Image.BILINEAR)
    p = p.convert('RGB').reduce(S)
    if dim: p = ImageEnhance.Brightness(p).enhance(0.55)
    return p


def outro_panel(sp, gt):
    img = bg(GAGS[PLAN['gags'][0]]['wall'], sp)
    if sp == 'cat':
        pet(img, sp, dict(t=gt, eyes='half', look=(0, 0.1), tail='up', wag=10, ws=3, mouth='smile', paw=0.5 + 0.5 * math.sin(gt * 3)))
    else:
        pet(img, sp, dict(t=gt, eyes='wide', look=(0, 0), tail='up', wag=60, ws=30, mouth='tongue', ears='perk', jump=30 * abs(math.sin(gt * 8))))
    return img


def render_frame(i):
    T = i / FPS
    gags = [GAGS[k] for k in PLAN['gags']]
    A, B, Q, top_sp, bot_sp = FORMATS[PLAN['format']]
    frame = Image.new('RGB', (W, H), (24, 20, 38))
    if T < INTRO:
        title = f'{A} VS {B}'; tstart = 0.0; g = gags[0]
        for sp, y in ((top_sp, TOP), (bot_sp, TOP + PH)):
            img = bg(g['wall'], sp); g['fn'](img, sp, -1, T); frame.paste(finish_panel(img, 0, T, False), (0, y))
    elif T < INTRO + GAG * len(gags):
        k = int((T - INTRO) // GAG); gl = T - INTRO - k * GAG; g = gags[k]
        title = g['title']; tstart = INTRO + k * GAG
        SPEAKER[0] = top_sp if gl < NDUR else None
        img = bg(g['wall'], top_sp); sn = g['fn'](img, top_sp, min(gl, NDUR), T)
        frame.paste(finish_panel(img, sn if gl < NDUR else 0, T, gl >= NDUR), (0, TOP))
        SPEAKER[0] = bot_sp if gl >= NDUR else None
        img = bg(g['wall'], bot_sp); sp_ = g['fn'](img, bot_sp, gl - NDUR, T)
        SPEAKER[0] = None
        frame.paste(finish_panel(img, sp_, T, gl < NDUR), (0, TOP + PH))
    else:
        title = Q; tstart = INTRO + GAG * len(gags)
        frame.paste(finish_panel(outro_panel(top_sp, T), 0, T, False), (0, TOP))
        frame.paste(finish_panel(outro_panel(bot_sp, T), 0, T, False), (0, TOP + PH))
    d = ImageDraw.Draw(frame)
    put_text_px(frame, title, W // 2, TOP // 2 + 4, 70, (255, 255, 255), scale=back(seg(T, tstart, tstart + 0.25)), max_w=1030)
    for y0, txt, c in ((TOP, f'1. {A}', (240, 140, 50)), (TOP + PH, f'2. {B}', (70, 140, 230))):
        spr = text_spr(txt, 44, (255, 255, 255))
        d.rounded_rectangle([22, y0 + 22, 22 + spr.width + 28, y0 + 22 + spr.height + 20], radius=16, fill=c, outline=DARK, width=4)
        frame.paste(spr, (36, y0 + 32), spr)
    d.rectangle([0, TOP + PH - 5, W, TOP + PH + 5], fill=DARK)
    d.ellipse([W // 2 - 56, TOP + PH - 56, W // 2 + 56, TOP + PH + 56], fill=(255, 210, 50), outline=DARK, width=6)
    put_text_px(frame, 'VS', W // 2, TOP + PH + 2, 54, (255, 255, 255))
    if T < INTRO:
        put_text_px(frame, A, W // 2, TOP + 300, 150, (255, 170, 80), scale=back(seg(T, 0.0, 0.25)), rot=-5, max_w=1000)
        put_text_px(frame, B, W // 2, TOP + PH + 300, 150, (120, 180, 255), scale=back(seg(T, 0.45, 0.7)), rot=5, max_w=1000)
    elif T >= INTRO + GAG * len(gags):
        tt = T - (INTRO + GAG * len(gags)); s = back(seg(tt, 0.1, 0.4)) * (1 + 0.05 * math.sin(tt * 8))
        put_text_px(frame, 'COMMENT', W // 2, TOP + PH - 180, 110, (255, 230, 60), scale=s, rot=-4)
        put_text_px(frame, '1 OR 2!', W // 2, TOP + PH + 170, 130, (255, 255, 255), scale=s, rot=4)
    return frame


@lru_cache(2)
def _first_frame(key):
    return render_frame(0)


def render_frame_loop(i):
    """Shorts başa sarar: son 0.45 sn ilk kareye karışır (kesintisiz döngü → tekrar izlenme)."""
    T = i / FPS; tot = total(); f = render_frame(i)
    if T > tot - 0.45:
        f = Image.blend(f, _first_frame(str(PLAN.get('seed'))), seg(T, tot - 0.45, tot))
    return f


def _frame_bytes(i): return render_frame_loop(i).tobytes()


@lru_cache(None)
def load_clip(f):
    with wave.open(f) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    nz = np.nonzero(np.abs(x) > 0.02)[0]
    return x[max(0, nz[0] - 200):nz[-1] + 800] if len(nz) else None


def line_clip(gag, sp):
    """Konuşan evcil hayvan repliği: voices/<Ses>/lines/<durum>_<N kedi|P köpek>.wav (yoksa None → sadece efektler)."""
    import voice_lines as vl
    voice, which = (vl.CAT_VOICE, 'N') if sp == 'cat' else (vl.DOG_VOICE, 'P')
    cands = [f for f in (os.path.join(HERE, 'voices', voice, 'lines', f'{gag}_{which}{suf}.wav') for suf in ('', '2', '3'))
             if os.path.exists(f)]   # 3 varyanttan videoya göre biri
    if not cands: return None
    x = load_clip(cands[random.Random(f"{PLAN.get('seed')}-{gag}-{sp}").randrange(len(cands))])
    return None if x is None else x / (np.abs(x).max() + 1e-9) * 0.8


LINE_AT = 2.3   # replik panelin vurucu anında (saniye)


def audio_events():
    """(efektler, sesler): [(t0, dizi)], [(t0, dizi, tür)] — tür 'cat'/'dog' (dudak senkronu)."""
    A, B, Q, top_sp, bot_sp = FORMATS[PLAN['format']]
    fx, vox = [], []
    for t0 in (0.0, 0.45): fx.append((t0, psfx('pop')))
    for k, key in enumerate(PLAN['gags']):
        g = GAGS[key]; base = INTRO + k * GAG
        for ev in g[top_sp]: fx.append((base + ev[0], psfx(ev[1], *ev[2:])))
        for ev in g[bot_sp]: fx.append((base + NDUR + ev[0], psfx(ev[1], *ev[2:])))
        for sp, off in ((top_sp, 0.0), (bot_sp, NDUR)):
            x = line_clip(key, sp)
            if x is not None: vox.append((base + off + LINE_AT, x[:int(SR * (NDUR - LINE_AT + 0.6))], sp))
    end = INTRO + GAG * len(PLAN['gags'])
    fx += [(end, psfx('ding')), (end + 0.6, psfx('meow_small')), (end + 1.2, psfx('bark'))]
    return fx, vox


@lru_cache(4)
def speech_levels(key):
    _, vox = audio_events()
    nf = int(total() * FPS) + 2
    lv = {'cat': np.zeros(nf), 'dog': np.zeros(nf)}
    hop = SR // FPS
    for t0, x, sp in vox:
        k = len(x) // hop
        if k == 0: continue
        rms = np.sqrt((x[:k * hop].reshape(k, hop) ** 2).mean(axis=1))
        i0 = int(round(t0 * FPS)); seg_ = lv[sp][i0:i0 + k]; seg_ += rms[:len(seg_)]
    for w in lv: lv[w] /= (lv[w].max() + 1e-9)
    return lv


SPEAKER = [None]


def speaking(t):
    w = SPEAKER[0]
    if w is None: return 0.0
    lv = speech_levels(str(PLAN.get('seed')) + PLAN.get('cat', '') + PLAN.get('dog', '') + ','.join(PLAN.get('gags', [])))[w]
    i = int(t * FPS)
    return float(lv[i]) if 0 <= i < len(lv) else 0.0


def build_audio(path):
    tot = total(); n = int(SR * tot); mus = music(tot, PLAN['seed'])
    mix = np.zeros(n); vo = np.zeros(n)
    fx, vox = audio_events()
    for t0, x in fx:
        i0 = int(t0 * SR); mix[i0:i0 + len(x)] += x[:max(0, n - i0)]
    for t0, x, _ in vox:
        i0 = int(t0 * SR); vo[i0:i0 + len(x)] += x[:max(0, n - i0)]
    env = np.convolve(np.abs(vo), np.ones(int(SR * 0.25)) / int(SR * 0.25), mode='same')
    duck = 1 - 0.65 * np.clip(env / (env.max() + 1e-9) * 4, 0, 1)   # konuşurken müzik kısılır
    mix = mus[:n] * duck + mix + vo * 1.15
    mix *= np.clip((tot - t_arr(tot)[:n]) / 0.25, 0, 1)   # döngüye temiz geçiş
    mix = mix / np.abs(mix).max() * 0.92
    pcm = (np.repeat(mix[:, None], 2, axis=1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- video
def render_video(plan, out_dir, workers=None):
    configure(plan)
    os.makedirs(out_dir, exist_ok=True)
    wav = os.path.join(out_dir, 'audio.wav'); mp4 = os.path.join(out_dir, 'video.mp4')
    build_audio(wav)
    nf = int(total() * FPS)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium',
           '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(workers or os.cpu_count(), initializer=configure, initargs=(plan,)) as pool:
        for i, buf in enumerate(pool.imap(_frame_bytes, range(nf), chunksize=6)):
            p.stdin.write(buf)
            if i % 150 == 0: print(f'  frame {i}/{nf}', flush=True)
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError('ffmpeg failed')
    os.remove(wav)
    return mp4


def _arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


if __name__ == '__main__':
    plan = dict(format='catdog', cat=_arg('--cat', 'ginger'), dog=_arg('--dog', 'goldie'), seed=1,
                room=_arg('--room', 'living'), gags=_arg('--gags', 'doorbell,vacuum,food,cup').split(','))
    out = os.path.join(HERE, 'output', 'preview')
    if '--preview' in sys.argv:
        configure(plan); os.makedirs(out, exist_ok=True)
        for s in _arg('--preview', '3').split(','):
            render_frame(int(float(s) * FPS)).save(os.path.join(out, f'p_{s}.png'))
        print('preview ok')
    else:
        print(render_video(plan, out))
