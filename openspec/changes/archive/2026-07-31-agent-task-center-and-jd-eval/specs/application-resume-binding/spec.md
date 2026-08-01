## Purpose

Binds job applications to specific resume versions to enable resume effectiveness tracking across different applications.

## ADDED Requirements

### Requirement: Application Foreign Key to Resume Version
The `applications` table SHALL include an optional `resume_id` foreign key referencing `resumes.id`.

#### Scenario: Application created with explicit resume version
- **WHEN** a job application is created with a valid `resume_id` via HTTP request or MCP tool `create_application`
- **THEN** the system SHALL store `resume_id` on the application record and allow retrieving the associated Resume object.
