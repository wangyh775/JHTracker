# ai-workspace-navigation Specification

## Purpose

Reorganizes sidebar navigation into 5 workflow domains and provides an AI Daily Briefing on the Dashboard to highlight actionable insights.

## Requirements

### Requirement: 5 Workflow Domain Navigation
The system SHALL group sidebar navigation items into Workspace (工作台), Opportunities (机会库), Applications (投递跟踪), Agent Center (智能体中心), and Knowledge Base (知识库).

#### Scenario: User navigates sidebar
- **WHEN** user views the navigation sidebar
- **THEN** the items SHALL be organized under the 5 workflow domain headers

### Requirement: AI Daily Briefing Card
The system SHALL display an AI Daily Briefing card on the Dashboard highlighting stale applications needing follow-up and pending approval proposals.

#### Scenario: Dashboard briefing display
- **WHEN** user loads the Dashboard
- **THEN** the briefing section SHALL display high-priority actionable recommendations generated from application states