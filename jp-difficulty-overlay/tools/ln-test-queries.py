#!/usr/bin/env python3
"""Test what kind of items autocomplete returns for different queries."""

import json
import urllib.request

H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def test(q):
    url = f'https://learnnatively.com/api/autocomplete-api/?q={urllib.request.quote(q)}&libraryType=video'
    try:
        data = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=H)).read())
        if isinstance(data, list):
            print(f'\n{q:20s}: {len(data)} items')
            for item in data:
                payload = item.get('item') or item.get('series') or {}
                t = payload.get('title','')[:30]
                mt = payload.get('mediaType','?')
                lt = payload.get('libraryType','?')
                lvl = payload.get('rating', {}).get('lvl', '?')
                print(f'  {t:30s} | media={mt:15s} | lib={lt:10s} | L{lvl}')
    except Exception as e:
        print(f'{q}: {str(e)[:50]}')

# Test queries that should match video content
for q in ['bocchi', 'alice', 'attack', 'terrace', 'jujutsu', 'demonslayer', 'fullmetal', 'deathnote', 'naruto', 'one piece']:
    test(q)