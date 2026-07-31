## MODIFIED Requirements

### Requirement: Feedback Context Ingestion
The system SHALL query historical `DecisionFeedback` records AND `Memory` rules of both polarities (positive `prefer_*` categories and negative `exclude_*` / `salary_too_low` / `general` categories) during JD evaluation, adjusting scoring bidirectionally—rewarding matches to approved preferences and penalizing matches to rejected patterns.

#### Scenario: Ingest negative feedback during JD evaluation
- **WHEN** evaluating a Job Description text that matches past negative memory rules or rejection feedback (e.g. pure web software, outsourcing)
- **THEN** the evaluation SHALL penalize the score and output explicit risk notes referencing past human rejection feedback.

#### Scenario: Ingest positive preferences during JD evaluation
- **WHEN** evaluating a Job Description text that matches positive memory rules (e.g. `prefer_tech=ROS`, `prefer_domain=robotics`)
- **THEN** the evaluation SHALL increase the score and output highlights referencing past human approval preferences.

## ADDED Requirements

### Requirement: Bidirectional Decision Memory
The system SHALL persist structured `Memory` rules for both approval and rejection decisions. Approval decisions SHALL produce positive rules (categories prefixed `prefer_`); rejection decisions SHALL produce negative rules (categories `exclude_tech` / `exclude_company` / `salary_too_low` / `general`). The `rule_value` field SHALL store a structured value (a keyword, company name, or salary bound), NOT free-form feedback text; free-form feedback SHALL be stored in `raw_feedback`.

#### Scenario: Approval writes positive memory
- **WHEN** a human approves a job recommendation proposal for a robotics position requiring ROS
- **THEN** the system SHALL create a `Memory` record with a `prefer_*` category and a structured `rule_value` (e.g. "ROS", "robotics"), distinct from any free-form note stored in `raw_feedback`.

#### Scenario: Rejection writes structured negative memory
- **WHEN** a human rejects a proposal with feedback "外包不考虑"
- **THEN** the system SHALL store a structured `rule_value` (e.g. "外包") in the negative memory, and the full feedback text in `raw_feedback`, so substring matching against future JDs remains effective.

#### Scenario: Missing structured value defers to batch induction
- **WHEN** a human rejects a proposal with free-form feedback but no structured `rule_value` provided
- **THEN** the system SHALL persist `raw_feedback` only and leave `rule_value` empty, to be populated later by the batch induction script; real-time negative matching SHALL skip records with empty `rule_value`.

### Requirement: Positive Rule Batch Induction
The system SHALL provide an offline script that analyzes historically approved applications and uses an LLM to induce structured positive preference rules, persisting them to `Memory` with `prefer_*` categories. The script SHALL batch multiple applications per LLM call to conserve tokens, skip induction when no new approvals exist since the last run, and avoid writing duplicate `(category, rule_value)` pairs.

#### Scenario: Batch induce positive rules from approvals
- **WHEN** the induction script runs against 30 historically approved applications
- **THEN** the system SHALL batch them into LLM calls (e.g. 15 per call), extract structured `prefer_*` rules, and persist them to `Memory` without duplicate `(category, rule_value)` entries.

#### Scenario: Skip when no new approvals
- **WHEN** the induction script runs but no new approvals exist since the last induction fingerprint
- **THEN** the system SHALL skip LLM calls and exit without writing new rules.

#### Scenario: Degrade gracefully without API key
- **WHEN** the induction script runs but no LLM API key is configured
- **THEN** the system SHALL skip LLM induction, log a warning, and exit without failing.

### Requirement: Manual Memory Rule Correction
The system SHALL expose MCP tools allowing an Agent or user to add and delete `Memory` rules of either polarity. Adding a rule SHALL accept a polarity (positive / negative), a category, and a structured `rule_value`. Deletion SHALL require explicit confirmation (`confirm=True`).

#### Scenario: Agent adds a positive rule
- **WHEN** an MCP client calls the memory rule add tool with polarity `positive`, category `prefer_tech`, and `rule_value` "C++"
- **THEN** the system SHALL persist a `Memory` record with the `prefer_tech` category.

#### Scenario: Delete requires confirmation
- **WHEN** an MCP client calls the memory rule delete tool without `confirm=True`
- **THEN** the system SHALL reject the deletion and return an error prompting for confirmation.
