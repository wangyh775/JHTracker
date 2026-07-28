---
name: career-tracker-scorer
description: "Scores companies in JHTracker's database against the candidate profile. Invoke when user asks to score/rate companies, run AI scoring, or says 评分/打分/重新评分/score companies. Reads data/profile.md + companies table, calls LLM in batches, writes scores back to DB. Platform-agnostic — works with Trae / Claude Code / Cursor / Codex / any AI agent."
---

# Career Tracker Scorer Skill

This skill drives JHTracker's AI-powered company scoring. The agent reads the candidate profile (`data/profile.md`) and the `companies` table, calls an LLM in batches to score each company's match, and writes results back to the DB.

**Platform-agnostic**: works with any AI agent that can read/write files and call an LLM. No Flask route is involved — the skill runs entirely in the agent's tool space.

## When to Invoke

Trigger this skill when the user says any of:
- "给公司评分" / "AI 评分" / "重新评分" / "打分"
- "score companies" / "rate companies" / "run AI scoring"
- User mentions they updated their profile and want to re-score
- User mentions specific companies need scoring

## Prerequisites

Before running, ensure these exist (create if missing):
- `data/tracker.db` — SQLite database (run `python app.py` once to initialize)
- `data/profile.md` — Candidate profile (use the `career-tracker-profile` skill to generate, or copy from `prompts/profile.example.md`)
- An LLM available on your agent platform

## Workflow

### Step 1: Verify profile exists

```python
import os
PROFILE = os.path.join(os.getcwd(), 'data', 'profile.md')
if not os.path.exists(PROFILE):
    print("❌ 未找到 data/profile.md。请先对智能体说「解析我的简历生成画像」")
    raise SystemExit(1)
with open(PROFILE, 'r', encoding='utf-8') as f:
    profile = f.read().strip()
if not profile:
    print("❌ profile.md 为空")
    raise SystemExit(1)
print(f"✅ 画像已加载 ({len(profile)} 字符)")
```

### Step 2: Determine scoring scope

Ask the user (or infer from their message):
- **增量评分**（默认）：只评 `score IS NULL` 的公司 — 用户说"评分新公司"
- **全量重评**：重评所有公司 — 用户说"重新评分所有"
- **单公司重评**：只评指定 ID — 用户说"重新评 {公司名}"

Query the DB to find target companies:

```python
import sqlite3
DB = os.path.join(os.getcwd(), 'data', 'tracker.db')
conn = sqlite3.connect(DB)
c = conn.cursor()

# 增量（默认）
c.execute("SELECT id,name,industry,job_type,city,priority,match_reason,tags FROM companies WHERE score IS NULL")
# 全量重评：去掉 WHERE 子句
# 单公司：WHERE id = ?

rows = c.fetchall()
columns = ['id','name','industry','job_type','city','priority','match_reason','tags']
companies = [dict(zip(columns, r)) for r in rows]
print(f"📊 待评分公司: {len(companies)} 家")
```

### Step 3: Stage 1 — Keyword prefilter (free, no LLM)

Apply deal-breaker keywords to instantly score obvious mismatches as 0:

```python
DEAL_BREAKERS = [
    '实习','intern','管培','保险','销售','客服','运营','市场','行政',
    'hr','人力','财务','会计','法务','前端','大数据','测试开发',
    '产品经理','数据分析','java','go语言','web前端','ui设计',
]

def prefilter(job_type, match_reason):
    text = f"{job_type or ''} {match_reason or ''}".lower()
    for w in DEAL_BREAKERS:
        if w in text:
            return 0, f"排除词触发: {w}"
    return None, None  # None 表示需要 LLM 评分

prefiltered = {}
to_llm = []
for comp in companies:
    score, reason = prefilter(comp['job_type'], comp['match_reason'])
    if score is not None:
        prefiltered[comp['id']] = (score, reason)
    else:
        to_llm.append(comp)
print(f"  预筛淘汰: {len(prefiltered)} 家 | 进入 LLM: {len(to_llm)} 家")
```

### Step 4: Stage 2 — LLM batch scoring

Score remaining companies in batches of 15 (one LLM call per batch, saves 90%+ tokens vs. one-by-one).

**Prompt template** (build the companies block, then call LLM once per batch):

```
你是一位专业的工科求职顾问。对每家公司从以下维度评估匹配度，给出 0-100 的综合评分：
1. 核心技能匹配 (40分)
2. 行业相关度 (20分)
3. 职能契合度 (25分)
4. 成长空间 (15分)

## 候选人简历
{profile}

## 待评估公司清单（共 {n} 家）
{companies_block}

请严格按以下 JSON 数组格式输出，不要输出其他内容：
[
  {"id": 1, "score": 75, "reason": "匹配理由（20字内）", "missing": "缺失项（20字内，可空）"}
]
数组长度必须等于 {n}，id 与输入一致。
```

**Platform-specific LLM calls** — use whatever LLM your agent platform provides:

| Platform | LLM tool |
|---|---|
| Trae | Use the platform's built-in LLM, or Anthropic/OpenAI MCP |
| Claude Code | Use the agent's own Claude model (process inline) |
| Cursor | Use the agent's own model, or call Anthropic/OpenAI API |
| Codex / other | Call Anthropic/OpenAI API directly |

For API-based calls (OpenAI-compatible):
```python
from openai import OpenAI
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'],
                base_url=os.environ.get('AI_BASE_URL'))  # optional
resp = client.chat.completions.create(
    model=os.environ.get('AI_MODEL', 'gpt-4o-mini'),
    max_tokens=2000,
    messages=[
        {"role":"system","content":"你是一个求职匹配评估助手。严格输出 JSON 数组。"},
        {"role":"user","content": prompt}
    ]
)
text = resp.choices[0].message.content
```

**Parse the JSON array** from LLM response:
```python
import json
start = text.find('[')
end = text.rfind(']') + 1
scores = json.loads(text[start:end])  # [{id, score, reason, missing}, ...]
```

**Key rules**:
- If LLM response is missing a company (JSON length < batch size), leave that company's score as NULL — it will be retried next run
- Do NOT assign default 50 to LLM failures — keep NULL so next incremental run picks them up
- Batch size 15 balances token cost vs. reliability (larger batches risk LLM truncating JSON)

### Step 5: Write scores back to DB

```python
cursor = conn.cursor()
for comp in to_llm:
    cid = comp['id']
    match = next((s for s in scores if s['id'] == cid), None)
    if match:
        score = match['score']
        reason = match['reason']
        missing = match.get('missing', '')
        full_reason = f"{reason}" + (f" | 缺: {missing}" if missing else "")
        cursor.execute("UPDATE companies SET score=?, score_reason=? WHERE id=?",
                       (score, full_reason, cid))
    else:
        # LLM 漏掉了这家，保持 NULL，下次重试
        cursor.execute("UPDATE companies SET score_reason=? WHERE id=?",
                       ("LLM 评分失败，下次重试", cid))

# 写入预筛结果
for cid, (score, reason) in prefiltered.items():
    cursor.execute("UPDATE companies SET score=?, score_reason=? WHERE id=?",
                   (score, reason, cid))
conn.commit()
conn.close()
print(f"✅ 完成！LLM 评分 {len(scores)} 家，预筛淘汰 {len(prefiltered)} 家")
```

### Step 6: Report results

After writing, summarize:
- Total scored / prefiltered / failed
- Score distribution (e.g. "高匹配 85+: 12 家 | 中匹配 60-85: 45 家 | 低匹配 <60: 8 家")
- Sample top 3: name + score + reason
- Failed count (if any) — tell user these will auto-retry next incremental run

## Key Rules

- **ALWAYS** read `data/profile.md` first — if missing, stop and ask user to generate profile via the `career-tracker-profile` skill
- **ALWAYS** batch LLM calls (15 companies per batch) to save tokens
- **NEVER** assign default 50 to LLM failures — keep score NULL for auto-retry
- **NEVER** overwrite existing scores unless user explicitly says "重新评分" / "rescore all"
- **ALWAYS** run keyword prefilter (Stage 1) before LLM — saves tokens on obvious mismatches
- Profile content is included once per batch (not per company) — that's the main token saving
- If profile changed since last scoring, re-score all; otherwise only score NULL companies

## Scope Modes

| Mode | When to use | SQL filter |
|---|---|---|
| 增量 (incremental) | User says "评分" / "score" | `WHERE score IS NULL` |
| 全量重评 (rescore all) | User says "重新评分所有" / "rescore all" | (no filter) |
| 单公司 (single) | User says "重新评 {公司名}" | `WHERE id = ?` |

## Error Handling

- `data/profile.md` missing → tell user to run `career-tracker-profile` skill first
- `data/tracker.db` missing → tell user to run `python app.py` once to init
- LLM API key missing → tell user to set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`
- LLM call fails (network/quota/auth) → report error, keep failed companies' scores as NULL
- LLM returns truncated JSON (fewer items than batch) → keep missing ones NULL for retry
- `openai`/`anthropic` library not installed → `pip install -r requirements-ai.txt`

## Example Invocation

User: "给公司评分"

Agent should:
1. Read `data/profile.md` → confirm loaded
2. Query DB for `score IS NULL` companies → e.g. 23 pending
3. Run keyword prefilter → e.g. 3 eliminated, 20 to LLM
4. Split 20 into 2 batches (15 + 5), call LLM twice
5. Parse JSON, write scores to DB
6. Report: "✅ 评分 20 家，预筛淘汰 3 家。高匹配 85+: 5 家 | 中匹配: 12 家 | 低匹配: 3 家"
7. If any failed: "⚠️ 2 家 LLM 评分失败，下次评分会自动重试"

## Install Dependencies (one-time)

```bash
pip install -r requirements-ai.txt
# 或：pip install openai  # OpenAI 兼容接口
# 或：pip install anthropic  # Anthropic Claude
```
