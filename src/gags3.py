

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
    pop(img, end, 540, 220, 2.8, tt, (255, 225, 70), 78, -4)
    return shake


def make_pgag(spec):
    def fn(img, sp, t, gt):
        tt = max(t, 0.0)
        if t < 0:
            pet(img, sp, idle(sp, gt)); pprop(img, spec, *PP, 0.9); return 0.0
        return pcat(img, spec, tt, gt) if sp == 'cat' else pdog(img, spec, tt, gt)
    return fn


PSFX_C = {'knock': [(1.3, 'click'), (2.0, 'smash')], 'sit_in': [(1.0, 'boing'), (1.8, 'purr', 1.4)], 'ignore': [(1.2, 'meow_flat')],
          'hiss': [(0.9, 'hiss')], 'stare': [(1.0, 'meow_small'), (2.2, 'whoosh'), (2.5, 'bang')], 'sleep_on': [(1.0, 'yawn'), (1.6, 'purr', 1.6)]}
PSFX_D = {'zoomies': [(0.4, 'whoosh'), (1.1, 'whoosh'), (1.8, 'whoosh'), (2.6, 'bark')], 'chew': [(0.8, 'growl'), (1.3, 'crunch'), (1.8, 'crunch'), (2.3, 'crunch')],
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


def register_pfactory(rows, debut0='2026-10-15', per_group=5):
    from datetime import date as _date, timedelta as _td
    d0 = _date.fromisoformat(debut0)
    for i, r in enumerate(rows):
        gid, title, name, shape, c1, c2, c3, label, cm, dm, cend, dend = r
        spec = dict(shape=shape, c1=c1, c2=c2, c3=c3, label=label, cat=cm, dog=dm, cend=cend, dend=dend)
        GAGS['p_' + gid] = dict(debut=str(d0 + _td(days=i // (per_group * 2))), fn=make_pgag(spec), title=title, name=name,
                                wall=tuple(int(lerp(x, 240, 0.7)) for x in c1), cat=PSFX_C[cm], dog=PSFX_D[dm], factory=True)


register_pfactory(PROWS)
