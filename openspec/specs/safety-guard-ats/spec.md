## Purpose

在 Playwright 预填与 MCP 工具调用中，强制执行身份/法律/薪酬/现状/金融 5 类敏感字段安全门，以及「绝不能自动点提交」的硬约束。借鉴 JobHuntBot `safety-and-boundaries.md`。

## ADDED Requirements

### Requirement: 敏感字段分类
`services/safety_guard.classify_field(label_text, name_attr, id_attr, placeholder)` SHALL 按正则黑名单返回分类：

| 分类 | 匹配关键词 | 命中后的强制行为 |
|---|---|---|
| `identity` | 身份证/护照/SSN/ID.?number/National.?ID | 只能从 profile 取，缺失 → `awaiting_human` |
| `legal` | 签证/sponsorship/work.?auth/犯罪/criminal/移民 | 只能从 profile 取，缺失 → `awaiting_human` |
| `compensation` | 薪资/salary/compensation/expect.*pay/wage | 只能从 profile.target_salary 取，缺失 → `awaiting_human` |
| `current_status` | 推荐人/reference/现任雇主/在职状态/employment.?status | 只能从 profile 取，缺失 → `awaiting_human` |
| `financial` | 银行/bank.?account/tax/社保/公积金 | 只能从 profile 取，缺失 → `awaiting_human` |
| `benign` | 其他 | 允许答 AnswerBank / 缺省为空后问人 |

#### Scenario: 命中签证问题
- **WHEN** 表单 label 含 "Do you require sponsorship?"
- **THEN** 分类 SHALL = `legal`，只能从 profile.work_authorization 取；若缺失则标记该字段为 `missing_human_input`，绝不填入默认值。

### Requirement: 禁止点击提交按钮
`SafetyGuard.is_submit_button(btn_text, btn_type, btn_id)` SHALL 在匹配到文本/属性中含有 `提交|Apply|确认投递|Submit|Finalize|投递简历` 时返回 True。Playwright 脚本 SHALL 在每次点击前经此检查，命中则跳过并记录 `safety_blocked_click` 轨迹。

#### Scenario: 自动识别提交按钮
- **WHEN** Agent 欲点击的元素文本 = "Apply Now"
- **THEN** is_submit_button 返回 True → 不执行 click() → `record_agent_trace(event_type='safety_blocked_click')`

### Requirement: 未识别字段暂停
若表单字段未命中 AnswerBank 且非 benign 类（即「敏感且 profile 缺」或「非敏感但库缺」），系统 SHALL 暂停预填并将 ApplicationSubmission.status 设为 `awaiting_human`，同时把待填清单返回给人审页。

### Requirement: CAPTCHA/登录态暂停
当 Playwright 检测到页面出现 `<iframe title="CAPTCHA">`、`<div recaptcha>` 或被 302 到登录页时，系统 SHALL 暂停并切换到 `awaiting_human`，同时在 Web UI 提示「请手动处理登录或验证后继续」。
