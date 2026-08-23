import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check all S/A companies with id >= 784
cur.execute("""
    SELECT id, name, priority, score, score_reason, website, industry, city, created_at, updated_at
    FROM companies
    WHERE priority IN ('S', 'A')
    ORDER BY id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

# Let's inspect companies with id >= 784
print("=== COMPANIES ID >= 784 ===")
for r in rows:
    if r['id'] >= 784:
        sr = r['score_reason'] or ""
        # check applications
        cur.execute("SELECT id, position, status, created_at, match_score, source_url FROM applications WHERE company_id = ? ORDER BY id DESC", (r['id'],))
        apps = [dict(a) for a in cur.fetchall()]
        print(f"ID {r['id']:<4} [{r['priority']}] {r['name']:<30} score:{r['score']} apps:{len(apps)}")
        for a in apps:
            print(f"    App #{a['id']}: {a['position']} ({a['status']}) - {a['created_at']} - {a['source_url']}")
        print(f"    SR: {sr}")

# Also check early IDs (e.g. ID 2, 216, 312, 313, 314, 315, 511, 523, 525...)
print("\n=== EARLY COMPANIES (ID 2 to 550) ===")
for r in rows:
    if r['id'] < 550:
        sr = r['score_reason'] or ""
        cur.execute("SELECT id, position, status, created_at FROM applications WHERE company_id = ? ORDER BY id DESC", (r['id'],))
        apps = [dict(a) for a in cur.fetchall()]
        print(f"ID {r['id']:<4} [{r['priority']}] {r['name']:<30} score:{r['score']} apps:{len(apps)} SR:{sr[:50]}")

conn.close()
