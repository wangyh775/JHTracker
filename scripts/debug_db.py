"""Debug the career-tracker DB: check priority sort, salary data, and source info."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use raw sqlite3 to avoid Flask app context issues
import sqlite3

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tracker.db')
print(f"DB path: {db_path}")
print(f"DB exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# List tables
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"\nTables: {[t['name'] for t in tables]}")

# Company table
try:
    c2 = c.execute("SELECT priority, name, salary_min, salary_max, website FROM companies ORDER BY priority, name").fetchall()
    print(f"\nCompany count: {len(c2)}")
    from collections import Counter
    prios = Counter(row['priority'] for row in c2)
    print(f"Priority distribution: {dict(prios)}")
    null_sal = sum(1 for row in c2 if row['salary_min'] is None and row['salary_max'] is None)
    print(f"Null salary: {null_sal} / {len(c2)}")
    print("\nFirst 8:")
    for row in c2[:8]:
        print(f"  {row['priority']} | {row['name']} | {row['salary_min']}-{row['salary_max']} | {row['website']}")
    print("\nLast 8:")
    for row in c2[-8:]:
        print(f"  {row['priority']} | {row['name']} | {row['salary_min']}-{row['salary_max']} | {row['website']}")
    # S priority specifically
    s_rows = [row for row in c2 if row['priority'] == 'S']
    print(f"\nS priority count: {len(s_rows)}")
    for row in s_rows:
        print(f"  {row['priority']} | {row['name']} | {row['salary_min']}-{row['salary_max']} | {row['website']}")
except Exception as e:
    print(f"Error: {e}")

# Application table
try:
    apps = c.execute("SELECT id, company_id, position, channel, url, salary_min, salary_max FROM applications LIMIT 10").fetchall()
    print(f"\nApplication count: {len(c.execute('SELECT COUNT(*) FROM applications').fetchone()[0])}")
    print("Sample apps:")
    for a in apps:
        print(f"  id={a['id']} | company_id={a['company_id']} | {a['position']} | ch={a['channel']} | url={a['url']} | {a['salary_min']}-{a['salary_max']}")
except Exception as e:
    print(f"Apps error: {e}")

conn.close()