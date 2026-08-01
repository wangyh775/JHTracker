## Purpose

Enables the AI scoring engine (`ai_scorer.py`) to dynamically read human rejection memories from the database and perform zero-token prefiltering against new companies.

## Requirements

### Requirement: Dynamic Negative Rule Ingestion
The scoring engine SHALL query the `memories` table for negative user preferences (category `exclude_*`, `salary_too_low`, `general`) and merge them into Stage 1 keyword prefiltering.

#### Scenario: Prefiltering company using dynamic negative rules
- **WHEN** `ai_scorer.py` evaluates a company whose job description, position, or match reason contains a word or phrase present in the user's negative rules
- **THEN** the system SHALL reject the company at Stage 1 with score 0 and reason "触发拒绝记忆/排除词: <rule>", skipping LLM evaluation

#### Scenario: Running prefiltering when no negative rules exist
- **WHEN** `ai_scorer.py` runs and the `memories` table contains no negative rules
- **THEN** the system SHALL fallback to using the built-in static `DEAL_BREAKERS` keyword list
