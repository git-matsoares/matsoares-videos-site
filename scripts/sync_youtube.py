"""Collect the latest public Shorts from the channel page, without an API key.
YouTube may change this public page format; failures preserve the previous feed.
"""
import json, os, re, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
OUT = Path(__file__).resolve().parents[1] / 'videos.json'
URL = 'https://www.youtube.com/@soumatsoares/shorts'

def parse(html):
    match = re.search(r'var ytInitialData = (.*?);</script>', html, re.S)
    if not match: raise ValueError('YouTube page format unavailable')
    data = json.loads(match[1])
    items, seen = [], set()
    def walk(value):
        if isinstance(value, dict):
            model = value.get('shortsLockupViewModel')
            if model:
                command = model.get('onTap', {}).get('innertubeCommand', {})
                ident = command.get('reelWatchEndpoint', {}).get('videoId', '')
                title = model.get('overlayMetadata', {}).get('primaryText', {}).get('content', '')
                if re.fullmatch(r'[A-Za-z0-9_-]{11}', ident) and title and ident not in seen:
                    seen.add(ident)
                    items.append(dict(id=ident,title=title,description=''))
                return
            for child in value.values(): walk(child)
        elif isinstance(value,list):
            for child in value: walk(child)
    walk(data)
    if not items: raise ValueError('No Shorts found; keep previous feed')
    return dict(source='youtube-shorts',channel='@soumatsoares',updatedAt=datetime.now(timezone.utc).isoformat(),items=items[:12])

def main():
    request = Request(URL, headers={'User-Agent':'Mozilla/5.0','Accept-Language':'pt-BR,pt;q=0.9'})
    with urlopen(request,timeout=30) as response: feed=parse(response.read().decode('utf-8'))
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding='utf-8'))
        if previous.get('items') == feed['items']:
            print('Shorts unchanged; no commit needed.')
            return
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=OUT.parent,delete=False) as output:
        json.dump(feed,output,ensure_ascii=False,indent=2)
        temporary=output.name
    os.replace(temporary,OUT)
    print(f"Feed generated: {len(feed['items'])} Shorts.")
if __name__=='__main__':
    try: main()
    except Exception:
        print('Shorts synchronization failed. Previous feed preserved; no upload performed.',file=sys.stderr)
        sys.exit(1)
