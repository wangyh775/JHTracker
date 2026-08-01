## Context

See `proposal.md` for motivation.
JHTracker uses Flask with SQLite (`data/tracker.db`), SQLAlchemy Models in `models.py`, Blueprint routes in `routes/`, and FastMCP server in `mcp_server.py`. Existing models include `AgentTask` and `AgentEvent` in `models.py`, which are currently populated via MCP tool `record_agent_trace`.

## Goals / Non-Goals

**Goals:**
- Add `resume_id` foreign key to `Application` model with SQLite migration compatibility.
- Implement `evaluate_jd` tool in FastMCP `mcp_server.py` using candidate profile (`data/profile.md`) and negative rules from `memories` table.
- Expose REST endpoints `/api/agent/tasks` and `/api/agent/tasks/<task_id>` in `routes/agent_api.py`.
- Add an Agent Task Center & Activity Feed section on the Web UI Dashboard.

**Non-Goals:**
- Complex multi-agent workflow orchestration engines (deferred to future changes).
- Real-time WebSocket trace streaming (HTTP polling is sufficient for current scale).

## Decisions

- **Decision 1: Use Alembic/Flask-Migrate for DB Schema updates**
  - *Rationale*: Safe migration for existing SQLite databases to add `resume_id` foreign key column.
- **Decision 2: Light-weight rule & Keyword Matching Engine for `evaluate_jd`**
  - *Rationale*: Evaluate JD text locally against `profile.md` keywords and negative rules in `memories` before generating trace logs, ensuring zero external API latency dependencies if LLM isn't configured, while formatting result for MCP Agent consumption.
- **Decision 3: REST API Polling for Web UI Task Center**
  - *Rationale*: Simple and robust frontend polling of `/api/agent/tasks` without introducing WebSocket dependencies.

## Risks / Trade-offs

- [Risk] Missing `resume_id` in existing applications → Mitigation: Set column as nullable in SQLite schema.
- [Risk] SQLite lock during concurrent trace writes from MCP → Mitigation: Keep WAL mode enabled and connection durations minimal.
