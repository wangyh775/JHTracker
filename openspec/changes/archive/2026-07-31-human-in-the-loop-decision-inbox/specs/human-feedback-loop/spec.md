## Purpose

Captures explicit human approval/rejection feedback and incorporates historical decision memory into future AI evaluations to refine agent scoring alignment over time.

## ADDED Requirements

### Requirement: Record Decision Feedback
The system SHALL store structured `DecisionFeedback` records whenever a human acts on a pending decision proposal.

#### Scenario: Store rejection feedback
- **WHEN** a human rejects a job recommendation proposal with feedback text "Role is too software-focused; prefer robotics/embedded"
- **THEN** the system SHALL create a `DecisionFeedback` record linked to the application with action `reject` and raw feedback text.

### Requirement: Feedback Context Ingestion
The system SHALL query historical `DecisionFeedback` records during JD evaluation to adjust scoring parameters and highlight potential user-disliked patterns.

#### Scenario: Ingest feedback during JD evaluation
- **WHEN** evaluating a Job Description text that matches past negative feedback rules (e.g. pure web software)
- **THEN** the evaluation SHALL penalize the score and output explicit risk notes referencing past human rejection feedback.
