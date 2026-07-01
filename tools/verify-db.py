#!/usr/bin/env python3
"""Verify the final DB has all expected titles and test the search."""
import json, re
from pathlib import Path

MEDIA = Path(__file__).parent.parent / 'media-index.json'

m = json.load(open(MEDIA, 'r', encoding='utf-8'))

def norm(s):
    if not s: return ''
    s = str(s).lower()
    s = re.sub(r'\b(subbed|dubbed|sub|dub|tv series|series|movie|ova|ona|special)\b',' ',s)
    s = re.sub(r'\bseason\s*\d+\b',' ',s)
    s = re.sub(r'\bs\d+\b',' ',s)
    s = re.sub(r'[!？:：;''\"\"\".,·•\-–_()\[\]{}<>/]',' ',s)
    s = s.replace('&',' and ')
    s = re.sub(r'\s+',' ',s).strip()
    return s

idx = {}
for e in m:
    n = norm(e.get('canonicalTitle',''))
    if n: idx[n] = e
    for a in e.get('aliases',[]):
        n = norm(a)
        if n: idx[n] = e

test = ['Horimiya','Haikyu!!','Attack on Titan','Jujutsu Kaisen',
        'Demon Slayer','My Hero Academia','Spy x Family','Steins;Gate',
        'Death Note','One Piece','Summer Time Rendering','Blue Box']

print(f"Total DB entries: {len(m)}")
print(f"All have canonicalTitle: {all(e.get('canonicalTitle','') for e in m)}")
print()
for t in test:
    k = norm(t)
    found = idx.get(k)
    if found:
        ln = found['ratings']['learnnatively']['level']
        jpdb = found['ratings']['jpdb']['difficulty']
        print(f"  FOUND: '{t}' -> {found['canonicalTitle'][:40]:40s} LN={ln} jpdb={jpdb}")
    else:
        print(f"  MISS:  '{t}' NOT FOUND")