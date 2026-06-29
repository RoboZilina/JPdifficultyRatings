#!/usr/bin/env python3
"""
JP Difficulty Overlay - Fetch anime-offline-database

Downloads the full anime-offline-database (~50MB JSON, MIT license),
filters to anime types we care about (TV, Movie, OVA, ONA, Special),
and extracts titles, aliases, and external IDs into our schema.

Usage:
    python tools/fetch-anime-offline-db.py
    python tools/fetch-anime-offline-db.py --limit 100   # test with 100 entries
"""

import json
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

# ============================================================================
# Config
# ============================================================================

# Use the latest release download (the old monolithic JSON is no longer on raw.githubusercontent.com)
# Latest release format: per-source minified JSON + JSONL combined format
# We use the combined anime-offline-database-minified.json for simplicity
ANIME_DB_URL = "https://github.com/manami-project/anime-offline-database/releases/download/2026-14/anime-offline-database-minified.json"
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / "candidates.json"

# Anime types we want to include
INCLUDE_TYPES = {"TV", "Movie", "OVA", "ONA", "Special"}

# Map their type strings to our workType values
TYPE_MAP = {
    "TV": "anime-series",
    "Movie": "anime-movie",
    "OVA": "anime-ova",
    "ONA": "anime-ona",
    "Special": "anime-special",
}

# Generic words to filter from aliases (prevent conflicts like "monster")
GENERIC_WORDS = {
    "anime", "movie", "film", "series", "tv", "special", "ova", "ona",
    "the", "a", "an", "in", "of", "and", "to", "for", "is", "it",
    "hero", "monster", "love", "world", "story", "tale", "chronicle",
    "legend", "saga", "war", "kingdom", "school", "city", "time",
}

# ============================================================================
# Helpers
# ============================================================================


def fetch_json(url):
    """Download JSON from URL with progress indication."""
    print(f"\nDownloading: {url}")
    print("(File is ~50MB, may take a moment...)")

    req = urllib.request.Request(url, headers={"User-Agent": "JP-Difficulty-Overlay/1.0"})
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise Exception(f"HTTP {response.status}: {response.reason}")

        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunks = []

        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded * 100 // total
                mb = downloaded / (1024 * 1024)
                sys.stdout.write(f"\r  Downloaded {mb:.0f} MB ({pct}%)...")
                sys.stdout.flush()

        sys.stdout.write(f"\r  Downloaded {downloaded / (1024 * 1024):.1f} MB total.\n")
        data = b"".join(chunks)
        return json.loads(data.decode("utf-8"))


def slugify(text):
    """Convert text to url-safe id."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


def extract_external_ids(sources):
    """Extract external IDs from sources array.
    
    Format: ["https://anilist.co/anime/142051", "https://myanimelist.net/anime/40748", ...]
    """
    ids = {}
    if not isinstance(sources, list):
        return ids

    for source_url in sources:
        # anilist.co/anime/142051
        match = re.search(r"anilist\.co/anime/(\d+)", source_url)
        if match:
            ids["anilist"] = int(match.group(1))
            continue
        
        # myanimelist.net/anime/40748
        match = re.search(r"myanimelist\.net/anime/(\d+)", source_url)
        if match:
            ids["mal"] = int(match.group(1))
            continue
        
        # anidb.net/anime/14227
        match = re.search(r"anidb\.net/anime/(\d+)", source_url)
        if match:
            ids["anidb"] = int(match.group(1))
            continue
        
        # kitsu.app/anime/12345 or kitsu.io (original domain)
        match = re.search(r"kitsu\.(?:app|io)/anime/(\d+)", source_url)
        if match:
            ids["kitsu"] = int(match.group(1))
            continue

    return ids


def extract_ja_and_romaji(synonyms, english_title):
    """Extract Japanese and romaji titles from synonyms list."""
    ja = ""
    romaji = ""

    if not isinstance(synonyms, list):
        return ja, romaji

    for syn in synonyms:
        if syn == english_title:
            continue

        # Japanese script (kanji, hiragana, katakana)
        if not ja and re.search(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]", syn):
            ja = syn
            continue

        # Romaji (Latin script only, not identical to English)
        if not romaji and re.match(r"^[a-zA-Z\s]+$", syn):
            romaji = syn

    return ja, romaji


def is_generic_alias(alias, english_title):
    """Check if an alias is too generic and could cause conflicts."""
    normalized = alias.lower().strip()
    if normalized == english_title.lower():
        return False
    if normalized in GENERIC_WORDS:
        return True
    # Just numbers (1-4 digits) or single letters
    if re.match(r"^[\d\s]{1,4}$", normalized):
        return True
    if re.match(r"^[a-z]$", normalized):
        return True
    return False


# ============================================================================
# Main
# ============================================================================


def main():
    limit = 0
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    print("===============================================")
    print("  Fetch anime-offline-database")
    print("===============================================")

    # Step 1: Download
    db = fetch_json(ANIME_DB_URL)
    entries = db.get("data", db)

    if not isinstance(entries, list):
        raise Exception("Unexpected data structure from anime-offline-database")

    print(f"\nTotal entries in database: {len(entries)}")

    # Step 2: Filter and map
    candidates = []
    seen_ids = set()
    skipped_type = 0
    skipped_dup = 0

    for anime in entries:
        # Filter by type
        anime_type = anime.get("type", "")
        if anime_type not in INCLUDE_TYPES:
            skipped_type += 1
            continue

        english_title = anime.get("title", "")
        if not english_title:
            continue

        # Generate ID
        entry_id = slugify(english_title)
        if entry_id in seen_ids:
            skipped_dup += 1
            continue
        seen_ids.add(entry_id)

        # Extract Japanese and romaji from synonyms
        ja, romaji = extract_ja_and_romaji(anime.get("synonyms", []), english_title)

        # Build aliases list from synonyms
        aliases = []
        if isinstance(anime.get("synonyms"), list):
            for syn in anime["synonyms"]:
                if syn == english_title:
                    continue
                lower = syn.lower().strip()
                if lower and lower not in aliases and not is_generic_alias(syn, english_title):
                    aliases.append(lower)

        # Build entry
        entry = {
            "id": entry_id,
            "workType": TYPE_MAP.get(anime_type, "anime-series"),
            "canonicalTitle": english_title,
            "titles": {
                "en": english_title,
                "ja": ja or "",
                "romaji": romaji or "",
            },
            "aliases": aliases,
            "externalIds": extract_external_ids(anime.get("sources", [])),
            "platformAliases": {
                "netflix": [],
                "crunchyroll": [],
            },
            "ratings": {
                "learnnatively": {
                    "level": None,
                    "jlptApprox": "",
                    "url": "",
                },
                "jpdb": {
                    "difficulty": None,
                    "url": "",
                },
            },
            "metadata": {
                "source": "anime-offline-database",
                "status": "needs-ratings",
                "lastModified": "2026-06-29",
            },
        }

        candidates.append(entry)

        # Optional limit for testing
        if limit > 0 and len(candidates) >= limit:
            break

    # Step 3: Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)

    # Step 4: Report
    type_counts = Counter(c["workType"] for c in candidates)
    with_ja = sum(1 for c in candidates if c["titles"]["ja"])
    with_romaji = sum(1 for c in candidates if c["titles"]["romaji"])
    with_ids = sum(1 for c in candidates if c["externalIds"])
    total_aliases = sum(len(c["aliases"]) for c in candidates)

    print("\n===============================================")
    print("  Summary")
    print("===============================================")
    print(f"\n  Candidates extracted: {len(candidates)}")
    print(f"  Skipped (wrong type):  {skipped_type}")
    print(f"  Skipped (duplicate):   {skipped_dup}")
    if limit > 0:
        print(f"  (Limited to {limit})")

    print("\n  By type:")
    for anime_type, count in type_counts.most_common():
        print(f"    {anime_type}: {count}")

    print(f"\n  With Japanese title: {with_ja}")
    print(f"  With romaji title:   {with_romaji}")
    print(f"  With external IDs:   {with_ids}")
    print(f"  Total aliases:       {total_aliases}")
    print(f"\n  Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)