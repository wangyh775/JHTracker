---
name: career-tracker-profile
description: "Manages the candidate profile (data/profile.md) for JHTracker. Use this when the user asks to view, edit, upload a resume, or update their personal information for AI scoring. Covers profile file management, resume parsing, and LLM-based profile generation."
---

# Career Tracker Profile Skill

This skill manages the candidate's personal profile (`data/profile.md`), which drives the AI scoring engine. 

**Platform-agnostic**: works with any AI agent that can read/write files and optionally call an LLM API.

## 1. When to use

- "查看/编辑我的画像" — View or edit the profile
- "上传简历解析" — Parse a PDF/Word resume into a structured profile
- "更新个人信息" — Update specific fields (education, skills, etc.)
- "没有profile.md" — Initialize the profile file

## 2. Workflow

### Step 1: Check if profile exists

The profile lives at `data/profile.md`. Check if it exists:
```bash
# Check file
ls data/profile.md
```

If it doesn't exist, create a default template:
```markdown
## 教育背景
- [学历]，[学校]，[专业]

## 核心技术栈
- [技能分类1]：[技能1], [技能2]
- [技能分类2]：[技能3], [技能4]

## 项目经验
1. [项目名]：[简述]

## 目标岗位
- [岗位方向1]
- [岗位方向2]

## 求职偏好
- [行业]：[偏好说明]
- [城市]：[偏好说明]
```

### Step 2: Allow editing

Let the user edit the file directly with the AI agent, or use the `/profile` web UI (Flask route) for a textarea-based editor.

### Step 3: Resume upload (optional)

If the user has a PDF or Word resume, you can parse it to populate the profile.

**Approach 1 — Using the Flask app**:
The `/profile` page has a file upload button that calls `routes/profile.py:profile_upload()`. It extracts text from the file and calls an LLM to restructure it into the profile format.

**Approach 2 — Direct Python**:
```python
# Extract text from PDF
# Requires: pip install PyPDF2 or pdfminer.six or pdfplumber
import PyPDF2
with open('resume.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    text = "\n".join(p.extract_text() for p in reader.pages)

# Or from Word
# Requires: pip install python-docx
from docx import Document
doc = Document('resume.docx')
text = "\n".join(p.text for p in doc.paragraphs)

# Call LLM to structure it
# Use your platform's LLM API (Anthropic, OpenAI, etc.)
# Prompt: "请将以下简历整理为结构化个人画像，按格式：## 教育背景..."
```

## 3. Profile format

The profile must follow this structure (each section is a level-2 heading):

```
## 教育背景
## 核心技术栈
## 项目经验
## 目标岗位
## 求职偏好
```

## 4. Integration with AI Scoring

The `scripts/ai_scorer.py` reads `data/profile.md` at runtime. If the profile is empty or missing, the script will:
1. Print a warning
2. Degrade to keyword-only pre-filtering (no LLM calls)
3. Assign default scores (50 points) to all companies

After updating the profile, the user should re-run AI scoring for accurate results.

## 5. Pitfalls

- **File encoding**: Always use UTF-8. Save with `encoding='utf-8'`.
- **Profile too long**: The scoring prompt includes the full profile. Keep it under 2000 characters. If the resume is very long, summarize it.
- **No API key**: The resume parsing feature requires an LLM API key. If none is configured, the raw extracted text will be saved as-is.