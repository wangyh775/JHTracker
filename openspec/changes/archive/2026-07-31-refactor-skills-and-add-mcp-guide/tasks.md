## 1. Skill Consolidation

- [x] 1.1 Remove the 8 legacy skill directories in `skills/` (`company-finder`, `career-tracker-scorer`, `career-tracker-application`, `career-tracker-offer`, `career-tracker-profile`, `career-tracker-resume`, `career-tracker-ops`, `career-tracker-import`).
- [x] 1.2 Create `skills/job-sourcing-and-scoring/SKILL.md` combining company searching, web fetching, AI scoring, and negative memory rules.
- [x] 1.3 Create `skills/application-tracker/SKILL.md` covering application status tracking, offer lifecycle, and HITL review integration.
- [x] 1.4 Create `skills/candidate-profile-and-resume/SKILL.md` for profile management, resume text/PDF parsing, and preference rules.
- [x] 1.5 Create `skills/tracker-ops/SKILL.md` for bulk data import, deduplication, auto-archiving, and database health operations.

## 2. Documentation & MCP Integration Guide

- [x] 2.1 Create `docs/SKILLS_AND_MCP_GUIDE.md` detailing system architecture, FastMCP server (`mcp_server.py`), `.mcp.json` setup, skill installation steps, and HITL approval workflow.

## 3. Verification

- [x] 3.1 Verify all 4 consolidated skills contain valid frontmatter and instructions.
- [x] 3.2 Verify `docs/SKILLS_AND_MCP_GUIDE.md` exists and covers all setup and execution instructions.
- [x] 3.3 Run `pytest` to confirm project tests remain green.
