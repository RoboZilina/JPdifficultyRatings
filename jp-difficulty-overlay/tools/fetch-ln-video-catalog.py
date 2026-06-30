#!/usr/bin/env python3
"""Fetch LearnNatively video catalog using browser session cookies."""

import json, os, sys, time, urllib.request, http.cookiejar
from pathlib import Path

DATA_DIR = Path('d:/DifficultyRatings/jp-difficulty-overlay/data')
API_BASE = "https://learnnatively.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://learnnatively.com/search/jpn/videos/',
    'X-CSRFToken': '',
}

def setup_session(cookie_string):
    cookie_jar = http.cookiejar.CookieJar()
    csrf_token = ''
    for part in cookie_string.split(';'):
        part = part.strip()
        if '=' in part:
            n, v = part.split('=', 1)
            n, v = n.strip(), v.strip()
            if n == 'csrftoken':
                csrf_token = v
            c = http.cookiejar.Cookie(0, n, v, None, False, 'learnnatively.com', True, False, '/', True, False, None, False, None, None, {}, False)
            cookie_jar.set_cookie(c)
    if csrf_token:
        HEADERS['X-CSRFToken'] = csrf_token
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def post_search(opener, page=1):
    data = json.dumps({'libraryType':'video','language':'jpn','sort':'popular','page':page}).encode()
    req = urllib.request.Request(f"{API_BASE}/api/search-api/", data=data, headers=HEADERS)
    try:
        return json.loads(opener.open(req, timeout=15).read().decode('utf-8'))
    except Exception as e:
        print(f"  Error: {e}")
        return None

def extract(payload):
    if not isinstance(payload, dict): return None
    r = payload.get('rating', {})
    if not isinstance(r, dict): r = {}
    result = {
        'id': payload.get('id',''),
        'title': payload.get('title',''),
        'englishTitle': payload.get('englishTitle',''),
        'url': payload.get('url',''),
        'mediaType': payload.get('mediaType',''),
        'libraryType': payload.get('libraryType',''),
        'genres': payload.get('genres',[]),
        'lvl': r.get('lvl'),
        'descriptor': r.get('lvlDescriptor',''),
    }
    for k in ['mal_id','tmdb_id','imdb_id']:
        if k in payload: result[k] = payload[k]
    return result

def main():
    print("="*60)
    print("  Fetch LearnNatively Video Catalog")
    print("="*60)
    print()
    print("HOW TO GET COOKIES from Chrome/Firefox:")
    print("1. Go to learnnatively.com, log in if needed")
    print("2. F12 -> Network tab -> refresh page")
    print("3. Click any request, find 'Cookie:' in Request Headers")
    print("4. Copy the entire cookie string")
    print("5. Paste below")
    print()
    
    cookie = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('LN_COOKIES', '')
    if not cookie:
        print("No cookies provided.")
        return
    
    opener = setup_session(cookie)
    
    # First try: search-api POST
    print("\nTrying search-api...")
    result = post_search(opener, 1)
    
    if result:
        print(f"Success! Response keys: {list(result.keys())[:10]}")
        
        # Find items and paginate
        items_key = None
        for k in ['items','results','data','entries']:
            if isinstance(result.get(k), list):
                items_key = k
                break
        
        if not items_key:
            for k,v in result.items():
                if isinstance(v, list) and len(v) > 0:
                    items_key = k
                    break
        
        total_pages = result.get('total_pages', result.get('pages', result.get('meta',{}).get('total_pages', 1)))
        if isinstance(total_pages, dict):
            total_pages = 1
        print(f"Total pages: {total_pages}")
        
        all_items = {}
        page = 1
        
        while page <= total_pages:
            if page > 1:
                result = post_search(opener, page)
                if not result: break
            
            items = result.get(items_key, []) if items_key else result
            if isinstance(items, dict):
                items = list(items.values()) if isinstance(items.get(list(items.keys())[0]), dict) else []
            
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        # Handle nested: {item: {...}} or {series: {...}}
                        payload = item.get('item') or item.get('series') or item
                        ext = extract(payload)
                        if ext and ext['id']:
                            all_items[ext['id']] = ext
            
            print(f"  Page {page}/{total_pages}: {len(items) if isinstance(items,list) else 0} items (total unique: {len(all_items)})")
            
            if isinstance(items, list) and len(items) < 20:
                break
            page += 1
            time.sleep(0.3)
        
        catalog = sorted(all_items.values(), key=lambda x: x['title'] or '')
        with open(str(DATA_DIR / 'ln-video-catalog.json'), 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        rated = sum(1 for c in catalog if c['lvl'] is not None)
        print(f"\nCatalog saved: {len(catalog)} items, {rated} with ratings")
        
        # Show samples
        for c in catalog[:5]:
            print(f"  {c['title'][:40]:40s} | L{c['lvl'] or '?'} | {c['mediaType'][:15]}")
    else:
        print("Failed. Try getting fresh cookies and running again.")
        print("\nNeed sessionid and csrftoken cookies from a logged-in browser.")

if __name__ == '__main__':
    main()