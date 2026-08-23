import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all S and A priority companies
cur.execute("""
    SELECT id, name, priority, score, score_reason, created_at 
    FROM companies 
    WHERE priority IN ('S', 'A') 
    ORDER BY id ASC
""")
companies = [dict(r) for r in cur.fetchall()]

# Let's inspect each company's last review info from score_reason and recent applications
review_data = []
for c in companies:
    cid = c['id']
    name = c['name']
    sr = c['score_reason'] or ""
    # Check if there is a review date in score_reason like 【2026-08-XX ...】
    m = re.search(r'2026-08-(\d{2})', sr)
    review_day = int(m.group(1)) if m else 0
    
    # Check latest application created_at for this company
    cur.execute("SELECT created_at, position FROM applications WHERE company_id = ? ORDER BY id DESC LIMIT 1", (cid,))
    app = cur.fetchone()
    last_app_date = app['created_at'] if app else None
    
    review_data.append({
        'id': cid,
        'name': name,
        'priority': c['priority'],
        'score': c['score'],
        'review_day': review_day,
        'last_app_date': last_app_date,
        'score_reason': sr[:60]
    })

# Print all S/A companies with their review day
out_path = r"D:/DJTU/HermesWorkspace/career-tracker/scripts/cron_review_candidates.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"Total S/A companies: {len(companies)}\n")
    for r in review_data:
        f.write(f"ID {r['id']:<4} [{r['priority']}] {r['name']:<35} RevDay: {r['review_day']:<2} LastApp: {str(r['last_app_date']):<20} SR: {r['score_reason']}\n")

conn.close()
