# zinc-design-system Specification

## Purpose

Establishes a unified Zinc design system supporting both dark and light themes with modern CSS variables, refined typography, crisp borders, and status badges for the entire user interface.

## Requirements

### Requirement: Modern Zinc Dark Theme
The system SHALL render all UI pages using a Zinc design theme, supporting both dark mode (#09090b canvas, #18181b cards, #27272a borders) and light mode (#ffffff canvas, #f4f4f5 cards, #e4e4e7 borders) with CSS variables under `data-bs-theme` selectors.

#### Scenario: Visual theme rendering in dark mode
- **WHEN** any page is loaded with `data-bs-theme="dark"`
- **THEN** the system SHALL apply the Zinc dark theme variables

#### Scenario: Visual theme rendering in light mode
- **WHEN** any page is loaded with `data-bs-theme="light"`
- **THEN** the system SHALL apply the Zinc light theme variables

### Requirement: Priority and Status Badges
The system SHALL provide status badges and priority tags styled with distinct color tokens (S/A/B/C and Applied/Interview/Offer/Rejected).

#### Scenario: Display priority badges
- **WHEN** a company or application card displays a priority rating or status
- **THEN** the system SHALL style the badge with high-contrast, rounded pill tag design
