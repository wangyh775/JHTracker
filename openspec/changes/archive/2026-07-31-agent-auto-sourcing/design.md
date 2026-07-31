## Context

See `proposal.md` for motivation. Currently JHTracker provides read/search endpoints for companies and scoring APIs for job postings, but lacks automated write endpoints for AI Agents to add companies and pending applications.

## Goals / Non-Goals

**Goals:**
- Provide API endpoints for company batch deduplication insertion and pending application creation in `routes/agent_api.py`.
- Expose corresponding tools (`create_company`, `create_application`) in `mcp_server.py`.
- Update `skills/company-finder/SKILL.md` to guide AI agents through company sourcing and application staging workflows.
- Document documentation-first updates across `docs/`.

**Non-Goals:**
- Automated background scheduling inside JHTracker Flask process (scheduling will rely on external Cron/Systemd/Agent triggers via API/MCP).
- Automatic application submission (applications are staged in `pending` status for manual human submission).

## Decisions

- **Write Endpoints in API Layer**: Add `POST /api/v1/companies` and `POST /api/v1/applications` to `routes/agent_api.py`.
- **Deduplication Logic**: Match company records case-insensitively by name. If existing, return existing record ID; if new, insert into database.
- **Pending Application Staging**: Application default status is `pending` when created by agent API/MCP, preserving human candidate control.
- **MCP Tool Integration**: Map MCP tools directly to database/API functions using FastMCP decorators in `mcp_server.py`.

## Risks / Trade-offs

- [Risk] Duplicate company names with slightly different formatting (e.g. "Google Inc." vs "Google") → Mitigation: Perform normalized string trimming and lowercasing match; support manual merge in Web UI.
- [Risk] Unvalidated URLs submitted by Agents → Mitigation: Validate URL format in API layer before database write.
