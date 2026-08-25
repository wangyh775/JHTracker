## Context

Career-Tracker 1.0 runs on Flask (`app.py`, `routes/`, SQLite `data/tracker.db`). Candidate details reside in `data/profile.md`, resume records in table `resumes`, and custom preferences in `memories`.
Enterprise recruitment websites (Beisen, Moka, ZhiLian, corporate ATS) render complex DOM structures using React, Vue, or Angular, with multi-step wizard navigation and reactive state bindings.

See `proposal.md` for motivation and background.

## Goals / Non-Goals

**Goals:**
- Provide a lightweight, privacy-preserving Chrome extension (Manifest V3) communicating with the local 1.0 Flask server via REST (`http://127.0.0.1:5000`).
- Render an isolated, draggable floating orb and modal widget via Web Components (closed Shadow DOM).
- Detect and progressively handle multi-step form transitions (Basic Info -> Education -> Work/Projects -> Open Questions -> Attachments).
- Deliver anti-bot synthetic typing with Gaussian jitter (35-60 chars/sec) and punctuation pauses to properly trigger framework reactive state setters.
- Support runtime switching between 4 engineering tracks to dynamically refresh bound resumes and tailored answers.
- Implement explicit on-demand resume PDF attachment using Chrome Debugger protocol (`DOM.setFileInputFiles`).

**Non-Goals:**
- Cloud-hosted sync or external SaaS auth (all data strictly remains on localhost).
- Autonomous headless auto-submission without human oversight (strictly enforces Zero-Submit human validation).
- Full OCR or automated CAPTCHA solving (remains human-in-the-loop).

## Decisions

### Decision 1: Manifest V3 Extension Architecture with Closed Shadow DOM
- **Choice**: Structure the extension as Manifest V3 with a Background Service Worker, Content Scripts, and an injected Custom Element `<career-tracker-widget>` using `#shadow-root (closed)`.
- **Rationale**: Host recruitment portals apply diverse CSS resets, utility frameworks, and component styling (Bootstrap, Ant Design, Element UI, Tailwind). Closed Shadow DOM prevents host CSS pollution and guarantees consistent UI rendering.
- **Alternatives Considered**:
  - *Iframe injection*: Heavier resource footprint, clunkier drag-and-drop mechanics, and cross-origin messaging friction.
  - *SidePanel API*: Shrinks the host webpage layout, causing responsive distortion on complex multi-column ATS forms.

### Decision 2: REST-based Handshake with Hash Anchor Handoff
- **Choice**: 1.0 Flask web UI (`/to-apply` & Dashboard) launches recruitment URLs with a hash token (e.g. `https://careers.corp.com/apply#hermes_app_id=42`). The extension content script extracts the hash parameter, requests `GET /api/agent/applications/<id>/autofill-payload`, and quietly strips the hash from the address bar. A fallback URL matcher `POST /api/agent/applications/match-by-url` is available if opened without a hash.
- **Rationale**: 100% deterministic binding between the local application record and the browser tab without complex background tab tracking heuristics.
- **Alternatives Considered**:
  - *Native Messaging*: Requires local registry/manifest installation, increasing deployment complexity.
  - *Continuous WebSocket stream*: Unnecessary connection overhead for sporadic page navigation and form-filling sessions.

### Decision 3: Progressive Perception Engine via MutationObserver
- **Choice**: Use a debounce-wrapped `MutationObserver` on the form container and window URL/hash changes to detect step transitions. Identify fields using progressive heuristics: `name`/`id`/`placeholder`/`aria-label` regex matching, parent label DOM traversal, and data attribute flagging (`data-hermes-filled`).
- **Rationale**: Modern ATS wizards dynamically mount and unmount step DOM nodes without full page reloads.

### Decision 4: Synthetic Keystroke Dispatcher with Prototype Setter Bypassing
- **Choice**: Dispatch full event sequences (`keydown` -> `beforeinput` -> Native Property Setter `HTMLInputElement.prototype.value` -> `input` -> `keyup`) with randomized time delays.
- **Rationale**: Direct `element.value = "..."` fails to notify React 16+ or Vue 3 internal synthetic event listeners. Calling the underlying native descriptor setter and firing bubbling `input` events ensures complete framework synchronization.

### Decision 5: Explicit CDP File Upload via `chrome.debugger`
- **Choice**: When the user clicks "一键挂载简历 (Attach Resume)", the background worker temporarily attaches `chrome.debugger` to the active tab, executes `DOM.setFileInputFiles` with the verified local file path, and detaches immediately.
- **Rationale**: Web sandbox constraints block arbitrary local filesystem paths via `HTMLInputElement.files`. Using the debugger API provides 100% native file attachment without requiring an external Playwright driver.

## Risks / Trade-offs

- **[Risk] Chrome Debugger Banner Display**: Attaching `chrome.debugger` shows a standard browser infobar ("Career-Tracker is debugging this tab").
  - *Mitigation*: Attach the debugger transiently only during the exact file injection call, then immediately detach so the infobar dismisses.
- **[Risk] Custom Component Cascader / DatePicker Variations**: Non-standard select/date dropdowns in certain niche ATS might not accept text values directly.
  - *Mitigation*: The widget provides clear visual color coding (Green=Filled, Yellow=AI Draft, Red=Requires Manual Input) with one-click "Scroll to Field" focus buttons.
- **[Risk] Flask CORS on Localhost**: Chrome extension background scripts can fetch localhost, but content scripts may face CORS when fetching `http://127.0.0.1:5000`.
  - *Mitigation*: Ensure Flask `agent_api` routes declare appropriate CORS headers (`Access-Control-Allow-Origin: *` or extension origin) or proxy requests through the extension background service worker.
