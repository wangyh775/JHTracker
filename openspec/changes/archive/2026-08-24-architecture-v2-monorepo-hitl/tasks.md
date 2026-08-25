## 1. Monorepo Scaffolding & Toolchain Configuration

- [x] 1.1 Create root `package.json` with unified development and build scripts (`setup`, `dev`, `build`, `start`, `daemon`)
- [x] 1.2 Configure backend dependencies in `pyproject.toml` using `uv` (FastAPI, uvicorn, sqlalchemy[asyncio], aiosqlite, pydantic, playwright)
- [x] 1.3 Scaffold `frontend/` directory with Vite, Vue 3, TypeScript, Tailwind CSS, and Lucide icons
- [x] 1.4 Configure static asset build output from `frontend/dist` to `backend/app/static/dist`

## 2. Asynchronous Backend Re-architecture (FastAPI)

- [x] 2.1 Implement async SQLite database session engine with WAL mode and `busy_timeout` in `backend/app/core/database.py`
- [x] 2.2 Port existing SQLAlchemy models to 2.0 Async declarative syntax with Pydantic v2 schemas in `backend/app/models/`
- [x] 2.3 Implement RESTful API endpoints for Companies, Jobs, Applications, and Audit Traces under `backend/app/api/`
- [x] 2.4 Port existing 37 FastMCP tools to bind against the new async service layer in `backend/app/mcp_server.py`
- [x] 2.5 Re-implement automated pytest suite in `backend/tests/` to verify parity with all existing 57 tests

## 3. Unified Autofill Adapter Engine & Zero-Submit Guard

- [x] 3.1 Define `BaseAutofillAdapter` abstract interface in `backend/app/services/autofill/base.py`
- [x] 3.2 Implement `CDPManager` with connection pooling, socket pre-flight probe, and platform heuristic router in `backend/app/services/autofill/manager.py`
- [x] 3.3 Implement `BeisenAutofillAdapter` for Beisen/Zhiye recruitment systems supporting drag-and-drop resume upload and reactive Vue field filling
- [x] 3.4 Implement `GenericFormAdapter` with proximity label matching for custom enterprise recruitment portals
- [x] 3.5 Implement `ZeroSubmitGuard` in `backend/app/services/autofill/guard.py` hard-blocking automated submission button interactions
- [x] 3.6 Implement SSE endpoint `/api/v1/autofill/stream` to broadcast live execution milestones to frontend

## 4. Frontend Recruitment Workbench SPA

- [x] 4.1 Implement Kanban board component (`frontend/src/components/KanbanBoard.vue`) supporting drag-and-drop state transitions and filtering
- [x] 4.2 Implement persistent floating quick-copy drawer (`frontend/src/components/QuickCopyDrawer.vue`) with one-click clipboard copying for profile blocks
- [x] 4.3 Implement live autofill trigger and SSE progress dialog component (`frontend/src/components/AutofillModal.vue`)
- [x] 4.4 Implement 3-track resume version and HR greeting cover letter inspector (`frontend/src/components/ResumeTrackSwitcher.vue`)
- [x] 4.5 Implement job detail view with JD analysis, score breakdown, and interview prediction questions panel

## 5. End-to-End Verification & Documentation Loop

- [x] 5.1 Run full backend test suite (`pytest`) to confirm 100% test pass rate
- [x] 5.2 Verify `npm run build` bundles the SPA and FastAPI serves the client from single port `http://localhost:8000`
- [x] 5.3 Verify `npm run dev` hot-reloading for both Vue 3 frontend and FastAPI backend
- [x] 5.4 Execute live CDP autofill test against mock and real recruitment portals verifying Zero-Submit boundary
- [x] 5.5 Update `README.md` and `AGENTS.md` with the new Monorepo developer guide and architecture documentation
