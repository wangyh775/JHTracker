## Purpose

Provides a Human-In-The-Loop (HITL) approval inbox allowing candidates to review, approve, or dismiss recruitment opportunities discovered by autonomous agents.

## Requirements

### Requirement: Sourcing Proposal Triage Queue
The system SHALL present newly discovered jobs in an isolated triage queue with match score justification, target track, and quick actions.

#### Scenario: Approving an opportunity
- **WHEN** user clicks "加入投递计划" on a pending proposal
- **THEN** system transitions the job to `待投递` status and assigns the default resume track

#### Scenario: Dismissing an opportunity
- **WHEN** user clicks "忽略" on a proposal
- **THEN** system archives the proposal to suppressed status and removes it from the inbox
