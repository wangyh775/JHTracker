## Purpose

Provides a dedicated "To-Apply" staging page for applications that have been approved by human users from Decision Inbox, allowing candidate resume binding and single-click progression to applied status.

## ADDED Requirements

### Requirement: Independent To-Apply View
The system SHALL provide a dedicated `/to-apply` view listing applications in `待投递` status.

#### Scenario: Navigating to to-apply page
- **WHEN** user opens `/to-apply`
- **THEN** the system SHALL render all non-archived applications with `status = '待投递'`, displaying company details, position, channel, AI score, and assigned resume version

### Requirement: Converting To-Apply to Applied Status
The system SHALL allow users to transition a `待投递` application to `已投递` status upon completing the job application.

#### Scenario: User submits application
- **WHEN** user marks an application in `/to-apply` as applied
- **THEN** the system SHALL update the application status to `已投递` and transfer the record to `/applications`