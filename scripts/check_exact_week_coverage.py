import sqlite3
import json
import glob
import os

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all S and A priority companies
cur.execute("""
    SELECT id, name, city, industry, priority, score, match_reason, score_reason, website
    FROM companies
    WHERE priority IN ('S', 'A')
    ORDER BY priority DESC, score DESC, id ASC
""")
sa_companies = [dict(r) for r in cur.fetchall()]

jobs_dir = r"D:/DJTU/HermesWorkspace/jobs"
files = glob.glob(os.path.join(jobs_dir, "面经*.md"))

# Week cutoff: past 7 days (2026-08-16 to 2026-08-23)
recent_dates = [f"202608{d:02d}" for d in range(16, 24)]
recent_files = [f for f in sorted(files) if any(d in f for d in recent_dates)]

file_contents = {}
for rf in recent_files:
    with open(rf, "r", encoding="utf-8", errors="ignore") as f:
        file_contents[os.path.basename(rf)] = f.read()

covered_map = {}
for comp in sa_companies:
    name = comp['name']
    short_name = name.split("（")[0].split("(")[0].strip()
    aliases = [name, short_name]
    
    # Specific keywords
    if "宇树" in name: aliases.extend(["宇树", "Unitree"])
    if "中望" in name: aliases.extend(["中望", "ZWSOFT"])
    if "国望" in name: aliases.extend(["国望"])
    if "格见" in name: aliases.extend(["格见"])
    if "普渡" in name: aliases.extend(["普渡", "Pudu"])
    if "首形" in name: aliases.extend(["首形", "AheadForm"])
    if "蓝箭" in name: aliases.extend(["蓝箭", "LandSpace", "鸿擎"])
    if "卡特彼勒" in name: aliases.extend(["卡特彼勒", "Caterpillar"])
    if "航天智能" in name: aliases.extend(["航天智能"])
    if "字节" in name: aliases.extend(["字节跳动", "ByteDance"])
    if "华曙" in name: aliases.extend(["华曙", "Farsoon"])
    if "铂力特" in name: aliases.extend(["铂力特", "BLT"])
    if "大疆" in name: aliases.extend(["大疆", "DJI"])
    if "逐际动力" in name: aliases.extend(["逐际动力", "LimX"])
    if "联合飞机" in name: aliases.extend(["联合飞机"])
    if "502所" in name or "五院502" in name or "北京控制工程研究所" in name: aliases.extend(["502所", "北京控制工程研究所"])
    if "803所" in name or "八院803" in name or "上海航天控制技术研究所" in name: aliases.extend(["803所", "上海航天控制技术研究所"])
    if "星际荣耀" in name: aliases.extend(["星际荣耀", "i-Space"])
    if "英伟达" in name: aliases.extend(["英伟达", "NVIDIA"])
    if "创想三维" in name: aliases.extend(["创想三维", "Creality"])
    if "纵维立方" in name: aliases.extend(["纵维立方", "Anycubic"])
    if "拓竹" in name: aliases.extend(["拓竹", "Bambu"])
    if "快造" in name: aliases.extend(["快造", "Snapmaker"])
    if "汇川" in name: aliases.extend(["汇川", "INOVANCE"])
    if "雷赛" in name: aliases.extend(["雷赛"])
    if "智元" in name: aliases.extend(["智元", "Agibot"])
    if "瑞芯微" in name: aliases.extend(["瑞芯微", "Rockchip"])
    if "18所" in name or "十八所" in name: aliases.extend(["18所", "十八所", "精密机电控制设备研究所"])

    matched_files = []
    for fname, content in file_contents.items():
        if any(a in content for a in aliases):
            matched_files.append(fname)
    
    if matched_files:
        covered_map[comp['id']] = matched_files

uncovered = [c for c in sa_companies if c['id'] not in covered_map]

print(f"Total S/A: {len(sa_companies)}")
print(f"Covered in week ({len(covered_map)}):")
for cid, fnames in covered_map.items():
    c_info = next(c for c in sa_companies if c['id'] == cid)
    print(f"  [{c_info['priority']}] ID:{c_info['id']:<3} {c_info['name']} -> {fnames}")

print(f"\nUncovered in week ({len(uncovered)}):")
for u in uncovered:
    print(f"  [{u['priority']}] ID:{u['id']:<3} {u['name']} (Score: {u['score']}) - {u['industry']}")

with open("career-tracker/data/target_uncovered_report.json", "w", encoding="utf-8") as f:
    json.dump({"covered": covered_map, "uncovered": uncovered}, f, ensure_ascii=False, indent=2)
