import sys
import os
import sqlite3
import json
from datetime import datetime

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all S/A companies
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")
companies = [dict(r) for r in cur.fetchall()]

# Get all agent events related to midnight review or sourcing
cur.execute("""
    SELECT e.id, e.task_id, e.event_type, e.payload_json, e.created_at, t.task_id as tid, t.agent_name
    FROM agent_events e
    JOIN agent_tasks t ON e.task_id = t.id
    WHERE t.agent_name LIKE '%Review%' OR t.agent_name LIKE '%review%' OR e.payload_json LIKE '%company_id%'
    ORDER BY e.id ASC
""")
events = [dict(r) for r in cur.fetchall()]

# Build mapping of company_id to last review time
last_reviewed = {}
for c in companies:
    cid = c['id']
    cname = c['name']
    # check in events
    latest_t = None
    for e in events:
        p = e['payload_json'] or ""
        if (f'"company_id": {cid}' in p or f'"company_id":{cid}' in p or 
            f'ID {cid}' in p or cname in p or f'company_id={cid}' in p):
            latest_t = e['created_at']
    # also check score_reason for date stamps like 【2026-08-xx
    if c['score_reason'] and '【2026-08-' in c['score_reason']:
        idx = c['score_reason'].find('【2026-08-')
        date_str = c['score_reason'][idx+1:idx+11]
        if not latest_t or date_str > latest_t[:10]:
            latest_t = date_str + " 00:00:00"
    last_reviewed[cid] = latest_t

# Get application counts & latest app
cur.execute("""
    SELECT company_id, COUNT(*) as app_cnt, MAX(created_at) as last_app
    FROM applications
    GROUP BY company_id
""")
app_stats = {r['company_id']: dict(r) for r in cur.fetchall()}

# Combine info
results = []
for c in companies:
    cid = c['id']
    rev = last_reviewed.get(cid)
    astat = app_stats.get(cid, {'app_cnt': 0, 'last_app': None})
    results.append({
        'id': cid,
        'name': c['name'],
        'priority': c['priority'],
        'score': c['score'],
        'score_reason': c['score_reason'],
        'last_reviewed': rev,
        'app_cnt': astat['app_cnt'],
        'last_app': astat['last_app']
    })

# Print overview sorted by last_reviewed ASC (None first), then by id ASC
results_sorted = sorted(results, key=lambda x: (x['last_reviewed'] or '1970-01-01', x['id']))

print("=== CANDIDATES FOR MIDNIGHT REVIEW (SORTED BY LAST REVIEW DATE) ===")
for r in results_sorted[:30]:
    print(f"ID {r['id']:<4} | {r['name']:<25} | [{r['priority']}] | LastRev: {str(r['last_reviewed']):<19} | Apps: {r['app_cnt']} | Score: {r['score']}")

# Also print the recent rotation batches from agent_events
print("\n=== RECENT ROTATION BATCHES FROM TASKS ===")
cur.execute("""
    SELECT task_id, agent_name, created_at, status 
    FROM agent_tasks 
    WHERE agent_name LIKE '%Review%' OR agent_name LIKE '%review%' OR task_id LIKE '%midnight%'
    ORDER BY id DESC LIMIT 10
""")
for t in cur.fetchall():
    print(dict(t))

conn.close()
