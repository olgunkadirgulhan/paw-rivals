"""Bir Short üret ve yükle: plan seç (kedi/köpek/oda/durum tekrar etmez) -> render -> YouTube -> history.json.

  python run.py --no-upload        # sadece output/<id>/video.mp4
"""
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paws  # noqa: E402

HISTORY = HERE / 'history.json'
PLAYLISTS = HERE / 'playlists.json'

TITLES = {
    'catdog': ['Cat vs Dog: {g} 😂', 'CAT vs DOG ({g}) 🐱🐶', 'How Cats vs Dogs React to {g} 😂', 'Team Cat or Team Dog? {g} 🤔',
               'Cats vs Dogs: {g} Edition 😹', '{g}: Cat vs Dog 🐶🐱', 'Cat Logic vs Dog Logic: {g} 🤣',
               'Cat Owners vs Dog Owners Know This ({g}) 😂', 'Which Pet Wins? {g} 🏆', 'Cat vs Dog Reaction: {g} 😳',
               'POV: Your Cat vs Your Dog ({g}) 🐾', 'Same Situation, Cat vs Dog: {g} 😂'],
}
TAGS = {'catdog': 'catvsdog'}


def load():
    return json.loads(HISTORY.read_text()) if HISTORY.exists() else {'videos': []}


PRIOR = {}


def performance(hist):
    """Kendi videolarımızın izlenmeleri (en az 20 saatlik olanlar) → format ve gag başına ortalama.
    YouTube'a erişilemezse boş döner; seçim o zaman PRIOR ile yapılır."""
    try:
        import upload
        if not upload.configured():
            return {}, {}
        now = datetime.now(timezone.utc)
        old = [v for v in hist['videos'][-40:] if v.get('kind', 'short') == 'short' and v.get('format')
               and (now - datetime.strptime(v['date'], '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)).total_seconds() > 20 * 3600]
        if not old:
            return {}, {}
        items = upload.client().videos().list(part='statistics', id=','.join(v['id'] for v in old)).execute()['items']
        views = {i['id']: int(i['statistics'].get('viewCount', 0)) for i in items}
    except Exception as e:
        print('performans okunamadı:', str(e)[:150]); return {}, {}
    fmt, gag = {}, {}
    for v in old:
        if v['id'] in views:
            fmt.setdefault(v['format'], []).append(views[v['id']])
            for g in v['gags']:
                gag.setdefault(g, []).append(views[v['id']])
    avg = lambda d: {k: sum(x) / len(x) for k, x in d.items()}
    return avg(fmt), avg(gag)


def weights(keys, perf, prior=None):
    """Keşif + sömürü: denenmemiş/az izlenen seçenek de şans bulur (taban 1), iyi gidenin ağırlığı en fazla 6."""
    prior = prior or {}
    top = max(perf.values(), default=0)
    return [max(prior.get(k, 1.0), 1.0 + 5.0 * perf[k] / top) if top and k in perf else prior.get(k, 1.0) for k in keys]


PET_ROOMS = ('living', 'kitchen', 'bedroom', 'office', 'library', 'greenhouse', 'hotel', 'cafe', 'bathroom', 'garage', 'diner', 'studio')


_TREND = None


def trend_gags(pool):
    """2026-10-12 trendler: YouTube arama önerilerinde adı geçen durumlar. Hata/erişim yoksa boş."""
    global _TREND
    if _TREND is None:
        _TREND = ''
        try:
            import requests
            for q in ('cat vs dog', 'cats vs dogs', 'funny cats', 'funny dogs'):
                r = requests.get('https://suggestqueries.google.com/complete/search',
                                 params={'client': 'firefox', 'ds': 'yt', 'hl': 'en', 'q': q}, timeout=6)
                _TREND += ' ' + ' '.join(r.json()[1]).lower()
        except Exception:
            pass
    hits = [k for k in pool if any(w in _TREND for w in paws.GAGS[k]['name'].lower().split() if len(w) > 3)]
    if hits:
        print('trend durumları:', hits, flush=True)
    return hits


def pick_plan(hist, rnd, perf=({}, {})):
    fperf, gperf = perf
    past = [v for v in hist['videos'] if v.get('kind', 'short') == 'short' and v.get('format')][-12:]  # derlemeler hariç
    last2 = [v['format'] for v in past[-2:]]
    fmts = [f for f in paws.FORMATS if not (len(last2) == 2 and last2[0] == last2[1] == f)] or list(paws.FORMATS)  # 3. kez üst üste yok
    fmt = rnd.choices(fmts, weights=weights(fmts, fperf, PRIOR))[0]
    last = past[-1] if past else {}
    cat = rnd.choice([c for c in paws.CATS if c != last.get('cat')])
    dog = rnd.choice([d for d in paws.DOGS if d != last.get('dog')])
    month = datetime.now(timezone.utc).month
    # bölüm özel durumlar: önce uzun bölümde çıkar; bölüm herkese açık olunca ya da 'debut' tarihi gelince Shorts'a girer
    shown = {g for v in hist['videos'] if v.get('kind') == 'episode' and v.get('privacy') == 'public'
             for g, *_ in v.get('items', [])}
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    pool = [k for k, g in paws.GAGS.items() if month in g.get('months', range(1, 13))
            and (not g.get('debut') or k in shown or today > g['debut'])]
    gw = dict(zip(pool, weights(pool, gperf)))
    for k in trend_gags(pool):                          # günün 'cat vs dog …' aramalarında geçen durum 3x
        gw[k] *= 3.0
    # tekrar cezası: son 6 videoda her kullanım ağırlığı 4'te birine indirir, son videodakiler hiç seçilmez;
    # hiç kullanılmamış gag 2 kat öne çıkar (viral gag'ler her videoya girip içeriği tekrarlamasın)
    recent = [g for v in past[-6:] for g in v.get('gags', [])]
    used_ever = {g for v in hist['videos'] for g in v.get('gags', [])}
    last_gags = set(past[-1]['gags']) if past else set()
    for k in pool:
        gw[k] *= 0.25 ** recent.count(k) * (2.0 if k not in used_ever else 1.0)
        if k in last_gags and len(pool) - len(last_gags) >= 4:
            gw[k] = 0.0
    gw = {k: (w if w > 0 else 1e-9) for k, w in gw.items()}
    seen_sets = {tuple(sorted(v['gags'])) for v in past}
    last_first = past[-1]['gags'][0] if past else None
    for _ in range(200):
        n, left, gags = 4, list(pool), []
        while len(gags) < n:                         # ağırlıklı, tekrarsız seçim
            g = rnd.choices(left, weights=[gw[k] for k in left])[0]
            gags.append(g); left.remove(g)
        if tuple(sorted(gags)) not in seen_sets and gags[0] != last_first:
            break
    last_room = past[-1].get('room') if past else None
    room = rnd.choice([r for r in PET_ROOMS if r != last_room])
    return dict(format=fmt, cat=cat, dog=dog, gags=gags, room=room, seed=rnd.randrange(10 ** 6))


# durum başına açıklama satırı (kedi ne yapar, köpek ne yapar) ve konuya özel etiket
LINES = {
    'doorbell': ('🔔', 'Doorbell: the cat keeps sleeping, the dog loses its mind', 'doorbell'),
    'vacuum': ('🧹', 'Vacuum: the cat says NOPE, the dog goes to war', 'vacuum'),
    'food': ('🍽️', 'Dinner: the cat is unimpressed, the dog inhales it', 'dinnertime'),
    'cup': ('🥛', 'Glass on the table: the cat knocks it off on purpose, the dog by accident', 'catlogic'),
    'bath': ('🛁', 'Bath time: the cat declares war, the dog jumps right in', 'bathtime'),
    'box': ('📦', 'Empty box: if it fits the cat sits, the dog destroys it', 'ififitsisits'),
    'laser': ('🔴', 'Red dot: the cat chases it into a wall, the dog chases its own tail', 'laserpointer'),
    'cucumber': ('🥒', 'Cucumber: the cat jumps to the ceiling, the dog eats it', 'cucumbercat'),
    'ball': ('🎾', 'Fetch: the cat takes a nap, the dog wants to go AGAIN', 'fetch'),
    'mirror': ('🪞', 'Mirror: the cat hisses at itself, the dog makes a new best friend', 'mirror'),
    'squeaky': ('🐤', 'Squeaky toy: one squeak for the cat, a hundred for the dog', 'squeakytoy'),
    'bed': ('🛏️', 'New bed: the cat picks the box, the dog picks violence', 'petbed'),
    'thunder': ('⛈️', 'Thunder: the cat hides, the dog needs a hug', 'thunderstorm'),
    'treat': ('🦴', 'Treat: the cat does no tricks, the dog does ALL the tricks', 'treats'),
    'cake': ('🎂', 'Birthday cake: the cat blows out the candle, the dog eats the cake', 'birthday'),
    'mail': ('✉️', 'Mail: the cat sits on it, the dog shreds it', 'mailman'),
    'sunbeam': ('☀️', 'Sunny spot: the cat melts, the dog overheats', 'sunbathing'),
    'bubbles': ('🫧', 'Bubbles: the cat feels betrayed, the dog has the best day ever', 'bubbles'),
    'fish': ('🐠', 'Goldfish: the cat gets splashed, the dog wants a friend', 'goldfish'),
    'yarn': ('🧶', 'Yarn: the cat gets tangled, the dog redecorates', 'yarn'),
}
HOOKS = ['Same situation. Totally different reactions. 😂', 'Cats and dogs will never agree on this. 🐱🐶',
         'Every pet owner has seen this happen. 🤣', 'Your cat vs your dog, be honest. 👀',
         'One house, two very different pets. 🏠', 'Who handled it better? 🏆']
ASKS = ['Team cat or team dog? Comment 1 or 2! 👇', 'Which one is YOUR pet: 1 or 2? 👇',
        'Who won: the cat (1) or the dog (2)? 👇', 'Is your pet a 1 or a 2? Tell us below! 👇']


def metadata(plan, hist, rnd):
    names = [paws.GAGS[k]['name'] for k in plan['gags']]
    g = f'{names[0]} & {names[1]}'
    cat, dog = paws.CATS[plan['cat']]['name'], paws.DOGS[plan['dog']]['name']
    used = {v['title'] for v in hist['videos']}
    opts = [t.format(g=g) for t in TITLES[plan['format']]]
    rnd.shuffle(opts)
    title = next((t for t in opts if t not in used), opts[0] + f' #{len(hist["videos"]) + 1}')
    lines = '\n'.join(f'{LINES[k][0]} {LINES[k][1]}' for k in plan['gags'] if k in LINES)
    tags_h = ' '.join(f'#{LINES[k][2]}' for k in plan['gags'][:2] if k in LINES)
    desc = (f'{rnd.choice(HOOKS)}\n\n'
            f'Starring {cat} the cat and {dog} the dog:\n{lines}\n\n'
            f'{rnd.choice(ASKS)}\n\n'
            f'New Paw Rivals cat vs dog Shorts every day. Subscribe and pick your side! 🐾\n\n'
            f'#shorts #catvsdog #funnyanimals {tags_h}')
    tags = ['paw rivals', 'cat vs dog', 'cats vs dogs', 'funny cats', 'funny dogs', 'funny animals', 'pet animation',
            'animated shorts', 'cat logic', 'dog logic', 'team cat', 'team dog', cat.lower(), dog.lower()] + [n.lower() for n in names]
    return title, desc, tags


def main():
    no_upload = '--no-upload' in sys.argv
    hist = load(); rnd = random.Random()
    perf = performance(hist)
    if perf[0]:
        print('format ortalama izlenme:', {k: round(v) for k, v in perf[0].items()}, flush=True)
    plan = pick_plan(hist, rnd, perf)
    title, desc, tags = metadata(plan, hist, rnd)
    vid_key = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    print(f'plan: {plan}\ntitle: {title}', flush=True)
    out = HERE / 'output' / vid_key
    mp4 = paws.render_video(plan, str(out))
    (out / 'meta.json').write_text(json.dumps(dict(plan=plan, title=title, description=desc, tags=tags), indent=2))
    if no_upload:
        print('render ok (yükleme yok):', mp4); return
    import upload
    if not upload.configured():
        sys.exit('YouTube secrets yok')
    print('kanal:', upload.check_channel())
    privacy = os.environ.get('YT_PRIVACY') or 'private'
    vid = upload.upload(mp4, title, desc, tags, privacy, category='15')
    print(f'yüklendi: https://youtube.com/shorts/{vid} ({privacy})')
    pl = json.loads(PLAYLISTS.read_text()) if PLAYLISTS.exists() else {}
    if plan['format'] in pl:
        try: upload.add_to_playlist(pl[plan['format']], vid)
        except Exception as e: print('playlist:', e)
    hist['videos'].append(dict(id=vid, date=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'), kind='short',
                               title=title, privacy=privacy, **plan))
    HISTORY.write_text(json.dumps(hist, indent=2, ensure_ascii=False) + '\n')
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if sum(v['date'].startswith(today) and v.get('kind', 'short') == 'short' for v in hist['videos']) == 1:
        social(mp4, title, f'https://youtube.com/shorts/{vid}', plan)


def social(mp4, title, url, plan):
    """Günün ilk videosu → social/ (artifact 'social-<run>'): fenek-shorts telegram-relay TikTok/Instagram için gönderir."""
    import shutil
    tiktok = f"{title}\nTeam cat or team dog? 1 or 2? 👇\n\n#catvsdog #cats #dogs #funnyanimals #fyp"
    insta = (f"{title}\n\nTeam cat or team dog? Comment 1 or 2 👇\nFollow for daily Paw Rivals 🐾\n\n"
             f"#catvsdog #cats #dogs #funnyanimals #animation")  # Instagram: en fazla 5
    soc = HERE / 'social'
    soc.mkdir(exist_ok=True)
    shutil.copy(mp4, soc / 'video.mp4')
    (soc / 'post.json').write_text(json.dumps({'channel': 'Paw Rivals', 'title': title, 'url': url, 'tiktok': tiktok,
                                               'instagram': insta}, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
