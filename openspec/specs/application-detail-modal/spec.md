# application-detail-modal Specification

## Purpose

Lets users view full application details including company info, AI score, resume version, feedback, and interview records in a modal without leaving the application list page.

## Requirements

### Requirement: Application Detail Modal
The system SHALL open a Bootstrap modal when clicking the company name on an application card, displaying the full application detail.

#### Scenario: Opening application detail modal
- **WHEN** user clicks a company name on an application card
- **THEN** the system SHALL open a Bootstrap modal containing: company name (with link to company detail page), position, status badge, channel, salary, deadline, JD link, AI score with agent reason, resume version name, feedback text, and the interview feedback form

### Requirement: Interview Feedback Moved to Modal
The interview feedback form SHALL be rendered inside the application detail modal, not inline in the card.

#### Scenario: Viewing interview feedback in modal
- **WHEN** user opens the application detail modal for an application with interview records
- **THEN** the modal SHALL display existing feedback entries and the add-feedback form, which were previously shown inline below the card