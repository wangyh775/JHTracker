import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Look at all S/A companies
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.created_at, c.updated_at,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_cnt,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

# Last reviewed trace batch on 2026-08-22 was [775, 776, 777, 779, 783]
# Let's see all companies with id >= 784 that have NOT been reviewed on 2026-08-20, 21, 22
recent_reviewed_days = {20, 21, 22, 23}

batch_candidates = []
for r in rows:
    if r['id'] >= 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        if last_sr_day not in recent_reviewed_days:
            # Also check if application created in last 3 days
            last_app = r['last_app'] or ""
            m_app = re.findall(r'2026-08-(\d{2})', last_app)
            last_app_day = max([int(x) for x in m_app]) if m_app else 0
            if last_app_day not in recent_reviewed_days:
                batch_candidates.append(r)

print(f"Candidates >= 784 not reviewed in last 3 days: {len(batch_candidates)}")
for c in batch_candidates:
    print(c['id'], c['priority'], c['name'], c['industry'], c['city'])

# If we need 5 companies, let's see how many >=784
# If fewer than 5, we wrap around to id >= 2!
print(f"Total >=784 candidates: {len(batch_candidates)}")

wrap_around_candidates = []
for r in rows:
    if r['id'] < 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        if last_sr_day not in recent_reviewed_days:
            last_app = r['last_app'] or ""
            m_app = re.findall(r'2026-08-(\d{2})', last_app)
            last_app_day = max([int(x) for x in m_app]) if m_app else 0
            if last_app_day not in recent_reviewed_days:
                wrap_around_candidates.append((r, last_sr_day))

print(f"\nCandidates < 784 not reviewed in last 3 days: {len(wrap_around_candidates)}")
for c, sr_day in wrap_around_candidates[:15]:
    print(f"ID {c['id']:<4} [{c['priority']}] {c['name']:<35} sr_day:{sr_day} apps:{c['app_cnt']}")

conn.close()
