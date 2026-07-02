# JP Difficulty Overlay

A private Chrome extension for adding Japanese-learning difficulty ratings to Netflix and Crunchyroll pages.

## Purpose

This extension displays a small overlay showing locally stored Japanese difficulty ratings for media titles on Netflix and Crunchyroll.

It uses a local community-maintained JSON index and optional user-created local mappings, with no external API calls or scraping.

## Features

✅ Shows LearnNatively difficulty levels and JLPT approximations  
✅ Shows jpdb difficulty ratings  
✅ Direct links to LearnNatively and jpdb for detailed info  
✅ Add local mappings for titles not yet in the community database  
✅ Export/import local mappings to share with the community  
✅ No scraping, no external API calls, fully local and private  

## Supported Sites

- **Netflix** (`netflix.com`)
- **Crunchyroll** (`crunchyroll.com`)

## What Gets Displayed

When a title is found in the database, the overlay shows:

```
日本語 Difficulty
LearnNatively: 20 / N3
jpdb: 7 / 100

[LearnNatively] [jpdb]
```

If a title is not found:

```
日本語 Difficulty
No community rating found
Detected: [Title]

[Search LearnNatively] [Search jpdb]
[Add local mapping]
```

## Privacy & Legal Scope

This extension is **fully local and private**. It does not phone home, track users, or collect any data.

### Runtime Behavior (What the extension does at all times)

- ✅ Reads a local bundled `media-index.json` file
- ✅ Reads optional user-created local mappings from Chrome local storage
- ✅ Opens outbound links only when the user clicks them (to LearnNatively or jpdb)
- ✅ Zero network activity from the extension itself — no runtime API calls, no analytics, no telemetry

### What We Do NOT Do (Legal Guardrails)

- ✅ Does NOT scrape Netflix or Crunchyroll pages, content, or subtitles
- ✅ Does NOT download or read video data, subtitles, or audio tracks
- ✅ Does NOT store or transmit viewing history, account info, or personal data
- ✅ Does NOT mirror or redistribute Netflix or Crunchyroll catalogs
- ✅ Does NOT run external API calls from the browser extension
- ✅ Does NOT inject ads, trackers, or analytics

---

## Data Rules

### What Is Stored in the Database

Only minimal metadata is stored in `media-index.json`:

- Title names (English, Japanese, romaji)
- Common aliases for matching
- LearnNatively difficulty levels and JLPT approximations
- jpdb difficulty scores
- Links to LearnNatively and jpdb detail pages

### What Is NEVER Stored

- ❌ Subtitles, dialogue, or scripts
- ❌ Vocabulary lists, example sentences, or studied words
- ❌ Copied descriptions, plot summaries, or reviews
- ❌ Images, posters, or screenshots
- ❌ Episode metadata, season details, or deck contents
- ❌ User viewing history or account data
- ❌ Netflix or Crunchyroll catalog dumps
- ❌ Copyrighted material of any kind

---

## How the Database Was Built (Data Pipeline)

The current `media-index.json` (5,820 entries) was built using a one-time, offline batch process. All tools are in `jp-difficulty-overlay/tools/`. The pipeline is never called from the browser extension.

| Phase | Tool Script | Source | What It Contributed |
|-------|-------------|--------|---------------------|
| 1. Title seeding | `fetch-anime-offline-db.py` | [anime-offline-database](https://github.com/manami-project/anime-offline-database) (MIT license) | 10,000+ anime titles, English/Japanese/romaji names, aliases, cross-reference IDs |
| 2. jpdb ratings | `fetch-jpdb-ratings.py` | jpdb.io public anime difficulty list pages | Difficulty scores (1–100 scale) for ~1,399 anime titles |
| 3. TMDB enrichment | `fetch-tmdb-netflix.py`, `build-rated-db.py` | [TMDB API](https://www.themoviedb.org/documentation/api) (requires API key, attribution required) | Non-anime Japanese live-action titles and platform aliases for Netflix |
| 4. LearnNatively ratings | `fetch-ln-*.py` (catalog, ratings, videos, all-pages, etc.) | LearnNatively public API endpoints | Difficulty levels (L0–40+), JLPT approximations, and Japanese/English titles for 5,000+ entries |
| 5. Merge & build | `build-merged-db.py` | All of the above | Final `media-index.json` — merged, deduplicated, normalized, cross-referenced |

All sources are queried at build time only. No external data is fetched at extension runtime.

### Source License Compliance

- **anime-offline-database** — MIT license. We credit manami-project and retain the `sources` field for cross-references.
- **TMDB API** — Used with attribution. TMDB data is for title/alias enrichment only, never for difficulty ratings.
- **jpdb & LearnNatively** — Publicly accessible pages and endpoints. No APIs were reverse-engineered. Data is used for difficulty referencing only.

### What the Pipeline Does NOT Do

- ❌ No scraping of Netflix or Crunchyroll content or subtitles
- ❌ No scraping of jpdb or LearnNatively — only public endpoints/difficulty lists
- ❌ No automated import of ratings from any source — all data is reviewed and constrained by the build script
- ❌ No storing of copyrighted content, images, descriptions, or episode data

## Installation

1. Clone or download this repository
2. Open Chrome and go to `chrome://extensions`
3. Enable **Developer Mode** (toggle in top right)
4. Click **Load unpacked**
5. Select the `jp-difficulty-overlay` folder
6. The extension is now installed!

Open Netflix or Crunchyroll and you should see the overlay on title pages.

## Setting Up on a New PC

A 3-step guide to get the extension running on any computer — no tools or API keys needed.

### 1. Get the files

```bash
git clone https://github.com/RoboZilina/JPdifficultyRatings.git
```

Or copy the `jp-difficulty-overlay` folder from another PC via USB/cloud.

> ⚠️ Keep it as a folder — Chrome cannot load zipped extensions.

### 2. Install

1. Open Chrome and go to **`chrome://extensions`**
2. Enable **Developer Mode** (top-right toggle)
3. Click **Load unpacked** → select the `jp-difficulty-overlay` folder

### 3. Verify

Open **Netflix** or **Crunchyroll** and navigate to a title page. The overlay appears near the title area.

**No overlay?** You might be on a browse/search page — click into a specific title. For other issues, see [SETUP.md](SETUP.md).

All titles, ratings, and data are bundled in the extension — no internet connection needed after installation.

## Local Mappings

### Adding a Mapping

If a title is not found in the community database:

1. Click **Add local mapping** on the overlay
2. Fill in the mapping details (titles, aliases, ratings, URLs)
3. Click **Save Local Mapping**
4. The mapping is saved locally and will appear on that title from now on

### Exporting Mappings

To share your local mappings with the community:

1. Go to the extension **Options** page (right-click extension icon → Options)
2. Scroll to **My Local Mappings**
3. Click **Export as JSON**
4. Share the downloaded JSON file with the community for review

### Importing Mappings

To restore or merge mappings:

1. Go to the extension **Options** page
2. Scroll to **Import Mappings**
3. Paste JSON (from an export or community submission)
4. Click **Import Mappings**

## Updating the Community Database

Edit `media-index.json` directly to add or update entries. The schema follows this structure:

```json
{
  "id": "bocchi-the-rock",
  "workType": "anime-series",
  "canonicalTitle": "Bocchi the Rock!",
  "titles": {
    "en": "Bocchi the Rock!",
    "ja": "ぼっち・ざ・ろっく！",
    "romaji": "Bocchi the Rock"
  },
  "aliases": ["bocchi the rock", "btr"],
  "platformAliases": {
    "netflix": [],
    "crunchyroll": ["BOCCHI THE ROCK!", "Bocchi the Rock!"]
  },
  "ratings": {
    "learnnatively": {
      "level": 20,
      "jlptApprox": "N3",
      "url": "https://learnnatively.com/..."
    },
    "jpdb": {
      "difficulty": 7,
      "url": "https://jpdb.io/..."
    }
  },
  "metadata": {
    "status": "verified",
    "lastVerified": "2026-06-26",
    "notes": "Minimal difficulty metadata only."
  }
}
```

Keep entries minimal. Include only what's necessary for matching and rating.

## How It Works

1. **Title Detection** - When you open a Netflix or Crunchyroll page, the extension detects the current title
2. **Normalization** - The title is normalized (lowercased, punctuation removed, etc.)
3. **Matching** - The normalized title is searched against the local index
4. **Overlay** - If a match is found, difficulty ratings are displayed; if not, a fallback UI is shown
5. **Local Storage** - User mappings are saved locally in Chrome storage and merged with the community database

## Building the Database (5000+ Titles)

The extension comes with a sample database (3 titles). Use the comprehensive tools to build a 5000+ title database with difficulty ratings.

### Quick Start (3 commands)

```bash
# 1. Download 10,000+ anime from anime-offline-database
npm run download

# 2. Extract and organize top 5,000 into CSV batches
npm run extract
npm run generate-batches

# 3. After adding ratings → Merge and deploy
npm run validate:csv batch-001.csv
node tools/build-database.js --import-ratings batch-001.csv
npm run merge
```

### Complete Workflow

See **[tools/WORKFLOW.md](tools/WORKFLOW.md)** for step-by-step instructions:
- Phase 1: Download (1-2 min)
- Phase 2: Extract (5 min)
- Phase 3: Generate CSV batches (1 min)
- Phase 4: Rate anime (50+ hours, team distributed)
- Phase 5: Import and validate
- Phase 6: Merge final database (1 min)
- Phase 7: Deploy to extension

**Time estimate:** 
- **Solo:** 3-4 weeks
- **Team of 5:** 1 week
- **MVP (500 titles):** 2-3 days

### All Commands

```bash
npm run download           # Download anime-offline-database
npm run extract           # Extract 5000 anime
npm run generate-batches  # Split into CSV batches
npm run generate-batch:range A D  # Generate specific range
npm run track            # Show coverage statistics
npm run track:gaps       # Find ratings gaps
npm run validate:csv     # Validate a CSV batch
npm run validate:candidates  # Validate all candidates
npm run merge            # Create final media-index.json
npm run stats            # Show database statistics
npm run enrich:sample    # Enrich metadata with AniList (optional)
npm run help             # Show all available commands
```

### Database Structure

```
Phase 1-2: Download & Extract
├── anime-offline-database.json (10,000+ anime from GitHub)
└── extracted-candidates.json (5,000 filtered, most popular)

Phase 3: Generate Batches
├── batch-001.csv (500 anime)
├── batch-002.csv (500 anime)
├── ...
└── batch-010.csv (final 500)

Phase 4: Rate (Human work)
├── (Edit CSVs with LearnNatively & jpdb ratings)
└── (Add Netflix/Crunchyroll platform aliases)

Phase 5: Import & Merge
└── media-index.json (final 5000 anime with ratings)
```

### Database Sources

- **anime-offline-database** - 10,000+ anime with aliases (public GitHub)
- **LearnNatively** - Difficulty levels 1-60+ (manual entry required)
- **jpdb** - Vocab difficulty 1-100 (manual entry required)
- **Netflix/Crunchyroll** - Platform aliases (manual mapping)

See [tools/DATA_PIPELINE.md](tools/DATA_PIPELINE.md) for the **real pipeline** that was used to build the current 5,820-entry database, or [tools/CURATION_GUIDE.md](tools/CURATION_GUIDE.md) and [tools/SCALING_GUIDE.md](tools/SCALING_GUIDE.md) for the aspirational community workflow.

## Development

The extension uses plain JavaScript, HTML, and CSS with no frameworks or bundlers.

File structure:

```
jp-difficulty-overlay/
├── manifest.json              # Chrome extension configuration
├── content.js                 # Title detection and overlay logic
├── styles.css                 # Overlay styling
├── media-index.json           # Community title database
├── options.html               # Settings page
├── options.js                 # Settings page logic
├── package.json               # Node.js tools configuration
├── README.md                  # This file
├── CONTRIBUTING.md            # Contribution guidelines
├── tools/
│   ├── build-media-index.js   # Fetch and validate database
│   ├── csv-to-media-index.js  # Convert CSV to JSON
│   ├── CURATION_GUIDE.md      # Database curation workflow
│   └── RATINGS_TEMPLATE.csv   # Pre-filled anime ratings template
└── data/
    └── (generated during curation)
```

## Notes

- This is a **private community extension** designed for a small group
- It is installed manually as an **unpacked extension**, not from the Chrome Web Store
- The goal is simplicity, privacy, and local-only operation
- Keep the database small and focused (20-100 titles for MVP)
- Do not try to mirror Netflix or Crunchyroll catalogs

## License & Attribution

This project intentionally keeps external dependencies minimal to remain practical and maintainable for a community.

## Support & Questions

Contact the community maintainers for questions about data accuracy, issues, or feature requests.

---

**Enjoy learning Japanese!** 日本語を頑張って！🇯🇵
