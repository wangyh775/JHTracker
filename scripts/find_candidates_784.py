import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check companies with id >= 784
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.created_at, c.updated_at,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_cnt,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app
    FROM companies c
    WHERE c.priority IN ('S', 'A') AND c.id >= 784
    ORDER BY c.id ASC
""")
rows_784 = [dict(r) for r in cur.fetchall()]

# Check which ones are already reviewed in the last 3 days (>= 2026-08-20)
# Today is 2026-08-23
recent_threshold = 20

unreviewed_784 = []
for r in rows_784:
    sr = r['score_reason'] or ""
    m = re.findall(r'2026-08-(\d{2})', sr)
    last_sr_day = max([int(x) for x in m]) if m else 0
    
    # Also check if it was reviewed on day 20, 21, 22
    if last_sr_day < recent_threshold:
        unreviewed_784.append((r, last_sr_day))

out = []
for r, sr_day in unreviewed_784:
    out.append({
        'id': r['id'],
        'name': r['name'],
        'priority': r['priority'],
        'score': r['score'],
        'industry': r['industry'],
        'city': r['city'],
        'website': r['website'],
        'sr_day': sr_day,
        'app_cnt': r['app_cnt'],
        'last_app': r['last_app'],
        'score_reason': r['score_reason']
    })

with open("career-tracker/scripts/unreviewed_784.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"Total unreviewed in >=784: {len(out)}")
for o in out:
    print(f"ID {o['id']:<4} [{o['priority']}] {o['name']:<35} sr_day:{o['sr_day']} apps:{o['app_cnt']} city:{o['city']}")

conn.close()
