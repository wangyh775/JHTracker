---
name: "job-sourcing-and-scoring"
description: "Fetches company/job info from the web, evaluates matching scores based on candidate profile and negative constraint rules (memories), and writes scores or recommendations back to JHTracker via MCP or REST API. Alias: company-finder, career-tracker-scorer."
allowed-tools:
  - JHTracker:get_user_preferences
  - JHTracker:search_companies
  - JHTracker:create_company
  - JHTracker:update_company_score
  - JHTracker:create_application
---

# Job Sourcing and Scoring Skill

This skill automates target company sourcing, job discovery, AI matching evaluation, and negative constraint memory filtering for JHTracker.

## Trigger Scenarios

Invoke when the user says any of:
- "帮我找XX行业的公司" / "搜索机器人公司" / "补充公司库" / "寻找符合偏好的岗位"
- "评估公司匹配度" / "给已有的公司打分" / "AI rating / score companies"
- "find companies in <industry>" / "score target companies"

## Workflow

### 1. Ingest Candidate Profile & Negative Rules
Before searching or scoring:
1. Call `JHTracker:get_user_preferences` (or read `data/profile.md` and query `memories` table).
2. Inspect `negative_rules` (e.g., excluded tech stacks, unwanted locations, prohibited industries) and `recent_rejection_notes`.
3. If candidate profile is missing, notify user to set up `data/profile.md`.

### 2. Sourcing & Deduplication
1. Search the web for target industry/role companies.
2. Check existing database using `JHTracker:search_companies(query=name)`.
3. If not existing, add the company using `JHTracker:create_company(...)`.

### 3. AI Matching Evaluation (0 - 100)
Score companies/jobs based on alignment with candidate skills, city, salary expectations, and negative rules:
- **0 - 59**: Violates negative rules or poor tech stack fit.
- **60 - 79**: Moderate match, keep in company DB.
- **80 - 100**: High match, candidate should consider applying.

Update company score using `JHTracker:update_company_score(company_id, score, reason)`.

### 4. Push High Match Jobs to HITL Queue
For jobs/companies with score ≥ 75, call `JHTracker:create_application(...)` with default status `'待投递'` and attach `match_score` and `agent_reason` to push into human-in-the-loop review funnel.
