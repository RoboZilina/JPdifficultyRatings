#!/usr/bin/env python3
"""
Parse LearnNatively video catalog from HTML page source.

The user browses learnnatively.com/search/jpn/videos/?page=N
and pastes the page HTML here. We extract video items with ratings.

Usage: paste HTML content, script extracts items.

The search-page API response is also embedded as JSON in the page.
"""

import json
import re
import sys

def extract_from_html(html):
    """Extract video items from LearnNatively search page HTML."""
    items = []
    
    # Try to find embedded JSON data first (search-page API response)
    # Look for window.__INITIAL_STATE__ or similar patterns
    json_patterns = [
        r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
        r'window\.__NUXT__\s*=\s*({.*?});',
        r'window\.__DATA__\s*=\s*({.*?});',
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>({.*?})</script>',
        r'window\.searchPageData\s*=\s*({.*?});',
        r'window\.__PRELOADED_STATE__\s*=\s*({.*?});',
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                print(f"Found embedded JSON data")
                return extract_from_json(data)
            except:
                continue
    
    # Fallback: look for item cards in HTML
    # Find item blocks (each video appears as a card)
    item_blocks = re.findall(
        r'<div[^>]*class="[^"]*item-card[^"]*"[^>]*>.*?</div>\s*</div>\s*</div>',
        html, re.DOTALL
    )
    
    if not item_blocks:
        # Try broader pattern
        item_blocks = re.findall(
            r'<div[^>]*class="[^"]*item[^"]*"[^>]*>.*?(?:rating|rubric).*?</div>',
            html, re.DOTALL
        )
    
    if not item_blocks:
        # Try to find any div with data attributes that look like items
        item_blocks = re.findall(
            r'data-item-id="([^"]*)"[^>]*>.*?<h[^>]*>([^<]+)</h',
            html, re.DOTALL
        )
    
    if not item_blocks:
        print("No item cards found in HTML")
        print(f"Page size: {len(html)} bytes")
        return []
    
    print(f"Found {len(item_blocks)} raw item blocks, parsing...")
    
    for block in item_blocks:
        item = parse_item_block(block)
        if item:
            items.append(item)
    
    return items

def parse_item_block(block):
    """Parse a single item HTML block to extract data."""
    result = {}
    
    # Title
    title_match = re.search(r'<h[^>]*>([^<]+)</h', block)
    if title_match:
        result['title'] = title_match.group(1).strip()
    
    # Level/Rating
    lvl_match = re.search(r'[Ll]evel[:\s]*(\d+)', block)
    if not lvl_match:
        lvl_match = re.search(r'rubric[^>]*>L?(\d+)', block)
    if lvl_match:
        result['lvl'] = int(lvl_match.group(1))
    
    # URL
    url_match = re.search(r'href="(/[^"]*)"', block)
    if url_match:
        result['url'] = url_match.group(1)
    
    # Media type
    media_match = re.search(r'class="[^"]*media-type[^"]*"[^>]*>([^<]+)', block)
    if media_match:
        result['mediaType'] = media_match.group(1).strip()
    
    # Image
    img_match = re.search(r'<img[^>]*src="([^"]*)"', block)
    if img_match:
        result['image_url'] = img_match.group(1)
    
    return result if result.get('title') else None

def extract_from_json(data):
    """Extract items from embedded JSON data."""
    items = []
    
    # The search-page API response structure
    if isinstance(data, dict):
        # Try direct results
        for key in ['results', 'items', 'entries']:
            if key in data and isinstance(data[key], list):
                return parse_json_results(data[key])
        
        # Try nested in initialState
        if 'initialState' in data and isinstance(data['initialState'], dict):
            for key, val in data['initialState'].items():
                if isinstance(val, list):
                    parsed = parse_json_results(val)
                    if parsed:
                        items.extend(parsed)
        
        # Try any list with item-like objects
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0:
                if isinstance(val[0], dict) and ('title' in val[0] or 'item' in val[0] or 'series' in val[0]):
                    parsed = parse_json_results(val)
                    if parsed:
                        items.extend(parsed)
    
    elif isinstance(data, list):
        items = parse_json_results(data)
    
    return items

def parse_json_results(items):
    """Parse a list of JSON item objects."""
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        
        # Handle nested {item: {...}, widget: 'item'} format
        payload = item.get('item') or item.get('series') or item
        
        rating_obj = payload.get('rating', {})
        if not isinstance(rating_obj, dict):
            rating_obj = {}
        
        if not payload.get('title'):
            continue
            
        entry = {
            'title': payload.get('title', ''),
            'englishTitle': payload.get('englishTitle', ''),
            'url': payload.get('url', ''),
            'mediaType': payload.get('mediaType', ''),
            'mediaTypeDisplay': payload.get('mediaTypeDisplay', ''),
            'libraryType': payload.get('libraryType', ''),
            'genres': payload.get('genres', []),
            'lvl': rating_obj.get('lvl'),
            'descriptor': rating_obj.get('lvlDescriptor', ''),
            'image_url': payload.get('image', {}).get('url', '') if isinstance(payload.get('image'), dict) else '',
        }
        
        # Extract descriptions
        blurbs = payload.get('blurbs', [])
        if blurbs and isinstance(blurbs, list):
            for b in blurbs:
                if isinstance(b, dict):
                    if b.get('textLanguageCode') == 'en':
                        entry['description_en'] = b.get('text', '')[:300]
                    elif b.get('textLanguageCode') == 'ja':
                        entry['description_ja'] = b.get('text', '')[:300]
        
        result.append(entry)
    
    return result

def save_items(items, page_num):
    """Save extracted items to a cumulative file."""
    import os
    data_dir = 'd:/DifficultyRatings/jp-difficulty-overlay/data'
    outfile = f'{data_dir}/ln-video-page-{page_num}.json'
    
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(items)} items to {outfile}")
    
    # Also update cumulative catalog
    cumul_file = f'{data_dir}/ln-video-catalog-manual.json'
    all_items = {}
    
    # Load existing cumulative
    if os.path.exists(cumul_file):
        with open(cumul_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            for item in existing:
                all_items[item.get('url', item.get('title', ''))] = item
    
    # Add new items
    for item in items:
        key = item.get('url', item.get('title', ''))
        all_items[key] = item
    
    # Save cumulative
    with open(cumul_file, 'w', encoding='utf-8') as f:
        json.dump(list(all_items.values()), f, indent=2, ensure_ascii=False)
    
    print(f"Cumulative catalog: {len(all_items)} unique items")

if __name__ == '__main__':
    print("Paste the HTML content of a LearnNatively video search page,")
    print("then press Ctrl+Z then Enter (Windows) or Ctrl+D (Mac/Linux).")
    print()
    
    html = sys.stdin.read()
    
    if len(html) < 100:
        print("HTML too short. Make sure you're copying the page source.")
        print("To get page source: Right-click -> 'View Page Source' -> Ctrl+A -> Ctrl+C")
        sys.exit(1)
    
    print(f"\nRead {len(html)} bytes of HTML")
    
    # Try to determine page number
    page_match = re.search(r'[?&]page=(\d+)', html)
    page_num = int(page_match.group(1)) if page_match else 1
    
    items = extract_from_html(html)
    
    if items:
        rated = sum(1 for i in items if i.get('lvl') is not None)
        print(f"\nExtracted {len(items)} items ({rated} with ratings)")
        
        # Show samples
        print("\nSample items:")
        for item in items[:5]:
            print(f"  {item.get('title','?')[:40]:40s} | L{item.get('lvl','?')} | {item.get('mediaType','?')[:15]}")
        
        save_items(items, page_num)
    else:
        print("\nCould not extract items from HTML.")
        print("The data might be loaded dynamically via JavaScript.")
        print()
        print("Alternative: In Chrome DevTools (F12):")
        print("1. Go to Network tab")
        print("2. Filter by 'api/search-api'")
        print("3. Click the request -> Preview tab")
        print("4. Right-click the JSON and 'Copy object'")
        print("5. Paste that JSON here instead")