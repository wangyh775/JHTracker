## 1. Backend API Extensions (Flask 1.0)

- [x] 1.1 Implement `GET /api/agent/applications/<id>/autofill-payload` in `routes/agent_api.py` extracting profile basics, 4-track resume paths, and generated open questions
- [x] 1.2 Implement `POST /api/agent/applications/match-by-url` in `routes/agent_api.py` for matching current tab URL with active application records
- [x] 1.3 Implement `POST /api/agent/applications/<id>/sync-submitted` in `routes/agent_api.py` updating application status to '已投递' and logging submission feedback
- [x] 1.4 Add direct apply button with ticket hash link in `templates/to_apply.html`, `templates/dashboard.html`, and `templates/_decision_inbox.html`
- [x] 1.5 Write unit tests for the new autofill API endpoints in `tests/test_agent_api_autofill.py`

## 2. Browser Extension Foundation & Manifest

- [x] 2.1 Scaffold `extension/` directory with `manifest.json` (Manifest V3, permissions: `activeTab`, `storage`, `debugger`, `scripting`, host permissions: `http://127.0.0.1:5000/*`, `<all_urls>`)
- [x] 2.2 Implement background service worker `extension/background.js` managing tab messaging, API proxying to Flask, and CDP debugger attachment
- [x] 2.3 Implement CDP resume file attachment handler in `extension/background.js` using `chrome.debugger.sendCommand("DOM.setFileInputFiles", ...)`

## 3. Content Script & Shadow DOM UI

- [x] 3.1 Implement Content Script entry point in `extension/content.js` and URL hash ticket extractor
- [x] 3.2 Create `<career-tracker-widget>` Web Component with closed Shadow DOM and isolated styling in `extension/widget.js`
- [x] 3.3 Implement draggable floating orb with boundary detection, edge snapping, and `localStorage` position persistence
- [x] 3.4 Implement expandable floating review modal with candidate info preview, track switcher dropdown, field checklist, and action buttons

## 4. Multi-Step Form Perception & Synthetic Typing Engine

- [x] 4.1 Implement form element discovery and classification heuristics in `extension/form-detector.js` (text, select, radio, checkbox, textarea, file)
- [x] 4.2 Implement `MutationObserver` wizard step change detection in `extension/wizard-observer.js` for automatic progressive prefilling
- [x] 4.3 Implement anti-bot synthetic typing simulator in `extension/typing-engine.js` with Gaussian keypress jitter (35-60 chars/sec), punctuation pauses, and reactive prototype setter dispatch
- [x] 4.4 Implement 4-track switching handler dynamically reloading track-specific resumes and open-question answers
- [x] 4.5 Implement manual override detection to immediately pause auto-typing upon user focus/click

## 5. End-to-End Integration & Verification

- [x] 5.1 Verify Flask backend endpoints with automated test suite (`pytest tests/test_agent_api_autofill.py`)
- [x] 5.2 Test extension loading and Shadow DOM rendering on test HTML form pages and real recruitment ATS portals
- [x] 5.3 Test end-to-end flow: Dashboard [一键直达] -> Floating Orb mounted -> Step 1 auto-fill -> Next Step perception -> 4-Track switch -> CDP Resume attach -> Final manual submit & status sync
