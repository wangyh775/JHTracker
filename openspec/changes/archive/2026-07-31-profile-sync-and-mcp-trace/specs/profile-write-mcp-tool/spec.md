## Purpose

Provide FastMCP tool `update_candidate_profile` to enable AI agents to write updated candidate career preferences directly into `data/profile.md`.

## ADDED Requirements

### Requirement: MCP Candidate Profile Update Tool
The FastMCP server SHALL expose a tool named `update_candidate_profile` that writes provided Markdown content to `data/profile.md`.

#### Scenario: Agent updates candidate profile via MCP
- **WHEN** an AI agent calls `update_candidate_profile(content="## Education\n- BS CS")`
- **THEN** `data/profile.md` is updated with the provided content and a success JSON status is returned.
