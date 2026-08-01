## ADDED Requirements

### Requirement: Pending Approvals Indicator in Agent Task Center
The Agent Task Center SHALL highlight the total number of pending job application proposals waiting for human approval.

#### Scenario: Display pending decision badge
- **WHEN** there are job applications in `Pending Approval` status
- **THEN** the Agent Task Center GET `/api/agent/tasks` response SHALL include a `pending_approvals_count` field.
