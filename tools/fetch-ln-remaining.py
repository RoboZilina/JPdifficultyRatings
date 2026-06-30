#!/usr/bin/env python3
"""Continue fetching LN catalog from page 50 onwards (we already have 0-50)."""

import json, time, urllib.request, http.cookiejar, sys

COOKIE = 'csrftoken=5r8kCglbLP4fTNfVccKBr0GZhoW0CNRvzQVqoVMZJzCWsswC9gTPm6JYGWFVUEkp; sessionid=96serekcdh9itgz5gr852dk9upt2bqzl'

def get_opener():
    jar = http.cookiejar.CookieJar()
    for p in COOKIE.split(';'):
        if '=' in p:
            n,v = p.split('=',1)
            if n.strip()=='csrftoken': csrf=v.strip()
            jar.set_cookie(http.cookiejar.Cookie(0,n.strip(),v.strip(),None,False,'learnnatively.com',True,False,'/',True,False,None,False,None,None,{},False))
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)), csrf

def fetch(opener, csrf, lib, page):
    h = {'User-Agent':'Mozilla/5.0','Content-Type':'application/json','X-Requested-With':'XMLHttpRequest',
         'Referer':'https://learnnatively.com/search/jpn/videos/','X-CSRFToken':csrf}
    data = json.dumps({'libraryType':lib,'language':'jpn','sort':'popular','page':page}).encode()
    req = urllib.request.Request('https://learnnatively.com/api/search-api/',data=data,headers=h)
    return json.loads(opener.open(req).read().decode('utf-8'))

def extract(r):
    items = []
    for item in r.get('results',[]):
        if not isinstance(item,dict): continue
        p = item.get('item') or item.get('series') or item
        rt = p.get('rating',{}) or {}
        d = p.get('libraryType') or item.get('libraryType','')
        items.append({
            'id':p.get('id',''),'title':p.get('title',''),'englishTitle':p.get('englishTitle',''),
            'mediaType':p.get('mediaType',''),'libraryType':d,'url':p.get('url',''),
            'genres':p.get('genres',[]),'lvl':rt.get('lvl') if isinstance(rt,dict) else None,
            'descriptor':rt.get('lvlDescriptor','') if isinstance(rt,dict) else '',
        })
    return items

def main():
    opener, csrf = get_opener()
    d = 'd:/DifficultyRatings/jp-difficulty-overlay/data'
    
    for lib in ['book']:
        print(f'Fetching {lib}...')
        
        # Get first page to know total
        try:
            r = fetch(opener, csrf, lib, 1)
            total = r['totalCount']; pages = r['numOfPages']
            print(f'  {total} items, {pages} pages')
        except:
            print('  Failed page 1'); continue
        
        all_ids = set()
        
        for page in range(1, pages+1):
            try:
                r = fetch(opener, csrf, lib, page)
                items = extract(r)
                if not items: break
                for it in items: all_ids.add(it['id'])
                if page % 20 == 0:
                    print(f'  Page {page}/{pages}: {len(items)} items, {len(all_ids)} unique')
            except Exception as e:
                print(f'  Stopped at page {page}: {e}')
                break
            time.sleep(0.3)
        
        print(f'  Total unique IDs: {len(all_ids)}')

if __name__ == '__main__':
    main()