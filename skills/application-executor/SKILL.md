---
name: "application-executor"
description: "Executes semi-automated job application form prefill (Agent pre-fills, human reviews and clicks submit). Manages AnswerBank for reusable answers. NEVER auto-submits. Alias: career-tracker-executor, career-tracker-prefill."
allowed-tools:
  - JHTracker:list_applications
  - JHTracker:get_application
  - JHTracker:update_application_status
  - JHTracker:get_resume_for_role
  - JHTracker:get_answer_bank
  - JHTracker:upsert_answer_bank
  - JHTracker:delete_answer_bank
  - JHTracker:prefill_application_form
  - JHTracker:record_submission_result
  - JHTracker:get_candidate_profile
  - JHTracker:record_agent_trace
  - JHTracker:notify_db_changed
---

# Application Executor Skill

Semi-automated job application form prefill for JHTracker. Agent pre-fills form fields with answers from AnswerBank + candidate profile; human reviews prefilled data and clicks submit on the real page. Agent NEVER clicks submit.

## Trigger Scenarios

Invoke when the user says any of:
- "预填 {公司} 的网申表单" / "投递 {公司}" / "fill {company} application form"
- "查答案库" / "添加答案" / "管理答案库"
- "选简历" / "推荐简历版本"
- "已提交 {公司} 投递" / "记录投递成功/失败"

## Safety Boundaries — NEVER Violate

Agent SHALL NOT:
1. **Click submit/apply buttons** — `提交/Apply/确认投递/立即投递/确认申请` are reserved for human only.
2. **Guess identity fields** — 身份证/护照/SSN. Must source from `data/profile.md`. If missing, status=`awaiting_human`.
3. **Guess legal fields** — 签证/工作授权/犯罪记录/移民. Same as identity.
4. **Guess compensation fields** — 薪资/期望薪资/当前薪资. Must come from profile or `answer_bank` only. Never invent.
5. **Guess current_status fields** — 推荐人/现任雇主/在职状态. Same rule.
6. **Guess financial fields** — 银行账号/社保/公积金/税务. Same rule.
7. **Auto-check agreement checkboxes** — terms/privacy consent must be human-reviewed.
8. **Set application status to `已投递` directly** — only `record_submission_result(success=True)` can flip 待提交 → 已投递, and it requires human to have manually clicked submit first.

If a sensitive field is missing from both `answer_bank` and `profile.md`, the field is left unfilled and the submission is marked `status=awaiting_human`. The Agent lists the missing items back to the user.

## Workflow: Prefill an Application Form

### Step 1 — Locate Target Application
```
JHTracker:list_applications(status="待投递", company_name="{company}")
→ get application_id, form_url (from `url` or `source_url` field), position
```

### Step 2 — Pick Best Resume
```
JHTracker:get_resume_for_role(role_family="{role_family}", jd_keywords="{comma-separated}")
→ get recommended_resume_id
```
Phase 1 returns default resume only; Phase 3 adds ExperienceBank matching.

### Step 3 — Identify Form Fields & Prefill
Phase 1 (current): User provides form field descriptors, Agent passes them to the tool.
```
fields = [
  {"label": "姓名", "name": "name"},
  {"label": "邮箱", "name": "email"},
  {"label": "期望薪资", "name": "salary"},        # 敏感 → 走 profile
  {"label": "身份证号", "name": "id_card"},       # 敏感 → 走 profile
  {"label": "学校", "name": "school"}             # 非敏感 → 走 AnswerBank
]
JHTracker:prefill_application_form(
    application_id={id},
    form_url="{url}",
    fields="<JSON array>",
    role_family="{role_family}",
    dry_run=true,           # Phase 2 will support dry_run=false for real Playwright
    task_id="{trace_id}"
)
```

### Step 4 — Check Return Status
```
result.status ∈ {"prefilled", "awaiting_human", "failed"}
```
- `prefilled` — All fields filled successfully. Application status → 待提交. Tell user to review at `/submissions/{id}`.
- `awaiting_human` — Some fields missing. Application status → 待提交. Show `awaiting_human_items` list to user, ask for missing answers.
- `failed` — Application not in 待投递/待提交 status, or invalid input. Show `reason`.

### Step 5 — Tell User What To Do Next
```
"已完成预填（X/Y 字段）。请打开 http://127.0.0.1:5000/submissions/{id} 审核预填数据，
确认无误后到真实招聘页面 {form_url} 手动点击提交按钮，再回到本对话告诉我「已提交」。"
```

## Workflow: Record Submission Result

After human confirms they clicked submit on the real page:

### Success Path
```
JHTracker:record_submission_result(
    application_id={id},
    success=true,
    screenshot_path="/data/submissions/{id}_submitted.png"  # optional
)
→ application.status: 待提交 → 已投递
→ submission.status: submitted
→ apply_date: today
```

### Failure Path
```
JHTracker:record_submission_result(
    application_id={id},
    success=false,
    failure_reason="{reason}"
)
→ application.status: 待提交 → 待投递 (revert)
→ submission.status: failed
```

## AnswerBank Operations

### Add / Update Reusable Answer
```
JHTracker:upsert_answer_bank(
    question_pattern="学校",
    answer="清华大学",
    role_family="",            # empty = general
    needs_review=false,
    source="manual"            # or "extracted" (auto-sedimented from past submissions)
)
```
Deduplicated by `(question_pattern, role_family)`. Both fields are normalized via `role_family_normalize()`.

**Warning**: If `question_pattern` matches a sensitive category (薪资/身份/法律/etc.), the tool returns a warning recommending the answer be sourced from `data/profile.md` instead of answer_bank. Stored anyway, but profile is preferred.

### Query Answer Bank
```
JHTracker:get_answer_bank(
    role_family="嵌入式",      # optional, normalized internally
    question="GPA"             # optional substring match
)
→ list of {id, question_pattern, answer, role_family, needs_review, source, sensitive_use_profile}
```

### Delete Answer
```
JHTracker:delete_answer_bank(answer_id={id}, confirm=true)
```

## Status Flow Reference

```
Pending Approval → 待投递 → 待提交 → 已投递 → 简历筛选 → ... → Offer/已拒
                 ↑__________|
                   (failure revert from 待提交)
```

- `待投递` → `待提交`: Only via `prefill_application_form` (Agent).
- `待提交` → `已投递`: Only via `record_submission_result(success=True)` (after human clicked submit).
- `待提交` → `待投递`: Only via `record_submission_result(success=False)` (failure revert).

## ATS Handling Playbook (Phase 2 Reference — Playwright Mode)

When Phase 2 enables `dry_run=false`, the following patterns apply:

### File Upload (Resume)
- Use `page.set_input_files('input[type=file]', resume_path)`.
- If ATS uses dynamic uploader (no `<input type=file>`), pause and ask user to upload manually.

### Dynamic Experience Fields
- ATS like Greenhouse/Lever add experience entries dynamically via "+ Add" buttons. Agent may click "+ Add" buttons (these are NOT submit buttons), but each row's fields go through the same SafetyGuard classification.

### Date Format
- Use `YYYY-MM` for graduation dates, `YYYY-MM-DD` for application dates unless ATS explicitly shows a different placeholder.

### CAPTCHA / Login Required
- If CAPTCHA detected (img.captcha, reCAPTCHA iframe, slider): pause, set `status=awaiting_human`, ask user to solve in the real browser window.
- If login required (page redirects to /login): pause, ask user to log in first.

### Fallback to integrated_browser MCP
If Playwright real mode fails (unrecognized ATS, weird form structure), Agent may fall back to:
- `browser_navigate` → `browser_snapshot` → `browser_type` → `browser_click` (NOT submit buttons)
Each step must respect SafetyGuard.

## Phase 1 Limitations

- `dry_run=false` returns error "Phase 2 feature".
- ExperienceBank matching returns empty array (Phase 3).
- `record_submission_result(extracted_answers=...)` accepts the parameter but does NOT auto-sediment into answer_bank yet (Phase 3).
- No browser automation — fields must be provided by the caller (typically from manual inspection or another Agent that reads the form structure).

## Example Conversation

**User**: "预填汇川技术 嵌入式工程师岗位的网申表单"

**Agent**:
1. `list_applications(status="待投递", company_name="汇川")` → application_id=42, source_url="https://..."
2. `get_resume_for_role(role_family="嵌入式")` → resume_id=3
3. Ask user: "请把表单字段告诉我（label/name/id 即可），或者先用 `integrated_browser` 打开页面抓取字段结构。"
4. User provides: `[{"label":"姓名","name":"name"},{"label":"期望薪资","name":"salary"}]`
5. `prefill_application_form(application_id=42, form_url="https://...", fields="[{...}]", role_family="嵌入式", dry_run=true)`
6. Reply: "已预填 2/2 字段（姓名走 AnswerBank，期望薪资走 profile）。请到 `/submissions/42` 审核后，到真实页面手动提交，再回来告诉我「已提交」。"

**User** (later): "已提交汇川的投递"

**Agent**:
1. `record_submission_result(application_id=42, success=true)` → 已投递
2. Reply: "已记录为已投递，apply_date=today。该岗位进入投递记录页面。"
