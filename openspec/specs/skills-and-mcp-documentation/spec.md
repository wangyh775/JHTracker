# skills-and-mcp-documentation Specification

## Purpose

Provide comprehensive documentation covering FastMCP server configuration, agent skill installation, and HITL workflow for AI assistants.

## Requirements

### Requirement: Complete Skills and MCP Guide
The repository SHALL contain `docs/SKILLS_AND_MCP_GUIDE.md` detailing architecture, `.mcp.json` setup, skill installation steps, and human-in-the-loop review operations.

#### Scenario: User configures new AI agent platform
- **WHEN** a user follows `docs/SKILLS_AND_MCP_GUIDE.md` to connect an AI agent (e.g. OpenCode, Claude Code, Cursor, Trae)
- **THEN** the user can successfully connect to `mcp_server.py` and import the skills under `skills/`.
