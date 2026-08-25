## Purpose

Enforces a strict Human-In-The-Loop (Zero-Submit) verification checkpoint allowing candidates to inspect, edit, and confirm prefilled form fields before manually completing final web submissions.

## ADDED Requirements

### Requirement: Prefilled Form Field Audit Interface
The system SHALL present a dedicated review station displaying all prefilled form fields grouped by status (filled vs. awaiting human entry) with confidence scores and source attributions.

#### Scenario: Inspecting prefilled submission details
- **WHEN** user navigates to `/submissions/:id`
- **THEN** the interface renders a structured table of every captured DOM field, proposed value, and completion flag

### Requirement: Zero-Submit Finalization Barrier
The automated agent and CDP workflows SHALL be strictly prohibited from triggering final form submission buttons, requiring explicit candidate verification and manual browser clicks.

#### Scenario: Completing application submission
- **WHEN** user validates all prefilled fields in the review interface
- **THEN** user clicks "Open Real Recruitment Portal" to review in browser, executes manual submit, and clicks "Mark as Submitted" to transition the application status to `已投递`
