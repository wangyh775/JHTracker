## ADDED Requirements

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