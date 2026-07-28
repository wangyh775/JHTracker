---
name: career-tracker-profile
description: "Parses resumes uploaded to JHTracker's 简历版本管理 (Resume table) into a structured candidate profile (data/profile.md). Invoke when user asks to parse/analyze their resume, generate/update their profile, or says 解析简历/生成画像/更新个人信息. Reads the default (or latest) resume from DB, extracts text, calls LLM, writes profile.md. Platform-agnostic — works with Trae / Claude Code / Cursor / Codex / any AI agent."
---

# Career Tracker Profile Skill

This skill drives JHTracker's AI-powered candidate profile. The agent reads a resume uploaded via the 简历版本管理 web UI, extracts its text, calls an LLM to restructure it into the standard profile format, and writes the result to `data/profile.md`.

**Platform-agnostic**: works with any AI agent that can read/write files and call an LLM. No Flask route is involved — the skill runs entirely in the agent's tool space.

## When to Invoke

Trigger this skill when the user says any of:
- "解析我的简历生成画像" / "根据简历更新画像"
- "parse my resume" / "generate my profile"
- "更新个人信息" / "重新生成 profile"
- User mentions they uploaded a new resume and want the profile updated

## Prerequisites

Before running, ensure these exist (create if missing):
- `data/tracker.db` — SQLite database (run `python app.py` once to initialize)
- At least one resume uploaded via the 简历版本管理 page (`/resumes`) — the skill reads from the `resumes` table

## Workflow

### Step 1: Find the resume to parse

Query the DB for the default resume, falling back to the latest upload:

```python
import sqlite3, os
DB = os.path.join(os.getcwd(), 'data', 'tracker.db')
conn = sqlite3.connect(DB)
c = conn.cursor()

# Prefer the default resume; fall back to the newest one
c.execute("SELECT id, name, file_path, file_type FROM resumes WHERE is_default = 1 LIMIT 1")
row = c.fetchone()
if not row:
    c.execute("SELECT id, name, file_path, file_type FROM resumes ORDER BY created_at DESC LIMIT 1")
    row = c.fetchone()

if not row:
    print("No resume found. Ask the user to upload one at /resumes first.")
    conn.close()
    raise SystemExit(1)

resume_id, resume_name, file_path, file_type = row
conn.close()
print(f"Using resume: {resume_name} (id={resume_id}, type={file_type})")
```

The `file_path` field is relative to the project root (e.g. `data/resumes/12345_abcdef.pdf`).

### Step 2: Extract text from the resume

Use the appropriate extractor based on `file_type`:

**PDF** (requires `PyPDF2` or `pdfplumber`):
```python
# Try PyPDF2 first, fall back to pdfplumber
try:
    import PyPDF2
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
except ImportError:
    import pdfplumber
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
```

**Word (.docx)** (requires `python-docx`):
```python
from docx import Document
doc = Document(file_path)
text = "\n".join(p.text for p in doc.paragraphs)
# Also extract table text (resumes often use tables)
for table in doc.tables:
    for row in table.rows:
        text += "\n" + " | ".join(cell.text for cell in row.cells)
```

**Old Word (.doc)**: not supported by python-docx. Tell the user to convert to `.docx` or `.pdf`.

If text is empty or under 50 chars, stop and tell the user the resume may be empty or scanned (image-only PDF needs OCR).

### Step 3: Call LLM to structure the profile

Use whatever LLM API your agent platform provides (Anthropic, OpenAI, local model, etc.).

**Prompt template**:
```
你是一位求职顾问。请将以下简历文本整理为结构化的个人画像，严格按这个格式输出，不要添加其他内容：

## 教育背景
- (学历/学校/专业/时间)

## 核心技术栈
- (分类技能，每行一条，如：控制系统：PID/MPC/串级控制)

## 项目经验
1. (项目名：你的角色 + 核心成果，2-3 行)

## 目标岗位
- (岗位方向，2-3 个)

## 求职偏好
- 行业：(目标行业)
- 城市：(目标城市)
- 其他：(企业性质/薪资/规模偏好)

以下是简历原文：
{text[:4000]}
```

**Platform-specific LLM calls**:

| Platform | LLM tool |
|---|---|
| Trae | Use the platform's built-in LLM (the agent itself), or Anthropic/OpenAI MCP |
| Claude Code | Use the agent's own Claude model (just process the text inline) |
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
        {"role": "system", "content": "你是一个专业的求职简历整理助手。输出结构化 Markdown。"},
        {"role": "user", "content": prompt}
    ]
)
parsed = resp.choices[0].message.content
```

### Step 4: Write the profile

Save the LLM output to `data/profile.md` (overwrite if exists):

```python
with open('data/profile.md', 'w', encoding='utf-8') as f:
    f.write(parsed)
print(f"✅ 个人画像已写入 data/profile.md ({len(parsed)} 字符)")
```

### Step 5: Ask about AI scoring (do NOT auto-run)

After writing the profile, ask the user:
> 画像已更新。是否运行 AI 评分对所有公司重新打分？（需要 ANTHROPIC_API_KEY 或 OPENAI_API_KEY）

If yes:
```bash
python scripts/ai_scorer.py
```
If no API key configured, the script degrades to keyword-only scoring.

## Profile Format

The profile must follow this structure (each section is a level-2 heading):

```markdown
## 教育背景
- ...

## 核心技术栈
- ...

## 项目经验
1. ...

## 目标岗位
- ...

## 求职偏好
- ...
```

This format is consumed by `scripts/ai_scorer.py`.

## Key Rules

- **ALWAYS** read from the `resumes` DB table — never ask the user to provide a file path
- **ALWAYS** prefer the default resume (`is_default = 1`); fall back to the newest
- **NEVER** skip text extraction — if it fails, stop and report (don't write garbage to profile.md)
- **NEVER** auto-run AI scoring — always ask first
- Keep profile under 2000 characters (the scoring prompt includes the full profile)
- If the resume is very long, the LLM should summarize; truncate input to 4000 chars max
- Always use UTF-8 encoding when writing `data/profile.md`

## Error Handling

- No resume in DB → tell user to upload at `/resumes` first
- `python-docx` not installed for .docx → `pip install python-docx`
- `PyPDF2`/`pdfplumber` not installed for PDF → `pip install pdfplumber` (recommended)
- `.doc` (old format) → tell user to convert to `.docx` or `.pdf`
- Empty extracted text → resume may be scanned image; suggest OCR or re-export
- LLM API key missing → tell user to set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- LLM call fails → show error, suggest retrying or checking API quota

## Example Invocation

User: "解析我的简历生成画像"

Agent should:
1. Query `resumes` table for default resume (or latest if no default)
2. Read the file from `data/resumes/xxx.pdf`
3. Extract text (PDF → PyPDF2; DOCX → python-docx, including tables)
4. Call LLM with the structuring prompt
5. Write output to `data/profile.md`
6. Report: "✅ 画像已更新（X 字符），来源：简历「{name}」"
7. Ask: "是否运行 AI 评分？"

## Install Dependencies (one-time)

```bash
pip install python-docx pdfplumber
# Or from requirements-ai.txt
pip install -r requirements-ai.txt
```
