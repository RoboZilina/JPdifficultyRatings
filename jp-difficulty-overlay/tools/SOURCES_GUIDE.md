# External Data Sources Guide

This guide explains how to leverage external anime databases and APIs for building the JP Difficulty Overlay database, following the principles in the planning document.

## Core Principle

**Only LearnNatively and jpdb ratings go into the extension.** All other sources are used **offline as developer tools only**, never in the live extension.

---

## Recommended Sources

### 1. anime-offline-database (⭐ Best for Aliases)

**Source:** https://github.com/manami-project/anime-offline-database

**What it provides:**
- 10,000+ anime titles with complete metadata
- Cross-references to MAL, AniDB, AniList, Kitsu, Anime-Planet, etc.
- Multiple title variants for each anime (English, Romaji, native, synonyms)
- Already solved the alias/matching problem

**Use for:**
- ✅ Candidate title seeding (what anime to include)
- ✅ Synonym/alias suggestions
- ✅ Source URLs to external platforms
- ✅ Matching assistance

**Never use for:**
- ❌ Copied descriptions
- ❌ Images or artwork
- ❌ Pre-filled ratings
- ❌ Tags/categories without explicit license review

**How to use:**
```bash
npm run download  # Downloads anime-offline-database.json
```

**Attribution required?**
Yes. The database is open source. Include attribution in README/CONTRIBUTING if redistributing.

**Our implementation:**
- `build-database.js --download-animedb` downloads it
- Used in title extraction for alias seeding
- Offline tool only - not called from extension

---

### 2. AniList API (⭐ Great for Lookups)

**Source:** https://graphql.anilist.co (public GraphQL endpoint)

**What it provides:**
- Searchable anime database
- Title variants (English, Romaji, native)
- Synonyms for each anime
- External links to other platforms
- No authentication required

**Use for:**
- ✅ Looking up individual anime
- ✅ Finding title variants
- ✅ Suggesting aliases
- ✅ Validating canonical titles

**Never use for:**
- ❌ Bulk importing descriptions
- ❌ Auto-populating ratings
- ❌ Calling from the browser extension

**How to use:**
```bash
# Enrich metadata with AniList
npm run enrich:sample
npm run enrich:all

# Suggest aliases using AniList
node tools/suggest-aliases.js "Bocchi the Rock!"
```

**Rate limits:**
- 90 requests per minute (free tier)
- Our tools respect this with delays

**Attribution required?**
Include link to AniList in README.

**Our implementation:**
- `enrich-anilist.js` queries metadata (genres, release dates)
- `suggest-aliases.js` queries for title variants
- Admin tools only - safe, no auth needed

---

### 3. AniDB Anime Titles Dump (Good for Aliases)

**Source:** https://anidb.net/

**What it provides:**
- Daily updated anime title dumps
- Japanese/English/Romaji variants
- AniDB ID mappings
- Designed for client-side search

**Use for:**
- ✅ Alias research and normalization
- ✅ AniDB ID lookups
- ✅ Title variant discovery

**Never use for:**
- ❌ More than once per day (respect rate limit)
- ❌ Descriptions or detailed metadata

**Rate limits:**
- Once per day maximum
- Cache locally after downloading

**Attribution required?**
Yes - AniDB requires attribution for any redistribution.

**Our implementation:**
- Not yet implemented, but can be added as supplementary source
- Would be used in `suggest-aliases.js` similar to anime-offline-database

**To implement:**
```bash
# Future enhancement
node tools/suggest-aliases.js --include-anidb "Title"
```

---

### 4. MyAnimeList API (Optional for Validation)

**Source:** https://myanimelist.net/api/v2 (official v2 API)

**What it provides:**
- Official MAL anime database
- Comprehensive metadata
- Search capabilities
- OAuth support available

**Use for:**
- ✅ Manual title validation
- ✅ MAL ID lookups
- ✅ Title variant verification

**Never use for:**
- ❌ Bulk importing without permission
- ❌ Auto-populating extension data

**Access:**
- Requires API client ID (free)
- Some endpoints may require OAuth

**Attribution required?**
Check MyAnimeList API terms.

**Our implementation:**
- Not automated (manual lookup recommended)
- Can be added for admin tooling if needed

---

### 5. Kitsu API (Optional Secondary Source)

**Source:** https://kitsu.io/api/edge

**What it provides:**
- Anime search via JSON:API
- Title filtering and pagination
- Alternate title discovery
- Community-maintained data

**Use for:**
- ✅ Alternate title research
- ✅ Secondary validation
- ✅ API-based search

**Limitations:**
- Pagination can be cumbersome for bulk operations
- Less comprehensive than MAL/AniDB

**Our implementation:**
- Optional enhancement
- Not yet prioritized

---

### 6. TMDB (The Movie Database) (For Non-Anime)

**Source:** https://www.themoviedb.org/api

**What it provides:**
- Movie and TV database (general, not anime-specific)
- Netflix live-action Japanese shows
- Regional title variants
- API access with key

**Use for:**
- ✅ Non-anime Japanese content on Netflix
- ✅ Live-action TV series
- ✅ Regional title variants

**Access:**
- Requires free API key
- API terms and rate limits apply

**Never use for:**
- ❌ Without explicit license review
- ❌ Copyrighted descriptions without attribution

**Our implementation:**
- Not yet implemented
- Future enhancement for non-anime content

---

### 7. TheTVDB (Optional, Complex)

**Source:** https://www.thetvdb.com/

**What it provides:**
- Long-running TV/movie database
- International titles
- Episode metadata

**Limitations:**
- More involved licensing/access
- Less convenient than TMDB for MVP

**Our implementation:**
- Not recommended for MVP
- Consider only if TMDB proves insufficient

---

## Tool: suggest-aliases.js

The **suggest-aliases.js** script implements the "version 2" recommendation from the planning document.

### What It Does

Takes a canonical title and suggests aliases from multiple sources:

```bash
node tools/suggest-aliases.js "Bocchi the Rock!"
```

**Process:**
1. Searches anime-offline-database for matching titles
2. Queries AniList for title variants
3. Generates common abbreviations
4. Returns deduplicated list

**Output:**
```json
{
  "title": "Bocchi the Rock!",
  "normalized": "bocchi the rock",
  "sources": {
    "animeOfflineDb": ["bocchi the rock", "bocchi "],
    "anilist": ["bocchi the rock", "btwr"],
    "variants": ["bocchi the rock", "bocchitherock"],
    "compactVariant": ["bocchitherock"]
  }
}
```

### Workflow

1. Admin runs: `node tools/suggest-aliases.js "Title"`
2. Reviews suggestions
3. Manually selects which ones to add to media-index.json
4. **Human review required** - never auto-import

### Usage Examples

```bash
# Single title
node tools/suggest-aliases.js "Demon Slayer"

# Batch suggestions
node tools/suggest-aliases.js --batch data/extracted-candidates.json

# Output: alias-suggestions.json with top 10 suggestions
```

---

## Database Building Strategy

### Phase 1: Use anime-offline-database
```bash
npm run download        # Get 10,000+ anime
npm run extract         # Extract top 5,000 candidates
```

### Phase 2: Manual Rating Entry
- Use LearnNatively + jpdb only
- No auto-import of ratings
- Human verifies each entry

### Phase 3: Suggest Aliases (Optional)
```bash
node tools/suggest-aliases.js "Title"  # For individual entries
node tools/suggest-aliases.js --batch data/extracted-candidates.json  # Batch
```

### Phase 4: Enrich Metadata (Optional)
```bash
npm run enrich:sample   # Add genres, dates, etc. from AniList
```

### Phase 5: Merge and Deploy
```bash
npm run merge           # Create final media-index.json
```

---

## Compliance Checklist

Before using any external source, verify:

- ✅ **License:** What is the source's license? Are we compliant?
- ✅ **Attribution:** Do we need to credit the source?
- ✅ **Rate limits:** Are there per-day or per-minute limits?
- ✅ **Terms:** Do the API/service terms allow our use case?
- ✅ **Caching:** Should we cache locally to respect limits?
- ✅ **Redistribution:** If bundling data, what are the rules?

### Current Status

| Source | License | Attribution | Rate Limit | Included |
|--------|---------|-------------|-----------|----------|
| anime-offline-database | Creative Commons | Yes | None | ✅ |
| AniList API | Public API | Yes | 90/min | ✅ |
| AniDB Dump | GPL/Custom | Yes | 1/day | 📋 Future |
| MyAnimeList API | Official | Check terms | Check terms | 📋 Future |
| Kitsu API | Public API | Likely | Check | 📋 Future |
| TMDB | Commercial | Yes | API key | 📋 Future |
| TheTVDB | Commercial | Yes | Complex | ❌ Low priority |

---

## What NOT to Do

### ❌ Auto-import Ratings
Never automatically populate LearnNatively or jpdb ratings from external sources.

**Why?**
- Different sources may have different difficulty scales
- Community has verified that only LN + jpdb are authoritative
- Extension's value is based on curated, human-verified data

### ❌ Copy Descriptions
Never copy plot summaries or descriptions from external databases.

**Why?**
- Likely copyrighted
- Not needed for difficulty rating display
- Can cause legal issues

### ❌ Bundle Images
Never include posters, artwork, or screenshots.

**Why?**
- Copyright issues
- Bloats the extension
- Against most API terms

### ❌ Call External APIs from Extension
Never make API calls from the browser extension itself.

**Why?**
- Leaks user activity to third parties
- Privacy violation
- Against most service terms
- Extension should be fully offline

### ❌ Exceed Rate Limits
Never spam API endpoints or ignore rate limits.

**Why?**
- Gets your IP/key banned
- Violates terms of service
- Degrades service for others
- Unsustainable for scale

---

## Future Enhancements

### Short Term
- [ ] Add AniDB dump support to `suggest-aliases.js`
- [ ] Document MyAnimeList integration for validation
- [ ] Create helper script for TMDB non-anime content

### Medium Term
- [ ] Build automated daily AniDB dump sync (respecting 1/day limit)
- [ ] Add MAL ID to metadata (for external tool integration)
- [ ] Create admin dashboard showing source coverage

### Long Term
- [ ] Partnership with LearnNatively for bulk rating data
- [ ] Partnership with jpdb for bulk difficulty data
- [ ] Automated updates from anime-offline-database
- [ ] Community API for sharing rating contributions

---

## References

- **anime-offline-database:** https://github.com/manami-project/anime-offline-database
- **AniList:** https://anilist.co and https://graphql.anilist.co
- **AniDB:** https://anidb.net/
- **MyAnimeList:** https://myanimelist.net/api/v2
- **Kitsu:** https://kitsu.io/api
- **TMDB:** https://www.themoviedb.org/api

---

## Questions?

See `WORKFLOW.md`, `SCALING_GUIDE.md`, or open an issue on GitHub.
