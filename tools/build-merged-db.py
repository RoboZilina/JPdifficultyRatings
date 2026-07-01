#!/usr/bin/env python3
"""
Build unified media index with rich title aliases for cross-platform lookup.
Sources:
- candidates_with_all.json (anime-offline + jpdb ratings + TMDB Netflix)
- ln-video-catalog.json (LearnNatively video difficulty L-levels)

Strategy: Build from LN catalog, cross-reference with candidates for jpdb scores and rich aliases.
Output: media-index-merged.json (for the extension). Source files preserved.
"""

import json, re, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

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
    # Reverse index: normalized candidate title → candidate (for LN→candidate matching)
    # Indexes canonicalTitle, en, ja, romaji, and aliases
    rev_idx = {}
    for c in candidates:
        cid = c.get('id', '')
        if not cid: continue
        titles_list = [c.get('canonicalTitle','')]
        t = c.get('titles', {})
        if isinstance(t, dict):
            for k in ('en', 'ja_jp', 'ja', 'romaji'):
                if t.get(k): titles_list.append(t[k])
        if isinstance(c.get('aliases'), list):
            titles_list.extend(c['aliases'])
        for t in titles_list:
            n = normalize(t)
            if n and n not in rev_idx:
                rev_idx[n] = c
    print(f"  {len(candidate_index)} unique title forms indexed, {len(rev_idx)} reverse index entries")
    
    print("\nCross-referencing LN entries with candidates...")
    
    matched = 0
    with_both = 0
    ln_only = 0
    unified = []
    matched_candidate_ids = set()  # Track which candidates were matched via LN
    unmatched_entries = []  # NEW: Track unmatched LN entries
    
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
        
        # Try to match (LN title → candidate titles)
        matched_candidate = None
        matched_idx = None
        for v in ln_variants:
            if v and v in candidate_index:
                matched_idx = candidate_index[v][0]
                matched_candidate = candidates[matched_idx]
                break
        
        # If no match, try reverse: candidate titles → LN title (try all LN variants)
        if not matched_candidate:
            for v in ln_variants:
                if v and v in rev_idx:
                    matched_candidate = rev_idx[v]
                    break
        
        if matched_candidate:
            # Avoid matching generic LN titles to overly-specific spin-offs
            ln_simple = (ln_english or ln_title).lower()
            cand_simple = matched_candidate.get('canonicalTitle', '').lower()
            
            # If LN title is short but candidate is very specific, look for a better match
            if len(ln_simple) < 25 and len(cand_simple) > len(ln_simple) + 10:
                norm_ln = normalize(ln_simple)
                alternatives = [c for c in candidates 
                              if normalize(c.get('canonicalTitle', '')) == norm_ln]
                if alternatives:
                    # Prefer the candidate with the shortest canonical title (likely main series)
                    best = min(alternatives, key=lambda c: len(c.get('canonicalTitle', '')))
                    if best['id'] != matched_candidate['id']:
                        print(f"    Corrected: [{matched_candidate.get('canonicalTitle','')[:40]}] -> [{best.get('canonicalTitle','')[:40]}]")
                        matched_candidate = best
            
            # Matched to anime-offline-database: use candidate titles
            c = matched_candidate
            titles_dict = {
                'en': c.get('titles', {}).get('en', '') if isinstance(c.get('titles'), dict) else '',
                'ja': c.get('titles', {}).get('ja_jp', '') or c.get('titles', {}).get('ja', '') or '',
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
            if candidate_id:
                matched_candidate_ids.add(candidate_id)
            matched += 1
            if ln_lvl is not None:
                with_both += 1
        else:
            # Not matched to candidate - build titles from LN data
            titles_dict = {
                'en': ln_english or '',
                'ja': ln_title or '',
                'romaji': '',
            }
            aliases = []
            jpdb_score = None
            candidate_id = None
            ln_only += 1
            # Track unmatched entries
            unmatched_entries.append({
                "id": ln_id,
                "title": ln_title,
                "english": ln_english,
                "type": ln_type,
                "level": ln_lvl,
                "url": ln_url,
            })
        
        # Collect all unique title forms for searchability
        all_titles = list(titles_dict.values()) + [ln_title, ln_english]
        all_titles = [t for t in all_titles if t]
        if aliases:
            all_titles.extend(aliases)
        entry_id = f'ln-{ln_id}'
        if candidate_id:
            entry_id = f'ao-{candidate_id}'
        
        # Build aliases list: all unique title forms
        canonical = titles_dict['en'] or titles_dict['ja'] or titles_dict['romaji'] or ''
        aliases_set = set()
        for t in [titles_dict['en'], titles_dict['ja'], titles_dict['romaji'], ln_title, ln_english]:
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
    
    # ===== Second pass: add unmatched candidates that have jpdb scores =====
    candidate_only = 0
    for c in candidates:
        cid = c.get('id', '')
        if not cid or cid in matched_candidate_ids:
            continue
        ratings = c.get('ratings', {})
        jpdb_score = None
        if isinstance(ratings, dict) and 'jpdb' in ratings:
            jpdb_score = ratings['jpdb'].get('difficulty') if isinstance(ratings['jpdb'], dict) else None
        if jpdb_score is None and c.get('difficulty') is not None:
            jpdb_score = c['difficulty']
        if jpdb_score is None:
            continue
        
        titles_dict = {
            'en': c.get('titles', {}).get('en', '') if isinstance(c.get('titles'), dict) else '',
            'ja': c.get('titles', {}).get('ja_jp', '') or c.get('titles', {}).get('ja', '') or '',
            'romaji': c.get('titles', {}).get('romaji', '') if isinstance(c.get('titles'), dict) else '',
        }
        aliases = c.get('aliases', []) or []
        canonical = titles_dict['en'] or titles_dict['ja'] or titles_dict['romaji'] or c.get('canonicalTitle', '') or ''
        
        aliases_set = set()
        for t in [titles_dict['en'], titles_dict['ja'], titles_dict['romaji']]:
            if t and t != canonical: aliases_set.add(t)
        for a in aliases:
            if a and a != canonical: aliases_set.add(a)
        
        jpdb_url = None
        if isinstance(ratings, dict) and 'jpdb' in ratings and isinstance(ratings['jpdb'], dict):
            jpdb_url = ratings['jpdb'].get('url')
        
        unified.append({
            'id': f'ao-{cid}',
            'canonicalTitle': canonical,
            'aliases': sorted(aliases_set) if aliases_set else [],
            'ratings': {
                'learnnatively': {'level': None, 'url': None},
                'jpdb': {'difficulty': jpdb_score, 'url': jpdb_url or None},
            },
        })
        candidate_only += 1
    
    print(f"\nResults:")
    print(f"  Total LN entries:       {len(ln_entries)}")
    print(f"  Matched to candidate:   {matched}")
    print(f"  With both ratings:      {with_both}")
    print(f"  LN only (no jpdb):      {ln_only}")
    print(f"  Candidate-only (jpdb):  {candidate_only}")
    print(f"  Total unified:          {len(unified)}")
    
    # Save merged DB
    outfile = DATA_DIR / 'media-index-merged.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(unified, f, indent=2, ensure_ascii=False)
    
    # NEW: Save comprehensive report with unmatched samples
    # Sort unmatched by level (highest first) for prioritization
    unmatched_by_level = sorted(unmatched_entries, key=lambda x: x.get('level') or 0, reverse=True)
    unmatched_samples = unmatched_by_level[:20]  # Top 20 hardest titles
    
    report = {
        'total_ln': len(ln_entries),
        'total_candidates': len(candidates),
        'matched': matched,
        'with_both_ratings': with_both,
        'ln_only_no_jpdb': ln_only,
        'total_unified': len(unified),
        'total_unmatched': len(unmatched_entries),
        'unmatched_samples': unmatched_samples,  # NEW: Top 20 for manual review
        'unmatched_by_type': {},  # NEW: Breakdown by mediaType
    }
    
    # NEW: Count unmatched by type
    for entry in unmatched_entries:
        mtype = entry.get('type', 'unknown')
        report['unmatched_by_type'][mtype] = report['unmatched_by_type'].get(mtype, 0) + 1
    
    with open(DATA_DIR / 'merge-report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nSaved: {outfile}")
    print(f"Saved: {DATA_DIR / 'merge-report.json'}")
    
    # NEW: Print unmatched summary
    print("\nUnmatched samples (top 20 by difficulty level):")
    for u in unmatched_samples:
        level_str = f"L{u['level']}" if u['level'] is not None else "??"
        title = (u['english'] or u['title'])[:50]
        mtype = u['type'] or '?'
        print(f"  [{level_str:>4}] [{mtype:>12}] {title}")
    
    print("\nUnmatched by type:")
    for mtype, count in sorted(report['unmatched_by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {mtype:20s}: {count:4d}")
    
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