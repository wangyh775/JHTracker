## Purpose

Allows AI Host Agents to evaluate a Job Description text against candidate profile and negative constraint rules via an MCP tool.

## ADDED Requirements

### Requirement: Evaluate Job Description MCP Tool
The FastMCP server SHALL provide an `evaluate_jd` tool that compares a given Job Description string against `data/profile.md` and user `memories` negative rules.

#### Scenario: MCP Host Agent calls evaluate_jd
- **WHEN** an MCP client calls `evaluate_jd` with a `jd_text` parameter
- **THEN** the system SHALL calculate a matching score (0-100), extract matching highlights and risks, record an `AgentTask` trace event, and return the structured JSON evaluation result.
