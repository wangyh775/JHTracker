## 0. Documentation First

- [x] 0.1 Update `docs/architecture.md` with Agent-Native Architecture and MCP Server details
- [x] 0.2 Update `docs/database.md` with `AgentTask` and `AgentEvent` schema and relations
- [x] 0.3 Update `docs/api.md` with `/api/v1/*` Agent endpoints, `/api/stream` SSE, and MCP tool references

## 1. Data Model & Database Migration

- [x] 1.1 Add `AgentTask` and `AgentEvent` models in `models.py`
- [x] 1.2 Create and apply database table initialization / migration for `data/tracker.db`

## 2. Agent RESTful API (`agent-api`)

- [x] 2.1 Implement `routes/agent_api.py` blueprint with `/api/v1/companies/search`, `/api/v1/companies/<id>/score`, and `/api/v1/profile`
- [x] 2.2 Register `agent_api` blueprint in `app.py`
- [x] 2.3 Add unit tests for `agent-api` in `tests/test_agent_api.py`

## 3. MCP Server (`mcp-server`)

- [x] 3.1 Create `mcp_server.py` exposing `jhtracker://profile` resource and `search_companies` tool
- [x] 3.2 Add CLI / stdio entrypoint for MCP clients (Claude Desktop, Cursor)

## 4. Agent Trace Logging & UI (`agent-trace`)

- [x] 4.1 Implement `/api/v1/traces` endpoint in `routes/agent_api.py` to record agent tasks and events
- [x] 4.2 Create `/traces` UI route and `templates/traces.html` template to review agent execution history
- [x] 4.3 Trigger SSE notifications upon trace logging for real-time dashboard alerts
- [x] 4.4 Add unit tests for trace logging and web interface
