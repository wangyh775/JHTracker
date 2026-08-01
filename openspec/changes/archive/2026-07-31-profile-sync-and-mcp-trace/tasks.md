## 1. FastMCP Server Tools Implementation

- [x] 1.1 Add `update_candidate_profile(content: str)` tool to `mcp_server.py`.
- [x] 1.2 Add `record_agent_trace(task_id: str, agent_name: str = "Agent", event_type: str = "info", payload: dict = None, status: str = "running")` tool to `mcp_server.py`.

## 2. Skill Documentation Updates

- [x] 2.1 Update `skills/candidate-profile-and-resume/SKILL.md` to document resume extraction and profile update workflow using `update_candidate_profile`.
- [x] 2.2 Update `skills/job-sourcing-and-scoring/SKILL.md` and `skills/application-tracker/SKILL.md` to instruct agents to call `record_agent_trace`.

## 3. Verification

- [x] 3.1 Update `tests/test_agent_api.py` (or add tests) to verify `update_candidate_profile` and `record_agent_trace` behavior.
- [x] 3.2 Run `pytest` to verify all tests pass.
