

# ================================================================ 2026-10-13 durum fabrikası (kullanıcı: durumları 3 katına çıkar)
# Her durum = bir nesne + kedinin tepkisi + köpeğin tepkisi + kendi espri yazıları. Nesne ve yazılar her durumda farklı.
PP = (840, TTOP - 60)


@lru_cache(512)
def pprop_spr(shape, c1, c2, c3, label, s=1.0):
    w = L(170 * s); spr = Image.new('RGBA', (w, w), (0, 0, 0, 0)); d = ImageDraw.Draw(spr)
    u = lambda v: int(v * w / 170)
    ol = dict(outline=DARK, width=max(2, u(4)))
    if shape == 'round':
        d.ellipse([u(25), u(30), u(145), u(150)], fill=c1, **ol)
        d.ellipse([u(50), u(50), u(80), u(75)], fill=tuple(min(255, x + 70) for x in c1))
        if c2: d.ellipse([u(78), u(12), u(110), u(40)], fill=c2, **ol)
        if c3: d.arc([u(30), u(40), u(140), u(140)], 200, 340, fill=c3, width=u(8))
    elif shape == 'box':
        d.rounded_rectangle([u(25), u(40), u(145), u(150)], radius=u(10), fill=c1, **ol)
        d.rectangle([u(35), u(75), u(135), u(110)], fill=c2)
        if label:
            f = font(u(24)); tw = d.textlength(label, font=f); d.text((u(85) - tw / 2, u(80)), label, font=f, fill=c3 or DARK)
    elif shape == 'cup':
        d.rounded_rectangle([u(30), u(45), u(120), u(150)], radius=u(14), fill=c1, **ol)
        d.ellipse([u(36), u(40), u(114), u(62)], fill=c2)
        d.arc([u(105), u(70), u(155), u(125)], 270, 90, fill=c1, width=u(12))
    elif shape == 'bottle':
        d.rounded_rectangle([u(50), u(55), u(120), u(160)], radius=u(18), fill=c1, **ol)
        d.rectangle([u(70), u(20), u(100), u(60)], fill=c1, **ol)
        d.rectangle([u(66), u(10), u(104), u(28)], fill=c2, **ol)
    elif shape == 'stick':
        d.rounded_rectangle([u(70), u(10), u(100), u(160)], radius=u(14), fill=c1, **ol)
        d.ellipse([u(55), u(0), u(115), u(55)], fill=c2, **ol)
    elif shape == 'disc':
        d.ellipse([u(15), u(60), u(155), u(130)], fill=c1, **ol)
        d.ellipse([u(45), u(75), u(125), u(115)], fill=c2)
    elif shape == 'hat':
        d.polygon([(u(85), u(5)), (u(25), u(140)), (u(145), u(140))], fill=c1, **ol)
        d.rounded_rectangle([u(15), u(130), u(155), u(155)], radius=u(10), fill=c2 or c1, **ol)
    elif shape == 'shoe':
        d.rounded_rectangle([u(15), u(90), u(155), u(140)], radius=u(20), fill=c1, **ol)
        d.rounded_rectangle([u(15), u(50), u(85), u(120)], radius=u(18), fill=c1, **ol)
        d.rectangle([u(15), u(130), u(155), u(145)], fill=c2 or (250, 250, 250))
    return spr


def pprop(img, spec, cx, cy, s=1.0, ang=0.0):
    put_rot(img, pprop_spr(spec['shape'], spec['c1'], spec.get('c2'), spec.get('c3'), spec.get('label', ''),
                           max(0.1, round(s * 20) / 20)), cx, cy, ang)


def pcat(img, spec, tt, gt):
    m, end = spec['cat'], spec['cend']; o = dict(idle('cat', gt)); shake = 0.0
    if m == 'knock':
        x = lerp(CX, 700, sm(seg(tt, 0.2, 1.0)))
        fall = seg(tt, 1.5, 2.0)
        o.update(x=x, walk=tt * 6 if tt < 1.0 else 0, paw=sm(seg(tt, 1.2, 1.45)) * (1 - sm(seg(tt, 1.6, 1.9))),
                 eyes='half' if tt < 2.1 else 'open', look=(1, -0.3) if tt < 2.1 else (-1, 0), tail='up')
        pet(img, 'cat', o)
        if tt < 1.5: pprop(img, spec, *PP, 0.9)
        elif tt < 2.0: pprop(img, spec, PP[0] + 120 * fall, lerp(PP[1], GY - 40, fall * fall), 0.9, 200 * fall)
        else: pprop(img, spec, PP[0] + 120, GY - 30, 0.9, 100)
        if 2.0 <= tt < 2.25: shake = 10
        pop(img, 'TAP.', 860, 360, 1.3, tt, (255, 255, 255), 64, 0, 0.6)
    elif m == 'sit_in':
        pprop(img, spec, 720, GY - 60, 1.5)
        x = lerp(CX, 720, sm(seg(tt, 0.3, 1.2))); jumpk = math.sin(math.pi * clamp((tt - 1.0) / 0.4)) if 1.0 <= tt < 1.4 else 0
        o.update(x=x, jump=120 * jumpk, sy=0.62 if tt >= 1.4 else 1.0, sx=0.85 if tt >= 1.4 else 1.0,
                 eyes='happy' if tt > 1.6 else 'open', walk=tt * 6 if tt < 1.0 else 0, tail='down' if tt >= 1.4 else 'up')
        pet(img, 'cat', o)
        if tt >= 1.4: pprop(img, spec, 720, GY - 30, 1.5)   # ön kenar kedinin önünde
    elif m == 'ignore':
        hx = lerp(1150, 760, sm(seg(tt, 0.2, 0.8)))
        o.update(f=-1 if tt >= 1.2 else 1, eyes='half', mouth='flat', look=(1, 0) if tt < 1.2 else (-1, 0), tail='down' if tt >= 1.2 else 'up', wag=2)
        pet(img, 'cat', o); hand(img, hx + 20, 420); pprop(img, spec, hx, 495, 0.95)
    elif m == 'hiss':
        hx = lerp(1150, 760, sm(seg(tt, 0.2, 0.7)))
        back_ = sm(seg(tt, 0.9, 1.2))
        o.update(x=CX - 150 * back_, puff=back_, tail='puff' if back_ > 0.3 else 'up', mouth='hiss' if 0.9 <= tt < 2.2 else 'flat',
                 eyes='angry' if tt >= 0.9 else 'wide', jump=60 * math.sin(math.pi * clamp((tt - 0.9) / 0.3)) if 0.9 <= tt < 1.2 else 0, ears='flat' if tt >= 0.9 else None)
        pet(img, 'cat', o); hand(img, hx + 20, 420); pprop(img, spec, hx, 495, 0.95)
        pop(img, 'HISS!', 640, 300, 0.9, tt, (255, 120, 90), 110, -8, 1.4)
    elif m == 'stare':
        pounce = sm(seg(tt, 2.2, 2.6))
        o.update(x=lerp(CX, 760, pounce), jump=180 * math.sin(math.pi * pounce), eyes='wide' if tt < 2.2 else 'happy',
                 look=(1, -0.4), sy=0.85 if 1.0 <= tt < 2.2 else 1.0, head_dx=6 * math.sin(gt * 30) if 1.6 <= tt < 2.2 else 0, tail='up', wag=20 if tt < 2.2 else 6)
        pet(img, 'cat', o)
        if tt < 2.5: pprop(img, spec, *PP, 0.9)
        else: pprop(img, spec, 900, GY - 30, 0.9, 80)
        pop(img, 'POUNCE!', 640, 300, 2.2, tt, (255, 225, 70), 110, -8, 0.8)
    elif m == 'sleep_on':
        pprop(img, spec, 640, GY - 30, 1.4)
        o.update(x=lerp(CX, 640, sm(seg(tt, 0.2, 0.9))), lie=sm(seg(tt, 0.9, 1.4)), gy=GY - 60 * sm(seg(tt, 0.9, 1.4)),
                 eyes='closed' if tt > 1.3 else 'half', mouth='flat', tail='down', walk=tt * 6 if tt < 0.9 else 0)
        pet(img, 'cat', o)
        if tt > 1.6: zzz(img, tt, 760, 420)
    elif m == 'bat':          # patiyle oynar, sonunda kaçırır
        taps = sum(1 for t0 in (0.7, 1.2, 1.7, 2.2) if tt >= t0)
        x0 = 640 + 45 * taps + (500 * sm(seg(tt, 2.2, 2.9)) if tt >= 2.2 else 0)
        o.update(x=lerp(CX, 500, sm(seg(tt, 0.1, 0.6))), paw=1.0 if any(t0 <= tt < t0 + 0.2 for t0 in (0.7, 1.2, 1.7, 2.2)) else 0.0,
                 eyes='wide' if tt < 2.4 else 'open', look=(1, 0.6) if tt < 2.4 else (1, 0), sy=0.9, tail='up', wag=18)
        pet(img, 'cat', o); pprop(img, spec, x0, GY - 40 - 30 * abs(math.sin(tt * 9)) * (tt < 2.9), 0.8, x0)
        pop(img, 'TAP. TAP.', 860, 360, 0.7, tt, (255, 255, 255), 60, 0, 1.6)
    elif m == 'groom':        # nesneyi umursamadan kendini yalar
        o.update(paw=0.9 if 0.6 <= tt < 2.4 else 0.0, mouth='tongue' if 0.6 <= tt < 2.4 and (tt * 4) % 1 < 0.6 else 'flat',
                 eyes='closed' if 0.6 <= tt < 2.4 else 'half', head_dx=-10 if 0.6 <= tt < 2.4 else 0, tail='down', wag=3)
        pet(img, 'cat', o); pprop(img, spec, *PP, 0.9)
        pop(img, 'lick lick', 640, 360, 0.7, tt, (220, 220, 235), 56, 0, 1.6)
    pop(img, end, 540, 220, 2.6 if m != 'stare' else 3.0, tt, (255, 255, 255), 74, -4)
    return shake


def pdog(img, spec, tt, gt):
    m, end = spec['dog'], spec['dend']; o = dict(idle('dog', gt)); shake = 0.0
    if m == 'zoomies':
        ph = (tt - 0.4) * 2.2 if tt >= 0.4 else 0
        x = CX + 360 * math.sin(ph * math.pi) if 0.4 <= tt < 3.0 else CX
        o.update(x=x, run=1.0 if 0.4 <= tt < 3.0 else 0, f=1 if math.cos(ph * math.pi) > 0 else -1, eyes='wide', mouth='tongue', ears='perk', wag=60, ws=30)
        pet(img, 'dog', o); pprop(img, spec, *PP, 0.9)
        pop(img, 'ZOOMIES!', 640, 300, 0.5, tt, (255, 225, 70), 110, -8, 2.4)
    elif m == 'chew':
        grab = tt >= 0.8
        o.update(x=lerp(CX, 640, sm(seg(tt, 0.2, 0.8))), head_dx=14 * math.sin(gt * 40) if 1.2 <= tt < 2.6 else 0, eyes='happy' if tt > 1.2 else 'wide',
                 mouth='open' if grab else 'tongue', mo=0.6, wag=40, ws=24, walk=tt * 6 if tt < 0.8 else 0)
        info = pet(img, 'dog', o)
        if not grab: pprop(img, spec, *PP, 0.9)
        elif tt < 2.6: pprop(img, spec, info['nose'][0] + 30, info['nose'][1] + 20, 0.75 * (1 - 0.4 * seg(tt, 1.2, 2.6)), 20 * math.sin(gt * 40))
        if 1.2 <= tt < 2.8: particles(img, 401, 1.2, tt, 24, (720, 600), (-200, 200), (-400, -100), 1200, [spec['c1'], spec.get('c2') or spec['c1']], (10, 22), life=0.8, emit=1.4)
        pop(img, 'CHOMP!', 640, 300, 1.2, tt, (255, 225, 70), 110, -8, 1.2)
    elif m == 'fetch':
        u_ = seg(tt, 0.4, 1.0); back_ = sm(seg(tt, 1.6, 2.4))
        o.update(x=lerp(CX, 900, sm(seg(tt, 0.5, 1.2))) * (1 - back_) + CX * back_, run=1.0 if 0.5 <= tt < 2.4 else 0,
                 f=-1 if 1.4 <= tt < 2.4 else 1, eyes='happy' if tt > 2.4 else 'wide', mouth='tongue' if tt < 1.3 else 'open', mo=0.4, wag=60, ws=30, ears='perk')
        info = pet(img, 'dog', o)
        if tt < 1.3: pprop(img, spec, lerp(PP[0], 980, u_), lerp(PP[1], GY - 40, u_) - 200 * math.sin(math.pi * u_), 0.8, 300 * u_)
        else: pprop(img, spec, info['nose'][0] + (-40 if o['f'] < 0 else 30), info['nose'][1] + 20, 0.7)
        pop(img, 'GOT IT!', 640, 300, 1.3, tt, (255, 225, 70), 100, -8, 1.0)
    elif m == 'scared':
        hx = lerp(1150, 780, sm(seg(tt, 0.2, 0.7)))
        b = sm(seg(tt, 0.7, 1.3))
        o.update(x=CX - 180 * b, f=1, eyes='wide', mouth='o' if tt > 0.7 else 'flat', tail='tuck' if tt > 0.7 else 'up', ears='flat' if tt > 0.7 else None,
                 sy=1.0 - 0.15 * b, head_dx=4 * math.sin(gt * 50) if tt > 1.3 else 0, wag=4)
        pet(img, 'dog', o); hand(img, hx + 20, 420); pprop(img, spec, hx, 495, 0.95)
        pop(img, 'WHAT IS THAT?!', 600, 300, 0.9, tt, (255, 255, 255), 84, -6, 1.6)
    elif m == 'love':
        hx = lerp(1150, 760, sm(seg(tt, 0.2, 0.7)))
        o.update(x=lerp(CX, 560, sm(seg(tt, 0.7, 1.2))), eyes='hearts' if tt > 0.8 else 'wide', mouth='tongue', wag=70, ws=34, ears='perk',
                 jump=60 * abs(math.sin(gt * 6)) if tt > 1.2 else 0)
        pet(img, 'dog', o); hand(img, hx + 20, 420); pprop(img, spec, hx, 495, 0.95)
        if tt > 1.0: particles(img, 402, 1.0, tt, 10, (560, 420), (-120, 120), (-260, -120), 0, [(255, 90, 140)], (16, 26), life=1.0, emit=2.2)
    elif m == 'bark':
        k = int((tt - 0.4) / 0.5) if 0.4 <= tt < 2.9 else -1
        o.update(eyes='angry' if tt < 2.9 else 'happy', mouth='open' if k >= 0 and (tt - 0.4) % 0.5 < 0.25 else 'flat', mo=0.9, ears='perk', wag=30, ws=20,
                 jump=50 * math.sin(math.pi * ((tt - 0.4) % 0.5) / 0.5) if k >= 0 else 0)
        pet(img, 'dog', o); pprop(img, spec, *PP, 0.9)
        if k >= 0: pop(img, 'WOOF!', 620 + (k % 2) * 160, 300 + (k % 3) * 40, 0.4 + k * 0.5, tt, (255, 255, 255), 90, -6 + k * 4, 0.45)
    elif m == 'dig':          # kapıp toprağa gömer
        grab = sm(seg(tt, 0.3, 0.9)); dig = 1.0 <= tt < 2.6
        o.update(x=lerp(CX, 600, grab), head_dy=40 if dig else 0, head_dx=12 * math.sin(gt * 30) if dig else 0, eyes='wide' if dig else 'happy',
                 mouth='tongue', wag=50, ws=26, paw=abs(math.sin(gt * 18)) if dig else 0)
        info = pet(img, 'dog', o)
        sink = sm(seg(tt, 1.2, 2.6))
        if tt < 1.0: pprop(img, spec, lerp(PP[0], info['nose'][0] + 30, grab), lerp(PP[1], info['nose'][1] + 20, grab), 0.8)
        else: pprop(img, spec, 780, GY - 20 + 50 * sink, 0.8 * (1 - 0.7 * sink))
        if dig: particles(img, 403, 1.0, tt, 40, (760, GY - 10), (-260, 260), (-500, -200), 1400, [(120, 85, 55), (150, 105, 70)], (10, 22), life=0.6, emit=1.6)
        if tt >= 1.2: put_sphere(img, (120, 85, 55), 780, GY + 6, 200 * sink, 50 * sink, 0.2)
        pop(img, 'DIG DIG DIG!', 640, 300, 1.0, tt, (255, 225, 70), 96, -8, 1.6)
    elif m == 'roll':         # sırtüstü yuvarlanır
        o.update(lie=sm(seg(tt, 0.6, 1.0)), sy=1.0 - 0.1 * math.sin(gt * 10) * (tt > 1.0), eyes='happy', mouth='tongue', wag=80, ws=40,
                 head_dx=10 * math.sin(gt * 8) if tt > 1.0 else 0)
        pet(img, 'dog', o); pprop(img, spec, *PP, 0.9)
        if tt > 1.0: particles(img, 404, 1.0, tt, 8, (CX, GY - 200), (-120, 120), (-240, -120), 0, [(255, 90, 140)], (16, 24), life=1.0, emit=1.8)
        pop(img, 'WIGGLE WIGGLE', 640, 300, 1.0, tt, (255, 225, 70), 90, -6, 1.6)
    pop(img, end, 540, 220, 2.8, tt, (255, 225, 70), 78, -4)
    if spec.get('surprise'): psurprise(img, spec, tt, gt)
    return shake


def critter(img, kind, x, gy, gt, k=1.0):
    """Sürpriz misafirler (2026-10-13): papağan, hamster, tavşan, kaplumbağa. Yavru kedi pet() ile çizilir."""
    d = ImageDraw.Draw(img)
    if kind == 'parrot':
        y = gy; flap = math.sin(gt * 30) * 30
        put_rot(img, sphere((40, 170, 80), 70, 140, 0.4), x - 40, y + 10, 30 + flap)
        put_sphere(img, (50, 190, 90), x, y, 110, 140, 0.5); put_sphere(img, (230, 60, 50), x + 10, y + 30, 60, 60, 0.4)
        put_sphere(img, (50, 190, 90), x + 20, y - 70, 90, 90, 0.5)
        d = ImageDraw.Draw(img); d.polygon([(L(x + 55), L(y - 75)), (L(x + 100), L(y - 60)), (L(x + 55), L(y - 45))], fill=(250, 170, 40), outline=DARK)
        d.ellipse(box(x + 25, y - 92, x + 45, y - 72), fill=(255, 255, 255), outline=DARK, width=L(3)); d.ellipse(box(x + 33, y - 86, x + 41, y - 78), fill=DARK)
    elif kind == 'hamster':
        put_sphere(img, (200, 230, 250), x, gy - 90, 190, 190, 0.8)
        put_sphere(img, (235, 175, 110), x, gy - 70, 120, 95, 0.4)
        for s_ in (-1, 1): put_sphere(img, (255, 190, 200), x + s_ * 35, gy - 120, 30, 30, 0.3)
        d = ImageDraw.Draw(img)
        for s_ in (-1, 1): d.ellipse(box(x + s_ * 22 - 6, gy - 90, x + s_ * 22 + 6, gy - 78), fill=DARK)
    elif kind == 'bunny':
        put_sphere(img, (250, 250, 250), x, gy - 60, 130, 110, 0.4)
        for s_ in (-1, 1): put_rot(img, sphere((250, 250, 250), 36, 120, 0.4), x + 30 + s_ * 18, gy - 210, s_ * 10)
        put_sphere(img, (250, 250, 250), x + 30, gy - 130, 90, 80, 0.4)
        d = ImageDraw.Draw(img)
        for s_ in (-1, 1): d.ellipse(box(x + 30 + s_ * 18 - 6, gy - 142, x + 30 + s_ * 18 + 6, gy - 130), fill=DARK)
        put_sphere(img, (255, 150, 170), x + 30, gy - 118, 16, 12, 0.3)
    elif kind == 'turtle':
        d.chord(box(x - 90, gy - 120, x + 90, gy), 180, 360, fill=(70, 150, 80), outline=DARK, width=L(4))
        for dx in (-45, 0, 45): d.ellipse(box(x + dx - 20, gy - 95, x + dx + 20, gy - 70), outline=(40, 110, 50), width=L(4))
        put_sphere(img, (150, 200, 120), x + 105, gy - 50, 70, 60, 0.4)
        d = ImageDraw.Draw(img); d.ellipse(box(x + 112, gy - 66, x + 124, gy - 54), fill=DARK)


SURPRISES = {'parrot': ('SQUAWK! HELLO!', [(3.0, 'whoosh'), (3.3, 'meow_small')]), 'hamster': ('HAMSTER BALL!', [(3.0, 'whoosh_s'), (3.4, 'boing')]),
             'bunny': ('WHO INVITED THE BUNNY?', [(3.0, 'boing'), (3.3, 'boing')]), 'turtle': ('...hi.', [(3.3, 'ding')]),
             'kitten': ('MINI ME!', [(3.0, 'meow_small')])}


def psurprise(img, spec, tt, gt):
    """'Sonunu bekle': köpek panelinin sonunda sürpriz misafir gelir (başta 'WAIT FOR IT...' yazar)."""
    kind = spec['surprise']
    if tt < 2.9:
        put_text(img, 'WAIT FOR IT...', 860, 830, 46, (255, 255, 255)); return
    k = sm(seg(tt, 2.9, 3.5))
    if kind == 'parrot': critter(img, 'parrot', lerp(1150, 760, k) - 900 * sm(seg(tt, 3.6, 4.0)), 330 + 40 * math.sin(gt * 5), gt)
    elif kind == 'hamster': critter(img, 'hamster', lerp(1200, -150, seg(tt, 2.9, 3.9)), GY + 10, gt)
    elif kind == 'bunny': critter(img, 'bunny', lerp(1200, 860, k), GY + 10 - 90 * abs(math.sin((tt - 2.9) * 9)) * (1 - k), gt)
    elif kind == 'turtle': critter(img, 'turtle', lerp(1150, 830, seg(tt, 2.9, 4.0)), GY + 10, gt)
    elif kind == 'kitten': pet(img, 'cat', dict(idle('cat', gt), x=lerp(1200, 860, k), scale=0.45, eyes='wide', f=-1, run=1.0 if k < 1 else 0))
    pop(img, SURPRISES[kind][0], 640, 400, 3.1, tt, (255, 255, 255), 58, 6)


def make_pgag(spec):
    def fn(img, sp, t, gt):
        tt = max(t, 0.0)
        if t < 0:
            pet(img, sp, idle(sp, gt)); pprop(img, spec, *PP, 0.9); return 0.0
        if sp == 'cat':
            sh = pcat(img, spec, tt, gt)
            if spec.get('surprise'): put_text(img, 'WAIT FOR IT...', 860, 830, 46, (255, 255, 255))
            return sh
        return pdog(img, spec, tt, gt)
    return fn


PSFX_C = {'bat': [(0.7, 'click'), (1.2, 'click'), (1.7, 'click'), (2.2, 'whoosh_s')], 'groom': [(0.7, 'lick'), (1.3, 'lick'), (1.9, 'lick')], 'knock': [(1.3, 'click'), (2.0, 'smash')], 'sit_in': [(1.0, 'boing'), (1.8, 'purr', 1.4)], 'ignore': [(1.2, 'meow_flat')],
          'hiss': [(0.9, 'hiss')], 'stare': [(1.0, 'meow_small'), (2.2, 'whoosh'), (2.5, 'bang')], 'sleep_on': [(1.0, 'yawn'), (1.6, 'purr', 1.6)]}
PSFX_D = {'dig': [(0.4, 'bark'), (1.0, 'rattle', 1.6)], 'roll': [(0.6, 'boing'), (1.2, 'bark'), (2.0, 'lick')], 'zoomies': [(0.4, 'whoosh'), (1.1, 'whoosh'), (1.8, 'whoosh'), (2.6, 'bark')], 'chew': [(0.8, 'growl'), (1.3, 'crunch'), (1.8, 'crunch'), (2.3, 'crunch')],
          'fetch': [(0.4, 'whoosh'), (1.3, 'bark'), (2.5, 'bark')], 'scared': [(0.7, 'whine'), (1.5, 'whine')],
          'love': [(0.8, 'bark'), (1.3, 'lick'), (1.9, 'lick')], 'bark': [(0.4 + k * 0.5, 'bark') for k in range(5)]}

# (id, başlık, ad, şekil, c1, c2, c3, etiket, kedi, köpek, kedi son yazı, köpek son yazı)
PROWS = [
    ('vase', 'WHEN THERE IS A VASE ON THE TABLE', 'Vase', 'bottle', (90, 160, 220), (230, 90, 120), None, '', 'knock', 'zoomies', 'OOPS. NOT SORRY.', 'WHAT VASE?'),
    ('pizzabox', 'WHEN THE PIZZA ARRIVES', 'Pizza Box', 'box', (230, 200, 150), (200, 60, 40), (250, 250, 250), 'PIZZA', 'sit_in', 'chew', 'MY BOX NOW.', 'PIZZA FOR DOG?'),
    ('remote', 'WHEN YOU NEED THE REMOTE', 'Remote', 'box', (50, 50, 60), (200, 60, 60), (255, 255, 255), 'TV', 'sleep_on', 'chew', 'NO TV FOR YOU.', 'CHANNEL: DOG.'),
    ('shoe', 'WHEN YOU BUY NEW SHOES', 'Shoe', 'shoe', (220, 60, 60), (250, 250, 250), None, '', 'ignore', 'chew', 'UGLY SHOES.', 'NEW CHEW TOY!'),
    ('teddy', 'WHEN YOU GET A TEDDY BEAR', 'Teddy', 'round', (180, 120, 70), (180, 120, 70), None, '', 'ignore', 'fetch', 'NOT A REAL BEAR.', 'MY BEST FRIEND!'),
    ('frisbee', 'WHEN THE FRISBEE COMES OUT', 'Frisbee', 'disc', (60, 200, 150), (80, 220, 170), None, '', 'ignore', 'fetch', 'THROW IT YOURSELF.', 'AGAIN! AGAIN!'),
    ('toymouse', 'WHEN YOU BUY A TOY MOUSE', 'Toy Mouse', 'round', (160, 160, 170), (255, 160, 180), None, '', 'stare', 'scared', 'HUNTED.', 'TINY MONSTER!'),
    ('feather', 'WHEN A FEATHER FALLS', 'Feather', 'stick', (240, 230, 250), (200, 180, 240), None, '', 'stare', 'zoomies', 'CAUGHT THE BIRD.', 'SKY FLUFF!'),
    ('robot', 'WHEN THE ROBOT TOY MOVES', 'Robot Toy', 'box', (170, 180, 200), (90, 200, 230), (40, 40, 40), 'BEEP', 'hiss', 'bark', 'GET OUT, ROBOT.', 'INTRUDER ALERT!'),
    ('pumpkin2', 'WHEN THE HALLOWEEN PUMPKIN APPEARS', 'Pumpkin', 'round', (240, 130, 30), (80, 140, 60), None, '', 'sit_in', 'bark', 'PUMPKIN SPICE CAT.', 'SPOOKY THING!'),
    ('ornament', 'WHEN THE ORNAMENTS GO UP', 'Ornament', 'round', (220, 40, 60), (250, 200, 60), None, '', 'knock', 'love', 'DECORATED THE FLOOR.', 'SHINY BALL!'),
    ('keys', 'WHEN YOU CANT FIND YOUR KEYS', 'Keys', 'disc', (250, 200, 60), (200, 200, 210), None, '', 'knock', 'fetch', 'KEYS? WHAT KEYS?', 'FOUND THEM!'),
    ('phone2', 'WHEN YOU TRY TO USE YOUR PHONE', 'Phone', 'box', (40, 40, 50), (90, 160, 230), None, '', 'sleep_on', 'bark', 'SCREEN TIME OVER.', 'IT IS RINGING!'),
    ('laptop', 'WHEN YOU START WORKING', 'Laptop', 'box', (160, 170, 190), (60, 140, 220), (255, 255, 255), 'WORK', 'sleep_on', 'love', 'WARM KEYBOARD.', 'PLAY INSTEAD?'),
    ('book', 'WHEN YOU OPEN A BOOK', 'Book', 'box', (180, 60, 60), (240, 230, 210), (60, 40, 40), 'READ', 'sleep_on', 'chew', 'BOOK PILLOW.', 'TASTY STORY.'),
    ('plant', 'WHEN YOU BUY A HOUSEPLANT', 'Plant', 'cup', (200, 100, 60), (80, 170, 80), None, '', 'knock', 'chew', 'PLANT IS FLOOR NOW.', 'SALAD!'),
    ('pillow', 'WHEN YOU FLUFF THE PILLOW', 'Pillow', 'box', (240, 240, 250), (220, 220, 240), (120, 120, 160), 'ZZZ', 'sleep_on', 'chew', 'MINE.', 'IT WAS FULL OF FLUFF.'),
    ('sock', 'WHEN A SOCK GOES MISSING', 'Sock', 'stick', (240, 90, 90), (250, 250, 250), None, '', 'ignore', 'chew', 'NOT GUILTY.', 'GUILTY. HAPPY.'),
    ('hat', 'WHEN YOU WEAR A NEW HAT', 'Hat', 'hat', (70, 50, 140), (90, 70, 170), None, '', 'ignore', 'fetch', 'STILL UGLY.', 'MY HAT NOW!'),
    ('tube', 'WHEN THE PAPER TOWEL ROLL IS EMPTY', 'Cardboard Tube', 'stick', (210, 170, 120), (190, 150, 100), None, '', 'stare', 'zoomies', 'TUBE CAPTURED.', 'BEST TOY EVER!'),
    ('bottle', 'WHEN YOU LEAVE A WATER BOTTLE OUT', 'Water Bottle', 'bottle', (120, 190, 250), (60, 60, 70), None, '', 'knock', 'scared', 'GRAVITY TEST.', 'IT CRINKLES!'),
    ('icecube', 'WHEN AN ICE CUBE DROPS', 'Ice Cube', 'box', (200, 230, 250), (220, 240, 255), None, '', 'stare', 'chew', 'COLD PREY.', 'CRUNCHY WATER!'),
    ('lemon', 'WHEN THEY SMELL A LEMON', 'Lemon', 'round', (255, 225, 50), (90, 160, 60), None, '', 'hiss', 'scared', 'NOPE. NOPE.', 'SOUR MONSTER!'),
    ('cheese', 'WHEN YOU OPEN THE CHEESE', 'Cheese', 'box', (255, 210, 70), (255, 225, 110), None, '', 'ignore', 'love', 'I HEARD NOTHING.', 'CHEEEESE!'),
    ('carrot', 'WHEN YOU OFFER A CARROT', 'Carrot', 'stick', (255, 140, 40), (80, 170, 70), None, '', 'ignore', 'love', 'I AM NOT A RABBIT.', 'BEST VEGGIE!'),
    ('apple', 'WHEN AN APPLE ROLLS BY', 'Apple', 'round', (220, 40, 50), (90, 160, 60), None, '', 'knock', 'fetch', 'APPLE DOWN.', 'ROUND SNACK!'),
    ('tennis', 'WHEN THE TENNIS BALL COMES OUT', 'Tennis Ball', 'round', (210, 240, 70), None, (255, 255, 255), '', 'ignore', 'zoomies', 'DOG THING.', 'BALL BALL BALL!'),
    ('duck', 'WHEN THE RUBBER DUCK SQUEAKS', 'Rubber Duck', 'round', (255, 220, 40), (255, 140, 40), None, '', 'stare', 'bark', 'QUACK IS MINE.', 'WHO SAID QUACK?!'),
    ('hairdryer', 'WHEN THE HAIR DRYER TURNS ON', 'Hair Dryer', 'stick', (230, 90, 150), (60, 60, 70), None, '', 'hiss', 'scared', 'HOT WIND = ENEMY.', 'DRAGON!'),
    ('broom', 'WHEN YOU START SWEEPING', 'Broom', 'stick', (200, 150, 80), (220, 180, 90), None, '', 'hiss', 'bark', 'BROOM MONSTER.', 'FIGHT THE BROOM!'),
    ('suitcase', 'WHEN YOU PACK FOR A TRIP', 'Suitcase', 'box', (60, 90, 160), (40, 60, 120), (250, 250, 250), 'TRIP', 'sit_in', 'scared', 'TAKE ME OR STAY.', 'DONT LEAVE ME!'),
    ('basket', 'WHEN THE LAUNDRY BASKET IS FULL', 'Laundry Basket', 'cup', (230, 200, 150), (250, 250, 250), None, '', 'sit_in', 'zoomies', 'CLEAN LAUNDRY = BED.', 'SOCK PARTY!'),
    ('bag', 'WHEN YOU COME BACK FROM SHOPPING', 'Shopping Bag', 'box', (240, 230, 210), (230, 120, 60), (250, 250, 250), 'SHOP', 'sit_in', 'love', 'BAG > GIFTS.', 'DID YOU BUY TREATS?'),
    ('present', 'WHEN YOU WRAP A PRESENT', 'Present', 'box', (60, 160, 90), (230, 50, 60), (250, 250, 250), '', 'sit_in', 'chew', 'I AM THE GIFT.', 'UNWRAPPED IT!'),
    ('cupcake', 'WHEN THERE IS A CUPCAKE', 'Cupcake', 'cup', (230, 130, 170), (255, 240, 250), None, '', 'ignore', 'love', 'SUGAR? NO THANKS.', 'ONE BITE PLEASE!'),
    ('icecream', 'WHEN YOU HAVE ICE CREAM', 'Ice Cream', 'hat', (230, 170, 100), (255, 200, 220), None, '', 'knock', 'love', 'ICE CREAM IS FLOOR.', 'LICK LICK LICK!'),
    ('trophy', 'WHEN YOU WIN A TROPHY', 'Trophy', 'cup', (250, 200, 50), (255, 220, 90), None, '', 'knock', 'bark', 'I AM THE CHAMPION.', 'SHINY ENEMY!'),
    ('mug', 'WHEN YOU MAKE COFFEE', 'Mug', 'cup', (250, 250, 250), (110, 60, 40), None, '', 'knock', 'love', 'DECAF NOW.', 'COFFEE SMELLS NICE!'),
    ('fan', 'WHEN THE FAN TURNS ON', 'Fan', 'disc', (200, 220, 240), (120, 190, 240), None, '', 'stare', 'bark', 'WIND BIRD.', 'SPINNING THING!'),
    ('homework', 'WHEN YOU DO YOUR HOMEWORK', 'Homework', 'box', (250, 250, 245), (200, 210, 230), (60, 60, 70), 'MATH', 'sleep_on', 'chew', 'NO MATH TODAY.', 'THE DOG ATE IT.'),
]


# 2026-10-13 dağılım dengesi (kullanıcı: davranış değişsin, tekrar olmasın)
CMODE = {'teddy': 'groom', 'frisbee': 'bat', 'shoe': 'groom', 'apple': 'bat', 'keys': 'bat', 'cheese': 'groom', 'bottle': 'bat', 'tennis': 'bat', 'cupcake': 'groom'}
DMODE = {'shoe': 'dig', 'book': 'dig', 'plant': 'dig', 'sock': 'roll', 'pillow': 'roll', 'cheese': 'roll', 'present': 'dig', 'laptop': 'roll', 'carrot': 'dig'}
SURPRISE_ORDER = ['parrot', 'kitten', 'bunny', 'hamster', 'turtle']


def register_pfactory(rows, debut0='2026-10-15', per_group=5):
    from datetime import date as _date, timedelta as _td
    d0 = _date.fromisoformat(debut0)
    for i, r in enumerate(rows):
        gid, title, name, shape, c1, c2, c3, label, cm, dm, cend, dend = r
        cm, dm = CMODE.get(gid, cm), DMODE.get(gid, dm)
        sur = SURPRISE_ORDER[(i // 2) % len(SURPRISE_ORDER)] if i % 2 == 0 else None      # durumların yarısında sürpriz misafir
        spec = dict(shape=shape, c1=c1, c2=c2, c3=c3, label=label, cat=cm, dog=dm, cend=cend, dend=dend, surprise=sur)
        GAGS['p_' + gid] = dict(debut=str(d0 + _td(days=i // (per_group * 2))), fn=make_pgag(spec), title=title, name=name,
                                wall=tuple(int(lerp(x, 240, 0.7)) for x in c1), cat=PSFX_C[cm], dog=PSFX_D[dm] + (SURPRISES[sur][1] if sur else []),
                                factory=True, cmode=cm, dmode=dm, surprise=sur)


register_pfactory(PROWS)

# 2026-10-17 (kullanıcı: Paw'da günde 1 uzun bölüm, eşsiz olsun) → 60 yeni durum; havuz ~120
PROWS2 = [
    ('balloon', 'WHEN THE BIRTHDAY BALLOON FLOATS', 'Balloon', 'round', (240, 70, 90), (250, 250, 250), None, '', 'bat', 'scared', 'POP IS COMING.', 'FLYING BALL ENEMY!'),
    ('umbrella', 'WHEN YOU OPEN AN UMBRELLA INSIDE', 'Umbrella', 'hat', (60, 90, 200), (40, 60, 150), None, '', 'hiss', 'scared', 'INDOOR CLOUD. NO.', 'GIANT FLOWER!'),
    ('slipper', 'WHEN YOU LOOK FOR YOUR SLIPPERS', 'Slipper', 'shoe', (180, 140, 220), (250, 240, 250), None, '', 'sleep_on', 'dig', 'WARM BED FOUND.', 'BURIED IN THE YARD.'),
    ('pizza', 'WHEN A PIZZA SLICE FALLS', 'Pizza Slice', 'hat', (250, 200, 80), (220, 60, 40), None, '', 'ignore', 'love', 'CHEESE? UNWORTHY.', 'FIVE SECOND RULE!'),
    ('cookiejar', 'WHEN THE COOKIE JAR OPENS', 'Cookie Jar', 'cup', (230, 220, 200), (160, 110, 60), None, '', 'knock', 'love', 'JAR IS FLOOR.', 'COOKIE COOKIE!'),
    ('donut', 'WHEN THE DONUTS ARRIVE', 'Donut', 'disc', (240, 160, 190), (250, 230, 200), None, '', 'bat', 'love', 'DONUT HOCKEY.', 'SHARE? SHARE?'),
    ('burger', 'WHEN YOU UNWRAP A BURGER', 'Burger', 'disc', (200, 130, 60), (90, 170, 70), None, '', 'stare', 'love', 'GIVE ME THE MEAT.', 'BEST DAY EVER!'),
    ('banana', 'WHEN A BANANA APPEARS', 'Banana', 'stick', (250, 220, 60), (120, 90, 40), None, '', 'hiss', 'fetch', 'CURVED SNAKE.', 'YELLOW STICK!'),
    ('watermelon', 'WHEN YOU CUT A WATERMELON', 'Watermelon', 'round', (60, 150, 70), (230, 60, 80), None, '', 'ignore', 'roll', 'TOO JUICY.', 'SUMMER BALL!'),
    ('egg', 'WHEN AN EGG IS ON THE COUNTER', 'Egg', 'round', (250, 245, 230), (240, 230, 210), None, '', 'knock', 'scared', 'BREAKFAST IS FLOOR.', 'IT MOVED! MAYBE.'),
    ('milk', 'WHEN YOU POUR SOME MILK', 'Milk Carton', 'box', (250, 250, 250), (90, 150, 220), (40, 60, 120), 'MILK', 'groom', 'love', 'ONE SIP, HUMAN.', 'WHITE WATER!'),
    ('popcorn', 'WHEN MOVIE NIGHT STARTS', 'Popcorn', 'cup', (230, 60, 60), (255, 245, 210), None, '', 'sleep_on', 'love', 'MOVIE? NAP.', 'POPCORN RAIN!'),
    ('candle', 'WHEN YOU LIGHT A CANDLE', 'Candle', 'stick', (250, 240, 220), (255, 180, 60), None, '', 'stare', 'bark', 'TINY SUN.', 'FIRE FRIEND?!'),
    ('clock', 'WHEN THE ALARM CLOCK RINGS', 'Alarm Clock', 'round', (230, 60, 60), (250, 250, 250), None, '', 'knock', 'bark', 'ALARM DEFEATED.', 'WAKE UP! WAKE UP!'),
    ('lamp', 'WHEN YOU TURN ON THE LAMP', 'Lamp', 'hat', (250, 220, 120), (120, 90, 60), None, '', 'sleep_on', 'love', 'WARM SPOT.', 'LIGHT BALL!'),
    ('blender', 'WHEN THE BLENDER TURNS ON', 'Blender', 'cup', (200, 220, 240), (230, 100, 120), None, '', 'stare', 'scared', 'I SAW EVERYTHING.', 'THE KITCHEN IS ANGRY!'),
    ('leash', 'WHEN YOU GRAB THE LEASH', 'Leash', 'stick', (220, 60, 60), (60, 60, 70), None, '', 'ignore', 'zoomies', 'GOOD LUCK OUTSIDE.', 'WALK! WALK! WALK!'),
    ('towel', 'WHEN A TOWEL IS ON THE FLOOR', 'Towel', 'box', (120, 200, 210), (250, 250, 250), None, '', 'sleep_on', 'roll', 'PERFECT BED.', 'ROLL ROLL ROLL!'),
    ('brush', 'WHEN THE BRUSH COMES OUT', 'Brush', 'stick', (170, 110, 70), (60, 60, 70), None, '', 'groom', 'chew', 'PAMPER ME.', 'TASTY STICK!'),
    ('collar', 'WHEN THE NEW COLLAR ARRIVES', 'Collar', 'disc', (230, 60, 120), (250, 210, 60), None, '', 'ignore', 'love', 'I REFUSE FASHION.', 'I LOOK GREAT!'),
    ('carrier', 'WHEN THE PET CARRIER APPEARS', 'Pet Carrier', 'box', (200, 200, 210), (110, 110, 130), (40, 40, 50), 'VET', 'hiss', 'scared', 'NEVER AGAIN.', 'NOT THE VET!'),
    ('catnip', 'WHEN YOU OPEN THE CATNIP', 'Catnip', 'box', (90, 170, 90), (230, 250, 220), (30, 60, 30), 'NIP', 'groom', 'roll', 'SO HAPPY NOW.', 'WHY IS SHE WEIRD?'),
    ('bone', 'WHEN THE BIG BONE ARRIVES', 'Bone', 'stick', (245, 240, 225), (230, 225, 210), None, '', 'ignore', 'dig', 'NOT MY TYPE.', 'SAVING IT FOREVER.'),
    ('scratcher', 'WHEN THE NEW SCRATCHER IS SET UP', 'Scratcher', 'box', (200, 160, 110), (170, 130, 90), None, '', 'groom', 'chew', 'MY CLAW SPA.', 'CARDBOARD SNACK!'),
    ('tent', 'WHEN YOU SET UP A TOY TENT', 'Toy Tent', 'hat', (250, 90, 60), (60, 160, 230), None, '', 'sit_in', 'bark', 'CAMPING CAT.', 'WHO LIVES IN THERE?!'),
    ('snowglobe', 'WHEN THE SNOW GLOBE SHAKES', 'Snow Globe', 'round', (200, 230, 250), (250, 250, 255), None, '', 'stare', 'scared', 'TINY WINTER.', 'IT IS SNOWING INSIDE!'),
    ('guitar', 'WHEN YOU PLAY THE GUITAR', 'Guitar', 'bottle', (200, 120, 60), (60, 40, 30), None, '', 'sleep_on', 'bark', 'LULLABY.', 'SINGING ALONG!'),
    ('drum', 'WHEN THE TOY DRUM BEATS', 'Toy Drum', 'cup', (230, 60, 60), (250, 220, 120), None, '', 'hiss', 'bark', 'TOO LOUD.', 'BOOM BOOM BARK!'),
    ('paintbrush', 'WHEN YOU START PAINTING', 'Paint Brush', 'stick', (230, 180, 60), (60, 140, 220), None, '', 'knock', 'roll', 'ABSTRACT ART.', 'NOW I AM BLUE!'),
    ('tape', 'WHEN THE TAPE ROLL APPEARS', 'Tape Roll', 'disc', (210, 200, 180), (240, 235, 225), None, '', 'bat', 'chew', 'STICKY TRAP.', 'IT STUCK TO ME!'),
    ('puzzle', 'WHEN YOU START A PUZZLE', 'Puzzle Box', 'box', (90, 160, 220), (250, 230, 120), (30, 40, 60), '1000', 'sit_in', 'chew', 'I AM THE MISSING PIECE.', 'PIECE EATEN.'),
    ('glasses', 'WHEN YOU LOSE YOUR GLASSES', 'Glasses', 'disc', (60, 60, 70), (200, 220, 240), None, '', 'knock', 'fetch', 'GLASSES? UNDER THE SOFA.', 'FOUND THEM! WET.'),
    ('wallet', 'WHEN YOU DROP YOUR WALLET', 'Wallet', 'box', (110, 70, 40), (150, 100, 60), None, '', 'sleep_on', 'fetch', 'SECURITY GUARD.', 'I RETURNED IT!'),
    ('headphones', 'WHEN YOU PUT ON HEADPHONES', 'Headphones', 'disc', (60, 60, 70), (230, 60, 60), None, '', 'groom', 'love', 'FINALLY QUIET.', 'WHAT ARE YOU HEARING?'),
    ('gamepad', 'WHEN GAME NIGHT STARTS', 'Game Controller', 'box', (60, 60, 80), (90, 200, 230), (250, 250, 250), 'PLAY', 'sleep_on', 'chew', 'PAUSED FOREVER.', 'BUTTONS TASTE GOOD!'),
    ('newspaper', 'WHEN YOU READ THE NEWSPAPER', 'Newspaper', 'box', (240, 240, 235), (200, 200, 195), (40, 40, 40), 'NEWS', 'sit_in', 'fetch', 'BREAKING: CAT.', 'I BROUGHT THE NEWS!'),
    ('lunchbox', 'WHEN YOU PACK A LUNCHBOX', 'Lunchbox', 'box', (90, 180, 230), (250, 220, 60), (30, 50, 80), 'LUNCH', 'sit_in', 'love', 'I CAME WITH LUNCH.', 'TAKE ME TO SCHOOL!'),
    ('backpack', 'WHEN THE BACKPACK COMES OUT', 'Backpack', 'box', (230, 90, 60), (60, 60, 70), None, '', 'sit_in', 'scared', 'TAKE ME ALONG.', 'ARE YOU LEAVING?!'),
    ('toyblock', 'WHEN THE TOY BLOCKS COME OUT', 'Toy Block', 'box', (60, 180, 120), (250, 220, 60), (40, 40, 50), 'ABC', 'knock', 'zoomies', 'TOWER DEMOLISHED.', 'BUILDING TIME!'),
    ('skateboard', 'WHEN THE SKATEBOARD ROLLS', 'Skateboard', 'disc', (230, 120, 40), (60, 60, 70), None, '', 'stare', 'fetch', 'ROLLING RAT.', 'RIDE WITH ME!'),
    ('beachball', 'WHEN THE BEACH BALL BOUNCES', 'Beach Ball', 'round', (250, 80, 80), (70, 160, 240), (250, 220, 60), '', 'bat', 'fetch', 'BOUNCE ATTACK.', 'BIGGEST BALL EVER!'),
    ('sandcastle', 'WHEN YOU BUILD A SANDCASTLE', 'Sand Bucket', 'cup', (250, 200, 80), (230, 90, 70), None, '', 'sit_in', 'dig', 'MY ROYAL CASTLE.', 'I IMPROVED IT.'),
    ('snowball', 'WHEN A SNOWBALL ROLLS INSIDE', 'Snowball', 'round', (250, 250, 255), (230, 240, 250), None, '', 'hiss', 'roll', 'COLD STRANGER.', 'SNOW FRIEND!'),
    ('trafficcone', 'WHEN A TRAFFIC CONE SHOWS UP', 'Traffic Cone', 'hat', (240, 120, 30), (250, 250, 250), None, '', 'sit_in', 'roll', 'CONE THRONE.', 'ORANGE HAT FOR ME!'),
    ('hose', 'WHEN THE GARDEN HOSE TURNS ON', 'Garden Hose', 'stick', (70, 170, 80), (60, 120, 200), None, '', 'hiss', 'zoomies', 'WET IS WAR.', 'WATER PARTY!'),
    ('bell', 'WHEN THE LITTLE BELL JINGLES', 'Bell', 'cup', (250, 210, 60), (230, 180, 40), None, '', 'bat', 'bark', 'JINGLE JUSTICE.', 'DINNER BELL?!'),
    ('pinecone', 'WHEN A PINECONE FALLS', 'Pinecone', 'hat', (150, 100, 60), (120, 80, 50), None, '', 'stare', 'chew', 'FOREST INTRUDER.', 'CRUNCHY TREE SNACK!'),
    ('cactus', 'WHEN YOU BUY A CACTUS', 'Cactus', 'bottle', (80, 170, 90), (230, 200, 150), None, '', 'hiss', 'scared', 'POINTY ENEMY.', 'OUCH. NOPE.'),
    ('fishbowl', 'WHEN THE FISHBOWL ARRIVES', 'Fishbowl', 'round', (170, 220, 250), (250, 150, 60), None, '', 'stare', 'love', 'LIVE TELEVISION.', 'NEW FRIENDS!'),
    ('paperbag', 'WHEN A PAPER BAG IS ON THE FLOOR', 'Paper Bag', 'box', (200, 160, 110), (180, 140, 95), None, '', 'sit_in', 'chew', 'BAG CASTLE.', 'RIP RIP RIP!'),
    ('toaster', 'WHEN THE TOAST POPS UP', 'Toaster', 'box', (200, 200, 210), (230, 170, 90), None, '', 'stare', 'bark', 'HOT JUMPING BREAD.', 'THE BREAD ESCAPED!'),
    ('pan', 'WHEN YOU START COOKING', 'Frying Pan', 'disc', (60, 60, 70), (250, 220, 120), None, '', 'stare', 'love', 'CHEF INSPECTOR.', 'SMELLS AMAZING!'),
    ('scarf', 'WHEN YOU KNIT A SCARF', 'Scarf', 'stick', (200, 60, 80), (250, 200, 60), None, '', 'bat', 'chew', 'LONG STRING PREY.', 'LONG SNACK!'),
    ('glove', 'WHEN A GLOVE GOES MISSING', 'Glove', 'shoe', (90, 140, 220), (60, 100, 180), None, '', 'sleep_on', 'fetch', 'HAND HOUSE.', 'I FOUND A HAND!'),
    ('piggybank', 'WHEN YOU SHAKE THE PIGGY BANK', 'Piggy Bank', 'round', (250, 170, 190), (240, 140, 170), None, '', 'knock', 'bark', 'SAVINGS ARE FLOOR.', 'IT RATTLES!'),
    ('flashlight', 'WHEN THE POWER GOES OUT', 'Flashlight', 'stick', (60, 60, 70), (255, 230, 120), None, '', 'stare', 'scared', 'LIGHT HUNT.', 'WHERE DID EVERYTHING GO?'),
    ('gumball', 'WHEN A GUMBALL ROLLS AWAY', 'Gumball', 'round', (90, 180, 100), (250, 220, 60), None, '', 'hiss', 'love', 'ROLLING ENEMY.', 'MINTY BALL!'),
    ('marker', 'WHEN YOU LEAVE A MARKER OUT', 'Marker', 'stick', (250, 250, 250), (60, 120, 230), None, '', 'bat', 'chew', 'PEN HOCKEY.', 'BLUE TONGUE!'),
    ('cushion', 'WHEN YOU BUY A NEW CUSHION', 'Cushion', 'box', (240, 190, 90), (230, 160, 60), None, '', 'sleep_on', 'dig', 'THRONE CLAIMED.', 'LOOKING FOR TREASURE!'),
    ('pinetree', 'WHEN YOU BUY A TINY PINE TREE', 'Tiny Pine Tree', 'hat', (70, 160, 70), (150, 110, 70), None, '', 'ignore', 'scared', 'TINY TREE. NO.', 'IS IT ALIVE?'),
]
register_pfactory(PROWS2, debut0='2026-10-18', per_group=10)
