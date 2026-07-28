---
name: career-tracker-offer
description: "Offer comparison and decision tracking for JHTracker. Invoke when user says '对比Offer', 'offer对比', 'compare offers', '决策矩阵'."
---

# Career Tracker Offer Skill

Helps compare and decide between multiple offers.

## Workflow

1. Query applications with `status='Offer'`
2. Display side-by-side comparison
3. Optionally call LLM to analyze pros/cons

```sql
-- Get all offers with company details
SELECT a.id, c.name, a.position, a.salary_min, a.salary_max,
       a.job_desc, c.city, c.industry, a.apply_date, a.offer_status
FROM applications a JOIN companies c ON a.company_id = c.id
WHERE a.status = 'Offer' AND a.offer_status = 'pending'
ORDER BY a.salary_min DESC NULLS LAST;
```

## Offer Decision Dimensions
- Compensation (base/signing/bonus/stock)
- Location & living cost
- Company reputation & industry
- Team & technology stack
- Career growth & promotion path
- Work-life balance & culture