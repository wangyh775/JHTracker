## Purpose

Provides a unified, extensible browser automation adapter framework interfacing with diverse campus recruitment platforms (Beisen/北森, Moka, and generic DOM forms) via Chrome CDP, enforcing a strict Zero-Submit safety boundary.

## ADDED Requirements

### Requirement: Multi-System Platform Detection and Adapter Dispatch
The system SHALL automatically identify the target recruitment platform (Beisen, Moka, or Generic) based on active tab URL and DOM heuristics, and dispatch to the corresponding specialized adapter.

#### Scenario: Detecting Beisen system
- **WHEN** active Chrome tab navigates to a URL containing `zhiye.com` or `recruit.inovance.com`
- **THEN** system dispatches to BeisenAutofillAdapter and loads platform-specific selectors

#### Scenario: Fallback to generic form adapter
- **WHEN** active Chrome tab hosts an unrecognized custom enterprise recruitment portal
- **THEN** system falls back to GenericFormAdapter using heuristic label-input proximity matching

### Requirement: Safe Field Extraction and Autofill
The system SHALL extract profile data from `applicant_profile.json` and fill matched empty inputs without overwriting existing user modifications.

#### Scenario: Filling empty candidate fields
- **WHEN** adapter discovers visible input elements matching name, phone, email, school, and major
- **THEN** system populates the corresponding values, triggers input/change events for reactive frameworks, and reports filled count

#### Scenario: Preserving pre-filled user inputs
- **WHEN** an input field already contains non-empty text
- **THEN** adapter skips that field without altering its content

### Requirement: Resume PDF Drag-and-Drop Injection
The system SHALL automatically upload the targeted 3-track resume PDF to the recruitment system's attachment/parser zone.

#### Scenario: Injecting resume PDF for auto-parsing
- **WHEN** autofill is triggered on a page supporting file uploads
- **THEN** system sets the target resume PDF file into the file input element and waits for parse confirmation

### Requirement: Strict Zero-Submit Safety Enforcement
The system SHALL strictly prohibit any automated invocation of final submission or application confirmation controls.

#### Scenario: Completion of autofill cycle
- **WHEN** all form fields and resume files are filled and uploaded
- **THEN** system halts execution, leaves the browser on the review step, and outputs a notification reminding the human candidate to review and submit manually
