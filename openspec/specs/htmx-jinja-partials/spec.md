# htmx-jinja-partials Specification

## Purpose

Replaces client-side JavaScript innerHTML string assembly with server-rendered Jinja2 partial templates delivered over HTMX for dynamic updates.

## Requirements

### Requirement: Server-Side Partial Rendering for Decision Inbox
The system SHALL expose HTML endpoints that return rendered Jinja2 partials for the Decision Inbox.

#### Scenario: HTMX fetches pending decisions
- **WHEN** HTMX issues an HTTP GET request to `/api/agent/decisions/pending-html`
- **THEN** the system SHALL return a rendered `_decision_inbox.html` partial fragment containing active proposals

### Requirement: Server-Side Partial Rendering for Agent Task Feed
The system SHALL expose HTML endpoints that return rendered Jinja2 partials for the Agent Task Center feed.

#### Scenario: HTMX fetches agent tasks feed
- **WHEN** HTMX issues an HTTP GET request to `/api/agent/tasks-html`
- **THEN** the system SHALL return a rendered `_agent_tasks.html` partial fragment containing task status items