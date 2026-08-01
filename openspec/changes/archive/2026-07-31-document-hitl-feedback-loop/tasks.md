## 1. Update `docs/database.md` — Add DecisionFeedback & Memory

- [x] 1.1 Update table list from "8 张表" to "10 张表" and add rows for `decision_feedbacks` and `memories`
- [x] 1.2 Add `DecisionFeedback` entity to ER diagram with fields: id, application_id FK, action, reason_category, raw_feedback, created_at
- [x] 1.3 Add `Memory` entity to ER diagram with fields: id, rule_type, rule_value, raw_feedback, created_at
- [x] 1.4 Add `Application.decision_feedbacks` relationship to ER diagram
- [x] 1.5 Add field descriptions for both new tables below the ER diagram
- [x] 1.6 Update "迁移管理" section to include the new migration `c3d4e5f6a7b8_add_decision_feedbacks_table`

## 2. Update `docs/api.md` — Add HITL & Agent Task Endpoints

- [x] 2.1 Update Agent API endpoint table from 8 to 15 rows: add GET `/api/agent/tasks`, GET `/api/agent/tasks/<task_id>`, GET `/api/agent/decisions/pending`, POST `/api/agent/decisions/<id>`, GET `/api/v1/traces`, GET `/api/v1/companies`, and the DecisionFeedback-aware MCP tools
- [x] 2.2 Add a new subsection "🧑‍⚖️ HITL Decision Endpoints (`/api/agent/`)」with method, path, and description for each
- [x] 2.3 Update the MCP Server section to list `evaluate_jd`, `record_agent_trace`, `update_candidate_profile` tools with their signatures
- [x] 2.4 Update the endpoint count summary table (dashboard blueprint count: 3 → 5 for SSE endpoints if applicable)

## 3. Update `docs/SKILLS_AND_MCP_GUIDE.md` — Add MCP Tools & HITL Flow

- [x] 3.1 Add `evaluate_jd` to the MCP tools list with signature and description
- [x] 3.2 Add `record_agent_trace` to the MCP tools list with signature and description
- [x] 3.3 Add `update_candidate_profile` to the MCP tools list with signature and description
- [x] 3.4 Update the HITL workflow diagram (section 4) to include the feedback loop: approve → Applied, reject → DecisionFeedback + Memory → future evaluate_jd penalizes

## 4. Create `docs/hitl-feedback-loop.md` — New HITL Closed-Loop Design Doc

- [x] 4.1 Write overview: purpose, architecture diagram showing the full loop (Agent → create_application → Pending Approval → Decision Inbox → human approve/reject → DecisionFeedback → Memory → evaluate_jd)
- [x] 4.2 Write "Data Model" section: document DecisionFeedback (action, reason_category, raw_feedback) and Memory (rule_type, rule_value) with their role in the loop
- [x] 4.3 Write "HITL Decision Flow" section: describe the 3-action model (approve → Applied, reject → Rejected + feedback, edit → updates fields)
- [x] 4.4 Write "Feedback → Memory → Scoring" section: describe how evaluate_jd queries decision_feedbacks and penalizes scores based on past rejections
- [x] 4.5 Write "UI: Decision Inbox" section: describe the Decision Inbox card on the dashboard with approve/reject buttons, reject reason modal, 15s polling
- [x] 4.6 Write "UI: Agent Task Center" section: describe the Agent Task Center card with task status, event count, trace log link, pending approvals badge
- [x] 4.7 Write "Trace Audit" section: describe the /traces page with accordion UI, event type badges, JSON payload display
- [x] 4.8 Add a Mermaid sequence diagram for the complete HITL closed loop

## 5. Update `docs/README.md` — Document Index

- [x] 5.1 Add `hitl-feedback-loop.md` to the document index table
- [x] 5.2 Add "HITL 闭环" to the quick navigation section