## Context

See `proposal.md`. `README.md` 顶部的 `docs/product-diagram.png` 已过时，且缺乏对分层检索协议、待投递隔离、双向记忆飞轮等最新特性的可视化展现。

## Goals / Non-Goals

**Goals:**
- 删除 `docs/product-diagram.png`
- 在 `README.md` 中嵌入 4 张高清晰度 Mermaid 流程图/架构图：
  1. 系统架构与接口拓扑图 (`flowchart TB`)
  2. 岗位多阶生命周期与权限隔离图 (`flowchart LR`)
  3. 分层检索协议与真实性验证闭环图 (`flowchart TB`)
  4. 人在回路与双向记忆闭环图 (`flowchart TB`)
- 在 `docs/README.md` 中同步更新系统一览图

**Non-Goals:**
- 不增加外部图片依赖（全部使用 Markdown 内置 Mermaid 代码块，保证在 GitHub 上原生直接渲染）

## Decisions

- **纯代码块选型 (Mermaid)**：使用纯代码块 Markdown Mermaid 替代静态 PNG，优点是零依赖、无破损风险、支持版本管理和协同修改。
- **图表位置安排**：
  - 图 1 放在 `README.md` 的 "Agent-Native & Career OS 架构一览" 章节
  - 图 2 放在 "投递全流程跟踪" 特性中
  - 图 3 放在 "Agent-Native 原生接口与 MCP" 特性中
  - 图 4 放在 "HITL 人机协同闭环" 特性中

## Risks / Trade-offs

- [部分 Markdown 渲染器不支持 Mermaid] → GitHub / GitLab / VS Code / Cursor / Obsidian 原生均支持 Mermaid 渲染。