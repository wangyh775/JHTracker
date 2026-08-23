# timeline-gantt-enhancement Specification

## MODIFIED Requirements

### Requirement: Timeline Item Status and Expiry Filtering
The system SHALL provide toggle options to filter out completed (`done = true`) and expired (`end_date < today`) events from the Gantt chart and details list by default, and SHALL render date ranges without clipping past items in the current view range or breaking JS parsing due to unescaped string formatting.

#### Scenario: Filtering completed and expired timeline nodes
- **WHEN** user views the timeline page with default filter settings
- **THEN** the system SHALL render only active, unexpired events in both the Gantt chart and the details list

#### Scenario: Toggling filter switches
- **WHEN** user toggles "Include Completed" or "Include Expired" checkboxes
- **THEN** the system SHALL dynamically re-render the Gantt chart and details list to reflect the updated filter criteria

#### Scenario: Timeline view range padding and safe event delegation
- **WHEN** user views the timeline in month or quarter view or clicks on a card with multi-line descriptions
- **THEN** the Gantt chart SHALL include sufficient past/future bounds (`xmin`/`xmax`) to render events starting earlier in the month, and event handlers SHALL parse item metadata safely without JS syntax errors
