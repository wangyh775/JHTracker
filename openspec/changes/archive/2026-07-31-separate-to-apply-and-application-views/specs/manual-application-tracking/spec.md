## Purpose

Restricts the `/applications` page to human-controlled active application lifecycle states, excluding unapproved proposals and pre-apply staged items, while preventing AI agents from modifying applied records directly.

## ADDED Requirements

### Requirement: Filtered Applications View
The system SHALL exclude `Pending Approval`, `待审批`, and `待投递` records from the `/applications` list.

#### Scenario: Viewing active applications
- **WHEN** user loads `/applications`
- **THEN** the system SHALL display only applications with active/finalized status (`已投递`, `简历筛选`, `笔试`, `一面`, `二面`, `终面`, `Offer`, `已拒`)

### Requirement: Human-Only Write Access for Applied Records
The system SHALL reject any Agent/MCP request to modify or mutate applications that are already in active lifecycle states (`已投递` and beyond).

#### Scenario: Agent attempts to mutate applied record
- **WHEN** an Agent tool or API attempts to update or delete an application with status other than `Pending Approval`
- **THEN** the system SHALL return an error indicating that active application records are reserved for human edit only