## Purpose

防止智能体在自动搜寻与岗位推送过程中，向数据库和决策收件箱中重复创建针对同一公司与同一岗位的待审批提案。

## Requirements

### Requirement: Application Proposal Deduplication in MCP and API

The MCP tool `create_application` and REST API `/api/agent/applications` SHALL check if an active application proposal (with status `Pending Approval` or `待投递`) already exists for the specified `company_id` and normalized `position`. If such a record exists, the system SHALL return the existing record details with `created: false` instead of creating a duplicate row.

#### Scenario: Agent submits a proposal for an already existing company and position
- **WHEN** the agent calls `create_application` with a `company_id` and `position` that already has a `Pending Approval` record in the database
- **THEN** the system does not create a new database row and returns the existing application object with `status: "success"` and `created: false`

#### Scenario: Agent submits a proposal for a novel position at an existing company
- **WHEN** the agent calls `create_application` with a `company_id` and a distinct `position` that has no `Pending Approval` record
- **THEN** the system inserts a new application proposal into the database and returns `status: "success"` and `created: true`

### Requirement: Skill SOP Anti-Duplication Enforcement

The `job-sourcing-and-scoring` Skill SOP SHALL instruct host agents that when `create_company` returns `created: false`, the agent MUST check existing applications for that company before calling `create_application`, and MUST skip creating a duplicate proposal if the position is already present in `Pending Approval` or `待投递` status.

#### Scenario: Agent encounters an existing company during auto-sourcing
- **WHEN** `create_company` returns `created: false` indicating the company is already present in the database
- **THEN** the agent queries existing applications for that company, detects duplicate pending proposals, and skips calling `create_application` for that job

### Requirement: Setup Guide for MCP, Skill, and Cron Integration

The documentation (`docs/getting-started.md`) SHALL provide a comprehensive setup guide detailing how to wire MCP tools, Skill SOPs, and Host Agent scheduled cron tasks together with anti-duplication prompt contracts.

#### Scenario: User or Agent configures a daily auto-sourcing scheduled task
- **WHEN** following the setup guide to create a scheduled task
- **THEN** the user or agent can configure a cron prompt that instructs the host agent to fetch existing database companies first, exclude them from search queries, and strictly avoid duplicate proposal pushes
