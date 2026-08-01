## 1. Database & Model Updates

- [x] 1.1 Add `resume_id` column to `Application` model in `models.py` referencing `resumes.id`
- [x] 1.2 Generate or execute migration script to update SQLite `applications` table

## 2. Agent REST API & MCP Enhancements

- [x] 2.1 Update `routes/agent_api.py` to expose `/api/agent/tasks` (GET list) and `/api/agent/tasks/<task_id>` (GET trace details)
- [x] 2.2 Add `evaluate_jd` tool in `mcp_server.py` to compare JD text against candidate profile & memory rules with automated trace logging
- [x] 2.3 Update `create_application` tool in `mcp_server.py` and application routes to support `resume_id` parameter

## 3. Web UI & Frontend Integration

- [x] 3.1 Update Dashboard UI (`templates/index.html` or dedicated template) to include Agent Task Center & Activity Feed card
- [x] 3.2 Add JavaScript polling to load and render Agent tasks and event traces in the Web UI Activity Feed

## 4. Testing & Verification

- [x] 4.1 Write unit tests in `tests/test_agent_api.py` and `tests/test_routes.py` for task log endpoints and `resume_id` binding
- [x] 4.2 Run pytest suite and verify build/test status
