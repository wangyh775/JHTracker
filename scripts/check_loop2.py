import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check all S/A companies with id >= 770
cur.execute("SELECT id, name, priority, score, score_reason FROM companies WHERE id >= 770 AND priority IN ('S', 'A') ORDER BY id ASC")
all_sa_after_770 = [dict(r) for r in cur.fetchall()]

# Also check company ID 1 to 50
cur.execute("SELECT id, name, priority, score, score_reason FROM companies WHERE priority IN ('S', 'A') ORDER BY id ASC LIMIT 20")
all_sa_first_20 = [dict(r) for r in cur.fetchall()]

out_path = r"D:/DJTU/HermesWorkspace/career-tracker/scripts/loop_inspect.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        'after_770': all_sa_after_770,
        'first_20': all_sa_first_20
    }, f, ensure_ascii=False, indent=2)

conn.close()
