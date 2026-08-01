## Context

See `proposal.md` for motivation and system re-orientation toward a Human-in-the-Loop (HITL) Career Intelligence OS.
JHTracker currently allows Agents to evaluate JDs and bind applications to resumes via FastMCP tools. However, applications created by Agent tools currently jump directly into actionable statuses, bypassing explicit human approval and lacking a mechanism to capture user feedback on rejected proposals.

## Goals / Non-Goals

**Goals:**
- Introduce a `DecisionFeedback` model to persist human decision actions (`approve`, `reject`, `edit`) and raw feedback strings.
- Enforce strict approval boundaries: Agent-created applications default to `Pending Approval` (or `Draft`).
- Provide a `Decision Inbox` UI component in `templates/dashboard.html` that displays proposal cards with score breakdown, risk warnings, and action triggers.
- Enhance `evaluate_jd` in `mcp_server.py` to ingest historical `DecisionFeedback` and negative rules to dynamically adjust evaluation scores.

**Non-Goals:**
- Fully automated external application submission (auto-apply without human approval is explicitly prohibited).
- Complex ML-based feedback learning models (simple keyword and rules-based ingestion from `DecisionFeedback` into `memories` is sufficient).

## Decisions

### 1. Database Schema Extension for Decision Feedback
- **Choice**: Create `DecisionFeedback` model linked to `Application` via foreign key `application_id`.
- **Fields**: `id`, `application_id`, `action` (`approve`/`reject`/`edit`), `reason_category`, `raw_feedback`, `created_at`.
- **Rationale**: Keeps application status transitions audit-trackable while feeding human feedback into the memory subsystem.

### 2. Default Status for Agent-Created Applications
- **Choice**: Change default status in `create_application` FastMCP tool to `Pending Approval`.
- **Rationale**: Enforces human-in-the-loop principle: Agents stage proposals; humans approve and move status to `Applied`.

### 3. Decision Inbox UI & API Design
- **Choice**: Add `/api/agent/decisions/pending` (GET) and `/api/agent/decisions/<application_id>` (POST) REST endpoints.
- **UI Component**: Render a top-level "Decision Inbox" card on `templates/dashboard.html` with interactive buttons (`Approve & Apply`, `Reject with Reason`, `Edit Draft`).

## Risks / Trade-offs

- [Risk] Pending proposals might accumulate if the user doesn't review them regularly.
  → *Mitigation*: Display a prominent badge count in the top navigation and Agent Task Center header.
- [Risk] Duplicate feedback entries could clutter the evaluation prompt.
  → *Mitigation*: Aggregate recent `DecisionFeedback` entries (latest 20) when constructing the `evaluate_jd` context.

## Migration Plan

1. Create Flask-Migrate script `add_decision_feedbacks_table.py` for new `DecisionFeedback` model.
2. Upgrade local database via `flask db upgrade`.
3. Add REST API endpoints in `routes/agent_api.py`.
4. Update `mcp_server.py` `create_application` default status and `evaluate_jd` prompt logic.
5. Update UI in `templates/dashboard.html`.
