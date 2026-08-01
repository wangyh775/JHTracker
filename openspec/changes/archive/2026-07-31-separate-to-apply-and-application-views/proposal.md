## Why

当前「投递记录」页面将智能体未审批的提案（`Pending Approval`）、待投递岗位（`待投递`）与真正的投递追踪（`已投递`、`面试`、`Offer` 等）混在一起，导致页面混乱，且智能体接口可以直接写入和混入用户的正式投递流水。

需要将“投递前”的准备与“投递后”的记录明确剥离，新增独立的「待投递清单」页面，同时将「投递记录」定位为纯人工管控与只读的数据流水。

## What Changes

- **新增「待投递」独立视图 (`/to-apply`)**：
  - 专门展示人类在 Decision Inbox 中点击「批准 (Approve)」后转入的待投递岗位（状态为 `待投递`）。
  - 提供快速关联简历版本、查看 JD 链接、发起真正投递并填报渠道/薪资的能力。
- **重构「投递记录」视图 (`/applications`)**：
  - 过滤排除 `Pending Approval` 和 `待投递` 状态，仅保留已发生投递动作的真正流程节点（`已投递`、`简历筛选`、`笔试`、`一面`、`二面`、`终面`、`Offer`、`已拒`）。
  - 投递记录全权归人工掌控，智能体仅拥有只读与分析建议权限，禁止智能体直接修改已投递记录。
- **侧栏导航更新**：
  - 在侧栏「投递跟踪」分组中增加「待投递」入口。

## Capabilities

### New Capabilities
- `to-apply-management`: 独立「待投递」备选岗位清单与投递动作触发管理
- `manual-application-tracking`: 「投递记录」过滤隔离与人工专属写权限控制

## Impact

- `routes/application.py` — 新增 `/to-apply` 路由，更新 `/applications` 过滤逻辑
- `templates/to_apply.html` — 新增待投递视图模板
- `templates/applications.html` — 更新列表渲染与状态排除过滤
- `templates/_sidebar.html` — 增加「待投递」导航链接
- `routes/agent_api.py` & `mcp_server.py` — 智能体接口禁止修改已投递记录状态