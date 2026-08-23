import sys
import os
import json
import sqlite3

sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")
from mcp_server import get_db_connection, get_candidate_profile

conn = get_db_connection()
cur = conn.cursor()

# Get recent trace logs to see which companies were reviewed in recent runs
cur.execute("""
    SELECT task_id, agent_name, event_type, payload, status, created_at
    FROM agent_traces
    WHERE event_type IN ('start', 'review', 'summary', 'complete')
    ORDER BY id DESC
    LIMIT 30
""")
traces = [dict(r) for r in cur.fetchall()]

print("--- RECENT TRACES ---")
for t in traces[:10]:
    print(t['created_at'], t['agent_name'], t['event_type'], t['payload'][:120] if t['payload'] else '')

# Get all S and A priority companies sorted by id
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.updated_at, c.created_at,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app_date,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_count
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")

rows = [dict(r) for r in cur.fetchall()]
print(f"\nTotal S/A companies: {len(rows)}")

# Check last reviewed companies
# On 2026-08-22 (yesterday), batch was [775, 776, 777, 779, 783]
# Let's inspect who was reviewed on 2026-08-20, 2026-08-21, 2026-08-22
import re

candidates = []
for r in rows:
    cid = r['id']
    name = r['name']
    sr = r['score_reason'] or ""
    
    # Check date matches
    m = re.findall(r'2026-08-(\d{2})', sr)
    last_sr_day = max([int(x) for x in m]) if m else 0
    
    # Check last app date
    last_app = r['last_app_date'] or ""
    m_app = re.findall(r'2026-08-(\d{2})', last_app)
    last_app_day = max([int(x) for x in m_app]) if m_app else 0
    
    max_day = max(last_sr_day, last_app_day)
    candidates.append({
        'id': cid,
        'name': name,
        'priority': r['priority'],
        'score': r['score'],
        'max_day': max_day,
        'last_sr_day': last_sr_day,
        'last_app_day': last_app_day,
        'last_app_date': r['last_app_date'],
        'app_count': r['app_count'],
        'score_reason': sr[:80]
    })

# Sort candidates by max_day ASC, then id ASC
candidates_sorted = sorted(candidates, key=lambda x: (x['max_day'], x['id']))

print("\n--- TOP 20 OLDEST REVIEWED CANDIDATES ---")
for c in candidates_sorted[:20]:
    print(f"ID {c['id']:<4} [{c['priority']}] {c['name']:<32} MaxDay: {c['max_day']:<2} (SR:{c['last_sr_day']} App:{c['last_app_day']}) Apps: {c['app_count']}")

with open("career-tracker/scripts/candidate_analysis.json", "w", encoding="utf-8") as f:
    json.dump(candidates_sorted, f, ensure_ascii=False, indent=2)

conn.close()
