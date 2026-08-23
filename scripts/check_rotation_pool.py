import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check recent agent_traces
cur.execute("SELECT id, task_id, agent_name, event_type, payload, status, created_at FROM agent_traces ORDER BY id DESC LIMIT 20")
traces = [dict(r) for r in cur.fetchall()]

# Print trace history
print("=== RECENT AGENT TRACES ===")
for t in traces:
    print(f"[{t['created_at']}] {t['task_id']} | {t['event_type']} | {t['status']} | {str(t['payload'])[:80]}")

# Get all S and A priority companies sorted by id
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.updated_at, c.created_at,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app_date,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_count
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")

rows = [dict(r) for r in cur.fetchall()]

# Find all companies reviewed in the last 3 days (today is 2026-08-23, so days 20, 21, 22, 23)
recent_reviewed_ids = set()
for r in rows:
    sr = r['score_reason'] or ""
    m = re.findall(r'2026-08-(\d{2})', sr)
    if m:
        max_sr_day = max([int(x) for x in m])
        if max_sr_day >= 20: # 20, 21, 22, 23
            recent_reviewed_ids.add(r['id'])

print(f"\nCompanies reviewed in last 3 days (>= 2026-08-20): {len(recent_reviewed_ids)} companies")
print("IDs:", sorted(list(recent_reviewed_ids)))

# Filter unreviewed or oldest reviewed companies
unreviewed_or_old = []
for r in rows:
    if r['id'] not in recent_reviewed_ids:
        # Check last review day
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        unreviewed_or_old.append({
            'id': r['id'],
            'name': r['name'],
            'priority': r['priority'],
            'score': r['score'],
            'last_sr_day': last_sr_day,
            'app_count': r['app_count'],
            'last_app_date': r['last_app_date'],
            'industry': r['industry'],
            'city': r['city'],
            'website': r['website'],
            'score_reason': sr
        })

print(f"\nUnreviewed or eligible for review (count={len(unreviewed_or_old)}):")
# Sort by company_id ASC as specified by rule 2: "按 company_id 升序轮询 S/A 级企业（每次选取 5 家未复盘或最久未更新的企业）"
# Also check who was already rotated in previous runs:
# Batch 2026-08-20: [770, 771, 772, 773, 774]
# Batch 2026-08-21: ...
# Batch 2026-08-22: [775, 776, 777, 779, 783]
# Let's inspect the next 5 companies after 783 or starting from unreviewed.

unreviewed_sorted = sorted(unreviewed_or_old, key=lambda x: x['id'])

for u in unreviewed_sorted[:25]:
    print(f"ID {u['id']:<4} [{u['priority']}] {u['name']:<35} RevDay: {u['last_sr_day']} Apps: {u['app_count']} LastApp: {u['last_app_date']}")

with open("career-tracker/scripts/rotation_pool.json", "w", encoding="utf-8") as f:
    json.dump(unreviewed_sorted, f, ensure_ascii=False, indent=2)

conn.close()
