#!/usr/bin/env node

/**
 * JP Difficulty Overlay - Media Index Builder
 * 
 * This script helps build the media-index.json from external anime databases.
 * It uses anime-offline-database as the primary source and helps with alias normalization.
 * 
 * Usage:
 *   node tools/build-media-index.js --fetch
 *   node tools/build-media-index.js --add-ratings
 *   node tools/build-media-index.js --validate
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// ============================================================================
// Configuration
// ============================================================================

const CONFIG = {
  // anime-offline-database URL
  animeDbUrl: 'https://raw.githubusercontent.com/manami-project/anime-offline-database/master/anime-offline-database.json',
  
  // Output files
  mediaIndexPath: path.join(__dirname, '../media-index.json'),
  candidatesPath: path.join(__dirname, '../data/candidates.json'),
  ratingsTemplatePath: path.join(__dirname, '../data/ratings-template.json'),
  
  // Popular anime to seed (these are titles people actually watch)
  seedTitles: [
    'Bocchi the Rock!',
    'Delicious in Dungeon',
    'Frieren: Beyond Journey\'s End',
    'Haikyu!!',
    'Demon Slayer',
    'My Hero Academia',
    'Attack on Titan',
    'Death Note',
    'Steins;Gate',
    'Neon Genesis Evangelion',
    'Cowboy Bebop',
    'Jujutsu Kaisen',
    'Chainsaw Man',
    'Spy x Family',
    'Solo Leveling',
    'Tower of God',
    'Bleach',
    'Naruto',
    'One Piece',
    'Fullmetal Alchemist',
    'Code Geass',
    'The Promised Neverland',
    'Mob Psycho 100',
    'Violet Evergarden',
    'A Silent Voice',
    'Your Name',
    'Weathering with You',
    'Kaguya-sama: Love is War',
    'Classroom of the Elite',
    'ReZero',
    'Overlord',
    'That Time I Got Reincarnated as a Spider',
    'Sword Art Online',
    'Log Horizon',
    'Made in Abyss',
    'Dr. Stone',
    'The God of High School',
    'Vinland Saga',
    'Ergo Proxy',
    'Psycho-Pass',
    'Monster',
    'Parasyte',
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

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    console.log(`Fetching: ${url}`);
    https.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (err) {
          reject(new Error(`Failed to parse JSON: ${err.message}`));
        }
      });
    }).on('error', reject);
  });
}

function createMediaEntry(animeData) {
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
  
  // Add normalized title
  const normalizedMain = normalizeTitle(animeData.title);
  if (normalizedMain) aliases.push(normalizedMain);
  
  // Add synonyms as aliases
  if (animeData.synonyms && Array.isArray(animeData.synonyms)) {
    for (const synonym of animeData.synonyms) {
      const normalized = normalizeTitle(synonym);
      if (normalized && !aliases.includes(normalized)) {
        aliases.push(normalized);
      }
    }
  }

  return {
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
      notes: 'Auto-generated from anime-offline-database. Ratings pending manual entry.',
      source: {
        animeOfflineDb: animeData.sources?.[0] || null
      }
    }
  };
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

// ============================================================================
// Commands
// ============================================================================

async function fetchAndCandidates() {
  console.log('\n📥 Fetching anime-offline-database...');
  
  try {
    const db = await fetchUrl(CONFIG.animeDbUrl);
    console.log(`✅ Fetched ${db.data.length} anime entries`);

    // Find seed titles
    const candidates = [];
    const seedSet = new Set(CONFIG.seedTitles.map(t => normalizeTitle(t)));

    for (const anime of db.data) {
      const normalizedMain = normalizeTitle(anime.title);
      
      if (seedSet.has(normalizedMain)) {
        candidates.push(createMediaEntry(anime));
        console.log(`  ✓ ${anime.title}`);
      }
    }

    // Save candidates
    fs.mkdirSync(path.dirname(CONFIG.candidatesPath), { recursive: true });
    fs.writeFileSync(CONFIG.candidatesPath, JSON.stringify(candidates, null, 2));
    
    console.log(`\n✅ Found ${candidates.length} seed titles`);
    console.log(`📁 Saved to: ${CONFIG.candidatesPath}`);
    console.log('\nNext steps:');
    console.log('1. Add LearnNatively and jpdb ratings to candidates.json');
    console.log('2. Update platform aliases based on Netflix/Crunchyroll');
    console.log('3. Run: node tools/build-media-index.js --merge');
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

function mergeRatings() {
  console.log('\n🔗 Merging candidates with ratings...');
  
  try {
    if (!fs.existsSync(CONFIG.candidatesPath)) {
      throw new Error(`Candidates file not found: ${CONFIG.candidatesPath}`);
    }

    const candidates = JSON.parse(fs.readFileSync(CONFIG.candidatesPath, 'utf8'));
    
    // Sort by title
    candidates.sort((a, b) => a.canonicalTitle.localeCompare(b.canonicalTitle));

    // Save as media-index.json
    fs.writeFileSync(CONFIG.mediaIndexPath, JSON.stringify(candidates, null, 2));
    
    console.log(`✅ Merged ${candidates.length} entries into media-index.json`);
    console.log(`📁 Saved to: ${CONFIG.mediaIndexPath}`);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

function validateIndex() {
  console.log('\n✓ Validating media-index.json...');
  
  try {
    if (!fs.existsSync(CONFIG.mediaIndexPath)) {
      throw new Error(`Media index not found: ${CONFIG.mediaIndexPath}`);
    }

    const index = JSON.parse(fs.readFileSync(CONFIG.mediaIndexPath, 'utf8'));
    
    let issues = [];
    const ids = new Set();

    for (const item of index) {
      // Check required fields
      if (!item.id) issues.push(`Missing id: ${item.canonicalTitle}`);
      if (!item.canonicalTitle) issues.push(`Missing canonicalTitle at ${item.id}`);
      
      // Check for duplicates
      if (ids.has(item.id)) issues.push(`Duplicate id: ${item.id}`);
      ids.add(item.id);
      
      // Check ratings status
      const hasRatings = 
        (item.ratings?.learnnatively?.level !== null && item.ratings?.learnnatively?.level !== undefined) ||
        (item.ratings?.jpdb?.difficulty !== null && item.ratings?.jpdb?.difficulty !== undefined);
      
      if (!hasRatings) {
        console.log(`  ⚠️  ${item.canonicalTitle} - no ratings`);
      }
    }

    if (issues.length > 0) {
      console.log('\n❌ Issues found:');
      issues.forEach(issue => console.log(`  • ${issue}`));
      process.exit(1);
    }

    console.log(`✅ Valid! ${index.length} entries, all checks passed`);
    
    // Summary
    const withRatings = index.filter(item => 
      (item.ratings?.learnnatively?.level !== null && item.ratings?.learnnatively?.level !== undefined) ||
      (item.ratings?.jpdb?.difficulty !== null && item.ratings?.jpdb?.difficulty !== undefined)
    );
    console.log(`\n📊 Statistics:`);
    console.log(`  Total entries: ${index.length}`);
    console.log(`  With ratings: ${withRatings.length}`);
    console.log(`  Needs ratings: ${index.length - withRatings.length}`);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

function printUsage() {
  console.log(`
JP Difficulty Overlay - Media Index Builder

Usage:
  node tools/build-media-index.js [command]

Commands:
  --fetch       Fetch seed titles from anime-offline-database
  --merge       Merge candidates into media-index.json
  --validate    Validate media-index.json
  --help        Show this help message

Workflow:
  1. node tools/build-media-index.js --fetch
     (Downloads popular anime titles and creates candidates.json)
  
  2. Edit data/candidates.json
     (Add LearnNatively and jpdb ratings manually)
  
  3. node tools/build-media-index.js --merge
     (Merges candidates into media-index.json)
  
  4. node tools/build-media-index.js --validate
     (Validates the final database)

Examples:
  node tools/build-media-index.js --fetch
  node tools/build-media-index.js --validate
`);
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2];

switch (command) {
  case '--fetch':
    fetchAndCandidates();
    break;
  case '--merge':
    mergeRatings();
    break;
  case '--validate':
    validateIndex();
    break;
  case '--help':
  case '-h':
    printUsage();
    break;
  default:
    if (command) {
      console.error(`Unknown command: ${command}`);
    }
    printUsage();
    process.exit(command ? 1 : 0);
}
