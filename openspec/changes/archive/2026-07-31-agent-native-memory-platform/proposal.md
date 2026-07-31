## Why

JHTracker 目前定位偏向传统的单体 Web 管理应用，缺乏对大模型与 AI 智能体 (Hermes, OpenCode, Claude Desktop, Cursor 等) 的标准化抽象。为了将 JHTracker 从“单纯的 CRUD 管理工具”升维为“面向 AI 智能体生态的通用职业数据基础设施与记忆中枢 (Agent-Native Career Memory & Workflow Platform)”，需要提供标准化的 Agent 访问接口、实时事件推送到 UI、智能体行为 Trace 追踪，以及 MCP (Model Context Protocol) 访问能力。

## What Changes

- **MCP Server 原生支持与 API 端点**：在 `routes/` 中新增 `agent_api.py` 及 `mcp_server.py`，并在 `docs/` 下配套更新 `api.md`、`database.md` 与 `architecture.md`。
- **Agent Trace 与事件体系**：新增 `AgentTask` 与 `AgentEvent` 数据模型并做数据库迁移。
- **界面与数据协同升级**：整合已实现的 SQLite WAL 高并发模式与 SSE 实时更新通知，在 Dashboard 呈现 AI 匹配度与薪资分布图及 Agent 动态追踪。

## Capabilities

### New Capabilities
- `agent-api`: 提供面向 Agent 的标准化 RESTful JSON 接口与数据导出机制。
- `mcp-server`: 提供 Model Context Protocol (MCP) 原生 Server 支持，供支持 MCP 的客户端直接调用工具。
- `agent-trace`: 存储并展示智能体的执行轨迹 (Reasoning Trace) 与任务日志。

### Modified Capabilities
(none)

## Impact

- **数据层**：在 `models.py` 中新增 `Agent`、`AgentTask`、`AgentEvent` 模型并做 Alembic/Flask-Migrate 数据库迁移。
- **路由层**：在 `routes/` 中新增 `agent_api.py` 及 `mcp.py` 关联路由。
- **集成与拓展**：支持 MCP Protocol (FastMCP/mcp SDK) 独立运行与协同。
