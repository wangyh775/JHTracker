## Purpose

Consolidate fragmented Agent Skills into 4 domain-driven core skills while adding HITL review and MCP tool integration requirements.

## ADDED Requirements

### Requirement: Agent Skills Consolidation Structure
The system SHALL provide exactly 4 consolidated skill directories under `skills/`: `job-sourcing-and-scoring`, `application-tracker`, `candidate-profile-and-resume`, and `tracker-ops`.

#### Scenario: Verify skill directories
- **WHEN** an AI agent checks the `skills/` directory
- **THEN** it finds the 4 consolidated skill directories, each containing a valid `SKILL.md` file.

### Requirement: FastMCP Tool and HITL Review Support in Skills
The consolidated skills SHALL explicitly define FastMCP tool mappings and support pushing jobs to `待投递` (pending review) status for Human-in-the-Loop (HITL) approval.

#### Scenario: Agent pushes candidate application via skill
- **WHEN** an AI agent discovers a job matching candidate profile score >= 75
- **THEN** it calls the MCP tool `create_application` setting initial status to `待投递` and including match metadata (`match_score`, `agent_reason`).
