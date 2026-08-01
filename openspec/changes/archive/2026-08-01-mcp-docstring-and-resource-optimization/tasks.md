## 1. Docstring 优化 (P0/P1)

- [x] 1.1 更新 `update_application_status` docstring，声明 Agent 禁止设置 `POST_APPLY_STATUS_LIST` 状态
- [x] 1.2 更新 `get_pending_approvals` docstring，明确仅返回 `Pending Approval` / `待审批`，排除 `待投递`
- [x] 1.3 更新 `search_companies` docstring，补充返回字段、LIMIT 20、排序规则说明
- [x] 1.4 更新 `get_company` docstring，补充返回字段列表说明

## 2. 统计字段增强 (P0)

- [x] 2.1 在 `get_statistics` 中增加 `to_apply_count` 字段（`SELECT COUNT(*) FROM applications WHERE status = '待投递'`）

## 3. 新增 MCP 资源 (P2)

- [x] 3.1 新增 `@mcp.resource("jhtracker://statistics")` 资源，返回仪表盘统计 JSON
- [x] 3.2 新增 `@mcp.resource("jhtracker://memories")` 资源，返回全部偏好记忆规则 JSON

## 4. 验证

- [x] 4.1 运行 `pytest` 确认无回归