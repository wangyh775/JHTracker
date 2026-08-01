---
name: "tracker-ops"
description: "Handles database operations, company deduplication, batch data import, application archiving, and system maintenance. Alias: career-tracker-ops, career-tracker-import."
allowed-tools:
  - JHTracker:create_note
  - JHTracker:list_notes
  - JHTracker:update_note
  - JHTracker:delete_note
  - JHTracker:create_timeline_event
  - JHTracker:list_timeline_events
  - JHTracker:toggle_timeline_event
  - JHTracker:list_agent_tasks
  - JHTracker:get_agent_task
  - JHTracker:clear_agent_traces
  - JHTracker:notify_db_changed
  - JHTracker:get_statistics
---

# Tracker Operations Skill

Provides maintenance and operations utilities for JHTracker, including database health checks, deduplication, batch imports, and application archiving.

## Trigger Scenarios

Invoke when the user says any of:
- "查看数据库统计" / "检查重复公司" / "数据去重"
- "批量导入公司/岗位数据" / "导入 CSV"
- "运行应用归档" / "清理停滞投递"
- "database stats" / "run archiving script"

## Key Operations & CLI Commands

### 1. Database Health & Statistics
```bash
python -c "
import sqlite3
c = sqlite3.connect('data/tracker.db').cursor()
c.execute('SELECT COUNT(*) FROM companies'); print('Companies:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM applications WHERE is_archived = 0'); print('Active Apps:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM applications WHERE is_archived = 1'); print('Archived Apps:', c.fetchone()[0])
"
```

### 2. Application Auto-Archiving
Preview stale applications (> 15 days inactive):
```bash
python scripts/archive_applications.py --dry-run
```
Execute archiving:
```bash
python scripts/archive_applications.py
```

### 3. Batch Data Import
Run batch fetch or import scripts in `scripts/` or `data/`:
```bash
python scripts/fetch_and_import.py
```
