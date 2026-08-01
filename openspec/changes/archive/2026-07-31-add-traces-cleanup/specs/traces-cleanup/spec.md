## Purpose

Prevents unbounded growth of Agent trace data by automatically expiring old records and providing a manual purge option, keeping the database size manageable without user intervention.

## ADDED Requirements

### Requirement: Automatic trace expiration
The system SHALL automatically delete `agent_events` and orphaned `agent_tasks` records older than a configurable retention period.

#### Scenario: Expired traces are cleaned on page visit
- **WHEN** a user visits the `/traces` page
- **THEN** the system SHALL delete `agent_events` where `created_at` is older than the retention period, and delete `agent_tasks` that have no remaining events
- **AND** the cleanup SHALL run at most once per day (throttled)

#### Scenario: Recent traces are preserved
- **WHEN** a trace event was created within the retention period (default 30 days)
- **THEN** the system SHALL NOT delete it during automatic cleanup

### Requirement: Manual purge of all traces
The system SHALL expose a way for users to delete all trace records immediately.

#### Scenario: User clears all traces
- **WHEN** a user clicks "清空全部轨迹" on the `/traces` page
- **THEN** the system SHALL delete all records from `agent_events` and `agent_tasks`
- **AND** the system SHALL show a confirmation dialog before executing

### Requirement: Configurable retention period
The system SHALL allow configuring the retention period via environment variable, with a hardcoded default.

#### Scenario: Retention period is configurable
- **WHEN** the environment variable `JH_TRACES_RETENTION_DAYS` is set to `60`
- **THEN** the system SHALL retain trace records for 60 days instead of the default 30