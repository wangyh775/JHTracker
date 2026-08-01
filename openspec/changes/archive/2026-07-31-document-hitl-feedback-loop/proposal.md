## Why

JHTracker 已实现完整的 HITL 闭环（DecisionFeedback/Memory 模型、决策 API、Decision Inbox UI、evaluate_jd 反馈注入），但 docs/ 文档停留在归档功能前的状态，缺少 HITL 相关记录。文档缺口导致新贡献者无法理解系统核心能力，也增加了维护风险。

## What Changes

- **补 `docs/database.md`**：新增 `DecisionFeedback`、`Memory` 两张表及 `Application.decision_feedbacks` 关系
- **补 `docs/api.md`**：新增 `/api/agent/tasks`、`/api/agent/decisions/pending`、`/api/agent/decisions/<id>`、`GET /api/v1/companies` 等端点
- **补 `docs/SKILLS_AND_MCP_GUIDE.md`**：新增 `evaluate_jd`、`record_agent_trace`、`update_candidate_profile` 三个 MCP 工具
- **新建 `docs/hitl-feedback-loop.md`**：HITL 闭环专题文档，覆盖模型→API→MCP→UI→评分引擎全链路
- **更新 `docs/README.md`**：文档索引增加 HITL 专题文档链接

## Capabilities

### New Capabilities
- `hitl-feedback-loop-docs`: 完整的 HITL 闭环专题文档，描述 Agent 推荐→人审核→反馈→记忆→评分纠偏的闭环设计

### Modified Capabilities
- `database-docs`: 数据库文档增加 `DecisionFeedback`、`Memory` 表及关系
- `api-docs`: API 文档增加 HITL 决策端点与 Agent Task 端点
- `mcp-skills-guide`: MCP 与 Skills 指南增加 evaluate_jd 等工具描述

## Impact

- `docs/database.md` — 更新表清单、ER 图、字段说明
- `docs/api.md` — 更新 Agent API 端点表格
- `docs/SKILLS_AND_MCP_GUIDE.md` — 更新 MCP 工具列表
- `docs/README.md` — 更新文档索引
- 新增 `docs/hitl-feedback-loop.md` — 无代码变更，纯文档