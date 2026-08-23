import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cids = [775, 776, 777, 779, 780, 783, 784, 785, 786, 787]
cur.execute(f"SELECT * FROM companies WHERE id IN ({','.join(map(str, cids))}) ORDER BY id ASC")
comps = [dict(r) for r in cur.fetchall()]

cur.execute(f"SELECT * FROM applications WHERE company_id IN ({','.join(map(str, cids))}) ORDER BY id DESC")
apps = [dict(r) for r in cur.fetchall()]

out_path = r"D:/DJTU/HermesWorkspace/career-tracker/scripts/inspect_target_5.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({'companies': comps, 'applications': apps}, f, ensure_ascii=False, indent=2)

conn.close()
