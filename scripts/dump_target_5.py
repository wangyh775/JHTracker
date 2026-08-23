import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get the candidate profile preferences
with open(r"D:/DJTU/HermesWorkspace/career-tracker/data/profile.md", "r", encoding="utf-8") as f:
    profile_text = f.read()

# Select companies 784, 785, 786, 787, 788
target_ids = [784, 785, 786, 787, 788]
cur.execute(f"SELECT * FROM companies WHERE id IN ({','.join(map(str, target_ids))}) ORDER BY id ASC")
companies = [dict(r) for r in cur.fetchall()]

for c in companies:
    cur.execute("SELECT * FROM applications WHERE company_id = ? ORDER BY id DESC", (c['id'],))
    c['applications'] = [dict(a) for a in cur.fetchall()]

with open("career-tracker/scripts/target_5_details.json", "w", encoding="utf-8") as f:
    json.dump(companies, f, ensure_ascii=False, indent=2)

print("Target companies details dumped.")
for c in companies:
    print(f"ID {c['id']}: {c['name']} [{c['priority']}] - Apps: {len(c['applications'])}")
    for a in c['applications']:
        print(f"  App {a['id']}: {a['position']} | {a['status']} | {a['created_at']} | {a['source_url']}")

conn.close()
