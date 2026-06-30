#!/usr/bin/env python3
"""
Fetch Japanese Netflix content from TMDB API.

Downloads:
- Japanese movies available on Netflix (Slovak region, 158 entries)
- Japanese TV shows available on Netflix (Slovak region, 223 entries)
- Filters OUT anime (genre 16) since we already have anime from anime-offline-database

Maps into our candidates schema with workType: "live-action-series" / "live-action-movie".

Usage:
    python tools/fetch-tmdb-netflix.py
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
CANDIDATES_FILE = PROJECT_DIR / "data" / "candidates_with_jpdb.json"
OUTPUT_FILE = PROJECT_DIR / "data" / "candidates_with_all.json"

API_KEY = 'cab36d677058c3caba030776bd98d1bd'
NETFLIX_PROVIDER_ID = 8  # TMDB watch provider ID for Netflix

def tmdb_get(path, params=''):
    """Make a GET request to TMDB API."""
    url = f'https://api.themoviedb.org/3{path}?api_key={API_KEY}&{params}'
    req = urllib.request.Request(url, headers={'User-Agent': 'JP-Difficulty-Overlay/1.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  Error {path}: HTTP {e.code}")
        return None

def fetch_all_pages(media_type, params):
    """Fetch all pages of discover results for a given media type and params."""
    all_results = []
    page = 1
    
    while True:
        data = tmdb_get(f'/discover/{media_type}', f'page={page}&{params}')
        if not data or not data.get('results'):
            break
        
        results = data['results']
        all_results.extend(results)
        
        total_pages = data.get('total_pages', 1)
        print(f"  Page {page}/{total_pages}: {len(results)} results (total: {len(all_results)})")
        
        if page >= total_pages or page >= 10:  # Max 10 pages = 200 results per type
            break
        
        page += 1
        time.sleep(0.25)  # Be polite to API
    
    return all_results

def get_alternative_titles(media_type, tmdb_id):
    """Get alternative titles for a movie or TV show."""
    data = tmdb_get(f'/{media_type}/{tmdb_id}/alternative_titles')
    if not data:
        return []
    
    titles = data.get('titles', data.get('results', []))
    return titles

def get_external_ids(media_type, tmdb_id):
    """Get external IDs (IMDB, etc.) for a movie or TV show."""
    data = tmdb_get(f'/{media_type}/{tmdb_id}/external_ids')
    if not data:
        return {}
    return data

def map_media_type(tmdb_type, genre_ids):
    """Map TMDB media type to our workType values."""
    # Check if it's anime (genre 16) — we're filtering these out, but just in case
    if 16 in (genre_ids or []):
        # Determine anime sub-type
        return 'anime-series' if tmdb_type == 'tv' else 'anime-movie'
    return 'live-action-series' if tmdb_type == 'tv' else 'live-action-movie'

def extract_titles(tmdb_entry, media_type):
    """Extract titles from a TMDB entry."""
    # TMDB title field name differs for movies vs TV
    main_title = tmdb_entry.get('title') or tmdb_entry.get('name', '')
    
    # Original title (usually Japanese)
    original_title = tmdb_entry.get('original_title') or tmdb_entry.get('original_name', '') or ''
    
    titles = {
        'en': main_title,
        'ja': original_title if original_title and any(
            ord(c) > 0x3000 for c in original_title
        ) else '',
        'romaji': '' if original_title and any(
            ord(c) > 0x3000 for c in original_title
        ) else original_title
    }
    
    return titles, main_title

def main():
    print("===============================================")
    print("  Fetch Japanese Netflix content from TMDB")
    print("===============================================")
    
    # Step 1: Load existing candidates
    if CANDIDATES_FILE.exists():
        with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        print(f"\nExisting candidates loaded: {len(candidates)}")
    else:
        candidates = []
        print(f"\nNo existing candidates found, starting fresh")
    
    # Track existing TMDB IDs to avoid duplicates
    existing_tmdb_ids = set()
    existing_imdb_ids = set()
    existing_titles = set()
    for c in candidates:
        eid = c.get('externalIds', {})
        if eid.get('tmdb'):
            for tid in (eid['tmdb'] if isinstance(eid['tmdb'], list) else [eid['tmdb']]):
                existing_tmdb_ids.add(int(tid))
        if eid.get('imdb'):
            existing_imdb_ids.add(eid['imdb'])
        existing_titles.add(c.get('canonicalTitle', '').lower().strip())
    
    print(f"  Existing TMDB IDs: {len(existing_tmdb_ids)}")
    print(f"  Existing titles indexed: {len(existing_titles)}")
    
    # Step 2: Fetch Japanese movies on Netflix (without anime)
    print("\nFetching Japanese movies on Netflix (no anime)...")
    movie_params = (
        f'with_original_language=ja'
        f'&with_watch_providers={NETFLIX_PROVIDER_ID}'
        f'&watch_region=SK'
        f'&without_genres=16'  # Exclude anime
        f'&sort_by=popularity.desc'
        f'&include_adult=false'
    )
    movies = fetch_all_pages('movie', movie_params)
    print(f"Total movies: {len(movies)}")
    
    # Step 3: Fetch Japanese TV on Netflix (without anime)
    print("\nFetching Japanese TV on Netflix (no anime)...")
    tv_params = (
        f'with_original_language=ja'
        f'&with_watch_providers={NETFLIX_PROVIDER_ID}'
        f'&watch_region=SK'
        f'&without_genres=16'  # Exclude anime
        f'&sort_by=popularity.desc'
        f'&include_adult=false'
    )
    tv_shows = fetch_all_pages('tv', tv_params)
    print(f"Total TV shows: {len(tv_shows)}")
    
    # Step 4: Process and add new entries
    print("\nProcessing and adding new entries...")
    new_count = 0
    skipped_duplicate = 0
    
    # Process both movies and TV shows
    for media_type, entries in [('movie', movies), ('tv', tv_shows)]:
        for entry in entries:
            tmdb_id = entry['id']
            
            # Skip if we already have this TMDB ID
            if tmdb_id in existing_tmdb_ids:
                skipped_duplicate += 1
                continue
            
            titles, main_title = extract_titles(entry, media_type)
            
            # Skip if title already exists (fuzzy deduplication)
            if main_title.lower().strip() in existing_titles:
                skipped_duplicate += 1
                continue
            
            # Get alternative titles
            alt_titles = get_alternative_titles(media_type, tmdb_id)
            time.sleep(0.1)
            
            # Extract alternate titles as aliases
            aliases = []
            jp_title_found = titles['ja'] != ''
            for alt in alt_titles:
                t = alt.get('title', '') if isinstance(alt, dict) else ''
                if not t or t == main_title:
                    continue
                lower = t.lower().strip()
                if lower and lower not in aliases:
                    aliases.append(lower)
                # Check if alt title gives us Japanese title
                if not jp_title_found and any(ord(c) > 0x3000 for c in t):
                    titles['ja'] = t
                    jp_title_found = True
            
            # Get external IDs
            ext_ids = get_external_ids(media_type, tmdb_id)
            time.sleep(0.1)
            
            external_ids = {
                'tmdb': tmdb_id,
                'imdb': ext_ids.get('imdb_id', ''),
            }
            
            # Filter out None values
            external_ids = {k: v for k, v in external_ids.items() if v}
            
            genre_ids = entry.get('genre_ids', [])
            
            entry_data = {
                'id': f'tmdb-{media_type}-{tmdb_id}',
                'workType': map_media_type(media_type, entry.get('genre_ids', [])),
                'canonicalTitle': main_title,
                'titles': titles,
                'aliases': aliases[:20],  # Keep top 20 aliases
                'externalIds': external_ids,
                'platformAliases': {
                    'netflix': [],
                    'crunchyroll': []
                },
                'ratings': {
                    'learnnatively': {
                        'level': None,
                        'jlptApprox': '',
                        'url': ''
                    },
                    'jpdb': {
                        'difficulty': None,
                        'url': ''
                    }
                },
                'metadata': {
                    'source': 'tmdb',
                    'netflix_available': True,
                    'overview': entry.get('overview', '')[:200] if entry.get('overview') else '',
                    'release_year': (entry.get('release_date') or entry.get('first_air_date') or '')[:4],
                    'genre_ids': genre_ids
                }
            }
            
            candidates.append(entry_data)
            new_count += 1
            
            # Track to avoid duplicates
            existing_tmdb_ids.add(tmdb_id)
            existing_titles.add(main_title.lower().strip())
            
            if new_count % 50 == 0:
                print(f"  Added {new_count} entries so far...")
    
    # Step 5: Report
    print(f"\n{'='*50}")
    print(f"  Results")
    print(f"{'='*50}")
    print(f"  New entries added:         {new_count}")
    print(f"  Skipped (duplicate):       {skipped_duplicate}")
    print(f"  Total candidates now:      {len(candidates)}")
    
    # Count by type
    from collections import Counter
    type_counts = Counter(c['workType'] for c in candidates)
    print(f"\n  By type:")
    for t, count in type_counts.most_common():
        print(f"    {t}: {count}")
    
    # Step 6: Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Saved to: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()