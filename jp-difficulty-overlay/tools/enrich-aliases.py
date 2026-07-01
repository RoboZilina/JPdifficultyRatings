#!/usr/bin/env python3
"""Enrich 6,800 rated entries with English aliases from 22k candidates."""
import json, re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
MEDIA_FILE = Path(__file__).parent.parent / 'media-index.json'

def normalize(s):
    if not s: return ''
    s = str(s).lower()
    s = re.sub(r'[^\w\s\u3000-\u9fff\uff00-\uffef\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def title_variants(title):
    variants = set()
    if not title: return variants
    variants.add(normalize(title))
    # Strip S1, Season 1, etc.
    cleaned = re.sub(r'\s*S\d+\s*$', '', title, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\s*(?:Season|Part|Vol|Volume)[.\s]*\d+.*$', '', cleaned, flags=re.IGNORECASE).strip()
    if cleaned != title: variants.add(normalize(cleaned))
    cleaned2 = re.sub(r'\s*\([^)]*\)\s*', '', title).strip()
    if cleaned2 != title: variants.add(normalize(cleaned2))
    cleaned3 = re.sub(r'\s*[:]\s*', ' ', title).strip()
    if cleaned3 != title: variants.add(normalize(cleaned3))
    return variants

# Build reverse index from candidates
print("Building candidate lookup...")
candidates = json.load(open(DATA_DIR / 'candidates_with_all.json', 'r', encoding='utf-8'))
rev = {}
for cand in candidates:
    titles = [cand.get('canonicalTitle', '')]
    t = cand.get('titles', {})
    if isinstance(t, dict):
        for k in ('en', 'ja_jp', 'ja', 'romaji'):
            if t.get(k): titles.append(t[k])
    if isinstance(cand.get('aliases'), list):
        titles.extend(cand['aliases'])
    meta = {
        'en': t.get('en', '') if isinstance(t, dict) else '',
        'ja': t.get('ja_jp', '') or t.get('ja', '') or '' if isinstance(t, dict) else '',
        'rom': t.get('romaji', '') if isinstance(t, dict) else '',
        'aliases': cand.get('aliases', []) or [],
    }
    for title in titles:
        n = normalize(title)
        if n and n not in rev:
            rev[n] = meta

print(f"  Lookup table: {len(rev)} entries")

# Load the built DB
m = json.load(open(MEDIA_FILE, 'r', encoding='utf-8'))
print(f"  Loaded DB: {len(m)} entries")

# Enrich each entry
enriched = 0
for entry in m:
    existing = set(entry.get('aliases', []))
    for v in title_variants(entry.get('canonicalTitle', '')):
        if v and v in rev:
            meta = rev[v]
            for t in [meta['ja'], meta['rom'], meta['en']]:
                if t and t != entry['canonicalTitle'] and t not in existing:
                    existing.add(t)
                    enriched += 1
            for a in meta['aliases']:
                if a and a != entry['canonicalTitle'] and a not in existing:
                    existing.add(a)
                    enriched += 1
            break  # one match is enough
    entry['aliases'] = sorted(existing)

# Save
json.dump(m, open(DATA_DIR / 'media-index-merged.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"  Enriched: {enriched} aliases added")
print(f"  Saved: {len(m)} entries")

# Verify Blue Box
bb = [e for e in m if 'アオのハコ' in (e.get('canonicalTitle', ''))]
for e in bb:
    print(f"  Blue Box: {e['canonicalTitle']} L={e['ratings']['learnnatively']['level']} aliases={e.get('aliases', [])[:3]}")