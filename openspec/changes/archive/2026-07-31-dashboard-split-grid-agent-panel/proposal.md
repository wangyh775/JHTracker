## Why

Dashboard 底部全宽平铺的 Decision Inbox（待审批岗位推荐）与 Agent Task Center 占据页面下半部分，过于扁平死板，且迫使用户滚动到页面最底才能进行 HITL 审批。将 Dashboard 布局重构为「左侧数据与分析主区 (col-lg-8) + 右侧 Agent 协同控制栏 (col-lg-4)」双栏分屏结构，能把待审批推荐和 Agent 轨迹提升至首屏黄金右上角，极大提升人机协同交互体验。

## What Changes

- **Dashboard 双栏分屏重构**：页面整体划分为左侧 8 列（统计卡片、投递漏斗、城市/行业分布饼图、匹配度散点图）与右侧 4 列（Agent 协同侧栏）。
- **右侧 Agent 协同侧栏 (Agent Co-Pilot Panel)**：
  - 顶部放置 **Decision Inbox (待审批岗位推荐)**，垂直列形式呈现为微型卡片，固定最大高度（如 380px）内部滚动。
  - 中部放置 **Agent Task Center (任务轨迹)**，固定最大高度（如 260px）内部滚动。
  - 底部放置 **待办节点 & 最近动态**，构成一体化右侧控制区。
- **微型推荐卡片优化**：优化 Decision Inbox 内卡片的垂直排布与样式，增加鼠标悬浮高亮效果 (Hover Border Glow)。

## Capabilities

### New Capabilities
- `dashboard-split-grid`: Dashboard 采用左 8 右 4 分屏栅格，右侧为 Agent 协同控制侧栏，把 Decision Inbox 与 Agent Task Center 置于首屏右上区域

### Modified Capabilities
<!-- No requirement breaking changes -->

## Impact

- `templates/dashboard.html` — 重构 HTML 栅格结构与右侧 Agent Panel 布局
- `docs/hitl-feedback-loop.md` — 更新 Dashboard 布局与交互示意图