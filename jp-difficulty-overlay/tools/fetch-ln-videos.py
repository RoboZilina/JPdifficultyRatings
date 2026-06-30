#!/usr/bin/env python3
"""Fetch ALL pages from LearnNatively Video library."""

import json, time, urllib.request, http.cookiejar, sys, os

COOKIE = 'csrftoken=5r8kCglbLP4fTNfVccKBr0GZhoW0CNRvzQVqoVMZJzCWsswC9gTPm6JYGWFVUEkp; sessionid=96serekcdh9itgz5gr852dk9upt2bqzl'

def get_opener():
    jar = http.cookiejar.CookieJar()
    csrf = ''
    for p in COOKIE.split(';'):
        if '=' in p:
            n, v = p.split('=', 1)
            n, v = n.strip(), v.strip()
            if n == 'csrftoken': csrf = v
            jar.set_cookie(http.cookiejar.Cookie(0, n, v, None, False, 'learnnatively.com', True, False, '/', True, False, None, False, None, None, {}, False))
    h = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json',
         'X-Requested-With': 'XMLHttpRequest', 'Referer': 'https://learnnatively.com/search/jpn/videos/',
         'X-CSRFToken': csrf}
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)), h

def fetch_page(opener, h, lib_type, page):
    data = json.dumps({'libraryType': lib_type, 'language': 'jpn', 'sort': 'popular', 'page': page}).encode()
    req = urllib.request.Request('https://learnnatively.com/api/search-api/', data=data, headers=h)
    return json.loads(opener.open(req).read().decode('utf-8'))

def extract_items(result):
    items = []
    for item in result.get('results', []):
        if not isinstance(item, dict): continue
        p = item.get('item') or item.get('series') or item
        r = p.get('rating', {}) or {}
        items.append({
            'id': p.get('id', ''),
            'title': p.get('title', ''),
            'englishTitle': p.get('englishTitle', ''),
            'mediaType': p.get('mediaType', ''),
            'libraryType': p.get('libraryType', ''),
            'url': p.get('url', ''),
            'genres': p.get('genres', []),
            'lvl': r.get('lvl') if isinstance(r, dict) else None,
            'descriptor': r.get('lvlDescriptor', '') if isinstance(r, dict) else '',
        })
    return items

def main():
    opener, h = get_opener()
    data_dir = 'd:/DifficultyRatings/jp-difficulty-overlay/data'
    
    # Only fetch 'videos' (plural) - this is the real video catalog
    lib_type = 'videos'
    print(f'\nFetching ALL pages for libraryType="{lib_type}"...')
    
    result = fetch_page(opener, h, lib_type, 1)
    total = result.get('totalCount', 0)
    pages = result.get('numOfPages', 1)
    print(f'Total: {total} items across {pages} pages')
    
    all_items = {}
    
    for page in range(1, pages + 1):
        result = fetch_page(opener, h, lib_type, page)
        for item in result.get('results', []):
            if not isinstance(item, dict): continue
            p = item.get('item') or item.get('series') or item
            r = p.get('rating', {}) or {}
            entry = {
                'id': p.get('id', ''),
                'title': p.get('title', ''),
                'englishTitle': p.get('englishTitle', ''),
                'mediaType': p.get('mediaType', ''),
                'url': p.get('url', ''),
                'genres': p.get('genres', []),
                'lvl': r.get('lvl') if isinstance(r, dict) else None,
                'descriptor': r.get('lvlDescriptor', '') if isinstance(r, dict) else '',
            }
            all_items[entry['id']] = entry
        
        if page % 10 == 0 or page == 1 or page == pages:
            print(f'  Page {page}/{pages}: {len(result.get("results",[]))} items (total unique: {len(all_items)})')
        time.sleep(0.3)
    
    catalog = sorted(all_items.values(), key=lambda x: x['title'] or '')
    outfile = f'{data_dir}/ln-video-catalog.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    rated = sum(1 for c in catalog if c['lvl'] is not None)
    print(f'\nSaved: {outfile}')
    print(f'{len(catalog)} items, {rated} with ratings')
    
    # Show sample
    print('\nSample items:')
    for c in catalog[:5]:
        print(f'  {c.get("title","?")[:40]:40s} | {c.get("mediaType","?")} | L{c.get("lvl","?")}')

if __name__ == '__main__':
    main()
