

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
    if y - 50 > -20:   # el ekranın üstündeyken kol yüksekliği negatif olur (render çöküyordu)
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
