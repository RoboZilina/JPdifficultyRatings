#!/usr/bin/env python3
"""Analyze LearnNatively page content."""

import json
import re

DATA_DIR = r'd:\DifficultyRatings\jp-difficulty-overlay\data'

# Analyze browse page
with open(f'{DATA_DIR}\\ln-browse.txt', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

results = {'browse_page': {}}
results['browse_page']['size'] = len(html)
results['browse_page']['has_next_data'] = '__NEXT_DATA__' in html
results['browse_page']['has_window_gs'] = 'window.gs' in html

# Find URL configs
urls = re.findall(r"'(/[^']*?api[^']*)'", html)
results['browse_page']['api_urls'] = urls[:20]

# Find all data-loading URLs
data_urls = re.findall(r"'(/[^']*?item[^']*)'", html)
results['browse_page']['data_urls'] = data_urls[:10]

# Analyze videos search page
with open(f'{DATA_DIR}\\ln-videos.txt', 'r', encoding='utf-8', errors='ignore') as f:
    html2 = f.read()

results['videos_page'] = {}
results['videos_page']['size'] = len(html2)

# Check if results are rendered in HTML
item_blocks = re.findall(r'<div class="item[^"]*"[^>]*>', html2)
results['videos_page']['item_divs'] = len(item_blocks)

# Look for level data in format L##
levels_in_html = re.findall(r'L(\d+)', html2)
results['videos_page']['level_patterns'] = len(levels_in_html)

# Look for rubric elements
rubrics = re.findall(r'rubric', html2, re.I)
results['videos_page']['rubric_mentions'] = len(rubrics)

# Check for any JSON data in scripts
json_scripts = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html2)
results['videos_page']['json_scripts'] = len(json_scripts)

# Check pagination
pagination = re.findall(r'page=(\d+)', html2)
results['videos_page']['pagination_pages'] = sorted(set(pagination))[:10]

# Check for any ajax/data-endpoint hints
api_calls = re.findall(r'api', html2, re.I)
results['videos_page']['api_mentions'] = len(api_calls)

# Save
with open(f'{DATA_DIR}\\ln-analysis-results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("Analysis saved")