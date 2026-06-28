#!/usr/bin/env node

/**
 * CSV Batch Generator
 * 
 * Generates CSV templates from extracted-candidates.json for batch rating entry.
 * Useful for creating spreadsheets to share with community for parallel rating work.
 * 
 * Usage:
 *   node tools/generate-csv-batch.js --all
 *   node tools/generate-csv-batch.js --range A D
 *   node tools/generate-csv-batch.js --sample 50
 *   node tools/generate-csv-batch.js --missing-ratings
 */

const fs = require('fs');
const path = require('path');

const CONFIG = {
  extractedCandidatesPath: path.join(__dirname, '../data/extracted-candidates.json'),
  batchOutputDir: path.join(__dirname, '../data/rating-batches'),
};

function createCSVLine(entry) {
  const fields = [
    entry.canonicalTitle,
    '', // LearnNatively Level
    '', // LearnNatively JLPT
    '', // LearnNatively URL
    '', // jpdb Difficulty
    '', // jpdb URL
    entry.platformAliases?.netflix?.[0] || '',
    entry.platformAliases?.crunchyroll?.[0] || '',
    `${entry.workType}` // Notes with type
  ];

  return fields.map(f => {
    // Escape quotes and wrap in quotes if needed
    if (f.includes(',') || f.includes('"') || f.includes('\n')) {
      return `"${f.replace(/"/g, '""')}"`;
    }
    return `"${f}"`;
  }).join(',');
}

function generateCSV(entries, filename) {
  fs.mkdirSync(CONFIG.batchOutputDir, { recursive: true });

  const header = '"Canonical Title","LearnNatively Level","LearnNatively JLPT","LearnNatively URL","jpdb Difficulty","jpdb URL","Netflix Alias","Crunchyroll Alias","Notes"';
  const lines = [header];

  for (const entry of entries) {
    lines.push(createCSVLine(entry));
  }

  const filePath = path.join(CONFIG.batchOutputDir, filename);
  fs.writeFileSync(filePath, lines.join('\n'));

  console.log(`✅ Generated: ${filename}`);
  console.log(`   Entries: ${entries.length}`);
  console.log(`   Path: ${filePath}`);
  console.log();

  return filePath;
}

function generateAllBatches() {
  console.log('\n📋 Generating CSV batches for all candidates...\n');

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found. Run: --extract first');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

  // Batch size for each file
  const BATCH_SIZE = 500;
  const numBatches = Math.ceil(candidates.length / BATCH_SIZE);

  console.log(`📊 Splitting ${candidates.length} titles into ${numBatches} batches of ${BATCH_SIZE}\n`);

  for (let i = 0; i < numBatches; i++) {
    const start = i * BATCH_SIZE;
    const end = Math.min(start + BATCH_SIZE, candidates.length);
    const batch = candidates.slice(start, end);
    const batchNum = String(i + 1).padStart(3, '0');

    generateCSV(batch, `batch-${batchNum}.csv`);
  }

  console.log(`✅ Generated ${numBatches} CSV files in ${CONFIG.batchOutputDir}`);
  console.log(`   Total entries: ${candidates.length}`);
  console.log('\n📝 Instructions:');
  console.log('   1. Open each CSV in Google Sheets or Excel');
  console.log('   2. Assign batches to different people');
  console.log('   3. Have each person fill in the rating columns');
  console.log('   4. Import with: node tools/build-database.js --import-ratings <batch-file.csv>');
}

function generateByRange(startChar, endChar) {
  console.log(`\n📋 Generating CSV for titles starting with ${startChar}-${endChar}...\n`);

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found. Run: --extract first');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

  const filtered = candidates.filter(entry => {
    const firstChar = entry.canonicalTitle[0].toUpperCase();
    return firstChar >= startChar.toUpperCase() && firstChar <= endChar.toUpperCase();
  });

  console.log(`Found ${filtered.length} titles starting with ${startChar}-${endChar}\n`);

  const filename = `batch-${startChar.toUpperCase()}-${endChar.toUpperCase()}.csv`;
  generateCSV(filtered, filename);

  console.log(`📝 Assign this batch to someone for rating completion`);
}

function generateSample(count) {
  console.log(`\n📋 Generating sample CSV with ${count} random titles...\n`);

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found. Run: --extract first');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

  // Shuffle and pick random
  const shuffled = [...candidates].sort(() => Math.random() - 0.5);
  const sample = shuffled.slice(0, Math.min(count, candidates.length));

  generateCSV(sample, `sample-${count}.csv`);

  console.log(`📝 Use this to test the rating import workflow`);
}

function generateMissingRatings() {
  console.log(`\n📋 Generating CSV for titles missing ratings...\n`);

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found. Run: --extract first');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));

  const needsRatings = candidates.filter(entry =>
    !entry.ratings?.learnnatively?.level && !entry.ratings?.jpdb?.difficulty
  );

  console.log(`Found ${needsRatings.length}/${candidates.length} titles without ratings\n`);

  // Create multiple batches for those needing ratings
  const BATCH_SIZE = 500;
  const numBatches = Math.ceil(needsRatings.length / BATCH_SIZE);

  for (let i = 0; i < numBatches; i++) {
    const start = i * BATCH_SIZE;
    const end = Math.min(start + BATCH_SIZE, needsRatings.length);
    const batch = needsRatings.slice(start, end);
    const batchNum = String(i + 1).padStart(3, '0');

    generateCSV(batch, `missing-ratings-${batchNum}.csv`);
  }

  console.log(`✅ Generated ${numBatches} CSVs for titles needing ratings`);
}

function printUsage() {
  console.log(`
CSV Batch Generator

Generates CSV templates from extracted candidates for batch rating entry.
Useful for creating spreadsheets to distribute to community members.

Commands:
  --all                        Generate CSV files for all candidates (500 per file)
  --range <A> <D>             Generate CSV for titles starting with A-D
  --sample <N>                Generate sample CSV with N random titles
  --missing-ratings           Generate CSVs for entries without ratings
  --help                       Show this help

Workflow:

  1. node tools/build-database.js --extract
     (Creates extracted-candidates.json with all 5000 titles)

  2. node tools/generate-csv-batch.js --all
     (Splits into 500-title batches for parallel work)

  3. Share batch-001.csv, batch-002.csv, etc. with community
     (Have different people rate different batches)

  4. node tools/build-database.js --import-ratings batch-001.csv
     (Import completed ratings)

  5. Repeat for each batch

Examples:
  node tools/generate-csv-batch.js --all
  node tools/generate-csv-batch.js --range A D
  node tools/generate-csv-batch.js --sample 100
  node tools/generate-csv-batch.js --missing-ratings
`);
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2];
const arg1 = process.argv[3];
const arg2 = process.argv[4];

switch (command) {
  case '--all':
    generateAllBatches();
    break;
  case '--range':
    if (!arg1 || !arg2) {
      console.error('❌ Usage: --range <START_CHAR> <END_CHAR>');
      console.error('   Example: --range A D');
      process.exit(1);
    }
    generateByRange(arg1, arg2);
    break;
  case '--sample':
    if (!arg1) {
      console.error('❌ Usage: --sample <COUNT>');
      process.exit(1);
    }
    generateSample(parseInt(arg1, 10));
    break;
  case '--missing-ratings':
    generateMissingRatings();
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
