## Purpose

Lets users toggle between dark and light visual themes, with their preference persisted in localStorage.

## ADDED Requirements

### Requirement: Theme toggle button
The system SHALL provide a theme toggle button in the sidebar that switches between dark and light mode.

#### Scenario: Toggling theme
- **WHEN** user clicks the theme toggle button
- **THEN** the system SHALL switch between dark and light themes and persist the choice in localStorage

## MODIFIED Requirements

### Requirement: Modern Zinc Dark Theme
The system SHALL render all UI pages using a Zinc design theme, supporting both dark mode (#09090b canvas, #18181b cards, #27272a borders) and light mode (#ffffff canvas, #f4f4f5 cards, #e4e4e7 borders) with CSS variables under `data-bs-theme` selectors.

#### Scenario: Visual theme rendering in dark mode
- **WHEN** any page is loaded with `data-bs-theme="dark"`
- **THEN** the system SHALL apply the Zinc dark theme variables

#### Scenario: Visual theme rendering in light mode
- **WHEN** any page is loaded with `data-bs-theme="light"`
- **THEN** the system SHALL apply the Zinc light theme variables