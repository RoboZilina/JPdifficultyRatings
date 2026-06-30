#!/usr/bin/env python3
"""
Explore LearnNatively API endpoints to find the one that lists items with ratings.
"""

import json
import urllib.request
import time

BASE = "https://learnnatively.com"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def try_url(path, params=''):
    url = f"{BASE}{path}?{params}" if params else f"{BASE}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read()
        try:
            return json.loads(data)
        except:
            return f"Non-JSON: {len(data)} bytes"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"Error: {e}"

# Hypothetical endpoints to test
endpoints = [
    # Known working
    "/api/search-page/jpn/videos/",
    "/api/autocomplete-api/?q=a&libraryType=video",
    
    # Guesses for item listing
    "/api/video-list/",
    "/api/video-list/jpn/",
    "/api/video-list/jpn/?page=1",
    "/api/load-more-video/",
    "/api/load-more-video/jpn/?page=1",
    "/api/list-video/jpn/",
    "/api/list-video/jpn/?page=1",
    "/api/video-search/jpn/",
    "/api/video-search/jpn/?page=1",
    "/api/videos/jpn/",
    "/api/videos/jpn/?page=1",
    
    # From search-page API structure
    "/api/search-api/jpn/videos/?page=1",
    "/api/search/jpn/videos/?page=1",
    "/api/search-item/jpn/videos/?page=1",
    "/api/search-items/jpn/videos/?page=1",
    
    # browse variations
    "/api/browse/jpn/videos/?page=1",
    "/api/browse-items/jpn/videos/?page=1",
    
    # with libraryType
    "/api/video-list/?libraryType=video&language=jpn&page=1",
    "/api/list-items/?libraryType=video&language=jpn&page=1",
    "/api/load-items/?libraryType=video&language=jpn&page=1",
    
    # Django REST-ish patterns
    "/api/items/",
    "/api/items/?libraryType=video&language=jpn&page=1",
    "/api/video/",
    "/api/video/?libraryType=video&language=jpn&page=1",
]

results = []
for ep in endpoints:
    time.sleep(0.2)
    result = try_url(ep)
    summary = f"{result[:60]}" if isinstance(result, str) else f"JSON, keys={list(result.keys())[:10] if isinstance(result, dict) else 'list'}"
    results.append(f"{result:>12s} | {ep}")
    print(f"{result if isinstance(result, str) and 'HTTP' in result else 'OK':>12s} | {ep}")

with open('d:/DifficultyRatings/jp-difficulty-overlay/data/ln-endpoint-test.txt', 'w') as f:
    f.write('\n'.join(results))
print(f"\nDone. {sum(1 for r in results if 'HTTP 200' in r)} working endpoints")