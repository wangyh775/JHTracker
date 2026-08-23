import sys
import os
import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

lines = []

lines.append("=== S / A COMPANIES ===")
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.created_at,
           COUNT(a.id) as app_count,
           MAX(a.created_at) as last_app_created,
           (SELECT MAX(created_at) FROM agent_events WHERE payload_json LIKE '%' || c.name || '%' OR payload_json LIKE '%"company_id": ' || c.id || '%' OR payload_json LIKE '%"company_id":' || c.id || '%') as last_review_time
    FROM companies c
    LEFT JOIN applications a ON c.id = a.company_id
    WHERE c.priority IN ('S', 'A')
    GROUP BY c.id
    ORDER BY c.id ASC
""")
rows = cur.fetchall()
for r in rows:
    lines.append(f"ID {r['id']:<4} | {r['name']:<25} | Priority: {r['priority']} | Score: {r['score']} | Apps: {r['app_count']} | LastApp: {r['last_app_created']} | LastEvent: {r['last_review_time']}")

lines.append("\n=== RECENT AGENT TASKS (LAST 10) ===")
cur.execute("SELECT id, task_id, agent_name, status, created_at FROM agent_tasks ORDER BY id DESC LIMIT 10")
for t in cur.fetchall():
    lines.append(str(dict(t)))

lines.append("\n=== RECENT AGENT EVENTS (LAST 25) ===")
cur.execute("SELECT id, task_id, event_type, created_at, SUBSTR(payload_json, 1, 150) as payload FROM agent_events ORDER BY id DESC LIMIT 25")
for e in cur.fetchall():
    lines.append(f"Event {e['id']} | Task {e['task_id']} | Type {e['event_type']} | Date: {e['created_at']} | Payload: {e['payload']}")

lines.append("\n=== USER PREFERENCES / MEMORIES ===")
cur.execute("SELECT id, category, rule_value, raw_feedback FROM memories ORDER BY id DESC LIMIT 10")
for m in cur.fetchall():
    lines.append(str(dict(m)))

lines.append("\n=== ALL APPLICATIONS FOR S/A COMPANIES ===")
cur.execute("""
    SELECT a.id, a.company_id, c.name as company_name, a.position, a.status, a.match_score, a.created_at, a.source_url
    FROM applications a
    JOIN companies c ON a.company_id = c.id
    WHERE c.priority IN ('S', 'A')
    ORDER BY a.id DESC
""")
for a in cur.fetchall():
    lines.append(f"App {a['id']} | Comp {a['company_id']} ({a['company_name']}): {a['position']} [{a['status']}] Score: {a['match_score']} Date: {a['created_at']} URL: {a['source_url']}")

conn.close()

with open(r"D:/DJTU/HermesWorkspace/career-tracker/scripts/inspect_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
