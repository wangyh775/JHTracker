# rich-opportunity-cards Specification

## Purpose

Provides rich card representations for companies and applications that display skill breakdown badges (ROS ✓, C++ ✓, Outsourcing ✗) and match highlights.

## Requirements

### Requirement: Skill Breakdown Badges on Cards
The system SHALL display matched skill highlights and negative risk warnings as discrete badges on company and application cards.

#### Scenario: Card renders matching analysis
- **WHEN** displaying an application or company recommendation card
- **THEN** matched positive keywords SHALL show as green badges with checkmarks (✓) and risks SHALL show as amber/red warning badges (✗)