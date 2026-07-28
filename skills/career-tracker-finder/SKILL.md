---
name: career-tracker-finder
description: "Searches the web for companies matching a candidate profile and imports them into JHTracker's SQLite database. Use this when the user asks to find, search, or expand the company list for a specific industry, city, or job role. Supports web search + deduplication + structured import."
---

# Career Tracker Company Finder Skill

This skill helps the user expand their JHTracker company database by searching the web for employers matching their target industries, cities, and job roles.

**Platform-agnostic**: Works with any AI agent that has web search capability.

## 1. When to use

- "帮我找XX行业的公司" / "搜索机器人公司"
- "Find companies in <industry> for <city>"
- "填充公司库" / "Expand the company database"
- Any request to discover new potential employers

## 2. Prerequisites

- `data/profile.md` must exist (candidate's profile with target industries, cities, job roles)
- `data/tracker.db` must exist (run `python app.py` once to initialize)
- Web search capability on your agent platform

## 3. Workflow

### Step 1: Determine search scope

Read `data/profile.md` to get the candidate's target industries, cities, and job roles.

If the user hasn't specified what to search for, extract from the profile:
- **Industries**: find the `## 求职偏好` section
- **Cities**: find the city preferences
- **Job roles**: find the `## 目标岗位` section

### Step 2: Search the web

Run 2-3 targeted searches per industry. Use your platform's web search tool:

**Search templates** (replace `{industry}` `{city}` `{job_role}`):
```
{industry} 公司 招聘 {job_role} {city} 2026 校招
{industry} 龙头企业 2026 校招 自动化 嵌入式
{industry} 细分领域 隐形冠军 招聘 控制
{industry} companies hiring {job_role} {city} 2026 campus
```

### Step 3: Extract company info

From search results, extract for each company:
- `name` — Full Chinese name (e.g. "汇川技术", not "汇川")
- `industry` — One of: 3D打印, 机器人, 工业自动化, 高端装备, 汽车制造, 半导体, 能源与新能源, 医疗器械, 消费电子, 航空航天, 人工智能/算法, 嵌入式/软件, 轨道交通
- `city` — City or cities (use `/` to separate)
- `job_type` — Job role category (e.g. "控制/嵌入式/自动化", "自动化/机电")
- `match_reason` — One-sentence fit reason referencing the candidate's specific skills
- `website` — URL of the career page (optional, but prefer specific job portal URLs)
- `company_type` — 民企/央企/国企/合资/外企-美国/外企-德国/外企-日本

### Step 4: Deduplicate

Check existing companies in the database:
```bash
python -c "
import sqlite3, json
c = sqlite3.connect('data/tracker.db').cursor()
c.execute('SELECT name FROM companies')
existing = [r[0] for r in c.fetchall()]
print(json.dumps(existing, ensure_ascii=False))
"
```

**Dedup rules**:
1. Normalize: strip `有限公司`, `股份`, `集团`, `科技`, `（中国）`, `(中国)`
2. If normalized name is a substring of an existing name (or vice versa), skip
3. Cross-reference entries (e.g. "大疆创新（DJI）（见机器人章节）") — keep as separate entries

### Step 5: Import into DB

Build a JSON array and import:
```json
[
  {
    "name": "公司全称",
    "industry": "工业自动化",
    "city": "深圳",
    "job_type": "自动化/机电",
    "match_reason": "伺服系统龙头企业，候选人PID控制经验与伺服驱动技术高度匹配",
    "website": "https://www.example.com/campus",
    "company_type": "民企"
  }
]
```

Import via the fetch script:
```bash
echo '[...]' | python scripts/fetch_and_import.py --stdin
```

The script inserts into `companies` table and prints a summary.

### Step 6: Report results

Tell the user exactly what was added:
```
已新增 X 家公司：
- 公司A（行业，城市，岗位）
- 公司B（行业，城市，岗位）
...（仅列出新增的）
```

## 4. Key rules

- **NEVER** overwrite existing companies — only insert new ones
- **ALWAYS** deduplicate before inserting
- Use **full company names** (not abbreviations)
- Match reasons must reference **specific candidate skills** from profile.md, not generic praise
- After import, ask the user if they want to re-run AI scoring
- If the search returns 0 results, try different query patterns or report honestly

## 5. Output archive

The import script automatically saves a Markdown archive to `career_data/企业清单_AI_<industry>_<date>.md` for audit.