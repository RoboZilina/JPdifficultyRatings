#!/usr/bin/env python3
"""
Check how many ln-* entries can be enriched with aliases from the candidate pool.
Only the ones that need it (empty/missing aliases).
"""
import json, re, sys
from pathlib import Path
DATA = Path(__file__).parent.parent / 'data'

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
    cleaned = re.sub(r'\s*S\d+\s*$', '', title, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\s*(?:Season|Part|Vol|Volume)[.\s]*\d+.*$', '', cleaned, flags=re.IGNORECASE).strip()
    if cleaned != title: variants.add(normalize(cleaned))
    cleaned2 = re.sub(r'\s*\([^)]*\)\s*', '', title).strip()
    if cleaned2 != title: variants.add(normalize(cleaned2))
    cleaned3 = re.sub(r'\s*[:]\s*', ' ', title).strip()
    if cleaned3 != title: variants.add(normalize(cleaned3))
    return variants

final = json.load(open(Path(__file__).parent.parent / 'media-index.json', 'r'))
candidates = json.load(open(DATA / 'candidates_with_all.json', 'r'))

# Build candidate lookup (normalized -> candidate metadata)
rev = {}
for cand in candidates:
    titles = [cand.get('canonicalTitle','')]
    t = cand.get('titles', {}) or {}
    for k in ('en','ja_jp','ja','romaji'):
        if t.get(k): titles.append(t[k])
    if cand.get('aliases'):
        titles.extend(cand['aliases'])
    meta = {
        'en': t.get('en','') or '',
        'ja': t.get('ja_jp','') or t.get('ja','') or '',
        'rom': t.get('romaji','') or '',
        'cand_id': cand.get('id',''),
        'aliases': cand.get('aliases',[]) or [],
    }
    for title in titles:
        n = normalize(title)
        if n and n not in rev:
            rev[n] = meta

ln_entries = [e for e in final if e['id'].startswith('ln-')]
print(f"Candidate pool: {len(rev)} normalized forms")
print(f"ln-* entries:   {len(ln_entries)}")

# Categorize
with_aliases = 0
no_aliases_matchable = 0
no_aliases_unmatchable = 0
no_aliases_no_jpdb = 0
for e in ln_entries:
    ct = e.get('canonicalTitle','')
    has_al = bool(e.get('aliases'))
    has_jp = e['ratings']['jpdb']['difficulty'] is not None
    
    if has_al:
        with_aliases += 1
        continue
    
    # No aliases - can we match to candidate pool?
    matched = False
    for v in title_variants(ct):
        if v in rev:
            matched = True
            break
    
    if matched:
        no_aliases_matchable += 1
    else:
        no_aliases_unmatchable += 1
        if has_jp:
            no_aliases_no_jpdb += 1

print()
print(f"Already have aliases:        {with_aliases}")
print(f"No aliases but matchable:    {no_aliases_matchable}  (CAN enrich!)")
print(f"No aliases, no match:        {no_aliases_unmatchable}")
print(f"  - of those with jpdb too:  {no_aliases_no_jpdb}")

# Show some unmatchable samples
print()
print("Samples of unmatchable (no aliases, no candidate match):")
unmatchable = [e for e in ln_entries if not e.get('aliases') and not any(v in rev for v in title_variants(e.get('canonicalTitle','')))]
for e in unmatchable[:10]:
    jpdb = e['ratings']['jpdb']['difficulty']
    jp_str = f" jpdb={jpdb}" if jpdb else ""
    print(f"  {e['id']} | {e.get('canonicalTitle','')[:60]} L{e['ratings']['learnnatively']['level']}{jp_str}")