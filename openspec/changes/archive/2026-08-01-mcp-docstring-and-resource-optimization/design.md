## Context

See `proposal.md`. `mcp_server.py` 当前 1228 行，30+ 个 tool，仅 1 个 resource (`jhtracker://profile`)。多个 docstring 与最新状态分层架构脱节，`get_statistics` 缺少 `待投递` 计数。

## Goals / Non-Goals

**Goals:**
- 更新 5 个关键工具的 docstring 以反映 Agent 权限边界与状态分层
- 在 `get_statistics` 中增加 `to_apply_count` 字段
- 新增 `jhtracker://statistics` 和 `jhtracker://memories` 两个 MCP resource

**Non-Goals:**
- 不修改任何工具的核心业务逻辑（仅改 docstring 和增加返回字段）
- 不修改数据库表结构
- 不新增工具（只新增 resource）

## Decisions

- **Resource vs Tool**：statistics 和 memories 用 `@mcp.resource()` 而非 `@mcp.tool()`，因为它们是纯读取操作，不需要参数，Agent 可直接读取 URI 而非调用函数。
- **docstring 更新方式**：直接在现有 docstring 中追加说明段落，不改变函数签名或逻辑。
- **`to_apply_count` 实现方式**：在 `get_statistics` 函数中增加一条 `SELECT COUNT(*) FROM applications WHERE status = '待投递'` 查询，加入返回 JSON。

## Risks / Trade-offs

- [Resource 返回 JSON 格式] → FastMCP resource 默认返回字符串，需要 `json.dumps` 序列化，Agent 端需自行解析。与现有 `jhtracker://profile` 返回纯文本不同。