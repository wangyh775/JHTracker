import sys
import os
import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

targets = [775, 776, 777, 779, 783]

lines = []
lines.append("=== TARGET COMPANIES DETAILS ===")
for tid in targets:
    cur.execute("SELECT * FROM companies WHERE id = ?", (tid,))
    c = dict(cur.fetchone())
    lines.append(f"\nTarget ID {c['id']}: {c['name']} (Priority: {c['priority']}, Score: {c['score']})")
    lines.append(f"  Reason: {c['score_reason']}")
    
    cur.execute("SELECT * FROM applications WHERE company_id = ?", (tid,))
    apps = [dict(a) for a in cur.fetchall()]
    lines.append(f"  Existing Applications ({len(apps)}):")
    for a in apps:
        lines.append(f"    App {a['id']}: {a['position']} [{a['status']}] Score: {a['match_score']} Source: {a['source_url']}")

with open(r"D:/DJTU/HermesWorkspace/career-tracker/scripts/target_inspect_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

conn.close()
