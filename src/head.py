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
}
DOGS = {
    'goldie': dict(name='Goldie', color=(228, 172, 92), light=(250, 225, 180), eye=(70, 45, 30), mark=None),
    'bruno': dict(name='Bruno', color=(140, 88, 52), light=(205, 160, 120), eye=(45, 30, 20), mark=None),
    'pepper': dict(name='Pepper', color=(245, 245, 245), light=(255, 255, 255), eye=(50, 35, 25), mark='spots'),
    'husky': dict(name='Koda', color=(120, 125, 140), light=(245, 245, 250), eye=(110, 180, 245), mark='mask'),
    'biscuit': dict(name='Biscuit', color=(210, 150, 100), light=(250, 240, 225), eye=(55, 38, 25), mark='patch'),
    'max': dict(name='Max', color=(50, 42, 38), light=(150, 100, 65), eye=(60, 40, 25), mark='mask'),
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
