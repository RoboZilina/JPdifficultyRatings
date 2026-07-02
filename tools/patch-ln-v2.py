#!/usr/bin/env python3
"""
Second pass: patch null LN ratings using Japanese title matching fallback.
Checks both candidate titles.ja/jp AND aliases for Japanese names.
"""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent

def normalize_compact(s):
    if not s: return ''
    s = re.sub(r'[^\w\s\u3000-\u9fff\uff00-\uffef\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', '', s.lower())
    s = re.sub(r'\s+', '', s)
    return s

def get_japanese_names(cand):
    """Get all Japanese-form names from a candidate (titles + aliases)."""
    names = set()
    t = cand.get('titles', {}) or {}
    for key in ['ja_jp', 'ja', 'native']:
        v = t.get(key, '') or ''
        if v: names.add(v)
    for alias in cand.get('aliases', []):
        if alias:
            # Only include aliases that contain Japanese characters
            if re.search(r'[\u3000-\u9fff\uff00-\uffef\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', alias):
                names.add(alias)
    return names

def main():
    print("=" * 60)
    print("LN PATCHER V2 (Japanese matching)")
    print("=" * 60)

    final = json.load(open(ROOT / 'media-index.json', 'r', encoding='utf-8'))
    cat = json.load(open(ROOT / 'data' / 'ln-video-catalog.json', 'r', encoding='utf-8'))
    candidates = json.load(open(ROOT / 'data' / 'candidates_with_all.json', 'r', encoding='utf-8'))

    print(f"  media-index: {len(final)} entries")
    print(f"  LN catalog: {len(cat)} entries")

    # Build English lookup
    ln_en = {}
    for ln in cat:
        eng = ln.get('englishTitle','') or ''
        if eng:
            c = normalize_compact(eng)
            if c: ln_en[c] = ln
            s = re.sub(r's\d+$','',c)
            if s and s not in ln_en: ln_en[s] = ln

    # Build Japanese native title lookup (LN side)
    ln_jp = {}
    for ln in cat:
        native = ln.get('title','') or ''
        if native:
            c = normalize_compact(native)
            if c: ln_jp[c] = ln
            s = re.sub(r's\d+$','',c)
            if s and s != c and s not in ln_jp: ln_jp[s] = ln

    print(f"  English lookup keys: {len(ln_en)}")
    print(f"  Japanese lookup keys: {len(ln_jp)}")

    null_entries = [(i, e) for i, e in enumerate(final)
                    if e['ratings']['learnnatively']['level'] is None
                    and e['id'].startswith('ao-')]
    print(f"  Null-LN entries: {len(null_entries)}")

    cand_map = {c.get('id',''): c for c in candidates if c.get('id','')}

    patches = []
    still_missing = []

    for idx, entry in null_entries:
        eid = entry['id'].replace('ao-', '')
        ct = entry.get('canonicalTitle', '')
        if not ct: continue

        # Skip if English-matchable
        if normalize_compact(ct) in ln_en:
            continue

        cand = cand_map.get(eid)
        if not cand:
            still_missing.append(ct)
            continue

        # Get ALL Japanese names from candidate (titles + aliases)
        jap_names = get_japanese_names(cand)
        if not jap_names:
            still_missing.append(ct)
            continue

        # Try each Japanese name against LN JP lookup
        matched = False
        for jap in jap_names:
            c_jp = normalize_compact(jap)
            if not c_jp: continue

            ln = ln_jp.get(c_jp)
            if not ln:
                c_jp_no_s = re.sub(r's\d+$', '', c_jp)
                if c_jp_no_s != c_jp:
                    ln = ln_jp.get(c_jp_no_s)

            if ln:
                lvl = ln.get('lvl')
                if lvl is not None:
                    ln_url = ln.get('url', '') or ''
                    patches.append((entry['id'], ct, lvl, f"https://learnnatively.com{ln_url}" if ln_url else None))
                    matched = True
                    break

        if not matched:
            still_missing.append(ct)

    print(f"\n  Japanese-matched (v2): {len(patches)}")
    print(f"  Still missing: {len(still_missing)}")

    if not patches:
        print("\n  No new patches. Exiting.")
        return

    # Show patches, highlighting Goblin Slayer
    print(f"\n  --- Patch sample ---")
    for pid, pct, plvl, _ in patches:
        if 'goblin' in pct.lower() or pid == 'ao-goblin-slayer':
            print(f"  ★ {pid} | {pct} → L{plvl} ← ")
    for pid, pct, plvl, _ in patches[:15]:
        if 'goblin' not in pct.lower():
            print(f"  {pid} | {pct} → L{plvl}")
    if len(patches) > 15:
        print(f"  ... and {len(patches)-15} more")

    # Backup
    backup = ROOT / 'media-index.json.bak2'
    shutil.copy2(ROOT / 'media-index.json', backup)
    print(f"\n  Backup: {backup}")

    # Apply
    patch_count = 0
    for pid, pct, plvl, purl in patches:
        for entry in final:
            if entry['id'] == pid:
                entry['ratings']['learnnatively']['level'] = plvl
                entry['ratings']['learnnatively']['url'] = purl
                patch_count += 1
                break

    json.dump(final, open(ROOT / 'media-index.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f"  ✓ {patch_count} entries patched")

if __name__ == '__main__':
    main()