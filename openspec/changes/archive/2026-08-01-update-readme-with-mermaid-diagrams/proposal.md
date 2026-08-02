## Why

README.md 和 docs/README.md 中的图表（`product-diagram.png`、Mermaid 架构图）与当前最新架构（分层检索协议、前/后投递状态解耦、双向记忆反馈、新 MCP 资源端点）存在脱节，需要删除旧图并补充 4 张新的 Mermaid 图以直观反映系统全貌。

## What Changes

- **删除** `docs/product-diagram.png` 旧 PNG 图
- **删除** README.md 中旧的 `Agent-Native & Career OS 架构一览` 流水图
- **更新** README.md 特性章节补充 4 张 Mermaid 图表：
  1. 系统架构与接口拓扑图
  2. 岗位多阶生命周期与权限隔离图
  3. 分层检索协议与真实性验证闭环图
  4. 人在回路与双向记忆闭环图
- **更新** docs/README.md 中的系统一览 Mermaid 图

## Capabilities

### New Capabilities

### Modified Capabilities
- `skills-and-mcp-documentation`: README 和 docs 中的图表需更新以反映最新架构

## Impact

- `README.md` — 删除旧图，补充 4 张 Mermaid 图
- `docs/README.md` — 更新系统一览图
- `docs/product-diagram.png` — 删除