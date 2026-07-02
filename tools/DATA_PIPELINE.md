# JP Difficulty Overlay — Data Pipeline Guide

This document describes how the `media-index.json` database (currently 5,820 entries) is built from LearnNatively and jpdb, with enrichment from anime-offline-database and TMDB.

> ⚠️ **This is the real pipeline** that was used to build the current database. It is **not** the same as the Node.js/CSV workflow described in `WORKFLOW.md` and `SCALING_GUIDE.md` — that system was designed for future community contributions but was **never used** to build the existing database.

## Core Principle

- **LearnNatively (LN)** and **jpdb** are the **only sources of difficulty ratings**
- **anime-offline-database** is used **only for enrichment** (aliases, Japanese/romaji titles, external IDs) — it never supplies ratings
- **TMDB** is used **only for non-anime Netflix live-action content** that doesn't exist in the other sources

## Architecture

```
                         ┌───────────────────────┐
                         │  LearnNatively (LN)    │
                         │  Primary title &       │
                         │  rating source         │
                         │  ~5,000+ entries       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  anime-offline-        │
                         │  database              │
                         │  Enrichment only       │
                         │  (aliases, ja titles,  │
                         │   external IDs)        │
                         └───────────┬───────────┘
                                     │ (cross-reference by
                                     │  title/MAL ID)
                                     ▼
                         ┌───────────────────────┐
                         │  jpdb                 │
                         │  Secondary rating     │
                         │  source               │
                         │  ~1,399 entries       │
                         └───────────┬───────────┘
                                     │ (matched via
                                     │  candidate index)
                                     ▼
                         ┌───────────────────────┐
                         │  TMDB Netflix         │
                         │  Non-anime live-action │
                         │  supplement           │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  media-index.json     │
                         │  5,820 entries        │
                         │  LN base + jpdb-only  │
                         │  + live-action extras │
                         └───────────────────────┘
```

## Pipeline Steps (In Order)

### Step 0: Understand the relationship

LN is the **primary seed**: entries from LN's catalog form the base of the database. Each LN entry is cross-referenced against anime-offline-database candidates to pull in rich aliases, Japanese/romaji titles, and external IDs. jpdb scores are attached to candidates, which are then matched to LN entries (or added as standalone entries if they have no LN match).

### Step 1: Fetch LearnNatively catalog

> **⚠️ Prerequisite: You need a valid LN session cookie.**

The LN search API (`/api/search-api/`) requires authentication. Unlike the public autocomplete API, this gives complete catalog coverage.

| File | Details |
|------|---------|
| **Script** | `tools/fetch-ln-all-pages.py` |
| **Input** | Hardcoded LN cookies (`sessionid` + `csrftoken`) |
| **Output** | `data/ln-video-catalog.json` + `data/ln-book-catalog.json` |
| **What it fetches** | All pages of LN's video and book catalogs (sorted by popularity) |
| **Key data** | Title, English title, difficulty level (`lvl`), URL, media type, genres |

**How to get fresh cookies:**
1. Log in to learnnatively.com in Chrome
2. Open DevTools → Network tab → refresh page
3. Click any request, find `Cookie:` in Request Headers
4. Copy the entire cookie string
5. Paste it into the `COOKIE` variable at line 6 of `fetch-ln-all-pages.py`

**Gotcha:** The cookie expires. You'll need a fresh one each time you re-run this script. If the script fails with a 403, your cookie has expired.

---

### Step 2: Fetch jpdb difficulty ratings

jpdb has a public anime difficulty list at `/anime-difficulty-list` with ~1,399 entries. This script downloads all pages and parses them via regex.

| File | Details |
|------|---------|
| **Script** | `tools/fetch-jpdb-ratings.py` |
| **Input** | `data/candidates.json` (from step 3) |
| **Output** | `data/candidates_with_jpdb.json` |
| **API** | Public HTML pages (no auth) — regex-parses `<h5>` titles and `<th>Average difficulty</th>` |
| **Matching strategy** | 3 fallbacks: (1) MAL ID, (2) normalized title, (3) stripped season title then normalized title |
| **Key data** | Difficulty score (1-100), jpdb URL, MAL ID |

**Important:** This script **must run after** `fetch-anime-offline-db.py` (step 3) because it matches jpdb entries against the candidate database. It reads `candidates.json` and writes `candidates_with_jpdb.json`.

**Gotcha:** This is HTML scraping, not an API. If jpdb changes their page HTML structure, the regex will break. The pagination uses `?offset=` parameters (50 entries per page).

---

### Step 3: Fetch anime-offline-database (enrichment only)

This downloads the full anime-offline-database (~50MB JSON) from the manami-project GitHub releases. It is used **only** to provide rich aliases, Japanese/romaji titles, and external IDs — **never** for ratings.

| File | Details |
|------|---------|
| **Script** | `tools/fetch-anime-offline-db.py` |
| **Input** | GitHub release (https://github.com/manami-project/anime-offline-database) |
| **Output** | `data/candidates.json` |
| **What it filters** | Only TV, Movie, OVA, ONA, Special types |
| **What it extracts** | English title, Japanese title, romaji, aliases, external IDs (MAL, AniList, AniDB, Kitsu) |
| **Rating fields** | All set to `null` — ratings come from LN and jpdb only |

**How it enriches the final database:**
- LN entries (from step 1) are matched against these candidates by title
- Matched candidates contribute: Japanese titles, romaji, additional aliases, MAL/AniList IDs
- These enrichments make title matching work better on Netflix/Crunchyroll

**Usage:**
```bash
python tools/fetch-anime-offline-db.py          # All candidates
python tools/fetch-anime-offline-db.py --limit 100  # Test with 100 entries
```

---

### Step 4: Fetch TMDB Netflix entries (non-anime only)

This fetches Japanese-language movies and TV shows available on Netflix (Slovak region) from TMDB. It **excludes anime** (genre 16) since those are covered by LN + jpdb.

| File | Details |
|------|---------|
| **Script** | `tools/fetch-tmdb-netflix.py` |
| **Input** | `data/candidates_with_jpdb.json` (from step 2) |
| **Output** | `data/candidates_with_all.json` |
| **API** | TMDB API (free key, hardcoded in script) |
| **What it adds** | Japanese live-action series/movies on Netflix with title aliases |
| **workType** | `live-action-series` or `live-action-movie` |

**Gotcha:** The API key is hardcoded. If it gets revoked or rate-limited, you'll need a new one (free from https://www.themoviedb.org/documentation/api).

---

### Step 5: Build merged database

This is the final merge script. It reads all the above outputs and produces the extension's `media-index.json`.

| File | Details |
|------|---------|
| **Script** | `tools/build-merged-db.py` |
| **Inputs** | `data/ln-video-catalog.json` (from step 1), `data/candidates_with_all.json` (from step 4) |
| **Output** | `data/media-index-merged.json` (copy to `media-index.json`) |
| **Matching strategy** | 3 fallbacks: (1) LN title → candidate title index, (2) LN variant → reverse candidate index, (3) length-based correction for generic titles |

**Merge logic:**
1. **Iterate LN entries** — each LN title is matched against the candidate database (anime-offline-db + jpdb + TMDB). Matched entries get rich aliases, jpdb scores, and external IDs.
2. **Unmatched LN entries** are included anyway — they just lack jpdb scores and rich aliases.
3. **jpdb-only candidates** — candidates that have jpdb scores but no LN match are appended as standalone entries.
4. **TMDB live-action entries** are included as-is.

**Gotcha:** The matching has a "correction" mechanism at lines 144-155 — if an LN title is short but the matched candidate is very specific, it looks for a better match by preferring the candidate with the shortest canonical title. This fixed some cases where generic LN titles matched wrong spin-offs.

---

### Step 6: Patch null LN ratings via Japanese matching (second pass)

After the initial merge, some entries may have jpdb scores but no LN rating. This happens when the English title matching failed but the Japanese title exists in LN's catalog.

| File | Details |
|------|---------|
| **Script** | `tools/patch-ln-v2.py` |
| **Inputs** | `media-index.json` (from step 5), `data/ln-video-catalog.json`, `data/candidates_with_all.json` |
| **Output** | Patched `media-index.json` (backup created as `media-index.json.bak2`) |
| **Matching strategy** | Builds a Japanese-title lookup from LN catalog (native titles), then checks candidates' `ja_jp`/`ja`/`native` fields + Japanese-character aliases |

This is a second pass that specifically targets entries where English title matching failed but Japanese title matching works.

---

## Complete Re-run Sequence

```bash
# 1. First, update the LN session cookie in fetch-ln-all-pages.py
#    (Open learnnatively.com in browser → get fresh cookie → paste into script)

# 2. Fetch LN catalog (needs valid session cookie)
python tools/fetch-ln-all-pages.py

# 3. Fetch anime-offline-database (enrichment)
python tools/fetch-anime-offline-db.py

# 4. Fetch jpdb ratings (reads candidates.json from step 3)
python tools/fetch-jpdb-ratings.py

# 5. Fetch TMDB Netflix (reads candidates_with_jpdb.json from step 4)
python tools/fetch-tmdb-netflix.py

# 6. Build merged database
python tools/build-merged-db.py

# 7. Copy to extension
cp data/media-index-merged.json media-index.json

# 8. Patch null LN ratings (optional, for better coverage)
python tools/patch-ln-v2.py
```

## When to Re-run

| Trigger | What to re-run | Notes |
|---------|----------------|-------|
| New anime season (Jan/Apr/Jul/Oct) | Steps 1-3, 5 | New titles added to LN + anime-offline-db |
| jpdb updates their difficulty list | Steps 3-5 | jpdb updates regularly |
| New Netflix live-action shows | Steps 4-5 | TMDB discover query picks them up |
| Monthly maintenance | Steps 1-7 | Full rebuild |
| Quarterly check | Steps 1-7 | Ensure no URL/title drift |

## What NOT to Use

The following documentation and scripts describe a **different, Node.js/CSV-based pipeline** that was designed for distributed community contributions but was **never used** to build the actual database:

- ❌ **`WORKFLOW.md`** — Manual CSV entry workflow (aspirational, not tested)
- ❌ **`SCALING_GUIDE.md`** — Same manual CSV strategy
- ❌ **`npm run download` / `npm run extract` / `npm run generate-batches`** — These Node.js scripts are unused
- ❌ **`build-database.js`** — Node.js equivalent that was never used for production
- ❌ **`csv-to-media-index.js`** — CSV import that was never used

These were created as a plan for future community contribution, but the Python pipeline above is what actually produced the 5,820-entry database.

## Exploratory Scripts (Abandoned Approaches)

The following scripts were part of trial-and-error and are **not** part of the production pipeline:

| Script | What it tried | Why abandoned |
|--------|---------------|---------------|
| `fetch-ln-catalog.py` | Public autocomplete API enumeration | Incomplete coverage (only finds what you search for) |
| `fetch-ln-ratings.py` | Same approach, test only | Exploratory |
| `fetch-ln-video-catalog.py` | Search API with cookie, single catalog | Superseded by `fetch-ln-all-pages.py` (which does video + book) |
| `fetch-ln-videos.py` | Same | Superseded |
| `fetch-ln-remaining.py` | Incremental fetch | Superseded |
| `explore-ln-api.py` | API discovery | Investigation only |
| `explore-ln-endpoints.py` | Endpoint testing | Investigation only |
| `test-algolia.py` | Algolia search approach | LN doesn't use Algolia |
| `analyze-ln.py` | LN data analysis | Investigation only |
| `analyze-ln-v2.py` | LN data analysis v2 | Investigation only |
| `patch-null-ln-ratings.py` | Earlier patching attempt | Superseded by `patch-ln-v2.py` |
| `fix-unmatched-jpdb.py` | Fixing jpdb match failures | Superseded by `build-merged-db.py`'s improved matching |

## Lessons Learned

1. **LN needs a session cookie for bulk access** — The public autocomplete API can't enumerate the full catalog. The search API (`/api/search-api/`) needs `sessionid` + `csrftoken` cookies.

2. **jpdb has no public API** — The difficulty list is HTML-only. The scraping is fragile.

3. **Title matching is the hardest problem** — Three fallback strategies exist because no single approach catches everything. Even then, `patch-ln-v2.py` is needed as a second pass for Japanese-only matching.

4. **anime-offline-database is enrichment, not a source** — It provides aliases that make the extension's title matching work, but it's not a rating source.

5. **The Node.js scripts were aspirational** — They represent a manual, community-driven approach that was planned but never executed. All 5,820 entries came from the Python pipeline.