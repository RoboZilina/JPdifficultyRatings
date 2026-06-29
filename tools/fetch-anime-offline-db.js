#!/usr/bin/env node

/**
 * JP Difficulty Overlay - Fetch anime-offline-database
 * 
 * Downloads the full anime-offline-database (~50MB JSON, MIT license),
 * filters to anime types we care about (TV, Movie, OVA, ONA, Special),
 * and extracts titles, aliases, and external IDs into our schema.
 * 
 * Usage:
 *   node tools/fetch-anime-offline-db.js
 *   node tools/fetch-anime-offline-db.js --limit 100   # test with 100 entries
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// ============================================================================
// Config
// ============================================================================

const ANIME_DB_URL = 'https://raw.githubusercontent.com/manami-project/anime-offline-database/master/anime-offline-database.json';
const OUTPUT_DIR = path.join(__dirname, '..', 'data');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'candidates.json');

// Anime types we want to include
const INCLUDE_TYPES = new Set([
  'TV',
  'Movie',
  'OVA',
  'ONA',
  'Special'
]);

// Map their type strings to our workType values
const TYPE_MAP = {
  'TV': 'anime-series',
  'Movie': 'anime-movie',
  'OVA': 'anime-ova',
  'ONA': 'anime-ona',
  'Special': 'anime-special'
};

// ============================================================================
// Helpers
// ============================================================================

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    console.log(`\nDownloading: ${url}`);
    console.log('(File is ~50MB, may take a moment...)');
    https.get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
        return;
      }
      let data = '';
      let bytes = 0;
      res.on('data', (chunk) => {
        data += chunk;
        bytes += chunk.length;
        // Show progress every 10MB
        if (bytes % (10 * 1024 * 1024) < chunk.length) {
          process.stdout.write(`  Downloaded ${(bytes / 1024 / 1024).toFixed(0)} MB...\r`);
        }
      });
      res.on('end', () => {
        process.stdout.write(`  Downloaded ${(bytes / 1024 / 1024).toFixed(1)} MB total.\n`);
        try {
          resolve(JSON.parse(data));
        } catch (err) {
          reject(new Error(`Failed to parse JSON: ${err.message}`));
        }
      });
    }).on('error', reject);
  });
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function extractExternalIds(sources) {
  const ids = {};
  if (!Array.isArray(sources)) return ids;
  
  for (const source of sources) {
    // Format: "sourcename: id" e.g. "anilist: 101921"
    const match = source.match(/^(\w+):\s*(\S+)$/);
    if (match) {
      const [, name, id] = match;
      switch (name) {
        case 'anilist':      ids.anilist = parseInt(id); break;
        case 'myanimelist':  ids.mal = parseInt(id); break;
        case 'anidb':        ids.anidb = parseInt(id); break;
        case 'kitsu':        ids.kitsu = parseInt(id); break;
      }
    }
  }
  return ids;
}

function extractJaAndRomaji(synonyms, englishTitle) {
  let ja = '';
  let romaji = '';

  if (!Array.isArray(synonyms)) return { ja, romaji };

  for (const syn of synonyms) {
    if (syn === englishTitle) continue;
    
    // Japanese script (kanji, hiragana, katakana)
    if (!ja && /[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]/.test(syn)) {
      ja = syn;
      continue;
    }
    // Romaji (Latin script, not English)
    if (!romaji && /^[a-zA-Z\s]+$/.test(syn)) {
      romaji = syn;
    }
  }

  return { ja, romaji };
}

function isGenericAlias(alias, englishTitle) {
  // Filter out overly generic single-word aliases that could cause conflicts
  const genericWords = new Set([
    'anime', 'movie', 'film', 'series', 'tv', 'special', 'ova', 'ona',
    'the', 'a', 'an', 'in', 'of', 'and', 'to', 'for', 'is', 'it',
    'hero', 'monster', 'love', 'world', 'story', 'tale', 'chronicle',
    'legend', 'saga', 'war', 'kingdom', 'school', 'city', 'time'
  ]);
  
  const normalized = alias.toLowerCase().trim();
  if (genericWords.has(normalized) && normalized !== englishTitle.toLowerCase()) {
    return true;
  }
  // Filter if it's just numbers or single characters
  if (/^[\d\s]{1,4}$/.test(normalized)) return true;
  if (/^[a-z]$/.test(normalized)) return true;
  
  return false;
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  const limit = process.argv.includes('--limit')
    ? parseInt(process.argv[process.argv.indexOf('--limit') + 1]) || 0
    : 0;

  console.log('╔══════════════════════════════════════════════╗');
  console.log('║  Fetch anime-offline-database               ║');
  console.log('╚══════════════════════════════════════════════╝');

  // Step 1: Download
  const db = await fetchJson(ANIME_DB_URL);
  const entries = db.data || db;
  
  if (!Array.isArray(entries)) {
    throw new Error('Unexpected data structure from anime-offline-database');
  }
  console.log(`\nTotal entries in database: ${entries.length}`);

  // Step 2: Filter and map
  const candidates = [];
  const seenIds = new Set();
  let skippedType = 0;
  let skippedDup = 0;

  for (const anime of entries) {
    // Filter by type
    const type = anime.type || '';
    if (!INCLUDE_TYPES.has(type)) {
      skippedType++;
      continue;
    }

    const englishTitle = anime.title || '';
    if (!englishTitle) continue;

    // Generate ID
    const id = slugify(englishTitle);
    if (seenIds.has(id)) {
      skippedDup++;
      continue;
    }
    seenIds.add(id);

    // Extract Japanese and romaji from synonyms
    const { ja, romaji } = extractJaAndRomaji(anime.synonyms, englishTitle);

    // Build aliases list
    const aliases = [];
    
    // Add synonyms as aliases (filtered)
    if (Array.isArray(anime.synonyms)) {
      for (const syn of anime.synonyms) {
        if (syn === englishTitle) continue;
        const lower = syn.toLowerCase().trim();
        if (lower && !aliases.includes(lower) && !isGenericAlias(syn, englishTitle)) {
          aliases.push(lower);
        }
      }
    }

    // Build entry
    const entry = {
      id,
      workType: TYPE_MAP[type] || 'anime-series',
      canonicalTitle: englishTitle,
      titles: {
        en: englishTitle,
        ja: ja || '',
        romaji: romaji || ''
      },
      aliases,
      externalIds: extractExternalIds(anime.sources),
      platformAliases: {
        netflix: [],
        crunchyroll: []
      },
      ratings: {
        learnnatively: {
          level: null,
          jlptApprox: '',
          url: ''
        },
        jpdb: {
          difficulty: null,
          url: ''
        }
      },
      metadata: {
        source: 'anime-offline-database',
        status: 'needs-ratings',
        lastModified: new Date().toISOString().split('T')[0]
      }
    };

    candidates.push(entry);

    // Optional limit for testing
    if (limit > 0 && candidates.length >= limit) break;
  }

  // Step 3: Save
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(candidates, null, 2));

  // Step 4: Report
  const types = {};
  for (const c of candidates) {
    types[c.workType] = (types[c.workType] || 0) + 1;
  }
  const withJa = candidates.filter(c => c.titles.ja).length;
  const withRomaji = candidates.filter(c => c.titles.romaji).length;
  const withIds = candidates.filter(c => Object.keys(c.externalIds).length > 0).length;
  const totalAliases = candidates.reduce((sum, c) => sum + c.aliases.length, 0);

  console.log('\n╔══════════════════════════════════════════════╗');
  console.log('║  Summary                                     ║');
  console.log('╚══════════════════════════════════════════════╝');
  console.log(`\n  Candidates extracted: ${candidates.length}`);
  console.log(`  Skipped (wrong type):  ${skippedType}`);
  console.log(`  Skipped (duplicate):   ${skippedDup}`);
  if (limit > 0) console.log(`  (Limited to ${limit})`);
  
  console.log('\n  By type:');
  for (const [type, count] of Object.entries(types).sort((a, b) => b[1] - a[1])) {
    console.log(`    ${type}: ${count}`);
  }
  
  console.log(`\n  With Japanese title: ${withJa}`);
  console.log(`  With romaji title:   ${withRomaji}`);
  console.log(`  With external IDs:   ${withIds}`);
  console.log(`  Total aliases:       ${totalAliases}`);
  console.log(`\n  Saved to: ${OUTPUT_FILE}`);
}

main().catch(err => {
  console.error('\n❌ Error:', err.message);
  process.exit(1);
});