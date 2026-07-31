# jd-evaluation-mcp Specification

## Purpose

Allows AI Host Agents to evaluate a Job Description text against candidate profile and negative constraint rules via an MCP tool.

## Requirements

### Requirement: Evaluate Job Description MCP Tool
The FastMCP server SHALL provide an `evaluate_jd` tool that compares a given Job Description string against `data/profile.md`, user `Memory` rules of BOTH polarities (positive `prefer_*` and negative `exclude_*`), and historical `DecisionFeedback` records. Positive rule matches SHALL increase the score and produce highlights; negative rule matches and rejection-feedback matches SHALL decrease the score and produce risks. The tool SHALL NOT rely on a hard-coded keyword list for positive scoring.

#### Scenario: MCP Host Agent calls evaluate_jd with positive preferences
- **WHEN** an MCP client calls `evaluate_jd` with a `jd_text` that matches stored `prefer_tech` rules (e.g. "ROS", "robotics")
- **THEN** the system SHALL increase the matching score, list the matched positive rules in highlights, record an `AgentTask` trace event, and return the structured JSON evaluation result.

#### Scenario: MCP Host Agent calls evaluate_jd with negative matches
- **WHEN** an MCP client calls `evaluate_jd` with a `jd_text` that matches stored negative rules or past rejection feedback
- **THEN** the system SHALL decrease the matching score, list the matched negative patterns in risks, record an `AgentTask` trace event, and return the structured JSON evaluation result.

#### Scenario: evaluate_jd with empty memory rules
- **WHEN** an MCP client calls `evaluate_jd` and no `Memory` rules of either polarity exist
- **THEN** the system SHALL return a baseline score with no polarity-based highlights or risks, and SHALL NOT fall back to a hard-coded keyword list.
