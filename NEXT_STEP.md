# Next Step: Build the Title Database

## What We're Doing Right Now
Build the list of anime/movies/shows from **anime-offline-database** only.

## Why Only This Source
- MIT license — free to use and redistribute
- Already aggregates AniList, MyAnimeList, AniDB, Kitsu data
- Single file, single download, single JSON parse
- Has everything we need: titles, Japanese titles, romaji, synonyms, type (TV/Movie/OVA), and cross-reference IDs

## Plan for Step 1
1. Create `tools/fetch-anime-offline-db.js` — downloads the JSON file, filters by type (TV, Movie, OVA, ONA), maps fields into our schema, outputs candidates
2. Run it → produces `data/candidates.json` with 5000+ entries
3. Review what we got

## What Each Entry Will Look Like
```json
{
  "id": "bocchi-the-rock",
  "workType": "anime-series",
  "titles": {
    "en": "Bocchi the Rock!",
    "ja": "",
    "romaji": ""
  },
  "aliases": [
    "bocchi the rock",
    "ぼっちざろっく",
    "btr"
  ],
  "externalIds": {
    "anilist": 101921,
    "myanimelist": 40748,
    "anidb": 14227,
    "kitsu": 12345
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
  }
}
```

## Not Yet
- Difficulty ratings (jpdb/LearnNatively) — that's step 2
- Platform aliases (Netflix/Crunchyroll exact strings) — that's step 3 after we figure out matching

## Ready?
Once you say go, I'll create the fetch script and run it.