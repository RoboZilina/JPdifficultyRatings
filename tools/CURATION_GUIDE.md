# JP Difficulty Overlay - Database Curation Guide

This guide explains how to build and maintain the `media-index.json` database from external sources.

## Overview

The database is built using a **three-step workflow**:

1. **Fetch** — Fetch popular anime titles from anime-offline-database
2. **Rate** — Add difficulty ratings from LearnNatively and jpdb
3. **Merge** — Convert into final media-index.json

## Step 1: Fetch Seed Titles

The script fetches popular anime titles that the community actually watches.

```bash
node tools/build-media-index.js --fetch
```

This creates `data/candidates.json` with 40+ popular anime titles and their aliases extracted from anime-offline-database.

**What gets created:**
- Canonical English title
- Japanese title (if available)
- Romaji title (if available)
- Aliases for matching
- Platform-specific aliases (from anime-offline-database)

**Example output:**
```json
{
  "id": "bocchi-the-rock",
  "canonicalTitle": "Bocchi the Rock!",
  "titles": {
    "en": "Bocchi the Rock!",
    "ja": "ぼっち・ざ・ろっく！",
    "romaji": "Bocchi the Rock"
  },
  "aliases": ["bocchi the rock", "ぼっち ざ ろっく"],
  "platformAliases": {
    "netflix": [],
    "crunchyroll": ["BOCCHI THE ROCK!"]
  },
  "ratings": {
    "learnnatively": { "level": null, "jlptApprox": "", "url": "" },
    "jpdb": { "difficulty": null, "url": "" }
  }
}
```

## Step 2: Add Difficulty Ratings

The ratings must be added **manually** by researching on LearnNatively and jpdb.

### Option A: Use CSV Template (Recommended)

A pre-filled CSV template is provided with popular anime and their ratings:

```bash
# Edit the template
nano tools/RATINGS_TEMPLATE.csv
```

The CSV has these columns:
- `Canonical Title` — English title
- `LearnNatively Level` — 1-60+ (difficulty level)
- `LearnNatively JLPT` — N5/N4/N3/N2/N1 (approximate)
- `LearnNatively URL` — Direct link to the series on LearnNatively
- `jpdb Difficulty` — 1-100 (difficulty number)
- `jpdb URL` — Direct link to the series on jpdb
- `Netflix Alias` — As seen on Netflix (e.g., "BOCCHI THE ROCK!")
- `Crunchyroll Alias` — As seen on Crunchyroll
- `Notes` — Any additional info (genre, type, etc.)

**Example row:**
```csv
"Bocchi the Rock!",20,N3,https://learnnatively.com/search?q=bocchi,7,https://jpdb.io/search?q=bocchi,"BOCCHI THE ROCK!","BOCCHI THE ROCK!","Popular music comedy"
```

### Option B: Manual JSON Editing

You can also directly edit `data/candidates.json`:

```json
{
  "id": "bocchi-the-rock",
  "ratings": {
    "learnnatively": {
      "level": 20,           // ← Add the level
      "jlptApprox": "N3",    // ← Add JLPT approx
      "url": "https://..."   // ← Add LearnNatively link
    },
    "jpdb": {
      "difficulty": 7,       // ← Add difficulty
      "url": "https://..."   // ← Add jpdb link
    }
  }
}
```

### How to Find Ratings

**LearnNatively:**
1. Visit https://learnnatively.com/
2. Search for the anime title
3. Note the **Level** (shown in the series card)
4. Note the **JLPT Approx** (shown under the level)
5. Copy the series URL

**jpdb:**
1. Visit https://jpdb.io/
2. Search for the anime title
3. Click on the series
4. Note the **Difficulty** number (shown prominently)
5. Copy the series URL

## Step 3: Convert CSV to JSON

Once you've filled in the CSV with ratings:

```bash
node tools/csv-to-media-index.js tools/RATINGS_TEMPLATE.csv
```

This creates `media-index.json` with all the properly formatted entries.

## Step 4: Validate

Validate the final database:

```bash
node tools/build-media-index.js --validate
```

This checks:
- All required fields are present
- No duplicate IDs
- IDs are properly formatted (lowercase-with-hyphens)
- Valid JSON structure
- Statistics (how many have ratings, etc.)

## Workflow Summary

```bash
# 1. Fetch seed titles
node tools/build-media-index.js --fetch

# 2. Edit the CSV template
nano tools/RATINGS_TEMPLATE.csv
# (Add LearnNatively and jpdb ratings)

# 3. Convert CSV to JSON
node tools/csv-to-media-index.js tools/RATINGS_TEMPLATE.csv

# 4. Validate
node tools/build-media-index.js --validate

# 5. Update the extension
# Copy media-index.json into the extension folder
cp media-index.json path/to/jp-difficulty-overlay/
```

## Adding More Titles

To expand the database with new titles:

### Method 1: Fetch More from anime-offline-database

Edit `build-media-index.js` and add titles to `CONFIG.seedTitles`:

```javascript
seedTitles: [
  'Bocchi the Rock!',
  'Your New Title Here',  // ← Add here
  'Another Title'
]
```

Then run:
```bash
node tools/build-media-index.js --fetch
```

### Method 2: Manually Add to CSV

Add a new row to `RATINGS_TEMPLATE.csv` and re-run the converter:

```bash
node tools/csv-to-media-index.js tools/RATINGS_TEMPLATE.csv
```

## Data Quality Rules

When curating the database, follow these rules:

### Titles
- ✅ Use the **official English title** from the source
- ✅ Include **Japanese title** if available
- ✅ Include **romaji** if available
- ❌ Don't use alternate titles as the canonical title

### Aliases
- ✅ Include common variations (abbreviations, alternate romanizations)
- ✅ Include both with and without punctuation
- ✅ Include both English and Japanese variants
- ❌ Don't include single-word generic terms ("adventure", "school")
- ❌ Don't include misspellings

### Platform Aliases
- ✅ Add **exact titles as seen** on Netflix
- ✅ Add **exact titles as seen** on Crunchyroll
- ❌ Don't modify or normalize these — they need to match exactly

### Ratings
- ✅ Use the **exact level number** from LearnNatively
- ✅ Use the **exact difficulty number** from jpdb
- ✅ Include the **JLPT approximation** from LearnNatively
- ❌ Don't guess or estimate
- ❌ Don't modify ratings — use what the source shows

## Database Statistics

Target database size for MVP:
- **Minimum:** 20–50 titles
- **Good:** 100+ titles
- **Comprehensive:** 500+ titles

## Maintenance

To keep the database current:

1. **Monthly:** Check if new popular anime need to be added
2. **Quarterly:** Review for title matching issues
3. **As needed:** Update ratings if LearnNatively/jpdb change them

## Example: Adding "Jujutsu Kaisen"

Here's a complete example of adding a title:

### 1. Find on anime-offline-database
The title is already in the seed list, so it will be fetched.

### 2. Research on LearnNatively
- Visit: https://learnnatively.com/search?q=jujutsu
- Find "Jujutsu Kaisen" series
- Note: **Level 20**, **JLPT N3**
- Copy URL: `https://learnnatively.com/...`

### 3. Research on jpdb
- Visit: https://jpdb.io/search?q=jujutsu
- Click on "Jujutsu Kaisen"
- Note: **Difficulty 13**
- Copy URL: `https://jpdb.io/...`

### 4. Add to CSV
```csv
"Jujutsu Kaisen",20,N3,https://learnnatively.com/...,13,https://jpdb.io/...,"JUJUTSU KAISEN","JUJUTSU KAISEN","Action supernatural"
```

### 5. Convert
```bash
node tools/csv-to-media-index.js tools/RATINGS_TEMPLATE.csv
```

Done! The entry is now in media-index.json.

## Troubleshooting

### "Title not found on LearnNatively"
Some niche anime might not be on LearnNatively. In this case:
- Try alternate titles
- Use a broad JLPT approximation based on the jpdb difficulty
- Leave the LearnNatively level as null

### "Difficulty mismatch between sources"
LearnNatively and jpdb use different scales:
- **LearnNatively:** 1–60+ (relative difficulty)
- **jpdb:** 1–100 (absolute frequency ranking)

Both are valid — include both values.

### "CSV not parsing"
Make sure:
- Titles with commas are quoted: `"A, B, C"`
- Quotes inside quotes are doubled: `"He said ""hello"""`
- URLs are properly quoted if they contain special characters

## Contributing

To contribute new titles or ratings:

1. Fork the extension repository
2. Edit `tools/RATINGS_TEMPLATE.csv`
3. Add ratings and platform aliases
4. Run validation
5. Submit a pull request

See `CONTRIBUTING.md` for more details.
