#!/usr/bin/env python3
"""
Build a focused database containing only entries with difficulty ratings.
This is the "rate first, metadata later" approach.

Outputs:
  data/media-index-rated.json — 1,094 anime with jpdb ratings + 255 live-action Netflix entries
  data/jpdb-difficulty-list.json — raw 1,399 jpdb entries as they appear on the difficulty list
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CANDIDATES_FILE = DATA_DIR / "candidates_with_all.json"
OUTPUT_RATED = DATA_DIR / "media-index-rated.json"

def main():
    # Load the full database
    with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    
    print(f"Full database: {len(candidates)} entries")
    
    # Group by type
    rated_anime = [c for c in candidates if c['ratings']['jpdb']['difficulty'] is not None]
    live_action = [c for c in candidates if c.get('workType', '').startswith('live-')]
    other = [c for c in candidates if c['ratings']['jpdb']['difficulty'] is None and not c.get('workType', '').startswith('live-')]
    
    print(f"  With jpdb ratings: {len(rated_anime)}")
    print(f"  Live-action (Netflix): {len(live_action)}")
    print(f"  Unrated anime (excluded): {len(other)}")
    
    # Build the focused DB: rated anime + live-action
    focused = []
    
    for c in rated_anime:
        focused.append({
            'id': c['id'],
            'workType': c['workType'],
            'canonicalTitle': c['canonicalTitle'],
            'titles': c['titles'],
            'aliases': c['aliases'],
            'externalIds': c.get('externalIds', {}),
            'ratings': {
                'jpdb': {
                    'difficulty': c['ratings']['jpdb']['difficulty'],
                    'url': c['ratings']['jpdb']['url']
                }
            }
        })
    
    for c in live_action:
        focused.append({
            'id': c['id'],
            'workType': c['workType'],
            'canonicalTitle': c['canonicalTitle'],
            'titles': c['titles'],
            'aliases': c['aliases'],
            'externalIds': c.get('externalIds', {}),
            'ratings': {
                'jpdb': {
                    'difficulty': c['ratings']['jpdb']['difficulty'],
                    'url': c['ratings']['jpdb']['url']
                }
            },
            'metadata': {
                'source': 'tmdb',
                'netflix_available': True
            }
        })
    
    # Save
    with open(OUTPUT_RATED, 'w', encoding='utf-8') as f:
        json.dump(focused, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved: {OUTPUT_RATED}")
    print(f"  Total: {len(focused)} entries ({len(rated_anime)} rated + {len(live_action)} live-action)")
    
    # Show stats
    from collections import Counter
    types = Counter(c['workType'] for c in focused)
    print(f"\nBy type:")
    for t, count in types.most_common():
        ratings = sum(1 for c in focused if c['workType'] == t and c['ratings']['jpdb']['difficulty'] is not None)
        print(f"  {t}: {count} (rated: {ratings})")

if __name__ == '__main__':
    main()