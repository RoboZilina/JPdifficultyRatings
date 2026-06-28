# Implementation Plan: 5000+ Title Database Building Suite

## Objective
Transform the existing JP Difficulty Overlay project from a prototype (3 titles) into a production-ready system supporting 5000+ anime titles with community contribution workflows and external source integration.

## Current State (Baseline)
- `jp-difficulty-overlay/media-index.json`: 3 anime entries
- `tools/build-media-index.js`: Basic candidate builder
- `tools/csv-to-media-index.js`: CSV → JSON converter
- `tools/CURATION_GUIDE.md`: Basic curation guide
- `JP_Difficulty_Overlay_Normalized_DB_Plan/`: Schema and normalization design docs

## Planned Deliverables

### 1. Update CONTRIBUTING.md
Add database contribution guidelines:
- Hybrid workflow: seed fetching + manual CSV rating + extension-assisted local mapping
- How to fetch candidate titles from anime-offline-database
- How to add LearnNatively and jpdb ratings via CSV batches
- How to validate and submit contributions via PR
- Data quality rules and safety constraints
- Links to new tools and guides

### 2. New Tool Scripts (tools/)
| File | Purpose |
|------|---------|
| `build-database.js` | Main database builder: fetches and extracts top 5000 candidates |
| `generate-csv-batch.js` | Splits candidates into CSV batches (e.g., 500 titles each) for distributed work |
| `track-ratings.js` | Monitor rating progress, show completion %, identify gaps |
| `validate-ratings.js` | Validate CSV data quality before import |
| `suggest-aliases.js` | ⭐ **NEW**: Query anime-offline-database + AniList API to suggest aliases for human review |
| `enrich-anilist.js` | Optional: query AniList API for genres, dates, external links |

### 3. New Documentation
| File | Purpose |
|------|---------|
| `WORKFLOW.md` | Complete 7-phase workflow: download → extract → generate batches → rate → validate → merge → stats |
| `SCALING_GUIDE.md` | Strategies for distributed team work, tiered priority, community contributions |
| `SOURCES_GUIDE.md` | ⭐ **NEW**: When/how to use each external source (anime-offline-database, AniList, AniDB, MAL, Kitsu, TMDB, TheTVDB) |

### 4. Updated Files
| File | Changes |
|------|---------|
| `package.json` | Add npm scripts for each phase of the workflow, including suggest-aliases |
| `tools/CURATION_GUIDE.md` | Update to reflect batch workflow, distributed work, and new tooling |

## External Source Integration (per JP_Difficulty_Overlay_Normalized_DB_Plan.md)

### Core Principle
**Only LearnNatively and jpdb ratings go into the extension.** All other sources are offline developer tools only — never auto-imported.

```javascript
// ✅ CORRECT: Manual entry from LearnNatively/jpdb
entry.ratings.learnnatively.level = 20  // from human
entry.ratings.jpdb.difficulty = 7       // from human

// ❌ WRONG: Auto-imported from other sources
// entry.ratings = importFromAniList()   // Never!
```

### Data Flow

```
anime-offline-database (10,000+ anime)
        ↓
   download (npm run download)
        ↓
extracted-candidates.json (5,000 filtered) (npm run extract)
        ↓
    ├─→ suggest-aliases.js (for alias research)
    │       ├─→ Query anime-offline-database for matching titles
    │       ├─→ Query AniList API for title variants
    │       ├─→ Generate common abbreviations and variations
    │       └─→ Return deduplicated suggestions for human review
    └─→ Manual LearnNatively + jpdb rating entry (sole rating sources)
        ↓
rating CSV batches (human-filled via RATINGS_TEMPLATE.csv)
        ↓
   import & validate (npm run validate:csv)
        ↓
media-index.json (final, curated, 5000 titles)
        ↓
   Deploy to extension
```

### Source-by-Source Strategy

| Source | Role | Usage | In Extension? |
|--------|------|-------|---------------|
| **anime-offline-database** | Primary alias seeding | `npm run download` → offline tool | ❌ No |
| **AniList API** | Title lookup, metadata enrichment | `suggest-aliases.js`, `enrich-anilist.js` | ❌ No |
| **AniDB dumps** | Alias research (secondary) | Manual lookup, documented in SOURCES_GUIDE.md | ❌ No |
| **MyAnimeList API** | Manual validation | Admin tooling only | ❌ No |
| **Kitsu API** | Secondary alias source | Documented fallback | ❌ No |
| **TMDB** | Non-anime Japanese content | Netflix live-action shows | ❌ No |
| **TheTVDB** | General TV validation | Documented, lower priority | ❌ No |
| **LearnNatively** | ⭐ **Sole difficulty rating source** | Manual human entry | ✅ Yes |
| **jpdb** | ⭐ **Sole difficulty rating source** | Manual human entry | ✅ Yes |

### suggest-aliases.js Design

```bash
# Single title
node tools/suggest-aliases.js "Demon Slayer"

# Batch processing
node tools/suggest-aliases.js --batch data/extracted-candidates.json

# Output: data/alias-suggestions.json for human review
```

**Capabilities:**
- Queries anime-offline-database for matching titles and synonyms
- Queries AniList API for romaji/English/native variants
- Generates common abbreviations (e.g., "JJK" for "Jujutsu Kaisen")
- Normalizes and deduplicates suggestions
- **Does NOT auto-import** — requires human review before merging into media-index.json

**Enforces plan constraint:** "A human reviewer still approves what goes into media-index.json"

## Proposed Workflow (7 Phases)

### Phase 1: Download
```bash
npm run download
```
Downloads `anime-offline-database.json` (~50MB) to `data/raw/`

### Phase 2: Extract
```bash
npm run extract
```
Filters to top 5,000 most popular anime by type/score → `data/extracted-candidates.json`

### Phase 3: Suggest Aliases (Optional, per planning doc)
```bash
npm run suggest-aliases "Bocchi the Rock!"
npm run suggest-aliases --batch data/extracted-candidates.json
```
Queries anime-offline-database and AniList → `data/alias-suggestions.json` for review

### Phase 4: Generate Batches
```bash
npm run generate-batches
```
Splits 5000 titles into 10 CSV batches (500 each) → `data/rating-batches/batch-001.csv`, etc.

### Phase 5: Rate Anime
- Each team member/community contributor rates their assigned batch
- Tool: `tools/RATINGS_TEMPLATE.csv`
- Fields: LearnNatively level + JLPT, jpdb difficulty, platform aliases
- **Can use alias suggestions from Phase 3 to help fill aliases**

### Phase 6: Import & Validate
```bash
npm run validate:csv data/rating-batches/batch-001.csv
node tools/build-database.js --import-ratings data/rating-batches/batch-001.csv
npm run track
```

### Phase 7: Merge
```bash
npm run merge
```
Produces final `media-index.json`

### Phase 8: Statistics
```bash
npm run stats
```
Shows coverage metrics.

## Time Estimates
- Solo (500 titles): 2–3 days
- Solo (5000 titles): 3–4 weeks (~50h rating work)
- Team of 5 (5000): 1 week
- MVP (100 titles): 1 day

## Safety & Licensing Constraints
- Fetch from anime-offline-database (respect license/attribution, document in SOURCES_GUIDE.md)
- Use AniList/MAL/Kitsu/TMDB/AniDB only as **offline research aids**
- **Never** auto-import ratings or copied descriptions from external sources
- **Never** include images, subtitles, descriptions, or vocabulary lists
- Only store: title aliases, platform aliases, difficulty ratings, source links
- Add alias suggestions to suggest-aliases.js as candidate ideas only, not auto-merged

## Dependencies & Assumptions
- Node.js available
- GitHub access for cloning/PRs
- Optional: git-lfs if batches become large

## Success Criteria
- `media-index.json` contains 5000+ anime entries with difficulty ratings
- All community contributions go through CSV + validate + merge workflow
- `suggest-aliases.js` implemented per planning doc as offline admin tool
- `SOURCES_GUIDE.md` documents all external sources with usage rules
- Documentation covers all tools and distribution strategies
- Extension still functions safely with the larger database

## Files to Update/Create

### Create
```
IMPLEMENTATION_PLAN.md          # (this file)
tools/suggest-aliases.js
tools/enrich-anilist.js
WORKFLOW.md
SCALING_GUIDE.md
SOURCES_GUIDE.md
```

### Update
```
CONTRIBUTING.md                 # Add database contribution guidelines
package.json                    # Add npm scripts for new tools
tools/CURATION_GUIDE.md         # Reflect batch workflow and new tooling
```

### Existing (keep)
```
tools/build-database.js
tools/generate-csv-batch.js
tools/track-ratings.js
tools/validate-ratings.js
tools/RATINGS_TEMPLATE.csv
tools/csv-to-media-index.js
media-index.json (3 entries)
```

---
*This is a documentation plan only. No code changes will be made until approved.*