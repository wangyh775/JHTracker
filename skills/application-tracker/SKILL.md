---
name: "application-tracker"
description: "Manages job application lifecycle (HITL review approval/rejection, apply status changes, interview feedback, offer tracking). Alias: career-tracker-application, career-tracker-offer."
allowed-tools:
  - JHTracker:create_application
  - JHTracker:get_user_preferences
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

`待投递` (Pending Review) → `已投递` → `简历筛选` → `笔试` → `一面` → `二面` → `终面` → `Offer` / `已拒`

## HITL (Human-in-the-Loop) Review Workflow

When applications are created by Agent recommendation:
1. Status is initially set to `待投递` with metadata (`match_score`, `agent_reason`, `source_url`).
2. Candidate reviews application in Web UI (`/applications` or `/traces`).
3. **Approve**: Status updates to `to_apply` (Ready to apply).
4. **Reject**: Status updates to `rejected` and feedback is automatically saved to `memories` table to refine future Agent recommendations.

## Database SQL Reference

```sql
-- Create pending application recommendation
INSERT INTO applications (company_id, position, status, channel, match_score, agent_reason, created_at)
VALUES (?, ?, '待投递', 'Agent Recommendation', 85, 'Strong tech match', datetime('now'));

-- User status updates
UPDATE applications SET status = '已投递', apply_date = CURRENT_DATE WHERE id = ?;

-- Transition to Offer
UPDATE applications SET status = 'Offer', offer_status = 'pending' WHERE id = ?;
```
