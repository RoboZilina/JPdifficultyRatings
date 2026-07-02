# JP Difficulty Overlay — New PC Setup Guide

## Prerequisites

- **A Chromium browser** — Chrome, Edge, Brave, Opera, or Vivaldi
- **Nothing else** — no Node.js, no Python, no API keys, no internet setup

---

## Step 1: Get the Extension Files

You only need the `jp-difficulty-overlay` folder. The 5,820-entry database is bundled inside it.

### Option A — Clone from GitHub

```bash
git clone https://github.com/RoboZilina/JPdifficultyRatings.git
```

The folder is at `JPdifficultyRatings/jp-difficulty-overlay/`.

### Option B — Copy from USB / Cloud

Copy the entire `jp-difficulty-overlay` folder from your other PC via USB drive, Dropbox, Google Drive, etc.

> ⚠️ Keep it as a folder — do NOT zip it. Chrome cannot load zipped extensions.

---

## Step 2: Install in Chrome

1. Open Chrome and go to **`chrome://extensions`**
2. Enable **Developer Mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `jp-difficulty-overlay` folder
5. The extension appears in your toolbar with a puzzle-piece icon

---

## Step 3: Verify It Works

1. Open **Netflix** or **Crunchyroll** in a new tab
2. Navigate to any anime or show title page (not the browse/search page)
3. Look for the difficulty overlay near the title or description area

You should see something like:

```
日本語 Difficulty
LearnNatively: 20 / N3
jpdb: 7 / 100

[LearnNatively] [jpdb]
```

If the title isn't in the database, the overlay will show search buttons instead.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No overlay appears | You're on a browse/search page, not a title page. Click into a specific show. |
| "No community rating found" | That title isn't in the database yet. Use the search buttons to check LearnNatively / jpdb manually, or add a local mapping. |
| Extension icon is greyed out | The extension may not be enabled on that site. Check `chrome://extensions` → this extension → toggle "Site access" to "On all sites". |
| Error: "Manifest file is missing" | You loaded a zip file or didn't select the correct folder. Unzip first, or select the `jp-difficulty-overlay` folder specifically. |
| Changes from a newer version aren't showing | Go to `chrome://extensions` → click the refresh icon on this extension's card, then reload the Netflix/Crunchyroll page. |

---

## Updating to a Newer Version

When the community releases an update:

1. Pull the latest files: `git pull origin main`
2. Or copy the new `jp-difficulty-overlay` folder over the old one
3. Go to `chrome://extensions` → click the **refresh** icon on this extension's card
4. Reload any open Netflix/Crunchyroll tabs

That's it. No re-installation needed.