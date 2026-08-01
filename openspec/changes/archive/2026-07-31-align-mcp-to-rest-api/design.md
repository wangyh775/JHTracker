## Context

MCP Server (`mcp_server.py`) currently has 9 tools. The REST API (`routes/agent_api.py`) covers far more operations. Agent clients use MCP protocol, not HTTP, so they cannot access REST endpoints. The goal is to make MCP the complete interface for AI agents, while keeping REST API as a fallback for frontend and for when MCP is unavailable.

See proposal.md for motivation. See specs/mcp-full-coverage/spec.md for full tool requirements.

## Goals / Non-Goals

**Goals:**
- MCP Server expands from 9 to 36 tools across 11 domains
- Delete operations require explicit confirmation (Agent cannot delete without extra step)
- `batch_evaluate_jds()` accepts array of JD inputs, returns array of results
- REST API unchanged — maintained as fallback
- Skills updated to reference new tools

**Non-Goals:**
- No changes to the ORM models or database schema
- No changes to the REST API endpoints
- No changes to the frontend UI
- No changes to the HITL decision flow

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Implementation pattern | Direct SQLite via `get_db_connection()` | All existing MCP tools use this pattern, avoiding Flask/SQLAlchemy dependency in MCP process |
| Write tool design | `get_db_connection()` + cursor + json.dumps return | Consistent with existing 9 tools — MCP runs as standalone process, not inside Flask |
| Delete protection | Delete tools require a `confirm=True` parameter | Agent must explicitly pass confirm=True to delete; accidental calls without confirm return error |
| batch_evaluate_jds | Loop over inputs, call evaluate_jd logic per item | Simple, no parallelism needed for <20 items; each gets its own trace |
| Skill updates | Only update the "对应 MCP 工具" column in each SKILL.md | 4 skills already have correct structure; just need to reference new tools |

## Risks / Trade-offs

- [Code duplication] MCP tools duplicate query logic from REST API. → Acceptable: MCP is standalone (no Flask), and keeping them separate avoids coupling
- [Maintenance burden] 36 tools to maintain. → Each tool is 10-20 lines, following the same pattern; low per-tool cost
- [Test coverage] 27 new tools need tests. → Use `tmp_path` + `monkeypatch` pattern from existing `TestMCPToolsDirectly` tests