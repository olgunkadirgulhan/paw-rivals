"""Uzun bölüm (yatay 16:9, TV/masaüstü): 7 yeni kedi-köpek karşılaşması (her biri 3 durum, Shorts'ta kullanılmamış durum
üçlüsü; kedi/köpek/oda her parçada farklı). Dikey sahne ortada, solda kadro, sağda durumlar; açıklamada
bölüm zaman damgaları. Yatay video Shorts sayılmaz → izlenme süresi YPP'nin 4.000 saatine yazılır.

  python episode.py [--no-upload]
"""
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paws as orbit  # noqa: E402
import run  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

OW, OH = 1920, 1080
PARTS = int(os.environ.get('EP_PARTS') or 5)        # 2026-10-17: günde 1 bölüm → 5 parça × 3 durum
CARD = 2.5
# 2026-10-13 kurgular (kullanıcı: tekrar olmasın diye kurguları artır, Bloop'taki gibi): her bölüm farklı yapı
KURGUS = ['matchups', 'rivalry', 'tournament', 'day', 'ranked', 'room']
DAY = {'food': '7:30 AM', 'cup': '8:00 AM', 'mail': '9:00 AM', 'vacuum': '10:00 AM', 'doorbell': '11:00 AM', 'box': '12:00 PM',
       'sunbeam': '1:00 PM', 'laser': '3:00 PM', 'ball': '4:00 PM', 'squeaky': '4:30 PM', 'cucumber': '5:00 PM', 'treat': '6:00 PM',
       'fish': '6:30 PM', 'cake': '7:00 PM', 'bath': '8:00 PM', 'bubbles': '8:30 PM', 'mirror': '9:00 PM', 'yarn': '9:30 PM',
       'thunder': '10:30 PM', 'bed': '11:00 PM'}
FF = None
YELLOW, WHITE = (255, 230, 60), (255, 255, 255)


def ff(*args):
    subprocess.run([FF, '-y', '-loglevel', 'error', *args], check=True)


def strip(t):
    return re.sub('[\U0001F000-\U0001FFFF☀-➿‍️]', '', t).strip()


def font(sz):
    return ImageFont.truetype(orbit.FONT, sz)


def text(d, xy, s, sz, fill, anchor='mm', maxw=None):
    f = font(sz)
    lines = [s]
    if maxw:   # kelime kaydırma
        lines, cur = [], ''
        for w_ in s.split():
            nxt = (cur + ' ' + w_).strip()
            if f.getlength(nxt) <= maxw: cur = nxt
            else: lines.append(cur); cur = w_
        lines = [l for l in lines + [cur] if l]
    lh = sz * 1.15
    y0 = xy[1] - lh * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        d.text((xy[0], y0 + i * lh), ln, font=f, fill=fill, anchor=anchor, stroke_width=max(3, sz // 12), stroke_fill=(20, 16, 34))


def background(kind=None):
    """Yatay arka plan: sıcak koyu degrade + pati izleri."""
    import numpy as np
    t = np.linspace(0, 1, OH)[:, None, None]
    a = (np.array((48, 30, 60), float) * (1 - t) + np.array((110, 60, 70), float) * t) * np.ones((1, OW, 1))
    img = Image.fromarray(a.astype('uint8')).convert('RGB'); d = ImageDraw.Draw(img); r = random.Random(4)
    for _ in range(40):
        x, y, s = r.uniform(0, OW), r.uniform(0, OH), r.uniform(14, 26)
        col = (150, 95, 110)
        d.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8], fill=col)
        for dx, dy in ((-1.1, -1.3), (0, -1.7), (1.1, -1.3)):
            d.ellipse([x + dx * s - s * 0.38, y + dy * s - s * 0.38, x + dx * s + s * 0.38, y + dy * s + s * 0.38], fill=col)
    return img


def panel_png(path, k, n, plan, label=None, head='TODAY THEY FACE'):
    img = background(); d = ImageDraw.Draw(img)
    text(d, (330, 300), label or f'#{k}', 120 if not label or len(label) < 6 else 70, YELLOW, maxw=600)
    text(d, (330, 520), orbit.CATS[plan['cat']]['name'].upper(), 64, (255, 180, 90))
    text(d, (330, 610), 'VS', 50, WHITE)
    text(d, (330, 700), orbit.DOGS[plan['dog']]['name'].upper(), 64, (140, 200, 255))
    text(d, (330, 900), f'{k} / {n}', 40, (230, 200, 220))
    text(d, (OW - 330, 200), head, 46, YELLOW, maxw=600)
    for i, g in enumerate(plan['gags']):
        text(d, (OW - 330, 360 + i * 170), strip(orbit.GAGS[g]['title']).upper(), 50, WHITE, maxw=520)
    text(d, (OW - 330, 900), 'TEAM CAT OR TEAM DOG?', 40, YELLOW)
    img.save(path)


def card_mp4(path, lines, kind=None, seconds=CARD):
    img = background(kind); d = ImageDraw.Draw(img)
    for s, y, sz, col in lines:
        text(d, (OW // 2, y), s, sz, col, maxw=1600)
    png = str(path) + '.png'; img.save(png)
    ff('-loop', '1', '-i', png, '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', str(seconds),
       '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', str(orbit.FPS), '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-shortest', str(path))


def part(out, k, n, plan, label=None, head='TODAY THEY FACE'):
    raw = orbit.render_video(plan, str(out / f'raw{k}'))
    pan = out / f'panel{k}.png'; panel_png(pan, k, n, plan, label, head)
    dst = out / f'part{k}.mp4'
    ff('-loop', '1', '-i', str(pan), '-i', raw, '-filter_complex',
       f'[1:v]scale=-2:{OH}[v];[0:v][v]overlay=(W-w)/2:0:shortest=1,format=yuv420p[o]',
       '-map', '[o]', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-r', str(orbit.FPS),
       '-c:a', 'aac', '-ar', '44100', '-ac', '2', str(dst))
    return dst


def dur(mp4):
    r = subprocess.run([FF, '-i', str(mp4)], capture_output=True, text=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def stamp(t):
    t = int(t); return f'{t // 60}:{t % 60:02d}'


def main():
    global FF
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    no_upload = '--no-upload' in sys.argv
    hist = run.load()
    eps = [v for v in hist['videos'] if v.get('kind') == 'episode']
    if eps and not no_upload:
        last = datetime.strptime(eps[-1]['date'], '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - last < timedelta(hours=18):     # 2026-10-17: günde 1 bölüm
            print(f'son bölüm {eps[-1]["date"]}: 18 saat dolmadı, atlandı'); return
    rnd = random.Random()
    sim = {'videos': list(hist['videos'])}; plans = []; perf = run.performance(hist)
    recent = {g for v in eps[-6:] for g in (v.get('gags') or [x for x, *_ in v.get('items', [])])}   # son 6 bölümün durumları yasak
    for _ in range(PARTS * 40):
        if len(plans) == PARTS: break
        p = run.pick_plan(sim, rnd, perf)
        if len(p['gags']) < 3 or any(set(p['gags']) & set(q['gags']) for q in plans) or set(p['gags'][:3]) & recent:
            continue   # bölümde aynı durum iki kez olmasın; son 6 bölümde geçen durum yok; her parça 3 durum
        p['gags'] = p['gags'][:3]
        sim['videos'].append(dict(kind='short', **p)); plans.append(p)
    if len(plans) < min(4, PARTS):
        print(f'yeni plan yetmiyor ({len(plans)}) → bölüm atlandı'); return
    n_ep = len(eps) + 1
    kurgu = KURGUS[(n_ep - 1) % len(KURGUS)]
    if eps and eps[-1].get('kurgu') == kurgu:
        kurgu = KURGUS[n_ep % len(KURGUS)]
    c0, d0 = orbit.CATS[plans[0]['cat']]['name'], orbit.DOGS[plans[0]['dog']]['name']
    if kurgu == 'rivalry':                               # tek kedi vs tek köpek, bütün bölüm boyunca
        for p in plans: p['cat'], p['dog'] = plans[0]['cat'], plans[0]['dog']
    if kurgu == 'room':                                  # bütün bölüm tek mekânda
        r0 = rnd.choice(orbit.ROOMS)
        for p in plans: p['room'] = r0
    if kurgu == 'day':                                   # sabahtan geceye
        plans.sort(key=lambda p: min(datetime.strptime(DAY.get(g, '12:00 PM'), '%I:%M %p') for g in p['gags']))
        for p in plans: p['gags'].sort(key=lambda g: datetime.strptime(DAY.get(g, '12:00 PM'), '%I:%M %p'))
    n = len(plans)
    stages = (['QUARTERFINAL 1', 'QUARTERFINAL 2', 'QUARTERFINAL 3', 'QUARTERFINAL 4', 'SEMIFINAL 1', 'SEMIFINAL 2', 'FINAL']
              if n == 7 else [f'ROUND {i + 1}' for i in range(n - 1)] + ['FINAL'])
    labels = {'tournament': stages, 'ranked': [f'#{n - i}' for i in range(n)],
              'day': [DAY.get(p['gags'][0], '') for p in plans], 'rivalry': [f'ROUND {i + 1}' for i in range(n)]}.get(kurgu, [f'#{i + 1}' for i in range(n)])
    head = {'ranked': 'MOST CHAOTIC, RANKED', 'day': 'THEIR DAY CONTINUES', 'tournament': 'THE BRACKET', 'rivalry': 'THE RIVALRY'}.get(kurgu, 'TODAY THEY FACE')
    print(f'kurgu: {kurgu}', flush=True)
    out = HERE / 'output' / f'episode-{n_ep}'; out.mkdir(parents=True, exist_ok=True)
    names = [strip(orbit.GAGS[g]['title']) for p in plans for g in p['gags']]
    files = []
    intro = out / 'intro.mp4'
    big = {'matchups': f'{len(plans) * 3} SITUATIONS: CATS VS DOGS', 'rivalry': f'{c0.upper()} VS {d0.upper()}: THE RIVALRY',
           'tournament': 'CAT VS DOG TOURNAMENT', 'day': 'A DAY WITH A CAT AND A DOG', 'ranked': f'TOP {len(plans)} PET CHAOS MOMENTS',
           'room': f'{plans[0]["room"].upper()} CHAOS'}[kurgu]
    card_mp4(intro, [('PAW RIVALS', 380, 150, WHITE), (f'EPISODE {n_ep}', 560, 90, YELLOW), (big, 720, 56, WHITE)])
    files.append(intro)
    chapters = [('0:00', 'Intro')]; t = CARD
    for k, p in enumerate(plans, 1):
        orbit.configure(p)
        f = part(out, k, len(plans), p, labels[k - 1], head); files.append(f)
        chapters.append((stamp(t), f"{orbit.CATS[p['cat']]['name']} vs {orbit.DOGS[p['dog']]['name']}: " +
                         ', '.join(strip(orbit.GAGS[g]['title']).title() for g in p['gags'])))
        t += dur(f)
        print(f'bölüm parçası {k}/{len(plans)}: {p}', flush=True)
    outro = out / 'outro.mp4'
    card_mp4(outro, [('TEAM CAT OR TEAM DOG?', 420, 110, YELLOW), ('Tell us in the comments!', 600, 64, WHITE),
                     ('New cat vs dog videos every day', 760, 56, WHITE)], None, 4.0)
    files.append(outro); chapters.append((stamp(t), 'Team cat or team dog?'))
    lst = out / 'list.txt'; lst.write_text(''.join(f"file '{f}'\n" for f in files))
    mp4 = out / 'episode.mp4'
    ff('-f', 'concat', '-safe', '0', '-i', str(lst), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
       '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(mp4))
    # kapak: ilk planın son sıralama karesi + başlık
    orbit.configure(plans[0])
    th = orbit.render_frame(int((orbit.total() - 1.0) * orbit.FPS)).resize((608, 1080))
    thumb = background(); thumb.paste(th, ((OW - 608) // 2, 0)); d = ImageDraw.Draw(thumb)
    text(d, (330, 420), 'CAT', 130, (255, 180, 90)); text(d, (330, 580), 'VS DOG', 120, (140, 200, 255))
    text(d, (OW - 330, 500), f'EPISODE {n_ep}', 90, WHITE)
    thumb = thumb.resize((1280, 720)); thumb.save(out / 'thumb.png')
    title = {'matchups': rnd.choice([f'Cats vs Dogs: {len(names)} Situations, Totally Different Reactions 😂',
                                     f'Cat vs Dog: {", ".join(names[:3])} & More 🐱🐶']),
             'rivalry': f'{c0} vs {d0}: Cat vs Dog Rivalry, {len(names)} Rounds 🐱🐶',
             'tournament': f'Cat vs Dog Tournament: Quarterfinals to the Final 🏆',
             'day': f'A Day With a Cat and a Dog: Morning to Night 🐱🐶',
             'ranked': f'Top {len(plans)} Cat vs Dog Chaos Moments, Ranked 🏆',
             'room': f'{plans[0]["room"].title()} Chaos: Cats vs Dogs, {len(names)} Situations 😂'}[kurgu]
    title = f'{title} | Paw Rivals Ep {n_ep}'[:100]
    facts = '\n'.join(f'{c[0]} {c[1]}' for c in chapters)
    desc = (f'Paw Rivals episode {n_ep}: {len(names)} everyday situations, and the cats and dogs react in totally different ways.\n\n'
            + facts + '\n\nTeam cat or team dog? Comment below 👇\n\n#catvsdog #cats #dogs #pets #animation')
    tags = ['cat vs dog', 'cats vs dogs', 'funny cats', 'funny dogs', 'pets', 'cat and dog animation', 'paw rivals',
            'animation'] + [x.lower() for x in names[:6]]
    (out / 'meta.json').write_text(json.dumps(dict(title=title, description=desc, plans=plans), indent=1, ensure_ascii=False))
    print(f'bölüm hazır: {mp4} ({stamp(dur(mp4))})\n{title}', flush=True)
    if no_upload:
        return
    import upload
    privacy = os.environ.get('YT_PRIVACY') or 'private'
    vid = upload.upload(str(mp4), title, desc, tags, privacy, category='15')
    print(f'yüklendi: https://youtu.be/{vid} ({privacy})', flush=True)
    try:
        upload.set_thumbnail(vid, str(out / 'thumb.png'))
    except Exception as e:  # noqa: BLE001 — kanal doğrulanmamışsa kapak yüklenemez
        print('kapak atlandı:', str(e)[:150])
    pl = json.loads((HERE / 'playlists.json').read_text()) if (HERE / 'playlists.json').exists() else {}
    if pl.get('catdog'):
        try: upload.add_to_playlist(pl['catdog'], vid)
        except Exception as e: print('playlist:', e)  # noqa: E701
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    hist['videos'].append(dict(id=vid, date=now, kind='episode', title=title, privacy=privacy,
                               items=[[g] for p in plans for g in p['gags']], parts=plans, kurgu=kurgu))
    run.HISTORY.write_text(json.dumps(hist, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
