## 1. 常量与权限规则升级

- [x] 1.1 在 `constants.py` 中增加 `POST_APPLY_STATUS_LIST` 与 `STAGED_STATUS_LIST` 定义
- [x] 1.2 在 `routes/agent_api.py` 及 `mcp_server.py` 的改写工具中增加防护，禁止 Agent 改写处于 `POST_APPLY_STATUS_LIST` 中的已投递记录

## 2. 待投递视图与路由

- [x] 2.1 在 `routes/application.py` 中新增 `GET /to-apply` 路由及 `to_apply` 处理器
- [x] 2.2 创建 `templates/to_apply.html` 模板，展示 `待投递` 状态岗位并提供一键触发投递动作
- [x] 2.3 修改 `/applications` 路由与 `templates/applications.html`，过滤排除 `STAGED_STATUS_LIST`（包括 `Pending Approval` 和 `待投递`），仅保留正式投递流

## 3. 导航与 UI 对齐

- [x] 3.1 在 `templates/_sidebar.html` 投递跟踪分组中增加「待投递」入口及状态计数徽章

## 4. 验证

- [x] 4.1 运行自动化测试套件 (`pytest tests/`) 确认无逻辑回归
- [x] 4.2 验证 Agent API / MCP 在更新已投递记录时受阻并返回正确错误提示