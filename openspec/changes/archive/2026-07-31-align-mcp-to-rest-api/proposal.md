## Why

MCP Server 目前只有 9 个工具，远少于 REST API（agent_api.py）覆盖的能力。系统目标是完全托管给智能体，但 Agent 通过 MCP 协议只能做有限操作——不能查投递列表、不能读笔记、不能更新状态、不能看统计数据。Skill 指导 Agent 做复杂任务时，Agent 发现 MCP 没有对应工具，只能绕过或放弃。

## What Changes

- 在 `mcp_server.py` 中新增 27 个 MCP 工具，从 9 个扩展到 36 个，覆盖所有数据域
- 权限策略：读操作 + 创建/更新操作 Agent 自主执行；删除操作（delete_company, delete_note 等）需要审批
- 新增 `batch_evaluate_jds()` 支持一次评估多个 JD
- REST API 保持不动，作为 MCP 断连时的 fallback
- 更新 4 个 Skill 的 `SKILL.md` 以引用新增工具

## Capabilities

### New Capabilities
- `mcp-full-coverage`: MCP 工具集覆盖全部 11 个数据域（Profile, Company, Application, InterviewFeedback, Note, Timeline, Resume, Statistics, Trace, Evaluation, System），共 36 个工具

### Modified Capabilities
<!-- No existing specs change behavior -->

## Impact

- `mcp_server.py` — 新增 27 个工具函数，从 9 扩至 36 个
- `skills/job-sourcing-and-scoring/SKILL.md` — 引用新增的 company/statistics 工具
- `skills/application-tracker/SKILL.md` — 引用新增的 application/feedback 工具
- `skills/candidate-profile-and-resume/SKILL.md` — 引用新增的 resume/memory 工具
- `skills/tracker-ops/SKILL.md` — 引用新增的 note/timeline/trace 工具
- `docs/SKILLS_AND_MCP_GUIDE.md` — 更新 MCP 工具列表
- `tests/test_mcp_full.py` — 新增测试