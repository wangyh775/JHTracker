## Purpose

升级分层检索协议：新增 Layer 0（国内 ATS 直连），重排 Layer 顺序，平台路由从一维改为二维（enterprise_preference × job_scenario），并定义 Layer 0 命中时的降级规则。

## Requirements

### Requirement: 新增 Layer 0 国内 ATS 直连

系统 SHALL 在分层检索协议的最前端新增 Layer 0，优先调用 `JHTracker:fetch_ats_jobs` 从国内 ATS 平台直连获取岗位。

#### Scenario: Layer 0 优先调用
- **WHEN** Agent 开始 sourcing 任务且 `job_scenario` 为"校招"
- **THEN** Agent SHALL 首先调用 `fetch_ats_jobs(provider="all", keyword=...)` 触发 Layer 0
- **THEN** Agent SHALL NOT 在 Layer 0 未执行前直接进入 Layer 1

#### Scenario: Layer 0 命中足够结果
- **WHEN** Layer 0 返回 ≥3 条去重后的有效结果
- **THEN** Agent SHALL 停止检索，不进入 Layer 1
- **THEN** Agent SHALL 将结果走 Authenticity Verification Gate 后写入数据库

#### Scenario: Layer 0 命中不足
- **WHEN** Layer 0 返回 <3 条结果
- **THEN** Agent SHALL 进入 Layer 1 补充检索
- **THEN** Agent SHALL 合并 Layer 0 + Layer 1 结果去重

### Requirement: Layer 顺序重排

系统 SHALL 采用以下优先级顺序，CDP 从原 Layer 2 降级到 Layer 3：

```
Layer 0: 国内 ATS 直连（JHTracker:fetch_ats_jobs）
Layer 1: 平台结构化爬虫（Firecrawl）
Layer 2: 通用搜索兜底（Exa + Tavily）
Layer 3: CDP 高风险源（Playwright）
Layer 4: webfetch 终极兜底
```

#### Scenario: 逐层降级
- **WHEN** Layer 0 命中 <3 条
- **THEN** Agent SHALL 尝试 Layer 1（Firecrawl 抓国聘/猎聘/海投网列表页）
- **WHEN** Layer 1 仍无结果
- **THEN** Agent SHALL 尝试 Layer 2（Exa + Tavily 通用搜索）
- **WHEN** Layer 2 仍无结果
- **THEN** Agent SHALL 尝试 Layer 3（CDP 高风险源，仅 BOSS/智联）
- **WHEN** Layer 3 仍无结果
- **THEN** Agent SHALL 尝试 Layer 4（webfetch 终极兜底）

#### Scenario: CDP 仅在前 3 层全空时触发
- **WHEN** Layer 0/1/2 任一层返回 ≥3 条结果
- **THEN** Agent SHALL NOT 进入 Layer 3 CDP
- **THEN** CDP SHALL 只在前 3 层全空时才触发，避免高风险源被频繁调用

### Requirement: 平台路由二维化

系统 SHALL 按 `enterprise_preference × job_scenario` 二维路由到不同平台，替代原一维路由。

#### Scenario: 校招 + 央国企
- **WHEN** `enterprise_preference="央国企"` 且 `job_scenario="校招"`
- **THEN** Layer 0 SHALL 调用 `fetch_ats_jobs(provider="beisen")` 优先（央企校招多走北森）
- **THEN** Layer 1 SHALL 抓取国聘（iguopin.com）校招专区

#### Scenario: 校招 + 外企
- **WHEN** `enterprise_preference="外企"` 且 `job_scenario="校招"`
- **THEN** Layer 0 SHALL 调用 `fetch_ats_jobs(provider="moka")` 优先（外企校招多走 Moka）
- **THEN** Layer 1 SHALL 抓取目标外企官网 Workday/Greenhouse 页面

#### Scenario: 校招 + 民企大厂
- **WHEN** `enterprise_preference="民企"` 且 `job_scenario="校招"`
- **THEN** Layer 0 SHALL 调用 `fetch_ats_jobs(provider="moka")` + `provider="beisen"` 并发
- **THEN** Layer 3 CDP SHALL 降级为兜底，不作为主源

#### Scenario: 社招 + 民企
- **WHEN** `enterprise_preference="民企"` 且 `job_scenario="社招"`
- **THEN** Layer 0 SHALL 跳过（ATS 直连对社招覆盖低）
- **THEN** Layer 1 SHALL 直接抓 BOSS直聘/拉勾/智联列表页
- **THEN** Layer 3 CDP SHALL 作为 BOSS直聘明文薪资的主要获取方式

#### Scenario: job_scenario 缺失时的默认行为
- **WHEN** `job_scenario` 字段缺失且无法从对话推断
- **THEN** Agent SHALL 询问用户"校招还是社招"
- **THEN** Agent SHALL 将答案写入 `data/profile.md` 的 `job_scenario` 字段

### Requirement: 原 CDP Network Interception Layer 降级

原 spec 中 "CDP Network Interception Layer" 从 Layer 2 降级到 Layer 3，定位为高风险兜底源而非主源。

#### Scenario: CDP 仅用于 BOSS/智联明文薪资
- **WHEN** Layer 0/1/2 全部无结果，或结果薪资字段全部为空
- **THEN** Agent SHALL 启动 CDP 抓取 BOSS直聘 `/wapi/zpgeek/search/joblist.json`
- **THEN** Agent SHALL 从 CDP 响应提取明文 `salaryDesc` 字段

### Requirement: form_type 传递到 Application 记录

Agent 在 Layer 0/1/2/3/4 任一层获取到岗位后 SHALL 识别 `form_type`，并在 `create_application` 时传入。

#### Scenario: Layer 0 自动携带 form_type
- **WHEN** Agent 从 `fetch_ats_jobs` 获取到岗位
- **THEN** Agent SHALL 直接使用返回结果中的 `form_type` 调用 `create_application`

#### Scenario: 非 Layer 0 来源需手动识别
- **WHEN** Agent 从 Layer 1/2/3/4 获取到岗位
- **THEN** Agent SHALL 从 `apply_url` 域名匹配 form_type 规则
- **THEN** 未命中规则时 SHALL 设置 `form_type="open_question"`

### Requirement: 保留原有 Authenticity Verification Gate

原 spec 的三步验证门（URL 可达性、内容一致性、交叉源验证）SHALL 保持不变，Layer 0 结果同样需要通过验证门。

#### Scenario: Layer 0 结果走验证门
- **WHEN** Layer 0 返回岗位列表
- **THEN** Agent SHALL 对每个候选岗位执行 URL 可达性检查
- **THEN** Agent SHALL 标记 `verified` 或 `single_source` 状态
