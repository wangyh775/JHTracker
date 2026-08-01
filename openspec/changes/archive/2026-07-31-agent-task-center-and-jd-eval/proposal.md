## Why

JHTracker currently functions as a job application tracker, but lacks visibility into AI Agent operations, dynamic Job Description (JD) matching tools via MCP, and explicit links between job applications and specific resume versions. Adding an Agent Task Center with Activity Feed logging, an `evaluate_jd` MCP tool for on-demand job fit analysis, and `resume_id` tracking on applications establishes JHTracker as an agent-driven Career OS with observable task execution and transparent AI reasoning.

## What Changes

- **Agent Task Center & Activity Feed**: Introduce a dedicated Web UI section and REST endpoints (`/api/agent/tasks`, `/api/agent/tasks/<task_id>`) for monitoring agent tasks and real-time event trace logs.
- **JD Matching MCP Tool**: Add `evaluate_jd` tool in `mcp_server.py` that compares candidate profile (`data/profile.md`) and user negative constraint rules against a provided JD text, returning a score, match highlights, and reasoning.
- **Application Resume Binding**: Add `resume_id` foreign key to `applications` model and expose it across routes and MCP tools (`create_application`).

## Capabilities

### New Capabilities
- `agent-task-center`: Monitoring and activity feed tracking for Agent tasks and execution event traces.
- `jd-evaluation-mcp`: On-demand JD matching and reasoning tool for MCP host agents.
- `application-resume-binding`: Binding applications to specific resume versions.

### Modified Capabilities

## Impact

- **Database**: Adds `resume_id` column to `applications` table.
- **API & MCP**: Updates `mcp_server.py` with `evaluate_jd`, updates `create_application` to accept `resume_id`, and expands `routes/agent_api.py` for task log retrieval.
- **UI**: Adds Agent Task Center & Activity Feed UI views on Dashboard.
