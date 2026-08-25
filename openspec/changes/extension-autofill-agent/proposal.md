## Why

In Career-Tracker 1.0 (Flask + SQLite `tracker.db` + Jinja2), job discovery and evaluation are automated, but the actual submission step on external enterprise recruitment portals (e.g. Beisen, Moka, ZhiLian, corporate ATS) remains manual, repetitive, and time-consuming. 

Standalone browser automation (such as Playwright/CDP scripts) suffers from frequent session expiration (SMS/WeChat login), bot detection, and brittle multi-step wizard navigation. Conversely, commercial autofill extensions lack privacy guarantees and cannot interface with a user's private local AI agent, 4-track resume assets, profile markdown, and dynamic AnswerBank memories.

Building a dedicated browser extension backed by the local Career-Tracker 1.0 Flask backend delivers a privacy-first, human-in-the-loop (Zero-Submit) companion. It provides a draggable floating orb, anti-cheat human-like typing simulation, multi-step wizard perception, 4-track dynamic switching, and explicit CDP-based resume file attachment directly inside real enterprise job portals.

## What Changes

- **Local Extension API Endpoints in Flask 1.0**: Add backend routes in `routes/agent_api.py` to serve application autofill payloads (`GET /api/agent/applications/<id>/autofill-payload`), match applications by URL (`POST /api/agent/applications/match-by-url`), and synchronize final submission status (`POST /api/agent/applications/<id>/sync-submitted`).
- **Browser Extension (Manifest V3)**:
  - **Shadow DOM Floating Orb & Modal**: Draggable, edge-snapping floating orb with closed Shadow DOM styling that opens a review card without style conflicts on host ATS pages.
  - **Multi-Step Wizard Perception**: `MutationObserver` and step change detection engine to automatically identify and prefill consecutive form wizard steps (Basic Info, Education, Experience, Open Questions, Attachments).
  - **Anti-Cheat Human-like Typing Simulator**: Synthetic DOM event dispatcher injecting text with Gaussian jitter (35-60 chars/sec) and punctuation pauses to bypass anti-bot detection and preserve responsive framework state (React/Vue/Angular).
  - **4-Track Dynamic Re-targeting**: In-widget dropdown allowing instant switching between the 4 engineering tracks (Control Algorithms, Automation & Embedded, Mechatronics & Electrical, Mechanical & Simulation) to dynamically re-synthesize open answers and switch bound resume PDFs.
  - **Explicit CDP Resume Attachment**: On-demand file injection leveraging Chrome Debugger protocol (`DOM.setFileInputFiles`) to directly attach local resume files without manual file dialog hunting.
- **1.0 UI Direct Link Integration**: Add an "一键直达网申 (Direct Apply)" launcher button in 1.0 `/to-apply` and Dashboard decision cards embedding temporary ticket hashes to instantly hand off jobs to the extension.

## Capabilities

### New Capabilities
- `extension-autofill`: Browser extension companion engine providing draggable floating orb UI, multi-step wizard auto-perception, human-like typing simulation, 4-track switching, explicit CDP resume attachment, and bidirectional synchronization with Career-Tracker 1.0 Flask backend.

### Modified Capabilities
- `agent-api`: Extend agent API endpoints to provide autofill payload retrieval, URL-based application matching, and post-submission lifecycle status synchronization.

## Impact

- **Backend**: New API endpoints in `routes/agent_api.py` reading `data/profile.md`, `resumes`, `memories`, `applications`, and `companies`.
- **Frontend (1.0 Templates)**: Added direct navigation links with hash anchors in `templates/to_apply.html`, `templates/dashboard.html`, and `templates/_decision_inbox.html`.
- **New Subsystem**: Standalone Chrome extension codebase residing under `extension/` (Manifest V3, Service Worker, Content Scripts, Shadow DOM UI).
- **Dependencies**: No external cloud services required; operates strictly over local HTTP (`http://127.0.0.1:5000`).
