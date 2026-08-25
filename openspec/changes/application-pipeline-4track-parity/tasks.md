## 1. Documentation-First & Architecture Specifications

- [x] 1.1 Create/update `docs/architecture_v2.md` detailing the 4-track routing model, active/archived state machine, and Zero-Submit audit lifecycle.
- [x] 1.2 Document REST API endpoint contracts and data dictionary in `docs/api_specification.md`.
- [x] 1.3 Update system data flow diagrams and Mermaid state machines in `README.md` and `docs/`.

## 2. Backend Schema & 4-Track Router Parity

- [x] 2.1 Update SQLAlchemy entity definitions in `backend/app/models/entities.py` (add `is_archived`, `archived_at`, `form_type`, `source_platform`, `source_url`, `resume_id`, `ApplicationSubmission`, `InterviewFeedback`, `DecisionFeedback`, `Memory`, `Resume`, `Note`, `Timeline`).
- [x] 2.2 Align Pydantic validation schemas in `backend/app/models/schemas.py` to support all extended entity fields and query filters.
- [x] 2.3 Implement the 4-track classifier and dynamic copy synthesizer in `backend/app/services/router.py` (Control, Embedded/Auto, Mechatronics, Mechanical/CFD).
- [x] 2.4 Expand FastAPI endpoints in `backend/app/api/routes.py` (`/applications`, `/to-apply`, `/submissions`, `/submissions/{id}`, `/feedbacks`, `/settings`).
- [x] 2.5 Re-align FastAPI backend port to `5000` in `package.json`, `main.py`, and test configurations.

## 3. Frontend Vue 3 SPA Routing & Component Reconstruction

- [x] 3.1 Install and configure `vue-router` in `frontend/src/router/index.ts` with routes for `/applications`, `/to-apply`, `/submissions`, `/submissions/:id`, `/companies`, `/compare`, `/answer-bank`, `/traces`.
- [x] 3.2 Implement `frontend/src/views/ApplicationsView.vue` featuring structured Table View, active/archived dual tabs, auto-archival settings panel, and Kanban mode toggle.
- [x] 3.3 Implement `frontend/src/views/ToApplyView.vue` with AI score callouts, 4-track badges, JD link shortcuts, and one-click prefill triggers.
- [x] 3.4 Implement `frontend/src/views/SubmissionsView.vue` and `frontend/src/views/SubmissionDetailView.vue` for field-by-field Zero-Submit auditing.
- [x] 3.5 Build global Feedback Drawer and dynamic Profile clipboard sidebar in `frontend/src/App.vue`.

## 4. Verification & Testing

- [x] 4.1 Execute pytest test suite verifying database entities, 4-track routing accuracy, and API endpoints.
- [x] 4.2 Verify frontend build via `pnpm run build` and test view navigation.
