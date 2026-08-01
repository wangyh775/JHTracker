## Why

MCP 审计发现多个工具 docstring 与最新架构（投递前/后状态解耦、Agent 只读防护、`Pending Approval` 提案制）存在脱节，且缺少 `待投递` 统计计数和可读取的 MCP 资源，导致 Agent 调用时行为预期不清晰。

## What Changes

- **P0: `update_application_status` docstring 补充 Agent 禁止声明**：明确声明 Agent 不能设置 `POST_APPLY_STATUS_LIST` 中的状态，仅可操作 `STAGED_STATUS_LIST` 范围内的记录。
- **P0: `get_statistics` 增加 `待投递` 计数**：新增 `to_apply_count` 字段统计 `status = '待投递'` 的记录数量。
- **P1: `get_pending_approvals` docstring 明确排除 `待投递`**：注明仅返回 `Pending Approval` / `待审批` 状态的记录，不含已批准待投递项。
- **P1: `search_companies` / `get_company` docstring 补充返回字段说明**：注明返回字段列表、LIMIT、排序规则。
- **P2: 新增 `jhtracker://statistics` MCP 资源**：Agent 可直接读取仪表盘统计而无需调用 tool。
- **P2: 新增 `jhtracker://memories` MCP 资源**：Agent 可直接读取偏好记忆规则全集用于预筛。

## Capabilities

### New Capabilities
- `mcp-resource-endpoints`: 新增 MCP 资源端点 (`jhtracker://statistics` 和 `jhtracker://memories`) 供 Agent 直接读取

### Modified Capabilities
- `mcp-server`: 多个工具 docstring 需更新以反映 Agent 只读防护与状态分层；`get_statistics` 需增加 `待投递` 计数