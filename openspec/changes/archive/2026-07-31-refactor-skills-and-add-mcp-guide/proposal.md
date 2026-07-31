## Why

The current Agent Skills in `skills/` are fragmented into 8 overly detailed files, causing agent hesitation, trigger overlap, and missing HITL (Human-in-the-Loop) flow integration. Moreover, there is no comprehensive documentation explaining how to install, configure, and use these skills in conjunction with the project's FastMCP server (`mcp_server.py`).

## What Changes

- **Consolidate Skills**: Merge the 8 existing skills in `skills/` into 4 cohesive, domain-driven core skills:
  1. `job-sourcing-and-scoring`: Company discovery, web search, AI matching score, and memory/rejection-rule ingestion.
  2. `application-tracker`: Full application lifecycle tracking (pending review, applied, interviews, offer, rejection) with HITL review integration.
  3. `candidate-profile-and-resume`: Candidate career preferences, resume file management, and negative constraint memory management.
  4. `tracker-ops`: Bulk data import, deduplication, auto-archiving, and DB health operations.
- **Add Installation & Integration Guide**: Create `docs/SKILLS_AND_MCP_GUIDE.md` covering MCP server setup (`mcp_server.py`), `.mcp.json` configuration, skills installation for various AI agents (OpenCode, Claude Code, Cursor, Trae), and HITL approval workflow.

## Capabilities

### New Capabilities
- `agent-skills-consolidation`: Core Agent skills consolidation into 4 domain-driven skills with MCP integration and HITL review support.
- `skills-and-mcp-documentation`: Complete installation, setup, and usage documentation in `docs/SKILLS_AND_MCP_GUIDE.md`.

### Modified Capabilities

## Impact

- `skills/`: Replaces 8 legacy skill directories (`company-finder`, `career-tracker-scorer`, `career-tracker-application`, `career-tracker-offer`, `career-tracker-profile`, `career-tracker-resume`, `career-tracker-ops`, `career-tracker-import`) with 4 consolidated skill directories.
- `docs/`: Adds `docs/SKILLS_AND_MCP_GUIDE.md`.
- No breaking changes to SQLite schema or Flask API endpoints.
