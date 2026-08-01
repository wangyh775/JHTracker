# application-resume-binding Specification

## Purpose

Binds job applications to specific resume versions to enable resume effectiveness tracking across different applications.

## Requirements

### Requirement: Application Foreign Key to Resume Version
The `applications` table SHALL include an optional `resume_id` foreign key referencing `resumes.id`. Applications created automatically by AI Agent tools SHALL default to status `Pending Approval`.

#### Scenario: Application created with explicit resume version
- **WHEN** a job application is created with a valid `resume_id` via HTTP request or MCP tool `create_application`
- **THEN** the system SHALL store `resume_id` on the application record with initial status `Pending Approval` (unless explicitly overridden by human user) and allow retrieving the associated Resume object.
