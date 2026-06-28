#!/usr/bin/env node

/**
 * CSV to Media Index Converter
 * 
 * Converts RATINGS_TEMPLATE.csv into properly formatted media-index.json entries.
 * 
 * Usage:
 *   node tools/csv-to-media-index.js tools/RATINGS_TEMPLATE.csv
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

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
      // Simple CSV parsing (handles quoted fields)
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
    .replace(/-+/g, '-');
}

function rowToMediaEntry(row) {
  const canonicalTitle = row['Canonical Title'];
  
  return {
    id: slugify(canonicalTitle),
    workType: 'anime-series',
    canonicalTitle: canonicalTitle,
    titles: {
      en: canonicalTitle,
      ja: '',
      romaji: ''
    },
    aliases: [normalizeTitle(canonicalTitle)],
    platformAliases: {
      netflix: row['Netflix Alias'] ? [row['Netflix Alias']] : [],
      crunchyroll: row['Crunchyroll Alias'] ? [row['Crunchyroll Alias']] : []
    },
    ratings: {
      learnnatively: {
        level: row['LearnNatively Level'] ? parseInt(row['LearnNatively Level'], 10) : null,
        jlptApprox: row['LearnNatively JLPT'] || '',
        url: row['LearnNatively URL'] || ''
      },
      jpdb: {
        difficulty: row['jpdb Difficulty'] ? parseInt(row['jpdb Difficulty'], 10) : null,
        url: row['jpdb URL'] || ''
      }
    },
    metadata: {
      status: 'verified',
      lastVerified: new Date().toISOString().split('T')[0],
      notes: row['Notes'] || 'Curated from anime-offline-database'
    }
  };
}

async function main() {
  const csvFile = process.argv[2];

  if (!csvFile) {
    console.error('Usage: node tools/csv-to-media-index.js <csv-file>');
    process.exit(1);
  }

  if (!fs.existsSync(csvFile)) {
    console.error(`File not found: ${csvFile}`);
    process.exit(1);
  }

  try {
    console.log(`\n📖 Reading CSV: ${csvFile}`);
    const rows = await parseCSV(csvFile);
    console.log(`✅ Parsed ${rows.length} entries`);

    const entries = rows.map(rowToMediaEntry);
    
    // Sort by canonical title
    entries.sort((a, b) => a.canonicalTitle.localeCompare(b.canonicalTitle));

    // Output as JSON
    const outputPath = path.join(path.dirname(csvFile), '../media-index.json');
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify(entries, null, 2));

    console.log(`\n✅ Generated ${entries.length} entries`);
    console.log(`📁 Saved to: ${outputPath}`);

    // Summary
    const withBothRatings = entries.filter(e => 
      e.ratings.learnnatively.level !== null && 
      e.ratings.jpdb.difficulty !== null
    );
    const withLN = entries.filter(e => e.ratings.learnnatively.level !== null);
    const withJPDB = entries.filter(e => e.ratings.jpdb.difficulty !== null);

    console.log(`\n📊 Statistics:`);
    console.log(`  Total entries: ${entries.length}`);
    console.log(`  With both ratings: ${withBothRatings.length}`);
    console.log(`  With LearnNatively: ${withLN.length}`);
    console.log(`  With jpdb: ${withJPDB.length}`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

main();
