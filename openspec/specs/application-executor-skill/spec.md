## Purpose

定义跨平台 Agent Skill `application-executor` 的触发场景、端到端工作流、安全边界清单、ATS 表单处理手册。供 Trae / Hermes / Claude Code / Cursor / Codex 等 Agent 按相同协议执行半自动化网申预填。借鉴 JobHuntBot `SKILL.md` + `application-playbook.md`。

## ADDED Requirements

### Requirement: 触发场景匹配
Skill 前端 matter SHALL 声明匹配触发词：
- 中文：`投递 {公司}` / `执行 {id} 网申` / `预填 {公司} 表单` / `帮我填申请表`
- 英文：`apply to {company}` / `prefill application {id}` / `execute submission for {id}`
- Alias：`jobhunt-executor` / `career-application-executor`

### Requirement: 端到端工作流（12 步）
Skill 工作流 SHALL：
1. 从 `/to-apply` 取目标 application（status=待投递）。
2. 校验目标已关联 form_url（若缺则向用户索要）。
3. 调 `get_resume_for_role(role_family, jd_keywords)` 选推荐简历并展示给人确认。
4. 调 `prefill_application_form(application_id, form_url)`，触发 Playwright 预填。
5. 【安全门 1】敏感字段分类 → 缺则 await_human 清单。
6. 【安全门 2】AnswerBank 未命中字段 → 缺则 await_human 清单。
7. 【安全门 3】检测到 CAPTCHA/登录 → await_human。
8. 等待人类在 Web `/submissions` 页审核预填内容 + 审核缺失答案。
9. 跳转真实页面（`screenshot_path` 旁边放跳转按钮），人类在页面上做任何调整，最终**人类点击提交**。
10. 回到 JHTracker，点击「已提交」或「提交失败」。
11. 触发 `record_submission_result(success=...)`。
12. 自动提取沉淀答案 → AnswerBank（`needs_review=1`）。

### Requirement: 安全边界清单
Skill 开头 SHALL 打印（或在每轮开头 remind）以下 NEVER 清单：
- NEVER 猜测身份证/护照/社保/银行账号。
- NEVER 猜测签证/工作授权/犯罪记录。
- NEVER 猜测期望薪资（只从 profile/answer_bank 取）。
- NEVER 猜测在职状态/推荐人信息。
- NEVER 点击「提交/Apply/确认投递/Submit/Finalize」任何提交类按钮。
- NEVER 勾选法律条款/隐私条款/非竞争协议（必须人工）。

### Requirement: ATS 处理手册（Playbook 章节）
Skill 中 SHALL 有「ATS Handling Playbook」章节，覆盖：
- 文件上传（`input[type=file]`）：只上传用户确认好的简历路径，绝不自动生成 PDF。
- 单选/下拉（select/radio）：按 AnswerBank 精确匹配，否则 await。
- 多行经历区块（"Add Experience" 动态表）：优先 ExperienceBank，按 jd_keywords 排序插入。
- 答案长度限制（字符计数 / 段落）：遵守 maxlength，超则从尾部截断并 await。
- 日期字段：日期格式与页面要求匹配（YYYY-MM-DD / MM/YYYY 等），不匹配则 await。

## MODIFIED Requirements

### Modification: Skill 与 MCP 工具关联
Skill 的 `allowed-tools` 清单 SHALL 包含（新增 6 + 复用既有 8）：
- 新增：`JHTracker:get_answer_bank`、`JHTracker:upsert_answer_bank`、`JHTracker:delete_answer_bank`、`JHTracker:prefill_application_form`、`JHTracker:record_submission_result`、`JHTracker:get_resume_for_role`
- 复用：`JHTracker:get_application`、`JHTracker:list_applications`、`JHTracker:update_application_status`（仅限 `待投递↔待提交`）、`JHTracker:get_user_preferences`、`JHTracker:get_candidate_profile`、`JHTracker:update_candidate_profile`、`JHTracker:list_resumes`、`JHTracker:record_agent_trace`
