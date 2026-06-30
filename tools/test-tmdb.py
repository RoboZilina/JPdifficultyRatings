#!/usr/bin/env python3
"""Test TMDB API for Netflix Japanese content."""

import json
import urllib.request

API_KEY = 'cab36d677058c3caba030776bd98d1bd'

results = {}

# Test 1: Japanese movies on Netflix (Slovak region)
results['movies_netflix'] = []
url = f'https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&with_original_language=ja&with_watch_providers=8&watch_region=SK&sort_by=popularity.desc'
resp = urllib.request.urlopen(url, timeout=15)
data = json.loads(resp.read())
results['movies_netflix'].append({'total': data['total_results'], 'pages': data['total_pages'], 'results': len(data['results'])})

# Test 2: Japanese TV on Netflix
results['tv_netflix'] = []
url = f'https://api.themoviedb.org/3/discover/tv?api_key={API_KEY}&with_original_language=ja&with_watch_providers=8&watch_region=SK&sort_by=popularity.desc'
resp = urllib.request.urlopen(url, timeout=15)
data = json.loads(resp.read())
results['tv_netflix'].append({'total': data['total_results'], 'pages': data['total_pages'], 'results': len(data['results'])})

# Test 3: Get detail for first movie
if data['results']:
    first = data['results'][0]
    results['sample_tv'] = {'name': first['name'], 'genre_ids': first.get('genre_ids', []), 'overview': first.get('overview', '')[:100]}

# Test 4: Check alternative titles endpoint
first_id = data['results'][0]['id']
url = f'https://api.themoviedb.org/3/tv/{first_id}/alternative_titles?api_key={API_KEY}'
resp = urllib.request.urlopen(url, timeout=15)
alt_data = json.loads(resp.read())
results['alt_titles_sample'] = alt_data.get('results', [])[:5]

# Test 5: Just Japanese movies (all, not just Netflix)
url = f'https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&with_original_language=ja&sort_by=popularity.desc'
resp = urllib.request.urlopen(url, timeout=15)
data = json.loads(resp.read())
results['movies_all_ja'] = {'total': data['total_results'], 'first_5': [{'title': m['title'], 'year': m.get('release_date','')[:4]} for m in data['results'][:5]]}

# Test 6: Check if we can filter OUT anime (genre 16)
url = f'https://api.themoviedb.org/3/discover/tv?api_key={API_KEY}&with_original_language=ja&with_watch_providers=8&watch_region=SK&without_genres=16&sort_by=popularity.desc'
resp = urllib.request.urlopen(url, timeout=15)
data = json.loads(resp.read())
results['tv_no_anime'] = {'total': data['total_results'], 'first_5': [{'name': t['name'], 'genres': t.get('genre_ids', [])} for t in data['results'][:5]]}

# Save results
with open(r'd:\DifficultyRatings\jp-difficulty-overlay\data\tmdb-test-results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("Tests done. Results saved.")