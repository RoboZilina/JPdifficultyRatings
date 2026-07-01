#!/usr/bin/env python3
"""Check if 'Blue Box' is in the LN catalog and merged DB."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
MEDIA_INDEX = Path(__file__).parent.parent / 'media-index.json'

ln = json.load(open(DATA_DIR / 'ln-video-catalog.json', 'r', encoding='utf-8'))
m = json.load(open(MEDIA_INDEX, 'r', encoding='utf-8'))

# Search LN catalog for Blue Box
print("=== LN Catalog Search ===")
for e in ln:
    t = (e.get('title','') + ' ' + e.get('englishTitle','')).lower()
    if 'blue' in t or 'ao no' in t or 'hako' in t:
        print(f"  id={e['id']} title={e['title']} eng={e.get('englishTitle','')} url={e['url']} lvl={e.get('lvl')}")

# Search merged DB
print("\n=== Merged DB Search ===")
for e in m:
    t = (e.get('canonicalTitle','') + ' ' + ' '.join(e.get('aliases',[]))).lower()
    if 'blue' in t or 'ao no' in t or 'hako' in t:
        print(f"  id={e['id']} title={e['canonicalTitle']} ln={e['ratings']['learnnatively']['level']} jpdb={e['ratings']['jpdb']['difficulty']}")

# Also check candidates
c = json.load(open(DATA_DIR / 'candidates_with_all.json', 'r', encoding='utf-8'))
print("\n=== Candidates Search ===")
for e in c:
    t = (e.get('canonicalTitle','') + ' ' + e.get('titles',{}).get('en','') + ' ' + e.get('titles',{}).get('ja_jp','')).lower()
    if 'blue' in t or 'ao no' in t or 'hako' in t:
        jpdb = e.get('ratings',{}).get('jpdb',{}).get('difficulty') if isinstance(e.get('ratings'), dict) else None
        print(f"  id={e.get('id','')} title={e.get('canonicalTitle','')} jpdb={jpdb}")