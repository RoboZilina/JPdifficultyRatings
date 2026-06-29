#!/usr/bin/env python3
"""
Investigate and fix unmatched jpdb entries.

The script:
1. Re-fetches all jpdb difficulty list pages
2. Shows which entries are unmatched and why
3. Attempts smarter matching (by normalized title without stop words, by adding more aliases)
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
CANDIDATES_FILE = PROJECT_DIR / "data" / "candidates_with_jpdb.json"
OUTPUT_FILE = PROJECT_DIR / "data" / "candidates_with_jpdb_v2.json"
REPORT_FILE = PROJECT_DIR / "data" / "jpdb-unmatched-report.txt"

def fetch_page(offset):
    url = f"https://jpdb.io/anime-difficulty-list?offset={offset}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching offset {offset}: {e}")
        return None

def parse_all_pages():
    """Fetch all pages and return all jpdb entries."""
    all_entries = []
    offset = 0
    while True:
        html = fetch_page(offset)
        if not html:
            break
        blocks = re.split(r'<div style="display: flex; flex-wrap: wrap;">', html)
        page_entries = []
        for block in blocks:
            title_m = re.search(r'<h5[^>]*>(.*?)</h5>', block)
            if not title_m:
                continue
            title = title_m.group(1)
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
            
            page_entries.append({
                'title': title,
                'difficulty': difficulty,
                'mal_id': mal_id,
                'jpdb_id': jpdb_id,
                'jpdb_slug': jpdb_slug
            })
        
        if not page_entries:
            break
        
        all_entries.extend(page_entries)
        print(f"  Offset {offset}: {len(page_entries)} entries")
        offset += 50
        time.sleep(0.3)
    
    return all_entries

def normalize(t):
    """Normalize title for comparison: lowercase, remove non-alphanumeric, remove common words."""
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # Remove season markers, common words that vary
    for word in ['season', 's', 'tv', 'movie', 'film', 'the', 'a', 'an', 'and', 'of', 'part', 'ova', 'ona', 'special']:
        t = re.sub(r'\b' + word + r'\b', ' ', t)
    t = re.sub(r"\s+", "", t)  # compact
    return t

def build_lookups(candidates):
    """Build MAL ID and normalized title lookups."""
    mal_map = {}
    title_map = {}
    
    for c in candidates:
        mid = c.get('externalIds', {}).get('mal')
        if mid:
            mal_map[mid] = c
        
        # Add canonical title
        key = normalize(c['canonicalTitle'])
        title_map[key] = c
        
        # Add all aliases
        for alias in c.get('aliases', []):
            key = normalize(alias)
            title_map[key] = c
    
    return mal_map, title_map

def main():
    print("===============================================")
    print("  Investigate unmatched jpdb entries")
    print("===============================================")
    
    # Step 1: Load candidates
    with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    print(f"\nCandidates loaded: {len(candidates)}")
    
    # Step 2: Re-fetch all jpdb entries
    print("\nFetching all jpdb difficulty list pages...")
    jpdb_entries = parse_all_pages()
    print(f"Total jpdb entries: {len(jpdb_entries)}")
    
    # Step 3: Build lookups
    mal_map, title_map = build_lookups(candidates)
    print(f"MAL IDs indexed: {len(mal_map)}")
    print(f"Title keys indexed: {len(title_map)}")
    
    # Step 4: Match and report
    matched = 0
    by_mal = 0
    by_title = 0
    by_title_v2 = 0
    unmatched = []
    newly_matched_v2 = []
    
    for entry in jpdb_entries:
        candidate = None
        match_type = None
        
        # Try MAL ID
        if entry['mal_id'] and entry['mal_id'] in mal_map:
            candidate = mal_map[entry['mal_id']]
            match_type = 'mal'
            by_mal += 1
        else:
            # Try normalized title
            norm = normalize(entry['title'])
            if norm in title_map:
                candidate = title_map[norm]
                match_type = 'title_v1'
                by_title += 1
            else:
                # Show what we tried for debugging
                unmatched.append(entry)
        
        if candidate and match_type:
            # Update rating (might be already done, but ensure consistency)
            candidate['ratings']['jpdb'] = {
                'difficulty': entry['difficulty'],
                'url': f"https://jpdb.io/anime/{entry['jpdb_id']}/{entry['jpdb_slug']}" if entry['jpdb_id'] and entry['jpdb_slug'] else ''
            }
            candidate['metadata']['status'] = 'has-jpdb-rating'
            matched += 1
    
    # Step 5: Report on unmatched entries
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write(f"Unmatched jpdb entries: {len(unmatched)}\n\n")
        
        # Group by possible reasons
        no_mal = [e for e in unmatched if not e['mal_id']]
        has_mal = [e for e in unmatched if e['mal_id']]
        
        report.write(f"  No MAL ID: {len(no_mal)}\n")
        report.write(f"  Has MAL ID but not in candidates: {len(has_mal)}\n\n")
        
        report.write("=== Unmatched entries ===\n\n")
        for entry in unmatched:
            norm = normalize(entry['title'])
            report.write(f"Title: {entry['title']}\n")
            report.write(f"  MAL ID: {entry['mal_id']}\n")
            report.write(f"  Difficulty: {entry['difficulty']}\n")
            report.write(f"  Normalized: {norm}\n")
            
            # Show closest match from candidates
            candidates_norm = {k: v for k, v in title_map.items()}
            closest = [k for k in candidates_norm.keys() if len(k) > 3 and (k in norm or norm in k)]
            if closest:
                report.write(f"  Close title matches: {closest[:5]}\n")
            report.write("\n")
    
    print(f"\n===== Results =====")
    print(f"  Total jpdb entries: {len(jpdb_entries)}")
    print(f"  Matched by MAL ID:  {by_mal}")
    print(f"  Matched by title:   {by_title}")
    print(f"  Unmatched:          {len(unmatched)}")
    print(f"  Of which no MAL ID: {len(no_mal)}")
    print(f"  Of which has MAL ID: {len(has_mal)}")
    print(f"\nReport saved: {REPORT_FILE}")
    
    # If we found improvements, save updated file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    
    with_ratings = sum(1 for c in candidates if c['ratings']['jpdb']['difficulty'] is not None)
    print(f"\nUpdated file: {OUTPUT_FILE}")
    print(f"Candidates with jpdb ratings: {with_ratings} / {len(candidates)}")

if __name__ == '__main__':
    main()