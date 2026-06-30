#!/usr/bin/env python3
"""Explore the LearnNatively search API response structure."""

import json
import re

DATA_DIR = 'd:/DifficultyRatings/jp-difficulty-overlay/data'
d = json.load(open(f'{DATA_DIR}/ln-search-api.txt', 'r', encoding='utf-8'))

out = open(f'{DATA_DIR}/ln-api-exploration.txt', 'w', encoding='utf-8')

out.write(f'=== LearnNatively API Structure ===\n')
out.write(f'Top-level keys: {list(d.keys())}\n\n')

# gsTags - these might be the actual items
tags = d['gsTags']
out.write(f'gsTags: {len(tags)} items\n')
if tags and isinstance(tags[0], dict):
    out.write(f'  Item keys: {list(tags[0].keys())}\n')
    out.write(f'  Sample: {json.dumps(tags[0], indent=2, ensure_ascii=False)[:800]}\n\n')

# initialState - might have search results
state = d['initialState']
out.write(f'initialState keys: {list(state.keys())}\n')
for k, v in state.items():
    if isinstance(v, list):
        out.write(f'  {k}: list of {len(v)}\n')
        if v and isinstance(v[0], dict):
            out.write(f'    keys: {list(v[0].keys())[:10]}\n')
            out.write(f'    sample: {json.dumps(v[0], indent=2, ensure_ascii=False)[:500]}\n')
    elif isinstance(v, dict):
        out.write(f'  {k}: dict with {len(v)} keys\n')

# bootstrap
bs = d['bootstrap']
out.write(f'\nbootstrap keys: {list(bs.keys())[:20]}\n')
if 'levelMapping' in bs:
    out.write(f'  levelMapping: {json.dumps(bs["levelMapping"], indent=2, ensure_ascii=False)[:500]}\n')

# meta - might have pagination
meta = d['meta']
out.write(f'\nmeta: {json.dumps(meta, indent=2, ensure_ascii=False)[:500]}\n')

# check for levelOptionsForSearch
if 'levelOptionsForSearch' in d:
    out.write(f'\nlevelOptionsForSearch: {json.dumps(d["levelOptionsForSearch"], indent=2, ensure_ascii=False)}\n')

out.close()
print('Saved to:', f'{DATA_DIR}/ln-api-exploration.txt')