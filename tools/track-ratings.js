#!/usr/bin/env node

/**
 * Rating Progress Tracker
 * 
 * Monitors rating completion across all candidates and batches.
 * Helps identify gaps and prioritize work.
 * 
 * Usage:
 *   node tools/track-ratings.js --overview
 *   node tools/track-ratings.js --by-type
 *   node tools/track-ratings.js --gaps
 *   node tools/track-ratings.js --export-summary <file.json>
 */

const fs = require('fs');
const path = require('path');

const CONFIG = {
  extractedCandidatesPath: path.join(__dirname, '../data/extracted-candidates.json'),
  mediaIndexPath: path.join(__dirname, '../media-index.json'),
};

function loadCandidates() {
  if (!fs.existsSync(CONFIG.extractedCandidatesPath)) {
    throw new Error('Extracted candidates not found. Run: build-database.js --extract');
  }
  return JSON.parse(fs.readFileSync(CONFIG.extractedCandidatesPath, 'utf8'));
}

function showOverview() {
  console.log('\n📊 Rating Completion Overview\n');

  const candidates = loadCandidates();

  const stats = {
    total: candidates.length,
    withBothRatings: 0,
    withLNOnly: 0,
    withJpdbOnly: 0,
    withNeither: 0,
    withNetflixAlias: 0,
    withCrunchyrollAlias: 0,
  };

  for (const entry of candidates) {
    const hasLN = entry.ratings?.learnnatively?.level !== null && entry.ratings?.learnnatively?.level !== undefined;
    const hasJpdb = entry.ratings?.jpdb?.difficulty !== null && entry.ratings?.jpdb?.difficulty !== undefined;

    if (hasLN && hasJpdb) {
      stats.withBothRatings++;
    } else if (hasLN) {
      stats.withLNOnly++;
    } else if (hasJpdb) {
      stats.withJpdbOnly++;
    } else {
      stats.withNeither++;
    }

    if (entry.platformAliases?.netflix?.length > 0) {
      stats.withNetflixAlias++;
    }
    if (entry.platformAliases?.crunchyroll?.length > 0) {
      stats.withCrunchyrollAlias++;
    }
  }

  const percentBoth = ((stats.withBothRatings / stats.total) * 100).toFixed(1);
  const percentLN = ((stats.withLNOnly / stats.total) * 100).toFixed(1);
  const percentJpdb = ((stats.withJpdbOnly / stats.total) * 100).toFixed(1);
  const percentRated = (((stats.withBothRatings + stats.withLNOnly + stats.withJpdbOnly) / stats.total) * 100).toFixed(1);

  console.log(`Total Entries: ${stats.total}`);
  console.log(`\nRating Coverage:`);
  console.log(`  ✅ Both ratings: ${stats.withBothRatings} (${percentBoth}%)`);
  console.log(`  📚 LearnNatively only: ${stats.withLNOnly} (${percentLN}%)`);
  console.log(`  📖 jpdb only: ${stats.withJpdbOnly} (${percentJpdb}%)`);
  console.log(`  ⚠️  No ratings: ${stats.withNeither}`);
  console.log(`\nOverall: ${(stats.withBothRatings + stats.withLNOnly + stats.withJpdbOnly)} titles rated (${percentRated}%)`);

  console.log(`\nPlatform Aliases:`);
  console.log(`  🎬 Netflix: ${stats.withNetflixAlias} (${((stats.withNetflixAlias / stats.total) * 100).toFixed(1)}%)`);
  console.log(`  📺 Crunchyroll: ${stats.withCrunchyrollAlias} (${((stats.withCrunchyrollAlias / stats.total) * 100).toFixed(1)}%)`);

  console.log(`\nNext Steps:`);
  console.log(`  • Need ${stats.withNeither} more titles with at least one rating`);
  console.log(`  • ${stats.withLNOnly} have only LearnNatively (add jpdb)`);
  console.log(`  • ${stats.withJpdbOnly} have only jpdb (add LearnNatively)`);
  console.log(`  • ${stats.total - stats.withNetflixAlias} missing Netflix aliases`);
}

function showByType() {
  console.log('\n📊 Rating Coverage by Anime Type\n');

  const candidates = loadCandidates();

  // Group by type
  const byType = {};
  for (const entry of candidates) {
    const type = entry.workType || 'unknown';
    if (!byType[type]) {
      byType[type] = { total: 0, withBoth: 0, withOne: 0, withNone: 0 };
    }
    byType[type].total++;

    const hasLN = entry.ratings?.learnnatively?.level !== null && entry.ratings?.learnnatively?.level !== undefined;
    const hasJpdb = entry.ratings?.jpdb?.difficulty !== null && entry.ratings?.jpdb?.difficulty !== undefined;

    if (hasLN && hasJpdb) {
      byType[type].withBoth++;
    } else if (hasLN || hasJpdb) {
      byType[type].withOne++;
    } else {
      byType[type].withNone++;
    }
  }

  // Sort by total
  const sorted = Object.entries(byType).sort((a, b) => b[1].total - a[1].total);

  console.log('Type                   Total   Both    One    None   Coverage');
  console.log('─────────────────────────────────────────────────────────────');

  for (const [type, stats] of sorted) {
    const coverage = (((stats.withBoth + stats.withOne) / stats.total) * 100).toFixed(0);
    const typeStr = type.padEnd(20);
    const totalStr = String(stats.total).padStart(5);
    const bothStr = String(stats.withBoth).padStart(5);
    const oneStr = String(stats.withOne).padStart(5);
    const noneStr = String(stats.withNone).padStart(5);
    const coverageStr = `${coverage}%`.padStart(6);

    console.log(`${typeStr} ${totalStr} ${bothStr} ${oneStr} ${noneStr} ${coverageStr}`);
  }
}

function showGaps() {
  console.log('\n🔍 Rating Gaps\n');

  const candidates = loadCandidates();

  // Find gaps
  const noLN = candidates.filter(e => !e.ratings?.learnnatively?.level);
  const noJpdb = candidates.filter(e => !e.ratings?.jpdb?.difficulty);
  const neither = candidates.filter(e => 
    !e.ratings?.learnnatively?.level && !e.ratings?.jpdb?.difficulty
  );

  console.log(`Missing LearnNatively: ${noLN.length}/${candidates.length}`);
  console.log(`  Top 10 by type:`);

  const lnByType = {};
  for (const entry of noLN) {
    const type = entry.workType || 'unknown';
    lnByType[type] = (lnByType[type] || 0) + 1;
  }

  Object.entries(lnByType)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .forEach(([type, count]) => {
      console.log(`    ${type}: ${count}`);
    });

  console.log(`\nMissing jpdb: ${noJpdb.length}/${candidates.length}`);
  console.log(`  Top 10 by type:`);

  const jpdbByType = {};
  for (const entry of noJpdb) {
    const type = entry.workType || 'unknown';
    jpdbByType[type] = (jpdbByType[type] || 0) + 1;
  }

  Object.entries(jpdbByType)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .forEach(([type, count]) => {
      console.log(`    ${type}: ${count}`);
    });

  console.log(`\nNeed Both Ratings: ${neither.length}/${candidates.length}`);
  console.log(`  Examples to prioritize:`);
  neither
    .slice(0, 10)
    .forEach(entry => {
      console.log(`    • ${entry.canonicalTitle}`);
    });
}

function exportSummary(outputFile) {
  console.log(`\n📋 Exporting summary to ${outputFile}...\n`);

  const candidates = loadCandidates();

  const summary = {
    generatedAt: new Date().toISOString(),
    totalTitles: candidates.length,
    stats: {
      withBothRatings: 0,
      withLNOnly: 0,
      withJpdbOnly: 0,
      withNeither: 0,
      withNetflixAlias: 0,
      withCrunchyrollAlias: 0,
    },
    byType: {},
    needsWork: {
      missingBoth: [],
      missingLN: [],
      missingJpdb: [],
    }
  };

  for (const entry of candidates) {
    const hasLN = entry.ratings?.learnnatively?.level !== null && entry.ratings?.learnnatively?.level !== undefined;
    const hasJpdb = entry.ratings?.jpdb?.difficulty !== null && entry.ratings?.jpdb?.difficulty !== undefined;

    // Stats
    if (hasLN && hasJpdb) {
      summary.stats.withBothRatings++;
    } else if (hasLN) {
      summary.stats.withLNOnly++;
    } else if (hasJpdb) {
      summary.stats.withJpdbOnly++;
    } else {
      summary.stats.withNeither++;
    }

    if (entry.platformAliases?.netflix?.length > 0) {
      summary.stats.withNetflixAlias++;
    }
    if (entry.platformAliases?.crunchyroll?.length > 0) {
      summary.stats.withCrunchyrollAlias++;
    }

    // By type
    const type = entry.workType || 'unknown';
    if (!summary.byType[type]) {
      summary.byType[type] = { total: 0, withBoth: 0, withOne: 0 };
    }
    summary.byType[type].total++;
    if (hasLN && hasJpdb) {
      summary.byType[type].withBoth++;
    } else if (hasLN || hasJpdb) {
      summary.byType[type].withOne++;
    }

    // Needs work
    if (!hasLN && !hasJpdb) {
      summary.needsWork.missingBoth.push(entry.canonicalTitle);
    } else if (!hasLN) {
      summary.needsWork.missingLN.push(entry.canonicalTitle);
    } else if (!hasJpdb) {
      summary.needsWork.missingJpdb.push(entry.canonicalTitle);
    }
  }

  fs.writeFileSync(outputFile, JSON.stringify(summary, null, 2));
  console.log(`✅ Exported to ${outputFile}`);
  console.log(`   Size: ${summary.needsWork.missingBoth.length} missing both`);
  console.log(`   Size: ${summary.needsWork.missingLN.length} missing LN`);
  console.log(`   Size: ${summary.needsWork.missingJpdb.length} missing jpdb`);
}

function printUsage() {
  console.log(`
Rating Progress Tracker

Monitors completion and identifies gaps in ratings.

Commands:
  --overview              Show overall completion statistics
  --by-type              Show coverage by anime type
  --gaps                 Show what's missing and prioritize work
  --export-summary <f>   Export summary to JSON file
  --help                 Show this help

Examples:
  node tools/track-ratings.js --overview
  node tools/track-ratings.js --by-type
  node tools/track-ratings.js --gaps
  node tools/track-ratings.js --export-summary progress.json
`);
}

// ============================================================================
// Main
// ============================================================================

const command = process.argv[2];
const arg = process.argv[3];

switch (command) {
  case '--overview':
    showOverview();
    break;
  case '--by-type':
    showByType();
    break;
  case '--gaps':
    showGaps();
    break;
  case '--export-summary':
    if (!arg) {
      console.error('❌ Usage: --export-summary <filename>');
      process.exit(1);
    }
    exportSummary(arg);
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
