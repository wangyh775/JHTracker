## Purpose

Reorganizes the Dashboard into a 2-column split grid layout (col-lg-8 main analytics area, col-lg-4 Agent Co-Pilot sidebar) so that Decision Inbox proposals and Agent tasks are prominently positioned in the top-right viewport.

## ADDED Requirements

### Requirement: Split Grid Layout Structure
The system SHALL layout the Dashboard using a 2-column grid where the main analytics area takes 8 columns (`col-lg-8`) and the Agent Co-Pilot panel takes 4 columns (`col-lg-4`).

#### Scenario: Displaying split grid
- **WHEN** user loads the Dashboard on a desktop screen (lg breakpoint)
- **THEN** analytics cards and charts SHALL render in the left column and Decision Inbox, Agent Task feed, and Timeline/Activity SHALL render in the right column

### Requirement: Right-Column Agent Inbox and Task Scroll Panels
The system SHALL display Decision Inbox proposals and Agent Tasks in dedicated scrollable panels within the right 4-column sidebar.

#### Scenario: Rendering scrollable panels
- **WHEN** Decision Inbox proposals or Agent Task items are rendered in the right sidebar
- **THEN** each panel SHALL have a maximum height constraint and internal scrolling for excessive items