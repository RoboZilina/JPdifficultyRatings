#!/usr/bin/env python3
"""Debug why Blue Box enrichment isn't working."""
import json, re
from pathlib import Path

DATA = Path(__file__).parent.parent / 'data'
MEDIA = Path(__file__).parent.parent / 'media-index.json'

def normalize(s):
    if not s: return ''
    s = str(s).lower()
    s = re.sub(r'[^\w\s\u3000-\u9fff\uff00-\uffef\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def title_variants(title):
    variants = set()
    if not title: return variants
    variants.add(title)
    variants.add(normalize(title))
    cleaned = re.sub(r'\s*(?:Season|S\d+|Part|Vol|Volume)[.\s]*\d+.*$', '', title, flags=re.IGNORECASE).strip()
    if cleaned != title and cleaned:
        variants.add(normalize(cleaned))
    cleaned2 = re.sub(r'\s*\([^)]*\)\s*', '', title).strip()
    if cleaned2 != title and cleaned2:
        variants.add(normalize(cleaned2))
    cleaned3 = re.sub(r'\s*[:]\s*', ' ', title).strip()
    if cleaned3 != title and cleaned3:
        variants.add(normalize(cleaned3))
    return variants

candidates = json.load(open(DATA / 'candidates_with_all.json', 'r', encoding='utf-8'))

# Build enrich_idx like build-merged-db.py
enrich_idx = {}
for c in candidates:
    cid = c.get('id', '')
    if not cid: continue
    titles = c.get('titles', {})
    en = titles.get('en', '') if isinstance(titles, dict) else ''
    ja = titles.get('ja_jp', '') or titles.get('ja', '') or '' if isinstance(titles, dict) else ''
    rom = titles.get('romaji', '') if isinstance(titles, dict) else ''
    aliases = c.get('aliases', []) or []
    meta = {'en': en, 'ja': ja, 'romaji': rom, 'aliases': aliases}
    for title in [c.get('canonicalTitle',''), en, ja, rom] + aliases:
        if title:
            n = normalize(title)
            if n and n not in enrich_idx:
                enrich_idx[n] = meta

# Debug: check every variant of "アオのハコ S1"
ct = "アオのハコ S1"
print("Variants of ct:", title_variants(ct))
for v in title_variants(ct):
    match = v in enrich_idx
    print(f"  '{v}' in enrich_idx: {match}")
    if match:
        m = enrich_idx[v]
        print(f"    en={m['en']}, ja={m['ja']}, aliases={m['aliases'][:3]}")

# Check what keys match "アオのハコ" specifically
print("\nAll enrich_idx keys containing 'アオのハコ':")
keys = [k for k in enrich_idx if 'アオのハコ' in k]
for k in keys[:5]:
    print(f"  '{k}' -> en={enrich_idx[k]['en']}, ja={enrich_idx[k]['ja']}")