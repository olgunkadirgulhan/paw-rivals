

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
