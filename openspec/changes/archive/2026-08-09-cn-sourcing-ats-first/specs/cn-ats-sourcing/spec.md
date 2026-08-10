## Purpose

提供国内主流 ATS 平台（北森、Moka、牛客、应届生求职网）的直连接口，作为分层检索协议的 Layer 0，让 AI Agent 能以最低成本获取结构化岗位数据并识别网申类型。

## Requirements

### Requirement: MCP Tool `fetch_ats_jobs`

系统 SHALL 提供 MCP 工具 `JHTracker:fetch_ats_jobs`，封装国内 ATS 平台的公开 JSON 接口，对 Agent 屏蔽各平台接口差异。

#### Scenario: Agent 调用 fetch_ats_jobs 查询单平台
- **WHEN** Agent 调用 `fetch_ats_jobs(provider="moka", keyword="嵌入式", city="深圳")`
- **THEN** 系统 SHALL 调用 Moka 公开接口 `app.mokahr.com/api/apply/spa/positions/search`
- **THEN** 系统 SHALL 返回标准化字段 `{title, company, location, salary, apply_url, form_type, source_platform}` 的列表

#### Scenario: provider=all 并发查询全部平台
- **WHEN** Agent 调用 `fetch_ats_jobs(provider="all", keyword="嵌入式")`
- **THEN** 系统 SHALL 并发调用 beisen / moka / nowcoder / yingjiesheng 四个适配器
- **THEN** 系统 SHALL 合并结果并按 (company, title) 去重
- **THEN** 单个适配器失败时 SHALL NOT 阻塞其他适配器，失败平台在返回结果的 `errors` 字段中标注

#### Scenario: 缺少必需参数
- **WHEN** Agent 调用 `fetch_ats_jobs(provider="moka")` 但未提供 `company_slug` 且无法从 keyword 推断
- **THEN** 系统 SHALL 返回 `{jobs: [], error: "company_slug required for moka provider"}` 而非抛异常

### Requirement: 标准化 Job 字段

所有 ATS 适配器 SHALL 返回统一的 `AtsJob` 结构，确保下游 skill 与 application-executor 无需感知平台差异。

#### Scenario: 字段标准化映射
- **WHEN** 北森接口返回 `{JobName, CompanyName, WorkPlaceName, SalaryStr, Url}`
- **THEN** 系统 SHALL 映射为 `{title: JobName, company: CompanyName, location: WorkPlaceName, salary: SalaryStr, apply_url: Url, source_platform: "beisen"}`
- **THEN** 缺失字段 SHALL 填充为 `None` 而非省略

#### Scenario: salary 字段标准化
- **WHEN** 平台返回薪资为 "面议" 或空字符串
- **THEN** 系统 SHALL 统一返回 `salary: None`
- **WHEN** 平台返回 "15-30K·14薪"
- **THEN** 系统 SHALL 保留原始字符串，不做数值解析（数值解析由 ai-scoring 负责）

### Requirement: form_type 识别

系统 SHALL 从 `apply_url` 域名识别网申类型 `form_type`，写入返回结果，供 application-executor 选择填写策略。

#### Scenario: 北森/Moka 识别为 structured
- **WHEN** `apply_url` 匹配 `beisen.com` 或 `yingjiesheng.com` 或 `mokahr.com`
- **THEN** 系统 SHALL 设置 `form_type = "structured"`

#### Scenario: Workday/Greenhouse 识别为 attachment
- **WHEN** `apply_url` 匹配 `workday.com` 或 `greenhouse.io` 或 `lever.co`
- **THEN** 系统 SHALL 设置 `form_type = "attachment"`

#### Scenario: BOSS 直聘识别为 one_click
- **WHEN** `apply_url` 匹配 `zhipin.com`
- **THEN** 系统 SHALL 设置 `form_type = "one_click"`

#### Scenario: 未命中规则默认 open_question
- **WHEN** `apply_url` 不匹配任何已知规则
- **THEN** 系统 SHALL 设置 `form_type = "open_question"`（最保守，会走 awaiting_human）

### Requirement: 各 ATS 适配器独立容错

每个 ATS 适配器 SHALL 独立 try/except，单家失败不阻塞其他平台。

#### Scenario: 北森接口超时
- **WHEN** 北森接口 10 秒未响应
- **THEN** 系统 SHALL 跳过北森结果
- **THEN** `provider="all"` 模式下 SHALL 仍返回其他平台结果
- **THEN** 返回结果的 `errors` 字段 SHALL 包含 `{"beisen": "timeout after 10s"}`

#### Scenario: Moka orgId 无效
- **WHEN** 提供的 `company_slug` 在 Moka 上不存在
- **THEN** 系统 SHALL 返回 `{jobs: [], error: "invalid orgId"}` 而非抛 HTTP 错误

### Requirement: form_type 透传到 application 记录

Agent 调用 `create_application` 创建岗位时 SHALL 传入 `form_type`，系统 SHALL 写入 `applications.form_type` 字段。

#### Scenario: create_application 接收 form_type
- **WHEN** Agent 调用 `create_application(form_type="structured", source_platform="beisen", ...)`
- **THEN** 系统 SHALL 将 `form_type` 与 `source_platform` 写入 application 记录
- **WHEN** 未传 `form_type`
- **THEN** 系统 SHALL 写入默认值 `form_type = "open_question"`

### Requirement: profile.md 支持 job_scenario 字段

系统 SHALL 支持 `data/profile.md` 中的 `job_scenario` 字段（校招/社招/实习），用于二维路由。

#### Scenario: 读取 job_scenario
- **WHEN** Agent 启动 sourcing 任务
- **THEN** Agent SHALL 从 `data/profile.md` 读取 `job_scenario` 字段
- **WHEN** 字段缺失
- **THEN** Agent SHALL 询问用户并写入 profile 供后续会话使用
