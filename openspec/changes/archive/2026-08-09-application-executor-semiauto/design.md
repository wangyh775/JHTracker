## Context

JHTracker 现架构为 Flask 3.0（同步）+ FastMCP（同步 def）+ SQLAlchemy + SQLite，Agent 任务通过 `agent_tasks` 表 + SSE 广播（`/traces`）长跟踪；Post-Application（`已投递` 之后）为 Agent 只读保护区。本 change 在此架构之上扩展，**不升级为 FastAPI/async**，通过 `concurrent.futures.ThreadPoolExecutor` 把 Playwright 同步调用跑在子线程里，复用 `record_agent_trace` / SSE 机制。

决策依据：用户已用 Hermes 定时任务实现自动化，当前同步架构 + 长任务轨迹系统足以支撑 2-4 个并发预填。未来如要跑常驻批量队列再评估升级。

## Goals / Non-Goals

**Goals:**
- 新增 `AnswerBank` / `ExperienceBank` / `ApplicationSubmission` 3 张表 + Alembic 迁移。
- 新增 6 个 MCP 工具：`get_answer_bank` / `upsert_answer_bank` / `delete_answer_bank` / `prefill_application_form` / `record_submission_result` / `get_resume_for_role`。
- 新增 `待提交` 中间态：`待投递 → 待提交 → 已投递`；`已投递` 之后仍 Agent 只读。
- 实现 Playwright 预填（headless=False）：打开、解析、填值、截图、不点提交。
- 实现安全门：5 类敏感字段分类 + 禁止提交按钮点击 + CAPTCHA/登录暂停。
- 新增 Skill `skills/application-executor/SKILL.md` 与 Web `/submissions` 审核页。

**Non-Goals:**
- 全自动点击「提交」——永远不做。
- 架构升级为 FastAPI/async——本期不做。
- 浏览器扩展/Tampermonkey 用户脚本——留待 Phase 4。
- 多用户支持/权限隔离。

## Decisions

### 1. 同步 + ThreadPoolExecutor 跑 Playwright（而非引入 async）
- **Choice**：在 `services/submission_executor.py` 中用 `playwright.sync_api.sync_playwright`，外层用 `concurrent.futures.ThreadPoolExecutor(max_workers=2)` 做非阻塞提交。任务完成后写 `ApplicationSubmission` + `record_agent_trace`。SSE 事件走原有 `/traces` 通道。
- **Rationale**：
  - 不改变 Flask 同步路由与 MCP 同步工具签名，无侵入。
  - 预填是 I/O 密集，GIL 不是瓶颈，2 并发足够个人求职场景。
  - headless=False 必须有真实显示，远程沙箱/CI 测试时可降级为「仅组装 prefilled_data 不启动浏览器」分支（见 Risks）。
- **Trade-off**：无法取消子线程中已启动的 Playwright 浏览器，需设 `PLAYWRIGHT_TIMEOUT`（默认 180s）自动收尾。

### 2. 敏感答案从 profile 直通、不入 AnswerBank
- **Choice**：`SENSITIVE_FIELD_PATTERNS` 分类为 identity/legal/compensation/current_status/financial 的字段，答案检索逻辑跳过 `answer_bank` 表，直接解析 `data/profile.md` 对应 key；若 profile 缺 key → 标记 `missing=true` 切 `awaiting_human`。
- **Rationale**：
  - 避免敏感数据双写；profile 是用户单一真相源（Single Source of Truth）。
  - 与 `get_candidate_profile()`/`update_candidate_profile()` MCP 工具协同。
- **Trade-off**：profile.md 需要约定一组标准字段名（target_salary、work_authorization、reference_contacts 等）。Phase 1 在 Skill 中输出一个推荐字段附录，用户可随时手动扩展。

### 3. role_family 采用「预设+自定义+归一化」
- **Choice**：
  - 预设候选集（从 `profile.md` 的 `enterprise_preference.target_positions` 读取，再加 "通用"）。
  - 允许自填任意字符串。
  - 入库前统一：`role_family = re.sub(r'\s+', '', text).replace('／','/').replace('、','/').lower()`。
  - AnswerBank/ExperienceBank 唯一键为 `(normalized_pattern, normalized_role_family)`。
- **Rationale**：兼顾灵活与去重；避免"机器人算法" vs "机器人 / 算法" 被当两类。
- **Trade-off**：归一化后可能误伤（如 "算法" vs "算法工程师"），靠 `role_family LIKE` 模糊匹配兜底。

### 4. prefilled_data JSON 结构
- **Choice**：固定 schema：
```json
{
  "fields": [
    { "selector": {"label":...,"name":...,"id":...},
      "classified_as": "benign|compensation|...",
      "answer": "...",
      "source": "answer_bank|profile|answer_bank_needs_review|missing|human_filled",
      "filled": true|false
    }
  ],
  "resume_version_id": 1,
  "awaiting_human_items": ["第 3 项：薪酬期望缺失，请补填"]
}
```
- **Rationale**：Audit-trackable——可以精确还原每个字段来源与命中情况，支持 Web UI 分色展示。

### 5. 禁止提交按钮：正则 + 属性双重检查
- **Choice**：`safety_guard.is_submit_button(text, type, id, cls, onclick)`：
  - 文本正则：`r"(提交|确认投递|apply|submit|finalize|确认|投递简历)"i`，且长度 ≤ 30（避免文章正文误判）。
  - 类型 `type=submit` / `input[type=submit]` 直接 True。
  - id/class 含 `submit`/`confirm`/`apply-button`。
- Playwright 在 `page.click(selector)` 前必先调此函数，命中抛 `SafetyBlockedError`，上层捕获记轨迹。
- **Rationale**：双保险（内容 + 属性），最大程防止误点。

## Risks / Trade-offs

- **[Risk]** Playwright headless=False 需要图形环境，CI 或远程无桌面环境无法跑预填。
  → *Mitigation*：`prefill_application_form()` 提供 `dry_run=True` 参数：不启动浏览器，只按 `form_url` 标记状态，生成「示意预填 JSON」给用户在 /submissions 手动对照填。CI 测试只跑 dry_run 分支 + safety_guard 单元测试。
- **[Risk]** ATS 表单 DOM 结构多变，字段定位器不稳定。
  → *Mitigation*：`classify_field` 采用 4 级回退：label 可见文本 → name→ id→ placeholder；全部失败则 await_human 并把元素截图发到人审页。后续靠用户反馈累计 pattern。
- **[Risk]** Playwright 子线程长时间占资源。
  → *Mitigation*：`PLAYWRIGHT_TIMEOUT=180s` 环境变量 + `page.set_default_timeout()`；Agent 任务中心实时显示 running 状态，人可手动 `clear_agent_traces` 对应 task。
- **[Risk]** AnswerBank 自动沉淀可能产生低质量或错误答案。
  → *Mitigation*：`extracted` 来源默认 `needs_review=1`。检索时 `needs_review=1` 的答案会在返回里打标，人类在人审页必须显式点「确认可用」后参与自动填；未确认的只作建议。

## Migration Plan（Phase 1 → 2 → 3 拆期）

### Phase 1 MVP（无浏览器）
1. Alembic 迁移：建 `answer_banks`、`experience_banks`、`application_submissions` 3 表；
2. `models.py` +3 模型；`constants.py` 加 `待提交` 状态与安全黑名单；
3. MCP 工具：`get_answer_bank`、`upsert_answer_bank`、`delete_answer_bank`、`record_submission_result`、`get_resume_for_role`；
4. `prefill_application_form` 先只跑 dry_run：接受外部传入的表单字段，组装 prefilled_data，不启 Playwright；
5. status 流转打通；
6. `/submissions` 基本审核页 + `/to-apply` 列表加按钮。
7. Skill `application-executor/SKILL.md`（工作流 + 安全门）产出。

**交付：能跑通「预填（手动）JSON → 人审 → 提交回写 → 答案沉淀」的闭环。**

### Phase 2 Playwright 集成
1. `services/safety_guard.py`；
2. `services/submission_executor.py`：`sync_playwright` + ThreadPoolExecutor；
3. MCP `prefill_application_form` 支持 `dry_run=False` 真实填值；
4. 截图落盘 `data/submissions/`；
5. CAPTCHA/登录页检测 → await_human。

**交付：真实网站预填（不点提交）+ 截图。**

### Phase 3 沉淀闭环 + 简历路由
1. 自动答案提取：`record_submission_result` 内部扫描 prefilled_data → AnswerBank（needs_review=1）。
2. ExperienceBank 扩展：`resume_routing` 逻辑实装到 `get_resume_for_role`。
3. Web 管理页 `/answer_bank` 与 `/experience_bank`。

### Phase 4（可选）
Tampermonkey 用户脚本 / Chrome 扩展：在 BOSS/智联页面注入浮窗，通过 REST 拉 prefilled_data 回填。本期不做。
