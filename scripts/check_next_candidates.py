import sys
import os
sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")
from mcp_server import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Get the candidate profile
with open(r"D:/DJTU/HermesWorkspace/career-tracker/data/profile.md", "r", encoding="utf-8") as f:
    profile_text = f.read()

print("Profile loaded, length:", len(profile_text))

# Let's inspect companies starting from 784 onwards, or starting from ID 2 if we wrapped around
cur.execute("""
    SELECT id, name, priority, score, score_reason, website, industry, city, created_at, updated_at
    FROM companies
    WHERE id >= 784 AND priority IN ('S', 'A')
    ORDER BY id ASC
""")
rows_784_plus = [dict(r) for r in cur.fetchall()]
print(f"Companies with id >= 784: {len(rows_784_plus)}")
for r in rows_784_plus:
    print(r['id'], r['priority'], r['name'], r['industry'], r['city'])

# If we pick 5 companies following 783 (784, 785, 786, 787, 788... or 784, 785, 786, 788, 789 etc.)
# Let's check which ones in 784+ were reviewed in last 3 days
