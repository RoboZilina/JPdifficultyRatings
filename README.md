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

This extension:

- ✅ Does NOT scrape Netflix or Crunchyroll
- ✅ Does NOT scrape LearnNatively or jpdb
- ✅ Does NOT fetch from external sites
- ✅ Does NOT download subtitles
- ✅ Does NOT read or store video data
- ✅ Does NOT store viewing history
- ✅ Does NOT collect personal data

It only uses:

- A local bundled `media-index.json` file
- Optional user-created local mappings stored in Chrome local storage
- Normal user-initiated outbound links

## Data Rules

**Allowed in the database:**

- Title names (English, Japanese, romaji)
- Aliases for matching
- LearnNatively difficulty ratings and JLPT approximations
- jpdb difficulty ratings
- Links to LearnNatively and jpdb

**Not allowed:**

- Subtitles
- Dialogue or scripts
- Vocabulary lists or example sentences
- Copied descriptions or plot summaries
- Images, posters, or screenshots
- Episode metadata or deck contents
- User viewing history or account data

## Installation

1. Clone or download this repository
2. Open Chrome and go to `chrome://extensions`
3. Enable **Developer Mode** (toggle in top right)
4. Click **Load unpacked**
5. Select the `jp-difficulty-overlay` folder
6. The extension is now installed!

Open Netflix or Crunchyroll and you should see the overlay on title pages.

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

## Building the Database

The extension comes with a small sample database (3 titles). To expand it with hundreds of anime, use the curation tools:

### Quick Start

```bash
# 1. Fetch popular anime from anime-offline-database
npm run fetch

# 2. Edit tools/RATINGS_TEMPLATE.csv and add LearnNatively & jpdb ratings
nano tools/RATINGS_TEMPLATE.csv

# 3. Convert CSV to media-index.json
npm run build

# 4. Validate the database
npm run validate
```

For detailed instructions, see [tools/CURATION_GUIDE.md](tools/CURATION_GUIDE.md).

### Database Sources

The curation workflow uses these public sources:

- **anime-offline-database** - Title aliases and metadata
- **LearnNatively** - Japanese difficulty levels (manual entry)
- **jpdb** - Kanji/vocab difficulty numbers (manual entry)

See the [Title Source Recommendations](JP_Difficulty_Overlay_Title_Source_Recommendations.md) document for details on all available sources.

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
