#!/usr/bin/env python3
"""Fetch ALL pages from LearnNatively (video + book catalogs)."""

import json, time, urllib.request, http.cookiejar

COOKIE = 'csrftoken=5r8kCglbLP4fTNfVccKBr0GZhoW0CNRvzQVqoVMZJzCWsswC9gTPm6JYGWFVUEkp; sessionid=96serekcdh9itgz5gr852dk9upt2bqzl'

def get_opener_csrf():
    jar = http.cookiejar.CookieJar()
    csrf = ''
    for p in COOKIE.split(';'):
        if '=' in p:
            n, v = p.split('=', 1)
            n, v = n.strip(), v.strip()
            if n == 'csrftoken': csrf = v
            jar.set_cookie(http.cookiejar.Cookie(0, n, v, None, False, 'learnnatively.com', True, False, '/', True, False, None, False, None, None, {}, False))
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    return opener, csrf

def fetch_page(opener, csrf, lib_type, page):
    h = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json',
         'X-Requested-With': 'XMLHttpRequest', 'Referer': 'https://learnnatively.com/search/jpn/videos/',
         'X-CSRFToken': csrf}
    data = json.dumps({'libraryType': lib_type, 'language': 'jpn', 'sort': 'popular', 'page': page}).encode()
    req = urllib.request.Request('https://learnnatively.com/api/search-api/', data=data, headers=h)
    resp = json.loads(opener.open(req).read().decode('utf-8'))
    return resp

def extract_items(result):
    items = []
    for item in result.get('results', []):
        if not isinstance(item, dict): continue
        payload = item.get('item') or item.get('series') or item
        r = payload.get('rating', {}) or {}
        items.append({
            'id': payload.get('id', ''),
            'title': payload.get('title', ''),
            'englishTitle': payload.get('englishTitle', ''),
            'mediaType': payload.get('mediaType', ''),
            'libraryType': payload.get('libraryType', ''),
            'url': payload.get('url', ''),
            'genres': payload.get('genres', []),
            'lvl': r.get('lvl') if isinstance(r, dict) else None,
            'descriptor': r.get('lvlDescriptor', '') if isinstance(r, dict) else '',
        })
    return items

def fetch_with_retry(opener, csrf, lib_type, page, retries=2):
    for attempt in range(retries):
        try:
            return fetch_page(opener, csrf, lib_type, page)
        except Exception as e:
            if attempt < retries - 1:
                print(f'  Retry page {page} ({e})')
                time.sleep(1)
            else:
                print(f'  Failed page {page}: {e}')
                return None

def main():
    opener, csrf = get_opener_csrf()
    DATA_DIR = 'd:/DifficultyRatings/jp-difficulty-overlay/data'
    
    for lib_type in ['book', 'video']:
        print(f'\nFetching {lib_type} catalog...')
        all_items = {}
        
        result = fetch_with_retry(opener, csrf, lib_type, 1)
        if not result:
            continue
        total = result.get('totalCount', 0)
        num_pages = result.get('numOfPages', 1)
        print(f'  Total: {total} items across {num_pages} pages')
        
        items = extract_items(result)
        for it in items:
            all_items[it['id']] = it
        print(f'  Page 1/{num_pages}: {len(items)} items (total: {len(all_items)})')
        
        for page in range(2, num_pages + 1):
            result = fetch_with_retry(opener, csrf, lib_type, page)
            if not result:
                print(f'  Stopped at page {page} due to error')
                break
            items = extract_items(result)
            for it in items:
                all_items[it['id']] = it
            if page % 10 == 0 or page == num_pages:
                print(f'  Page {page}/{num_pages}: {len(items)} items (total: {len(all_items)})')
            time.sleep(0.3)
        
            # Save incrementally every 50 pages
            if page % 50 == 0:
                temp = sorted(all_items.values(), key=lambda x: x['title'] or '')
                with open(f'{DATA_DIR}/ln-{lib_type}-catalog-partial.json', 'w', encoding='utf-8') as f:
                    json.dump(temp, f, indent=2, ensure_ascii=False)
        
        catalog = sorted(all_items.values(), key=lambda x: x['title'] or '')
        outfile = f'{DATA_DIR}/ln-{lib_type}-catalog.json'
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        rated = sum(1 for c in catalog if c['lvl'] is not None)
        print(f'\n  Saved: {outfile}')
        print(f'  {len(catalog)} items, {rated} with ratings')

if __name__ == '__main__':
    main()