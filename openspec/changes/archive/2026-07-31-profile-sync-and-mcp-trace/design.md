## Context

`mcp_server.py` uses `sqlite3` directly to access `tracker.db` and read `data/profile.md`. See `proposal.md` for background.

## Goals / Non-Goals

**Goals:**
- Expose `update_candidate_profile(content: str)` in `mcp_server.py` to write `data/profile.md`.
- Expose `record_agent_trace(task_id: str, agent_name: str, event_type: str, payload: str_or_dict, status: str)` in `mcp_server.py` inserting/updating `agent_tasks` and `agent_events` in `tracker.db`.
- Update `skills/candidate-profile-and-resume/SKILL.md` to detail resume-to-profile extraction workflow.

**Non-Goals:**
- Modifying SQLite schema or existing Flask routes.

## Decisions

1. **Direct SQLite for Trace Tool in MCP**:
   - In `mcp_server.py`, query/insert into `agent_tasks` and `agent_events` using standard `sqlite3` connection (matching existing tools pattern in `mcp_server.py`).
2. **Skill Prompt Alignment**:
   - Update `candidate-profile-and-resume/SKILL.md` with explicit steps: Read Resume -> Extract Struct -> Call `update_candidate_profile`.
   - Update `job-sourcing-and-scoring/SKILL.md` and `application-tracker/SKILL.md` to recommend calling `record_agent_trace`.

## Risks / Trade-offs

- **[Risk]** Writing `profile.md` concurrently from Web and MCP could cause race conditions.
- **[Mitigation]** Standard file write with UTF-8 encoding; typical single-user access pattern avoids heavy concurrency issues.
