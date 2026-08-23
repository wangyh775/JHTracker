import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, task_id, agent_name, event_type, payload, status, created_at 
    FROM agent_traces 
    WHERE task_id LIKE '%midnight%' 
    ORDER BY id DESC LIMIT 20
""")
traces = [dict(r) for r in cur.fetchall()]

with open("career-tracker/scripts/midnight_traces_dump.json", "w", encoding="utf-8") as f:
    json.dump(traces, f, ensure_ascii=False, indent=2)

conn.close()
