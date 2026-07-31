## Purpose

Provides a human-in-the-loop review inbox, rejection memory capture, and agent preference retrieval endpoints to ensure human oversight and continuous agent alignment.

## Requirements

### Requirement: Human-in-the-loop Pending Application Review
The system SHALL provide a dedicated review workflow for pending applications, allowing users to approve proposals into the active application pipeline or reject them with feedback.

#### Scenario: Approving a pending application
- **WHEN** a user submits an approval request for a pending application via the review API
- **THEN** the system updates the application status from "pending" to "to_apply"

#### Scenario: Rejecting a pending application with feedback
- **WHEN** a user submits a rejection request for a pending application with optional category and raw feedback text
- **THEN** the system updates the application status to "rejected" and creates a memory record in the memories table

### Requirement: Agent Proposal Rationale & Match Score Metadata
The application creation endpoints and MCP tools SHALL support optional match scores, agent recommendation reasons, task IDs, and source URLs.

#### Scenario: Creating application with recommendation metadata
- **WHEN** an AI Agent submits an application proposal with match score, agent reason, task ID, and source URL
- **THEN** the system stores these metadata fields alongside the application record for human review and traceability

### Requirement: Candidate Preference & Memory Retrieval
The system SHALL expose an endpoint and MCP tool that return candidate profile preferences, negative constraints, and recent rejection feedback.

#### Scenario: Agent requests user preferences
- **WHEN** an AI Agent calls `GET /api/v1/profile/preferences` or the `get_user_preferences` MCP tool
- **THEN** the system returns structured negative constraint rules (such as excluded tech or company types) and raw human rejection notes
