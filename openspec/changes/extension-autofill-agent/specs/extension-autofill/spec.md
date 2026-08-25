## Purpose

Enables browser-assisted automated job application prefilling directly inside external enterprise recruitment portals using local agent intelligence, Shadow DOM floating controls, anti-bot typing emulation, and explicit file attachment.

## ADDED Requirements

### Requirement: Draggable Shadow DOM Floating Orb and Review Widget
The browser extension MUST inject an isolated Shadow DOM floating UI widget into target job application pages that can be dragged, snaps to viewport edges, persists its position, and expands into a review modal without CSS pollution from the host webpage.

#### Scenario: Floating orb renders and remembers position
- **WHEN** user navigates to an enterprise recruitment portal page
- **THEN** the extension MUST mount a Shadow DOM floating orb displaying readiness status and resume track match score
- **AND** the orb position MUST persist across page navigation and step changes via localStorage

#### Scenario: Expanding review modal
- **WHEN** user clicks on the floating orb
- **THEN** the extension MUST expand the review modal displaying candidate summary, bound resume PDF path, track selector, and field prefill checklist

### Requirement: Multi-Step Wizard Perception and Progressive Prefill
The extension MUST observe DOM mutations and wizard step changes, dynamically detecting form fields and triggering automated prefilling per step.

#### Scenario: Step change detection
- **WHEN** user clicks a native "Next Step" or "Save & Continue" button on a recruitment portal
- **THEN** the extension MUST detect new step containers and unpopulated input elements
- **AND** automatically invoke the prefill engine for the newly rendered step without overwriting previously validated fields

### Requirement: Anti-Cheat Human-like Synthetic Typing Emulation
The extension MUST simulate human keystrokes when injecting text into text inputs and textareas to satisfy SPA reactive state bindings and avoid anti-automation bot flags.

#### Scenario: Keystroke injection with jitter
- **WHEN** the extension prefills text into a text input or textarea
- **THEN** it MUST dispatch native keydown, beforeinput, input, and keyup events with variable inter-keystroke intervals (35 to 60 characters per second) and punctuation pauses
- **AND** update the underlying framework component state (React/Vue/Angular)

#### Scenario: Human override during typing
- **WHEN** user focuses or clicks on an input field while typing simulation is in progress
- **THEN** the extension MUST immediately halt automatic typing on that field and hand over focus to the user

### Requirement: 4-Track Dynamic Switching
The extension review modal MUST provide a track selection control enabling the user to switch between the 4 engineering tracks, updating bound resume paths and re-generating tailored open-question answers.

#### Scenario: Switching track updates payload
- **WHEN** user selects a different track (e.g. Track 2 Automation & Embedded) in the floating review modal
- **THEN** the extension MUST update the local bound resume PDF path to the corresponding track resume
- **AND** refresh prefill suggestions and open question answers aligned with that track's skill profile

### Requirement: Explicit CDP Resume File Attachment
The extension MUST support on-demand local resume PDF injection into file upload elements using the Chrome Debugger protocol without requiring manual file picker navigation.

#### Scenario: User triggers resume attachment
- **WHEN** user clicks the explicit "Attach Resume File" button in the review modal
- **THEN** the extension MUST invoke Chrome Debugger `DOM.setFileInputFiles` with the verified local file path of the active track resume
- **AND** the target page file input MUST display the attached file with a success confirmation in the widget
