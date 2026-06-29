# Data Source Extraction & Normalization Plan

## Objective
Define how to fetch, parse, normalize, and merge title data from each approved external source into our `media-index.json` schema — without violating licensing, rate limits, or the project's metadata-minimal policy.

## Guiding Principles
1. **Only LearnNatively and jpdb ratings enter the extension** — all other sources provide only titles/aliases.
2. **External sources are offline admin tools only** — never called from the browser extension at runtime.
3. **A human reviewer always approves** what goes into `media-index.json`.
4. **Attribution and license compliance** must be documented for each source.

---

## 1. anime-offline-database (Primary Source)

### Format
- Single JSON file (`anime-offline-database.json`)
- Each entry has fields:
  - `sources` — array of `sourcename: id` strings (e.g. `["anilist: 101921", "myanimelist: 40748", "anidb: 14227"]`)
  - `title` — English title (string)
  - `type` — e.g. `"TV"`, `"Movie"`, `"OVA"`, `"ONA"`, `"Special"`
  - `episodes` — number
  - `status` — `"FINISHED"`, `"RELEASING"`, `"NOT_YET_RELEASED"`
  - `animeSeason` — `{ season: "spring", year: 2022 }`
  - `picture` — URL (we do NOT download or store images)
  - `thumbnail` — URL (we do NOT download or store)
  - `synonyms` — array of alternate title strings
  - `relations` — array of related anime IDs
  - `tags` — array of strings (we do NOT import tags without explicit review)

### Extraction Strategy
```bash
# Fetch (1 GB HTTPS, ~50 MB file)
curl -L -o data/raw/anime-offline-database.json \
  https://raw.githubusercontent.com/manami-project/anime-offline-database/master/anime-offline-database.json

# Read JSON, filter to types we want (TV, Movie, OVA, ONA)
# Map into our schema
```

### Field Mapping to Our Schema
```
anime-offline-database         →   media-index.json
────────────────────────────────────────────────────
title                          →   titles.en
type                           →   workType (map: TV→anime-series, Movie→anime-movie, etc.)
synonyms                       →   aliases[]
sources (anilist: id)          →   externalIds.anilist
sources (myanimelist: id)      →   externalIds.mal
sources (anidb: id)            →   externalIds.anidb
sources (kitsu: id)            →   externalIds.kitsu
────────────────────────────────────────────────────
NOT imported: picture, thumbnail, episodes, status, animeSeason, relations, tags
```

### ID Generation
Derive `id` from the English title:
```js
function generateId(title) {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
```

### License
- MIT license (manami-project/anime-offline-database)
- Attribution required: include `sources` field referencing original, credit manami-project
- Allowed to redistribute title data with attribution

### Normalization Applied Before Storing
- `titles.en`: kept as-is, the canonical English title
- `aliases[]`: lowercased, trimmed, deduplicated
- `synonyms` imported to `aliases[]` after filtering out ones that are overly generic (single common words like "monster", "hero")

---

## 2. AniDB Anime Title Dumps (Secondary Source)

### Format
- Plain text file, pipe-delimited lines
- Format per line: `aid|type|language|title`
- Types: `1`=primary title, `2`=synonym, `3`=short title, `4`=official title
- Languages include `en`, `ja`, `x-jat` (romaji), `x-other`, etc.

### Extraction Strategy
```bash
# Fetch (once per day maximum)
curl -o data/raw/anidb-titles.titles.gz \
  https://vgmdb.net/db/anime-titles.dat.gz
gunzip data/raw/anidb-titles.titles.gz
```

### Field Mapping
```
AniDB line                     →   media-index.json
────────────────────────────────────────────────────
aid                            →   externalIds.anidb
title (language=en, type=1/4) →   titles.en (if not already set)
title (language=ja, type=1/4) →   titles.ja
title (language=x-jat, type=1)→   titles.romaji
title (any language, type=2/3)→   aliases[] (after normalization)
```

### Constraints
- **Fetch once per day maximum** — cache locally after first download
- Use only for **alias enrichment**, not as authoritative source for canonical titles
- AniDB license terms: check before redistribution; used only as intermediate tooling

### Build Merge Logic
When a title exists in both anime-offline-database and AniDB:
1. Prefer anime-offline-database for `titles.en` and `titles.romaji` (it's more maintained)
2. Use AniDB for filling `titles.ja` if anime-offline-database doesn't have it
3. Use AniDB synonyms to enrich `aliases[]`

---

## 3. AniList GraphQL API (Tertiary / Manual Lookup)

### API Details
- Endpoint: `POST https://graphql.anilist.co`
- No API key required
- Rate limit: 90 requests per minute
- Supports batching up to 50 IDs per request via `Page` query

### GraphQL Query
```graphql
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    synonyms
    format
    episodes
    status
    startDate { year }
    genres
  }
}
```

### Extraction Strategy
- Not suitable for batch bulk extraction (rate limit, pagination)
- Use for **individual title lookup during curation**
- Or use the **10000-query-per-day limit** to batch-enrich all entries gradually

### Field Mapping
```
AniList Media.title.english    →   titles.en (supplemental)
AniList Media.title.romaji     →   titles.romaji (supplemental)
AniList Media.title.native     →   titles.ja (supplemental)
AniList Media.synonyms         →   aliases[] (after review)
AniList Media.id               →   externalIds.anilist
AniList Media.format           →   workType (map: TV→anime-series, MOVIE→anime-movie, etc.)
```

### NOT Imported
- `genres` — not needed for title resolution
- `episodes`, `status`, `startDate` — not needed
- `description` — explicitly forbidden

### Usage Rules
- **Do not call from the browser extension**
- Admin/developer tooling only
- Max 90 req/min, ~10,000/day — enough to enrich 5000 entries in batches

---

## 4. MyAnimeList API (Manual Validation)

### API Details
- Endpoint: `https://api.myanimelist.net/v2/anime`
- Requires OAuth or client-ID header: `X-MAL-CLIENT-ID`
- Paginated results, max 100 per page

### Limitations
- Less convenient for batch extraction
- Requires API registration
- Rate-limited per application

### Recommended Use
- Manual title validation during curation
- Filling `externalIds.mal` when needed
- Not suitable as a primary batch source

### Field Mapping
```
MAL node.title                 →   for manual comparison only
MAL node.id                    →   externalIds.mal
MAL node.alternative_titles    →   for alias review only
```

---

## 5. Kitsu API (Secondary Lookup)

### API Details
- Endpoint: `https://kitsu.io/api/edge/anime`
- JSON:API format
- Pagination: max 20 per page, can be slow for bulk

### Recommended Use
- Secondary alias lookup during curation
- Not efficient for bulk seeding

### Field Mapping
```
Kitsu attributes.titles.en     →   comparison/review only
Kitsu attributes.titles.ja_jp  →   comparison/review only
Kitsu attributes.abbreviatedTitles → aliases[] candidates
Kitsu attributes.id            →   externalIds.kitsu
```

---

## 6. TMDB API (Netflix Non-Anime)

### API Details
- Endpoint: `https://api.themoviedb.org/3/{tv|movie}`
- Requires API key: `api_key` query parameter
- Supports search and title details

### Recommended Use
- Netflix live-action Japanese content
- Not for anime (already covered by above sources)

### Field Mapping
```
TMDB name/title                →   titles.en
TMDB external_ids.imdb_id      →   externalIds.imdb
TMDB alternative_titles.titles →   aliases[] candidates
```

---

## Normalization Pipeline (Shared Across All Sources)

### Step 1: Title Cleaning
Applied to every title and alias from every source before storage:
```js
function normalizeTitle(title) {
  if (!title) return "";
  return String(title)
    .toLowerCase()
    .normalize("NFKC")
    .replace(/\b(subbed|dubbed|sub|dub)\b/g, " ")
    .replace(/\b(tv series|series|movie|ova|ona|special)\b/g, " ")
    .replace(/\bseason\s*\d+\b/g, " ")
    .replace(/\bs\d+\b/g, " ")
    .replace(/[!！?？:：;；'’"“”.,・·•\-–—_()[\]{}<>]/g, " ")
    .replace(/&/g, " and ")
    .replace(/\s+/g, " ")
    .trim();
}
```

### Step 2: Compact Key (for Japanese matching)
```js
function normalizeTitleCompact(title) {
  return normalizeTitle(title).replace(/\s+/g, "");
}
```

### Step 3: Generate Lookup Index
```js
function addAlias(lookupMap, alias, entryId) {
  const normal = normalizeTitle(alias);
  const compact = normalizeTitleCompact(alias);
  if (normal) lookupMap.set(normal, entryId);
  if (compact && compact !== normal) lookupMap.set(compact, entryId);
}
```

### Step 4: Conflict Detection
```js
// If two different entryIds normalize to the same key, it's a conflict
// Add to generated-conflicts.json and exclude from auto-lookup
// Require more specific aliases to disambiguate
```

---

## Merge Strategy (Multi-Source)

When processing multiple sources, use this priority to resolve conflicts:

```
1. anime-offline-database        → primary canonical titles
2. AniDB title dumps             → fill missing ja/romaji, enrich aliases
3. AniList API                   → supplement missing fields, add external IDs
4. MAL / Kitsu / TMDB            → tertiary validation, non-anime content
```

### Conflict Resolution Rules
- If two sources give different `titles.en`, prefer anime-offline-database
- If a title only exists in AniDB (not in anime-offline-database), mark it as unverified
- If a synonym from AniDB normalizes to the same key as an existing alias from another entry, flag as conflict

---

## External ID Schema

Add to `media-index.json` schema for cross-referencing:
```json
{
  "id": "bocchi-the-rock",
  "titles": { ... },
  "aliases": [ ... ],
  "externalIds": {
    "anilist": 101921,
    "myanimelist": 40748,
    "anidb": 14227,
    "kitsu": 12345
  },
  "ratings": { ... }
}
```

`externalIds` are:
- Optional — not required for MVP
- Useful for deduplication and future enrichment
- Allowed per source licenses (check each)
- Not exposed in the extension runtime (kept for admin tooling only)

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA SOURCE PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  anime-offline-database (MIT)                                       │
│    ↓ fetch + parse                                                  │
│    ↓ extract: title, synonyms, type, sources                        │
│    ↓ map to: titles.en, aliases[], workType, externalIds            │
│    ↓ normalize + deduplicate                                        │
│    ↓ output: data/candidates-from-aod.json                          │
│                                                                     │
│  AniDB title dumps (check license)                                  │
│    ↓ fetch (1x/day) + parse pipe-delimited                          │
│    ↓ extract: aid, title variants by language                       │
│    ↓ map to: titles.ja, titles.romaji, aliases[], externalIds.anidb │
│    ↓ merge with candidates-from-aod.json (fill gaps)                │
│    ↓ output: data/candidates-merged.json                            │
│                                                                     │
│  AniList API (admin tool only, no auth required)                    │
│    ↓ batch query by externalIds.anilist                             │
│    ↓ extract: title variants, synonyms, format, genres              │
│    ↓ map to: titles.* (supplement), aliases[], workType             │
│    ↓ output: data/candidates-enriched.json                          │
│                                                                     │
│  Human Reviewer                                                     │
│    ↓ review candidates-enriched.json                                │
│    ↓ approve aliases, add ratings from LearnNatively/jpdb           │
│    ↓ output: data/media-index.json (final, curated)                 │
│                                                                     │
│  generate-normalized-index.js                                       │
│    ↓ read media-index.json                                          │
│    ↓ normalize all aliases                                          │
│    ↓ detect conflicts                                               │
│    ↓ output: data/generated-normalized-index.json                   │
│    ↓ output: data/generated-conflicts.json                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Files to Create

```
tools/
├── fetch-anime-offline-db.js     # Downloads + parses anime-offline-database
├── fetch-anidb-titles.js         # Downloads + parses AniDB title dumps
├── enrich-from-anilist.js        # Batch queries AniList for enrichment
├── merge-candidates.js           # Merges all sources into combined candidate list
├── generate-normalized-index.js  # Generates lookup + conflict reports
└── validate-media-index.js       # Checks final media-index.json for compliance

docs/
├── SOURCES_GUIDE.md              # When/how to use each source (already planned)
└── ATTRIBUTIONS.md               # License and attribution for each source
```

## Success Criteria

1. Each source's fetch/extract tool works independently (can run one at a time)
2. Merge tool produces a combined candidate file with deduplication and conflict flags
3. Human reviewer can review and approve candidates before they enter `media-index.json`
4. Generation tool produces normalized index and conflict report from final DB
5. All source licenses and rate limits are respected and documented

---
*This is a documentation plan only. No code changes until approved.*