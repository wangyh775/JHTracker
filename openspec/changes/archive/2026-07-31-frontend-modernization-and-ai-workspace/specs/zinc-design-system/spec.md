## Purpose

Establishes a unified Zinc dark-mode design system with modern CSS variables, refined typography, crisp borders, and status badges for the entire user interface.

## ADDED Requirements

### Requirement: Modern Zinc Dark Theme
The system SHALL render all UI pages using a Zinc dark design theme (#09090b canvas, #18181b cards, #27272a 1px borders) with CSS variables.

#### Scenario: Visual theme rendering
- **WHEN** any page in the system is loaded in the browser
- **THEN** the system SHALL apply the Zinc dark theme variables with refined font hierarchies and crisp borders

### Requirement: Priority and Status Badges
The system SHALL provide status badges and priority tags styled with distinct color tokens (S/A/B/C and Applied/Interview/Offer/Rejected).

#### Scenario: Display priority badges
- **WHEN** a company or application card displays a priority rating or status
- **THEN** the system SHALL style the badge with high-contrast, rounded pill tag design