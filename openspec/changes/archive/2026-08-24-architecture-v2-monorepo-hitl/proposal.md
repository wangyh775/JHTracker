# Proposal: Architecture v2.0 Monorepo & HITL Framework

## Why

The current Career Tracker application is structured as a monolithic Flask server using server-side Jinja2 templates, coupled with synchronous sub-process scripts and scattered tooling. This architecture creates significant friction during online campus recruitment (网申):
1. **Interactive Experience Bottleneck**: Server-rendered HTML is poorly suited for multi-tasking (e.g., side-by-side browser filling, instant floating clipboards, live CDP progress indicators).
2. **Async Automation Incompatibilities**: Browser automation (CDP/Playwright) and real-time streaming (SSE) face event loop conflicts with synchronous Flask WSGI servers.
3. **Lack of a Unified Monorepo & Daemon Management**: Managing Python virtualenvs and background daemons manually on Windows requires repetitive terminal maintenance rather than a clean, single-command development experience (`npm run dev`/`npm run daemon`).

Migrating to a modern Monorepo (Vue 3 + Vite SPA Frontend + FastAPI Async Backend) with a strict Human-In-The-Loop (HITL) safety framework ensures lightning-fast autofill, seamless agent orchestration via FastMCP, zero-risk submission isolation, and single-command local deployment.

## What Changes

- **Monorepo Unification**: Establish a clean Monorepo layout with root `package.json` and `uv` orchestration for unified zero-config setup, concurrent development (`npm run dev`), static frontend asset bundling, and background daemon execution (`npm run daemon`).
- **Async Backend Re-architecture (FastAPI)**: Replace synchronous Flask routing with an asynchronous FastAPI application utilizing SQLAlchemy 2.0 (Async) + `aiosqlite`, providing native async Playwright CDP connection pools, SSE progress streaming, and strict Pydantic v2 contract schemas.
- **Modern SPA Frontend (Vue 3 + Vite + Tailwind)**: Build a high-performance recruitment workbench featuring a Kanban pipeline, a floating quick-copy drawer (for manual multi-step form entry), one-click CDP autofill trigger buttons, and 3-track resume/script switchers.
- **Autofill Adapter Framework (`services/autofill/`)**: Abstract web recruitment system integrations (Beisen/北森, Moka, and Generic DOM) behind a unified asynchronous adapter contract.
- **Strict HITL & Zero-Submit Safety Guard**: Hard-code isolation barriers in the autofill engine prohibiting automatic clicks on final submission buttons; enforce write-protection on post-apply application states.
- **MCP SSE & REST Coexistence**: Expose dual-channel interfaces (REST for instant UI actions, FastMCP over SSE for Hermes Agent autonomous background operations).

## Capabilities

### New Capabilities
- `autofill-adapter-engine`: Unified asynchronous browser automation adapter framework interfacing with Beisen, Moka, and generic campus recruitment portals via Chrome CDP, enforcing strict Zero-Submit safety boundaries.
- `recruitment-workbench-spa`: Modern Vue 3 SPA web interface offering interactive Kanban state transitions, side-by-side floating recruitment clipboard, and real-time SSE progress streaming.
- `monorepo-toolchain-daemon`: Root-level multi-runtime orchestration (`package.json` + `uv`) providing single-command setup, concurrent development hot-reload, and background Windows service daemonization.
- `hitl-governance-guard`: Multi-tier Human-In-The-Loop policy engine enforcing proposal approval gates, Zero-Submit execution barriers, and immutable post-application state protection.

### Modified Capabilities
<!-- No requirement changes to existing capability specs; existing data stores and scoring models are preserved -->

## Impact

- **Backend**: `app.py` and Flask blueprint routes migrated to `backend/app/` (FastAPI). Existing SQLite database (`tracker.db`) schema and WAL settings preserved with backward compatibility.
- **Frontend**: Deprecate Jinja2 templates (`templates/`) in favor of standalone `frontend/` (Vue 3 + TypeScript + Vite + Tailwind CSS).
- **Tooling & Agents**: Existing 37 FastMCP tools adapted to async FastMCP server endpoints without breaking Hermes Agent's existing skill integration.
- **Dependencies**: Introduces Node.js (Vite/Vue3/pnpm/npm) alongside Python `uv` virtual environment management.
