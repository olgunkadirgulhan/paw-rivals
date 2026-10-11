"""Önizleme sayfası: her durum için kedi ortası/sonu ve köpek ortası/sonu kareleri (output/preview/sheet_*.png)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paws
from PIL import Image

gags = sys.argv[1].split(',') if len(sys.argv) > 1 else list(paws.GAGS)
out = os.path.join(paws.HERE, 'output', 'preview'); os.makedirs(out, exist_ok=True)
for c in range(0, len(gags), 3):
    grp = gags[c:c + 3]
    plan = dict(format='catdog', cat=os.environ.get('CAT', 'ginger'), dog=os.environ.get('DOG', 'goldie'), seed=1,
                room=os.environ.get('ROOM', 'living'), gags=grp)
    paws.configure(plan)
    times = [1.6, 2.9, 3.95, 5.6, 6.9, 7.95]
    tiles = []
    for k in range(len(grp)):
        for tl in times:
            tiles.append(paws.render_frame(int((paws.INTRO + k * paws.GAG + tl) * paws.FPS)).resize((270, 480)))
    g = Image.new('RGB', (270 * len(times), 480 * len(grp)))
    for i, im in enumerate(tiles): g.paste(im, ((i % len(times)) * 270, (i // len(times)) * 480))
    g.save(os.path.join(out, f'sheet_{c // 3}.png'))
    print('sheet', c // 3, grp, flush=True)
