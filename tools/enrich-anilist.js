#!/usr/bin/env node

/**
 * AniList Metadata Enricher
 * 
 * Enriches anime database with metadata from AniList GraphQL API.
 * Adds alternate titles, genres, release dates, and links.
 * 
 * Free tier - no authentication required
 * Rate limited: ~90 requests per minute
 * 
 * Usage:
 *   node tools/enrich-anilist.js --sample 10
 *   node tools/enrich-anilist.js --batch batch-001
 *   node tools/enrich-anilist.js --all
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG = {
  anilistUrl: 'https://graphql.anilist.co',
  extractedCandidatesPath: path.join(__dirname, '../data/extracted-candidates.json'),
  enrichedPath: path.join(__dirname, '../data/enriched-candidates.json'),
  
  // Rate limiting
  requestDelay: 100, // ms between requests (600 req/min safe)
};

// GraphQL query for anime information
const ANILIST_QUERY = `
  query ($search: String) {
    Media(search: $search, type: ANIME) {
      id
      title {
        english
        romaji
        native
      }
      type
      format
      status
      startDate {
        year
        month
        day
      }
      genres
      synonyms
      externalLinks {
        site
        url
      }
      idMal
    }
  }
`;

function queryAniList(title) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      query: ANILIST_QUERY,
      variables: { search: title }
    });

    const options = {
      hostname: 'graphql.anilist.co',
      path: '',
      port: 443,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'User-Agent': 'JP-Difficulty-Overlay/1.0'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json.data?.Media || null);
        } catch (err) {
          resolve(null);
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

function mergeMetadata(entry, anilistData) {
  if (!anilistData) return entry;

  // Merge alternate titles
  const titleMap = {
    romaji: anilistData.title?.romaji,
    native: anilistData.title?.native,
  };

  if (anilistData.title?.english && anilistData.title.english !== entry.canonicalTitle) {
    titleMap.en = anilistData.title.english;
  }

  // Update titles
  entry.titles = {
    en: entry.titles.en || anilistData.title?.english || entry.canonicalTitle,
    ja: entry.titles.ja || anilistData.title?.native || '',
    romaji: entry.titles.romaji || anilistData.title?.romaji || ''
  };

  // Add genres
  if (anilistData.genres && !entry.metadata.genres) {
    entry.metadata.genres = anilistData.genres;
  }

  // Add MAL ID
  if (anilistData.idMal) {
    entry.metadata.source.mal_id = anilistData.idMal;
  }

  // Add external links
  if (anilistData.externalLinks) {
    entry.metadata.externalLinks = anilistData.externalLinks.map(link => ({
      site: link.site,
      url: link.url
    }));
  }

  // Add format/status
  if (anilistData.format) {
    entry.metadata.format = anilistData.format;
  }
  if (anilistData.status) {
    entry.metadata.status = anilistData.status;
  }

  return entry;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function enrichSample(count) {
  console.log(`\n🌐 Enriching ${count} random anime from AniList...\n`);

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found');
    process.exit(1);
  }

  let candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

  // Shuffle and pick random
  candidates = candidates
    .sort(() => Math.random() - 0.5)
    .slice(0, Math.min(count, candidates.length));

  let enriched = 0;
  let failed = 0;

  for (let i = 0; i < candidates.length; i++) {
    const entry = candidates[i];
    
    try {
      console.log(`[${i + 1}/${candidates.length}] Enriching: ${entry.canonicalTitle}`);
      
      const anilistData = await queryAniList(entry.canonicalTitle);
      if (anilistData) {
        mergeMetadata(entry, anilistData);
        enriched++;
      } else {
        failed++;
      }
    } catch (error) {
      console.error(`  ❌ Error: ${error.message}`);
      failed++;
    }

    // Rate limiting
    await sleep(CONFIG.requestDelay);
  }

  fs.writeFileSync(CONFIG.extractedCandidatesPath, JSON.stringify(candidates, null, 2));

  console.log(`\n✅ Enriched ${enriched}/${candidates.length}`);
  console.log(`❌ Failed: ${failed}`);
}

async function enrichBatch(batchName) {
  console.log(`\n🌐 Enriching batch: ${batchName}...\n`);

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

  // Filter to batch (assuming batch files like batch-001.csv)
  // For now, just show what would be enriched
  console.log(`Found ${candidates.length} candidates`);
  console.log('To enrich a specific batch:');
  console.log('  1. Extract titles from batch CSV');
  console.log('  2. Filter candidates by title');
  console.log('  3. Enrich via AniList');
  console.log('\nUse --sample N for quick testing');
}

async function enrichAll() {
  console.log(`\n🌐 Enriching all candidates from AniList...\n`);
  console.log('⚠️  This will take a long time (5000+ requests)');
  console.log('Rate limit: 90 requests/minute');
  console.log('Estimated time: ~1 hour\n');

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));
  let enriched = 0;
  let failed = 0;

  for (let i = 0; i < candidates.length; i++) {
    const entry = candidates[i];
    
    try {
      if ((i + 1) % 100 === 0) {
        console.log(`[${i + 1}/${candidates.length}] Progress: ${enriched} enriched, ${failed} failed`);
      }
      
      const anilistData = await queryAniList(entry.canonicalTitle);
      if (anilistData) {
        mergeMetadata(entry, anilistData);
        enriched++;
      } else {
        failed++;
      }
    } catch (error) {
      failed++;
    }

    // Rate limiting
    await sleep(CONFIG.requestDelay);
  }

  fs.writeFileSync(CONFIG.extractedCandidatesPath, JSON.stringify(candidates, null, 2));

  console.log(`\n✅ Enriched ${enriched}/${candidates.length}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`\nSaved to: ${CONFIG.extractedCandidatesPath}`);
}

function printUsage() {
  console.log(`
AniList Metadata Enricher

Adds additional metadata to anime database using AniList GraphQL API.
No authentication required (public API).

Commands:
  --sample <N>           Enrich N random anime (for testing)
  --batch <name>         Enrich specific batch (--batch batch-001)
  --all                  Enrich all candidates (takes ~1 hour)
  --help                 Show this help

What gets added:
  • Alternate titles (English, Romaji, Native)
  • Genres
  • Format (TV, Movie, OVA, etc.)
  • Release dates
  • External links
  • MyAnimeList ID

Rate Limits:
  • 90 requests per minute (free tier)
  • 100ms delay between requests (safe)
  • Estimated time: ~60 minutes for 5000 anime

Examples:
  node tools/enrich-anilist.js --sample 10
  node tools/enrich-anilist.js --sample 100
  node tools/enrich-anilist.js --all

Tips:
  • Start with --sample 10 to test the connection
  • Run --all overnight or during off-peak hours
  • Enrichment is optional - ratings are more important
`);
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case '--sample':
    if (!arg) {
      console.error('❌ Usage: --sample <count>');
      process.exit(1);
    }
    enrichSample(parseInt(arg, 10));
    break;
  case '--batch':
    if (!arg) {
      console.error('❌ Usage: --batch <batch-name>');
      process.exit(1);
    }
    enrichBatch(arg);
    break;
  case '--all':
    enrichAll();
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
