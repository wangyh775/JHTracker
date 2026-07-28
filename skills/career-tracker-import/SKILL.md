---
name: career-tracker-import
description: "Imports company lists from Markdown files in career_data/ to the SQLite database. Invoke when user says '导入数据', 'import companies', or adds a new Markdown file and wants it in the DB."
---

# Career Tracker Import Skill

Handles importing company data from Markdown tables into the SQLite database.

## Prerequisites

- `data/tracker.db` — SQLite database
- Markdown files in `career_data/` containing tables with columns: `公司名称`, `细分行业`, `城市`, `岗位方向`, `匹配理由` (optional: `官网链接`, `薪资`)

## Workflow

1. Read Markdown files in `career_data/`
2. Parse Markdown tables (ignoring header rows)
3. Insert into `companies` table using `scripts/fetch_and_import.py` (via JSON) or direct SQL
4. Inform user about skipped duplicates

```bash
# Easy way: Use the built-in script if JSON is available
python scripts/fetch_and_import.py --check-existing
```

Or write direct SQLite insert script if parsing raw Markdown.