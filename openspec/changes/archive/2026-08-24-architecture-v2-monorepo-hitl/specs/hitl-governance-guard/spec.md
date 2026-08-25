## Purpose

Provides a multi-tier Human-In-The-Loop (HITL) governance policy engine ensuring candidate full authority over sourcing proposals, zero unauthorized submissions, and immutable post-application protection.

## ADDED Requirements

### Requirement: Sourcing Proposal Approval Gating
The system SHALL isolate newly discovered jobs in a `Pending Approval` (待审核) queue until explicit human authorization moves them into the active recruitment pipeline.

#### Scenario: Agent sources new job
- **WHEN** autonomous cron or sourcing agent discovers a high-scoring recruitment opportunity
- **THEN** system creates the record in `Pending Approval` state and suppresses automatic application actions until approved by the candidate

#### Scenario: Candidate approves proposal
- **WHEN** candidate clicks "加入投递计划" (Approve) in Web UI or Feishu card
- **THEN** system transitions the job to `待投递` (Ready to Apply) and assigns target resume version

### Requirement: Hard Zero-Submit Physical Isolation
The system SHALL strictly restrict automation to form pre-filling and document attachment, raising a security violation error if any component attempts automated submission.

#### Scenario: Preventing accidental form submission
- **WHEN** autofill execution completes all fields on a third-party job portal
- **THEN** system explicitly terminates the CDP control session, leaving the final submission action solely to the physical candidate

### Requirement: Post-Application Mutation Write-Protection
The system SHALL enforce immutable write-protection on job records that have progressed to or past the `已投递` stage, preventing autonomous agents from altering or deleting them.

#### Scenario: Agent attempts mutation on active application
- **WHEN** background sourcing job attempts to overwrite or archive a job in `已投递`, `笔试`, `一面`, `二面`, or `Offer` status
- **THEN** system rejects the modification, records an audit log trace, and preserves the human-managed state
