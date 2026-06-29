#!/usr/bin/env python3
"""
Fetch difficulty ratings from jpdb.io public anime difficulty list.

Downloads all 1399 entries from jpdb's anime difficulty list,
matches them to our candidates by MAL ID (primary) or normalized title (fallback),
with special handling for seasons (S2, Movie, etc.) since we can't 
distinguish seasons on Netflix/Crunchyroll anyway.

Usage:
    python tools/fetch-jpdb-ratings.py
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
CANDIDATES_FILE = PROJECT_DIR / "data" / "candidates.json"
OUTPUT_FILE = PROJECT_DIR / "data" / "candidates_with_jpdb.json"
REPORT_FILE = PROJECT_DIR / "data" / "jpdb-match-report.txt"

# ============================================================================
# Fetch
# ============================================================================

def fetch_page(offset):
    url = f"https://jpdb.io/anime-difficulty-list?offset={offset}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching offset {offset}: {e}")
        return None

def parse_difficulty_page(html):
    """Extract anime entries from the difficulty list HTML."""
    entries = []
    blocks = re.split(r'<div style="display: flex; flex-wrap: wrap;">', html)
    
    for block in blocks:
        title_m = re.search(r'<h5[^>]*>(.*?)</h5>', block)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        title = title.replace('&#39;', "'").replace('&', '&').replace('"', '"')
        
        diff_m = re.search(r'<th>Average difficulty</th>\s*<td>(\d+)/100</td>', block)
        if not diff_m:
            continue
        difficulty = int(diff_m.group(1))
        
        mal_m = re.search(r'myanimelist\.net/anime/(\d+)', block)
        mal_id = int(mal_m.group(1)) if mal_m else None
        
        jpdb_m = re.search(r'href="/anime/(\d+)/([^"]+)"', block)
        jpdb_id = jpdb_m.group(1) if jpdb_m else None
        jpdb_slug = jpdb_m.group(2) if jpdb_m else None
        
        entries.append({
            'title': title,
            'difficulty': difficulty,
            'mal_id': mal_id,
            'jpdb_id': jpdb_id,
            'jpdb_slug': jpdb_slug
        })
    
    return entries

# ============================================================================
# Normalization & Matching
# ============================================================================

def normalize(t):
    """Normalize title: lowercase, remove punctuation, compact."""
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def strip_season(title):
    """Remove season/part/movie/suffix markers to get base title.
    
    e.g. "Yuru Yuri S2" → "Yuru Yuri"
         "K-ON! S2" → "K-ON!"
         "Tamako Love Story" → "Tamako Love Story" (no change)
    """
    t = title.strip()
    # Remove: S2, Season 2, Part 2, Movie 1, etc.
    t = re.sub(r'\s+S\d+(\s|$)', ' ', t)
    t = re.sub(r'\s+Season\s+\d+(\s|$)', ' ', t)
    t = re.sub(r'\s+Part\s+\d+(\s|$)', ' ', t)
    t = re.sub(r'\s+Movie\s+\d*(\s|$)', ' ', t)
    t = re.sub(r'\s+(OVA|ONA|Special|TV|Film)(\s|$)', ' ', t)
    t = re.sub(r'[:].*$', '', t)  # Remove subtitle after colon
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def match_jpdb_to_candidates(jpdb_entries, candidates):
    """Match jpdb entries to candidates with fallback strategy."""
    
    # === Build lookups from candidates ===
    
    # By MAL ID (int → candidate)
    mal_map = {}
    for c in candidates:
        mid = c.get('externalIds', {}).get('mal')
        if mid:
            mal_map[int(mid)] = c
    
    # By normalized title (str → candidate)
    title_map = {}
    for c in candidates:
        for title in [c['canonicalTitle']] + c.get('aliases', []):
            if not title:
                continue
            key = normalize(title)
            if key:
                title_map[key] = c
        
        # Also index the base season-stripped version
        base = strip_season(c['canonicalTitle'])
        if base != c['canonicalTitle']:
            key = normalize(base)
            if key:
                title_map[key] = c
    
    # === Match ===
    stats = {'mal': 0, 'title': 0, 'title_base': 0, 'unmatched': 0}
    unmatched_detail = []
    matched_ids = set()
    
    for entry in jpdb_entries:
        candidate = None
        match_type = None
        
        # Strategy 1: MAL ID
        if entry['mal_id'] and entry['mal_id'] in mal_map:
            candidate = mal_map[entry['mal_id']]
            match_type = 'mal'
        
        # Strategy 2: Normalized title
        if not candidate:
            norm = normalize(entry['title'])
            if norm in title_map:
                candidate = title_map[norm]
                match_type = 'title'
        
        # Strategy 3: Strip season from jpdb title, then match
        if not candidate:
            base_title = strip_season(entry['title'])
            if base_title != entry['title']:
                norm = normalize(base_title)
                if norm in title_map:
                    candidate = title_map[norm]
                    match_type = 'title_base'
        
        if candidate:
            stats[match_type] = stats.get(match_type, 0) + 1
            matched_ids.add(id(candidate))
            
            # Update rating (keep higher difficulty if multiple seasons)
            existing = candidate['ratings']['jpdb']['difficulty']
            if existing is None or entry['difficulty'] > existing:
                candidate['ratings']['jpdb'] = {
                    'difficulty': entry['difficulty'],
                    'url': f"https://jpdb.io/anime/{entry['jpdb_id']}/{entry['jpdb_slug']}" if entry['jpdb_id'] and entry['jpdb_slug'] else ''
                }
                candidate['metadata']['status'] = 'has-jpdb-rating'
        else:
            stats['unmatched'] += 1
            unmatched_detail.append(entry)
    
    return stats, unmatched_detail

# ============================================================================
# Main
# ============================================================================

def main():
    print("===============================================")
    print("  Fetch jpdb anime difficulty ratings")
    print("===============================================")
    
    # Step 1: Load candidates
    if not CANDIDATES_FILE.exists():
        print(f"Error: {CANDIDATES_FILE} not found")
        sys.exit(1)
    
    with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    print(f"\nCandidates loaded: {len(candidates)}")
    print(f"  With MAL IDs: {sum(1 for c in candidates if c.get('externalIds',{}).get('mal'))}")
    
    # Step 2: Download all jpdb pages
    print("\nDownloading jpdb difficulty list pages...")
    all_entries = []
    offset = 0
    
    while True:
        html = fetch_page(offset)
        if not html:
            break
        entries = parse_difficulty_page(html)
        if not entries:
            break
        all_entries.extend(entries)
        print(f"  Page {offset//50 + 1}: {len(entries)} entries (total: {len(all_entries)})")
        offset += 50
        time.sleep(0.3)
    
    print(f"\nTotal jpdb entries: {len(all_entries)}")
    
    # Step 3: Match
    print("\nMatching jpdb entries to candidates...")
    stats, unmatched = match_jpdb_to_candidates(all_entries, candidates)
    
    # Step 4: Report
    total_matched = stats['mal'] + stats['title'] + stats['title_base']
    print(f"\n{'='*50}")
    print(f"  Matching Results")
    print(f"{'='*50}")
    print(f"  By MAL ID:        {stats['mal']}")
    print(f"  By title:         {stats['title']}")
    print(f"  By base title:    {stats['title_base']}")
    print(f"  Unmatched:        {stats['unmatched']}")
    print(f"  Total matched:    {total_matched}")
    
    # Save report
    if unmatched:
        print(f"\n  Unmatched entries ({len(unmatched)}):")
        for entry in unmatched[:20]:
            mal_str = str(entry['mal_id']) if entry['mal_id'] else '-'
            print(f"    {entry['title'][:50]:50s} | MAL: {mal_str:>7s} | diff: {entry['difficulty']}")
        if len(unmatched) > 20:
            print(f"    ... and {len(unmatched) - 20} more")
    
    # Step 5: Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    
    # Statistics
    with_ratings = sum(1 for c in candidates if c['ratings']['jpdb']['difficulty'] is not None)
    without_ratings = sum(1 for c in candidates if c['ratings']['jpdb']['difficulty'] is None)
    
    print(f"\n{'='*50}")
    print(f"  Database Statistics")
    print(f"{'='*50}")
    print(f"  With jpdb ratings:  {with_ratings}")
    print(f"  Without ratings:    {without_ratings}")
    print(f"  Total candidates:   {len(candidates)}")
    print(f"\n  Saved to: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()