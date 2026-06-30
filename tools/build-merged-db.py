#!/usr/bin/env python3
"""
Build unified media index with rich title aliases for cross-platform lookup.
Sources:
- candidates_with_all.json (anime-offline + jpdb ratings + TMDB Netflix)
- ln-video-catalog.json (LearnNatively video difficulty L-levels)

Strategy: Build from LN catalog, cross-reference with candidates for jpdb scores and rich aliases.
Output: media-index-merged.json (for the extension). Source files preserved.
"""

import json, re
from pathlib import Path

DATA_DIR = Path('d:/DifficultyRatings/jp-difficulty-overlay/data')

def normalize(s):
    """Lowercase, strip special chars, collapse whitespace. Keeps Japanese chars."""
    if not s: return ''
    s = s.lower()
    s = re.sub(r'[^\w\s\u3000-\u9fff\uff00-\uffef\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def title_variants(title):
    """Generate search variants from a title for matching."""
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

def build_candidate_index(candidates):
    """Build lookup of all title forms → candidate index for fast cross-referencing."""
    index = {}
    for idx, entry in enumerate(candidates):
        titles_to_add = set()
        # Get all known titles
        if entry.get('canonicalTitle'):
            titles_to_add.add(entry['canonicalTitle'])
        titles = entry.get('titles', {})
        if isinstance(titles, dict):
            for key in ['en', 'ja_jp', 'ja', 'romaji']:
                if titles.get(key):
                    titles_to_add.add(titles[key])
        for alias in entry.get('aliases', []):
            if alias:
                titles_to_add.add(alias)
        
        for t in titles_to_add:
            for v in title_variants(t):
                if v:
                    if v not in index:
                        index[v] = []
                    index[v].append(idx)
    return index

def main():
    print("Loading LN video catalog...")
    ln_entries = json.load(open(DATA_DIR / 'ln-video-catalog.json', 'r', encoding='utf-8'))
    print(f"  {len(ln_entries)} LN entries")
    
    print("Loading candidate database (anime-offline + jpdb)...")
    candidates = json.load(open(DATA_DIR / 'candidates_with_all.json', 'r', encoding='utf-8'))
    print(f"  {len(candidates)} candidate entries")
    
    print("\nBuilding candidate title index...")
    candidate_index = build_candidate_index(candidates)
    print(f"  {len(candidate_index)} unique title forms indexed")
    
    print("\nCross-referencing LN entries with candidates...")
    
    matched = 0
    with_both = 0
    ln_only = 0
    unified = []
    
    for ln_entry in ln_entries:
        ln_id = str(ln_entry.get('id', ''))
        if not ln_id:
            continue
        
        ln_title = ln_entry.get('title', '')
        ln_english = ln_entry.get('englishTitle', '')
        ln_lvl = ln_entry.get('lvl')
        ln_type = ln_entry.get('mediaType', '')
        ln_url = ln_entry.get('url', '')
        
        # Generate LN title variants
        ln_variants = set()
        for t in [ln_title, ln_english]:
            ln_variants.update(title_variants(t))
        
        # Try to match
        matched_candidate = None
        matched_idx = None
        for v in ln_variants:
            if v and v in candidate_index:
                matched_idx = candidate_index[v][0]
                matched_candidate = candidates[matched_idx]
                break
        
        titles_dict = {'en': '', 'jp': '', 'romaji': ''}
        aliases = []
        jpdb_score = None
        candidate_id = None
        
        if matched_candidate:
            c = matched_candidate
            titles_dict = {
                'en': c.get('titles', {}).get('en', '') if isinstance(c.get('titles'), dict) else '',
                'jp': c.get('titles', {}).get('ja_jp', '') or c.get('titles', {}).get('ja', '') or '',
                'romaji': c.get('titles', {}).get('romaji', '') if isinstance(c.get('titles'), dict) else '',
            }
            aliases = c.get('aliases', []) or []
            
            # Get jpdb score
            ratings = c.get('ratings', {})
            if isinstance(ratings, dict) and 'jpdb' in ratings:
                jpdb_score = ratings['jpdb'].get('difficulty') if isinstance(ratings['jpdb'], dict) else None
            if jpdb_score is None and c.get('difficulty') is not None:
                jpdb_score = c['difficulty']
            
            candidate_id = c.get('id', '')
            matched += 1
            if ln_lvl is not None:
                with_both += 1
        
        if not matched_candidate:
            ln_only += 1
        
        # Collect all unique title forms for searchability
        all_titles = list(titles_dict.values()) + [ln_title, ln_english]
        all_titles = [t for t in all_titles if t]
        if aliases:
            all_titles.extend(aliases)
        
        entry_id = f'ln-{ln_id}'
        if candidate_id:
            entry_id = f'ao-{candidate_id}'
        
        # Build aliases list: all unique title forms
        canonical = titles_dict['en'] or ln_english or titles_dict['romaji'] or titles_dict['jp'] or ''
        aliases_set = set()
        for t in [titles_dict['en'], titles_dict['jp'], titles_dict['romaji'], ln_title, ln_english]:
            if t and t != canonical:
                aliases_set.add(t)
        for a in aliases:
            if a and a != canonical:
                aliases_set.add(a)
        
        jpdb_url = None
        if matched_candidate:
            r = matched_candidate.get('ratings', {})
            if isinstance(r, dict) and 'jpdb' in r and isinstance(r['jpdb'], dict):
                jpdb_url = r['jpdb'].get('url')
        
        unified.append({
            'id': entry_id,
            'canonicalTitle': canonical,
            'aliases': sorted(aliases_set) if aliases_set else [],
            'ratings': {
                'learnnatively': {
                    'level': ln_lvl,
                    'url': f"https://learnnatively.com{ln_url}" if ln_url else None,
                },
                'jpdb': {
                    'difficulty': jpdb_score,
                    'url': jpdb_url or None,
                },
            },
        })
    
    print(f"\nResults:")
    print(f"  Total LN entries:     {len(ln_entries)}")
    print(f"  Matched to candidate: {matched}")
    print(f"  With both ratings:    {with_both}")
    print(f"  LN only (no jpdb):    {ln_only}")
    print(f"  Total unified:        {len(unified)}")
    
    # Save
    outfile = DATA_DIR / 'media-index-merged.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(unified, f, indent=2, ensure_ascii=False)
    
    report = {
        'total_ln': len(ln_entries),
        'total_candidates': len(candidates),
        'matched': matched,
        'with_both_ratings': with_both,
        'ln_only_no_jpdb': ln_only,
        'total_unified': len(unified),
    }
    with open(DATA_DIR / 'merge-report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nSaved: {outfile}")
    print(f"Saved: {DATA_DIR / 'merge-report.json'}")
    
    # Samples
    print("\nSample entries (first 5 with both ratings):")
    count = 0
    for u in unified:
        if count >= 5: break
        ln_rating = u['ratings']['learnnatively']
        jpdb_rating = u['ratings']['jpdb']
        if jpdb_rating and jpdb_rating['difficulty'] is not None and ln_rating and ln_rating['level'] is not None:
            t = u['canonicalTitle'][:40]
            print(f"  [BOTH] {t:40s} | jpdb={jpdb_rating['difficulty']:5.1f} | LN=L{ln_rating['level']}")
            count += 1
    print("Sample entries (first 3 LN-only):")
    count = 0
    for u in unified:
        if count >= 3: break
        ln_rating = u['ratings']['learnnatively']
        jpdb_rating = u['ratings']['jpdb']
        if ln_rating and ln_rating['level'] is not None and (not jpdb_rating or jpdb_rating['difficulty'] is None):
            t = u['canonicalTitle'][:40]
            print(f"  [LN]   {t:40s} | LN=L{ln_rating['level']}")
            count += 1

if __name__ == '__main__':
    main()