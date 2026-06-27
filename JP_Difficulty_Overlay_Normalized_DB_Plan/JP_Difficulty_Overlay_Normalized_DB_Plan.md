# JP Difficulty Overlay — Normalized Database Plan

## Purpose

This document describes how to create and maintain the normalized title database for the private JP Difficulty Overlay Chrome extension.

The database is not intended to be a Netflix or Crunchyroll catalog mirror. It is a community-maintained title-resolution layer that maps titles observed on Netflix or Crunchyroll to a canonical work and its small set of learning difficulty ratings.

The database should answer one question:

> When the extension sees this title string on Netflix or Crunchyroll, which learning-difficulty entry should it map to?

The project should remain legal-safe and metadata-minimal:

- no scraping of Netflix, Crunchyroll, LearnNatively, or jpdb
- no subtitle extraction
- no copied descriptions
- no vocabulary lists
- no episode scripts
- no images
- no viewing history

---

## Core Design

Use one canonical index rather than separate Netflix, Crunchyroll, jpdb, and LearnNatively databases.

Recommended source-of-truth file:

```text
data/media-index.json
```

Each entry represents one canonical work:

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
  "aliases": [
    "bocchi the rock",
    "ぼっちざろっく",
    "btr"
  ],
  "platformAliases": {
    "crunchyroll": [
      "BOCCHI THE ROCK!",
      "Bocchi the Rock!"
    ],
    "netflix": []
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
  }
}
```

The extension should build lookup keys from:

```text
titles.en
titles.ja
titles.romaji
aliases[]
platformAliases.netflix[]
platformAliases.crunchyroll[]
seasonAliases[].aliases[]
```

---

## What Normalized Means

Normalization should handle mechanical differences between title strings:

```text
uppercase/lowercase
full-width/half-width characters
punctuation
extra whitespace
Japanese middle dot ・
season labels
sub/dub labels
episode labels
```

Normalization should not try to guess actual title equivalence. That belongs in aliases.

For example, these should be handled by aliases, not by normalization:

```text
Frieren: Beyond Journey's End
Sousou no Frieren
葬送のフリーレン
Frieren
```

---

## Recommended Schema

Use this stronger schema for human-edited entries:

```json
{
  "id": "frieren-beyond-journeys-end",
  "workType": "anime-series",
  "canonicalTitle": "Frieren: Beyond Journey's End",
  "titles": {
    "en": "Frieren: Beyond Journey's End",
    "ja": "葬送のフリーレン",
    "romaji": "Sousou no Frieren"
  },
  "aliases": [
    "frieren",
    "sousou no frieren",
    "frieren beyond journeys end",
    "葬送のフリーレン"
  ],
  "platformAliases": {
    "crunchyroll": [
      "Frieren: Beyond Journey's End"
    ],
    "netflix": [
      "Frieren: Beyond Journey's End"
    ]
  },
  "seasonAliases": [
    {
      "season": 1,
      "aliases": [
        "Frieren Season 1",
        "Frieren: Beyond Journey's End Season 1"
      ]
    }
  ],
  "ratings": {
    "learnnatively": {
      "level": 25,
      "jlptApprox": "N3",
      "url": "https://learnnatively.com/..."
    },
    "jpdb": {
      "difficulty": 20,
      "url": "https://jpdb.io/..."
    }
  },
  "metadata": {
    "status": "verified",
    "lastVerified": "2026-06-26",
    "notes": "Ratings manually entered. No scraped metadata."
  }
}
```

Metadata notes should contain only project-maintenance notes, not copied descriptions.

---

## Where Platform Aliases Come From

Platform aliases should be collected safely, not scraped.

### 1. Manual observation

A community member opens a Netflix or Crunchyroll title page and notes the title string detected by the extension.

Example:

```text
Detected title: DELICIOUS IN DUNGEON
```

Then add it to:

```json
"platformAliases": {
  "netflix": [
    "DELICIOUS IN DUNGEON"
  ]
}
```

### 2. Extension-assisted local capture

If the extension sees an unknown title, it shows:

```text
No community rating found
Detected: DELICIOUS IN DUNGEON
Add local mapping
```

The options page pre-fills the detected title, and the user manually fills the canonical mapping and ratings.

### 3. Reviewed community merge

Users export local mappings and submit them to the private repository. A reviewer checks that the entry contains only allowed minimal metadata before merging it into `media-index.json`.

---

## Recommended Data Files

Use these files:

```text
data/
├── media-index.json
├── generated-normalized-index.json
├── generated-conflicts.json
└── schema.json

tools/
└── generate-normalized-index.js
```

### Human source of truth

```text
data/media-index.json
```

This is manually edited and reviewed.

### Generated lookup

```text
data/generated-normalized-index.json
```

This is generated from all aliases and should not be hand-edited.

Example:

```json
{
  "bocchi the rock": "bocchi-the-rock",
  "btr": "bocchi-the-rock",
  "ぼっちざろっく": "bocchi-the-rock",
  "frieren": "frieren-beyond-journeys-end",
  "sousou no frieren": "frieren-beyond-journeys-end",
  "葬送のフリーレン": "frieren-beyond-journeys-end"
}
```

### Conflict report

```text
data/generated-conflicts.json
```

This lists aliases that normalize to more than one canonical work.

---

## Normalization Pipeline

Recommended normalizer:

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

Add a compact key for Japanese titles:

```js
function normalizeTitleCompact(title) {
  return normalizeTitle(title).replace(/\s+/g, "");
}
```

When building the generated lookup:

```js
function addAlias(map, alias, id) {
  const normal = normalizeTitle(alias);
  const compact = normalizeTitleCompact(alias);

  if (normal) map.set(normal, id);
  if (compact && compact !== normal) map.set(compact, id);
}
```

---

## Conflict Detection

Conflict detection is mandatory.

Example conflict:

```text
monster
```

could refer to:

```text
Monster
Monster Hunter
Monster Strike
```

The generator should output:

```json
{
  "key": "monster",
  "ids": [
    "monster",
    "monster-hunter"
  ]
}
```

For ambiguous keys:

- do not include them automatically in the generated lookup
- require more specific aliases
- add conflict to generated-conflicts.json

Good specific aliases:

```json
[
  "monster anime",
  "naoki urasawa monster",
  "モンスター"
]
```

Bad overly generic aliases:

```json
[
  "anime",
  "journey",
  "end"
]
```

---

## Example media-index.json Entries

```json
[
  {
    "id": "delicious-in-dungeon",
    "workType": "anime-series",
    "canonicalTitle": "Delicious in Dungeon",
    "titles": {
      "en": "Delicious in Dungeon",
      "ja": "ダンジョン飯",
      "romaji": "Dungeon Meshi"
    },
    "aliases": [
      "delicious in dungeon",
      "dungeon meshi",
      "ダンジョン飯"
    ],
    "platformAliases": {
      "netflix": [
        "DELICIOUS IN DUNGEON",
        "Delicious in Dungeon"
      ],
      "crunchyroll": []
    },
    "ratings": {
      "learnnatively": {
        "level": null,
        "jlptApprox": "",
        "url": ""
      },
      "jpdb": {
        "difficulty": null,
        "url": ""
      }
    },
    "metadata": {
      "status": "needs-rating",
      "lastVerified": "",
      "notes": "Title aliases only. Ratings not yet filled."
    }
  },
  {
    "id": "bocchi-the-rock",
    "workType": "anime-series",
    "canonicalTitle": "Bocchi the Rock!",
    "titles": {
      "en": "Bocchi the Rock!",
      "ja": "ぼっち・ざ・ろっく！",
      "romaji": "Bocchi the Rock"
    },
    "aliases": [
      "bocchi the rock",
      "btr",
      "ぼっちざろっく",
      "ぼっち ざ ろっく"
    ],
    "platformAliases": {
      "netflix": [],
      "crunchyroll": [
        "BOCCHI THE ROCK!",
        "Bocchi the Rock!"
      ]
    },
    "ratings": {
      "learnnatively": {
        "level": 20,
        "jlptApprox": "N3",
        "url": "https://learnnatively.com/"
      },
      "jpdb": {
        "difficulty": 7,
        "url": "https://jpdb.io/"
      }
    },
    "metadata": {
      "status": "verified",
      "lastVerified": "2026-06-26",
      "notes": "Minimal difficulty metadata only."
    }
  }
]
```

---

## Generator Script Behavior

The generator should:

1. Read `data/media-index.json`.
2. Validate every entry.
3. Collect aliases from:
   - `canonicalTitle`
   - `titles.en`
   - `titles.ja`
   - `titles.romaji`
   - `aliases[]`
   - `platformAliases.netflix[]`
   - `platformAliases.crunchyroll[]`
   - `seasonAliases[].aliases[]`
4. Normalize each alias.
5. Generate compact variants.
6. Detect conflicts.
7. Output `data/generated-normalized-index.json`.
8. Output `data/generated-conflicts.json`.
9. Warn or fail the build if conflicts exist.

---

## Should We Include Platform IDs?

Not for MVP.

Netflix and Crunchyroll URLs may contain internal IDs, but relying on them makes the data model more platform-specific and may be brittle.

For MVP, prefer visible title aliases.

Possible future field:

```json
"platformIds": {
  "netflix": [
    "81231974"
  ],
  "crunchyroll": [
    "GY8VEQ95Y"
  ]
}
```

Do not start with this unless title matching proves insufficient.

---

## Community Data-Entry Workflow

### Step 1: User opens title page

Extension detects:

```text
Detected title: DELICIOUS IN DUNGEON
```

### Step 2: No match found

Extension shows:

```text
No community rating found
Add local mapping
```

### Step 3: User manually creates mapping

They fill:

```text
Canonical title: Delicious in Dungeon
Japanese title: ダンジョン飯
Romaji: Dungeon Meshi
Platform alias: DELICIOUS IN DUNGEON
```

Then they manually check LearnNatively and jpdb and enter only:

```text
difficulty number
URL
```

### Step 4: Export local mappings

The user exports:

```text
jp-difficulty-local-mappings.json
```

### Step 5: Reviewer merges into shared DB

Reviewer verifies:

```text
only title aliases, ratings, links
no copied metadata
no subtitles
no vocabulary lists
no images
```

### Step 6: Generate normalized index

Run:

```bash
node tools/generate-normalized-index.js
```

---

## Runtime Lookup

At runtime, the extension should do:

```js
const detectedTitle = extractCurrentTitle();
const key = normalizeTitle(detectedTitle);
const compactKey = normalizeTitleCompact(detectedTitle);

const id =
  normalizedIndex[key] ||
  normalizedIndex[compactKey];

const item = id
  ? mediaItemsById[id]
  : null;
```

Local user mappings can be converted into an in-memory lookup on startup.

---

## Candidate Public Title Sources

These are not Netflix or Crunchyroll catalog sources. They are possible anime title/alias sources for a separate offline seeding tool or for manual research.

Important: before importing any source wholesale, check its license and terms. For this project, the safest rule is to use external lists only as a research aid or as a separately attributed/imported optional dataset, not as copied hidden data without review.

### Recommended source: anime-offline-database

The manami-project anime-offline-database is a JSON-based anime dataset that aggregates anime metadata and cross-references providers such as MyAnimeList, AniDB, AniList, Kitsu, and others. It is useful because it already solves the cross-reference and alias problem better than starting from scratch.

Use it for:

- candidate canonical titles
- synonyms/aliases
- source URLs to AniList/MAL/Kitsu/AniDB
- matching assistance

Do not use it for:

- copied descriptions
- images
- tags unless you explicitly decide the license and scope allow it

Recommendation:

- best source for anime alias seeding
- keep it as an offline developer tool input
- import only title aliases and source IDs/URLs that you are allowed to use
- document attribution and license compliance

### Useful source: AniDB anime-titles dump

AniDB provides daily updated anime title dumps intended for client-side anime search and AID lookups. It explicitly says not to request the files more than once per day.

Use it for:

- aliases
- Japanese/English/romaji title variants
- AniDB ID lookup

Recommendation:

- good for title normalization research
- respect the once-per-day limit
- cache locally
- check AniDB usage rules before redistribution

### Useful API: AniList

AniList provides a GraphQL API. GraphQL requests are made as POST requests to `https://graphql.anilist.co`, and media title fields include romaji, English, and native title variants.

Use it for:

- searching individual anime
- title aliases
- canonical IDs
- source URLs

Recommendation:

- good for lookup during manual mapping or private tooling
- do not call it from the browser extension
- use it only in a developer/admin import tool if allowed by API rules

### Useful API: MyAnimeList

MyAnimeList has an official v2 API with anime search endpoints and field selection. It may need OAuth or client-ID based access depending on endpoint and usage.

Use it for:

- manual title validation
- MAL IDs
- title variants

Recommendation:

- good for manual lookup or admin tooling
- less convenient as a bulk source unless API terms and pagination are handled carefully

### Useful API: Kitsu

Kitsu exposes an anime API via JSON:API, including text filtering, pagination, and title discovery.

Use it for:

- alternate titles
- API-based search
- title matching research

Recommendation:

- useful secondary source
- max page size and pagination make it less convenient for full database import

### Useful non-anime/general media API: TMDB

TMDB is a community movie and TV database with API support for movie and TV metadata. It can help with Netflix items that are not anime or that are better represented as live-action TV/movies.

Use it for:

- general TV/movie title lookup
- Netflix live-action Japanese shows
- alternate regional titles

Recommendation:

- useful for Netflix, especially non-anime Japanese content
- requires API key and terms compliance
- do not include descriptions/images unless the project scope and license/attribution supports it

### TheTVDB

TheTVDB is a long-running community TV/movie metadata database with an API and licensing model.

Use it for:

- TV series title validation
- alternative title research

Recommendation:

- useful but licensing/access may be more involved
- not the first choice for MVP

---

## Practical Recommendation for This Project

Use a hybrid approach:

```text
1. Start with manual entries for shows the community actually watches.
2. Add extension-assisted local mapping and export.
3. Use anime-offline-database or AniDB title dumps only as offline admin tooling to suggest aliases.
4. Never auto-show imported ratings from these sources because the extension rating sources are LearnNatively and jpdb only.
5. Continue to enter LearnNatively/jpdb ratings manually.
```

For the MVP, seed only 20–50 titles that the community cares about.

For version 2, add an admin-only helper script:

```text
tools/suggest-aliases.js
```

The script can take a canonical title and suggest aliases from allowed public datasets. A human reviewer still approves what goes into `media-index.json`.

---

## Final Recommendation

Implement the normalized database in three layers:

```text
1. data/media-index.json
   Human-edited source of truth.

2. data/generated-normalized-index.json
   Generated lookup from all known aliases.

3. chrome.storage.local userMappings
   Personal local overrides, exportable back to the community DB.
```

The core workflow should be:

```text
extension detects title
→ normalize title
→ lookup generated index
→ if not found, allow manual mapping
→ export and review local mappings
→ merge into media-index.json
→ regenerate normalized index
```

This keeps the system maintainable, private, legal-safe, and practical.
