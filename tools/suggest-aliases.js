#!/usr/bin/env node

/**
 * Suggest Aliases Tool
 * 
 * Takes a canonical title and suggests aliases from external sources.
 * Uses anime-offline-database, AniDB, and other sources to recommend
 * matching titles and variants.
 * 
 * Admin-only tool: Requires human review before adding to media-index.json
 * 
 * Usage:
 *   node tools/suggest-aliases.js "Bocchi the Rock!"
 *   node tools/suggest-aliases.js --lookup "Demon Slayer"
 *   node tools/suggest-aliases.js --batch candidates.json
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG = {
  rawAnimeDbPath: path.join(__dirname, '../data/raw/anime-offline-database.json'),
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

function calculateSimilarity(str1, str2) {
  const s1 = normalizeTitle(str1);
  const s2 = normalizeTitle(str2);

  if (s1 === s2) return 1.0;

  const longer = s1.length > s2.length ? s1 : s2;
  const shorter = s1.length > s2.length ? s2 : s1;

  if (longer.length === 0) return 1.0;

  const editDistance = getEditDistance(longer, shorter);
  return (longer.length - editDistance) / longer.length;
}

function getEditDistance(s1, s2) {
  const costs = [];
  for (let i = 0; i <= s1.length; i++) {
    let lastValue = i;
    for (let j = 0; j <= s2.length; j++) {
      if (i === 0) {
        costs[j] = j;
      } else if (j > 0) {
        let newValue = costs[j - 1];
        if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
          newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
        }
        costs[j - 1] = lastValue;
        lastValue = newValue;
      }
    }
    if (i > 0) costs[s2.length] = lastValue;
  }
  return costs[s2.length];
}

function queryAniList(title) {
  return new Promise((resolve, reject) => {
    const query = `
      query ($search: String) {
        Media(search: $search, type: ANIME) {
          id
          title { english romaji native }
          synonyms
          externalLinks { site url }
          idMal
        }
      }
    `;

    const postData = JSON.stringify({
      query: query,
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

// ============================================================================
// Alias Suggestion
// ============================================================================

async function suggestAliases(title) {
  console.log(`\n🔍 Suggesting aliases for: "${title}"\n`);

  const suggestions = {
    title: title,
    normalized: normalizeTitle(title),
    sources: {
      animeOfflineDb: [],
      anilist: [],
      variants: [],
      compactVariant: []
    },
    notes: []
  };

  // 1. Try anime-offline-database
  if (fs.existsSync(CONFIG.rawAnimeDbPath)) {
    console.log('📚 Searching anime-offline-database...');
    try {
      const db = JSON.parse(fs.readFileSync(CONFIG.rawAnimeDbPath, 'utf8'));

      for (const anime of db.data) {
        const similarity = calculateSimilarity(title, anime.title);

        if (similarity > 0.7) {
          const aliases = new Set();

          // Add direct synonyms
          if (anime.synonyms && Array.isArray(anime.synonyms)) {
            anime.synonyms.forEach(syn => {
              const normalized = normalizeTitle(syn);
              if (normalized) aliases.add(normalized);
            });
          }

          // Add the anime's own title
          aliases.add(normalizeTitle(anime.title));

          suggestions.sources.animeOfflineDb = Array.from(aliases)
            .sort()
            .slice(0, 10);

          console.log(`✅ Found in anime-offline-database (${(similarity * 100).toFixed(0)}% match)`);
          console.log(`   Title: ${anime.title}`);
          console.log(`   Aliases: ${suggestions.sources.animeOfflineDb.slice(0, 3).join(', ')}`);
          break;
        }
      }
    } catch (error) {
      console.error('❌ Error reading anime-offline-database:', error.message);
      suggestions.notes.push('Could not access anime-offline-database');
    }
  } else {
    console.log('⚠️  anime-offline-database not found (run: npm run download)');
    suggestions.notes.push('anime-offline-database not available - run download first');
  }

  // 2. Try AniList API
  console.log('\n🌐 Querying AniList...');
  try {
    const anilistData = await queryAniList(title);
    if (anilistData) {
      const aliases = new Set();

      // Add all title variants
      if (anilistData.title) {
        if (anilistData.title.english) aliases.add(normalizeTitle(anilistData.title.english));
        if (anilistData.title.romaji) aliases.add(normalizeTitle(anilistData.title.romaji));
        if (anilistData.title.native) aliases.add(normalizeTitle(anilistData.title.native));
      }

      // Add synonyms
      if (anilistData.synonyms && Array.isArray(anilistData.synonyms)) {
        anilistData.synonyms.forEach(syn => {
          const normalized = normalizeTitle(syn);
          if (normalized) aliases.add(normalized);
        });
      }

      suggestions.sources.anilist = Array.from(aliases)
        .filter(a => a)
        .sort()
        .slice(0, 10);

      console.log(`✅ Found on AniList`);
      if (anilistData.title?.english) console.log(`   English: ${anilistData.title.english}`);
      if (anilistData.title?.romaji) console.log(`   Romaji: ${anilistData.title.romaji}`);
      if (anilistData.title?.native) console.log(`   Native: ${anilistData.title.native}`);
    } else {
      console.log('❌ Not found on AniList');
    }
  } catch (error) {
    console.error('⚠️  AniList query failed:', error.message);
    suggestions.notes.push('AniList API unavailable');
  }

  // 3. Generate title variants
  console.log('\n✨ Generating title variants...');
  const variants = new Set();

  // Original with/without punctuation
  variants.add(normalizeTitle(title));
  variants.add(title.toLowerCase());

  // Compact version (no spaces in Japanese-style titles)
  const compactVersion = title.replace(/\s+/g, '');
  if (compactVersion !== title) {
    variants.add(normalizeTitle(compactVersion));
    suggestions.sources.compactVariant = [normalizeTitle(compactVersion)];
  }

  // Common abbreviations
  const words = title.split(/\s+/);
  if (words.length > 1) {
    const acronym = words.map(w => w[0]).join('').toLowerCase();
    variants.add(acronym);
  }

  suggestions.sources.variants = Array.from(variants)
    .filter(v => v && v !== suggestions.normalized)
    .slice(0, 10);

  // 4. Merge and deduplicate all sources
  const allAliases = new Set();
  Object.values(suggestions.sources).forEach(source => {
    if (Array.isArray(source)) {
      source.forEach(alias => allAliases.add(alias));
    }
  });

  console.log('\n📋 Suggested Aliases:\n');

  const aliasArray = Array.from(allAliases)
    .filter(a => a && a !== suggestions.normalized)
    .sort();

  if (aliasArray.length === 0) {
    console.log('ℹ️  No aliases found. Use manual entry.');
  } else {
    aliasArray.forEach((alias, i) => {
      console.log(`  ${i + 1}. "${alias}"`);
    });
  }

  console.log(`\n📝 For media-index.json, include:`);
  console.log(`  "aliases": [${aliasArray.map(a => `"${a}"`).join(', ')}]`);

  if (suggestions.notes.length > 0) {
    console.log(`\n⚠️  Notes: ${suggestions.notes.join('; ')}`);
  }

  return suggestions;
}

async function suggestBatch(candidatesPath) {
  console.log(`\n📊 Generating alias suggestions for batch...\n`);

  if (!fs.existsSync(candidatesPath)) {
    console.error(`❌ File not found: ${candidatesPath}`);
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(candidatesPath, 'utf8'));
  const suggestions = [];

  for (let i = 0; i < Math.min(candidates.length, 10); i++) {
    const candidate = candidates[i];
    console.log(`[${i + 1}/10] Processing: ${candidate.canonicalTitle}`);

    try {
      const result = await suggestAliases(candidate.canonicalTitle);
      suggestions.push(result);
    } catch (error) {
      console.error(`  Error: ${error.message}`);
    }

    // Rate limiting
    await new Promise(r => setTimeout(r, 500));
  }

  const outputPath = path.join(
    path.dirname(candidatesPath),
    'alias-suggestions.json'
  );
  fs.writeFileSync(outputPath, JSON.stringify(suggestions, null, 2));

  console.log(`\n✅ Saved suggestions to: ${outputPath}`);
  console.log(`   Use these as reference when updating media-index.json`);
}

function printUsage() {
  console.log(`
Suggest Aliases Tool

Queries external sources (anime-offline-database, AniList) to suggest
aliases for a given anime title. Admin tool - human review required.

Commands:
  <title>              Suggest aliases for a title
  --lookup <title>     Same as above (explicit)
  --batch <file>       Generate suggestions for first 10 in candidates.json
  --help               Show this help

Examples:
  node tools/suggest-aliases.js "Bocchi the Rock!"
  node tools/suggest-aliases.js --lookup "Demon Slayer"
  node tools/suggest-aliases.js --batch data/extracted-candidates.json

How it works:
  1. Searches anime-offline-database for matching titles
  2. Queries AniList API for title variants
  3. Generates common abbreviations and variants
  4. Returns deduplicated list

Output:
  • Normalized aliases for use in media-index.json
  • Source attribution (which source suggested which aliases)
  • JSON file for batch processing

Use:
  • Review suggestions carefully before adding to database
  • Discard overly generic or ambiguous aliases
  • Verify matches on LearnNatively/jpdb

Requirements:
  • anime-offline-database.json (run: npm run download)
  • Internet (for AniList queries)
  • Node.js 14+
`);
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case '--lookup':
    if (!arg) {
      console.error('❌ Usage: --lookup <title>');
      process.exit(1);
    }
    suggestAliases(arg);
    break;
  case '--batch':
    if (!arg) {
      console.error('❌ Usage: --batch <candidates-file>');
      process.exit(1);
    }
    suggestBatch(arg);
    break;
  case '--help':
  case '-h':
    printUsage();
    break;
  default:
    if (command && !command.startsWith('-')) {
      // Treat as title
      suggestAliases(command);
    } else if (command) {
      console.error(`❌ Unknown command: ${command}`);
      printUsage();
      process.exit(1);
    } else {
      printUsage();
    }
}
