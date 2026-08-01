## Why

Skill 审查发现 `application-tracker/SKILL.md` 和 `candidate-profile-and-resume/SKILL.md` 的内容与最新架构（投递前/投递后状态解耦、`Pending Approval` 提案制、`enterprise_preference` 偏好路由、Agent 只读防护）存在断层，需要同步对齐。

## What Changes

- **`application-tracker/SKILL.md` 状态流转对齐**：
  - 修正状态流转图为：`Pending Approval` (Agent提案) → 人类批准 → `待投递` (/to-apply) → 人类投递 → `已投递` (/applications) → `简历筛选` → `笔试` → `面试` → `Offer` / `已拒`
  - 修正 SQL 示例中的 `'待投递'` 为 `'Pending Approval'`
  - 新增 Agent 只读防护声明：禁止 Agent 改写 `POST_APPLY_STATUS_LIST` 中的已投递记录
- **`candidate-profile-and-resume/SKILL.md` 补齐偏好字段**：
  - 在 Asset Locations 与 Workflow 中增加 `enterprise_preference` (央国企/外企/民企/不限) 字段的识别与同步说明
  - 在 Resume Parsing 流程中增加从简历中提取企业偏好的步骤

## Capabilities

### New Capabilities

### Modified Capabilities
- `agent-skills-consolidation`: Application Tracker 与 Candidate Profile Skill 规范需同步最新状态流转与偏好字段