# Proposal: cn-sourcing-ats-first

## What & Why

当前 `job-sourcing-and-scoring` skill 的分层检索协议以通用 web 工具（Firecrawl / Exa / Tavily / webfetch）为主，对国内招聘生态适配不足：

1. **缺失国内 ATS 直连层**。校招网申 70%+ 走北森（Beisen）、Moka、牛客网、应届生求职网，这些平台的招聘页有公开 JSON 接口、无需鉴权、字段结构化、反爬弱。当前流程直接从通用搜索入手，token 成本高、字段不稳定。
2. **Layer 顺序倒挂**。CDP（Playwright）成本和风险最高，却排在 Firecrawl 之后、Exa 之前。应该按"免费稳定源 → 结构化爬虫 → 通用搜索 → 高风险 CDP 兜底"重排。
3. **平台路由一维化**。只按"央国企/外企/民企"一维路由到平台首页，未区分校招/社招场景。国内校招与社招数据源差异巨大（校招走 ATS + 校园招聘专区，社招走 BOSS/智联/猎聘）。
4. **网申入口未传递**。sourcing 找到岗位后未识别 `form_type`（结构化简历表单 / 开放式问题 OQ / 附件上传 / 一键投递），导致下游 `application-executor` 无法针对性选择填写策略。

## Proposed Change

### 1. 新增 MCP 工具 `JHTracker:fetch_ats_jobs`

封装国内主流 ATS 平台公开接口，作为 sourcing 的 Layer 0（最优先层）：

- **北森（Beisen）**：`m.beisen.com` 系列接口，覆盖央企/国企/大厂校招
- **Moka**：`app.mokahr.com/api`，覆盖民企大厂/外企校招
- **牛客网**：`nowcoder.com` 校招岗位搜索
- **应届生求职网**：`yingjiesheng.com` 校招聚合

工具入参：`ats_provider`, `keyword`, `city`, `page`，返回标准化字段：`title`, `company`, `location`, `salary`, `apply_url`, `form_type`, `raw`。

### 2. 升级 layered-retrieval-protocol spec

重排 Layer 顺序为：

```
Layer 0: 国内 ATS 直连（JHTracker:fetch_ats_jobs）← 新增
Layer 1: 平台结构化爬虫（Firecrawl）  ← 原 Layer 1
Layer 2: 通用搜索兜底（Exa + Tavily）   ← 原 Layer 3/4
Layer 3: CDP 高风险源（Playwright）     ← 原 Layer 2 降级
Layer 4: webfetch 终极兜底              ← 原 Layer 5
```

### 3. 平台路由二维化

把 `enterprise_preference × scenario`（校招/社招）作为路由维度：

| | 校招（网申） | 社招 |
|---|---|---|
| 央国企 | 北森/国聘/Moka | 国聘/猎聘 |
| 外企 | Workday/Greenhouse/Moka | LinkedIn/猎聘 |
| 民企大厂 | Moka/北森 | BOSS/拉勾 |
| 民企创业 | Moka/牛客 | BOSS/拉勾 |

### 4. 网申入口识别（`form_type`）

sourcing 找到岗位后，从 `apply_url` 域名识别 `form_type`，写入 application 记录，供 `application-executor` 消费：

| form_type | 域名特征 | 填写策略 |
|---|---|---|
| `structured` | beisen.com, mokahr.com | AnswerBank 直接取值 |
| `open_question` | 快消/咨询校招页 | AnswerBank + LLM 生成 |
| `attachment` | workday.com | 跳过表单，走简历生成 |
| `one_click` | zhipin.com | 不需要 prefill |

## Out of Scope

- BOSS直聘 CDP 字体反爬破解（维护成本高，放 Phase 2 后再做）
- 智联招聘内部接口逆向（灰色地带，暂不接入）
- LLM 生成 OQ 答案（属 application-executor 范畴，本变更只识别 form_type 并传递）
