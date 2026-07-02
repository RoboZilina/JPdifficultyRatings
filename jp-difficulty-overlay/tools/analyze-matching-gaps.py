#!/usr/bin/env python3
"""
Analyze why candidates fail to match LN entries.
Uses hash lookups only (fast) to quantify the matching gap.
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = Path(__file__).parent.parent / 'data'

def normalize(s):
    if not s: return ''
    s = s.lower()
    s = re.sub(r'[^\w\s\u3000-\u9fff\uff00-\uffef\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_compact(s):
    return normalize(s).replace(' ', '')

def title_variants(title):
    variants = set()
    if not title: return variants
    variants.add(normalize(title))
    cleaned = re.sub(r'\s*S\d+\s*$', '', title, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\s*(?:Season|Part|Vol|Volume)[.\s]*\d+.*$', '', cleaned, flags=re.IGNORECASE).strip()
    if cleaned != title and cleaned:
        variants.add(normalize(cleaned))
    cleaned2 = re.sub(r'\s*\([^)]*\)\s*', '', title).strip()
    if cleaned2 != title and cleaned2:
        variants.add(normalize(cleaned2))
    cleaned3 = re.sub(r'\s*[:]\s*', ' ', title).strip()
    if cleaned3 != title and cleaned3:
        variants.add(normalize(cleaned3))
    return variants

print("=" * 70)
print("MATCHING GAP ANALYSIS (fast mode)")
print("=" * 70)

candidates = json.load(open(DATA_DIR / 'candidates_with_all.json', 'r', encoding='utf-8'))
ln_entries = json.load(open(DATA_DIR / 'ln-video-catalog.json', 'r', encoding='utf-8'))
final = json.load(open(Path(__file__).parent.parent / 'media-index.json', 'r', encoding='utf-8'))

print(f"\nCandidates: {len(candidates)}")
print(f"LN entries: {len(ln_entries)}")
print(f"Final: {len(final)}")

has_ln = sum(1 for e in final if e['ratings']['learnnatively']['level'] is not None)
null_ln = sum(1 for e in final if e['ratings']['learnnatively']['level'] is None)
print(f"Final with LN: {has_ln}, null LN: {null_ln}")

# Build fast LN compact-title lookup
ln_by_compact = {}
for ln in ln_entries:
    for t in [ln.get('englishTitle', ''), ln.get('title', '')]:
        if t:
            for v in title_variants(t):
                c = normalize_compact(v)
                if c and c not in ln_by_compact:
                    ln_by_compact[c] = ln

print(f"\nLN compact lookup keys: {len(ln_by_compact)}")

# Also build compact lookup with "s1" appended (since LN often tags S1)
# and a version that strips trailing "s1"
ln_by_compact_variants = {}
for c, ln in ln_by_compact.items():
    ln_by_compact_variants[c] = ln
    # Also store without trailing s1/s2 etc
    stripped = re.sub(r's\d+$', '', c)
    if stripped and stripped != c and stripped not in ln_by_compact_variants:
        ln_by_compact_variants[stripped] = ln

print(f"LN compact lookup (+ variants): {len(ln_by_compact_variants)}")

# Collect null-LN candidate IDs
null_ids = set()
for e in final:
    if e['ratings']['learnnatively']['level'] is None and e['id'].startswith('ao-'):
        null_ids.add(e['id'].replace('ao-', ''))

null_candidates = [c for c in candidates if c.get('id', '') in null_ids]
print(f"\nNull-LN candidates: {len(null_candidates)}")

matched_exact = []
matched_stripped = []
no_match = []

for c in null_candidates:
    ct = c.get('canonicalTitle', '')
    if not ct:
        no_match.append((c.get('id', ''), '(no title)'))
        continue
    
    c_compact = normalize_compact(ct)
    
    # Check exact compact match
    ln = ln_by_compact_variants.get(c_compact)
    
    if not ln:
        # Try stripping S1 from candidate too
        c_stripped = re.sub(r's\d+$', '', c_compact)
        if c_stripped and c_stripped != c_compact:
            ln = ln_by_compact_variants.get(c_stripped)
            if ln:
                matched_stripped.append((ct, ln.get('englishTitle', '') or ln.get('title', ''), ln.get('lvl'), f"stripped candidate: {c_compact} -> {c_stripped}"))
                continue
        
        # Check if candidate compact ends with a digit (season number)
        # and try the version without the digit
        c_no_trailing_num = re.sub(r'\d$', '', c_compact)
        if c_no_trailing_num and c_no_trailing_num != c_compact:
            # Check if LN has something that matches this
            for lc, l in ln_by_compact_variants.items():
                if lc.startswith(c_no_trailing_num) or c_no_trailing_num.startswith(lc):
                    if abs(len(lc) - len(c_no_trailing_num)) <= 4:
                        ln = l
                        matched_stripped.append((ct, ln.get('englishTitle', '') or ln.get('title', ''), ln.get('lvl'), f"fuzzy stripped: {c_compact} ~ {lc}"))
                        break
        
    if ln:
        matched_exact.append((ct, ln.get('englishTitle', '') or ln.get('title', ''), ln.get('lvl'), c_compact))
    else:
        no_match.append((ct, c_compact))

print(f"\n{'=' * 70}")
print("RESULTS")
print(f"{'=' * 70}")
print(f"\nExact LN match found (compact): {len(matched_exact)}")
print(f"Match via S1/season stripping: {len(matched_stripped)}")
print(f"No LN entry at all: {len(no_match)}")

print(f"\n--- Exact matches (sample of 20) ---")
for ct, ln_title, lvl, reason in matched_exact[:20]:
    print(f"  {ct}  →  {ln_title}  (L{lvl})")

print(f"\n--- Stripped matches (sample of 20) ---")
for ct, ln_title, lvl, reason in matched_stripped[:20]:
    print(f"  {ct}  →  {ln_title}  (L{lvl})  [{reason}]")

print(f"\n--- No match (sample of 15) ---")
for ct, comp in no_match[:15]:
    print(f"  {ct}")