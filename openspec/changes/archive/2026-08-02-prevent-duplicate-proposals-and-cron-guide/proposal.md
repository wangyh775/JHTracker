## Why

智能体在自动搜寻岗位时，会反复为数据库中已存在的公司推送重复的 `Pending Approval` 提案。根因是 `create_company` 有按名称去重的逻辑，但 `create_application` 缺乏"同公司+同岗位"去重校验——Agent 拿到已有公司的 ID 后仍会无脑插入新提案。此外，新用户安装 JHTracker 后缺乏一份从零打通 MCP → Skill → 定时任务三链路的指南，导致 Agent 定时任务未配置防重约束，每次全量搜索都会把已有公司再推一遍。

## What Changes

- **MCP `create_application` 增加去重校验**：插入前检查同 `company_id` + `position` 是否已存在 `Pending Approval` 或 `待投递` 记录，若存在则返回已有记录而非新建。
- **数据库层增加唯一索引**：在 `applications` 表上对 `(company_id, position, status)` 建立部分唯一索引，物理兜底防止重复 Pending Approval 记录。
- **Skill SOP 更新**：在 `job-sourcing-and-scoring/SKILL.md` 中新增 Step 2.5"查重跳过步骤"，明确要求 Agent 在 `create_company` 返回 `created=False` 时必须先检查已有提案再决定是否跳过。
- **三链路打通与定时任务防重指南文档**：在 `docs/getting-started.md` 中新增独立章节"三链路打通与防重配置"，全闭环指导用户与智能体如何配置 MCP 挂载、Skill 加载和定时任务防重 Prompt。

## Capabilities

### New Capabilities
- `sourcing-dedup`: 智能体岗位推送去重机制——在 MCP 工具层、数据库层和 Skill SOP 层构建纵深防御，防止同一公司+同一岗位被重复推送为 Pending Approval 提案。

### Modified Capabilities
（无）

## Impact

- **`mcp_server.py`**：`create_application` 函数增加去重查询逻辑，返回结构新增 `created` 字段。
- **`routes/agent_api.py`**：REST API 的 `create_application` 端点同步增加去重校验，保持 MCP 与 API 行为一致。
- **`models.py` / 数据库迁移**：新增 `applications` 表部分唯一索引。
- **`skills/job-sourcing-and-scoring/SKILL.md`**：工作流新增查重跳过步骤。
- **`docs/getting-started.md`**：新增三链路打通章节与定时任务防重 Prompt 模板。
- **`constants.py`**：可能需要新增 `DEDUP_STATUS_LIST` 常量定义受去重保护的状态集合。
- **测试**：新增去重逻辑的单元测试与集成测试。
