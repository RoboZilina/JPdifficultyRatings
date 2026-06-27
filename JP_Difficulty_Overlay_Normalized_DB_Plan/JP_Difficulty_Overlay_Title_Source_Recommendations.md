# JP Difficulty Overlay — Public Title Source Recommendations

## Purpose

This document summarizes recommended public title/alias sources for building and maintaining the private JP Difficulty Overlay normalized database.

The goal is not to mirror Netflix or Crunchyroll catalogs. The goal is to help the community identify canonical anime/media titles and collect useful aliases so that title strings detected on Netflix or Crunchyroll can be mapped to a small, local difficulty-rating entry.

The extension itself should remain simple and legal-safe:

- no scraping of Netflix
- no scraping of Crunchyroll
- no scraping of LearnNatively
- no scraping of jpdb
- no automatic fetching from public anime databases at runtime
- no copied plot summaries
- no subtitles
- no vocabulary lists
- no images
- no user viewing history

Use public title sources only for offline/admin tooling or manual research, not as runtime dependencies in the browser extension.

---

## Recommended Strategy

Use a hybrid approach:

```text
1. Start with manual entries for shows the community actually watches.
2. Let the extension capture unknown detected titles locally.
3. Let users manually add mappings and export them.
4. Review exported mappings before merging into the shared DB.
5. Use public title databases only as offline alias-suggestion sources.
6. Continue entering LearnNatively and jpdb difficulty ratings manually.
```

For MVP, seed only 20–50 titles that the community actually cares about.

For version 2, add an admin-only helper script:

```text
tools/suggest-aliases.js
```

This script can suggest aliases from approved public title datasets. A human reviewer should still approve every alias that goes into `data/media-index.json`.

---

## Best Starting Point: anime-offline-database

### What it is

The manami-project `anime-offline-database` is a JSON-based anime dataset that aggregates anime metadata and cross-references providers such as MyAnimeList, AniDB, AniList, Kitsu, Anime-Planet, AniSearch, LiveChart, and others.

It is useful because it already solves much of the anime cross-reference and alias problem.

### Why it is useful for this project

Use it for:

- candidate canonical anime titles
- English title variants
- Japanese/native title variants
- romaji title variants
- synonyms and aliases
- cross-reference IDs or URLs to anime databases
- offline alias suggestions

Do not use it for:

- copied descriptions
- images
- tags unless explicitly allowed and actually needed
- anything unrelated to title matching

### Recommended usage

Use it as an offline/admin input source, not as part of the browser extension runtime.

Recommended workflow:

```text
1. Download or reference the dataset according to its license and release process.
2. Run an admin script to search for a title.
3. Show candidate aliases to the maintainer.
4. Maintainer manually approves useful aliases.
5. Only approved title aliases are copied into data/media-index.json.
```

Do not blindly import the whole dataset into the extension.

---

## Strong Anime Alias Source: AniDB Anime Title Dumps

### What it is

AniDB provides daily updated anime title dumps intended for client-side anime search and anime-title-to-AID lookup.

AniDB explicitly warns not to request the title dump files more than once per day.

### Why it is useful for this project

Use it for:

- anime title aliases
- alternative English titles
- romaji titles
- Japanese titles
- AniDB ID lookup
- improving normalization and matching

### Recommended usage

Use AniDB title dumps only in offline/admin tooling.

Recommended rules:

```text
- cache the dump locally
- respect the once-per-day request limit
- do not call AniDB from the browser extension
- do not redistribute more than the project is allowed to redistribute
- copy only reviewed title aliases into the community DB
```

AniDB is especially useful for alias discovery, but the project should still keep its own small curated database.

---

## Useful API Source: AniList

### What it is

AniList provides a GraphQL API. Requests are made as POST requests to the AniList GraphQL endpoint, and media title fields include romaji, English, and native title variants.

### Why it is useful for this project

Use it for:

- manual title lookup
- canonical title validation
- romaji/English/native title variants
- checking whether a title is anime
- finding AniList IDs for optional cross-reference fields

### Recommended usage

AniList is good for manual lookup or an admin-only helper script.

Do not call AniList from the browser extension runtime.

Possible admin workflow:

```text
1. Maintainer enters title: Dungeon Meshi.
2. Helper script queries AniList.
3. Script shows candidate title variants.
4. Maintainer chooses aliases worth keeping.
5. Approved aliases are added to media-index.json.
```

---

## Useful API Source: MyAnimeList

### What it is

MyAnimeList has an official v2 API with anime search endpoints and field selection. Depending on usage, it may require OAuth or client-ID-based access.

### Why it is useful for this project

Use it for:

- manual title validation
- MAL ID lookup
- popular English title variants
- anime search during curation

### Recommended usage

Use MAL as a manual/admin research source.

Avoid using it directly from the Chrome extension.

Recommended rules:

```text
- respect authentication and API rules
- do not bulk import unless terms allow it
- do not copy descriptions or images
- keep only approved title aliases and optional source IDs/URLs
```

---

## Useful Secondary Source: Kitsu

### What it is

Kitsu exposes an anime API using JSON:API. It supports text filtering and pagination.

### Why it is useful for this project

Use it for:

- alternate title lookup
- anime search
- validating edge cases
- additional title variants

### Recommended usage

Kitsu is useful as a secondary source for admin tooling or manual lookup.

It is less ideal for bulk seeding because pagination limits can make full imports inconvenient.

Recommended rules:

```text
- use for lookup, not runtime extension calls
- avoid copying non-title metadata
- manually approve aliases before merging
```

---

## Useful for Netflix Non-Anime: TMDB

### What it is

TMDB is a movie and TV database with an API for movie, TV, actor, image, configuration, and translation data.

### Why it is useful for this project

TMDB is useful for Netflix content that is not anime, especially:

- Japanese live-action shows
- Japanese movies
- dramas
- general TV/movie titles
- regional title variants

### Recommended usage

Use TMDB only for admin/manual research or a separate offline helper tool.

Recommended rules:

```text
- get an API key if using the API
- follow TMDB terms and attribution requirements
- do not copy descriptions or images into this project
- copy only approved title aliases and optional source URL/ID if allowed
```

TMDB is not necessary for the anime-focused MVP, but it becomes useful if the community wants Netflix live-action Japanese media.

---

## TheTVDB

### What it is

TheTVDB is a long-running community TV and movie metadata database with an API and explicit licensing/access model.

### Why it may be useful

Use it for:

- TV-series title validation
- alternate title research
- non-anime series lookup
- cross-checking difficult Netflix matches

### Recommended usage

TheTVDB is not recommended for MVP because access/licensing may be more involved.

Use it later only if the project needs better TV-series title coverage and the community is comfortable with the licensing requirements.

---

## Source Priority Recommendation

Recommended priority for this project:

```text
1. Manual community mappings
2. anime-offline-database for anime alias suggestions
3. AniDB title dumps for anime alias suggestions
4. AniList API for manual/admin lookup
5. MyAnimeList API for manual/admin lookup
6. Kitsu API for secondary lookup
7. TMDB for Netflix non-anime / live-action content
8. TheTVDB only if needed later
```

---

## What Should Actually Go Into media-index.json

Even if public datasets contain many fields, the project DB should remain minimal.

Allowed:

```text
- canonical ID
- English title
- Japanese title
- romaji title
- aliases
- platform-observed aliases
- LearnNatively difficulty level
- LearnNatively approximate JLPT label
- LearnNatively URL
- jpdb difficulty number
- jpdb URL
- optional source IDs/URLs if license allows
```

Not allowed:

```text
- plot descriptions
- reviews
- subtitles
- dialogue
- vocabulary lists
- example sentences
- images
- tags unless explicitly approved
- episode metadata
- user data
```

---

## Recommended Admin Tooling

Create these optional helper scripts after MVP:

```text
tools/generate-normalized-index.js
tools/suggest-aliases.js
tools/validate-media-index.js
```

### generate-normalized-index.js

Reads `data/media-index.json`, normalizes all aliases, detects conflicts, and writes:

```text
data/generated-normalized-index.json
data/generated-conflicts.json
```

### suggest-aliases.js

Given a title, searches approved offline/API title sources and prints candidate aliases.

Important rule:

```text
suggest-aliases.js should suggest aliases, not directly modify media-index.json without human approval.
```

### validate-media-index.js

Checks that entries follow project rules:

```text
- required fields exist
- difficulty values are numeric or null
- URLs are valid
- aliases are not empty
- duplicate/ambiguous aliases are reported
- forbidden fields are not present
```

---

## Example Curation Workflow

```text
1. User opens Crunchyroll or Netflix.
2. Extension detects an unknown title.
3. User clicks Add local mapping.
4. User manually enters canonical title and ratings.
5. User exports local mapping.
6. Maintainer reviews mapping.
7. Maintainer optionally runs suggest-aliases.js.
8. Maintainer chooses useful aliases.
9. Entry is merged into data/media-index.json.
10. Maintainer runs generate-normalized-index.js.
11. Conflicts are reviewed.
12. New version of the private extension is shared.
```

---

## Final Recommendation

For this community extension, do not try to build a complete Netflix or Crunchyroll title catalog.

Instead:

```text
Start small.
Use manual platform observations.
Use public anime title datasets only as offline alias suggestion tools.
Keep LearnNatively and jpdb difficulty ratings manually verified.
Store only minimal title aliases, ratings, and links.
```

The best practical path is:

```text
MVP:
manual DB of 20–50 watched titles

Version 2:
anime-offline-database or AniDB-assisted alias suggestions

Version 3:
optional AniList/MAL/Kitsu/TMDB admin lookup tools
```

This keeps the project useful, maintainable, private, and legal-safe.
