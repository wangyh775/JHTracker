## Purpose

Upgrades the company detail page into a rich 360° profile with AI score highlights, skill breakdown badges, and linked resume display, while improving the Agent Task Center card layout to eliminate button alignment issues.

## ADDED Requirements

### Requirement: Company Detail 360° Profile
The company detail page SHALL display AI score prominence, match analysis badges, and rich metadata layout.

#### Scenario: Displaying company detail
- **WHEN** user opens a company detail page
- **THEN** the page SHALL show the AI score as a prominent badge at the top, skill match highlights (ROS ✓) and risk warnings (外包 ✗) as visual tags, and the company metadata in a well-structured card

### Requirement: Agent Task Card Dual-Row Layout
The Agent Task Center feed SHALL render each task as a two-row compact card with proper button alignment.

#### Scenario: Rendering task cards
- **WHEN** the Agent Task Center feed is rendered in the Dashboard sidebar
- **THEN** each task card SHALL display the agent name and event count in the first row, and Task ID with an aligned Trace Log link button in the second row