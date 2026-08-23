import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cids = [775, 776, 777, 779, 780, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795]
cur.execute(f"""
    SELECT id, name, priority, score, score_reason, website, industry, city, created_at 
    FROM companies 
    WHERE id IN ({','.join(map(str, cids))})
    ORDER BY id ASC
""")
comps = [dict(r) for r in cur.fetchall()]

for c in comps:
    cid = c['id']
    cur.execute("SELECT id, position, status, match_score, source_url, created_at FROM applications WHERE company_id = ? ORDER BY id DESC", (cid,))
    c['applications'] = [dict(a) for a in cur.fetchall()]

out_path = r"D:/DJTU/HermesWorkspace/career-tracker/scripts/inspect_sa_775_plus.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(comps, f, ensure_ascii=False, indent=2)

conn.close()
