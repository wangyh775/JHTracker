## Purpose

Provide FastMCP tool `record_agent_trace` to enable pure MCP AI agents to log tasks and execution events into `AgentTask` and `AgentEvent` tables.

## ADDED Requirements

### Requirement: MCP Agent Trace Logging Tool
The FastMCP server SHALL expose a tool named `record_agent_trace` that records or updates an `AgentTask` and appends an `AgentEvent` in the database.

#### Scenario: Agent records trace event via MCP
- **WHEN** an AI agent calls `record_agent_trace(task_id="task-123", agent_name="SourcingAgent", event_type="info", payload={"found": 5})`
- **THEN** an `AgentTask` record is created or updated and an `AgentEvent` record is stored, returning a success JSON status with `task_id` and `event_id`.
