# agent-api Spec

## Purpose

Provides standardized RESTful JSON endpoints for AI agents to query, create, update, and manage job hunting data in JHTracker.

## Requirements

### Requirement: Agent can search and update company records
The system MUST provide HTTP JSON endpoints for searching companies by keyword or criteria and updating company AI scores and match reasons.

#### Scenario: Agent searches for companies
- **WHEN** an agent sends a GET request to `/api/v1/companies/search?q=robotics`
- **THEN** the system MUST return a JSON list of matching companies with id, name, city, industry, and priority

#### Scenario: Agent updates company AI match score
- **WHEN** an agent sends a POST request to `/api/v1/companies/<id>/score` with score and reason JSON payload
- **THEN** the system MUST update the company record in database and return success JSON status

### Requirement: Agent can query candidate profile
The system MUST provide an HTTP JSON endpoint for agents to fetch candidate profile background and target job preferences.

#### Scenario: Agent fetches candidate profile
- **WHEN** an agent sends a GET request to `/api/v1/profile`
- **THEN** the system MUST return candidate skills, target roles, and profile content in JSON format
