# skills-and-mcp-documentation Specification

## Purpose

Provide comprehensive documentation covering FastMCP server configuration, agent skill installation, and HITL workflow for AI assistants.

## Requirements

### Requirement: Complete Skills and MCP Guide
The repository SHALL contain `docs/SKILLS_AND_MCP_GUIDE.md` detailing architecture, `.mcp.json` setup, skill installation steps, and human-in-the-loop review operations.

#### Scenario: User configures new AI agent platform
- **WHEN** a user follows `docs/SKILLS_AND_MCP_GUIDE.md` to connect an AI agent (e.g. OpenCode, Claude Code, Cursor, Trae)
- **THEN** the user can successfully connect to `mcp_server.py` and import the skills under `skills/`.

### Requirement: Architecture Diagrams in README
The repository `README.md` SHALL include 4 updated Mermaid diagrams representing (1) System Architecture & Interface Topology, (2) Multi-Stage Application Lifecycle & Permissions, (3) Layered Retrieval Protocol & Authenticity Verification Gate, and (4) Human-in-the-Loop Memory Flywheel, while removing obsolete PNG image references.

#### Scenario: Reading repository README
- **WHEN** a user opens `README.md` in GitHub or a Markdown viewer
- **THEN** the system SHALL display the 4 Mermaid diagrams inline and SHALL NOT reference deleted PNG image files