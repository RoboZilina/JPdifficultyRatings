#!/usr/bin/env node

/**
 * JP Difficulty Overlay - Comprehensive Database Builder
 * 
 * Builds a large-scale media database from multiple sources:
 * - anime-offline-database (10,000+ anime)
 * - LearnNatively ratings (manual/batch import)
 * - jpdb ratings (manual/batch import)
 * - AniList API (metadata enrichment)
 * 
 * Usage:
 *   node tools/build-database.js --download-animedb
 *   node tools/build-database.js --extract --limit 5000
 *   node tools/build-database.js --import-ratings <csv-file>
 *   node tools/build-database.js --merge
 *   node tools/build-database.js --stats
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const readline = require('readline');

// ============================================================================
// Configuration
// ============================================================================

const CONFIG = {
  // Source URLs
  animeDbUrl: 'https://raw.githubusercontent.com/manami-project/anime-offline-database/master/anime-offline-database.json',
  anilistUrl: 'https://graphql.anilist.co',
  
  // Local paths
  rawAnimeDbPath: path.join(__dirname, '../data/raw/anime-offline-database.json'),
  extractedCandidatesPath: path.join(__dirname, '../data/extracted-candidates.json'),
  ratingsPath: path.join(__dirname, '../data/ratings.json'),
  mediaIndexPath: path.join(__dirname, '../media-index.json'),
  
  // Extraction filters
  minAnimeToExtract: 100,
  maxAnimeToExtract: 5000,
  
  // Anime types to include
  animeTypes: ['TV', 'Movie', 'OVA', 'ONA', 'Special'],
  
  // Exclude keywords
  excludeKeywords: [
    'preview', 'promo', 'ost', 'pv', 'commercial',
    'short', 'chibi', 'parody', 'trailer'
  ]
};

// ============================================================================
// Utility Functions
// ============================================================================

function normalizeTitle(title) {
  if (!title) return "";
  return String(title)
    .toLowerCase()
    .normalize("NFKC")
    .replace(/\b(subbed|dubbed|sub|dub)\b/g, " ")
    .replace(/\b(tv series|series|movie|ova|ona|special)\b/g, " ")
    .replace(/\bseason\s*\d+\b/g, " ")
    .replace(/\bs\d+\b/g, " ")
    .replace(/[!！?？:：;；''""".,・·•\-–—_()[\]{}<>]/g, " ")
    .replace(/&/g, " and ")
    .replace(/\s+/g, " ")
    .trim();
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .substring(0, 50);
}

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    console.log(`📥 Fetching: ${url.substring(0, 80)}...`);
    https.get(url, (res) => {
      let data = '';
      const totalSize = parseInt(res.headers['content-length'], 10);
      let downloadedSize = 0;

      res.on('data', (chunk) => {
        data += chunk;
        downloadedSize += chunk.length;
        const percent = Math.round((downloadedSize / totalSize) * 100);
        process.stdout.write(`\r   Progress: ${percent}%`);
      });

      res.on('end', () => {
        console.log('\n✅ Download complete');
        try {
          resolve(JSON.parse(data));
        } catch (err) {
          reject(new Error(`Failed to parse JSON: ${err.message}`));
        }
      });
    }).on('error', reject);
  });
}

function parseCSV(filePath) {
  return new Promise((resolve, reject) => {
    const rows = [];
    const rl = readline.createInterface({
      input: fs.createReadStream(filePath),
      crlfDelay: Infinity
    });

    let isHeader = true;
    let headers = [];

    rl.on('line', (line) => {
      const values = [];
      let current = '';
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        const nextChar = line[i + 1];

        if (char === '"') {
          if (inQuotes && nextChar === '"') {
            current += '"';
            i++;
          } else {
            inQuotes = !inQuotes;
          }
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      values.push(current.trim());

      if (isHeader) {
        headers = values;
        isHeader = false;
      } else if (values[0]) {
        const row = {};
        headers.forEach((header, i) => {
          row[header] = values[i] || '';
        });
        rows.push(row);
      }
    });

    rl.on('close', () => resolve(rows));
    rl.on('error', reject);
  });
}

function shouldIncludeAnime(anime) {
  if (!anime || !anime.title) return false;
  
  const title = anime.title.toLowerCase();
  
  // Check excluded keywords
  for (const keyword of CONFIG.excludeKeywords) {
    if (title.includes(keyword)) return false;
  }
  
  // Check anime type
  if (anime.type && !CONFIG.animeTypes.includes(anime.type)) {
    return false;
  }
  
  return true;
}

function createMediaEntry(animeData, ratingData = null) {
  const titles = {
    en: animeData.title || '',
    ja: '',
    romaji: ''
  };

  // Extract from synonyms
  if (animeData.synonyms && Array.isArray(animeData.synonyms)) {
    for (const synonym of animeData.synonyms) {
      if (!titles.ja && /[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]/.test(synonym)) {
        titles.ja = synonym;
      } else if (!titles.romaji && /^[a-z\s]+$/i.test(synonym) && synonym !== titles.en) {
        titles.romaji = synonym;
      }
    }
  }

  const aliases = [];
  const normalizedMain = normalizeTitle(animeData.title);
  if (normalizedMain) aliases.push(normalizedMain);

  if (animeData.synonyms && Array.isArray(animeData.synonyms)) {
    for (const synonym of animeData.synonyms) {
      const normalized = normalizeTitle(synonym);
      if (normalized && !aliases.includes(normalized)) {
        aliases.push(normalized);
      }
    }
  }

  const entry = {
    id: slugify(animeData.title),
    workType: animeData.type?.toLowerCase() || 'anime-series',
    canonicalTitle: animeData.title,
    titles: titles,
    aliases: aliases,
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
      status: 'needs-ratings',
      lastVerified: new Date().toISOString().split('T')[0],
      notes: 'Auto-extracted from anime-offline-database',
      source: {
        animeOfflineDb: animeData.sources?.[0] || null,
        mal_id: animeData.sources?.find(s => s.includes('myanimelist'))?.[0] || null,
        anilist_id: animeData.sources?.find(s => s.includes('anilist'))?.[0] || null
      }
    }
  };

  // Merge rating data if provided
  if (ratingData) {
    if (ratingData['LearnNatively Level']) {
      entry.ratings.learnnatively.level = parseInt(ratingData['LearnNatively Level'], 10);
    }
    if (ratingData['LearnNatively JLPT']) {
      entry.ratings.learnnatively.jlptApprox = ratingData['LearnNatively JLPT'];
    }
    if (ratingData['LearnNatively URL']) {
      entry.ratings.learnnatively.url = ratingData['LearnNatively URL'];
    }
    if (ratingData['jpdb Difficulty']) {
      entry.ratings.jpdb.difficulty = parseInt(ratingData['jpdb Difficulty'], 10);
    }
    if (ratingData['jpdb URL']) {
      entry.ratings.jpdb.url = ratingData['jpdb URL'];
    }
    if (ratingData['Netflix Alias']) {
      entry.platformAliases.netflix = [ratingData['Netflix Alias']];
    }
    if (ratingData['Crunchyroll Alias']) {
      entry.platformAliases.crunchyroll = [ratingData['Crunchyroll Alias']];
    }
    entry.metadata.status = 'verified';
  }

  return entry;
}

// ============================================================================
// Commands
// ============================================================================

async function downloadAnimeDb() {
  console.log('\n📥 Downloading anime-offline-database...');
  console.log('   (This is a large file ~50MB, may take 1-2 minutes)\n');

  try {
    const db = await fetchUrl(CONFIG.animeDbUrl);
    
    fs.mkdirSync(path.dirname(CONFIG.rawAnimeDbPath), { recursive: true });
    fs.writeFileSync(CONFIG.rawAnimeDbPath, JSON.stringify(db, null, 2));
    
    console.log(`\n✅ Downloaded and saved ${db.data.length} anime`);
    console.log(`📁 Saved to: ${CONFIG.rawAnimeDbPath}`);
    console.log('\nNext: node tools/build-database.js --extract');
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

async function extractCandidates(limit) {
  console.log(`\n📊 Extracting anime from raw database (limit: ${limit})...\n`);

  try {
    if (!fs.existsSync(CONFIG.rawAnimeDbPath)) {
      throw new Error(`Raw database not found. Run: --download-animedb`);
    }

    const rawDb = JSON.parse(fs.readFileSync(CONFIG.rawAnimeDbPath, 'utf8'));
    const candidates = [];

    // Sort by some heuristic (e.g., has more synonyms = more popular)
    const sorted = rawDb.data
      .filter(shouldIncludeAnime)
      .sort((a, b) => {
        const aScore = (a.synonyms?.length || 0) + (a.sources?.length || 0);
        const bScore = (b.synonyms?.length || 0) + (b.sources?.length || 0);
        return bScore - aScore;
      })
      .slice(0, limit);

    for (let i = 0; i < sorted.length; i++) {
      const anime = sorted[i];
      candidates.push(createMediaEntry(anime));
      
      if ((i + 1) % 500 === 0) {
        console.log(`  ✓ Extracted ${i + 1}/${Math.min(limit, sorted.length)}`);
      }
    }

    fs.mkdirSync(path.dirname(CONFIG.extractedCandidatesPath), { recursive: true });
    fs.writeFileSync(CONFIG.extractedCandidatesPath, JSON.stringify(candidates, null, 2));

    console.log(`\n✅ Extracted ${candidates.length} candidates`);
    console.log(`📁 Saved to: ${CONFIG.extractedCandidatesPath}`);
    console.log('\nNext: Add ratings and run --merge');
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

async function importRatings(csvFile) {
  console.log(`\n📥 Importing ratings from: ${csvFile}\n`);

  try {
    if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
      throw new Error('Extracted candidates not found. Run: --extract first');
    }

    const csvRows = await parseCSV(csvFile);
    const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

    // Create a map for quick lookup
    const candidateMap = new Map();
    for (const candidate of candidates) {
      candidateMap.set(candidate.canonicalTitle.toLowerCase(), candidate);
      for (const alias of candidate.aliases) {
        candidateMap.set(alias.toLowerCase(), candidate);
      }
    }

    let matched = 0;
    for (const row of csvRows) {
      const title = row['Canonical Title']?.toLowerCase();
      if (!title) continue;

      const candidate = candidateMap.get(title);
      if (candidate) {
        // Apply rating data
        if (row['LearnNatively Level']) {
          candidate.ratings.learnnatively.level = parseInt(row['LearnNatively Level'], 10);
        }
        if (row['LearnNatively JLPT']) {
          candidate.ratings.learnnatively.jlptApprox = row['LearnNatively JLPT'];
        }
        if (row['LearnNatively URL']) {
          candidate.ratings.learnnatively.url = row['LearnNatively URL'];
        }
        if (row['jpdb Difficulty']) {
          candidate.ratings.jpdb.difficulty = parseInt(row['jpdb Difficulty'], 10);
        }
        if (row['jpdb URL']) {
          candidate.ratings.jpdb.url = row['jpdb URL'];
        }
        if (row['Netflix Alias']) {
          candidate.platformAliases.netflix = [row['Netflix Alias']];
        }
        if (row['Crunchyroll Alias']) {
          candidate.platformAliases.crunchyroll = [row['Crunchyroll Alias']];
        }
        candidate.metadata.status = 'verified';
        matched++;
      }
    }

    fs.writeFileSync(CONFIG.extractedCandidatesPath, JSON.stringify(candidates, null, 2));

    console.log(`✅ Matched and updated ${matched}/${csvRows.length} entries`);
    console.log(`📁 Updated: ${CONFIG.extractedCandidatesPath}`);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

function merge() {
  console.log(`\n🔗 Merging database...\n`);

  try {
    if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
      throw new Error('Extracted candidates not found. Run: --extract first');
    }

    let entries = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

    // Sort by title
    entries.sort((a, b) => a.canonicalTitle.localeCompare(b.canonicalTitle));

    // Remove duplicates (by ID)
    const seen = new Set();
    entries = entries.filter(entry => {
      if (seen.has(entry.id)) return false;
      seen.add(entry.id);
      return true;
    });

    fs.mkdirSync(path.dirname(CONFIG.mediaIndexPath), { recursive: true });
    fs.writeFileSync(CONFIG.mediaIndexPath, JSON.stringify(entries, null, 2));

    console.log(`✅ Created media-index.json with ${entries.length} entries`);
    console.log(`📁 Saved to: ${CONFIG.mediaIndexPath}`);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

function showStats() {
  console.log(`\n📊 Database Statistics\n`);

  try {
    if (fs.existsSync(CONFIG.mediaIndexPath)) {
      const entries = JSON.parse(fs.readFileSync(CONFIG.mediaIndexPath, 'utf8'));

      const withBothRatings = entries.filter(e =>
        e.ratings?.learnnatively?.level !== null &&
        e.ratings?.jpdb?.difficulty !== null
      );

      const withLN = entries.filter(e => e.ratings?.learnnatively?.level !== null);
      const withJPDB = entries.filter(e => e.ratings?.jpdb?.difficulty !== null);
      const withNetflix = entries.filter(e => e.platformAliases?.netflix?.length > 0);
      const withCrunchyroll = entries.filter(e => e.platformAliases?.crunchyroll?.length > 0);

      console.log(`📊 Final Database (media-index.json):`);
      console.log(`   Total entries: ${entries.length}`);
      console.log(`   With both ratings: ${withBothRatings.length} (${((withBothRatings.length / entries.length) * 100).toFixed(1)}%)`);
      console.log(`   With LearnNatively: ${withLN.length}`);
      console.log(`   With jpdb: ${withJPDB.length}`);
      console.log(`   With Netflix alias: ${withNetflix.length}`);
      console.log(`   With Crunchyroll alias: ${withCrunchyroll.length}`);
      console.log();
    }

    if (fs.existsSync(CONFIG.extractedCandidatesPath)) {
      const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));
      const withBothRatings = candidates.filter(e =>
        e.ratings?.learnnatively?.level !== null &&
        e.ratings?.jpdb?.difficulty !== null
      );

      console.log(`🔄 Candidates (extracted-candidates.json):`);
      console.log(`   Total candidates: ${candidates.length}`);
      console.log(`   With both ratings: ${withBothRatings.length} (${((withBothRatings.length / candidates.length) * 100).toFixed(1)}%)`);
      console.log();
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

function printUsage() {
  console.log(`
JP Difficulty Overlay - Comprehensive Database Builder

Building a 5000+ title database from external sources.

Commands:
  --download-animedb         Download anime-offline-database.json (~50MB)
  --extract [--limit N]      Extract and filter N anime (default: 5000)
  --import-ratings <csv>     Import ratings from CSV file
  --merge                    Merge candidates into media-index.json
  --stats                    Show database statistics
  --help                     Show this help message

Workflow for 5000+ Title Database:

  1. node tools/build-database.js --download-animedb
     (Downloads 10,000+ anime from anime-offline-database)
     Takes ~1-2 minutes

  2. node tools/build-database.js --extract --limit 5000
     (Extracts most popular 5000 anime)
     Creates extracted-candidates.json

  3. Batch Import Ratings:
     a. Use tools/RATINGS_TEMPLATE.csv as a template
     b. Create batch CSV files with 500+ ratings each
     c. Run: node tools/build-database.js --import-ratings <csv>
     d. Repeat for each CSV batch

  4. node tools/build-database.js --merge
     (Creates final media-index.json)

  5. node tools/build-database.js --stats
     (Shows coverage: how many have ratings)

External Sources:
  - anime-offline-database: 10,000+ anime + aliases + metadata
  - LearnNatively: Difficulty levels (manual entry or bulk import)
  - jpdb: Vocabulary difficulty (manual entry or bulk import)
  - Netflix/Crunchyroll: Platform aliases (manual mapping)

Tips for Scaling:
  • Batch rating imports in groups of 500-1000
  • Use CSV files for bulk operations
  • Automate with spreadsheet tools (Google Sheets, Excel)
  • Parallel processing: One person can handle extraction, another ratings

Target: 5000+ titles with both LN and jpdb ratings
`);
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case '--download-animedb':
    downloadAnimeDb();
    break;
  case '--extract':
    const limit = arg === '--limit' ? parseInt(process.argv[4], 10) : CONFIG.maxAnimeToExtract;
    extractCandidates(limit);
    break;
  case '--import-ratings':
    if (!arg) {
      console.error('❌ Please specify CSV file: --import-ratings <file>');
      process.exit(1);
    }
    importRatings(arg);
    break;
  case '--merge':
    merge();
    break;
  case '--stats':
    showStats();
    break;
  case '--help':
  case '-h':
    printUsage();
    break;
  default:
    if (command) {
      console.error(`❌ Unknown command: ${command}`);
    }
    printUsage();
    process.exit(command ? 1 : 0);
}
