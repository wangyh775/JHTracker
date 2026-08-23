import sys
import os
import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== S / A COMPANIES ===")
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
    print(f"ID {r['id']:<4} | {r['name']:<25} | Priority: {r['priority']} | Score: {r['score']} | Apps: {r['app_count']} | LastApp: {r['last_app_created']} | LastEvent: {r['last_review_time']}")

print("\n=== RECENT AGENT TASKS (LAST 10) ===")
cur.execute("SELECT id, task_id, agent_name, status, created_at FROM agent_tasks ORDER BY id DESC LIMIT 10")
for t in cur.fetchall():
    print(dict(t))

print("\n=== RECENT AGENT EVENTS (LAST 20) ===")
cur.execute("SELECT id, task_id, event_type, created_at, SUBSTR(payload_json, 1, 150) as payload FROM agent_events ORDER BY id DESC LIMIT 20")
for e in cur.fetchall():
    print(f"Event {e['id']} | Task {e['task_id']} | Type {e['event_type']} | Date: {e['created_at']} | Payload: {e['payload']}")

print("\n=== USER PREFERENCES / MEMORIES ===")
cur.execute("SELECT id, category, rule_value, raw_feedback FROM memories ORDER BY id DESC LIMIT 10")
for m in cur.fetchall():
    print(dict(m))

conn.close()
