import sys
import os
sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")

import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.created_at, c.updated_at,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_cnt,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

recent_reviewed_days = {20, 21, 22, 23}

batch_candidates = []
for r in rows:
    if r['id'] >= 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        if last_sr_day not in recent_reviewed_days:
            last_app = r['last_app'] or ""
            m_app = re.findall(r'2026-08-(\d{2})', last_app)
            last_app_day = max([int(x) for x in m_app]) if m_app else 0
            if last_app_day not in recent_reviewed_days:
                batch_candidates.append(r)

wrap_around_candidates = []
for r in rows:
    if r['id'] < 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        if last_sr_day not in recent_reviewed_days:
            last_app = r['last_app'] or ""
            m_app = re.findall(r'2026-08-(\d{2})', last_app)
            last_app_day = max([int(x) for x in m_app]) if m_app else 0
            if last_app_day not in recent_reviewed_days:
                wrap_around_candidates.append(r)

out = {
    'batch_candidates_784_plus': batch_candidates,
    'wrap_around_candidates': wrap_around_candidates[:10]
}

with open("career-tracker/scripts/selected_rotation_raw.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

conn.close()
