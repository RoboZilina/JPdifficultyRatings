#!/usr/bin/env python3
"""
Patch null LearnNatively ratings in media-index.json by cross-referencing
against ln-video-catalog.json using normalized compact title matching.

The build-merged-db.py matching loop checks LN title variants against
candidate_index, but the normalization path differs between how candidates
are indexed and how LN variants are queried. This results in ~41 entries
that have a corresponding LN video entry but whose rating was never populated.

This script:
1. Reads media-index.json and ln-video-catalog.json
2. Builds a compact (no-space) lookup from LN titles
3. For each null-LN entry, checks if a match exists
4. Only patches entries where confidence is high (exact compact match)
5. Creates a backup before modifying
"""
import json, re, sys, shutil, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / 'data'
MEDIA_INDEX = ROOT_DIR / 'media-index.json'

def normalize(s):
    if not s: return ''
    s = s.lower()
    s = re.sub(r'[^\w\s\u3000-\u9fff\uff00-\uffef\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_compact(s):
    """Remove all spaces after normalizing."""
    return normalize(s).replace(' ', '')

def build_ln_lookup(ln_entries):
    """
    Build a compact-title → LN entry lookup.
    Includes variants with 'S1' / 'S2' suffixes stripped,
    since LN appends ' S1' to most video titles but our candidate titles don't have it.
    """
    lookup = {}
    for ln in ln_entries:
        for t in [ln.get('englishTitle', '') or '', ln.get('title', '') or '']:
            if not t: continue
            n = normalize(t)
            c = n.replace(' ', '')
            if c:
                lookup[c] = ln
            # LN appends "S1" etc to titles — also index without the suffix
            stripped = re.sub(r's\d+$', '', c).strip()
            if stripped and stripped != c and stripped not in lookup:
                lookup[stripped] = ln
    return lookup

def main():
    print("=" * 60)
    print("LN RATING PATCHER")
    print("=" * 60)

    # Load data
    final = json.load(open(MEDIA_INDEX, 'r', encoding='utf-8'))
    ln_videos = json.load(open(DATA_DIR / 'ln-video-catalog.json', 'r', encoding='utf-8'))
    
    print(f"  media-index.json: {len(final)} entries")
    print(f"  ln-video-catalog.json: {len(ln_videos)} entries")

    # Build LN lookup
    ln_lookup = build_ln_lookup(ln_videos)
    print(f"  LN compact lookup: {len(ln_lookup)} keys")

    # Find null-LN entries from candidate pool (ao-* prefix)
    null_entries = [(i, e) for i, e in enumerate(final) 
                    if e['ratings']['learnnatively']['level'] is None 
                    and e['id'].startswith('ao-')]
    print(f"  Null-LN entries to examine: {len(null_entries)}")

    # Attempt matches
    patches = []
    still_missing_count = 0
    matches_by_variant = {  # track which LN entries get matched
        'compact_direct': [],
        'compact_stripped_s1': [],
    }

    for idx, entry in null_entries:
        ct = entry.get('canonicalTitle', '')
        if not ct:
            still_missing_count += 1
            continue

        eid = entry['id']
        c_compact = normalize_compact(ct)
        
        # Try direct compact match
        ln = ln_lookup.get(c_compact)
        match_type = 'compact_direct'
        
        # Try stripping trailing season from candidate too
        if not ln:
            c_stripped = re.sub(r'(s\d+)$', '', c_compact)
            if c_stripped and c_stripped != c_compact and c_stripped in ln_lookup:
                ln = ln_lookup[c_stripped]
                match_type = 'compact_stripped_s1'
        
        if ln:
            lvl = ln.get('lvl')
            if lvl is not None:
                ln_url = ln.get('url', '') or ''
                full_url = f"https://learnnatively.com{ln_url}" if ln_url else None
                
                patches.append({
                    'id': eid,
                    'canonicalTitle': ct,
                    'ln_level': lvl,
                    'ln_url': full_url,
                    'match_type': match_type,
                    'ln_title': ln.get('englishTitle', '') or ln.get('title', ''),
                })
                matches_by_variant[match_type].append(ct)
            else:
                still_missing_count += 1
        else:
            still_missing_count += 1

    # Report
    print(f"\n  Matchable: {len(patches)}")
    print(f"    direct compact match: {len(matches_by_variant['compact_direct'])}")
    print(f"    after S1 stripping:   {len(matches_by_variant['compact_stripped_s1'])}")
    print(f"  Genuinely unmatched: {still_missing_count}")

    if not patches:
        print("\n  No patches needed. Exiting.")
        return

    # Show sample
    print(f"\n  --- Sample of patches (first 15) ---")
    for p in patches[:15]:
        print(f"  {p['id']} | {p['canonicalTitle']:45s} → L{p['ln_level']:2d}  [{p['match_type']}]")
    
    if len(patches) > 15:
        print(f"  ... and {len(patches) - 15} more")

    # Ask before applying
    print(f"\n  Backup: {MEDIA_INDEX.name}.bak")
    print(f"  Patches: {len(patches)} entries to update")
    
    # Create backup
    backup_path = MEDIA_INDEX.with_suffix('.json.bak')
    shutil.copy2(MEDIA_INDEX, backup_path)
    print(f"  Backup created: {backup_path}")
    
    # Apply patches
    patched_count = 0
    for p in patches:
        for entry in final:
            if entry['id'] == p['id']:
                entry['ratings']['learnnatively']['level'] = p['ln_level']
                entry['ratings']['learnnatively']['url'] = p['ln_url']
                patched_count += 1
                break
    
    # Write updated media-index.json
    with open(MEDIA_INDEX, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    
    # Generate report
    report_lines = [
        f"LN Rating Patch Report",
        f"=======================",
        f"Date: {datetime.datetime.now().isoformat()}",
        f"",
        f"Entries patched: {patched_count}",
        f"Still null: {still_missing_count}",
        f"",
        f"Patched entries:",
    ]
    for p in patches:
        report_lines.append(f"  {p['id']} | {p['canonicalTitle']} → L{p['ln_level']} ({p['match_type']})")
    
    report_path = ROOT_DIR / 'data' / 'ln-patch-report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n  Report: {report_path}")
    print(f"  ✓ {patched_count} entries patched successfully")

if __name__ == '__main__':
    main()