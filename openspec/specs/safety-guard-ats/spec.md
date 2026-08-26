## Purpose

在 Playwright 预填与 MCP 工具调用中，强制执行身份/法律/薪酬/现状/金融 5 类敏感字段安全门，以及「绝不能自动点提交」的硬约束。借鉴 JobHuntBot `safety-and-boundaries.md`。
## Requirements
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

#### Scenario: 遇到未知必填项
- **WHEN** 表单中出现未识别且画像中不存在的高危必填字段
- **THEN** 系统暂停自动填表并将状态置为 `awaiting_human`。

### Requirement: CAPTCHA/登录态暂停
当 Playwright 检测到页面出现 `<iframe title="CAPTCHA">`、`<div recaptcha>` 或被 302 到登录页时，系统 SHALL 暂停并切换到 `awaiting_human`，同时在 Web UI 提示「请手动处理登录或验证后继续」。

#### Scenario: 页面出现人机验证验证码
- **WHEN** 页面加载出验证码拦截 iframe
- **THEN** 系统立即暂停自动化并转交人工介入。

### Requirement: 数据库与核心画像防误删熔断保护 (Database & Asset Destruction Guard)
系统 SHALL 禁止在非测试环境（`TESTING=False`）下任意调用 `db.drop_all()` 或批量删除 `data/` 核心文件。若需执行危险重构或破坏性操作，必须提供显式环境变量确认（如 `ALLOW_DROP_DB=I_KNOW_WHAT_I_AM_DOING`），并在操作前强制触发一次外部安全区快照。

#### Scenario: 生产或日常运行环境下意外触发 drop_all
- **WHEN** 在默认开发/生产模式下执行包含 `db.drop_all()` 的脚本且未设置确认环境变量
- **THEN** 系统立即抛出 `RuntimeError("CRITICAL: drop_all is forbidden in non-test environment!")` 熔断拦截，阻止表结构与数据被抹除。

#### Scenario: 测试环境隔离运行
- **WHEN** 运行 pytest 自动化测试套件
- **THEN** 测试固件严格使用内存数据库（`:memory:`）或 pytest 提供的临时目录（`tmp_path`），严禁读写或覆盖 `data/tracker.db`。

