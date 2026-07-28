---
name: career-tracker-ops
description: "Core operational skill for JHTracker (Job Hunt Tracker). Use this when the user asks to manage the database, deduplicate companies, import new data, run AI scoring, enrich salaries/websites, or troubleshoot the Flask application. Provides standardized workflows for all scripts in the `scripts/` directory."
---

# Career Tracker Ops Skill

This is the core operational skill for managing the JHTracker application database and executing its batch scripts. 

**Platform-agnostic**: Works with any AI agent that can run local Python scripts (Hermes, Trae, Claude Code, Cursor, Codex).

## 1. When to use

Trigger this skill when the user asks to:
- "去重" / "合并公司" / "Clean up duplicates"
- "更新薪资" / "Enrich salary data"
- "补全官网" / "Find missing websites"
- "重新打分" / "Run AI scoring"
- "合并行业" / "Consolidate industries"
- "启动服务" / "Run the app"
- Fix database schema issues or perform bulk updates.

## 2. Standard Workflows

All scripts are located in the `scripts/` directory. **Always run them from the project root**, not from inside the `scripts/` folder.

### 2.1 AI Scoring (`ai_scorer.py`)
Scores companies based on the candidate's profile (`data/profile.md`).
```bash
# Score only companies with NULL score
python scripts/ai_scorer.py

# Force re-score ALL companies (costly, ask first)
python scripts/ai_scorer.py --force

# Score a specific company
python scripts/ai_scorer.py --company-id <ID>
```
*Note: Requires `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the `.env` file. If missing, the script gracefully degrades to keyword-only pre-filtering.*

### 2.2 Deduplication (`dedup_companies.py`)
Finds and merges duplicate company entries (e.g. "大疆" vs "大疆创新").
```bash
# Dry-run: Just list potential duplicates
python scripts/dedup_companies.py --dry-run

# Execute merge (always run dry-run first and ask user!)
python scripts/dedup_companies.py
```
*Rules:* 
1. Strips parenthesis like `(中国)` or `（集团）` before comparing.
2. Keeps the record with more complete data (website, salary, etc.) and migrates foreign keys (applications, notes) before deleting the duplicate.

### 2.3 Industry Consolidation (`merge_industries.py`)
Reduces 100+ granular industry tags (e.g. "金属3D打印") into 13 major buckets (e.g. "3D打印").
```bash
python scripts/merge_industries.py
```

### 2.4 Website Enrichment (`enrich_website.py`)
Fills in missing company websites by searching the web.
```bash
python scripts/enrich_website.py
```
*Pitfall Warning:* Do NOT fill Boss Zhipin search URLs (`zhipin.com/web/geek/job?query=...`) or generic corporate homepages if a specific career portal exists.

### 2.5 Salary Enrichment (`enrich_salary.py`)
Extracts salary brackets (`salary_min`, `salary_max`) from `match_reason` or searches the web for 2026/2027 campus recruitment data for S/A priority companies.
```bash
python scripts/enrich_salary.py
```

### 2.6 Daily Sourcing Cron (`daily_new_company_finder.py`)
Meant to be run via a cron job, but can be triggered manually. Searches the web for new companies matching the candidate's profile and inserts them.
```bash
python scripts/daily_new_company_finder.py
```

## 3. Database Rules (SQLite)

The database is at `data/tracker.db`.

1. **Priority Ordering**: Priority is `S > A > B > C`. Do not sort alphabetically (`ORDER BY priority` puts S last). Use:
   ```sql
   ORDER BY CASE priority WHEN 'S' THEN 0 WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 ELSE 4 END
   ```
2. **Schema Changes**: If you need to add a column, `ALTER TABLE` in SQLite is limited. Use raw SQL:
   ```python
   c.execute('ALTER TABLE companies ADD COLUMN new_col VARCHAR(50)')
   ```
3. **Company Types**: The `company_type` field uses standard labels: `民企`, `央企`, `国企`, `合资`, `外企-美国`, `外企-德国`, `外企-日本` etc.

## 4. Troubleshooting the Flask App

If the app crashes or the user reports an error on `http://127.0.0.1:5000`:
1. Check the logs in the terminal running `app.py`.
2. Verify `data/tracker.db` exists. If not, running `python app.py` will auto-create it via `db.create_all()`.
3. Check `routes/` for blueprint errors.
4. Check `templates/` for Jinja2 syntax errors.

To start the app for the user:
```bash
python app.py
```
*(Runs on port 5000 in debug mode).*
