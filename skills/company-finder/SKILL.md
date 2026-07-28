---
name: "company-finder"
description: "Fetches company info from the web and fills JHTracker's database. Invoke when user asks to find/search companies, expand the company list, or fill the database for a given industry/city/job role. Supports multiple search backends. Writes results to both SQLite DB and Markdown archive. Platform-agnostic — works with Trae / Claude Code / Cursor / Codex / any AI agent."
---

# Company Finder Skill

This skill drives JHTracker's AI-powered company database. The agent calls this skill to deep-search the web for companies matching the candidate's profile, then writes results to both the SQLite DB and a Markdown archive in `career_data/`.

**Platform-agnostic**: works with any AI agent that supports skills (Trae, Claude Code, Cursor, Codex, etc.). Use whatever web-search tool your platform provides.

## When to Invoke

Trigger this skill when the user says any of:
- "帮我找XX行业的公司" / "搜索机器人公司" / "补充公司库"
- "find companies in <industry>" / "search for <role> companies"
- "填充数据库" / "expand the company list"
- User mentions an industry + city + job role combo that maps to company sourcing

## Prerequisites

Before running, ensure these exist (create if missing):
- `data/tracker.db` — SQLite database (run `python app.py` once to initialize)
- `data/profile.md` — Candidate profile (copy from `prompts/profile.example.md`)
- A web-search tool available on your agent platform (see Step 3)

## Workflow

### Step 1: Gather intent

Ask the user (or infer from their message) for:
1. **Industry** — e.g. 机器人 / 3D打印 / 工业自动化 (multi-select ok)
2. **City** — e.g. 深圳 / 上海 / 北京 (multi-select ok, default: from `data/profile.md`)
3. **Job role** — e.g. 自动化工程师 / 嵌入式工程师 (default: from `data/profile.md`)

### Step 2: Load candidate profile

Read `data/profile.md`. If missing, ask the user to create it first (point to `prompts/profile.example.md`).

### Step 3: Search the web

For each target industry, run 2-3 targeted searches. Use whatever web-search tool your agent platform provides:

| Platform | Tool to use |
|---|---|
| Trae | `WebSearch` built-in, or Exa MCP (`mcp_Exa` → `web_search_exa` + `web_fetch_exa`) |
| Claude Code | `WebSearch` / `WebFetch` |
| Cursor | `@web` command |
| Codex | web_search tool |
| Other | Any web search / fetch capability |

**Search query patterns** (run at least 2 per industry):
- `{industry} 公司 招聘 {job_role} {city} 2026 校招`
- `{industry} 龙头企业 2026 校招 自动化 嵌入式`
- `{industry} 细分领域 隐形冠军 招聘 控制`

For promising results, fetch the page content to extract: company name, sub-industry, city, job role, and craft a match reason referencing the candidate's skills.

### Step 4: Extract & dedupe companies

From the search results, extract:
- Company name (full name, e.g. "汇川技术" not "汇川")
- Sub-industry (细分行业)
- City (multiple cities joined by `/`)
- Job role (岗位方向)
- Match reason (一句话匹配理由, referencing candidate's specific skills)
- Website (optional)

**Dedup against existing DB**:
```bash
python scripts/fetch_and_import.py --check-existing
```
This prints existing company names as JSON. Skip duplicates.

**Dedup heuristics**:
- Normalize names: strip `有限公司/股份/集团/科技/（中国）`
- Substring match: if new name is substring of existing or vice versa, skip

### Step 5: Write to DB + Markdown archive

Build a JSON array and pass it to the import script:
```bash
python scripts/fetch_and_import.py --input /tmp/companies.json
# Or via stdin:
echo '[...]' | python scripts/fetch_and_import.py --stdin
```

JSON format:
```json
[
  {
    "name": "汇川技术",
    "industry": "工业自动化",
    "sub_industry": "工控自动化",
    "city": "深圳",
    "job_type": "自动化/机电",
    "match_reason": "伺服系统市占率第一，候选人PID控制经验与伺服驱动技术高度匹配",
    "website": "https://www.inovance.com"
  }
]
```

The script will:
1. Insert into `companies` table (skip existing)
2. Append to `career_data/企业清单_AI_<industry>_<date>.md` as Markdown table
3. Print a JSON summary: `{added, skipped, failed, archive_files}`

### Step 6: Ask about AI scoring (do NOT auto-run)

After import, ask the user:
> 已新增 X 家公司。是否运行 AI 评分对它们打分？（需要 ANTHROPIC_API_KEY 或 OPENAI_API_KEY）

If yes:
```bash
python scripts/ai_scorer.py
```
If no API key configured, the script degrades to keyword-only scoring.

## Key Rules

- **NEVER** auto-trigger AI scoring — always ask first
- **NEVER** overwrite existing companies — only insert new ones
- **ALWAYS** save a Markdown archive alongside DB write (for audit/re-import)
- **ALWAYS** dedupe before insert (both against DB and against this run's results)
- If `data/profile.md` is missing, stop and ask user to create it first
- Company names must use **full names** (汇川技术 not 汇川)
- Cities only from candidate's target list (read from profile.md)
- Match reasons must reference candidate's **specific skills** (not generic praise)

## Output Format (Markdown archive)

The archive file `career_data/企业清单_AI_<industry>_<YYYYMMDD>.md` should look like:

```markdown
# AI 检索公司清单 - <industry>

> 生成时间：2026-07-28
> 数据来源：<search backend>
> 候选人画像：data/profile.md

---

## 一、<industry>（共X家）

| 序号 | 公司名称 | 细分行业 | 城市 | 岗位方向 | 匹配理由 |
|:---:|:---------|:---------|:-----|:---------|:---------|
| 1 | **公司全称** | 细分领域 | 城市 | 岗位 | 匹配理由 |
```

## Error Handling

- If `data/tracker.db` doesn't exist → tell user to run `python app.py` first
- If `data/profile.md` doesn't exist → tell user to copy `prompts/profile.example.md`
- If search backend returns 0 results → try alternative query patterns, then report
- If DB write fails (e.g. duplicate) → skip and continue, report at end
- If `fetch_and_import.py` fails → show error, suggest running `python app.py` to init DB

## Example Invocation

User: "帮我找一些机器人行业的公司，深圳上海的"

Agent should:
1. Read `data/profile.md` to understand candidate background
2. Pick search backend (use whatever web-search tool your platform provides)
3. Run searches: "机器人 公司 招聘 自动化 深圳 2026 校招", "机器人 龙头企业 上海 招聘 嵌入式"
4. Fetch promising URLs for details
5. Extract ~10-20 companies, dedupe against DB
6. Write `companies.json` to temp file
7. Run `python scripts/fetch_and_import.py --input /tmp/companies.json`
8. Report: "已新增 15 家机器人公司，存档到 career_data/企业清单_AI_机器人_20260728.md"
9. Ask: "是否运行 AI 评分？"
