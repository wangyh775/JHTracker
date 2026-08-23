## Context

See `proposal.md`. `applications.html` 在第 163 行附近漏掉了关闭 `<div class="card mb-2">` 的闭合标签，导致每轮循环生成的卡片嵌套在上一张卡片内部。`timeline.html` 目前在甘特图与列表中无条件渲染所有节点，包含已完成和历史过期节点，视觉较硬。

## Goals / Non-Goals

**Goals:**
- 在 `applications.html` 中闭合缺失的 `</div>`，修复套娃堆叠问题。
- 在 `timeline.html` 的 JS `render()` 中加入可控的条件过滤：默认过滤 `item.done == true` 和 `item.end < today`。
- 在页面增加复选框控制开关：`[ ] 显示已完成` / `[ ] 显示已过期`。
- 美化甘特图图表与列表项，使用微卡片 (Micro-Cards) 样式。

**Non-Goals:**
- 不修改数据库 `timeline` 表结构。
- 不影响时间节点创建/编辑逻辑。

## Decisions

- **DOM 结构修复**：在 `applications.html` 中的 Modal 结构前方插入 `</div>` 闭合 `card` 容器。
- **JS 端纯动态过滤**：所有时间线节点保持一次性全量传到前端 JSON `items`，由 JS 根据过滤开关的 DOM 状态在 `render()` 中执行 `.filter()` 筛选，无需增加后端路由的筛选参数。

## Risks / Trade-offs

- [无节点显示] 如果所有节点都已完成或过期，图表会显示空状态 → 提示“当前暂无活动时间节点，勾选顶部【显示已完成/已过期】可查看历史”，对用户体验友好。