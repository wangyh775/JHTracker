import sqlite3
import json
import re

# Direct execution script to output candidates directly to file
db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all S and A priority companies sorted by id
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.created_at, c.updated_at,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_cnt,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

# Recent 3 days = 20, 21, 22, 23
recent_days = {20, 21, 22, 23}

candidates_after_783 = []
for r in rows:
    if r['id'] >= 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        if last_sr_day not in recent_days:
            candidates_after_783.append(r)

# Take the first 5 in ascending order
selected = candidates_after_783[:5]

for c in selected:
    cur.execute("SELECT id, position, status, match_score, source_url, created_at, job_desc, agent_reason FROM applications WHERE company_id = ? ORDER BY id DESC", (c['id'],))
    c['applications'] = [dict(a) for a in cur.fetchall()]

# Write output file
with open(r"D:/DJTU/HermesWorkspace/career-tracker/scripts/selected_5_midnight_20260823.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)

conn.close()
