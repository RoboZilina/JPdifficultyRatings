# REFACTOR_SUMMARY.md — canonicalTitle Fix

## 1. The Bug

`build-merged-db.py` built 5,820 entries, but **3,823 had empty `canonicalTitle`** because unmatched LearnNatively entries never populated title fields.

```python
# BEFORE (broken)
if matched_candidate:
    titles_dict = { ... from candidate ... }
else:
    ln_only += 1
    # BUG: titles_dict stays empty → canonicalTitle = ''
```

## 2. Why It Mattered

The extension searches by `canonicalTitle` and aliases. Empty titles meant **most anime were invisible** to the search, producing "No rating found" for users.

- Matched entries: 1,997 had titles
- Unmatched entries: 3,823 had no titles
- Coverage: 34%

## 3. The Fix

Added explicit `else:` branch to populate `titles_dict` from LN data for unmatched entries:

```python
# AFTER (fixed)
if matched_candidate:
    # Matched: use candidate titles
    titles_dict = { ... from candidate ... }
    aliases = c.get('aliases', []) or []
    # ... jpdb score extraction ...
    matched += 1
else:
    # Unmatched: use LN data
    titles_dict = {
        'en': ln_english or '',
        'ja': ln_title or '',
        'romaji': '',
    }
    aliases = []
    ln_only += 1
    unmatched_entries.append({ ... })

# Single canonical line, no magic fallbacks
canonical = titles_dict['en'] or titles_dict['ja'] or titles_dict['romaji'] or ''
```

## 4. Before / After Metrics

| Metric | Before | After |
|--------|--------|-------|
| Entries with `canonicalTitle` | 1,997 | 5,820 |
| Entries without `canonicalTitle` | 3,823 | 0 |
| Coverage | 34% | 100% |
| Build script spec compliance | ❌ | ✅ |

## 5. Decisions Made

- **Kept unmatched entries as `ln-*` IDs** so we can distinguish them from matched `ao-*` entries later.
- **Used LN English title first**, then Japanese title, then romaji for canonical.
- **Did not add romaji for unmatched** because LN catalog does not provide it.
- **Retained all aliases** from candidates when matched; empty for unmatched (can be enriched later).
- **Added `merge-report.json`** with unmatched samples by difficulty level for future prioritization.

## 6. Verification

```bash
# All 5,820 have canonicalTitle
MISSING_CANONICAL=0
TOTAL_ENTRIES=5820

# Samples
MATCHED_SAMPLE_TITLE=.hack//Sign
UNMATCHED_SAMPLE_TITLE=It\'s in the Woods
MATCHED_SAMPLE_RATING=27
UNMATCHED_SAMPLE_RATING=30
```

## 7. Related Changes

- `content.js` — unchanged, hybrid fallback buttons already present
- `manifest.json` — version 0.2.0
- `media-index.json` — redeployed rebuilt DB
- `build-merged-db.py` — refactored to match `files2/CRITICAL_PATCH_canonicalTitle_fix.md` spec
- Git: tagged `v0.2.0`, commits on `db-build` branch

## 8. Next Steps

1. **Priority 1:** Add romaji for unmatched entries via machine translation or manual mapping.
2. **Priority 2:** Enrich unmatched entries with aliases from TMDB/AniList.
3. **Priority 3:** Increase matched coverage by improving candidate matching heuristics.