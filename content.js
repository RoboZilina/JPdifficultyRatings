// JP Difficulty Overlay - Content Script

// ============================================================================
// Global State
// ============================================================================

let mediaItems = [];
let searchIndex = new Map();
let lastUrl = location.href;
let lastDetectedTitle = null;
let updateTimer = null;
let currentOverlayElement = null;

// ============================================================================
// Platform Detection
// ============================================================================

function getPlatform() {
  const host = window.location.hostname;

  if (host.includes("netflix.com")) {
    return "netflix";
  }

  if (host.includes("crunchyroll.com")) {
    return "crunchyroll";
  }

  if (host.includes("disneyplus.com")) {
    return "disneyplus";
  }

  return "unknown";
}

// ============================================================================
// Load Bundled Media Index
// ============================================================================

async function loadMediaIndex() {
  const url = chrome.runtime.getURL("media-index.json");
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to load media-index.json: ${response.status}`);
  }

  return await response.json();
}

// ============================================================================
// Chrome Storage Helpers
// ============================================================================

function getUserMappings() {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get(["userMappings"], (result) => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
        return;
      }

      const mappings = result.userMappings || [];
      resolve(mappings);
    });
  });
}

// ============================================================================
// Title Normalization
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

function normalizeTitleCompact(title) {
  return normalizeTitle(title).replace(/\s+/g, "");
}

// ============================================================================
// Build Search Index
// ============================================================================

async function buildSearchIndex() {
  const bundledItems = await loadMediaIndex();
  const userMappings = await getUserMappings();

  mediaItems = [...bundledItems, ...userMappings];
  searchIndex.clear();

  console.log("[JP Difficulty Overlay] Building search index with", mediaItems.length, "items");

  for (const item of mediaItems) {
    // Index canonical title
    if (item.canonicalTitle) {
      addToSearchIndex(item.canonicalTitle, item.id);
    }

    // Index all titles
    if (item.titles) {
      if (item.titles.en) addToSearchIndex(item.titles.en, item.id);
      if (item.titles.ja) addToSearchIndex(item.titles.ja, item.id);
      if (item.titles.romaji) addToSearchIndex(item.titles.romaji, item.id);
    }

    // Index aliases
    if (item.aliases && Array.isArray(item.aliases)) {
      for (const alias of item.aliases) {
        addToSearchIndex(alias, item.id);
      }
    }

    // Index platform-specific aliases
    if (item.platformAliases) {
      const platformAliases = item.platformAliases.netflix || [];
      const crunchyrollAliases = item.platformAliases.crunchyroll || [];
      const disneyplusAliases = item.platformAliases.disneyplus || [];

      for (const alias of [...platformAliases, ...crunchyrollAliases, ...disneyplusAliases]) {
        addToSearchIndex(alias, item.id);
      }
    }
  }

  console.log("[JP Difficulty Overlay] Search index built with", searchIndex.size, "keys");
}

function addToSearchIndex(alias, itemId) {
  if (!alias || !itemId) return;

  const normal = normalizeTitle(alias);
  const compact = normalizeTitleCompact(alias);

  if (normal) searchIndex.set(normal, itemId);
  if (compact && compact !== normal) searchIndex.set(compact, itemId);
}

// ============================================================================
// Search and Matching
// ============================================================================

function findMediaItem(detectedTitle) {
  if (!detectedTitle) {
    console.log("[JP Difficulty Overlay] No title detected");
    return null;
  }

  const normalKey = normalizeTitle(detectedTitle);
  const compactKey = normalizeTitleCompact(detectedTitle);

  console.log("[JP Difficulty Overlay] Detected title:", detectedTitle);
  console.log("[JP Difficulty Overlay] Normalized key:", normalKey);
  console.log("[JP Difficulty Overlay] Compact key:", compactKey);
  console.log("[JP Difficulty Overlay] Search index size:", searchIndex.size);
  console.log("[JP Difficulty Overlay] Sample keys:", Array.from(searchIndex.keys()).slice(0, 10));

  const itemId = searchIndex.get(normalKey) || searchIndex.get(compactKey);

  console.log("[JP Difficulty Overlay] Matched ID:", itemId);

  if (!itemId) {
    console.log("[JP Difficulty Overlay] No match found in search index");
    return null;
  }

  const item = mediaItems.find((item) => item.id === itemId) || null;
  console.log("[JP Difficulty Overlay] Found item:", item?.canonicalTitle);
  return item;
}

// ============================================================================
// Title Extraction - Netflix
// ============================================================================

function extractNetflixTitle() {
  // Netflix uses dynamic page titles. Try multiple strategies.

  // Strategy 1: Page title from document.title
  const documentTitle = document.title;
  if (documentTitle && documentTitle !== "Netflix") {
    // Remove common suffixes
    const cleaned = documentTitle
      .replace(/\s*[-–]\s*Netflix.*$/i, "")
      .replace(/\s*\|\s*Netflix.*$/i, "");
    if (cleaned && cleaned.length > 0) {
      return cleaned;
    }
  }

  // Strategy 2: Look for title in h1 elements
  const h1Elements = document.querySelectorAll("h1");
  for (const h1 of h1Elements) {
    const text = h1.textContent?.trim();
    if (text && text.length > 2 && text.length < 200) {
      return text;
    }
  }

  // Strategy 3: Look for role="heading" aria-level="1"
  const mainHeading = document.querySelector('[role="heading"][aria-level="1"]');
  if (mainHeading) {
    const text = mainHeading.textContent?.trim();
    if (text && text.length > 2) {
      return text;
    }
  }

  // Strategy 4: Look in main content area
  const main = document.querySelector("main");
  if (main) {
    const headings = main.querySelectorAll("h1, h2");
    for (const heading of headings) {
      const text = heading.textContent?.trim();
      if (text && text.length > 2 && text.length < 200) {
        return text;
      }
    }
  }

  return null;
}

// ============================================================================
// Title Extraction - Crunchyroll
// ============================================================================

function extractCrunchyrollTitle() {
  // Crunchyroll uses dynamic titles. Try multiple strategies.

  // Helper to clean title
  const cleanTitle = (text) => {
    if (!text) return text;
    return text
      .replace(/^(Watch|Stream|Play|Continue|Start|Read)\s+/i, "")
      .replace(/\s+(Subbed|Dubbed|Sub|Dub|Series|Movie|OVA|on Crunchyroll)(\s|$)/i, "$2")
      .trim();
  };

  // Strategy 1: Page title
  const documentTitle = document.title;
  if (documentTitle && documentTitle !== "Crunchyroll") {
    let text = documentTitle
      .replace(/\s*[-–]\s*Crunchyroll.*$/i, "")
      .replace(/\s*\|\s*Crunchyroll.*$/i, "");
    text = cleanTitle(text);
    if (text && text.length > 2 && text.length < 200) {
      return text;
    }
  }

  // Strategy 2: h1 elements specifically (these usually have the series name)
  const h1s = document.querySelectorAll("h1");
  for (const h1 of h1s) {
    let text = h1.textContent?.trim();
    if (text && text.length > 2 && text.length < 200 && !text.includes("Crunchyroll")) {
      text = cleanTitle(text);
      if (text && text.length > 2) {
        return text;
      }
    }
  }

  // Strategy 3: Look for title in common containers
  const titleElements = document.querySelectorAll('[class*="title"], [class*="heading"], h2');
  for (const element of titleElements) {
    let text = element.textContent?.trim();
    if (
      text &&
      text.length > 2 &&
      text.length < 200 &&
      !text.includes("Crunchyroll")
    ) {
      text = cleanTitle(text);
      if (text && text.length > 2) {
        return text;
      }
    }
  }

  // Strategy 4: Check for data attributes
  const titleAttr = document.querySelector("[data-title], [data-series]");
  if (titleAttr) {
    const text =
      titleAttr.getAttribute("data-title") ||
      titleAttr.getAttribute("data-series");
    if (text) return cleanTitle(text);
  }

  // Strategy 5: Fallback to main content
  const main = document.querySelector("main, [role='main']");
  if (main) {
    const heading = main.querySelector("h1, h2");
    if (heading) {
      let text = heading.textContent?.trim();
      if (text && text.length > 2) {
        text = cleanTitle(text);
        if (text && text.length > 2) {
          return text;
        }
      }
    }
  }

  return null;
}

// ============================================================================
// Title Extraction - DisneyPlus
// ============================================================================

function extractDisneyPlusTitle() {
  // DisneyPlus uses dynamic page titles. Try multiple strategies.

  // Generic page titles to skip (homepage, navigation, etc.)
  const genericTitles = [
    "welcome back", "home", "search", "my stuff", "originals",
    "movies", "series", "tv", "settings", "profile", "profiles",
    "browse", "for you", "continue watching", "my list", "trending",
    "new to disney+", "popular", "recommended", "collections",
    "genres", "coming soon", "leaving soon", "extras", "trailers",
    "behind the scenes", "bloopers", "deleted scenes", "music videos",
    "short", "featurette", "bonus", "watchlist"
  ];

  function isGeneric(text) {
    if (!text) return true;
    const lower = text.toLowerCase().trim();
    if (lower.length < 3) return true;
    return genericTitles.includes(lower);
  }

  // Strategy 1: Page title from document.title
  const documentTitle = document.title;
  if (documentTitle && documentTitle !== "Disney+" && documentTitle !== "Disney Plus") {
    // Remove common suffixes
    const cleaned = documentTitle
      .replace(/\s*[-–]\s*Disney\+.*$/i, "")
      .replace(/\s*\|\s*Disney\+.*$/i, "")
      .replace(/\s*[-–]\s*Disney Plus.*$/i, "")
      .replace(/\s*\|\s*Disney Plus.*$/i, "")
      .trim();
    if (cleaned && cleaned.length > 0 && !isGeneric(cleaned)) {
      return cleaned;
    }
  }

  // Strategy 2: Look for title in h1 elements
  const h1Elements = document.querySelectorAll("h1");
  for (const h1 of h1Elements) {
    const text = h1.textContent?.trim();
    if (text && text.length > 2 && text.length < 200 && !isGeneric(text)) {
      return text;
    }
  }

  // Strategy 3: Look for role="heading" aria-level="1"
  const mainHeading = document.querySelector('[role="heading"][aria-level="1"]');
  if (mainHeading) {
    const text = mainHeading.textContent?.trim();
    if (text && text.length > 2 && !isGeneric(text)) {
      return text;
    }
  }

  // Strategy 4: Look in main content area
  const main = document.querySelector("main");
  if (main) {
    const headings = main.querySelectorAll("h1, h2");
    for (const heading of headings) {
      const text = heading.textContent?.trim();
      if (text && text.length > 2 && text.length < 200 && !isGeneric(text)) {
        return text;
      }
    }
  }

  return null;
}

// ============================================================================
// Detect Title Based on Platform
// ============================================================================

function detectCurrentTitle() {
  const platform = getPlatform();

  if (platform === "netflix") {
    return extractNetflixTitle();
  }

  if (platform === "crunchyroll") {
    return extractCrunchyrollTitle();
  }

  if (platform === "disneyplus") {
    return extractDisneyPlusTitle();
  }

  return null;
}

// ============================================================================
// Overlay Rendering — Hybrid UI
// ============================================================================

function makeButton(text, className, clickHandler) {
  const btn = document.createElement("button");
  btn.className = className;
  btn.textContent = text;
  if (clickHandler) btn.addEventListener("click", clickHandler);
  return btn;
}

function makeLink(text, className, url) {
  const a = document.createElement("a");
  a.className = className;
  a.href = url;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.textContent = text;
  return a;
}

// ===== Build fallback/search URLs =====
function buildFallbackUrl(type, titleQ) {
  switch (type) {
    case 'search-learnnatively':
      // Google search limited to learnnatively.com
      return `https://www.google.com/search?q=site:learnnatively.com "${titleQ}"`;
    case 'search-jpdb':
      // Google search limited to jpdb.io
      return `https://www.google.com/search?q=site:jpdb.io "${titleQ}"`;
    case 'jpdb-anime-list':
      // Direct link to jpdb's anime difficulty list
      return 'https://jpdb.io/anime';
    default:
      return '#';
  }
}

function createHybridOverlay(detectedTitle, item) {
  const container = document.createElement("div");
  container.className = "jp-difficulty-overlay-container";

  const overlay = document.createElement("div");
  overlay.className = `jp-difficulty-overlay${item ? "" : " unmatched"}`;

  // Close button
  const closeBtn = document.createElement("button");
  closeBtn.className = "jp-difficulty-close";
  closeBtn.textContent = "×";
  closeBtn.setAttribute("aria-label", "Close overlay");
  closeBtn.addEventListener("click", () => container.remove());

  // Title
  const titleEl = document.createElement("h3");
  titleEl.textContent = "JP Difficulty";

  overlay.appendChild(closeBtn);
  overlay.appendChild(titleEl);

  // Editable title input
  const inputGroup = document.createElement("div");
  inputGroup.className = "jp-difficulty-input-group";

  const titleInput = document.createElement("input");
  titleInput.type = "text";
  titleInput.className = "jp-difficulty-title-input";
  titleInput.value = detectedTitle || "";
  titleInput.placeholder = "Title or search query...";

  const refreshBtn = makeButton("↻", "jp-difficulty-refresh-btn", () => {
    lastDetectedTitle = null;
    updateOverlayWithTitle(titleInput.value.trim());
  });

  inputGroup.appendChild(titleInput);
  inputGroup.appendChild(refreshBtn);
  overlay.appendChild(inputGroup);

  const lnRating = item?.ratings?.learnnatively;
  const jpdbRating = item?.ratings?.jpdb;
  const titleForLookup = detectedTitle || titleInput.value;

  if (item) {
    // === Found: show ratings ===
    const foundEl = document.createElement("div");
    foundEl.className = "jp-difficulty-found-label";
    foundEl.textContent = `Detected: ${item.canonicalTitle || titleForLookup}`;
    overlay.appendChild(foundEl);

    // LearnNatively rating
    if (lnRating && lnRating.level != null) {
      const row = document.createElement("div");
      row.className = "jp-difficulty-rating";
      row.innerHTML = `<span class="jp-difficulty-rating-label">LearnNatively:</span> <span class="jp-difficulty-rating-value">L${lnRating.level}</span>`;
      overlay.appendChild(row);
    } else {
      const row = document.createElement("div");
      row.className = "jp-difficulty-rating missing";
      row.innerHTML = `<span class="jp-difficulty-rating-label">LearnNatively:</span> <span class="jp-difficulty-rating-missing">not found</span>`;
      overlay.appendChild(row);
    }

    // jpdb rating
    if (jpdbRating && jpdbRating.difficulty != null) {
      const row = document.createElement("div");
      row.className = "jp-difficulty-rating";
      row.innerHTML = `<span class="jp-difficulty-rating-label">jpdb:</span> <span class="jp-difficulty-rating-value">${jpdbRating.difficulty} / 100</span>`;
      overlay.appendChild(row);
    } else {
      const row = document.createElement("div");
      row.className = "jp-difficulty-rating missing";
      row.innerHTML = `<span class="jp-difficulty-rating-label">jpdb:</span> <span class="jp-difficulty-rating-missing">not found</span>`;
      overlay.appendChild(row);
    }
  } else {
    // === Not found: show guidance ===
    const notFoundEl = document.createElement("div");
    notFoundEl.className = "jp-difficulty-not-found";
    notFoundEl.textContent = "No rating found in local lists.";
    overlay.appendChild(notFoundEl);
  }

  // === Action buttons row ===
  const actionsDiv = document.createElement("div");
  actionsDiv.className = "jp-difficulty-actions";

  const titleQ = detectedTitle || titleInput.value;

  // LearnNatively Button (Source or Search)
  if (lnRating?.url) {
    actionsDiv.appendChild(makeLink("LearnNatively", "jp-difficulty-action-btn source", lnRating.url));
  } else {
    const lnSearchUrl = buildFallbackUrl('search-learnnatively', encodeURIComponent(titleQ));
    actionsDiv.appendChild(makeLink("🔍 Search LN", "jp-difficulty-action-btn search", lnSearchUrl));
  }

  // jpdb Button(s) (Source or Search)
  if (jpdbRating?.url) {
    actionsDiv.appendChild(makeLink("jpdb", "jp-difficulty-action-btn source", jpdbRating.url));
  } else {
    const jpdbSearchUrl = buildFallbackUrl('search-jpdb', encodeURIComponent(titleQ));
    const jpdbListUrl = buildFallbackUrl('jpdb-anime-list', encodeURIComponent(titleQ));
    actionsDiv.appendChild(makeLink("🔍 Search jpdb", "jp-difficulty-action-btn search", jpdbSearchUrl));
    actionsDiv.appendChild(makeLink("📊 Anime List", "jp-difficulty-action-btn search", jpdbListUrl));
  }

  // Copy title button
  const copyBtn = makeButton("📋 Copy", "jp-difficulty-action-btn copy", () => {
    navigator.clipboard.writeText(titleQ).catch(() => {});
    copyBtn.textContent = "✓ Copied!";
    setTimeout(() => { copyBtn.textContent = "📋 Copy"; }, 2000);
  });
  actionsDiv.appendChild(copyBtn);

  overlay.appendChild(actionsDiv);
  container.appendChild(overlay);
  return container;
}

// ============================================================================
// Update Overlay
// ============================================================================

function updateOverlay() {
  const detectedTitle = detectCurrentTitle();

  // Only update if title changed
  if (detectedTitle === lastDetectedTitle) {
    return;
  }

  lastDetectedTitle = detectedTitle;

  // Remove old overlay
  if (currentOverlayElement) {
    currentOverlayElement.remove();
    currentOverlayElement = null;
  }

  // Don't show overlay if no title detected
  if (!detectedTitle) {
    return;
  }

  // Find matching item
  const item = findMediaItem(detectedTitle);

  // Create and inject overlay
  currentOverlayElement = createHybridOverlay(detectedTitle, item);

  document.body.appendChild(currentOverlayElement);
}

// ============================================================================
// Update Overlay With Custom Title (from editable input)
// ============================================================================

function updateOverlayWithTitle(title) {
  // Remove old overlay
  if (currentOverlayElement) {
    currentOverlayElement.remove();
    currentOverlayElement = null;
  }

  // Find matching item
  const item = findMediaItem(title);

  // Create and inject overlay
  currentOverlayElement = createHybridOverlay(title, item);

  document.body.appendChild(currentOverlayElement);
}

// ============================================================================
// Debounced Update
// ============================================================================

function scheduleUpdate() {
  if (updateTimer) {
    clearTimeout(updateTimer);
  }

  updateTimer = setTimeout(() => {
    updateOverlay();
    updateTimer = null;
  }, 500);
}

// ============================================================================
// URL Change Detection
// ============================================================================

function detectUrlChange() {
  const currentUrl = location.href;

  if (currentUrl !== lastUrl) {
    lastUrl = currentUrl;
    lastDetectedTitle = null;
    scheduleUpdate();
  }
}

// ============================================================================
// DOM Mutation Observer
// ============================================================================

function setupMutationObserver() {
  const observer = new MutationObserver(() => {
    scheduleUpdate();
  });

  const config = {
    childList: true,
    subtree: true,
    characterData: false,
    attributes: false,
  };

  observer.observe(document.documentElement, config);
}

// ============================================================================
// Initialization
// ============================================================================

async function initialize() {
  try {
    // Build search index
    await buildSearchIndex();

    // Initial overlay
    updateOverlay();

    // Setup observers
    setupMutationObserver();

    // Detect URL changes
    setInterval(detectUrlChange, 1000);

    console.log("[JP Difficulty Overlay] Initialized successfully");
  } catch (error) {
    console.error("[JP Difficulty Overlay] Initialization error:", error);
  }
}

// Start when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initialize);
} else {
  initialize();
}