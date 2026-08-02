## 1. 核心去重逻辑实现 (MCP & REST API)

- [x] 1.1 在 `mcp_server.py` 的 `create_application` 函数中增加去重 SQL 查询（按 `company_id` + `LOWER(TRIM(position))` 在 `STAGED_STATUS_LIST` 范围内查重），如已有记录则直接返回现有记录且带有 `created: false` 标识。
- [x] 1.2 在 `routes/agent_api.py` 的 `create_application` 端点同步补充去重查询逻辑，保持 API 与 MCP 服务行为一致。
- [x] 1.3 在 `models.py` / 数据库初始化逻辑中对 `applications` 表增加部分唯一索引（Partial Unique Index），在数据库物理层兜底防重。

## 2. Skill SOP 规则增强

- [x] 2.1 更新 `skills/job-sourcing-and-scoring/SKILL.md` 的工作流，新增 Step 2.5 "查重与跳过 (Deduplication Check)" 规范，要求 Agent 当 `create_company` 返回 `created: false` 时先调 `list_applications` 检查，重复即跳过。

## 3. 三链路打通与定时任务防重指南编写

- [x] 3.1 在 `docs/getting-started.md` 中编写独立的第 7 节“MCP + Skill + 定时任务 三链路打通与防重配置指南”，收录连通性 CheckList 与防重 Cron Prompt 模板。

## 4. 测试与验证

- [x] 4.1 编写单元与集成测试（在 `tests/test_agent_api.py` 或 `tests/test_mcp.py` 中），验证重复推送时 `create_application` 正确返回已有记录且 `created: false`，不产生多余数据库行。
- [x] 4.2 运行全量 `pytest` 自动化测试集，确保所有单元测试通过。
