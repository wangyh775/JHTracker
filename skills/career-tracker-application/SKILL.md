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
- "归档投递" / "查看归档记录" / "恢复归档"

## Application Statuses

Status flow: 待投递 → 已投递 → 简历筛选 → 笔试 → 一面 → 二面 → 终面 → Offer/已拒

## Database Schema (applications table)
- company_id, position, channel, status, apply_date, deadline
- salary_min, salary_max, job_desc, url, feedback, offer_status
- is_archived (bool, default 0), archived_at (datetime, nullable)

## Archive Rules

- Stale threshold: default 15 days since `updated_at` (configurable via `JH_ARCHIVE_STALE_DAYS` or `data/settings.json`)
- Auto-archive excludes: `status='Offer' AND offer_status IN ('pending','accepted')`
- All other stale records are archived (including 已拒, rejected offers, stalled interviews)
- Archived records are hidden from active list and dashboard funnel

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

-- Query upcoming deadlines (active only)
SELECT c.name, a.position, a.deadline, a.status
FROM applications a JOIN companies c ON a.company_id = c.id
WHERE a.is_archived = 0
  AND a.deadline >= CURRENT_DATE AND a.status NOT IN ('Offer', '已拒')
ORDER BY a.deadline LIMIT 10;

-- Query stale applications eligible for archive (15 days)
SELECT a.id, c.name, a.position, a.status, a.updated_at
FROM applications a JOIN companies c ON a.company_id = c.id
WHERE a.is_archived = 0
  AND a.updated_at < datetime('now', '-15 days')
  AND NOT (a.status = 'Offer' AND a.offer_status IN ('pending', 'accepted'));

-- Manual archive
UPDATE applications SET is_archived = 1, archived_at = CURRENT_TIMESTAMP WHERE id = ?;

-- Restore from archive
UPDATE applications SET is_archived = 0, archived_at = NULL WHERE id = ?;
```
