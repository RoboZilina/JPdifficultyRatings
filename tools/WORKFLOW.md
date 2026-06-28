# JP Difficulty Overlay - Complete Database Building Workflow

This guide walks you through the complete process of building a 5000+ title anime database with difficulty ratings from LearnNatively and jpdb.

## Quick Reference

| Phase | Command | Time | Output |
|-------|---------|------|--------|
| 1. Download | `npm run download` | 1-2 min | anime-offline-database.json |
| 2. Extract | `npm run extract` | 5 min | extracted-candidates.json (5000 titles) |
| 3. Generate CSVs | `npm run generate-batches` | 1 min | batch-001.csv, batch-002.csv, ... |
| 4. Add Ratings | Manual entry in Excel/Sheets | ~50 hrs | Completed CSV batches |
| 5. Import | `npm run validate:csv batch-001.csv` + manual `--import-ratings` | 1 hr | Merged candidates |
| 6. Merge | `npm run merge` | 1 min | media-index.json |
| 7. Stats | `npm run stats` | 1 sec | Coverage report |

**Total time estimate:** 2 weeks (with small team), 4 weeks (solo)

---

## Phase 1: Download Base Database (1-2 minutes)

anime-offline-database contains 10,000+ anime with titles, synonyms, and metadata.

```bash
npm run download
```

**What happens:**
- Downloads ~50MB JSON file
- Saves to: `data/raw/anime-offline-database.json`
- Contains: titles, synonyms, sources (MAL, AniList, AniDB links)

**Time:** 1-2 minutes (depends on internet speed)

**Next:** Phase 2

---

## Phase 2: Extract Candidates (5 minutes)

Filter the 10,000 anime down to 5,000 most popular (by synonym count).

```bash
npm run extract
```

**Options:**
```bash
# Default: extract 5000
npm run extract

# Extract fewer (for testing)
npm run extract:sample  # 500 titles
```

**What happens:**
- Filters by anime type (TV, Movie, OVA, ONA, Special)
- Removes previews, shorts, OST tracks
- Sorts by popularity (synonym count)
- Creates: `data/extracted-candidates.json`

**Output:** 5000 anime with:
- Canonical title
- Alternate titles (English, Japanese, Romaji)
- Aliases for matching
- Platform aliases (from anime-offline-database)
- No ratings yet

**Next:** Phase 3 (prepare for rating entry)

---

## Phase 3: Generate CSV Batches (1 minute)

Split the 5000 candidates into 500-title CSV batches for parallel rating work.

```bash
npm run generate-batches
```

**What happens:**
- Creates 10 CSV files: `batch-001.csv` through `batch-010.csv`
- Each has ~500 anime titles
- Columns: Canonical Title, LN Level, jpdb Difficulty, URLs, etc.
- Saves to: `data/rating-batches/`

**Output files:**
```
batch-001.csv  (rows 1-500)
batch-002.csv  (rows 501-1000)
batch-003.csv  (rows 1001-1500)
...
batch-010.csv  (rows 4501-5000)
```

**Next:** Phase 4 (distribute for rating)

---

## Phase 4: Rate Anime (50+ hours work)

This is the longest phase. Add difficulty ratings from LearnNatively and jpdb.

### Strategy A: Distributed Team (Recommended)

Assign each batch to a different person.

```
Person 1: batch-001.csv
Person 2: batch-002.csv
Person 3: batch-003.csv
etc.
```

Each person:
1. Opens `batch-XXX.csv` in Excel or Google Sheets
2. Adds ratings for 500 anime:
   - LearnNatively Level (1-60+)
   - jpdb Difficulty (1-100)
   - LearnNatively URL
   - jpdb URL
   - Netflix/Crunchyroll aliases (optional)

**Estimated time per batch:** 5-8 hours
**With 10 people:** 5-8 hours total
**With 3 people:** 15-25 hours total

### Strategy B: Google Sheets Collaboration

For real-time collaboration:

1. Create a Google Sheet with all 5000 titles
2. Share with team members
3. Each person fills in their assigned rows
4. Export as CSV when complete

**Tools:**
- Google Sheets IMPORTRANGE for merging data
- Form submissions for contributions
- Comment threads for questions

### Strategy C: Community Contributions

Post batches on GitHub/Discord and wait for community submissions:

1. Upload each `batch-XXX.csv` to GitHub Issues
2. Label by alphabet (A-D, E-J, etc.)
3. Community members claim and rate
4. Submit PRs with completed CSVs

**Estimated time:** 2-4 weeks (depends on community size)

### How to Rate

For each anime in the batch:

**LearnNatively:**
1. Go to https://learnnatively.com/
2. Search for the anime title
3. Click on the series
4. Copy the **Difficulty Level** (large number on left)
5. Copy the **JLPT Approx** (N5-N1)
6. Copy the series URL

**jpdb:**
1. Go to https://jpdb.io/
2. Search for the anime
3. Click the series
4. Copy the **Difficulty** number
5. Copy the URL

**Platform Aliases (Optional but helpful):**
1. Search on Netflix
2. Copy the exact title as it appears
3. Repeat for Crunchyroll

**Example row:**
```csv
"Bocchi the Rock!",20,N3,https://learnnatively.com/...,7,https://jpdb.io/...,"BOCCHI THE ROCK!","BOCCHI THE ROCK!","Music"
```

### Tips for Efficiency

- **Batch lookup:** Have two browser windows open (LearnNatively + jpdb)
- **Copy/paste:** Copy URL patterns to reduce typing
- **Estimate JLPT:** If LN doesn't have it, estimate from jpdb difficulty
- **Partial entries:** It's OK to leave some fields blank (~70% coverage is good)
- **Team coordination:** Check progress with `npm run track`

---

## Phase 5: Import and Validate Ratings (ongoing)

As batches complete, import and validate them.

### Validate CSV First

Before importing, check for errors:

```bash
npm run validate:csv batch-001.csv
```

**Checks:**
- Valid rating numbers (1-100 range)
- Valid JLPT (N5-N1)
- Valid URLs (if provided)
- Duplicate titles
- Missing required fields

**Fix errors** in Excel/Sheets, then revalidate.

### Import Batch

```bash
node tools/build-database.js --import-ratings batch-001.csv
node tools/build-database.js --import-ratings batch-002.csv
# ... repeat for each batch
```

### Monitor Progress

After each import, check coverage:

```bash
npm run track
```

**Output example:**
```
Total Entries: 5000

Rating Coverage:
  ✅ Both ratings: 1250 (25%)
  📚 LearnNatively only: 800 (16%)
  📖 jpdb only: 700 (14%)
  ⚠️  No ratings: 2250 (45%)

Overall: 2750 titles rated (55%)
```

### What's Good Coverage?

- **MVP:** 500+ titles with both ratings (10%)
- **Good:** 1000+ with both (20%)
- **Comprehensive:** 2500+ with both (50%)

Even 500 titles covers most popular anime!

---

## Phase 6: Enrich Metadata (Optional, 1 hour)

Add additional metadata from AniList API (genres, release dates, etc.)

```bash
# Test with 10 anime
npm run enrich:sample

# Enrich all 5000 (takes ~1 hour)
npm run enrich:all
```

**Optional step** - ratings are more important than this.

---

## Phase 7: Merge Database (1 minute)

Once ratings are imported, create the final `media-index.json`:

```bash
npm run merge
```

**What happens:**
- Sorts all entries alphabetically
- Removes duplicates
- Saves to: `media-index.json`
- Ready for deployment to extension

---

## Phase 8: Check Statistics (1 second)

```bash
npm run stats
```

**Output:**
```
Final Database (media-index.json):
   Total entries: 5000
   With both ratings: 1250 (25%)
   With LearnNatively: 2300 (46%)
   With jpdb: 2100 (42%)
   With Netflix alias: 800 (16%)
   With Crunchyroll alias: 950 (19%)
```

---

## Complete Workflow Example (Solo, ~3 weeks)

### Week 1: Setup & Extraction
```bash
npm run download      # 2 min
npm run extract       # 5 min
npm run generate-batches  # 1 min
```

### Weeks 2-3: Rating Entry
```bash
# Rate 500 anime per week (5-8 hours)
# Use Google Sheets for easier workflow
# Import each batch as completed

npm run validate:csv batch-001.csv
node tools/build-database.js --import-ratings batch-001.csv

# Check progress
npm run track
```

### End of Week 3: Finalize
```bash
# Import remaining batches
node tools/build-database.js --import-ratings batch-002.csv
# ... (repeat for all batches)

# Create final database
npm run merge

# Check final stats
npm run stats

# Deploy to extension
cp media-index.json ../jp-difficulty-overlay/
```

---

## Complete Workflow Example (Team, ~1 week)

### Day 1: Setup (30 min)
```bash
npm run download
npm run extract
npm run generate-batches
```

Share batches with team:
- Batch 1-2 → Person A
- Batch 3-4 → Person B
- Batch 5-6 → Person C
- Batch 7-8 → Person D
- Batch 9-10 → Person E

### Days 2-5: Rating (4-5 days per batch)

Each person rates their assigned batches in parallel.

**Coordination:**
- Daily standup: How many done?
- Shared spreadsheet for questions/blockers
- Validation as batches complete

```bash
# As batches come in
npm run validate:csv batch-001.csv
node tools/build-database.js --import-ratings batch-001.csv
npm run track  # Monitor progress
```

### Day 6: Finalize (1 hour)

```bash
# Import all completed batches
for i in {1..10}; do
  node tools/build-database.js --import-ratings batch-$(printf "%03d" $i).csv
done

# Merge and check
npm run merge
npm run stats
```

### Day 7: Deploy

```bash
cp media-index.json ../jp-difficulty-overlay/
# Test in Chrome extension
# Commit and push to repository
```

---

## Troubleshooting

### Import fails with "Candidates not found"

```bash
# Run extraction first
npm run extract
```

### CSV validation shows many errors

```bash
# Check the CSV file
# Common issues:
# - Wrong column names (must match exactly)
# - Invalid rating numbers (must be 1-100)
# - Unclosed quotes in titles
```

**Fix in Excel/Sheets and revalidate:**
```bash
npm run validate:csv batch-001.csv
```

### Can't find anime on LearnNatively or jpdb

- Try different spellings/abbreviations
- Check if it's a well-known title
- Use MAL/AniList ID for verification
- If not available: leave blank (partial entries OK)

### Memory issues with large files

If running out of memory:
```bash
# Process in smaller batches
node tools/generate-csv-batch.js --range A D
# Then manually process each range
```

### Want to prioritize certain titles?

Use `--range` to work on specific sections:
```bash
npm run generate-batch:range A D  # Titles starting with A-D
```

---

## Tips & Best Practices

### Team Communication
- **Async updates:** Use a shared spreadsheet for progress
- **Questions:** Collect in a Discord/Slack channel
- **Reviews:** Have someone spot-check rating accuracy

### Quality Control
```bash
npm run validate:ratings --strict  # Check completeness
npm run track:gaps                 # Identify priority areas
```

### Batch Processing
- Start with popular anime (batch-001, -002)
- These will have the best LearnNatively/jpdb coverage
- Less popular anime might have fewer sources

### Speeding Up Rating Entry
1. Use browser shortcuts (tabs, search)
2. Have a template for common ratings
3. Batch similar types (all 20-level anime together)
4. Share URLs in team channel (reuse common ones)

### Validating Your Work
```bash
# Before submitting a batch
npm run validate:csv batch-001.csv

# Check it would merge correctly
npm run validate:candidates
```

---

## Long-term Maintenance

Once you have a database:

### Monthly Tasks
- Check anime-offline-database for new releases
- Update with new popular anime
- Review for title matching issues

### Quarterly Tasks
- Update LearnNatively/jpdb URLs if they change
- Add platform aliases for new streaming services
- Remove outdated entries

### Community Contributions
- Accept PRs with new ratings
- Update CSV batches as more anime are rated
- Share rating CSVs with other projects

---

## Next Steps

1. **Start:** `npm run download`
2. **Read:** `tools/SCALING_GUIDE.md` (detailed strategies)
3. **Reference:** `tools/CURATION_GUIDE.md` (rating sources)
4. **Get help:** See `CONTRIBUTING.md` (community guidelines)

Good luck building the database! 🚀
