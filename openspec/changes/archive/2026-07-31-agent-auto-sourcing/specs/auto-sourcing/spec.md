## Purpose

Provides automated company sourcing, pending application creation, and MCP tools for AI Agents while maintaining human control.

## ADDED Requirements

### Requirement: Automated Company Creation with Deduplication
The API SHALL allow AI Agents to batch insert or upsert company records. If a company with the same name already exists, the system SHALL update existing fields or reuse the existing company record without creating duplicates.

#### Scenario: Batch creating new companies
- **WHEN** an AI Agent sends a POST request to create multiple companies
- **THEN** the system creates new company records for unique names and returns their IDs

#### Scenario: Deduplicating existing companies
- **WHEN** an AI Agent submits a company name that already exists in the system
- **THEN** the system reuses the existing company record ID instead of creating a duplicate

### Requirement: Automated Application Creation in Pending Status
The API SHALL allow AI Agents to create new job application records with default status "pending", enabling human candidates to review and execute actual applications manually.

#### Scenario: Creating a pending application
- **WHEN** an AI Agent calls the application creation endpoint with company ID, position, and optional URL
- **THEN** the system creates an application record with status "pending" and records trace metadata

### Requirement: MCP Server Sourcing Tools
The MCP server SHALL provide `create_company` and `create_application` tools enabling external AI agents to trigger automated company and application creation over the Model Context Protocol.

#### Scenario: Agent invokes create_company MCP tool
- **WHEN** an AI Agent invokes the `create_company` MCP tool with valid parameters
- **THEN** the MCP server executes the company creation logic and returns structured JSON response

#### Scenario: Agent invokes create_application MCP tool
- **WHEN** an AI Agent invokes the `create_application` MCP tool with company ID and job position
- **THEN** the MCP server creates a pending application and returns the created record details
