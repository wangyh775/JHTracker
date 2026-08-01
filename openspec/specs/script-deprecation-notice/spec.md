## Purpose

Establishes a graceful deprecation notice and execution safeguard for legacy scripts replaced by AI Agent workflows.

## Requirements

### Requirement: Execution Safeguard for Deprecated Finder Script
The legacy script `scripts/daily_new_company_finder.py` SHALL display a deprecation warning and exit immediately when executed directly.

#### Scenario: Running legacy finder script
- **WHEN** a user or process executes `python scripts/daily_new_company_finder.py`
- **THEN** the script SHALL output a deprecation banner directing users to use Agent Sourcing Skill (`job-sourcing-and-scoring`) and exit with status code 0 without modifying the database
