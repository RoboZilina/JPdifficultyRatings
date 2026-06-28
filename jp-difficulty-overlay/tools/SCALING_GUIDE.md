# JP Difficulty Overlay - Scaling to 5000+ Titles

This guide explains how to build a comprehensive database of 5000+ anime titles with difficulty ratings from LearnNatively and jpdb.

## Overview

The scaling strategy uses this approach:

```
anime-offline-database.json (10,000+ anime)
         ↓
Extract top 5,000 by popularity
         ↓
Batch Import Ratings (LearnNatively + jpdb)
         ↓
Final media-index.json (5,000 titles)
```

## Architecture

### anime-offline-database
- **Size:** 10,000+ anime entries
- **Contains:** Titles, synonyms, metadata, MAL/AniList/AniDB IDs
- **License:** Public domain
- **Update frequency:** Monthly
- **Source:** https://github.com/manami-project/anime-offline-database

### LearnNatively Ratings
- **Type:** Difficulty level (1-60+) + JLPT approximation
- **Accuracy:** Community verified
- **Coverage:** ~500-1000 anime (limited coverage)
- **Access:** Manual lookup or bulk import from community

### jpdb Ratings  
- **Type:** Difficulty number (1-100) + vocab/kanji stats
- **Accuracy:** Automated from subtitle analysis
- **Coverage:** ~2000+ anime
- **Access:** Manual lookup or bulk import from community

## Step-by-Step Workflow

### Phase 1: Extract Base Database (5 minutes)

```bash
# 1. Download anime-offline-database.json
node tools/build-database.js --download-animedb

# 2. Extract top 5000 anime
node tools/build-database.js --extract --limit 5000

# This creates: data/extracted-candidates.json
# Size: ~5000 anime with titles, aliases, metadata (no ratings yet)
```

**What happens:**
- Downloads 10,000+ anime from anime-offline-database
- Filters by type (TV, Movie, OVA, ONA, Special)
- Sorts by popularity (based on synonym count)
- Extracts top 5000

**Output:** `extracted-candidates.json` with entries like:

```json
{
  "id": "bocchi-the-rock",
  "canonicalTitle": "Bocchi the Rock!",
  "titles": { "en": "...", "ja": "...", "romaji": "..." },
  "aliases": [...],
  "platformAliases": { "netflix": [], "crunchyroll": [] },
  "ratings": {
    "learnnatively": { "level": null, "jlptApprox": "", "url": "" },
    "jpdb": { "difficulty": null, "url": "" }
  }
}
```

### Phase 2: Batch Import Ratings (Ongoing)

This is the longest phase. There are several strategies:

#### Strategy A: Community CSV Batch Imports (Recommended)

Organize rating work into batches of 500-1000 titles per CSV file.

**Workflow:**
```bash
# 1. Create CSV file with ratings
#    Use RATINGS_TEMPLATE.csv as a template
#    Add 500 rows of ratings (Canonical Title, LN Level, jpdb Difficulty, etc.)

# 2. Import the batch
node tools/build-database.js --import-ratings batch-001.csv

# 3. Repeat for more batches
node tools/build-database.js --import-ratings batch-002.csv
node tools/build-database.js --import-ratings batch-003.csv
...

# 4. Check progress
node tools/build-database.js --stats
```

**CSV Format:**

```csv
Canonical Title,LearnNatively Level,LearnNatively JLPT,LearnNatively URL,jpdb Difficulty,jpdb URL,Netflix Alias,Crunchyroll Alias,Notes
"Bocchi the Rock!",20,N3,https://learnnatively.com/...,7,https://jpdb.io/...,"BOCCHI THE ROCK!","BOCCHI THE ROCK!","Music comedy"
"Jujutsu Kaisen",20,N3,https://learnnatively.com/...,13,https://jpdb.io/...,"JUJUTSU KAISEN","JUJUTSU KAISEN","Action"
...
```

**Key Points:**
- One CSV per batch (500-1000 rows)
- Must have `Canonical Title` column to match against extracted candidates
- Ratings are optional (partial imports OK)
- Platform aliases are optional but helpful

#### Strategy B: Distributed Community Effort

Assign different sections to different people:

```
Person 1: A-D (anime titles starting with A-D)
Person 2: E-J
Person 3: K-O
Person 4: P-T
Person 5: U-Z
```

Each person works on their section and produces a CSV with ratings. Then merge all CSVs:

```bash
node tools/build-database.js --import-ratings ratings-A-D.csv
node tools/build-database.js --import-ratings ratings-E-J.csv
node tools/build-database.js --import-ratings ratings-K-O.csv
node tools/build-database.js --import-ratings ratings-P-T.csv
node tools/build-database.js --import-ratings ratings-U-Z.csv
```

#### Strategy C: Prioritize Popular Titles

Don't rate all 5000. Instead:
1. Start with top 500 most popular (will have most of both LN and jpdb coverage)
2. Add another 500 less popular
3. Continue in tiers

This gives better coverage faster.

```
Tier 1 (500 titles): 80% coverage
Tier 2 (500 titles): 60% coverage  
Tier 3 (1000 titles): 40% coverage
Tier 4+ (2500 titles): 20% coverage
```

#### Strategy D: Parallel with Google Sheets

Use Google Sheets to crowdsource ratings:

1. **Create a Google Sheet** with extracted titles (use IMPORTRANGE or manual)
2. **Share with community** for rating collaboration
3. **Automate CSV export** from Google Sheets
4. **Import batch** with `--import-ratings`

This allows multiple people to work simultaneously.

### Phase 3: Merge and Finalize (1 minute)

Once you have enough ratings imported:

```bash
# Merge all imported ratings into final database
node tools/build-database.js --merge

# This creates: media-index.json (the extension's database)
```

**Check statistics:**

```bash
node tools/build-database.js --stats
```

Output example:
```
Final Database (media-index.json):
   Total entries: 5000
   With both ratings: 1250 (25%)
   With LearnNatively: 2300 (46%)
   With jpdb: 2100 (42%)
   With Netflix alias: 800 (16%)
   With Crunchyroll alias: 950 (19%)
```

## Data Sources for Ratings

### LearnNatively

**URL:** https://learnnatively.com/

**How to get ratings:**
1. Click on a series
2. View the **Difficulty Level** (main number)
3. View the **JLPT Approx** (N5-N1)
4. Copy the series URL

**Bulk Options:**
- Export from LearnNatively's reading list (if available)
- Community-maintained CSV with LN ratings
- Request bulk data from LearnNatively (long-term partnership)

### jpdb

**URL:** https://jpdb.io/

**How to get ratings:**
1. Search for an anime
2. Click on the series
3. View the **Difficulty** number (1-100 scale)
4. Copy the URL

**Bulk Options:**
- jpdb API (if available)
- jpdb data exports (request from maintainers)
- Community-maintained CSV with jpdb difficulties

### Netflix/Crunchyroll Aliases

These need to be manually verified or crowd-sourced:

1. Search Netflix for each title
2. Note the exact title as it appears
3. Add to the `Netflix Alias` column
4. Repeat for Crunchyroll

**Or:** Screenshot detection tool
- Someone browses Netflix/Crunchyroll
- Captures actual title strings
- Organizes into CSV
- Other people add to media-index.json

## Timeline Estimates

- **Phase 1 (Extract):** 5-10 minutes
- **Phase 2 (Rating import):** 
  - 500 titles: 2-4 hours (manual entry)
  - 500 titles: 30 minutes (bulk import from CSV)
  - 5000 titles: 20-50 hours total
- **Phase 3 (Merge):** 1 minute

**Recommended pace:**
- Week 1: Extract base database (Phase 1)
- Weeks 2-8: Import ratings in batches of 500
- Week 9: Merge and test final database

## Quality Metrics

Track coverage as you go:

```bash
# After each batch import
node tools/build-database.js --stats
```

Target:
- **MVP:** 500 titles with both ratings (~200-300 hours of work)
- **Good:** 1000 titles with both ratings
- **Comprehensive:** 2500+ titles with both ratings

Even with 1000 titles, you'll cover most popular anime people actually watch.

## Optimizations

### Parallel Processing

If you have multiple people working:

```
Person 1: Extract database (do once)
People 2-5: Each work on 500-1000 title ratings
Everyone: Email CSV files to coordinator
Coordinator: Imports all CSVs in sequence
```

This can reduce 50 hours to 10-15 hours of total work.

### Automation

You can automate some aspects:

```javascript
// Example: Auto-fetch jpdb difficulty if jpdb exposes an API
// (Currently not allowed per no-scraping rule)

// But you CAN:
// - Parse your own CSV files programmatically
// - Batch-verify titles against anime-offline-database
// - Generate platform alias suggestions
```

### Community Coordination

If building with a community:

1. **GitHub Issues:** One issue per 500-title batch
2. **Google Sheets:** Shared rating spreadsheet
3. **Discord:** Coordination and discussion
4. **Kanban board:** Track progress

## Maintenance Long-Term

Once you have 5000 titles:

- **Monthly:** Update new anime from anime-offline-database
- **Quarterly:** Check for title/alias mismatches
- **As-needed:** Update LearnNatively/jpdb URLs if they change

## Example: 500-Title Batch

Here's what importing a single batch looks like:

**Step 1: Create CSV** (`batch-001.csv`)
```csv
Canonical Title,LearnNatively Level,LearnNatively JLPT,LearnNatively URL,jpdb Difficulty,jpdb URL,Netflix Alias,Crunchyroll Alias,Notes
"Bocchi the Rock!",20,N3,https://learnnatively.com/anime/3471,7,https://jpdb.io/search?q=bocchi,"BOCCHI THE ROCK!","BOCCHI THE ROCK!","Music comedy"
"Jujutsu Kaisen",20,N3,https://learnnatively.com/anime/5034,13,https://jpdb.io/search?q=jujutsu,"JUJUTSU KAISEN","JUJUTSU KAISEN","Action"
"Demon Slayer",20,N3,https://learnnatively.com/anime/5005,15,https://jpdb.io/search?q=demon,"DEMON SLAYER","DEMON SLAYER","Action"
...
(500 rows total)
```

**Step 2: Import**
```bash
node tools/build-database.js --import-ratings batch-001.csv
```

**Output:**
```
✅ Matched and updated 480/500 entries
📁 Updated: data/extracted-candidates.json
```

**Step 3: Check progress**
```bash
node tools/build-database.js --stats
```

**Step 4: Repeat with next batch**
```bash
node tools/build-database.js --import-ratings batch-002.csv
```

## Contributing

To contribute to the database:

1. Choose a section (500 titles)
2. Add ratings to a CSV
3. Submit a pull request with the CSV
4. Maintainer imports and merges

See `CONTRIBUTING.md` for details.

## Final Notes

- **Quality over speed:** Better to have 1000 high-quality ratings than 5000 guesses
- **Community power:** A small team of 5 people can complete 5000 titles in 2-3 months
- **Incremental value:** Even 500 titles with ratings is useful (covers top anime)
- **Open source:** Consider sharing your rating CSVs with the community

Good luck building the database! 🚀
