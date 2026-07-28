---
name: career-tracker-profile
description: "Manages candidate profile for JHTracker. View/edit/upload resume → parse → update data/profile.md. Invoke when user asks to view profile, edit personal info, upload resume to update profile, or says 查看画像/编辑画像/上传简历更新. Platform-agnostic — works with Trae / Claude Code / Cursor / Codex."
---

# Career Tracker Profile Skill

This skill manages the candidate profile used by JHTracker's AI scoring engine. It reads from the profile route and can also parse an uploaded resume directly.

**Platform-agnostic**: works with any AI agent. The Flask web UI handles viewing/editing; this skill handles the agent-assisted resume → profile pipeline.

## When to Invoke

- "解析简历生成画像" / "根据简历更新profile"
- "更新个人信息" / "更新目标岗位"
- "parse my resume" / "generate my profile"
- User says they uploaded a new resume and want profile auto-updated

## Prerequisites

- `data/tracker.db` — SQLite database exists
- At least one resume uploaded via `/resumes` web page, OR user provides a file path

## Workflow

### Step 1: Find or ask for the resume source

**Option A — Use uploaded resume from DB:**
```python
import sqlite3, os
DB = os.path.join(os.getcwd(), 'data', 'tracker.db')
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT id, name, file_path, file_type FROM resumes WHERE is_default = 1 LIMIT 1")
row = c.fetchone()
if not row:
    c.execute("SELECT id, name, file_path, file_type FROM resumes ORDER BY created_at DESC LIMIT 1")
    row = c.fetchone()
conn.close()
if not row:
    print("No resume found. Ask user to upload at /resumes first.")
    raise SystemExit(1)
file_path = row[2]  # relative to project root, e.g. data/resumes/xxx.pdf
file_type = row[3]  # 'pdf' or 'docx'
```

**Option B — User provides a file path directly** (e.g., after uploading or exporting).

### Step 2: Extract text

**PDF:**
```bash
pip install pdfplumber
python -c "import pdfplumber; f=open('data/resumes/your.pdf','rb'); print(' '.join(p.extract_text() or '' for p in pdfplumber.open(f).pages))"
```

**Word (.docx):**
```bash
pip install python-docx
python -c "
from docx import Document
doc = Document('data/resumes/your.docx')
for p in doc.paragraphs: print(p.text)
for t in doc.tables:
    for r in t.rows: print(' | '.join(c.text for c in r.cells))
"
```

### Step 3: Call LLM to structure the profile

Use whatever LLM your agent platform provides. Prompt template:

```
你是一位求职顾问。请将以下简历文本整理为结构化的个人画像：

## 教育背景
- 学历/学校/专业/时间

## 核心技术栈
- (分类技能，每行一条)

## 项目经验
1. 项目名：角色 + 核心成果

## 目标岗位
- (2-3个方向)

## 求职偏好
- 行业：
- 城市：
- 其他：

简历原文：
{text[:4000]}
```

### Step 4: Write profile

```python
with open('data/profile.md', 'w', encoding='utf-8') as f:
    f.write(parsed_text)
```

### Step 5: Ask about AI scoring

After updating profile, ask:
> 画像已更新。是否运行 AI 评分对所有公司重新打分？

## Profile Format

```markdown
## 教育背景
## 核心技术栈
## 项目经验
## 目标岗位
## 求职偏好
```

This format is consumed by `scripts/ai_scorer.py`.

## Key Rules

- **ALWAYS** prefer default resume (`is_default=1`) from DB; fall back to latest
- **NEVER** auto-run AI scoring — always ask the user first
- **NEVER** write empty/garbage to profile.md
- Keep profile under 2000 characters (prompt budget)
- Truncate resume input to 4000 chars max
- Always use UTF-8 encoding

## Error Handling

- No resume in DB → tell user to upload at `/resumes`
- Empty text → resume may be image-only; suggest OCR
- LLM key missing → tell user to configure .env