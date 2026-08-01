## Context

See `proposal.md`. 当前 `/applications` 路由未排除 `Pending Approval` 与 `待投递` 状态，导致未审批提案与预备投递项直接暴露在正式投递流水中。智能体 API / MCP 缺乏对其改写人工确认状态记录的防护。

## Goals / Non-Goals

**Goals:**
- 在 `routes/application.py` 中新增 `GET /to-apply` 路由及 `templates/to_apply.html` 视图，展示人类批准后、尚未正式向企业发起的岗位。
- 修改 `/applications` 过滤条件，排除 `Pending Approval`、`待审批` 和 `待投递`，仅展示已投递及后续节点。
- 在 `_sidebar.html` 的「投递跟踪」菜单中加入「待投递」入口。
- 在 Agent API 和 MCP 工具中增加防护：禁止对已处于正式流程状态的记录做直接改写。

**Non-Goals:**
- 不改变数据库 `applications` 表结构（复用现有字段）。
- 不破坏现有面试反馈与 Offer 对比功能。

## Decisions

- **使用专有路由 `/to-apply` 与专有模板 `to_apply.html`**：
  保持 URL 语义清晰，不与参数式的 `/applications?view=to_apply` 混淆。
- **状态列表重构 (`constants.py`)**：
  明确定义 `POST_APPLY_STATUS_LIST = ['已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer', '已拒']` 与 `STAGED_STATUS_LIST = ['Pending Approval', '待审批', '待投递']`。
- **MCP & REST 写入防护**：
  在 `mcp_server.py` 和 `routes/agent_api.py` 的更新/修改工具中检查 `status`，如果记录已属于 `POST_APPLY_STATUS_LIST`，则阻止 Agent 的修改请求。

## Risks / Trade-offs

- [已有数据状态适配] 现有的 `待投递` 记录在页面更新后会从 `/applications` 移至 `/to-apply` → 用户无需做任何数据迁移，数据逻辑保持自然流动。