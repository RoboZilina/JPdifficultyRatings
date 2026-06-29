# Data Source Priority — Fully Automated Pipeline

## The Core Problem
It's just you and me. No community entering ratings. So everything must be fetched programmatically — titles AND difficulty ratings.

## Constraints from the Plan Docs
- ✅ anime-offline-database: MIT license, bulk download OK
- ❌ "no scraping of Netflix, Crunchyroll"
- ❌ "no scraping of LearnNatively"
- ❌ "no scraping of jpdb"

But jpdb has an **official API** (not scraping): https://jpdb.io/api
LearnNatively may or may not have an official API.

## Updated Source Ranking

### 1. anime-offline-database (⭐⭐⭐⭐⭐)
- **What we get:** 10,000+ titles, aliases, cross-IDs in one MIT-licensed file
- **Automation:** Single `curl`, single JSON parse
- **Status:** ✅ Ready. No human input needed.

### 2. jpdb API (⭐⭐⭐⭐⭐) — For Difficulty Ratings
- jpdb has a documented API at `https://jpdb.io/api/v1/`
- Can look up anime difficulty by:
  - Title search: `POST /api/v1/search/novels` or similar endpoints
  - By ID if we have jpdb IDs
- **What we need to check:**
  - Does the API have an endpoint for anime/media difficulty lookup?
  - Is authentication required (API key)?
  - What are the rate limits?
- **Status:** Needs investigation. Could automate 50% of our rating data.

### 3. LearnNatively — Unknown
- **Problem:** The plan says "no scraping," and I'm not aware of an official API
- **Options:**
  - If they have an API → automate it
  - If they don't → we might not be able to get their data legally/ethically
  - Alternative: Use jpdb as the sole rating source if LN is inaccessible
- **Status:** Needs investigation.

### 4. AniList API (⭐⭐⭐ — Optional Enrichment)
- No auth required, 90 req/min
- Could fill in missing Japanese titles, synonyms
- Already mostly covered by anime-offline-database
- **Status:** Nice-to-have for edge cases.

### Everything Else (AniDB, MAL, Kitsu, TMDB)
- **Status:** ❌ Skip. Redundant with anime-offline-database for titles.

## Revised Two-Phase Approach

### Phase 1: Title/Alias Database (Automated)
```
1. Download anime-offline-database.json
2. Parse and map into our schema
3. Done — 5000+ entries with titles, aliases, cross-IDs
```

### Phase 2: Difficulty Ratings (Needs Investigation)
```
1. Investigate jpdb API for automated difficulty lookup
2. If it works: batch-query by title or ID → fill rating fields
3. Investigate LearnNatively (API or other approach)
4. If neither works: we have a title database but no ratings
```

## Action Items
1. Read jpdb API docs → determine if we can batch-lookup anime difficulty
2. Check if LearnNatively has any programmatic access
3. Decide if we proceed with just one rating source (jpdb) if LN is unavailable