import sqlite3
import json
import os
import glob
from datetime import datetime

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all S and A companies
cur.execute("""
    SELECT id, name, priority, score, city, status, score_reason, updated_at, created_at
    FROM companies
    WHERE priority IN ('S', 'A')
    ORDER BY priority DESC, score DESC, id ASC
""")
sa_companies = [dict(r) for r in cur.fetchall()]
print(f"Total S/A companies found: {len(sa_companies)}")

# Check jobs directory files
jobs_dir = r"D:/DJTU/HermesWorkspace/jobs"
files = glob.glob(os.path.join(jobs_dir, "面经*.md"))
print(f"Found {len(files)} 面经 files:")
for f in sorted(files):
    print(" -", os.path.basename(f))

# Let's inspect which companies are covered in files within the past 7 days (today is 2026-08-23, past 7 days is 2026-08-16 to 2026-08-23)
recent_files = [f for f in files if any(f"202608{d:02d}" in f for d in range(16, 24))]
print(f"\nRecent files (2026-08-16 to 2026-08-23):")
covered_companies = set()
for rf in recent_files:
    fname = os.path.basename(rf)
    with open(rf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    print(f"\nFile: {fname} (length: {len(content)})")
    for comp in sa_companies:
        name = comp['name']
        short_name = name.split("（")[0].split("(")[0].strip()
        if name in content or short_name in content:
            covered_companies.add(comp['name'])
            print(f"   Covered: [{comp['priority']}] {comp['name']}")

print("\n=== S/A Companies Coverage Summary ===")
uncovered = []
for comp in sa_companies:
    is_cov = comp['name'] in covered_companies
    print(f"[{comp['priority']}] ID:{comp['id']:<3} {comp['name']:<35} Score:{comp['score']} Covered_in_last_week:{is_cov}")
    if not is_cov:
        uncovered.append(comp)

print(f"\nTotal uncovered S/A companies: {len(uncovered)}")
for u in uncovered:
    print(f" -> [{u['priority']}] ID:{u['id']} {u['name']} (Score: {u['score']})")

with open("career-tracker/scripts/uncovered_sa_companies.json", "w", encoding="utf-8") as f:
    json.dump(uncovered, f, ensure_ascii=False, indent=2)
