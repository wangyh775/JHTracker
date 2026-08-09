## Why

JHTracker 目前止步于 `/to-apply` 待投递清单。用户进入 `/to-apply` 后必须手动去各家招聘网站复制个人信息、反复填相同字段、应对 ATS 表单差异。这是求职流程中最耗时、最重复、最易错的环节——恰恰是 Agent 最该接手的部分。参考 JobHuntBot 的 `application-playbook.md` + `answer_bank.template.md` + `experience_bank.template.md` + 严格安全边界设计，将 JHTracker 的工作流从「找到值得投的公司」延伸到「把答案准备好，等人审后提交」，覆盖投递前最后一公里。

**不做全自动盲投**：严格保留你项目的 HITL 哲学——Agent 只做「预填」+「人审」，绝不在无人确认的情况下点「提交」。这是与 LinkedIn-AI-Job-Applier-Ultimate 这类全自动项目的根本区别。

## What Changes

- **Answer & Experience Banks（答案库）**：新增 2 张 SQLite 表，可复用答案（基本信息、毕业院校、期望薪资等）和按岗位族路由的经历片段；敏感答案（身份证/薪酬/签证等）从 `data/profile.md`（用户画像）直接取，不双写；非敏感答案从过往提交自动提取沉淀。
- **Pre-Submit 中间态**：在现有 status 流转 `待投递 → 已投递` 之间插入 `待提交`。`待提交` 是 Agent 可写预填数据的区域，**不越过现有 Post-Application 只读保护边界**。只有人类点击真实页面的提交按钮后，状态才转为 `已投递`。
- **Submission Executor（Playwright 预填）**：新增 `services/submission_executor.py`，基于 Playwright（同步 API + ThreadPool，不升级 Flask 架构）打开招聘网站表单 → 定位字段 → 逐字段匹配 answer_bank/profile → 填值（**不点提交**）→ 截图存证 → 写 `application_submissions` 表。
- **Safety Guard（安全边界引擎）**：新增 `services/safety_guard.py`，表单解析时命中敏感字段（身份/法律/薪酬/现状/金融）强制 `awaiting_human`；答案库未命中也停；绝对禁止点击 `提交/Apply/确认` 按钮。借鉴 JobHuntBot `safety-and-boundaries.md`。
- **6 个新 MCP 工具**：`get_answer_bank` / `upsert_answer_bank` / `delete_answer_bank` / `prefill_application_form` / `record_submission_result` / `get_resume_for_role`。36 → 42。
- **Application Executor Skill**：`skills/application-executor/SKILL.md`，完整工作流、安全门清单、ATS 处理手册。借鉴 JobHuntBot `SKILL.md` + `application-playbook.md`。
- **Web UI**：新增 `/submissions` 路由 + `templates/submissions.html` 审核页，展示预填 JSON、截图、待审字段，一键跳转真实页面继续。

## Capabilities

### New Capabilities
- `answer-bank`：可复用答案库 + 经历库持久化 + profile 敏感字段直通 + 提交历史自动沉淀。
- `submission-prefill`：`待提交` 状态流转 + Playwright 预填 + 存证截图 + 提交结果回写。
- `safety-guard-ats`：敏感字段安全门 + 字段黑名单 + 绝对禁止提交点击 + CAPTCHA/登录态暂停。
- `application-executor-skill`：跨平台 Skill 定义触发场景、工作流、安全边界、ATS 处理手册。

### Modified Capabilities
- `application-resume-binding`：扩展 status 枚举加入 `待提交`；`/to-apply` 列表增加「预填网申」入口按钮。
- `agent-task-center`：Agent 任务中心增加预填任务类型与 SSE 轨迹事件。

## Impact

- **`models.py`**：新增 `AnswerBank`、`ExperienceBank`、`ApplicationSubmission` 3 个模型。
- **`constants.py`**：新增 `PRE_SUBMIT_STATUS = '待提交'`；新增敏感字段黑名单 `SENSITIVE_FIELD_PATTERNS`。
- **`mcp_server.py`**：+6 MCP 工具（36 → 42）。
- **`services/submission_executor.py`**：新增 Playwright 预填封装（同步 API + ThreadPoolExecutor）。
- **`services/safety_guard.py`**：新增安全边界检查器。
- **`routes/submission.py`**：新增 Web 路由。
- **`templates/submissions.html`** + `templates/to_apply.html` 改动：预填入口 + 审核页。
- **`migrations/versions/xxx_add_submission_tables.py`**：Alembic 迁移脚本。
- **`skills/application-executor/SKILL.md`**：新增 Skill。
- **`requirements.txt`** + `requirements-ai.txt`：追加 `playwright`。
- **`tests/test_submissions.py`** + **`tests/test_safety_guard.py`**：新增测试。
