import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all S and A priority companies
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.created_at, c.updated_at,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_cnt,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

# Let's inspect the rotation sequence from recent traces:
# Let's see all previous trace logs for MidnightCompanyReviewAgent
cur.execute("""
    SELECT created_at, task_id, payload
    FROM agent_traces
    WHERE agent_name = 'MidnightCompanyReviewAgent' AND event_type = 'start'
    ORDER BY id DESC
    LIMIT 10
""")
traces = [dict(r) for r in cur.fetchall()]
print("=== PREVIOUS MIDNIGHT RUNS ===")
for t in traces:
    print(t['created_at'], t['task_id'], t['payload'])

conn.close()
