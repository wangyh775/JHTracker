## Purpose

Provides a high-density, multi-attribute structured table workbench for managing job applications across active and archived states with batch operations and Kanban mode switching.

## ADDED Requirements

### Requirement: Active and Archived Tab Segregation
The application workbench SHALL provide distinct tab views for active applications and historical archived applications, ensuring archived records do not clutter current recruitment pipelines.

#### Scenario: Switching between active and archived views
- **WHEN** user selects the "Archived" tab
- **THEN** the system displays only applications where `is_archived` is true with visual indicator badges and dimmed card styles

#### Scenario: Archiving and recovering applications
- **WHEN** user triggers the archive action on an active application
- **THEN** the system sets `is_archived` to true, records `archived_at` timestamp, and transitions the row to the archived pool

### Requirement: Customizable Auto-Archival Rules
The system SHALL support configurable stale threshold settings (e.g., N days without status update) with instant manual execution and preview counts.

#### Scenario: Executing stale auto-archival
- **WHEN** user initiates "Run Archival Now" with threshold set to 15 days
- **THEN** the system archives all non-final applications older than 15 days and returns the total count of archived records

### Requirement: Dual Mode Table and Kanban View
The workbench SHALL offer seamless toggling between a dense structured Table View and a drag-friendly Kanban View while retaining active filter criteria.

#### Scenario: Toggling view layout
- **WHEN** user clicks the "Kanban View" toggle button
- **THEN** the application list renders grouped by status columns with drag-and-drop status update capabilities
