import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, name, city, industry, priority, score, match_reason, score_reason, website
    FROM companies
    WHERE priority IN ('S', 'A')
    ORDER BY priority DESC, score DESC, id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

with open("D:/DJTU/HermesWorkspace/career-tracker/data/all_sa_raw.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
