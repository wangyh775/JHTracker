import sys
import os
import json
import sqlite3

sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")
from mcp_server import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Query all S and A priority companies sorted by id
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.updated_at, c.created_at,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app_date,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_count
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")

rows = [dict(r) for r in cur.fetchall()]

# Let's inspect which companies were reviewed recently (e.g. within last 3 days, today is 2026-08-23, so >= 2026-08-20 is last 3 days: 20, 21, 22)
with open("career-tracker/scripts/sa_inspection.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

print(f"Total S/A companies: {len(rows)}")
for r in rows:
    # check date in score_reason
    sr = r['score_reason'] or ""
    print(f"ID {r['id']:<4} [{r['priority']}] {r['name']:<30} score:{r['score']} apps:{r['app_count']} last_app:{r['last_app_date']} sr:{sr[:40]}")
