## 1. Skill 重构与 SOP 文档

- [x] 1.1 重写 `skills/job-sourcing-and-scoring/SKILL.md` 的 Workflow 部分，包含分层检索协议（工具链优先级、平台路由、检索-验证闭环）
- [x] 1.2 在 Skill 中增加拒绝机制 SOP：搜不到真实信息时禁止编造，必须如实报告

## 2. Profile 字段与平台路由

- [x] 2.1 在 `data/profile.md` 中增加 `enterprise_preference` 字段（可选值：央国企/外企/民企/不限）
- [x] 2.2 在 Skill 的 Step 0 中增加平台路由逻辑：读取 profile 字段，按偏好路由到对应平台

## 3. MCP 工具声明增强

- [x] 3.1 更新 `mcp_server.py` 中 `create_company` 的 docstring，增加真实性约束声明，要求附带真实 website 和 source_url
- [x] 3.2 更新 `mcp_server.py` 中 `create_application` 的 docstring，增加真实性约束声明，要求附带真实 source_url

## 4. 验证

- [x] 4.1 手动验证 Agent 在新增 SOP 指导下能正确路由平台并完成检索-验证闭环
- [x] 4.2 验证 Agent 在搜不到真实信息时能正确拒绝编造