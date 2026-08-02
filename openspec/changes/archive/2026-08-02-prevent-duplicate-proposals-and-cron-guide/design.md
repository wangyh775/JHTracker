## Context

当前 JHTracker 的去重机制仅停留在 `create_company` 按公司名称匹配。智能体在调用 `create_application` 推送岗位提案时，底层 SQLite 并没有针对 `(company_id, position)` 且处于未处理状态（`Pending Approval` 或 `待投递`）的重复提案拦截逻辑。

此外，智能体接入该系统时需要连通：
1. **MCP 协议** (`mcp_server.py`)
2. **Skill SOP** (`skills/job-sourcing-and-scoring/SKILL.md`)
3. **定时任务 Prompt** (Hermes / Cron 定时唤醒)

## Goals / Non-Goals

**Goals:**
- 在 MCP 层与 REST API 层实现 `create_application` 的轻量去重校验。
- 在 SQLite 数据库层对处于未处理状态的提案增加部分唯一索引（Partial Unique Index）。
- 更新 `job-sourcing-and-scoring` Skill，明确指令 Agent 遇到已有公司时先查询已有提案再决定是否跳过。
- 在 `docs/getting-started.md` 中编写闭环的三链路打通与定时任务防重指南。

**Non-Goals:**
- 不改变已投递/面试/Offer 等 Post-Apply 状态的记录逻辑。
- 不影响人为添加同公司多个不同岗位（仅去重完全相同的 `company_id` + 规范化后的 `position`）。

## Decisions

### 1. 去重逻辑触发的判定范围：`company_id` + `LOWER(TRIM(position))`
- **选择**: 在 `create_application` 中，查询条件为 `company_id = ? AND LOWER(TRIM(position)) = LOWER(TRIM(?)) AND status IN ('Pending Approval', '待投递')`。
- **替代方案**: 仅用 `source_url` 去重。理由：许多岗位的搜索 URL 含有追踪参数，导致同一岗位 URL 变化，不如使用规范化岗位名称更稳健。

### 2. 数据库层：使用 SQLite Partial Unique Index 物理兜底
- **选择**: 在 SQLite 中建立索引：
  `CREATE UNIQUE INDEX IF NOT EXISTS idx_applications_dedup ON applications(company_id, LOWER(position)) WHERE status IN ('Pending Approval', '待投递');`
- **替代方案**: 在 `applications` 表建立全量 UNIQUE(company_id, position)。理由：用户可能在历史投递中多次申请同一岗位的不同批次，部分唯一索引仅锁定待投递/待审批的“在办提案”，更符合业务规则。

### 3. 三链路打通指南编排
- **选择**: 在 `docs/getting-started.md` 增加第 7 节“MCP + Skill + 定时任务 三链路打通与防重配置指南”，提供可直接复制的 Hermes / Agent Cron 防重 Prompt 模板。

## Risks / Trade-offs

- **[风险] 岗位名称大小写或空格微小差异绕过去重** → **缓解方案**: 对 `position` 参数做 `TRIM()` 和 `LOWER()` 标准化处理。
- **[风险] 旧版本 SQLite 不支持 partial index** → **缓解方案**: SQLite ≥ 3.8.0 均支持 partial index，Python 3.10 内置 SQLite 版本远高于此。
