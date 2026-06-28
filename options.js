// JP Difficulty Overlay - Options Page Script

// ============================================================================
// Storage Helpers
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

function setUserMappings(mappings) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ userMappings: mappings }, () => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
        return;
      }

      resolve();
    });
  });
}

// ============================================================================
// Utility Functions
// ============================================================================

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

function getQueryParam(param) {
  const params = new URLSearchParams(window.location.search);
  return params.get(param);
}

// ============================================================================
// Form Handling
// ============================================================================

async function saveMapping(event) {
  event.preventDefault();

  const detectedTitle = document.getElementById("detected-title").value.trim();
  const canonicalId = document.getElementById("canonical-id").value.trim();
  const titleEn = document.getElementById("title-en").value.trim();
  const titleJa = document.getElementById("title-ja").value.trim();
  const titleRomaji = document.getElementById("title-romaji").value.trim();
  const aliasesStr = document.getElementById("aliases").value.trim();
  const learnnativelyLevel = document.getElementById("learnnatively-level").value;
  const learnnativelyJlpt = document.getElementById("learnnatively-jlpt").value;
  const learnnativelyUrl = document.getElementById("learnnatively-url").value.trim();
  const jpdbDifficulty = document.getElementById("jpdb-difficulty").value;
  const jpdbUrl = document.getElementById("jpdb-url").value.trim();

  // Validation
  if (!canonicalId || !titleEn) {
    alert("Please fill in Canonical ID and English Title.");
    return;
  }

  // Parse aliases
  const aliases = aliasesStr
    .split(",")
    .map((a) => a.trim())
    .filter((a) => a.length > 0);

  // Create mapping object
  const mapping = {
    id: canonicalId,
    workType: "user-added",
    canonicalTitle: titleEn,
    titles: {
      en: titleEn,
      ja: titleJa || null,
      romaji: titleRomaji || null,
    },
    aliases: aliases,
    platformAliases: {
      netflix: detectedTitle ? [detectedTitle] : [],
      crunchyroll: detectedTitle ? [detectedTitle] : [],
    },
    ratings: {
      learnnatively: {
        level: learnnativelyLevel ? parseInt(learnnativelyLevel, 10) : null,
        jlptApprox: learnnativelyJlpt || "",
        url: learnnativelyUrl || "",
      },
      jpdb: {
        difficulty: jpdbDifficulty ? parseInt(jpdbDifficulty, 10) : null,
        url: jpdbUrl || "",
      },
    },
    metadata: {
      status: "user-added",
      lastVerified: new Date().toISOString().split("T")[0],
      notes: "Added by user through options page.",
    },
  };

  // Get existing mappings
  let mappings = await getUserMappings();

  // Check if already exists
  const existingIndex = mappings.findIndex((m) => m.id === canonicalId);

  if (existingIndex >= 0) {
    // Update existing
    mappings[existingIndex] = mapping;
  } else {
    // Add new
    mappings.push(mapping);
  }

  // Save
  await setUserMappings(mappings);
  await renderMappings();

  // Clear form
  document.getElementById("mapping-form").reset();

  alert("Local mapping saved!");
}

async function exportMappings() {
  const mappings = await getUserMappings();
  const blob = new Blob([JSON.stringify(mappings, null, 2)], {
    type: "application/json",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `jp-difficulty-local-mappings-${new Date().toISOString().split("T")[0]}.json`;
  link.click();

  URL.revokeObjectURL(url);
}

async function clearMappings() {
  const confirmed = confirm(
    "Are you sure you want to clear all local mappings? This cannot be undone."
  );

  if (!confirmed) {
    return;
  }

  await setUserMappings([]);
  await renderMappings();

  alert("All local mappings cleared.");
}

async function importMappings() {
  const jsonText = document.getElementById("import-json").value.trim();

  if (!jsonText) {
    alert("Please paste JSON to import.");
    return;
  }

  try {
    const importedMappings = JSON.parse(jsonText);

    if (!Array.isArray(importedMappings)) {
      alert("JSON must be an array of mappings.");
      return;
    }

    let existing = await getUserMappings();

    // Merge: keep existing, add imported
    for (const imported of importedMappings) {
      const existingIndex = existing.findIndex((m) => m.id === imported.id);

      if (existingIndex >= 0) {
        const overwrite = confirm(
          `Mapping "${imported.id}" already exists. Overwrite?`
        );

        if (overwrite) {
          existing[existingIndex] = imported;
        }
      } else {
        existing.push(imported);
      }
    }

    await setUserMappings(existing);
    await renderMappings();

    document.getElementById("import-json").value = "";

    alert(
      `Imported ${importedMappings.length} mapping(s). Total: ${existing.length}`
    );
  } catch (error) {
    alert(`Import error: ${error.message}`);
  }
}

// ============================================================================
// Rendering
// ============================================================================

async function renderMappings() {
  const mappings = await getUserMappings();
  const container = document.getElementById("mappings-container");

  if (mappings.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No local mappings yet.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = mappings
    .map((mapping) => {
      const levelText = mapping.ratings?.learnnatively?.level
        ? `LearnNatively: ${mapping.ratings.learnnatively.level}`
        : "";
      const jlptText = mapping.ratings?.learnnatively?.jlptApprox
        ? `(${mapping.ratings.learnnatively.jlptApprox})`
        : "";
      const jpdbText = mapping.ratings?.jpdb?.difficulty
        ? `jpdb: ${mapping.ratings.jpdb.difficulty}`
        : "";

      const ratings = [levelText, jlptText, jpdbText].filter((x) => x);
      const ratingStr = ratings.join(" ");

      return `
        <div class="mapping-item">
          <div>
            <div class="mapping-title">${mapping.canonicalTitle}</div>
            <div class="mapping-subtitle">${mapping.id}</div>
            ${ratingStr ? `<div class="mapping-subtitle">${ratingStr}</div>` : ""}
          </div>
          <div class="mapping-actions">
            <button class="btn-secondary btn-small" onclick="editMapping('${mapping.id}')">Edit</button>
            <button class="btn-danger btn-small" onclick="deleteMapping('${mapping.id}')">Delete</button>
          </div>
        </div>
      `;
    })
    .join("");
}

async function editMapping(id) {
  const mappings = await getUserMappings();
  const mapping = mappings.find((m) => m.id === id);

  if (!mapping) {
    alert("Mapping not found.");
    return;
  }

  // Populate form
  document.getElementById("detected-title").value =
    mapping.platformAliases?.netflix?.[0] ||
    mapping.platformAliases?.crunchyroll?.[0] ||
    "";
  document.getElementById("canonical-id").value = mapping.id;
  document.getElementById("title-en").value = mapping.titles?.en || "";
  document.getElementById("title-ja").value = mapping.titles?.ja || "";
  document.getElementById("title-romaji").value = mapping.titles?.romaji || "";
  document.getElementById("aliases").value = (mapping.aliases || []).join(
    ", "
  );
  document.getElementById("learnnatively-level").value =
    mapping.ratings?.learnnatively?.level || "";
  document.getElementById("learnnatively-jlpt").value =
    mapping.ratings?.learnnatively?.jlptApprox || "";
  document.getElementById("learnnatively-url").value =
    mapping.ratings?.learnnatively?.url || "";
  document.getElementById("jpdb-difficulty").value =
    mapping.ratings?.jpdb?.difficulty || "";
  document.getElementById("jpdb-url").value = mapping.ratings?.jpdb?.url || "";

  // Scroll to form
  document.getElementById("mapping-form").scrollIntoView({ behavior: "smooth" });
}

async function deleteMapping(id) {
  const confirmed = confirm(`Delete mapping "${id}"?`);

  if (!confirmed) {
    return;
  }

  let mappings = await getUserMappings();
  mappings = mappings.filter((m) => m.id !== id);

  await setUserMappings(mappings);
  await renderMappings();
}

function prefillFromQuery() {
  // First check URL params (for manual opening)
  const title = getQueryParam("title");

  if (title) {
    document.getElementById("detected-title").value = title;
    document.getElementById("title-en").value = title;
    document.getElementById("canonical-id").value = slugify(title);
    document.getElementById("aliases").value = title.toLowerCase();

    // Scroll to form
    document.getElementById("mapping-form").scrollIntoView({
      behavior: "smooth",
    });
    return;
  }

  // Then check chrome.storage for pending title from content script
  chrome.storage.local.get(["pendingDetectedTitle"], (result) => {
    const pendingTitle = result.pendingDetectedTitle;

    if (pendingTitle) {
      document.getElementById("detected-title").value = pendingTitle;
      document.getElementById("title-en").value = pendingTitle;
      document.getElementById("canonical-id").value = slugify(pendingTitle);
      document.getElementById("aliases").value = pendingTitle.toLowerCase();

      // Clear the pending title from storage
      chrome.storage.local.remove("pendingDetectedTitle");

      // Scroll to form
      document.getElementById("mapping-form").scrollIntoView({
        behavior: "smooth",
      });
    }
  });
}

// ============================================================================
// Event Listeners
// ============================================================================

document
  .getElementById("mapping-form")
  .addEventListener("submit", saveMapping);
document
  .getElementById("export-json")
  .addEventListener("click", exportMappings);
document
  .getElementById("clear-mappings")
  .addEventListener("click", clearMappings);
document
  .getElementById("import-button")
  .addEventListener("click", importMappings);

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener("DOMContentLoaded", async () => {
  prefillFromQuery();
  await renderMappings();
});
