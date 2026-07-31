## Why

AI Agents (such as scheduled Hermes tasks) can perform automated company and job sourcing, but without a human-in-the-loop (HITL) review mechanism and feedback loop, users face information overload and agents repeatedly suggest unwanted positions. Adding a review inbox, agent rationale tracking, low-friction rejection feedback, and preference exposure via MCP enables seamless human decision-making and continuous agent alignment without extra LLM overhead during user interaction.

## What Changes

- **Review Inbox & Staging Workflow**: Introduce explicit pending application review states (`pending`, `to_apply`, `rejected`, `applied`) to stage agent-sourced proposals until approved or rejected by a human.
- **Rich Proposal Data Fields**: Extend application creation endpoints and MCP tools to capture `match_score`, `agent_reason`, `agent_task_id`, and `source_url`.
- **Rejection Feedback & Memory Capture**: Store human rejection tags and raw text feedback directly in a `memories` table upon rejection without mandatory LLM processing delays.
- **Agent Preference Retrieval API & MCP Tool**: Expose candidate profile and negative constraint rules via `GET /api/v1/profile/preferences` and the `get_user_preferences` MCP tool so agents ingest preferences prior to sourcing.

## Capabilities

### New Capabilities
- `hitl-sourcing`: Human-in-the-loop staging inbox, proposal recommendation metadata, rejection memory capture, and agent preference retrieval interfaces.

### Modified Capabilities
- None.

## Impact

- **Database Models**: Updates to `Application` model in `models.py` for review metadata and addition of `Memory` model.
- **API Routes**: New endpoints `POST /api/v1/applications/<id>/review` and `GET /api/v1/profile/preferences` in `routes/agent_api.py`.
- **MCP Server**: New tool `get_user_preferences` and updated `create_application` signature in `mcp_server.py`.
- **Skills & Docs**: Updated `skills/company-finder/SKILL.md` with 2-phase preference ingestion workflow, and updated `docs/api.md`.
