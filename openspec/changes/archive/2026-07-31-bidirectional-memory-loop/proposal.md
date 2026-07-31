## Why

当前 Memory Engine 只记录负向（拒绝）信号：用户 approve 岗位时不写任何记忆，`evaluate_jd` 的正向加分依赖硬编码 keywords 列表，无法随用户偏好演化。这导致推荐闭环单向校准（只会越来越保守，不会越来越精准），且 `handle_decision` 的 reject 分支存在写入 bug——把整段 `raw_feedback` 塞进 `rule_value`，使负向子串匹配几乎永不命中，闭环半失效。spec 声称的 "refine scoring alignment over time" 未真正落地。

## What Changes

- 扩展 `Memory` 表 category 枚举，新增正向类别：`prefer_tech` / `prefer_domain` / `prefer_company` / `salary_expected` / `culture_fit`
- `handle_decision(action='approve')` 写入正向记忆，从关联 JD/company 提取结构化特征
- **BREAKING**（修 bug）：`handle_decision(action='reject')` 不再把 `raw_feedback` 塞进 `rule_value`；`rule_value` 仅存结构化值，`raw_feedback` 存原文
- `evaluate_jd` 用 `memories WHERE category LIKE 'prefer_%'` 替换硬编码 keywords 列表做正向加分
- 新增离线批量归纳脚本：从历史 approve 记录 LLM 归纳正向偏好规则写入 `memories`（省 token，质量优先）
- 新增/扩展 MCP 工具支持正向规则的手动增删（Agent / 用户可修正归纳结果）
- `get_user_preferences` 同时返回 `positive_rules` 与 `negative_rules`

## Capabilities

### New Capabilities
<!-- 无新 capability，全部归入现有 feedback loop 与 evaluation 的演进 -->

### Modified Capabilities
- `human-feedback-loop`: 闭环从单向（仅 reject 写记忆）扩展为双向（approve 也写正向记忆）；新增批量归纳与手动修正能力
- `jd-evaluation-mcp`: `evaluate_jd` 的正向加分从硬编码 keywords 改为消费 `memories` 正向规则

## Impact

- `models.py` — `Memory.category` 注释/常量更新（无 schema 迁移，category 是 String）
- `mcp_server.py` — `handle_decision` / `evaluate_jd` / `get_user_preferences` / `add_memory_rule` 改动
- `scripts/` — 新增 `induce_positive_rules.py` 批量归纳脚本
- `tests/` — 新增双向记忆与批量归纳测试
- `docs/` — `hitl-feedback-loop.md` 更新闭环说明

## Non-goals

- 不改 `ai_scorer.py` 的批量评分逻辑（独立链路，后续单独演进）
- 不做记忆规则的 UI 管理界面（本期仅 MCP 工具 + 脚本，UI 留待后续）
- 不引入向量检索/语义匹配（本期保持子串匹配，保证可解释与零依赖）
- 不做记忆规则的过期/衰减机制（后续视数据量再评估）
