# Technical Design: Vue 3 Full-Feature SPA Architecture & API Parity

## Context

See `proposal.md` for motivation. The frontend is migrating from 22 legacy Jinja2 server-rendered templates to a unified Vue 3 + TypeScript Single Page Application (SPA). To maintain complete parity, all legacy data models and views (Dashboard, Companies, Offer Compare, Decision Inbox, Answer Bank, Traces, Profile) must be mapped to reactive Vue 3 components backed by asynchronous FastAPI endpoints.

## Goals / Non-Goals

**Goals:**
- **100% Feature Parity**: Implement all 22 template capabilities in modular Vue 3 components.
- **Unified Navigation & State**: Single navigation sidebar enabling instantaneous zero-reload transitions between Workspace, Opportunities, Applications, Toolkit, and Agent Center.
- **RESTful API Expansion**: Extend FastAPI with endpoints for AI briefing generation, offer comparison calculation, traces, and answer bank retrieval.
- **Responsive Theme & Layout**: Consistent dark-mode UI with customizable light-mode tokens and Lucide icons.

**Non-Goals:**
- Server-Side Rendering (SSR) via Nuxt (static client bundle served from FastAPI is optimal).
- External CSS framework churn (standardize strictly on Tailwind CSS).

## Decisions

### 1. View & Component Modularization
- **Structure**:
  ```
  frontend/src/
  ├── views/
  │   ├── DashboardView.vue         # AI Briefing, stats, urgent deadlines
  │   ├── KanbanView.vue            # 8-stage interactive pipeline
  │   ├── CompaniesView.vue         # S/A/B tier directory & search
  │   ├── OfferCompareView.vue      # Compensation & 12% fund calculator
  │   ├── DecisionInboxView.vue     # HITL approval queue
  │   ├── AnswerBankView.vue        # Searchable interview defense QA
  │   ├── TracesView.vue            # Agent execution audit tree
  │   ├── TimelineView.vue          # Milestone timeline
  │   └── ProfileView.vue           # SSOT profile & 3-track resume manager
  ├── components/
  │   ├── QuickCopyDrawer.vue       # Floating clipboard drawer
  │   ├── AutofillModal.vue         # Live CDP execution dialog
  │   └── HeaderStats.vue           # Pipeline counter badge
  ```

### 2. Backend REST API Expansion (`backend/app/api/routes.py`)
- **New Endpoints**:
  - `GET /api/v1/dashboard/briefing`: Computes stale applications (> 7 days) and high-match proposals (>= 80).
  - `GET /api/v1/traces`: Returns historical `agent_traces` records.
  - `GET /api/v1/answer-bank`: Returns categorized project defense Q&A list.
  - `POST /api/v1/compare/offers`: Calculates net income, tax, and 12% housing fund projections.

### 3. Client State Management
- Use Vue 3 Composition API with reactive stores (`ref`/`computed`) for instant filtering, active tab tracking, and clipboard drawer synchronization.

## Risks / Trade-offs

- **[Risk] High Initial Bundle Size**
  → *Mitigation*: Leverage Vite's native code-splitting and asset tree-shaking; production dist remains under 100KB gzip.
- **[Risk] Schema Desynchronization with Legacy DB**
  → *Mitigation*: SQLAlchemy models map directly to existing `tracker.db` SQLite tables without altering column definitions.
