## Purpose

Provides additional MCP resource endpoints that allow AI agents to directly read dashboard statistics and memory rules without invoking executable tools, reducing unnecessary tool calls.

## Requirements

### Requirement: Statistics Resource Endpoint
The MCP server SHALL expose a `jhtracker://statistics` resource returning dashboard-level aggregate statistics as JSON.

#### Scenario: Agent reads statistics resource
- **WHEN** an AI agent requests reading resource URI `jhtracker://statistics`
- **THEN** the MCP server SHALL return JSON containing total companies, pending approvals, to-apply count, applied count, interview count, offer count, and archived count

### Requirement: Memories Resource Endpoint
The MCP server SHALL expose a `jhtracker://memories` resource returning all positive and negative memory rules as JSON.

#### Scenario: Agent reads memories resource
- **WHEN** an AI agent requests reading resource URI `jhtracker://memories`
- **THEN** the MCP server SHALL return JSON containing all memory rules separated into `positive_rules` and `negative_rules` arrays, each with `category`, `rule_value`, and `raw_feedback` fields
