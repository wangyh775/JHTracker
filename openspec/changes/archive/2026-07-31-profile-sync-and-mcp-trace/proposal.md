## Why

Currently, FastMCP server (`mcp_server.py`) only provides read access to candidate profile (`get_candidate_profile`), lacking a write tool for agents to update `data/profile.md` after parsing uploaded resumes. Furthermore, while the backend supports Agent Tracing via REST API (`/api/v1/traces`), FastMCP server has no tool to record Agent tasks and execution traces, disconnecting pure MCP agents from the UI trace tree (`/traces`).

## What Changes

- **MCP Profile Write Tool**: Add `update_candidate_profile(content: str)` tool to `mcp_server.py` allowing AI agents to update candidate preferences in `data/profile.md`.
- **MCP Agent Trace Tool**: Add `record_agent_trace(task_id: str, agent_name: str, event_type: str, payload: dict)` tool to `mcp_server.py` allowing pure MCP agents to log execution steps into `AgentTask` and `AgentEvent` models.
- **Skill Instructions Sync**: Update `skills/candidate-profile-and-resume/SKILL.md` to guide agents on parsing uploaded resumes and calling `update_candidate_profile`. Update `skills/job-sourcing-and-scoring/SKILL.md` and `skills/application-tracker/SKILL.md` to instruct agents on logging execution traces.

## Capabilities

### New Capabilities
- `profile-write-mcp-tool`: Enable AI agents to update `data/profile.md` via FastMCP tool `update_candidate_profile`.
- `trace-logging-mcp-tool`: Enable AI agents to record execution tasks and events via FastMCP tool `record_agent_trace`.

### Modified Capabilities

## Impact

- `mcp_server.py`: Adds `update_candidate_profile` and `record_agent_trace` FastMCP tools.
- `skills/candidate-profile-and-resume/SKILL.md`: Adds workflow for extracting resume content and syncing to profile.md.
- `skills/job-sourcing-and-scoring/SKILL.md` & `skills/application-tracker/SKILL.md`: Adds trace logging instructions.
- `tests/test_agent_api.py`: Adds unit tests for new MCP tools.
