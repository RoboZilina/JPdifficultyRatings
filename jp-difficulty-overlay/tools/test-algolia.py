#!/usr/bin/env python3
"""Test LearnNatively Algolia API + jpdb API access."""

import urllib.request
import json
import re
import sys

def test_learnnatively_algolia():
    """Test Algolia search API on LearnNatively"""
    print("=== LearnNatively Algolia API ===")
    
    # These are the keys suggested from the user's research
    headers = {
        'Content-Type': 'application/json',
        'x-algolia-api-key': '0bc1508db83cf4b1da90a079b76c8135',
        'x-algolia-application-id': '0K186L6U6Z',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    # Try standard Algolia search endpoint
    url = 'https://0K186L6U6Z-dsn.algolia.net/1/indexes/*/query'
    payload = {"params": "query=bocchi+the+rock&hitsPerPage=3"}
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        hits = body.get('hits', [])
        print(f"Status: {resp.status}, Hits: {len(hits)}")
        for h in hits[:2]:
            keys = ['title', 'level', 'url', 'type', 'slug', 'objectID', 'myanimelist_id', 'anilist_id']
            print(json.dumps({k: h.get(k) for k in keys if k in h}, indent=2, ensure_ascii=False))
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_jpdb_api():
    """Test jpdb API"""
    print("\n=== jpdb API ===")
    
    # jpdb API docs: https://jpdb.io/api
    # Search novels endpoint
    url = 'https://jpdb.io/api/v1/search/novels'
    payload = {"query": "Bocchi the Rock", "page": 0}
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        })
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        print(f"Status: {resp.status}")
        print(json.dumps(body, indent=2, ensure_ascii=False)[:500])
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_jpdb_token():
    """Test jpdb API token endpoint"""
    print("\n=== jpdb API: Search by anime ===")
    
    # Try the media endpoint if it exists
    url = 'https://jpdb.io/api/v1/search/media'
    payload = {"query": "Bocchi the Rock", "page": 0}
    
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        })
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        print(f"Status: {resp.status}")
        print(json.dumps(body, indent=2, ensure_ascii=False)[:500])
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    algolia_ok = test_learnnatively_algolia()
    jpdb_ok = test_jpdb_api()
    test_jpdb_token()
    
    print(f"\n=== Summary ===")
    print(f"LearnNatively Algolia: {'OK' if algolia_ok else 'FAILED'}")
    print(f"jpdb API: {'OK' if jpdb_ok else 'FAILED'}")