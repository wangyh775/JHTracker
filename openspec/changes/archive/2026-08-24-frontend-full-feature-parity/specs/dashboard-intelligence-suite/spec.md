## Purpose

Provides a centralized recruitment analytics dashboard integrating AI Daily Briefings, stale application follow-up alarms, deadline countdowns, and key pipeline metrics.

## ADDED Requirements

### Requirement: AI Daily Briefing Synthesis
The system SHALL aggregate high-scoring pending recommendations and identify stale applications exceeding 7 days without response.

#### Scenario: Displaying AI Briefing cards
- **WHEN** user visits the main Dashboard view
- **THEN** system renders the AI Daily Briefing panel highlighting follow-up candidates and high-match proposals (>= 80 score)

### Requirement: Urgent Deadline Countdown Banner
The system SHALL compute approaching application deadlines and render an alert banner when deadlines fall within the next 7 days.

#### Scenario: Warning of approaching deadline
- **WHEN** any active target job has a deadline <= 7 days from current date
- **THEN** system displays the company name and remaining days in an urgent alert banner at the top of the workspace
