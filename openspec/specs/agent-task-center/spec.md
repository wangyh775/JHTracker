# agent-task-center Specification

## Purpose

Provides a central task monitoring center and real-time execution event activity feed for tracking Agent execution and reasoning traces.

## Requirements

### Requirement: Agent Task List and Status Overview
The system SHALL expose REST API endpoints and a Web UI section to list and query Agent tasks with status and timestamp metadata.

#### Scenario: Query Agent tasks via API
- **WHEN** a GET request is made to `/api/agent/tasks`
- **THEN** the system SHALL return a JSON list of Agent tasks containing `task_id`, `agent_name`, `status`, and `created_at`.

### Requirement: Agent Event Trace Feed
The system SHALL store and return chronological event traces (`AgentEvent`) associated with a given Agent task ID.

#### Scenario: View event traces for a task
- **WHEN** a GET request is made to `/api/agent/tasks/<task_id>`
- **THEN** the system SHALL return the task details along with an ordered array of trace events including `event_type`, `payload_json`, and timestamps.

### Requirement: Pending Approvals Indicator in Agent Task Center
The Agent Task Center SHALL highlight the total number of pending job application proposals waiting for human approval.

#### Scenario: Display pending decision badge
- **WHEN** there are job applications in `Pending Approval` status
- **THEN** the Agent Task Center GET `/api/agent/tasks` response SHALL include a `pending_approvals_count` field.
