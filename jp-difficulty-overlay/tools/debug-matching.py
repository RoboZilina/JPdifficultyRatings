#!/usr/bin/env python3
"""Debug why titles in the DB aren't found by the extension's search."""

import json, re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
MEDIA_INDEX = Path(__file__).parent.parent / 'media-index.json'

def normalize_title(title):
    """Exact replica of content.js normalizeTitle."""
    if not title: return ""
    s = str(title).lower()
    s = re.sub(r'\b(subbed|dubbed|sub|dub)\b', ' ', s)
    s = re.sub(r'\b(tv series|series|movie|ova|ona|special)\b', ' ', s)
    s = re.sub(r'\bseason\s*\d+\b', ' ', s)
    s = re.sub(r'\bs\d+\b', ' ', s)
    s = re.sub(r'[!！?？:：;：;；\'\'\"\"\".,・·•\-–—_()\[\]{}<>/]', ' ', s)
    s = s.replace('&', ' and ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_title_compact(title):
    """Exact replica of content.js normalizeTitleCompact."""
    return normalize_title(title).replace(' ', '')

def build_search_index(items):
    """Exact replica of content.js buildSearchIndex logic."""
    idx = {}
    for item in items:
        if item.get('canonicalTitle'):
            normal = normalize_title(item['canonicalTitle'])
            compact = normalize_title_compact(item['canonicalTitle'])
            if normal: idx[normal] = item['id']
            if compact and compact != normal: idx[compact] = item['id']
        for alias in (item.get('aliases') or []):
            normal = normalize_title(alias)
            compact = normalize_title_compact(alias)
            if normal: idx[normal] = item['id']
            if compact and compact != normal: idx[compact] = item['id']
    return idx

def main():
    items = json.load(open(MEDIA_INDEX, 'r', encoding='utf-8'))
    print(f"Total DB entries: {len(items)}")
    
    # 1. Build the exact index the extension builds
    idx = build_search_index(items)
    print(f"Search index keys: {len(idx)}")
    
    # 2. How many entries would be found by canonicalTitle alone?
    by_canonical = set()
    for item in items:
        if item.get('canonicalTitle'):
            n = normalize_title(item['canonicalTitle'])
            if n in idx: by_canonical.add(item['id'])
    print(f"Entries findable via canonicalTitle normalization: {len(by_canonical)}")
    
    # 3. Entries with aliases (extra search paths)
    with_aliases = [e for e in items if e.get('aliases') and len(e['aliases']) > 0]
    print(f"Entries with aliases: {len(with_aliases)}")
    
    # 4. Simulated page titles → see if they match
    print("\n--- Simulated page title matches ---")
    test_titles = [
        "Haikyu!!",
        "Haikyu!! Season 1",
        "Haikyuu!! Lev Genzan!",
        "Attack on Titan",
        "Attack on Titan Season 1",
        "Shingeki no Kyojin",
        "Jujutsu Kaisen",
        "Jujutsu Kaisen Season 1",
        "Demon Slayer",
        "Kimetsu no Yaiba",
        "Summer Time Rendering",
        "Steins;Gate",
        "Death Note",
        "My Hero Academia",
        "One Punch Man",
        "One Piece",
        "Spy x Family",
    ]
    for t in test_titles:
        n = normalize_title(t)
        c = normalize_title_compact(t)
        match_id = idx.get(n) or idx.get(c)
        found_item = None
        if match_id:
            found_item = next((e for e in items if e['id'] == match_id), None)
        title_found = found_item['canonicalTitle'] if found_item else 'NOT FOUND'
        print(f"  '{t}' -> norm='{n}' -> {title_found}")
    
    # 5. Check for normalization collisions
    print("\n--- Keys that map to multiple entries (collisions) ---")
    from collections import Counter
    # Check how many canonical titles normalize to the same key
    norm_counts = Counter()
    for item in items:
        if item.get('canonicalTitle'):
            norm_counts[normalize_title(item['canonicalTitle'])] += 1
    collisions = {k: v for k, v in norm_counts.items() if v > 1}
    print(f"Normalization collisions: {len(collisions)} keys map to multiple entries")
    for k, v in sorted(collisions.items(), key=lambda x: -x[1])[:10]:
        entries = [e for e in items if normalize_title(e.get('canonicalTitle','')) == k]
        titles = [e['canonicalTitle'] for e in entries]
        print(f"  '{k}': {v} entries -> {titles}")
    
    # 6. What percentage of DB entries are actually reachable?
    reachable = len(set(idx.values()))
    print(f"\n--- Summary ---")
    print(f"DB entries: {len(items)}")
    print(f"Unique IDs in search index: {reachable}")
    print(f"Coverage: {reachable}/{len(items)} = {reachable/len(items)*100:.1f}%")
    
    unreachable = len(items) - reachable
    if unreachable > 0:
        unreachable_ids = set(e['id'] for e in items) - set(idx.values())
        print(f"UNREACHABLE entries: {unreachable}")
        for e in items:
            if e['id'] in unreachable_ids:
                print(f"  {e['id']:35s} title='{e.get('canonicalTitle','')[:40]}")

if __name__ == '__main__':
    main()