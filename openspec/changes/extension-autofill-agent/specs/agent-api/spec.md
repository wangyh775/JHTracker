## ADDED Requirements

### Requirement: Application Autofill Payload Endpoint
The backend MUST provide an HTTP JSON endpoint returning structured candidate data, bound resume file path, and prefilled field values tailored for browser extension autofilling.

#### Scenario: Extension requests autofill payload by application id
- **WHEN** the extension sends a GET request to `/api/agent/applications/<id>/autofill-payload`
- **THEN** the system MUST return candidate profile fields, track classification, bound resume file path, and open question answers in JSON format

#### Scenario: Extension queries application by portal URL
- **WHEN** the extension sends a POST request to `/api/agent/applications/match-by-url` with current webpage URL
- **THEN** the system MUST return the matching application record ID and prefill payload if found

### Requirement: Post-Submission Status Synchronization
The backend MUST provide an HTTP JSON endpoint allowing the extension to record successful manual submission and update application tracking status.

#### Scenario: Extension synchronizes submitted status
- **WHEN** the extension sends a POST request to `/api/agent/applications/<id>/sync-submitted`
- **THEN** the system MUST update the application status to "已投递", record the current timestamp as `apply_date`, and append any modified open question answers into AnswerBank memories
