import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check company table IDs
cur.execute("SELECT id, name, priority, score, score_reason FROM companies WHERE id >= 770 ORDER BY id ASC")
recent_comps = [dict(r) for r in cur.fetchall()]

# Let's inspect the entire company list to see the loop logic
cur.execute("SELECT id, name, priority, score FROM companies WHERE priority IN ('S', 'A') ORDER BY id ASC")
all_sa = [dict(r) for r in cur.fetchall()]

print(f"Total S/A: {len(all_sa)}")
print("First 10 S/A IDs:", [c['id'] for c in all_sa[:10]])
print("Last 15 S/A IDs:", [c['id'] for c in all_sa[-15:]])

conn.close()
