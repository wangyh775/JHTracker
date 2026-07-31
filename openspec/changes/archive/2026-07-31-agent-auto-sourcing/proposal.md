## Why

JHTracker 目前仅具备基本的 Agent 评分与公司搜索 API，缺乏 Agent 自动化建立公司与自动生成“待投递”状态投递记录的核心能力。为了实现彻底脱离人工繁琐操作的智能体全托管（Agent Auto-Sourcing），同时保留 Web UI 上人工完全控制的能力，需要提供公司/投递的写 API、对应 MCP 工具以及 Cron/Scheduler 工作流规范。

## What Changes

- **公司与投递写入 API**：在 `routes/agent_api.py` 中新增 `POST /api/v1/companies` (公司批量去重写入) 与 `POST /api/v1/applications` (自动生成待投递记录)。
- **MCP Server 工具拓展**：在 `mcp_server.py` 中增加 `create_company` 与 `create_application` 工具。
- **Auto-Sourcing 工作流与 Skill 升级**：升级 `skills/company-finder/SKILL.md`，并在文档中定义 Cron/Scheduler 定时任务接入规范。
- **文档优先更新**：同步更新 `docs/api.md`、`docs/database.md`、`docs/getting-started.md` 与 `docs/architecture.md`。

## Capabilities

### New Capabilities
- `auto-sourcing`: 提供面向 Agent 的公司自动去重录入、待投递应用自动创建与定时工作流调度能力。

### Modified Capabilities
(none)

## Impact

- **API & MCP 层**：`routes/agent_api.py` 与 `mcp_server.py` 新增写操作接口。
- **技能与文档层**：`skills/company-finder/SKILL.md` 及 `docs/` 目录下全部使用与接入文档。
