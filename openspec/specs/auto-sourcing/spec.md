## Purpose

Provides automated company sourcing, pending application creation, and MCP tools for AI Agents while maintaining human control.

## Requirements

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
- **THEN** the system creates a pending application and returns the created record details

### Requirement: Agent Must Use Layered Retrieval Protocol
The Agent SHALL follow the layered retrieval protocol for all company and job sourcing, including tool chain priority, platform routing, and authenticity verification.

#### Scenario: Agent sourcing uses protocol
- **WHEN** an AI Agent performs automated company sourcing
- **THEN** the Agent SHALL follow the layered retrieval protocol defined in the `layered-retrieval-protocol` specification
- **THEN** the Agent SHALL record the tool chain, verification status, and source URLs in the trace log

### Requirement: Source URL Required for Application Creation
The Agent SHALL provide a valid `source_url` when creating an application, and the system SHALL reject applications without a verifiable source URL.

#### Scenario: Application rejected without source URL
- **WHEN** an AI Agent calls `create_application` without a `source_url` or with an empty `source_url`
- **THEN** the system SHALL return an error and refuse to create the application record

### Requirement: Agent Must Not Fabricate Data
The Agent SHALL NOT create company or application records without real web-sourced data, and SHALL report failures to the user.

#### Scenario: Agent unable to find real data
- **WHEN** an AI Agent cannot find a real company or job matching the user's request after exhausting all retrieval layers
- **THEN** the Agent SHALL NOT create any records
- **THEN** the Agent SHALL report the failure to the user with details on what was searched and what was found