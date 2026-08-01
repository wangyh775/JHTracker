## Why

当前 `skills/job-sourcing-and-scoring/SKILL.md` 的检索流程过于笼统（"Search the web for target industry/role companies"），没有定义具体的工具链、工具优先级、真实性验证步骤，也没有按用户偏好匹配检索平台。Agent 在实际执行中容易编造公司名和 URL，或搜到不相关信息。

## What Changes

- **Skill 重构「分层检索协议」(Layered Retrieval Protocol)**：在 `skills/job-sourcing-and-scoring/SKILL.md` 中定义完整的检索-验证闭环，包括工具优先级（Firecrawl → CDP/Playwright → Exa → Tavily）、平台路由（按用户企业偏好匹配 BOSS/国聘/猎聘等）、真实性验证门（URL 可达性 + 内容一致性 + 交叉来源）。
- **新增 `enterprise_preference` 字段**：在 `data/profile.md` 中增加企业偏好字段，Agent 据此自动路由检索平台。用户也可在运行时直接告知偏好。
- **新增「拒绝机制」**：搜不到真实信息时，Agent 必须如实报告，禁止编造数据。
- **MCP 工具增强**：`create_company` 和 `create_application` 的 docstring 增加真实性约束声明，要求附带真实 `source_url`。

## Capabilities

### New Capabilities
- `layered-retrieval-protocol`: 分层检索工具链排列、平台路由、检索-验证闭环、拒绝机制

### Modified Capabilities
- `auto-sourcing`: 当前 auto-sourcing workflow 缺少真实性验证步骤和平台路由逻辑，需要更新 Skill 的 Workflow 规范

## Impact

- `skills/job-sourcing-and-scoring/SKILL.md` — 重构 Workflow 部分，增加分层检索协议
- `data/profile.md` — 增加 `enterprise_preference` 字段
- `prompts/company_list_prompt.md` — 增加平台路由提示
- `mcp_server.py` — `create_company` / `create_application` 的 docstring 增加真实性约束声明