import sys
import os
sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")
import json
import sqlite3

conn = sqlite3.connect(r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, task_id, agent_name, event_type, payload, status, created_at FROM agent_traces WHERE task_id LIKE '%midnight%' ORDER BY id DESC LIMIT 15")
traces = [dict(r) for r in cur.fetchall()]
for t in traces:
    print(t['created_at'], t['task_id'], t['event_type'], t['payload'][:100] if t['payload'] else '')

conn.close()
