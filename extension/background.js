/**
 * Hermes Career Autofill Extension - Background Service Worker
 * Handles API proxying to Flask 1.0 (localhost:5000), CDP Debugger attachment for file upload.
 */

const FLASK_BASE_URL = "http://127.0.0.1:5000";

// Listen to messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (!request || !request.action) return false;

  const tabId = sender.tab ? sender.tab.id : null;

  switch (request.action) {
    case "FETCH_AUTOFILL_PAYLOAD":
      handleFetchPayload(request.applicationId, request.track)
        .then(data => sendResponse({ success: true, data }))
        .catch(err => sendResponse({ success: false, error: err.message }));
      return true; // Keep message channel open for async response

    case "MATCH_BY_URL":
      handleMatchByUrl(request.url)
        .then(data => sendResponse({ success: true, data }))
        .catch(err => sendResponse({ success: false, error: err.message }));
      return true;

    case "SYNC_SUBMITTED":
      handleSyncSubmitted(request.applicationId, request.payload)
        .then(data => sendResponse({ success: true, data }))
        .catch(err => sendResponse({ success: false, error: err.message }));
      return true;

    case "ATTACH_RESUME_CDP":
      if (!tabId) {
        sendResponse({ success: false, error: "No active tab ID available for CDP debugger." });
        return false;
      }
      handleAttachResumeCDP(tabId, request.filePath, request.selector)
        .then(() => sendResponse({ success: true }))
        .catch(err => sendResponse({ success: false, error: err.message }));
      return true;

    default:
      sendResponse({ success: false, error: `Unknown action: ${request.action}` });
      return false;
  }
});

/**
 * Fetch Autofill Payload from local Flask backend
 */
async function handleFetchPayload(applicationId, track = null) {
  let url = `${FLASK_BASE_URL}/api/agent/applications/${applicationId}/autofill-payload`;
  if (track) {
    url += `?track=${encodeURIComponent(track)}`;
  }
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch payload (HTTP ${res.status}): ${await res.text()}`);
  }
  return await res.json();
}

/**
 * Match Application record by Portal/Source URL
 */
async function handleMatchByUrl(currentUrl) {
  const res = await fetch(`${FLASK_BASE_URL}/api/agent/applications/match-by-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: currentUrl })
  });
  if (!res.ok) {
    throw new Error(`Match by URL failed (HTTP ${res.status})`);
  }
  return await res.json();
}

/**
 * Sync submitted application state back to tracker.db
 */
async function handleSyncSubmitted(applicationId, payload) {
  const res = await fetch(`${FLASK_BASE_URL}/api/agent/applications/${applicationId}/sync-submitted`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });
  if (!res.ok) {
    throw new Error(`Sync submitted failed (HTTP ${res.status})`);
  }
  return await res.json();
}

/**
 * Native Resume Attachment via Chrome Debugger Protocol (CDP)
 * Bypasses browser file sandbox restrictions with OS absolute path
 */
async function handleAttachResumeCDP(tabId, filePath, selector = "input[type=file]") {
  const target = { tabId };

  try {
    // 1. Attach debugger to target tab
    await chrome.debugger.attach(target, "1.3");

    // 2. Enable DOM agent
    await chrome.debugger.sendCommand(target, "DOM.enable");

    // 3. Get Document root node
    const doc = await chrome.debugger.sendCommand(target, "DOM.getDocument", { depth: -1 });
    if (!doc || !doc.root) {
      throw new Error("Unable to retrieve Document root from CDP.");
    }

    // 4. Query target file input node ID
    const queryRes = await chrome.debugger.sendCommand(target, "DOM.querySelector", {
      nodeId: doc.root.nodeId,
      selector: selector
    });

    if (!queryRes || !queryRes.nodeId) {
      throw new Error(`Target file input selector not found: ${selector}`);
    }

    // 5. Send native file input payload
    await chrome.debugger.sendCommand(target, "DOM.setFileInputFiles", {
      nodeId: queryRes.nodeId,
      files: [filePath]
    });

    console.log(`[Hermes CDP] Successfully attached file "${filePath}" to node ${queryRes.nodeId}`);
  } finally {
    // 6. Always detach debugger to remove the warning bar
    try {
      await chrome.debugger.detach(target);
    } catch (e) {
      // Ignore detach errors if already detached
    }
  }
}
