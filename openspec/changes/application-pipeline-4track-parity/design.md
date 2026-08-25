## Context

See `proposal.md` for motivation. The application previously migrated to an asynchronous FastAPI backend and Vue 3 frontend but omitted the structured tabular tracking, 4-track career routing, and Zero-Submit audit stations present in v1.0.

## Goals / Non-Goals

**Goals:**
- **Documentation-First Protocol**: Fully document all entities, 4-track routing rules, and API endpoints in `docs/` prior to code modifications.
- **Backend Schema & Entity Parity**: Align SQLAlchemy models and Pydantic schemas to fully support active/archived separation, submission field snapshots, feedback logging, and preference rules.
- **4-Track Engineering Specialization**: Implement fine-grained job matching (Control, Embedded/Auto, Mechatronics, Mechanical/CFD) with automated pitch and resume resolution.
- **Vue-Router SPA Architecture**: Refactor Vue 3 SPA with full routing (`/applications`, `/to-apply`, `/submissions`, `/submissions/:id`), high-density table views, and toggleable Kanban.
- **Zero-Submit HITL Security**: Guarantee that automation scripts stop at field prefill without auto-submitting web applications.

**Non-Goals:**
- Modifying underlying FastMCP 37-tool toolchain signatures (keep existing tool protocol intact).
- Cloud deployment (maintain local zero-config SQLite WAL operation).

## Decisions

### Decision 1: `vue-router` with Tabular Workbenches as Primary View
- **Choice**: Structure the frontend around `vue-router` where `/applications` defaults to a rich tabular layout with an inline Kanban toggle.
- **Rationale**: Tabular views offer superior information density for sorting, batch archival, and status tracking during high-volume recruitment season, while preserving Kanban as a visual option.
- **Alternatives Considered**: Keeping a single monolithic `v-if="currentTab"` view in `App.vue` (rejected due to poor state retention, lack of deep linking, and unmaintainable component size).

### Decision 2: 4-Track Domain Classification Taxonomy
- **Choice**: Segment candidate capabilities into 4 dedicated engineering tracks:
  1. `control`: MPC, EKF, State Space, Motion Control, Trajectory Planning.
  2. `embedded_auto`: STM32H7, RK3588, Linux, C/C++, Klipper, Firmware, PLC.
  3. `mechatronics`: EPLAN, ECAD, Cabinets, Anti-Interference, Sensors, Power.
  4. `mechanical_cfd`: SolidWorks, CoreXY, CFD, Fluent, Thermal-Fluid, CAE.
- **Rationale**: Matches the candidate's cross-disciplinary research profile at Dalian Jiaotong University and maximizes keyword alignment with recruiter ATS filters.

### Decision 3: Zero-Submit Prefill Audit Entity Architecture
- **Choice**: Store prefilled DOM fields as JSON in `application_submissions` table and expose a dedicated `/submissions/:id` review page.
- **Rationale**: Eliminates accidental submission risk, allows candidate to verify salary expectations and personal data, and provides direct links to the live employer portal.

### Decision 4: Backend Port Re-alignment to 5000
- **Choice**: Standardize default FastAPI uvicorn port to `5000` with Vite proxy forwarding `/api` requests from `5173`.
- **Rationale**: Preserves developer muscle memory, existing curl scripts, and local browser bookmarks from v1.0.

## Risks / Trade-offs

- **[Risk] SQLite Migration Schema Divergence** → **Mitigation**: Implement automatic column check and table initialization in FastAPI startup lifespan (`PRAGMA table_info`).
- **[Risk] Large Prefilled JSON Payloads** → **Mitigation**: Store DOM field snapshots with compressed text formatting and limit screenshot uploads to local filesystem paths.
