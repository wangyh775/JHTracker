## 1. Data Model & Database Layer

- [x] 1.1 Extend `Application` model in `models.py` with `match_score`, `agent_reason`, `agent_task_id`, and `source_url`
- [x] 1.2 Add `Memory` model (`memories` table) in `models.py` for recording user preferences and rejection feedback

## 2. API & Endpoint Layer

- [x] 2.1 Update `POST /api/v1/applications` endpoint in `routes/agent_api.py` to accept recommendation metadata fields
- [x] 2.2 Add `POST /api/v1/applications/<id>/review` endpoint in `routes/agent_api.py` to handle approval and rejection with memory creation
- [x] 2.3 Add `GET /api/v1/profile/preferences` endpoint in `routes/agent_api.py` to expose user preferences and rejection notes

## 3. MCP Server & Tool Layer

- [x] 3.1 Update `create_application` tool in `mcp_server.py` to accept optional `match_score`, `agent_reason`, `agent_task_id`, and `source_url`
- [x] 3.2 Add `get_user_preferences` tool in `mcp_server.py` returning structured negative constraints and recent rejection notes

## 4. Skill & Documentation Layer

- [x] 4.1 Update `skills/company-finder/SKILL.md` to instruct agents to call preference retrieval before searching
- [x] 4.2 Update `docs/api.md` and `docs/getting-started.md` with new endpoints and MCP tools

## 5. Testing & Verification

- [x] 5.1 Add unit test cases in `tests/test_agent_api.py` for review and preferences endpoints
- [x] 5.2 Execute pytest suite and verify all test cases pass
