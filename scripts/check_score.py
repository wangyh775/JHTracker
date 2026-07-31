import sqlite3

db = sqlite3.connect('D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db')
cur = db.cursor()

cur.execute("SELECT COUNT(*) FROM companies WHERE priority IN ('S','A') AND score IS NOT NULL")
scored = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM companies WHERE priority IN ('S','A') AND score = 0")
zero_score = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM companies WHERE priority IN ('S','A') AND score IS NULL")
still_null = cur.fetchone()[0]

cur.execute("SELECT id, name, score, score_reason FROM companies WHERE priority IN ('S','A') AND score IS NOT NULL AND score > 0 ORDER BY score DESC LIMIT 5")
top5 = cur.fetchall()

print(f"已评分: {scored}")
print(f"淘汰(0分): {zero_score}")
print(f"未评分(NULL): {still_null}")
print("最高评分 Top 5:")
for t in top5:
    print(f"  ID={t[0]} {t[1]}: {t[2]}分 - {t[3][:60]}")
