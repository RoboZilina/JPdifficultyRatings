#!/usr/bin/env node

/**
 * Rating Validator
 * 
 * Validates rating data for errors and inconsistencies.
 * Catches common data entry mistakes before merging.
 * 
 * Usage:
 *   node tools/validate-ratings.js --candidates
 *   node tools/validate-ratings.js --csv <file.csv>
 *   node tools/validate-ratings.js --strict
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const CONFIG = {
  extractedCandidatesPath: path.join(__dirname, '../data/extracted-candidates.json'),
  mediaIndexPath: path.join(__dirname, '../media-index.json'),
};

class Validator {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.info = [];
  }

  addError(msg) {
    this.errors.push(msg);
  }

  addWarning(msg) {
    this.warnings.push(msg);
  }

  addInfo(msg) {
    this.info.push(msg);
  }

  report() {
    const total = this.errors.length + this.warnings.length;
    
    if (this.errors.length > 0) {
      console.log(`\n❌ Errors (${this.errors.length}):`);
      this.errors.slice(0, 10).forEach(e => console.log(`   • ${e}`));
      if (this.errors.length > 10) {
        console.log(`   ... and ${this.errors.length - 10} more`);
      }
    }

    if (this.warnings.length > 0) {
      console.log(`\n⚠️  Warnings (${this.warnings.length}):`);
      this.warnings.slice(0, 10).forEach(w => console.log(`   • ${w}`));
      if (this.warnings.length > 10) {
        console.log(`   ... and ${this.warnings.length - 10} more`);
      }
    }

    if (this.info.length > 0 && process.argv.includes('--verbose')) {
      console.log(`\nℹ️  Info (${this.info.length}):`);
      this.info.slice(0, 5).forEach(i => console.log(`   • ${i}`));
    }

    console.log(`\n📊 Summary: ${this.errors.length} errors, ${this.warnings.length} warnings`);

    return this.errors.length === 0;
  }
}

function validateCandidates() {
  console.log('\n🔍 Validating extracted candidates...\n');

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));
  const validator = new Validator();

  const seenIds = new Set();
  const seenTitles = new Set();

  for (let i = 0; i < candidates.length; i++) {
    const entry = candidates[i];

    // Check required fields
    if (!entry.id) {
      validator.addError(`Entry ${i}: Missing id`);
    } else if (seenIds.has(entry.id)) {
      validator.addError(`Entry ${i}: Duplicate id "${entry.id}"`);
    } else {
      seenIds.add(entry.id);
    }

    if (!entry.canonicalTitle) {
      validator.addError(`Entry ${i}: Missing canonicalTitle`);
    } else if (seenTitles.has(entry.canonicalTitle.toLowerCase())) {
      validator.addWarning(`Entry ${i}: Duplicate title "${entry.canonicalTitle}"`);
    } else {
      seenTitles.add(entry.canonicalTitle.toLowerCase());
    }

    // Check aliases
    if (!Array.isArray(entry.aliases)) {
      validator.addError(`Entry ${i} (${entry.canonicalTitle}): aliases is not an array`);
    }

    // Check ratings
    if (entry.ratings?.learnnatively?.level !== null && 
        entry.ratings?.learnnatively?.level !== undefined) {
      const ln = entry.ratings.learnnatively.level;
      if (typeof ln !== 'number' || ln < 1 || ln > 100) {
        validator.addWarning(`Entry ${i} (${entry.canonicalTitle}): Invalid LN level ${ln}`);
      }
    }

    if (entry.ratings?.jpdb?.difficulty !== null && 
        entry.ratings?.jpdb?.difficulty !== undefined) {
      const jpdb = entry.ratings.jpdb.difficulty;
      if (typeof jpdb !== 'number' || jpdb < 1 || jpdb > 100) {
        validator.addWarning(`Entry ${i} (${entry.canonicalTitle}): Invalid jpdb difficulty ${jpdb}`);
      }
    }

    // Check JLPT
    const jlpt = entry.ratings?.learnnatively?.jlptApprox;
    if (jlpt && !['N5', 'N4', 'N3', 'N2', 'N1'].includes(jlpt)) {
      validator.addWarning(`Entry ${i} (${entry.canonicalTitle}): Invalid JLPT "${jlpt}"`);
    }

    // Check URLs
    if (entry.ratings?.learnnatively?.url && !entry.ratings.learnnatively.url.startsWith('http')) {
      validator.addWarning(`Entry ${i} (${entry.canonicalTitle}): Invalid LN URL`);
    }
    if (entry.ratings?.jpdb?.url && !entry.ratings.jpdb.url.startsWith('http')) {
      validator.addWarning(`Entry ${i} (${entry.canonicalTitle}): Invalid jpdb URL`);
    }

    // Check work type
    const validTypes = ['tv', 'movie', 'ova', 'ona', 'special', 'anime-series'];
    if (!validTypes.includes(entry.workType?.toLowerCase())) {
      validator.addWarning(`Entry ${i} (${entry.canonicalTitle}): Invalid workType "${entry.workType}"`);
    }
  }

  return validator.report();
}

async function validateCSV(csvFile) {
  console.log(`\n🔍 Validating CSV: ${csvFile}\n`);

  if (!fs.existsSync(csvFile)) {
    console.error(`❌ File not found: ${csvFile}`);
    process.exit(1);
  }

  const rows = [];
  const rl = readline.createInterface({
    input: fs.createReadStream(csvFile),
    crlfDelay: Infinity
  });

  let isHeader = true;
  let headers = [];
  const validator = new Validator();

  return new Promise((resolve) => {
    rl.on('line', (line) => {
      // Parse CSV line
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

    rl.on('close', () => {
      // Validate rows
      const titleIdx = headers.indexOf('Canonical Title');
      const lnIdx = headers.indexOf('LearnNatively Level');
      const jpdbIdx = headers.indexOf('jpdb Difficulty');

      if (titleIdx < 0) {
        validator.addError('CSV missing "Canonical Title" column');
      }

      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const title = row['Canonical Title'];

        if (!title) {
          validator.addError(`Row ${i + 2}: Empty title`);
          continue;
        }

        const ln = row['LearnNatively Level'];
        const jpdb = row['jpdb Difficulty'];

        // At least one rating required
        if (!ln && !jpdb) {
          validator.addWarning(`Row ${i + 2} (${title}): No ratings provided`);
        }

        // Validate LN
        if (ln && ln !== '') {
          const lnNum = parseInt(ln, 10);
          if (isNaN(lnNum) || lnNum < 1 || lnNum > 100) {
            validator.addError(`Row ${i + 2} (${title}): Invalid LN level "${ln}"`);
          }
        }

        // Validate jpdb
        if (jpdb && jpdb !== '') {
          const jpdbNum = parseInt(jpdb, 10);
          if (isNaN(jpdbNum) || jpdbNum < 1 || jpdbNum > 100) {
            validator.addError(`Row ${i + 2} (${title}): Invalid jpdb difficulty "${jpdb}"`);
          }
        }

        // Validate JLPT
        const jlpt = row['LearnNatively JLPT'];
        if (jlpt && !['N5', 'N4', 'N3', 'N2', 'N1'].includes(jlpt)) {
          validator.addWarning(`Row ${i + 2} (${title}): Invalid JLPT "${jlpt}"`);
        }

        // Validate URLs
        const lnUrl = row['LearnNatively URL'];
        const jpdbUrl = row['jpdb URL'];

        if (lnUrl && lnUrl !== '' && !lnUrl.startsWith('http')) {
          validator.addWarning(`Row ${i + 2} (${title}): Invalid LN URL`);
        }
        if (jpdbUrl && jpdbUrl !== '' && !jpdbUrl.startsWith('http')) {
          validator.addWarning(`Row ${i + 2} (${title}): Invalid jpdb URL`);
        }
      }

      console.log(`✅ Parsed ${rows.length} rows`);
      const passed = validator.report();
      resolve(!passed);
    });
  });
}

function strictValidation() {
  console.log('\n🔍 Strict validation (checking for completeness)...\n');

  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    console.error('❌ Extracted candidates not found');
    process.exit(1);
  }

  const candidates = JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));
  const validator = new Validator();

  let highQuality = 0;

  for (const entry of candidates) {
    const hasLN = entry.ratings?.learnnatively?.level !== null && 
                  entry.ratings?.learnnatively?.level !== undefined;
    const hasJpdb = entry.ratings?.jpdb?.difficulty !== null && 
                    entry.ratings?.jpdb?.difficulty !== undefined;
    const hasLNUrl = entry.ratings?.learnnatively?.url && 
                     entry.ratings.learnnatively.url.startsWith('http');
    const hasJpdbUrl = entry.ratings?.jpdb?.url && 
                       entry.ratings.jpdb.url.startsWith('http');

    // High quality: both ratings + both URLs
    if (hasLN && hasJpdb && hasLNUrl && hasJpdbUrl) {
      highQuality++;
    }

    // Missing components
    if (hasLN && !hasLNUrl) {
      validator.addWarning(`${entry.canonicalTitle}: Has LN rating but missing URL`);
    }
    if (hasJpdb && !hasJpdbUrl) {
      validator.addWarning(`${entry.canonicalTitle}: Has jpdb rating but missing URL`);
    }
  }

  console.log(`\n📊 Strict Quality Analysis:`);
  console.log(`   Total: ${candidates.length}`);
  console.log(`   High quality (both + URLs): ${highQuality} (${((highQuality / candidates.length) * 100).toFixed(1)}%)`);
  console.log(`   Target: 50%+ high quality\n`);

  validator.report();
}

function printUsage() {
  console.log(`
Rating Validator

Validates rating data for errors and inconsistencies.

Commands:
  --candidates           Validate extracted-candidates.json
  --csv <file>          Validate a CSV rating batch
  --strict              Check for completeness (ratings + URLs)
  --help                Show this help

Examples:
  node tools/validate-ratings.js --candidates
  node tools/validate-ratings.js --csv batch-001.csv
  node tools/validate-ratings.js --strict

Use --verbose flag for detailed output:
  node tools/validate-ratings.js --candidates --verbose
`);
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case '--candidates':
    validateCandidates();
    break;
  case '--csv':
    if (!arg) {
      console.error('❌ Usage: --csv <file.csv>');
      process.exit(1);
    }
    validateCSV(arg);
    break;
  case '--strict':
    strictValidation();
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
