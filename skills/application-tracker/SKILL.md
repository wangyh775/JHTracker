---
name: "application-tracker"
description: "Manages job application lifecycle (HITL review approval/rejection, apply status changes, interview feedback, offer tracking). Alias: career-tracker-application, career-tracker-offer."
allowed-tools:
  - JHTracker:create_application
  - JHTracker:get_application
  - JHTracker:list_applications
  - JHTracker:update_application_status
  - JHTracker:get_pending_approvals
  - JHTracker:handle_decision
  - JHTracker:archive_application
  - JHTracker:create_interview_feedback
  - JHTracker:list_interview_feedbacks
  - JHTracker:get_user_preferences
  - JHTracker:record_agent_trace
---

# Application Tracker Skill

Manages the full lifecycle of job applications in JHTracker, supporting Human-in-the-Loop (HITL) approval, status updates, interview tracking, and offer management.

## Trigger Scenarios

Invoke when the user says any of:
- "记录投递 {公司} {岗位}" / "更新 {公司} 状态为 {状态}"
- "审核待投递岗位" / "批准/拒绝智能体推荐的岗位"
- "记录面试/笔试/Offer/拒信" / "查看 Offer 进展"
- "apply to {company}" / "mark {company} application as {status}"

## Application Lifecycle & Status Flow

### Pre-Application (投递前 — Agent 可写)
`Pending Approval` (Agent 提案) → 人类在 Decision Inbox 批准 → `待投递` (进入 /to-apply 待投递清单)

### Post-Application (投递后 — 仅人类可写)
人类在 /to-apply 完成投递 → `已投递` (进入 /applications 投递记录) → `简历筛选` → `笔试` → `一面` → `二面` → `终面` → `Offer` / `已拒`

## HITL (Human-in-the-Loop) Review Workflow & Trace Logging

When applications are created by Agent recommendation:
1. Status is initially set to `Pending Approval` with metadata (`match_score`, `agent_reason`, `source_url`, `agent_task_id`).
2. Log execution trace using `JHTracker:record_agent_trace(task_id=agent_task_id, agent_name="ApplicationAgent", event_type="recommendation_pushed", payload=...)`.
3. Candidate reviews application in Decision Inbox.
4. **Approve**: Status updates to `待投递` (moves to /to-apply page).
5. **Reject**: Status updates to `已拒绝` and feedback is automatically saved to `memories` table to refine future Agent recommendations.

## Agent Write Protection

Agent SHALL NOT modify any application record whose status is in `POST_APPLY_STATUS_LIST` (`已投递`, `简历筛选`, `笔试`, `一面`, `二面`, `终面`, `Offer`, `已拒`). These records are reserved for human edit only. The MCP tool `update_application_status` SHALL reject any Agent request to mutate post-apply records.

## Database SQL Reference

```sql
-- Create pending application recommendation (Agent writes this)
INSERT INTO applications (company_id, position, status, channel, match_score, agent_reason, source_url, created_at)
VALUES (?, ?, 'Pending Approval', 'Agent Recommendation', 85, 'Strong tech match', 'https://...', datetime('now'));

-- Human marks as applied (human-only operation)
UPDATE applications SET status = '已投递', apply_date = CURRENT_DATE WHERE id = ?;

-- Transition to Offer (human-only operation)
UPDATE applications SET status = 'Offer', offer_status = 'pending' WHERE id = ?;
```
