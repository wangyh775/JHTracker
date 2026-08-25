# Technical Design: Monorepo Architecture, FastAPI Async Backend & Vue 3 SPA

## Context

See `proposal.md` for motivation and background. The existing Career Tracker is built on Flask 3.0, synchronous SQLAlchemy, and Jinja2 templates, sharing data via SQLite (`data/tracker.db`). To enable responsive recruitment assistance (side-by-side filling, floating clipboards, live CDP feedback), the system will transition to an asynchronous Monorepo architecture while preserving SQLite database compatibility and 100% test coverage.

## Goals / Non-Goals

**Goals:**
- **Asynchronous FastAPI Core**: Provide high-performance REST APIs, native Playwright Async CDP execution, and SSE streaming.
- **Modern Vue 3 SPA Frontend**: Deliver a responsive recruitment workbench with Kanban drag-and-drop, side-by-side floating clipboard, and track switchers.
- **Monorepo Developer Experience**: Root `package.json` coordinating Node.js and Python `uv` virtualenv for single-command `npm run setup`, `npm run dev`, and `npm run daemon`.
- **Zero-Submit & HITL Enforcement**: Guarantee candidate sovereignty over applications and ensure autonomous agents cannot perform auto-submissions or modify active pipelines.
- **Data Continuity**: Zero data loss from existing `tracker.db` SQLite database.

**Non-Goals:**
- Porting backend to Node.js/TypeScript (rejected to preserve Python MCP, data science, and test assets).
- Electron/Tauri native binary packaging (standard browser SPA with responsive window docking is sufficient).
- Automated submission bypassing user review (prohibited by Zero-Submit policy).

## Decisions

### 1. Backend Architecture: FastAPI + SQLAlchemy 2.0 Async + aiosqlite
- **Rationale**: FastAPI natively runs on the Python standard `asyncio` event loop, seamlessly integrating with Playwright's `async_playwright` and Server-Sent Events (SSE) for real-time progress streaming without thread contention.
- **Alternatives Considered**:
  - *Keep Flask with Celery/Threading*: Introduces complex worker broker dependencies (Redis/RabbitMQ), overkill for a single-user desktop environment.
  - *Node.js/NestJS*: Requires 100% rewrite of all 37 FastMCP tools, 57 tests, and data science models.

### 2. Frontend Framework: Vue 3 + Vite + Tailwind CSS + Lucide Icons
- **Rationale**: Vue 3 with `<script setup>` and Vite provides sub-second HMR, lightweight reactivity, and seamless integration with single-file component development.
- **Alternatives Considered**:
  - *React + Next.js*: Unnecessary SSR complexity; client-side SPA served statically from FastAPI provides lower memory footprint and zero Node runtime requirement in production.

### 3. Autofill Adapter Abstraction (`backend/app/services/autofill/`)
- **Structure**:
  ```
  backend/app/services/autofill/
  ├── base.py              # BaseAutofillAdapter abstract contract
  ├── manager.py           # CDP connection pool & dynamic platform router
  ├── adapters/
  │   ├── beisen.py        # Beisen (北森/汇川/大疆) Vue/iframe adapter
  │   ├── moka.py          # Moka step-form adapter
  │   └── generic.py       # Heuristic DOM matching adapter
  └── guard.py             # Zero-Submit inspection barrier
  ```
- **Zero-Submit Mechanism**: `guard.py` monitors execution steps and terminates CDP sessions prior to any element matches on `submit`, `button:has-text("确认投递")`, or `button:has-text("提交申请")`.

### 4. Monorepo Toolchain & Daemonization (`package.json` + `uv`)
- **Toolchain Wiring**:
  - `npm run setup`: `pnpm install && uv sync`
  - `npm run dev`: `concurrently "pnpm --prefix frontend dev" "uv run uvicorn backend.app.main:app --reload --port 8000"`
  - `npm run build`: `pnpm --prefix frontend build` (outputs to `backend/app/static/dist`)
  - `npm run daemon`: `pm2 start backend/app/main.py --name career-tracker-api --interpreter python` (or background detached process)

## Risks / Trade-offs

- **[Risk] SQLite Concurrent Access between FastMCP and FastAPI Async**
  → *Mitigation*: Enforce SQLite WAL mode (`PRAGMA journal_mode=WAL`) and `busy_timeout=5000` on every async connection pool checkout.
- **[Risk] Chrome Port 9222 Collision or Inaccessibility**
  → *Mitigation*: `manager.py` implements pre-flight socket health probes, auto-detects running Chrome instances, and gracefully falls back with user guidance if the port is offline.
- **[Risk] Breaking Changes to Existing MCP Tools**
  → *Mitigation*: FastMCP server imports directly from FastAPI service layer models, preserving all 37 tool names and input parameter schemas.

## Migration Plan

1. **Phase 1: Backend Scaffolding & Service Porting**:
   - Establish `backend/` package structure and port SQLAlchemy models to 2.0 Async syntax.
   - Re-implement REST endpoints under `/api/v1/` and verify with async pytest suite.
2. **Phase 2: Frontend SPA Implementation**:
   - Scaffold `frontend/` Vue 3 + Vite project with Tailwind CSS.
   - Implement Kanban board, Floating Clipboard Drawer, and Autofill Trigger components.
3. **Phase 3: Integration & Monorepo Toolchain**:
   - Configure root `package.json` scripts and verify `npm run dev` and `npm run build`.
   - Embed frontend static distribution into FastAPI fallback routes.
4. **Phase 4: Verification & Test Parity**:
   - Run complete test suite and execute end-to-end CDP autofill trial on real portal.
