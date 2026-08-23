import sqlite3
import json
import re

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all S and A priority companies sorted by id
cur.execute("""
    SELECT c.id, c.name, c.priority, c.score, c.score_reason, c.website, c.industry, c.city, c.created_at, c.updated_at,
           (SELECT COUNT(*) FROM applications a WHERE a.company_id = c.id) as app_cnt,
           (SELECT MAX(a.created_at) FROM applications a WHERE a.company_id = c.id) as last_app
    FROM companies c
    WHERE c.priority IN ('S', 'A')
    ORDER BY c.id ASC
""")
rows = [dict(r) for r in cur.fetchall()]

# Last reviewed dates threshold:
# Today is 2026-08-23
# Recent 3 days = 20, 21, 22, 23
recent_days = {20, 21, 22, 23}

# Check history of rotation:
# Batch 2026-08-19: [540, 600, 619, 722, 768]
# Batch 2026-08-20: [770, 771, 772, 773, 774]
# Batch 2026-08-22: [775, 776, 777, 779, 783]
# Notice the sequence: 770-774 -> 775-783 -> NEXT IS 784+ !
# Let's check companies with id >= 784:
candidates_after_783 = []
for r in rows:
    if r['id'] >= 784:
        sr = r['score_reason'] or ""
        m = re.findall(r'2026-08-(\d{2})', sr)
        last_sr_day = max([int(x) for x in m]) if m else 0
        if last_sr_day not in recent_days:
            candidates_after_783.append(r)

print(f"Candidates with ID >= 784: {len(candidates_after_783)}")
for c in candidates_after_783:
    print(c['id'], c['priority'], c['name'], c['industry'], c['city'])

# If candidates_after_783 has companies, let's see which ones.
# 784: 首形科技（AheadForm）
# 785: 卡特彼勒（Caterpillar）
# 786: 航天智能科技研究院（航天科工）
# 787: 字节跳动（ByteDance） (sr has 2026-08-10, so not in recent_days!)
# 788: 深圳市元启姝辰科技有限公司
# 789: 中国长征火箭有限公司
# 790: 伽利略（天津）技术有限公司
# 791: 地平线（Horizon Robotics） (sr has 2026-08-17)
# 792: 强脑科技（BrainCo）
# (Note: 793, 794, 795 were added on 2026-08-19/20 and have 20 in score_reason)

# Let's also check if we need 5 companies, we can pick the first 5 in ascending order from 784+:
# [784, 785, 786, 787, 788] or [784, 785, 786, 788, 789] etc.

selected = candidates_after_783[:5]

# For each selected company, fetch applications and full details
for c in selected:
    cur.execute("SELECT id, position, status, match_score, source_url, created_at, job_desc, agent_reason FROM applications WHERE company_id = ? ORDER BY id DESC", (c['id'],))
    c['applications'] = [dict(a) for a in cur.fetchall()]

with open("career-tracker/scripts/selected_5_midnight_20260823.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)

print("\n--- SELECTED 5 TARGET COMPANIES FOR 2026-08-23 MIDNIGHT REVIEW ---")
for c in selected:
    print(f"ID {c['id']:<4} [{c['priority']}] {c['name']:<35} ({c['industry']} | {c['city']}) Apps: {len(c['applications'])}")

conn.close()
