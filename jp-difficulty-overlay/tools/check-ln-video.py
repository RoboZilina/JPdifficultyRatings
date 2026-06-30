#!/usr/bin/env python3
"""Check what LearnNatively 'video' library returns."""

import json, urllib.request, http.cookiejar

COOKIE = 'csrftoken=5r8kCglbLP4fTNfVccKBr0GZhoW0CNRvzQVqoVMZJzCWsswC9gTPm6JYGWFVUEkp; sessionid=96serekcdh9itgz5gr852dk9upt2bqzl'

jar = http.cookiejar.CookieJar()
csrf = ''
for p in COOKIE.split(';'):
    if '=' in p:
        n,v = p.split('=',1); n,v = n.strip(),v.strip()
        if n=='csrftoken': csrf=v
        jar.set_cookie(http.cookiejar.Cookie(0,n,v,None,False,'learnnatively.com',True,False,'/',True,False,None,False,None,None,{},False))
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
h = {'User-Agent':'Mozilla/5.0','Content-Type':'application/json','X-Requested-With':'XMLHttpRequest','X-CSRFToken':csrf,'Referer':'https://learnnatively.com/search/jpn/videos/'}

r = json.loads(opener.open(urllib.request.Request('https://learnnatively.com/api/search-api/',data=json.dumps({'libraryType':'video','language':'jpn','sort':'popular','page':1}).encode(),headers=h)).read())

print(f'Total: {r.get("totalCount")}')
print(f'Pages: {r.get("numOfPages")}')
print(f'Page 1 items: {len(r["results"])}')

# Show types  
types = {}
for item in r['results']:
    p = item.get('item') or item.get('series') or item
    mt = p.get('mediaType','?')
    lib = p.get('libraryType','?')
    t = f'{lib}/{mt}'
    types[t] = types.get(t,0)+1
print(f'\nType breakdown (page 1):')
for t,c in sorted(types.items(), key=lambda x:-x[1]):
    print(f'  {t}: {c}')

print(f'\nFirst 5 items:')
for item in r['results'][:5]:
    p = item.get('item') or item.get('series') or item
    t = p.get('title','?')[:40]
    mt = p.get('mediaType','?')
    lvl = p.get('rating',{}).get('lvl','?')
    print(f'  {t:40s} | {mt:20s} | L{lvl}')