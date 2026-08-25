# Proposal: Application Pipeline & 4-Track Resume Parity

## Why

Following the v2.0 Monorepo migration, the current user interface suffered substantial feature regression and functional omission compared to v1.0. Critical recruitment operations—such as multi-dimensional structured application tracking (active vs. archived), customizable auto-archival policies, human-in-the-loop (Zero-Submit) prefill field auditing (`/submissions`), candidate opportunity pools (`/to-apply`), interview feedback reviews, and fine-grained 4-track career profile routing—are missing or broken across both FastAPI backend models and Vue 3 SPA views. Restoring full feature parity with dedicated routing and precise 4-track differentiation is essential to maintain high-efficiency campus recruitment workflows for the 2027 recruitment cycle.

## What Changes

- **Documentation-First & Spec Alignment**: Mandate comprehensive documentation updates in `docs/` before implementing code changes, validating all architectural data flows and API contracts.
- **Backend Entities & Database Parity**:
  - Extend SQLAlchemy entity models (`backend/app/models/entities.py`) with all missing v1.0 properties (`is_archived`, `archived_at`, `form_type`, `source_platform`, `source_url`, `resume_id`, `deadline`, `salary_min`, `salary_max`, etc.).
  - Restore supporting models: `ApplicationSubmission`, `InterviewFeedback`, `DecisionFeedback`, `Memory`, `Resume`, `Note`, `Timeline`.
- **4-Track Resume & Script Synthesis Engine (`backend/app/services/router.py`)**:
  - Upgrade the candidate routing engine to distinctly segment 4 core engineering domains:
    1. 🔵 **Control Algorithms (控制算法 - MPC/EKF/State Estimation)**
    2. 🟣 **Automation & Embedded (自动化与嵌入式 - STM32H7/Linux/Klipper/Firmware)**
    3. 🟢 **Mechatronics & Electrical (机电一体化与电气 - EPLAN/ECAD/Cabinet/Anti-interference)**
    4. 🟠 **Mechanical Structure & CFD (机械结构与仿真 - CoreXY/SolidWorks/Fluent/Thermal-Fluid)**
  - Synthesize specialized greetings and automatically bind appropriate resume assets.
- **FastAPI Endpoints Parity**:
  - Full REST API support for `/api/v1/applications` (active/archived tabs, pagination, multi-field filtering, manual/auto archival trigger and settings).
  - Dedicated `/api/v1/to-apply` candidate pool endpoints.
  - Dedicated `/api/v1/submissions` and `/api/v1/submissions/{id}` Zero-Submit review endpoints.
  - Dedicated `/api/v1/feedbacks` and `/api/v1/memories` preference learning endpoints.
  - Re-align default backend API server port to 5000 (with proxy in Vite).
- **Vue 3 Modular SPA Workbench with Router**:
  - Introduce `vue-router` to separate concerns:
    - `/applications`: Structured Table View (with Kanban switch, archive toggle, and settings drawer).
    - `/to-apply`: Candidate opportunity queue with AI score highlights and 4-track quick-copy pitch.
    - `/submissions` & `/submissions/:id`: Zero-Submit verification station with field-by-field auditing.
    - Global Feedback Drawer & Dynamic Profile Clipboard.

## Capabilities

### New Capabilities
- `application-table-workbench`: High-density structured table workbench supporting active vs. archived segregation, batch archival rules, multi-attribute filtering, and seamless Kanban switching.
- `four-track-resume-router`: Automated 4-track job taxonomy classifier (Control, Embedded/Auto, Mechatronics, Mechanical/CFD) with dynamic greeting generation and resume asset binding.
- `zero-submit-audit-station`: Two-stage Zero-Submit verification interface allowing candidates to inspect, edit, and confirm prefilled form fields prior to manual browser submission.

### Modified Capabilities
<!-- No modified capabilities; existing base capabilities are extended without breaking prior schema contracts -->

## Impact

- **Backend**: `backend/app/models/entities.py`, `backend/app/models/schemas.py`, `backend/app/api/routes.py`, `backend/app/services/router.py`.
- **Frontend**: `frontend/src/router/index.ts`, `frontend/src/views/ApplicationsView.vue`, `frontend/src/views/ToApplyView.vue`, `frontend/src/views/SubmissionsView.vue`, `frontend/src/views/SubmissionDetailView.vue`, `frontend/src/App.vue`.
- **Docs**: Comprehensive update in `docs/` covering data dictionary, workflow diagrams, and API specifications.
- **Port**: Set FastAPI backend default port to 5000 for seamless developer experience.
