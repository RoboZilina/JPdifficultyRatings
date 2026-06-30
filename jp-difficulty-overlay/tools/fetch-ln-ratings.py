#!/usr/bin/env python3
"""
Fetch difficulty ratings from LearnNatively.

Uses the public API endpoints that return items with rating levels.
No authentication required.

Two approaches:
1. Autocomplete API (search by title - works, but one title at a time)
2. Search-page API provides config. We'll use the load-more endpoint.

LearnNatively level mapping:
  N5:   L0-12   (beginner)
  N4:   L13-19  (elementary)
  N3:   L20-26  (intermediate)
  N2:   L27-33  (upper intermediate)
  N1:   L34-40  (advanced)
  N1+:  L41+    (very advanced)

Usage:
    python tools/fetch-ln-ratings.py
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

API_BASE = "https://learnnatively.com"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_url(url):
    """Fetch a URL and return parsed JSON."""
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode('utf-8'))

def main():
    print("=" * 60)
    print("  Fetch LearnNatively Ratings")
    print("=" * 60)
    
    # =====================
    # Step 1: Try the search-page API to find the load-more endpoint
    # =====================
    print("\n1. Loading search page config...")
    config = fetch_url(f"{API_BASE}/api/search-page/jpn/videos/")
    
    # Check the urls config for item listing endpoints
    urls = config.get('urls', {})
    print(f"   URL config keys: {list(urls.keys())[:10]}")
    
    # The actual search endpoint for items (from the page JS)
    search_url = urls.get('itemSearch', urls.get('loadMore', urls.get('search', None)))
    if search_url:
        print(f"   Found search URL: {search_url}")
    
    # =====================
    # Step 2: Use search-page API's initial data if any
    # =====================
    items = []
    
    # Check if initialState has pre-loaded items
    state = config.get('initialState', {})
    for key in state:
        val = state[key]
        if isinstance(val, list):
            print(f"   initial state: {key} = {len(val)} items")
            items.extend(val)
    
    # =====================
    # Step 3: Test the autocomplete approach
    # =====================
    print("\n2. Testing autocomplete API...")
    
    # Search a few known titles
    tests = [
        ("bocchi", "video"),
        ("bocchi", "book"),
        ("jujutsu", "video"),
        ("attack on titan", "video"),
        ("alice in borderland", "video"),
        ("terrace house", "video"),
    ]
    
    all_results = []
    
    for query, lib_type in tests:
        url = f"{API_BASE}/api/autocomplete-api/?q={urllib.request.quote(query)}&libraryType={lib_type}"
        try:
            data = fetch_url(url)
            if isinstance(data, list):
                for item in data:
                    all_results.append({
                        'query': query,
                        'type': lib_type,
                        'raw': item
                    })
                print(f"   '{query}' ({lib_type}): {len(data)} results")
        except Exception as e:
            print(f"   '{query}' ({lib_type}): error - {e}")
        time.sleep(0.3)
    
    # =====================
    # Step 4: Save test results
    # =====================
    print(f"\n3. Saved {len(all_results)} test results")
    with open(DATA_DIR / "ln-all-test-results.json", 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # =====================
    # Step 5: Show what we found
    # =====================
    for item in all_results:
        raw = item['raw']
        if isinstance(raw, dict):
            # Handle different response structures
            payload = raw.get('item') or raw.get('series') or raw
            title = payload.get('title', 'N/A')
            rating = payload.get('rating', {})
            if isinstance(rating, dict) and 'lvl' in rating:
                print(f"\n   {item['query']} -> {title[:40]}")
                print(f"      Rating level: L{rating['lvl']}")
                print(f"      URL: {payload.get('url', 'N/A')}")
                
                # Check for external IDs
                mal_id = payload.get('mal_id')
                tmdb_id = payload.get('tmdb_id')
                if mal_id:
                    print(f"      MAL ID: {mal_id}")
                if tmdb_id:
                    print(f"      TMDB ID: {tmdb_id}")
                break  # Just show one example
    
    print("\nDone!")

if __name__ == '__main__':
    main()