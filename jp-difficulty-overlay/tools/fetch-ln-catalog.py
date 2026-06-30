#!/usr/bin/env python3
"""
Fetch full catalog from LearnNatively via the public autocomplete API.

Strategy:
- The search-api requires CSRF auth (403 without session)
- The autocomplete-api works without any auth
- We enumerate their catalog by searching letters/words and de-duplicate by ID
- Then match against our existing titles

Usage:
    python tools/fetch-ln-catalog.py
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from collections import OrderedDict

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

API_BASE = "https://learnnatively.com"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Search queries to enumerate their video catalog
# English letters, common words, hiragana, katakana, and kanji
SEARCH_QUERIES = list('abcdefghijklmnopqrstuvwxyz') + [
    # English content words that might match titles
    'anime', 'movie', 'film', 'drama', 'story', 'love', 'life', 'world',
    'tokyo', 'japan', 'japanese', 'school', 'time', 'day', 'night',
    'man', 'girl', 'boy', 'king', 'demon', 'magic', 'fight', 'war',
    'attack', 'titan', 'piece', 'ball', 'star', 'blue', 'red', 'black',
    'white', 'gold', 'silver', 'death', 'note', 'game', 'sport',
    'music', 'song', 'dance', 'food', 'cook', 'ramen', 'sushi',
    'cat', 'dog', 'dragon', 'ghost', 'angel', 'devil', 'god',
    'sword', 'shield', 'arrow', 'gun', 'train', 'bus', 'car',
    'house', 'home', 'city', 'town', 'rain', 'snow', 'wind',
    'fire', 'water', 'earth', 'light', 'shadow', 'dark', 'moon',
    'sun', 'star', 'sky', 'sea', 'ocean', 'river', 'mountain',
    'happy', 'sad', 'funny', 'scary', 'brave', 'strong', 'fast',
    # Japanese hiragana starters
    'あ', 'い', 'う', 'え', 'お',
    'か', 'き', 'く', 'け', 'こ',
    'さ', 'し', 'す', 'せ', 'そ',
    'た', 'ち', 'つ', 'て', 'と',
    'な', 'に', 'ぬ', 'ね', 'の',
    'は', 'ひ', 'ふ', 'へ', 'ほ',
    'ま', 'み', 'む', 'め', 'も',
    'や', 'ゆ', 'よ',
    'ら', 'り', 'る', 'れ', 'ろ',
    'わ', 'を', 'ん',
    # Katakana starters
    'ア', 'イ', 'ウ', 'エ', 'オ',
    'カ', 'キ', 'ク', 'ケ', 'コ',
    'サ', 'シ', 'ス', 'セ', 'ソ',
    'タ', 'チ', 'ツ', 'テ', 'ト',
    'ナ', 'ニ', 'ヌ', 'ネ', 'ノ',
    'ハ', 'ヒ', 'フ', 'ヘ', 'ホ',
    'マ', 'ミ', 'ム', 'メ', 'モ',
    'ヤ', 'ユ', 'ヨ',
    'ラ', 'リ', 'ル', 'レ', 'ロ',
    'ワ', 'ヲ', 'ン',
    # Common kanji starters
    '一', '人', '日', '月', '火', '水', '木', '金', '土',
    '大', '小', '上', '下', '中', '外', '前', '後',
    '新', '古', '白', '黒', '赤', '青',
    '東', '西', '南', '北',
]

def extract_item(item_data):
    """Extract clean item info from autocomplete response."""
    if not isinstance(item_data, dict):
        return None
    
    payload = item_data.get('item') or item_data.get('series') or item_data
    if not isinstance(payload, dict):
        return None
    
    # Get rating
    rating_obj = payload.get('rating', {})
    if not isinstance(rating_obj, dict):
        rating_obj = {}
    
    # Determine library type
    lib_type = payload.get('libraryType', 'video')
    
    # Extract key info
    result = {
        'id': payload.get('id', ''),
        'title': payload.get('title', ''),
        'englishTitle': payload.get('englishTitle', ''),
        'url': payload.get('url', ''),
        'libraryType': lib_type,
        'mediaType': payload.get('mediaType', ''),
        'language': payload.get('language', ''),
        'year': payload.get('year', ''),
        'genres': payload.get('genres', []),
        'rating': {
            'lvl': rating_obj.get('lvl'),
            'temporary': rating_obj.get('temporary', True),
            'lvlDescriptor': rating_obj.get('lvlDescriptor', ''),
        },
        'image_url': payload.get('image', {}).get('url', '') if isinstance(payload.get('image'), dict) else '',
        'numItems': payload.get('numOfItems', 1) if isinstance(payload, dict) else 1,
    }
    
    # For series, extract series-specific info
    if item_data.get('widget') == 'series' or 'series' not in str(payload.get('series')):
        result['is_series'] = False
        # Get blurbs/texts
        blurbs = payload.get('blurbs', [])
        if blurbs and isinstance(blurbs, list):
            for b in blurbs:
                if isinstance(b, dict) and b.get('textLanguageCode') == 'ja':
                    result['japanese_description'] = b.get('text', '')[:200]
                elif isinstance(b, dict) and b.get('textLanguageCode') == 'en':
                    result['english_description'] = b.get('text', '')[:200]
    else:
        result['is_series'] = True
        # Get blurbs
        blurbs = payload.get('blurbs', [])
        if blurbs and isinstance(blurbs, list):
            for b in blurbs:
                if isinstance(b, dict) and b.get('textLanguageCode') == 'ja':
                    result['japanese_description'] = b.get('text', '')[:200]
                elif isinstance(b, dict) and b.get('textLanguageCode') == 'en':
                    result['english_description'] = b.get('text', '')[:200]
    
    return result

def main():
    print("=" * 60)
    print("  Fetch LearnNatively Full Catalog")
    print("=" * 60)
    
    # Step 1: Enumerate via autocomplete API
    print(f"\n1. Enumerating with {len(SEARCH_QUERIES)} search queries...")
    
    all_items = OrderedDict()  # id -> item, to de-duplicate
    queries_done = 0
    
    for query in SEARCH_QUERIES:
        url = f"{API_BASE}/api/autocomplete-api/?q={urllib.request.quote(query)}&libraryType=video"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    extracted = extract_item(item)
                    if extracted and extracted['id']:
                        all_items[extracted['id']] = extracted
            
            queries_done += 1
            if queries_done % 20 == 0:
                print(f"   {queries_done} queries done, {len(all_items)} unique items found so far")
        
        except Exception as e:
            print(f"   Error on '{query}': {str(e)[:50]}")
        
        time.sleep(0.25)  # Rate limit
    
    # Step 2: Save catalog
    catalog = list(all_items.values())
    catalog.sort(key=lambda x: x['title'] or '')
    
    catalog_file = DATA_DIR / "ln-catalog.json"
    with open(catalog_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    print(f"\n2. Catalog saved: {len(catalog)} unique items")
    
    # Step 3: Statistics
    with_ratings = sum(1 for c in catalog if c['rating']['lvl'] is not None)
    by_type = {}
    for c in catalog:
        t = c.get('libraryType', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1
    
    print(f"\n   Items with ratings: {with_ratings}")
    print(f"   Items without ratings: {len(catalog) - with_ratings}")
    print(f"\n   By library type:")
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"     {t}: {count}")
    
    # Step 4: Show samples
    print(f"\n   Sample items (first 5 with ratings):")
    shown = 0
    for c in catalog:
        if c['rating']['lvl'] is not None and shown < 5:
            print(f"     {c['title'][:40]:40s} | L{c['rating']['lvl']:2d} | {c['mediaType'][:15]}")
            shown += 1

if __name__ == '__main__':
    main()