---
name: career-tracker-ops
description: "Operational tasks for JHTracker. Invoke when user says '查看数据库统计', '去重/检查重复公司','合并行业','启动应用','重启','备份恢复','修复/维护', or mentions database health."
---

# Career Tracker Operations Skill

Handles maintenance tasks for JHTracker.

## When to Invoke

- Database stats/config queries
- Deduplication of company entries
- Industry/priority/salary cleanup
- Start/restart application
- Application archive (auto/manual/preview)
- General health check

## Prerequisites

Running from the project root: `cd /path/to/career-tracker`

## Common Operations

### Database stats
```bash
python -c "
import sqlite3
c = sqlite3.connect('data/tracker.db').cursor()
# Total companies
c.execute('SELECT COUNT(*) FROM companies'); print('Companies:', c.fetchone()[0])
# Active vs archived applications
c.execute('SELECT COUNT(*) FROM applications WHERE is_archived = 0'); print('Active apps:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM applications WHERE is_archived = 1'); print('Archived apps:', c.fetchone()[0])
# By priority
c.execute('SELECT priority, COUNT(*) FROM companies GROUP BY priority ORDER BY priority')
print('Priority:', c.fetchall())
# By industry
c.execute('SELECT industry, COUNT(*) FROM companies GROUP BY industry ORDER BY COUNT(*) DESC LIMIT 10')
print('Industry:', c.fetchall())
# Scored vs unscored
c.execute('SELECT COUNT(*) FROM companies WHERE score IS NULL'); print('Unscored:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM companies WHERE score IS NOT NULL'); print('Scored:', c.fetchone()[0])
"
```

### Application archive

Preview stale applications (no DB changes):
```bash
python scripts/archive_applications.py --dry-run
```

Run archive with default threshold (15 days):
```bash
python scripts/archive_applications.py
```

Custom threshold:
```bash
python scripts/archive_applications.py --days 30
```

Restore a single record:
```bash
python scripts/archive_applications.py --unarchive 5
```

### Start Flask server
```bash
python app.py
```

### Dedup by name normalization
```bash
python -c "
import sqlite3, re
c = sqlite3.connect('data/tracker.db').cursor()
c.execute('SELECT id, name FROM companies ORDER BY name')
all_rows = c.fetchall()

def norm(n):
    n = re.sub(r'(有限公司|股份|集团|科技|（.*?）|\(.*?\))$', '', n)
    return n.strip()

seen = {}
dups = []
for id, name in all_rows:
    key = norm(name)
    if key in seen:
        dups.append((id, name, seen[key]))
    else:
        seen[key] = name
if dups:
    for id, name, orig in dups:
        print(f'  DELETE id={id} \"{name}\" — check against \"{orig}\"')
else:
    print('No obvious duplicates found')
"
```
