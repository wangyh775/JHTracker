import sqlite3
import json
import os
import glob

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, name, city, industry, priority, score, score_reason, website
    FROM companies
    WHERE priority IN ('S', 'A')
    ORDER BY priority DESC, score DESC, id ASC
""")
sa_companies = [dict(r) for r in cur.fetchall()]

# Recent files (past 7 days: 20260816 to 20260823)
jobs_dir = r"D:/DJTU/HermesWorkspace/jobs"
files = glob.glob(os.path.join(jobs_dir, "面经*.md"))
recent_dates = [f"202608{d:02d}" for d in range(16, 24)]
recent_files = [f for f in sorted(files) if any(d in f for d in recent_dates)]

file_contents = {}
for rf in recent_files:
    with open(rf, "r", encoding="utf-8", errors="ignore") as f:
        file_contents[os.path.basename(rf)] = f.read()

print(f"Total S/A companies in DB: {len(sa_companies)}")
print(f"Recent 面经 files found: {list(file_contents.keys())}")

report = []
for c in sa_companies:
    cid = c['id']
    name = c['name']
    prio = c['priority']
    score = c['score']
    
    # check if mentioned in recent files
    covered_in = []
    for fname, content in file_contents.items():
        # Check substrings
        short_name = name.split("（")[0].split("(")[0].strip()
        if len(short_name) >= 2 and short_name in content:
            covered_in.append(fname)
        elif name in content:
            covered_in.append(fname)
    
    report.append({
        "id": cid,
        "name": name,
        "priority": prio,
        "score": score,
        "city": c['city'],
        "industry": c['industry'],
        "covered_in": covered_in,
        "is_covered": len(covered_in) > 0
    })

with open("D:/DJTU/HermesWorkspace/career-tracker/data/sa_coverage_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

uncovered = [r for r in report if not r['is_covered']]
covered = [r for r in report if r['is_covered']]

print(f"\nSummary:")
print(f"Covered count: {len(covered)}")
print(f"Uncovered count: {len(uncovered)}")
print("\nUncovered companies:")
for u in uncovered:
    print(f"[{u['priority']}] ID: {u['id']} - {u['name']} (Score: {u['score']}, {u['industry']}, {u['city']})")
