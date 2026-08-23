import sqlite3
import json
import glob
import os

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, name, city, industry, priority, score, score_reason
    FROM companies
    WHERE priority IN ('S', 'A')
    ORDER BY priority DESC, score DESC, id ASC
""")
sa_companies = [dict(r) for r in cur.fetchall()]

jobs_dir = r"D:/DJTU/HermesWorkspace/jobs"
files = glob.glob(os.path.join(jobs_dir, "面经*.md"))
recent_dates = [f"202608{d:02d}" for d in range(16, 24)]
recent_files = [f for f in files if any(d in f for d in recent_dates)]

file_contents = {}
for rf in recent_files:
    with open(rf, "r", encoding="utf-8", errors="ignore") as f:
        file_contents[os.path.basename(rf)] = f.read()

covered_map = {}
for comp in sa_companies:
    name = comp['name']
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
    if "宇树" in name: alias_list.append("Unitree")
    if "普渡" in name: alias_list.append("Pudu")
    if "首形" in name: alias_list.append("AheadForm")
    if "蓝箭" in name: alias_list.append("LandSpace")

    for fname, content in file_contents.items():
        if any(a in content for a in alias_list):
            if comp['id'] not in covered_map:
                covered_map[comp['id']] = []
            covered_map[comp['id']].append(fname)

uncovered = [c for c in sa_companies if c['id'] not in covered_map]

res = {
    "total_sa_count": len(sa_companies),
    "covered_count": len(covered_map),
    "uncovered_count": len(uncovered),
    "all_sa_companies": sa_companies,
    "covered_map": covered_map,
    "uncovered_companies": uncovered
}

with open(r"D:/DJTU/HermesWorkspace/career-tracker/data/uncovered_analysis.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
