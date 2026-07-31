## Context

JHTracker maintains a Three-Tier Architecture (API -> MCP Tool -> Agent Skill). The system relies on SQLite (`data/tracker.db`) via SQLAlchemy and Flask. Currently, `Application` model has basic status fields, and `routes/agent_api.py` allows creating pending applications. However, there is no structured representation for agent recommendation metadata (match score, agent reason, provenance), no dedicated endpoint for human review/rejection feedback, and no `Memory` table to store candidate preferences for agent consumption.

## Goals / Non-Goals

**Goals:**
- Extend `Application` model with `match_score`, `agent_reason`, `agent_task_id`, and `source_url`.
- Add a new `Memory` model (`memories` table) to record structured rules and raw feedback text upon rejection.
- Implement `POST /api/v1/applications/<id>/review` for approving (`pending` -> `to_apply`) or rejecting (`pending` -> `rejected` + creating `Memory`).
- Implement `GET /api/v1/profile/preferences` and `get_user_preferences` MCP tool to return negative constraints and raw rejection feedback.
- Update `skills/company-finder/SKILL.md` to instruct agents to invoke preference retrieval before sourcing.

**Non-Goals:**
- Real-time LLM feedback extraction during user rejection (keep zero-latency, 0-token overhead by storing raw feedback directly).
- Vector store / embedding DB migration (sticking to lightweight SQLite SQL queries).

## Decisions

### Decision 1: Raw Feedback & Category Direct Storage vs. Real-time LLM Extraction
- **Choice**: Store pre-defined UI category tags and raw human text directly into the `memories` table when a user clicks "Reject".
- **Rationale**: Avoids 1-3s API latency during UI card review, eliminates token cost, and leverages downstream LLM's natural language comprehension when the Agent reads memory context via MCP.
- **Alternatives Considered**: Real-time LLM extraction via prompt during rejection (rejected due to latency, token cost, and potential hallucination).

### Decision 2: Application Review Endpoint Structure
- **Choice**: Unified `POST /api/v1/applications/<id>/review` with JSON payload `{ "action": "approve" | "reject", "category": "...", "rule_value": "...", "raw_feedback": "..." }`.
- **Rationale**: Single endpoint handles status transition and memory capture atomically inside a DB transaction.

### Decision 3: MCP Tool Signature Extension
- **Choice**: Extend `create_application` tool with optional parameters (`match_score`, `agent_reason`, `agent_task_id`, `source_url`) and add new `get_user_preferences` tool.
- **Rationale**: Backwards compatible with existing MCP callers while giving agents full access to HITL metadata and preference loading.

## Risks / Trade-offs

- **[Risk]** Redundant memory entries if user rejects multiple similar positions with free-text feedback.
  - *Mitigation*: Simple SQL sorting by `created_at desc` and limiting recent notes (e.g., top 10) in preference responses keeps prompt payload small.

## Migration Plan

1. Update `models.py` with column additions and `Memory` model class.
2. Update `routes/agent_api.py` with review and preferences routes.
3. Update `mcp_server.py` with tool updates and new `get_user_preferences` tool.
4. Update `skills/company-finder/SKILL.md` and documentation files.
5. Add test coverage in `tests/test_agent_api.py`.
