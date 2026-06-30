#!/usr/bin/env python3
"""Analyze LearnNatively pages for data extraction points."""

import json
import os
import re

DATA_DIR = 'd:/DifficultyRatings/jp-difficulty-overlay/data'

def save_analysis(name, items):
    """Save analysis results to a file."""
    path = f'{DATA_DIR}/ln-{name}-analysis.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'=== {name} analysis ===\n\n')
        for item in items:
            f.write(f'{item}\n')
    print(f'Saved: {path}')
    return path

# === Analyze browse page ===
with open(f'{DATA_DIR}/ln-browse.txt', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

results = [
    f'File size: {len(html)} bytes',
    f'Contains __NEXT_DATA__: {"__NEXT_DATA__" in html}',
    f'Contains window.gs: {"window.gs" in html}',
    f'Contains Algolia: {"algolia" in html.lower()}',    
]
# Find all API references
api_refs = re.findall(r"'(/[^']*?api[^']*?)'", html)
results.append(f'\nAPI URL references ({len(api_refs)}):')
for r in api_refs[:30]:
    results.append(f'  {r}')

# Find all URL route references with 'load', 'item', 'list'
for pattern in ['load', 'item', 'list', 'search', 'browse']:
    refs = re.findall(rf"'(/[^']*?{pattern}[^']*?)'", html, re.I)
    results.append(f'\n{pattern} URL references ({len(refs)}):')
    for r in refs[:10]:
        results.append(f'  {r}')

save_analysis('browse', results)

# === Analyze videos page ===
with open(f'{DATA_DIR}/ln-videos.txt', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Find all API URLs in the page
api_urls = re.findall(r'https?://[^\"\'\\\s<>]+api[^\"\'\\\s<>]*', html)
api_local = re.findall(r"'(/[^']*?api[^']*?)'", html)

results2 = [
    f'File size: {len(html)} bytes',
    f'Contains __NEXT_DATA__: {"__NEXT_DATA__" in html}',
    f'Contains window.gs: {"window.gs" in html}',
    f'Contains window.gs.urls: {"window.gs.urls" in html}',
    f'Contains window.gs.bootstrap: {"window.gs.bootstrap" in html}',
    f'Contains window.gs.initialState: {"window.gs.initialState" in html}',
    f'\nExternal API URLs ({len(api_urls)}):',
]
for u in api_urls[:20]:
    results2.append(f'  {u}')

results2.append(f'\nLocal API URLs ({len(api_local)}):')
for r in api_local[:30]:
    results2.append(f'  {r}')

# Find any JSON objects that look like data
json_objects = re.findall(r"'/(?:api/)?[a-z-]+(?:-api)?/'", html)
results2.append(f'\nRoute-like patterns ({len(json_objects)}):')
for r in json_objects[:20]:
    results2.append(f'  {r}')

# Find all URL keys in window.gs.urls
gs_urls = re.findall(r"'([a-z-]+)':\s*'([^']+)'", html)
results2.append(f'\nwindow.gs.urls entries ({len(gs_urls)}):')
for key, val in gs_urls[:40]:
    results2.append(f'  {key}: {val}')

save_analysis('videos', results2)

print('Done')