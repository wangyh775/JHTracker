## Context

JHTracker is a Flask and SQLite web application storing career memory (companies, applications, profiles). See `proposal.md` for motivation.
Existing concurrency setup uses SQLite WAL mode (`PRAGMA journal_mode=WAL;` and `busy_timeout=5000;`) and Server-Sent Events (`/api/stream`) for live UI notifications.

## Goals / Non-Goals

**Goals:**
- Implement RESTful JSON endpoints under `/api/v1/` for Agent interactions.
- Provide a Model Context Protocol (MCP) server integration (`mcp-server`) exposing JHTracker resources and tools.
- Implement data models (`AgentTask`, `AgentEvent`) and UI routes (`/traces`) to track Agent decision reasoning and execution.
- Maintain seamless SQLite WAL concurrency and live SSE notifications.

**Non-Goals:**
- Embedding LLM execution runtime inside JHTracker core (JHTracker acts as memory & control interface).
- Complex OAuth2 enterprise identity providers for Agent API authentication (simple API Token header authentication is sufficient).

## Decisions

### Decision 1: Flask Blueprint for `/api/v1/` vs standalone API server
- **Choice**: Blueprint `agent_api` registered on existing Flask app under `/api/v1/`.
- **Rationale**: Reuses existing SQLAlchemy models and WAL connection configuration without adding process management overhead.

### Decision 2: MCP Server implementation strategy
- **Choice**: Embedded FastMCP or standard `mcp` Python SDK CLI entrypoint (`mcp_server.py`) sharing database access with Flask app via `models.py`.
- **Rationale**: Allows external clients (Claude Desktop, Cursor) to launch `python -m mcp_server` stdio transport while reading/writing `data/tracker.db` under SQLite WAL mode safely.

### Decision 3: Trace Data Model design
- **Choice**: Add `AgentTask` (task_id, agent_name, status, created_at) and `AgentEvent` (event_id, task_id, event_type, payload_json, timestamp) tables.
- **Rationale**: Decouples high-frequency execution steps (`AgentEvent`) from overall task state (`AgentTask`), making querying and UI rendering simple and performant.

## Risks / Trade-offs

- **[Risk]**: SQLite database lock under high concurrent write load from multiple agents and MCP tools.
  - **Mitigation**: Rely on existing WAL mode and 5000ms `busy_timeout` configured in `app.py`.
- **[Risk]**: Schema updates on existing database.
  - **Mitigation**: Use Flask-Migrate / Alembic or conditional table creation helpers for safe schema migration.

## Migration Plan

1. Update `models.py` with `AgentTask` and `AgentEvent` models.
2. Run database migration script to add new tables to `data/tracker.db`.
3. Register `/api/v1` routes in `routes/agent_api.py`.
4. Deploy `mcp_server.py` entrypoint.
