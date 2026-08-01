## 1. Database Schema & Migration

- [x] 1.1 Add `DecisionFeedback` model to `models.py` with fields (`id`, `application_id`, `action`, `reason_category`, `raw_feedback`, `created_at`).
- [x] 1.2 Generate and execute Flask-Migrate script to create `decision_feedbacks` table.

## 2. FastMCP & Evaluation Loop Updates

- [x] 2.1 Update `create_application` tool in `mcp_server.py` to default application status to `Pending Approval`.
- [x] 2.2 Update `evaluate_jd` tool in `mcp_server.py` to fetch recent `DecisionFeedback` records and incorporate historical rejection reasons into risk scoring.

## 3. Decision Inbox REST APIs

- [x] 3.1 Implement GET `/api/agent/decisions/pending` in `routes/agent_api.py` returning staged proposals with Evaluation details.
- [x] 3.2 Implement POST `/api/agent/decisions/<application_id>` in `routes/agent_api.py` handling `approve`, `reject`, and `edit` actions.
- [x] 3.3 Update GET `/api/agent/tasks` to include `pending_approvals_count`.

## 4. UI Dashboard & Decision Cards

- [x] 4.1 Add "Decision Inbox" section with interactive recommendation cards (`Approve`, `Reject with Reason`, `Edit Draft`) to `templates/dashboard.html`.
- [x] 4.2 Add JS handlers for submitting decision actions and updating the Agent Task Center badge dynamically.

## 5. Verification & Tests

- [x] 5.1 Add unit tests in `tests/test_agent_api.py` for GET `/api/agent/decisions/pending` and POST `/api/agent/decisions/<application_id>`.
- [x] 5.2 Add unit tests in `tests/test_models.py` for `DecisionFeedback` model relationships.
- [x] 5.3 Run `pytest` to ensure all tests pass.
