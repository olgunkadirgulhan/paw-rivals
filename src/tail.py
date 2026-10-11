

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
        img = bg(g['wall'], top_sp); sn = g['fn'](img, top_sp, min(gl, NDUR), T)
        frame.paste(finish_panel(img, sn if gl < NDUR else 0, T, gl >= NDUR), (0, TOP))
        img = bg(g['wall'], bot_sp); sp_ = g['fn'](img, bot_sp, gl - NDUR, T)
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


def _frame_bytes(i): return render_frame(i).tobytes()


def build_audio(path):
    tot = total(); n = int(SR * tot); mix = music(tot, PLAN['seed'])
    A, B, Q, top_sp, bot_sp = FORMATS[PLAN['format']]
    def place(t0, x):
        i0 = int(t0 * SR); mix[i0:i0 + len(x)] += x[:max(0, n - i0)]
    for t0 in (0.0, 0.45): place(t0, psfx('pop'))
    for k, key in enumerate(PLAN['gags']):
        g = GAGS[key]; base = INTRO + k * GAG
        for ev in g[top_sp]: place(base + ev[0], psfx(ev[1], *ev[2:]))
        for ev in g[bot_sp]: place(base + NDUR + ev[0], psfx(ev[1], *ev[2:]))
    end = INTRO + GAG * len(PLAN['gags'])
    place(end, psfx('ding')); place(end + 0.6, psfx('meow_small')); place(end + 1.2, psfx('bark'))
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
