---
name: career-tracker-application
description: "Manages the application lifecycle in JHTracker — add/edit/transition status, record application details. Invoke when user says '投递/记录申请/更新状态/面试/offer/拒信' or 'track application/update status'."
---

# Career Tracker Application Skill

Manages job applications in the tracker.

## When to Invoke

- "记录投递 {公司} {岗位}" / "更新 {公司} 状态为 {状态}"
- "apply to {company}" / "mark {company} as {status}"
- "记录面试/笔试/Offer/拒信"
- "查看本周截止"

## Application Statuses

Status flow: 待投递 → 已投递 → 简历筛选 → 笔试 → 一面 → 二面 → 终面 → Offer/已拒

## Database Schema (applications table)
- company_id, position, channel, status, apply_date, deadline
- salary_min, salary_max, job_desc, url, feedback, offer_status

## Workflow

1. Look up company by name using Fuzzy match
2. Insert or update application record
3. On status change to Offer: offer_status should be set to 'pending'

```sql
-- Insert
INSERT INTO applications (company_id, position, status, apply_date, url)
VALUES (?, ?, '已投递', CURRENT_DATE, ?);

-- Status update
UPDATE applications SET status = 'Offer', offer_status = 'pending'
WHERE company_id = ? AND position = ?;

-- Query upcoming deadlines
SELECT c.name, a.position, a.deadline, a.status
FROM applications a JOIN companies c ON a.company_id = c.id
WHERE a.deadline >= CURRENT_DATE AND a.status NOT IN ('Offer', '已拒')
ORDER BY a.deadline LIMIT 10;
```