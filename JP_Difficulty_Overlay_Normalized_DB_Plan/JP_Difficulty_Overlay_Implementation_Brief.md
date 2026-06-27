# JP Difficulty Overlay — Implementation Brief for AI Coding Agent

## Project Purpose

Build a private Chrome Manifest V3 extension named **JP Difficulty Overlay**.

The extension adds a small Japanese-learning difficulty overlay to **Netflix** and **Crunchyroll** pages.

The overlay should show locally stored difficulty ratings and links for the currently detected title:

- LearnNatively difficulty level
- LearnNatively approximate JLPT level
- jpdb difficulty rating
- Link to LearnNatively
- Link to jpdb

This extension is for a small private community only. It will be installed manually as an unpacked Chrome extension. It will not be distributed through the Chrome Web Store.

---

## Hard Constraints

These constraints are mandatory.

The extension must **not**:

- scrape Netflix
- scrape Crunchyroll
- scrape LearnNatively
- scrape jpdb
- fetch data from LearnNatively
- fetch data from jpdb
- download subtitles
- read subtitles
- store subtitles
- extract scripts or dialogue
- store vocabulary lists
- store jpdb deck contents
- store copied descriptions
- store images or screenshots
- store user viewing history
- interact with DRM-protected video content
- bypass any platform restrictions

The extension may only use:

- a local `media-index.json` file bundled with the extension
- optional user-created local mappings stored in `chrome.storage.local`
- normal outbound links opened by user clicks

The extension should make **no external network requests** except normal user-initiated navigation when clicking a LearnNatively or jpdb link.

---

## Legal-Safe Data Policy

The local index may contain only minimal human-curated metadata:

```text
Allowed:
- canonical ID
- English title
- Japanese title
- romaji title
- aliases
- LearnNatively difficulty level
- LearnNatively approximate JLPT label
- LearnNatively URL
- jpdb difficulty number
- jpdb URL
```

The local index must not contain:

```text
Not allowed:
- subtitles
- episode dialogue
- scripts
- vocabulary lists
- example sentences
- deck contents
- copied descriptions
- posters
- screenshots
- reviews
- episode summaries
- streaming catalog dumps
- user data
```

---

## Technical Choice

Use a simple private unpacked Chrome extension.

Do not use React.

Do not use TypeScript.

Do not use a bundler.

Do not use a backend.

Do not use external APIs.

Use plain JavaScript, HTML, CSS, and JSON.

---

## Target Project Structure

Create the following files:

```text
jp-difficulty-overlay/
│
├── manifest.json
├── content.js
├── styles.css
├── media-index.json
├── options.html
├── options.js
├── README.md
└── CONTRIBUTING.md
```

---

## Functional Requirements

### 1. Extension Loading

The extension must load as an unpacked Chrome extension through:

```text
chrome://extensions
Developer Mode
Load unpacked
```

### 2. Supported Sites

The extension should run on:

```text
https://www.netflix.com/*
https://www.crunchyroll.com/*
```

### 3. Title Detection

The extension should detect the currently visible title on Netflix or Crunchyroll.

Because both sites are dynamic single-page applications, the extension must:

- run on initial page load
- watch DOM changes
- watch URL changes
- debounce updates
- avoid excessive processing

### 4. Matching

The detected title should be normalized and matched against:

1. bundled `media-index.json`
2. local user mappings from `chrome.storage.local`

Matching should be exact normalized matching for MVP.

No fuzzy matching is required in the first version.

### 5. Overlay

If a title is matched, show a small overlay.

Example:

```text
日本語 Difficulty
LearnNatively: 23 / N3
jpdb: 18 / 100

LearnNatively | jpdb
```

If no title is matched, show:

```text
No community rating found
Detected: <title>

Search LearnNatively | Search jpdb
Add local mapping
```

The search links may simply open the homepage/search page of LearnNatively and jpdb. Do not fetch from those sites.

### 6. Local Mapping

Provide an options page where users can manually add local mappings.

The options page should allow the user to enter:

```text
Detected title
Canonical ID
English title
Japanese title
Romaji title
Aliases
LearnNatively URL
LearnNatively level
LearnNatively JLPT approximation
jpdb URL
jpdb difficulty
```

The mapping should be saved to:

```js
chrome.storage.local.userMappings
```

The local mapping format should match the bundled `media-index.json` format.

---

## File Requirements

---

# manifest.json

Create a Chrome Manifest V3 file.

Required permissions:

```json
"permissions": ["storage"]
```

Required host permissions:

```json
"host_permissions": [
  "https://www.netflix.com/*",
  "https://www.crunchyroll.com/*"
]
```

Do not add host permissions for:

```text
learnnatively.com
jpdb.io
```

The extension only links to those sites. It must not fetch from them.

Use this manifest as the starting point:

```json
{
  "manifest_version": 3,
  "name": "JP Difficulty Overlay",
  "version": "0.1.0",
  "description": "Adds Japanese-learning difficulty ratings to Netflix and Crunchyroll using a local community-maintained index.",
  "permissions": [
    "storage"
  ],
  "host_permissions": [
    "https://www.netflix.com/*",
    "https://www.crunchyroll.com/*"
  ],
  "content_scripts": [
    {
      "matches": [
        "https://www.netflix.com/*",
        "https://www.crunchyroll.com/*"
      ],
      "js": [
        "content.js"
      ],
      "css": [
        "styles.css"
      ],
      "run_at": "document_idle"
    }
  ],
  "web_accessible_resources": [
    {
      "resources": [
        "media-index.json"
      ],
      "matches": [
        "https://www.netflix.com/*",
        "https://www.crunchyroll.com/*"
      ]
    }
  ],
  "options_page": "options.html"
}
```

---

# media-index.json

Create a local JSON array.

Use this format:

```json
[
  {
    "id": "bocchi-the-rock",
    "titles": {
      "en": "Bocchi the Rock!",
      "ja": "ぼっち・ざ・ろっく！",
      "romaji": "Bocchi the Rock"
    },
    "aliases": [
      "bocchi the rock",
      "btr",
      "ぼっちざろっく"
    ],
    "ratings": {
      "learnnatively": {
        "level": 20,
        "jlptApprox": "N3",
        "url": "https://learnnatively.com/"
      },
      "jpdb": {
        "difficulty": 7,
        "url": "https://jpdb.io/"
      }
    }
  }
]
```

Use placeholder URLs initially if exact item URLs are not known.

Do not add copied descriptions, plot summaries, images, vocabulary, or subtitles.

---

# content.js

Implement the full content script.

It must contain:

```text
- initialization
- loading media-index.json
- loading user mappings
- merging indexes
- platform detection
- Netflix title extraction
- Crunchyroll title extraction
- title cleaning
- title normalization
- exact matching
- overlay rendering
- unmatched state rendering
- Add local mapping button behavior
- MutationObserver
- URL change detection
- debounced updates
```

Important implementation details:

## Global State

Use:

```js
let mediaItems = [];
let searchIndex = new Map();
let lastUrl = location.href;
let lastDetectedTitle = null;
let updateTimer = null;
```

## Platform Detection

Implement:

```js
function getPlatform() {
  const host = window.location.hostname;

  if (host.includes("netflix.com")) {
    return "netflix";
  }

  if (host.includes("crunchyroll.com")) {
    return "crunchyroll";
  }

  return "unknown";
}
```

## Load Bundled Index

Implement:

```js
async function loadMediaIndex() {
  const url = chrome.runtime.getURL("media-index.json");
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to load media-index.json: ${response.status}`);
  }

  return response.json();
}
```

## Load User Mappings

Implement:

```js
async function loadUserMappings() {
  const result = await chrome.storage.local.get(["userMappings"]);
  return Array.isArray(result.userMappings) ? result.userMappings : [];
}
```

## Merge Items

Implement:

```js
function mergeItems(baseItems, userItems) {
  return [...baseItems, ...userItems];
}
```

## Build Search Index

Implement:

```js
function buildSearchIndex(items) {
  const map = new Map();

  for (const item of items) {
    const candidates = [
      item.titles?.en,
      item.titles?.ja,
      item.titles?.romaji,
      ...(Array.isArray(item.aliases) ? item.aliases : [])
    ];

    for (const candidate of candidates) {
      const key = normalizeTitle(candidate);

      if (key) {
        map.set(key, item);
      }
    }
  }

  return map;
}
```

## Clean Extracted Title

Implement:

```js
function cleanExtractedTitle(value) {
  if (!value) return null;

  const cleaned = String(value)
    .replace(/\s+/g, " ")
    .trim();

  return cleaned || null;
}
```

## Normalize Title

Implement:

```js
function normalizeTitle(title) {
  if (!title) return "";

  return String(title)
    .toLowerCase()
    .normalize("NFKC")
    .replace(/[!！?？:：'’"“”.,・\-–—_()[\]{}]/g, " ")
    .replace(/\b(season|series|tv|movie|dub|sub|episode|episodes)\b/g, " ")
    .replace(/\bs\d+\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
```

## Netflix Selectors

Use multiple fallbacks.

```js
const NETFLIX_TITLE_SELECTORS = [
  "[data-uia='video-title']",
  ".video-title",
  ".previewModal--player-titleTreatmentWrapper img[alt]",
  ".billboard-title img[alt]",
  "h1"
];
```

Implement:

```js
function extractNetflixTitle() {
  for (const selector of NETFLIX_TITLE_SELECTORS) {
    const element = document.querySelector(selector);

    if (!element) continue;

    const value =
      element.getAttribute("alt") ||
      element.getAttribute("aria-label") ||
      element.textContent;

    const cleaned = cleanExtractedTitle(value);

    if (cleaned) {
      return cleaned;
    }
  }

  return null;
}
```

## Crunchyroll Selectors

Use multiple fallbacks.

```js
const CRUNCHYROLL_TITLE_SELECTORS = [
  "h1",
  "[data-t='series-title']",
  "[data-testid='series-title']",
  ".erc-series-hero h1",
  ".show-title"
];
```

Implement:

```js
function extractCrunchyrollTitle() {
  for (const selector of CRUNCHYROLL_TITLE_SELECTORS) {
    const element = document.querySelector(selector);

    if (!element) continue;

    const value =
      element.getAttribute("aria-label") ||
      element.textContent;

    const cleaned = cleanExtractedTitle(value);

    if (cleaned) {
      return cleaned;
    }
  }

  return null;
}
```

## Extract Current Title

Implement:

```js
function extractCurrentTitle() {
  const platform = getPlatform();

  if (platform === "netflix") {
    return extractNetflixTitle();
  }

  if (platform === "crunchyroll") {
    return extractCrunchyrollTitle();
  }

  return null;
}
```

## Find Match

Implement:

```js
function findMatch(detectedTitle) {
  const key = normalizeTitle(detectedTitle);
  return searchIndex.get(key) || null;
}
```

## Escape Helpers

Implement:

```js
function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
```

## Overlay Root

Implement:

```js
function getOverlayRoot() {
  let root = document.getElementById("jp-difficulty-overlay");

  if (!root) {
    root = document.createElement("div");
    root.id = "jp-difficulty-overlay";
    document.documentElement.appendChild(root);
  }

  return root;
}
```

## Remove Overlay

Implement:

```js
function removeOverlay() {
  const root = document.getElementById("jp-difficulty-overlay");

  if (root) {
    root.remove();
  }
}
```

## Render Overlay

Implement:

```js
function renderOverlay(html) {
  const root = getOverlayRoot();
  root.innerHTML = html;

  const addButton = root.querySelector("#jpdo-add-mapping");

  if (addButton) {
    addButton.addEventListener("click", () => {
      const title = addButton.getAttribute("data-title") || "";
      const url = chrome.runtime.getURL("options.html") + "?title=" + encodeURIComponent(title);
      window.open(url, "_blank", "noopener,noreferrer");
    });
  }
}
```

## Matched Overlay HTML

Implement:

```js
function renderMatchedOverlay(item, detectedTitle) {
  const ln = item.ratings?.learnnatively;
  const jpdb = item.ratings?.jpdb;

  const lnLevel = ln?.level ?? "?";
  const lnJlpt = ln?.jlptApprox ? ` / ${escapeHtml(ln.jlptApprox)}` : "";
  const jpdbDifficulty = jpdb?.difficulty ?? "?";

  const lnLink = ln?.url
    ? `<a class="jpdo-link" href="${escapeAttr(ln.url)}" target="_blank" rel="noopener noreferrer">LearnNatively</a>`
    : "";

  const jpdbLink = jpdb?.url
    ? `<a class="jpdo-link" href="${escapeAttr(jpdb.url)}" target="_blank" rel="noopener noreferrer">jpdb</a>`
    : "";

  return `
    <div class="jpdo-card">
      <div class="jpdo-title">日本語 Difficulty</div>

      <div class="jpdo-row">
        <span class="jpdo-label">Detected:</span>
        <span class="jpdo-muted">${escapeHtml(detectedTitle)}</span>
      </div>

      <div class="jpdo-row">
        <span class="jpdo-label">LearnNatively:</span>
        <span>${lnLevel}${lnJlpt}</span>
      </div>

      <div class="jpdo-row">
        <span class="jpdo-label">jpdb:</span>
        <span>${jpdbDifficulty} / 100</span>
      </div>

      <div class="jpdo-links">
        ${lnLink}
        ${jpdbLink}
      </div>
    </div>
  `;
}
```

## Unmatched Overlay HTML

Implement:

```js
function renderUnmatchedOverlay(detectedTitle) {
  const encoded = encodeURIComponent(detectedTitle);

  return `
    <div class="jpdo-card">
      <div class="jpdo-title">No community rating found</div>

      <div class="jpdo-row">
        <span class="jpdo-label">Detected:</span>
        <span class="jpdo-muted">${escapeHtml(detectedTitle)}</span>
      </div>

      <div class="jpdo-links">
        <a class="jpdo-link" href="https://learnnatively.com/search/?q=${encoded}" target="_blank" rel="noopener noreferrer">Search LearnNatively</a>
        <a class="jpdo-link" href="https://jpdb.io/search?q=${encoded}" target="_blank" rel="noopener noreferrer">Search jpdb</a>
      </div>

      <button class="jpdo-button" id="jpdo-add-mapping" data-title="${escapeAttr(detectedTitle)}">
        Add local mapping
      </button>
    </div>
  `;
}
```

If the exact search URLs do not work correctly on the source sites, fall back to their homepages. Do not implement scraping.

## Update Overlay

Implement:

```js
async function updateOverlay() {
  const platform = getPlatform();

  if (platform === "unknown") {
    removeOverlay();
    return;
  }

  const detectedTitle = extractCurrentTitle();

  if (!detectedTitle) {
    removeOverlay();
    return;
  }

  if (detectedTitle === lastDetectedTitle) {
    return;
  }

  lastDetectedTitle = detectedTitle;

  const match = findMatch(detectedTitle);

  if (match) {
    renderOverlay(renderMatchedOverlay(match, detectedTitle));
  } else {
    renderOverlay(renderUnmatchedOverlay(detectedTitle));
  }
}
```

## Debounced Update

Implement:

```js
function scheduleUpdate() {
  clearTimeout(updateTimer);

  updateTimer = setTimeout(() => {
    updateOverlay().catch(console.error);
  }, 400);
}
```

## Observe Page Changes

Implement:

```js
function observePageChanges() {
  const observer = new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      lastDetectedTitle = null;
      scheduleUpdate();
      return;
    }

    scheduleUpdate();
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });

  setInterval(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      lastDetectedTitle = null;
      scheduleUpdate();
    }
  }, 1000);
}
```

## Initialize

Implement:

```js
async function init() {
  const baseItems = await loadMediaIndex();
  const userItems = await loadUserMappings();

  mediaItems = mergeItems(baseItems, userItems);
  searchIndex = buildSearchIndex(mediaItems);

  await updateOverlay();

  observePageChanges();
}

init().catch(console.error);
```

---

# styles.css

Create a clean, unobtrusive overlay style.

```css
#jp-difficulty-overlay {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 2147483647;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #ffffff;
  pointer-events: auto;
}

.jpdo-card {
  background: rgba(20, 20, 20, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 12px;
  padding: 10px 12px;
  min-width: 230px;
  max-width: 340px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.38);
  backdrop-filter: blur(8px);
}

.jpdo-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 7px;
}

.jpdo-row {
  font-size: 13px;
  line-height: 1.45;
  margin-top: 3px;
}

.jpdo-label {
  font-weight: 600;
  margin-right: 4px;
}

.jpdo-muted {
  color: rgba(255, 255, 255, 0.72);
}

.jpdo-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 9px;
}

.jpdo-link {
  color: #8fd3ff;
  text-decoration: none;
  font-size: 12px;
}

.jpdo-link:hover {
  text-decoration: underline;
}

.jpdo-button {
  margin-top: 9px;
  background: #333333;
  color: #ffffff;
  border: 1px solid #555555;
  border-radius: 8px;
  padding: 6px 9px;
  cursor: pointer;
  font-size: 12px;
}

.jpdo-button:hover {
  background: #444444;
}
```

---

# options.html

Create a basic options page for adding local mappings.

It should contain:

- a form
- inputs for title data
- inputs for ratings
- save button
- list of stored local mappings
- export button
- clear local mappings button

Use this as the initial structure:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>JP Difficulty Overlay Options</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      max-width: 900px;
      margin: 32px auto;
      padding: 0 20px;
      line-height: 1.5;
    }

    label {
      display: block;
      font-weight: 600;
      margin-top: 14px;
    }

    input,
    textarea {
      width: 100%;
      box-sizing: border-box;
      padding: 8px;
      margin-top: 4px;
    }

    textarea {
      min-height: 70px;
    }

    button {
      margin-top: 16px;
      margin-right: 8px;
      padding: 8px 12px;
      cursor: pointer;
    }

    pre {
      background: #f4f4f4;
      padding: 12px;
      overflow: auto;
    }

    .hint {
      color: #555;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <h1>JP Difficulty Overlay Options</h1>

  <p class="hint">
    Add local mappings here. Store only title aliases, difficulty ratings, and source links.
    Do not store subtitles, vocabulary lists, copied descriptions, images, or episode text.
  </p>

  <form id="mapping-form">
    <label>
      Detected title
      <input id="detected-title" type="text">
    </label>

    <label>
      Canonical ID
      <input id="canonical-id" type="text" placeholder="example-title-id">
    </label>

    <label>
      English title
      <input id="title-en" type="text">
    </label>

    <label>
      Japanese title
      <input id="title-ja" type="text">
    </label>

    <label>
      Romaji title
      <input id="title-romaji" type="text">
    </label>

    <label>
      Aliases, one per line
      <textarea id="aliases"></textarea>
    </label>

    <label>
      LearnNatively URL
      <input id="ln-url" type="url">
    </label>

    <label>
      LearnNatively level
      <input id="ln-level" type="number" min="0" step="1">
    </label>

    <label>
      LearnNatively JLPT approximation
      <input id="ln-jlpt" type="text" placeholder="N5, N4, N3, N2, N1, N1+">
    </label>

    <label>
      jpdb URL
      <input id="jpdb-url" type="url">
    </label>

    <label>
      jpdb difficulty
      <input id="jpdb-difficulty" type="number" min="0" max="100" step="1">
    </label>

    <button type="submit">Save local mapping</button>
  </form>

  <hr>

  <button id="export-json">Export local mappings</button>
  <button id="clear-mappings">Clear local mappings</button>

  <h2>Current Local Mappings</h2>
  <pre id="current-mappings"></pre>

  <script src="options.js"></script>
</body>
</html>
```

---

# options.js

Implement options page logic.

Required behavior:

- read `title` query parameter and prefill detected title
- save form data into `chrome.storage.local.userMappings`
- render current local mappings
- export mappings as JSON
- clear local mappings after confirmation

Implementation:

```js
function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFKC")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

async function getUserMappings() {
  const result = await chrome.storage.local.get(["userMappings"]);
  return Array.isArray(result.userMappings) ? result.userMappings : [];
}

async function setUserMappings(mappings) {
  await chrome.storage.local.set({ userMappings: mappings });
}

function getValue(id) {
  return document.getElementById(id).value.trim();
}

function getNumberValue(id) {
  const value = getValue(id);

  if (!value) {
    return null;
  }

  const parsed = Number(value);

  return Number.isFinite(parsed) ? parsed : null;
}

function buildMappingFromForm() {
  const detectedTitle = getValue("detected-title");
  const titleEn = getValue("title-en");
  const titleJa = getValue("title-ja");
  const titleRomaji = getValue("title-romaji");
  const canonicalId = getValue("canonical-id") || slugify(titleEn || titleRomaji || detectedTitle);

  const aliases = getValue("aliases")
    .split("\n")
    .map(value => value.trim())
    .filter(Boolean);

  if (detectedTitle && !aliases.includes(detectedTitle)) {
    aliases.unshift(detectedTitle);
  }

  return {
    id: canonicalId,
    titles: {
      en: titleEn,
      ja: titleJa,
      romaji: titleRomaji
    },
    aliases,
    ratings: {
      learnnatively: {
        level: getNumberValue("ln-level"),
        jlptApprox: getValue("ln-jlpt"),
        url: getValue("ln-url")
      },
      jpdb: {
        difficulty: getNumberValue("jpdb-difficulty"),
        url: getValue("jpdb-url")
      }
    }
  };
}

async function renderMappings() {
  const mappings = await getUserMappings();
  document.getElementById("current-mappings").textContent = JSON.stringify(mappings, null, 2);
}

async function saveMapping(event) {
  event.preventDefault();

  const mapping = buildMappingFromForm();

  if (!mapping.id) {
    alert("Canonical ID is required.");
    return;
  }

  const mappings = await getUserMappings();
  const nextMappings = mappings.filter(item => item.id !== mapping.id);
  nextMappings.push(mapping);

  await setUserMappings(nextMappings);
  await renderMappings();

  alert("Local mapping saved.");
}

async function exportMappings() {
  const mappings = await getUserMappings();
  const blob = new Blob([JSON.stringify(mappings, null, 2)], {
    type: "application/json"
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "jp-difficulty-local-mappings.json";
  link.click();

  URL.revokeObjectURL(url);
}

async function clearMappings() {
  const confirmed = confirm("Clear all local mappings?");

  if (!confirmed) {
    return;
  }

  await setUserMappings([]);
  await renderMappings();
}

function prefillFromQuery() {
  const title = getQueryParam("title");

  if (title) {
    document.getElementById("detected-title").value = title;
    document.getElementById("title-en").value = title;
    document.getElementById("canonical-id").value = slugify(title);
    document.getElementById("aliases").value = title;
  }
}

document.getElementById("mapping-form").addEventListener("submit", saveMapping);
document.getElementById("export-json").addEventListener("click", exportMappings);
document.getElementById("clear-mappings").addEventListener("click", clearMappings);

prefillFromQuery();
renderMappings().catch(console.error);
```

---

# README.md

Create this README:

```markdown
# JP Difficulty Overlay

Private Chrome extension for adding Japanese-learning difficulty ratings to Netflix and Crunchyroll pages.

## Purpose

This extension shows a small overlay with locally stored Japanese difficulty ratings for media titles.

It uses a local community-maintained JSON file and optional local user mappings.

## Supported Sites

- Netflix
- Crunchyroll

## Displayed Data

The overlay may show:

- LearnNatively difficulty level
- LearnNatively approximate JLPT level
- jpdb difficulty rating
- Link to LearnNatively
- Link to jpdb

## Privacy and Legal Scope

This extension does not scrape external sites.

It does not fetch from LearnNatively or jpdb.

It does not download subtitles.

It does not read or store video data.

It does not store viewing history.

It does not collect personal data.

## Data Rules

Allowed in `media-index.json`:

- title names
- aliases
- difficulty ratings
- source links

Not allowed:

- subtitles
- dialogue
- scripts
- vocabulary lists
- copied descriptions
- images
- screenshots
- deck contents
- streaming catalog dumps

## Installation

1. Download or clone this repository.
2. Open Chrome.
3. Go to `chrome://extensions`.
4. Enable Developer Mode.
5. Click `Load unpacked`.
6. Select the `jp-difficulty-overlay` folder.
7. Open Netflix or Crunchyroll.

## Updating the Shared Index

Edit `media-index.json`.

Add only minimal metadata.

## Local Mappings

If a title is not found, click `Add local mapping`.

This opens the options page where you can manually add a local mapping.

Local mappings are stored in Chrome local extension storage.

They are not uploaded anywhere.

## Development Notes

The extension intentionally avoids automation against external rating sites.

This keeps the project simple, private, and legally safer.
```

---

# CONTRIBUTING.md

Create this contribution guide:

```markdown
# Contributing to JP Difficulty Overlay

This project is for a small private community of Japanese learners.

The goal is to show difficulty ratings on Netflix and Crunchyroll using a minimal local metadata index.

## Allowed Contributions

You may add:

- English title
- Japanese title
- romaji title
- common aliases
- LearnNatively difficulty level
- LearnNatively approximate JLPT label
- LearnNatively URL
- jpdb difficulty number
- jpdb URL

## Forbidden Contributions

Do not add:

- subtitles
- dialogue
- scripts
- vocabulary lists
- example sentences
- jpdb deck contents
- copied descriptions
- reviews
- images
- screenshots
- posters
- streaming catalog dumps
- user viewing history
- account data

## Data Entry Rules

1. Manually verify the title.
2. Add only minimal rating data.
3. Add useful aliases for matching.
4. Do not scrape source sites.
5. Do not copy large metadata.
6. Do not include copyrighted text.
7. Prefer direct source links.
8. Keep each entry small.

## Review Checklist

Before accepting a new entry, check:

- no copied descriptions
- no subtitles
- no vocabulary lists
- no images
- no large external metadata
- links are valid
- aliases are useful
- difficulty values are numeric
```

---

## MVP Acceptance Criteria

The MVP is complete when all of the following are true:

```text
- Extension loads as an unpacked Chrome extension.
- Extension runs on Netflix.
- Extension runs on Crunchyroll.
- media-index.json loads successfully.
- User mappings load from chrome.storage.local.
- Platform detection works.
- Title extraction works on at least one Netflix title/detail page.
- Title extraction works on at least one Crunchyroll series page.
- Exact normalized alias matching works.
- Overlay appears for a known title.
- Unknown title displays fallback UI.
- Add local mapping opens the options page.
- Options page can save local mappings.
- Options page can export local mappings.
- Options page can clear local mappings.
- No external fetches are made to LearnNatively or jpdb.
- LearnNatively and jpdb are only opened by user clicking links.
```

---

## Suggested Implementation Order

Implement in this exact order:

```text
1. Create project files.
2. Implement manifest.json.
3. Implement media-index.json with one sample entry.
4. Implement styles.css.
5. Implement content.js loading logic.
6. Implement title normalization.
7. Implement search index.
8. Implement platform detection.
9. Implement Netflix title extraction.
10. Implement Crunchyroll title extraction.
11. Implement overlay rendering.
12. Implement unmatched overlay.
13. Implement MutationObserver and debounced updates.
14. Implement options.html.
15. Implement options.js.
16. Implement README.md.
17. Implement CONTRIBUTING.md.
18. Test in Chrome as unpacked extension.
```

---

## Testing Plan

### Test 1: Extension Loads

Open:

```text
chrome://extensions
```

Enable Developer Mode.

Load the extension folder.

Expected:

```text
JP Difficulty Overlay appears in the extensions list.
No manifest errors.
```

### Test 2: Crunchyroll Known Title

1. Add a known title to `media-index.json`.
2. Open the matching Crunchyroll page.
3. Wait for the page to load.

Expected:

```text
Overlay appears.
Detected title is shown.
LearnNatively rating is shown.
jpdb rating is shown.
Links are clickable.
```

### Test 3: Netflix Known Title

1. Add a known Netflix title or anime to `media-index.json`.
2. Open the Netflix detail/title page.
3. Wait for the page to load.

Expected:

```text
Overlay appears.
Detected title is shown.
Rating information appears.
```

### Test 4: Unknown Title

Open a title not present in the index.

Expected:

```text
No community rating found.
Detected title is shown.
Search links are shown.
Add local mapping button is shown.
```

### Test 5: Local Mapping

1. Click `Add local mapping`.
2. Fill in the options form.
3. Save the mapping.
4. Return to the media page.
5. Refresh.

Expected:

```text
The locally added mapping is used.
Overlay displays the saved rating.
```

### Test 6: No External Background Requests

Open DevTools Network tab.

Expected:

```text
The extension loads only local extension files.
No automatic requests are made to LearnNatively or jpdb.
```

---

## Future Improvements After MVP

Do not implement these until the MVP works.

Possible future improvements:

```text
- better selectors for Netflix
- better selectors for Crunchyroll
- optional fuzzy matching
- import local mappings from JSON
- community data validation script
- badge collapse/expand toggle
- per-site enable/disable setting
- overlay position setting
- dark/light UI setting
```

Still do not add scraping or external fetching.

---

## Final Guiding Principle

Prefer this:

```text
manual data
small local JSON
exact matching
simple overlay
minimal permissions
no scraping
```

Avoid this:

```text
automatic scraping
external APIs
large metadata copies
subtitle extraction
video interaction
complex UI before MVP
```

End of implementation brief.
