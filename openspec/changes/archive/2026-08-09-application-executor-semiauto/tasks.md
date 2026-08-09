## Phase 1 MVP（无浏览器） — 闭环跑通 ✓

### 1. 数据库迁移 + 模型
- [x] 1.1 在 `models.py` 新增 `AnswerBank`、`ExperienceBank`、`ApplicationSubmission` 3 个模型，字段完全对齐 proposal 的 schema。
- [x] 1.2 在 `constants.py` 新增：`PRE_APPLY_STATUS_LIST` 追加 `'待提交'`；`SENSITIVE_FIELD_PATTERNS`（正则+分类字典）；`SUBMISSION_STATUSES` 枚举。
- [x] 1.3 生成 Alembic 迁移脚本 `migrations/versions/<hash>_add_submission_tables.py` 并本地 `flask db upgrade` 验证。

### 2. 服务层基础
- [x] 2.1 新建 `services/safety_guard.py`：实现 `classify_field()`（5 类正则分类）、`is_submit_button()`（按钮安全检查）、`SafetyBlockedError` 异常。
- [x] 2.2 新建 `services/submission_executor.py`：先实现 `prefill_dry_run()`（不启 Playwright，只接收传入 fields 列表 + application_id，组装 prefilled_data JSON 并写 ApplicationSubmission + Application 状态 待投递→待提交）；`executor = ThreadPoolExecutor(max_workers=2)` 留好接口。
- [x] 2.3 在 `utils.py` 或新增函数：`role_family_normalize(text)`（去空格+统一斜杠+小写）。

### 3. MCP 工具（5/6 先上，prefill 先 dry_run 版）
- [x] 3.1 `get_answer_bank(role_family=None, question=None)`：正则匹配 question_pattern；先 role_family 精确后回退通用；命中 needs_review=1 打标；敏感字段分类命中时走 profile 解析（复用 `get_candidate_profile` 内部逻辑）。
- [x] 3.2 `upsert_answer_bank(question_pattern, answer, role_family=None, needs_review=False, source='manual')`：按 `(question_pattern_normalized, role_family_normalized)` 唯一约束 upsert。
- [x] 3.3 `delete_answer_bank(answer_id, confirm=False)`：需要 `confirm=True` 才生效。
- [x] 3.4 `prefill_application_form(application_id, form_url, fields_override=None, dry_run=True)`：MVP 强制 dry_run=True；走 submission_executor.prefill_dry_run；记录轨迹；改 application 状态。
- [x] 3.5 `record_submission_result(application_id, success, screenshot_path=None, failure_reason=None, extracted_answers=None)`：success=True→已投递+apply_date；False→回退待投递；写 ApplicationSubmission。**AnswerBank 自动沉淀先留 TODO 注释，Phase 3 实装**。
- [x] 3.6 `get_resume_for_role(role_family=None, jd_keywords=None)`：MVP 只返回默认简历（`get_default_resume()` 逻辑），ExperienceBank 匹配留 TODO，Phase 3 实装。

### 4. Web 路由 & UI
- [x] 4.1 新建 `routes/submission.py`：
  - GET `/submissions`：列出 status=待提交/awaiting_human 的列表 + prefilled_data + 截图预览。
  - POST `/submissions/<submission_id>/mark-submitted` → 内部调 `record_submission_result(success=True)`。
  - POST `/submissions/<submission_id>/mark-failed` → 调 `record_submission_result(success=False, failure_reason=...)`。
  - POST `/submissions/<submission_id>/answer` → 人工补填缺失答案，写 ApplicationSubmission.prefilled_data（就地覆盖 field.filled=true, source=human_filled）。
- [x] 4.2 新建 `templates/submissions.html`：Bootstrap 5，Tab（待提交 / awaiting_human / 已完成 / 失败），每条卡片展示表单 URL跳转按钮、字段清单分色展示（绿色=bank命中；橙色=needs_review；紫色=profile取；红色=missing）、缺失字段下方 inline 输入框 + 保存按钮、「标记已提交 / 标记失败」按钮。
- [x] 4.3 修改 `templates/to_apply.html`：每条加「预填网申」按钮 → 带参数 POST 到 prefill_application_form（MVP 弹出 prompt 让用户手动填字段 JSON 或直接走 dry_run 空结构）。
- [x] 4.4 修改 `templates/base.html`：侧边栏加「待提交审核」链接。

### 5. Skill
- [x] 5.1 新建 `skills/application-executor/SKILL.md`：
  - matter：name、description、触发中/英文关键词、alias、allowed-tools（6 新+8 旧）。
  - 12 步工作流对齐 specs/application-executor-skill/spec.md。
  - NEVER 边界清单 6 条对齐 safety-guard spec。
  - ATS Handling Playbook 章节 5 小节对齐 spec。
  - profile.md 推荐字段附录（target_salary、work_authorization、reference_contacts、id_card_number 等）。

### 6. 测试
- [x] 6.1 新建 `tests/test_safety_guard.py`：覆盖 5 类敏感字段分类命中/不命中、is_submit_button 的正则/属性/长度边界、Role family 归一化。
- [x] 6.2 新建 `tests/test_submissions.py`：覆盖 3 表 CRUD、status 流转（待投递→待提交→已投递；待提交→失败→待投递）、prefill_dry_run 输出 prefilled_data schema。
- [x] 6.3 在 `tests/test_agent_api.py` 追加 6 个新 MCP 工具的同步调用测试（dry_run 模式）。
- [x] 6.4 运行 `python -m pytest tests/`，全绿。

---

## Phase 2 Playwright 集成

### 7. 依赖 & 初始化
- [ ] 7.1 `requirements.txt` 加 `playwright`；`requirements-ai.txt` 同步。
- [ ] 7.2 在 `start.sh` / `start.bat` 追加：首次启动提示（若未安装浏览器二进制）运行 `playwright install chromium`。

### 8. submission_executor 真实预填
- [ ] 8.1 `services/submission_executor.py` 新增 `_prefill_real(application_id, form_url, task_id)`：
  - `with sync_playwright() as p: browser = p.chromium.launch(headless=False, slow_mo=500)`。
  - `page.set_default_timeout(180_000)`。
  - `page.goto(form_url)`；若 302 到 login URL → 检测 URL 关键字 → 记轨迹 + status=awaiting_human + 返回。
  - 检测 CAPTCHA：查询 `iframe[title*="CAPTCHA" i]`、`.g-recaptcha`、`[class*="captcha" i]` → 命中则同上暂停。
  - 解析表单字段：查询所有 `input:not([type=hidden]):not([type=submit]), select, textarea`；取 (label关联文本, name, id, placeholder)。
  - 对每字段：`classify_field()` → 按分类取答案（敏感→profile；其余→answer_bank；缺→加入 await 清单）。
  - 填值：text/textarea→fill；select→select_option；radio→check（按 value 匹配答案）；checkbox→根据答案布尔。
  - **点击前安全检查**：所有 `click()` 前走 `is_submit_button()`，命中→跳过 + trace 记 `safety_blocked_click`。
  - 截图：`page.screenshot(path=..., full_page=True)`。
  - 组装 prefilled_data JSON，关闭浏览器，写库 + 改状态。
- [ ] 8.2 新增 `prefill_async_submit(application_id, form_url, task_id)` → `executor.submit(_prefill_real, ...)`，立即返回 task_id，由 future.add_done_callback 写库 + send SSE（复用 `notify_db_changed` + `record_agent_trace`）。
- [ ] 8.3 MCP `prefill_application_form` 新增 `dry_run=False` 分支：调 `prefill_async_submit`，返回 `{"task_id": ..., "status": "running"}`（跟 agent_tasks 机制对齐）。

### 9. tests 补充
- [ ] 9.1 在 CI 中 Playwright 相关测试用 pytest.mark.skipif 跳过；只跑 dry_run + safety_guard。
- [ ] 9.2 本地手动测试脚本：`scripts/test_prefill_sample.py`（打开一个公开表单页做手动验证，不提交）。

---

## Phase 3 沉淀闭环 + 简历路由

### 10. AnswerBank 自动提取
- [ ] 10.1 `record_submission_result(success=true)`：扫描 prefilled_data.fields，条件是 `source in (answer_bank_needs_review, human_filled)` 且 classified_as ∉ {identity, legal, financial, current_status, compensation} → 逐条 `upsert_answer_bank(needs_review=True, source='extracted')`。

### 11. ExperienceBank + resume_routing
- [ ] 11.1 MCP `upsert_answer_bank` 旁边实现 ExperienceBank 的 CRUD 工具（建议并入 get/upsert/delete，用工具名前缀区分：如 `upsert_experience_bank(...)` — 或作为同一工具用 `kind='answer'|'experience'` 开关）。
- [ ] 11.2 `get_resume_for_role` 实装：按 (role_family 归一化 + jd_keywords 交集数量) 排序 ExperienceBank，选出 TOP 5 经历与最佳匹配 resume_version_id。

### 12. Web 管理页
- [ ] 12.1 新增 `routes/answer_bank.py` + `templates/answer_bank.html`：列表、搜索、新增、编辑、删除、needs_review 一键确认。
- [ ] 12.2 新增 `routes/experience_bank.py` + `templates/experience_bank.html`：同上。

---

## Phase 4（可选，不入本期）
- Tampermonkey 用户脚本 / Chrome 扩展：在 BOSS/智联/Lagou 页面注入浮窗，GET 后端 REST `/api/v1/submissions/<id>/prefilled-data`，按 selector 回填。本期不做。
