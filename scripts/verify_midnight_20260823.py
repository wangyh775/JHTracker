import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Inspect reviewed companies
cur.execute("SELECT id, name, priority, score, score_reason, updated_at FROM companies WHERE id IN (784, 785, 786, 787, 788)")
companies = [dict(r) for r in cur.fetchall()]
print("=== UPDATED COMPANIES ===")
for c in companies:
    print(f"ID {c['id']}: {c['name']} [{c['priority']}] -> Score: {c['score']}")
    print(f"   Reason: {c['score_reason']}")

# 2. Inspect applications for Caterpillar (785)
cur.execute("SELECT id, company_id, position, status, match_score, source_url, created_at FROM applications WHERE company_id = 785 ORDER BY id DESC")
apps = [dict(r) for r in cur.fetchall()]
print("\n=== APPLICATIONS FOR CATERPILLAR (785) ===")
for a in apps:
    print(f"App #{a['id']}: {a['position']} ({a['status']}) - Match: {a['match_score']} - URL: {a['source_url']}")

# 3. Inspect latest agent_traces
cur.execute("SELECT id, task_id, agent_name, event_type, status, created_at FROM agent_traces WHERE task_id = 'cron_midnight_review_20260823' ORDER BY id ASC")
traces = [dict(r) for r in cur.fetchall()]
print("\n=== AGENT TRACES ===")
for t in traces:
    print(f"Trace #{t['id']}: {t['event_type']} ({t['status']}) - {t['created_at']}")

conn.close()
