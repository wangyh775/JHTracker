## Context

See `proposal.md`. `application-tracker/SKILL.md` 中的状态流转图和 SQL 示例仍在使用旧的 `待投递` 作为 Agent 推送的初始状态，与 `constants.py` 中 `STAGED_STATUS_LIST` / `POST_APPLY_STATUS_LIST` 的定义和 `separate-to-apply-and-application-views` change 的解耦设计不一致。`candidate-profile-and-resume/SKILL.md` 缺少对 `enterprise_preference` 字段的支持。

## Goals / Non-Goals

**Goals:**
- 将 `application-tracker/SKILL.md` 的状态流转图、SQL 示例和 HITL 描述全部对齐为 `Pending Approval` → `待投递` → `已投递` 的新分层。
- 在 `application-tracker/SKILL.md` 中新增 Agent 只读防护声明。
- 在 `candidate-profile-and-resume/SKILL.md` 中增加 `enterprise_preference` 字段的 Asset Location 与 Resume Parsing 工作流说明。

**Non-Goals:**
- 不修改 `job-sourcing-and-scoring/SKILL.md`（已是最新标准）。
- 不修改 `tracker-ops/SKILL.md`（维护工具类，无状态流转问题）。
- 不改动数据库表结构或 MCP 工具代码。

## Decisions

- **状态流转图重写**：直接替换 `application-tracker/SKILL.md` 中的状态流转段落和 SQL 示例，确保与 `constants.py` 中的 `STAGED_STATUS_LIST` 和 `POST_APPLY_STATUS_LIST` 完全一致。
- **Agent 只读防护声明位置**：放在 `application-tracker/SKILL.md` 的 HITL Workflow 段落之后，作为独立的"Agent Write Protection"小节。
- **enterprise_preference 解析逻辑**：在 `candidate-profile-and-resume/SKILL.md` 的 Resume Parsing 步骤中增加提取企业类型偏好的说明。

## Risks / Trade-offs

- [Skill 文档与代码不同步] → 本次对齐后应定期审查 Skill 文档与 constants.py 的一致性。