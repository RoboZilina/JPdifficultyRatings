# Contributing to JP Difficulty Overlay

Thank you for helping build this community extension!

This project is maintained by and for a small community of Japanese learners. The goal is to show difficulty ratings on Netflix and Crunchyroll using a minimal, local, community-maintained metadata index.

## What You Can Contribute

### Add or Update Entries in `media-index.json`

We welcome contributions to add new titles or update existing ratings.

**What to include:**

- English title
- Japanese title (if available)
- Romaji title
- Common aliases and alternative names
- LearnNatively difficulty level (1–60+)
- LearnNatively approximate JLPT level (N5, N4, N3, N2, N1)
- LearnNatively direct link
- jpdb difficulty number (1–100)
- jpdb direct link
- Platform-specific aliases (as seen on Netflix or Crunchyroll)

**What NOT to include:**

- Subtitles or dialogue
- Scripts or episode information
- Vocabulary lists or example sentences
- Copied descriptions or plot summaries
- Images, posters, or screenshots
- Reviews or user commentary
- Streaming catalog dumps
- Episode counts or season information (unless needed for matching)
- User data or viewing history
- Copyrighted material

### Use Local Mappings

1. Use the extension's **Add local mapping** feature to test new entries
2. Verify your entries are correct
3. Export your mappings as JSON
4. Submit the JSON for community review

### Report Inaccuracies

If a difficulty rating seems wrong or a title is missing:

1. Open an issue or contact a maintainer
2. Provide the title, current rating, and corrected rating
3. Include a link to LearnNatively or jpdb if possible

## Data Entry Rules

### Before Adding

- [ ] Verify the title exists on Netflix or Crunchyroll
- [ ] Check LearnNatively for the rating
- [ ] Check jpdb for the difficulty number
- [ ] Verify the Japanese title is correct
- [ ] Ensure aliases are useful for matching

### Canonical ID Format

Use lowercase, hyphens, no spaces:

✅ `bocchi-the-rock`  
✅ `delicious-in-dungeon`  
✅ `frieren-beyond-journeys-end`  

❌ `BocchiTheRock`  
❌ `bocchi_the_rock`  
❌ `Bocchi the Rock`  

### Title Format

Use the official English title from the source:

✅ `Delicious in Dungeon`  
✅ `Bocchi the Rock!`  
✅ `Frieren: Beyond Journey's End`  

❌ `delicious in dungeon`  
❌ `DELICIOUS IN DUNGEON`  
❌ `Delicious In Dungeon`  

### Aliases

Include common variations:

✅ Original English title  
✅ Common abbreviations  
✅ Japanese title (both with and without spaces/punctuation)  
✅ Romaji variants  
✅ Platform-detected titles  

❌ Overly generic terms  
❌ Single-word aliases that could match unrelated titles  
❌ Misspellings  

### Ratings

**LearnNatively Level:**

- Range: 1–60+
- Consult LearnNatively for the actual level
- Use the exact number provided

**jpdb Difficulty:**

- Range: typically 1–100
- Consult jpdb for the actual difficulty
- Use the exact number provided

**JLPT Approximation:**

- Options: N5, N4, N3, N2, N1
- Use LearnNatively's suggested approximation
- Leave blank if uncertain

### URLs

Include direct links to the titles on LearnNatively and jpdb:

✅ `https://learnnatively.com/series/[id]`  
✅ `https://jpdb.io/search?q=[title]`  

If you cannot find the exact URL, use the homepage:

✅ `https://learnnatively.com/`  
✅ `https://jpdb.io/`  

## Review Checklist

Before submitting a contribution, verify:

- [ ] No copied descriptions or plot summaries
- [ ] No subtitles or dialogue
- [ ] No vocabulary lists or example sentences
- [ ] No images, posters, or screenshots
- [ ] No large external metadata copies
- [ ] All links are valid and accessible
- [ ] Aliases are useful and not overly generic
- [ ] Difficulty values are numeric or null
- [ ] ID is in lowercase-with-hyphens format
- [ ] No duplicate IDs
- [ ] JSON is valid (use a JSON validator)

## Workflow for Adding an Entry

### Step 1: Use Local Mapping

1. Open Netflix or Crunchyroll
2. Navigate to a title page
3. Click **Add local mapping** on the overlay
4. Fill in all details carefully
5. Save the mapping locally

### Step 2: Verify

1. Go to the options page
2. Check your entry in **My Local Mappings**
3. If incorrect, click **Edit** and update
4. Test on the actual page

### Step 3: Export

1. Go to the options page
2. Click **Export as JSON**
3. Download the file

### Step 4: Submit

Send the exported JSON to a maintainer for review.

A reviewer will:

- [ ] Verify all data is accurate
- [ ] Check for forbidden content
- [ ] Ensure proper formatting
- [ ] Test the entry in the extension
- [ ] Merge into `media-index.json` if approved

## Editing the Index Directly

For maintainers or experienced contributors, you can edit `media-index.json` directly.

**Rules:**

1. Use a JSON validator to check syntax before committing
2. Keep entries in alphabetical order by ID
3. Include the metadata section with status and date
4. Write a clear commit message explaining the change
5. Do NOT remove existing entries without discussion

## Platform Aliases

When you detect a title on Netflix or Crunchyroll, note how it appears and add it as a platform alias.

Example:

```json
"platformAliases": {
  "netflix": [
    "DELICIOUS IN DUNGEON",
    "Delicious in Dungeon"
  ],
  "crunchyroll": []
}
```

This helps the extension match titles more reliably.

## Conflict Resolution

If you add an alias that could match multiple titles, we may ask you to:

- Add a more specific alias (e.g., include the author or year)
- Remove the ambiguous alias
- Include additional context in metadata notes

Example of problematic aliases:

❌ `monster` (could match: Monster, Monster Hunter, Monster Strike)  
✅ `naoki urasawa monster` (specific and unambiguous)  

## Questions or Issues

If you're unsure about:

- A rating value
- Whether something is "allowed"
- The correct Japanese title
- How to format an entry

Ask a maintainer before submitting. It's better to clarify than to submit incorrect data.

## Code Changes

The extension intentionally uses plain JavaScript with no frameworks. If you propose code changes:

- [ ] Keep changes minimal
- [ ] Do not add external dependencies
- [ ] Do not add transpilation or bundlers
- [ ] Test in Chrome before submitting
- [ ] Document changes clearly

For larger changes, open an issue first to discuss.

## Thank You!

Your contributions help build a better resource for the Japanese learning community. We appreciate your time and care in maintaining data quality and privacy standards.

頑張ってください！ 🇯🇵

---

**Questions?** Contact a maintainer or open an issue in the community repository.
