## Why

MCP 已从 9 个工具扩展到 36 个，HITL 闭环已实现，但文档多处停留在旧状态。`docs/api.md` 的 MCP 工具列表还是 9 个，根目录 `README.md` 的特性和架构图未反映 36 个工具和 HITL 能力，设计哲学（Agent-First、Human-in-the-Loop、Data Sovereignty）没有在任何地方统一表述。

## What Changes

- **`docs/api.md`**：MCP 工具列表从 9 个更新到 36 个，按 11 个数据域分组
- **`docs/README.md`**（文档中心）：增加设计哲学章节
- **根目录 `README.md`**：更新特性列表、MCP 工具列表、架构图 tools 区块、增加设计哲学章节
- **`docs/architecture.md`**：设计决策表增加 "MCP 覆盖全部 REST API 能力"、"Agent 自主执行 / 删除需审批"、"三原则设计哲学"

## Capabilities

### New Capabilities
- `design-philosophy-docs`: 统一表述 JHTracker 三大设计哲学（Agent-First, Human-in-the-Loop, Data Sovereignty），并同步到所有相关文档

### Modified Capabilities
<!-- No existing specs change behavior -->

## Impact

- `docs/api.md` — MCP 工具列表 9→36，按域分组
- `docs/README.md` — 增加设计哲学章节
- `README.md`（根目录）— 更新特性、MCP 列表、架构图、增加设计哲学
- `docs/architecture.md` — 设计决策表增加 3 条