"""history.json'daki videoların açıklamasını run.metadata ile yeniden yazar (başlık korunur)."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run, upload

hist = run.load()
yt = upload.client()
for v in hist['videos']:
    if v.get('kind', 'short') != 'short':
        continue
    _, desc, tags = run.metadata(v, {'videos': []}, random.Random(v['id']))
    cur = yt.videos().list(part='snippet', id=v['id']).execute()['items'][0]['snippet']
    body = {'id': v['id'], 'snippet': {'title': cur['title'], 'description': desc, 'tags': tags, 'categoryId': cur['categoryId']}}
    yt.videos().update(part='snippet', body=body).execute()
    print('updated', v['id'], cur['title'])
