import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Query all S/A companies
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.created_at, c.updated_at,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_cnt,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

# Days that count as "recently reviewed in last 3 days" (Today is 2026-08-23: days 20, 21, 22, 23)
recent_reviewed_days = {20, 21, 22, 23}

# Companies with id >= 784
candidates_tail = []
for r in rows:
    if r['id'] >= 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        last_app = r['last_app'] or ""
        m_app = re.findall(r'2026-08-(\d{2})', last_app)
        last_app_day = max([int(x) for x in m_app]) if m_app else 0
        if last_sr_day not in recent_reviewed_days and last_app_day not in recent_reviewed_days:
            candidates_tail.append(r)

# Candidates from start (id < 784)
candidates_head = []
for r in rows:
    if r['id'] < 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        last_app = r['last_app'] or ""
        m_app = re.findall(r'2026-08-(\d{2})', last_app)
        last_app_day = max([int(x) for x in m_app]) if m_app else 0
        if last_sr_day not in recent_reviewed_days and last_app_day not in recent_reviewed_days:
            candidates_head.append(r)

# Pick 5 companies: take from tail first (784, 785, 786, 788, 789, 790, 792), or whatever matches
selected_5 = []
if len(candidates_tail) >= 5:
    selected_5 = candidates_tail[:5]
else:
    selected_5 = candidates_tail + candidates_head[:5 - len(candidates_tail)]

# For each selected company, fetch all existing applications
for c in selected_5:
    cur.execute("SELECT id, position, status, match_score, source_url, created_at, job_desc, agent_reason FROM applications WHERE company_id = ? ORDER BY id DESC", (c['id'],))
    c['applications'] = [dict(a) for a in cur.fetchall()]

with open(r"D:/DJTU/HermesWorkspace/career-tracker/scripts/selected_5_companies.json", "w", encoding="utf-8") as f:
    json.dump(selected_5, f, ensure_ascii=False, indent=2)

print(f"Selected {len(selected_5)} companies for review:")
for c in selected_5:
    print(f"ID {c['id']:<4} [{c['priority']}] {c['name']:<35} ({c['industry']} | {c['city']}) Apps: {len(c['applications'])}")

conn.close()
