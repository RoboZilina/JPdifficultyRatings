#!/usr/bin/env python3
"""Check if Goblin Slayer exists in any LN raw data backup."""
import json, sys

# Write to a file instead of console
out = open('goblin_check_results.txt', 'w', encoding='utf-8')

# 1. Check current media-index.json
final = json.load(open('jp-difficulty-overlay/media-index.json', 'r', encoding='utf-8'))
for e in final:
    if e['id'] == 'ao-goblin-slayer':
        out.write(f"Current media-index.json -> id={e['id']} title={e['canonicalTitle']} LN level={e['ratings']['learnnatively']['level']} jpdb={e['ratings']['jpdb']['difficulty']}\n")
        break

# 2. Check ln-video-catalog.json (the extracted catalog used in build)
cat = json.load(open('jp-difficulty-overlay/data/ln-video-catalog.json', 'r', encoding='utf-8'))
found = []
for e in cat:
    et = (e.get('englishTitle','') or '').lower()
    nt = (e.get('title','') or '').lower()
    if 'goblin' in et or 'goblin' in nt or 'ゴブリンスレイヤー' in nt:
        found.append(e)
out.write(f"\nln-video-catalog.json: {len(cat)} entries\n")
if found:
    for f in found:
        out.write(f"  FOUND: id={f.get('id')} en=\"{f.get('englishTitle','')}\" native=\"{f.get('title','')}\" L{f.get('lvl')} type={f.get('mediaType')} url={f.get('url')}\n")
else:
    out.write(f"  NOT found (only movie 'Goblin\'s Crown' exists)\n")
    for e in cat:
        if 'goblin' in json.dumps(e, ensure_ascii=False).lower():
            out.write(f"  Raw match: {json.dumps(e, ensure_ascii=False)[:200]}\n")

# 3. Check ln-search-api2-raw.txt (the large raw API response backup)
api2 = json.load(open('jp-difficulty-overlay/backups/ln-search-api2-raw.txt', 'r', encoding='utf-8'))
results = api2.get('results', [])
out.write(f"\nln-search-api2-raw.txt: {len(results)} result objects\n")
for r in results:
    item = r.get('item') or r.get('series') or r
    text = json.dumps(item, ensure_ascii=False).lower()
    if 'goblin' in text:
        out.write(f"  FOUND: {json.dumps(item, ensure_ascii=False)[:300]}\n")
        break
else:
    out.write(f"  NOT FOUND in api2 backup\n")

# 4. Check html backup for goblin slayer
html = open('jp-difficulty-overlay/backups/ln-search-bluebox-raw.html', 'r', encoding='utf-8', errors='replace').read()
if 'goblin' in html.lower():
    out.write(f"\nln-search-bluebox-raw.html: FOUND 'goblin' in HTML\n")
    for line in html.split('\n'):
        if 'goblin' in line.lower():
            out.write(f"  {line.strip()[:300]}\n")
            break
else:
    out.write(f"\nln-search-bluebox-raw.html: NOT FOUND\n")

# 5. Check ln-browse-raw.txt
browse = open('jp-difficulty-overlay/backups/ln-browse-raw.txt', 'r', encoding='utf-8', errors='replace').read()
if 'goblin' in browse.lower():
    out.write(f"\nln-browse-raw.txt: FOUND 'goblin' in content\n")
    for line in browse.split('\n'):
        if 'goblin' in line.lower():
            out.write(f"  {line.strip()[:300]}\n")
            break
else:
    out.write(f"\nln-browse-raw.txt: NOT FOUND\n")

# 6. Check ln-videos-raw.txt 
videos = open('jp-difficulty-overlay/backups/ln-videos-raw.txt', 'r', encoding='utf-8', errors='replace').read()
if 'goblin' in videos.lower():
    out.write(f"\nln-videos-raw.txt: FOUND 'goblin' (len={len(videos)})\n")
    for line in videos.split('\n'):
        if 'goblin' in line.lower():
            out.write(f"  {line.strip()[:300]}\n")
            break
else:
    out.write(f"\nln-videos-raw.txt: NOT FOUND (len={len(videos)})\n")

out.close()
print("Written to goblin_check_results.txt")