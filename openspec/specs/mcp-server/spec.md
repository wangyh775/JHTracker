# mcp-server Spec

## Purpose

Exposes Model Context Protocol (MCP) tools and resources to enable AI agents to query, create, and update JHTracker career memory data.

## Requirements

### Requirement: MCP server exposes resources for career context
The MCP server MUST expose readable resources for candidate profile and application data allowing AI models to inspect career context.

#### Scenario: Agent reads candidate profile resource
- **WHEN** an AI agent requests reading resource URI `jhtracker://profile`
- **THEN** the MCP server MUST return the formatted candidate profile text and skills metadata

### Requirement: MCP server provides tools for database operations
The MCP server MUST provide executable tools for searching companies, adding position applications, and updating evaluation scores.

#### Scenario: Agent invokes company search tool
- **WHEN** an AI agent calls tool `search_companies` with query argument `"AI"`
- **THEN** the MCP server MUST query the SQLite database and return matching company records
