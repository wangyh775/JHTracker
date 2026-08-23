import sys
import os
import json
import sqlite3
import glob

sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")
from mcp_server import search_companies, get_db_connection

# Step 1: Query all companies with priority S or A
conn = get_db_connection()
cur = conn.cursor()
cur.execute("""
    SELECT id, name, city, industry, priority, score, score_reason
    FROM companies
    WHERE priority IN ('S', 'A')
    ORDER BY priority DESC, score DESC, id ASC
""")
sa_companies = [dict(r) for r in cur.fetchall()]
print(f"Total S/A companies in DB: {len(sa_companies)}")

# Step 2: Check all interview files in jobs/ from 2026-08-16 to 2026-08-23 (past 7 days)
jobs_dir = r"D:/DJTU/HermesWorkspace/jobs"
files = glob.glob(os.path.join(jobs_dir, "面经*.md"))
recent_dates = [f"202608{d:02d}" for d in range(16, 24)]
recent_files = [f for f in files if any(d in f for d in recent_dates)]

print(f"Checking {len(recent_files)} recent interview files (2026-08-16 to 2026-08-23):")
for f in recent_files:
    print(" -", os.path.basename(f))

covered_map = {}
for rf in recent_files:
    fname = os.path.basename(rf)
    with open(rf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    for comp in sa_companies:
        name = comp['name']
        # Also try short names
        short_name = name.split("（")[0].split("(")[0].strip()
        alias_list = [name, short_name]
        if "拓竹" in name: alias_list.append("Bambu")
        if "快造" in name: alias_list.append("Snapmaker")
        if "地瓜" in name: alias_list.append("Diguarobotics")
        if "瑞芯微" in name: alias_list.append("Rockchip")
        if "18所" in name or "十八所" in name: alias_list.extend(["18所", "十八所", "精密机电控制设备研究所"])
        if "汇川" in name: alias_list.append("汇川")
        if "雷赛" in name: alias_list.append("雷赛")
        if "魔芯" in name: alias_list.append("魔芯")
        if "智元" in name: alias_list.append("Agibot")
        if "中望" in name: alias_list.append("ZWSOFT")
        if "国望" in name: alias_list.append("国望")
        if "华曙" in name: alias_list.append("Farsoon")
        if "铂力特" in name: alias_list.append("BLT")

        matched = False
        for a in alias_list:
            if a in content:
                matched = True
                break
        if matched:
            if comp['id'] not in covered_map:
                covered_map[comp['id']] = []
            covered_map[comp['id']].append(fname)

print("\n--- All S/A Companies Status ---")
uncovered = []
for c in sa_companies:
    cov = covered_map.get(c['id'], [])
    if cov:
        print(f"ID {c['id']:<3} [{c['priority']}] {c['name']:<35} (Score {c['score']}) -> Covered in: {', '.join(cov)}")
    else:
        print(f"ID {c['id']:<3} [{c['priority']}] {c['name']:<35} (Score {c['score']}) -> [NOT COVERED THIS WEEK]")
        uncovered.append(c)

print(f"\nTotal Uncovered: {len(uncovered)}")

output = {
    "total_sa": len(sa_companies),
    "covered_count": len(covered_map),
    "uncovered_count": len(uncovered),
    "uncovered_companies": uncovered
}

with open("career-tracker/scripts/uncovered_result.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
