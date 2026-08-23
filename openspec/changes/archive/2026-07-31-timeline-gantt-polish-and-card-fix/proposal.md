## Why

时间线页面（甘特图）目前展示了所有历史与完成节点，干扰当前重点关注的即将截止事件与行动项；同时投递记录页面（`applications.html`）存在 `<div>` 标签未闭合结构 Bug，导致卡片逐层嵌套堆叠，影响视觉。

## What Changes

- **修复 `applications.html` 卡片嵌套堆叠 Bug**：在循环末尾补充缺失的闭合 `</div>`，恢复独立标准的单卡片布局。
- **时间线甘特图与列表重构**：
  - 在甘特图和节点详情列表中默认隐藏已完成（`done == true`）与已过期（`end_date < today`）节点。
  - 增加顶部动态筛选开关（显示/隐藏已完成，显示/隐藏已过期）。
  - 甘特图视觉升级：高对比分类配色、包含今日参考线的图表配置、微卡片列表排版。

## Capabilities

### New Capabilities
- `timeline-gantt-enhancement`: 时间线甘特图节点状态过滤、动态开关与视觉样式重构

## Impact

- `templates/applications.html` — 闭合缺失的 `div` 标签，消除卡片嵌套堆叠问题
- `templates/timeline.html` — 添加过滤控制开关、重构 Chart.js 甘特图与微卡片列表
- `routes/timeline.py` — 支持按状态过滤参数接收（可选）