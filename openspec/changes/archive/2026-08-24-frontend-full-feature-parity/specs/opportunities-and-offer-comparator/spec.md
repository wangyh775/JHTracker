## Purpose

Provides a comprehensive enterprise directory with S/A/B/C tier classification and a multi-factor Offer comparison decision matrix.

## ADDED Requirements

### Requirement: Structured Enterprise and Job Opportunities Directory
The system SHALL display all target companies with tier ratings, industry, city, careers portal URL, and associated job openings with instant client-side filtering.

#### Scenario: Filtering companies by tier and city
- **WHEN** user selects Tier 'S' and City '苏州'
- **THEN** system filters the opportunity list instantly to show only matching enterprise cards

### Requirement: Multi-Offer Comparison Matrix
The system SHALL provide a side-by-side comparison table evaluating total compensation, base salary, 12% provident fund contributions, city living cost, and travel requirements.

#### Scenario: Comparing multiple offers
- **WHEN** user selects two or more job offers to compare
- **THEN** system calculates annual net take-home and housing fund benefits and presents a structured comparison breakdown
