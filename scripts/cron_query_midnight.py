import sys
import sqlite3
import json

out_path = r"D:/DJTU/HermesWorkspace/career-tracker/scripts/cron_query_output.txt"

try:
    db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    lines = []

    # 1. Get user preferences
    cur.execute("SELECT category, rule_value, raw_feedback FROM memories ORDER BY id DESC")
    memories = [dict(r) for r in cur.fetchall()]
    lines.append("=== MEMORIES / PREFERENCES ===")
    for m in memories[:15]:
        lines.append(str(m))

    # 2. Get S and A priority companies sorted by id ASC
    cur.execute("""
        SELECT id, name, priority, score, score_reason, created_at 
        FROM companies 
        WHERE priority IN ('S', 'A') 
        ORDER BY id ASC
    """)
    companies = [dict(r) for r in cur.fetchall()]
    lines.append(f"\n=== TOTAL S/A COMPANIES ({len(companies)}) ===")
    for c in companies:
        lines.append(f"ID {c['id']}: {c['name']} [{c['priority']}] (Score: {c['score']}) - Created: {c['created_at']} - Reason: {c['score_reason']}")

    # 3. Check agent traces or review history
    cur.execute("""
        SELECT task_id, agent_name, status, created_at 
        FROM agent_tasks 
        ORDER BY id DESC LIMIT 20
    """)
    tasks = [dict(r) for r in cur.fetchall()]
    lines.append("\n=== RECENT AGENT TASKS ===")
    for t in tasks:
        lines.append(str(t))

    # 4. Check agent events
    cur.execute("""
        SELECT e.id, e.task_id, e.event_type, e.payload_json, e.created_at, t.task_id as tid
        FROM agent_events e
        JOIN agent_tasks t ON e.task_id = t.id
        ORDER BY e.id DESC LIMIT 30
    """)
    events = [dict(r) for r in cur.fetchall()]
    lines.append("\n=== RECENT AGENT EVENTS ===")
    for e in events:
        lines.append(f"{e['created_at']} | Task: {e['tid']} | Event: {e['event_type']} | Payload: {e['payload_json'][:140] if e['payload_json'] else ''}")

    # 5. Check existing applications for all S/A companies
    cur.execute("""
        SELECT a.id, a.company_id, c.name as company_name, a.position, a.status, a.match_score, a.created_at, a.updated_at, a.source_url
        FROM applications a
        JOIN companies c ON a.company_id = c.id
        WHERE c.priority IN ('S', 'A')
        ORDER BY a.id DESC
    """)
    apps = [dict(r) for r in cur.fetchall()]
    lines.append(f"\n=== S/A APPLICATIONS ({len(apps)}) ===")
    for a in apps:
        lines.append(f"App {a['id']} | Comp {a['company_id']} ({a['company_name']}): {a['position']} [{a['status']}] Score: {a['match_score']} Created: {a['created_at']}")

    # 6. Check default resume
    cur.execute("SELECT id, name, version, file_path, is_default FROM resumes ORDER BY is_default DESC, id DESC LIMIT 5")
    resumes = [dict(r) for r in cur.fetchall()]
    lines.append(f"\n=== RESUMES ===")
    for r in resumes:
        lines.append(str(r))

    conn.close()

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

except Exception as e:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
