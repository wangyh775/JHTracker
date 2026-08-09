## Purpose

在 JHTracker 现有 status 流转中插入 `待提交`（Pre-Submit）中间态，由 Agent 通过 Playwright 完成招聘网站表单预填（**不点击提交**）并截图存证，人类在 Web 审核后跳转真实页面自行提交。提交结果回写数据库，**绝不越过 Post-Application 只读保护**。

## ADDED Requirements

### Requirement: `待提交` Status 与流转
系统 SHALL 在 Application status 枚举中新增 `待提交`，流转为：`待投递 ──prefill──→ 待提交 ──human_submit──→ 已投递`；失败可 `待提交 ──failure──→ 待投递`。

#### Scenario: 预填成功流转
- **WHEN** MCP `prefill_application_form(application_id, form_url)` 执行成功并写入 prefilled_data
- **THEN** Application.status SHALL 从 `待投递` 变为 `待提交`；对应 `ApplicationSubmission.status = 'prefilled'`。

#### Scenario: 失败回退
- **WHEN** `prefill_application_form` 因表单无法定位 / 页面加载失败等中断
- **THEN** Application.status SHALL 保持或回退到 `待投递`；`ApplicationSubmission.status = 'failed'` 并填 `failure_reason`。

### Requirement: `ApplicationSubmission` 存证
系统 SHALL 持久化 `ApplicationSubmission` 记录，字段：`id`、`application_id`、`form_url`、`prefilled_data`（JSON）、`agent_trace_id`、`status`（prefilled/awaiting_human/submitted/failed）、`human_approved_at`、`submitted_at`、`screenshot_path`、`failure_reason`。

### Requirement: Playwright 预填不点提交
`prefill_application_form` 实现 SHALL：
1. 用 Playwright（同步 API）打开 `form_url`（headless=False 以便人审）；
2. 解析可见表单字段（label/name/id/placeholder 组合）；
3. 逐字段经 `safety_guard.classify_field()` 分类并取答案；
4. 填值（input/select/textarea/radio），**绝对不调用 `提交/Apply/确认` 类按钮点击**；
5. 取全屏截图存 `data/submissions/{app_id}_{ts}.png`；
6. 写入 `ApplicationSubmission` + 状态变更。

#### Scenario: 命中禁止按钮
- **WHEN** Playwright 脚本尝试定位到文本包含 `提交|Apply|确认投递|Submit` 的按钮
- **THEN** 系统 SHALL 跳过点击，仅在 agent_trace 中记 `safety_blocked_click` 事件。

### Requirement: 人类提交结果回写
MCP `record_submission_result(application_id, success, screenshot_path, failure_reason, extracted_answers)` SHALL：
- success=True → Application.status = `已投递`、`apply_date = today`、ApplicationSubmission.status = `submitted`、`submitted_at = now`；
- success=False → Application.status = `待投递`（回退）、ApplicationSubmission.status = `failed`；
- 提取 `extracted_answers` 触发 answer-bank 自动沉淀（见 answer-bank spec）。

#### Scenario: 人类提交成功
- **WHEN** 人类在真实页面点完提交后，在 Web UI 点击「已提交」
- **THEN** 系统 SHALL 自动调用 `record_submission_result(success=true)` 并写回状态。

### Requirement: 现有 Post-Application 只读保护不变
`update_application_status` MCP 工具与 Web 端 SHALL 仍然阻止 Agent 对 `已投递` 及之后状态的修改；Agent 仅能写 `待投递 ↔ 待提交` 之间的流转。
