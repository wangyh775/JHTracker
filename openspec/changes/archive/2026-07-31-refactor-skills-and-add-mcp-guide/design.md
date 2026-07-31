## Context

The current `skills/` directory contains 8 legacy skill subdirectories. FastMCP server (`mcp_server.py`) and REST APIs (`routes/agent_api.py`) are fully functional with HITL (Human-in-the-Loop) review capabilities. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Consolidate legacy 8 skills into 4 clean, domain-driven core skills in `skills/`.
- Align skill definitions with `mcp_server.py` FastMCP tools (`search_companies`, `create_company`, `create_application`, `update_company_score`, `get_user_preferences`, `get_candidate_profile`).
- Document installation, configuration, and agent integration in `docs/SKILLS_AND_MCP_GUIDE.md`.

**Non-Goals:**
- Changing existing SQLite database schema (`models.py`).
- Altering existing Flask REST API endpoints or templates.

## Decisions

1. **Skill Merging Strategy**:
   - Merge `company-finder` + `career-tracker-scorer` -> `job-sourcing-and-scoring`.
   - Merge `career-tracker-application` + `career-tracker-offer` -> `application-tracker`.
   - Merge `career-tracker-profile` + `career-tracker-resume` -> `candidate-profile-and-resume`.
   - Merge `career-tracker-ops` + `career-tracker-import` -> `tracker-ops`.
2. **Directory Structure**:
   - Clean up old directories in `skills/` and write the 4 consolidated `SKILL.md` files.
   - Create `docs/SKILLS_AND_MCP_GUIDE.md` for comprehensive documentation.

## Risks / Trade-offs

- **[Risk]** Existing agent workflows referencing old skill names (e.g. `company-finder`) might fail if not updated.
- **[Mitigation]** Include alias trigger words in `description` fields of the 4 new skills so agents will still match user intents seamlessy.
