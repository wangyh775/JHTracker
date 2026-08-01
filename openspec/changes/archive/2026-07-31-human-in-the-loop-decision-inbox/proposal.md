## Why

Reorient JHTracker from an autonomous "agent-centric auto-apply" tool into a Human-in-the-Loop (HITL) Career Intelligence System. AI Agents extend human analytical capabilities by evaluating job opportunities and preparing application proposals, while humans retain absolute control over final approval, edits, and submission decisions with explicit feedback logging.

## What Changes

- **Decision Inbox & Pending Proposals UI**: Add a dedicated "Decision Inbox" section on the dashboard to present Agent job recommendations (`Pending Approval` applications) with match reasoning, risk highlights, and explicit human action triggers (`Approve`, `Reject`, `Edit`).
- **Human Approval & Feedback Model**: Extend database models (`DecisionFeedback` / `Memory`) to capture explicit human rejection reasons and feedback metadata when approving/rejecting proposals.
- **Human Feedback Loop for Evaluation**: Update `evaluate_jd` MCP tool and evaluation logic to incorporate historical human decision feedback (`DecisionFeedback` and confirmed rules in `memories`), refining score weighting and risk detection over time.
- **Strict Approval Workflow for Agent Tools**: Enforce approval boundaries where Agents can only stage applications in `Draft` or `Pending Approval` state, requiring human approval before marking as `Applied`.

## Capabilities

### New Capabilities
- `decision-inbox-ui`: Web UI and REST API for reviewing, approving, modifying, and rejecting Agent job recommendation proposals.
- `human-feedback-loop`: Memory engine and feedback capture mechanisms that feed human decision reasons back into future `evaluate_jd` evaluations.

### Modified Capabilities
- `agent-task-center`: Extend Agent task center requirements to expose pending decision approval counts and approval-related trace events.
- `jd-evaluation-mcp`: Modify `evaluate_jd` tool requirements to factor in historical human decision feedback (`DecisionFeedback`) alongside candidate profile and negative rules.
- `application-resume-binding`: Ensure application creation by Agents defaults to `Pending Approval` / `Draft` status until explicitly approved by human action.

## Impact

- `models.py`: Add `DecisionFeedback` model and update `Application` status handling (`Pending Approval`).
- `routes/agent_api.py` & `routes/application.py`: Add endpoints for fetching pending proposals, submitting decision feedback (approve/reject), and updating application status.
- `mcp_server.py`: Update `evaluate_jd` to load past `DecisionFeedback` records for context-aware scoring; restrict `create_application` default status to `Pending Approval`.
- `templates/dashboard.html`: Integrate the "Decision Inbox" component with recommendation cards and feedback dialogs.
- `tests/test_agent_api.py` & `tests/test_routes.py`: Add unit tests for Decision Inbox APIs and Feedback Loop evaluation logic.
