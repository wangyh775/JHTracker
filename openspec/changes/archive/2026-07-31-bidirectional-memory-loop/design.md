## Context

当前 Memory Engine 是单向的：`handle_decision(action='reject')` 写 `memories` 表，`approve` 不写任何记忆；`evaluate_jd` 的正向加分依赖代码内硬编码 `keywords` 列表（`python/c++/ros/robotics/嵌入式...`），不随用户偏好演化。同时 `handle_decision` 的 reject 分支有写入 bug——把整段 `raw_feedback` 塞进 `rule_value`（[mcp_server.py:586-589](file:///d:/DJTU/HermesWorkspace/career-tracker/mcp_server.py#L586-L589)），使 `evaluate_jd` 的子串匹配几乎永不命中。详见 proposal.md - Why。

约束：`Memory` 表 `category` 是 `String(50)`，无 DB 约束，语义扩展不需要 schema 迁移；项目零云依赖，LLM 可降级；`scripts/` 长任务直连 `sqlite3`，与 Web 进程解耦。

## Goals / Non-Goals

**Goals:**
- 让反馈闭环双向化：approve 产生正向信号，reject 产生负向信号，两者都参与下次评估
- 修复 `rule_value` 污染 bug，恢复负向匹配有效性
- 用批量归纳保证正向规则质量（LLM 提炼），用 MCP 工具允许人工/Agent 修正
- 替换 `evaluate_jd` 的硬编码 keywords，让正向加分由用户行为驱动

**Non-Goals:**
- 不做记忆规则 UI 管理界面（本期仅 MCP 工具 + 脚本）
- 不引入向量检索/语义匹配（保持子串匹配，可解释、零依赖）
- 不改 `ai_scorer.py` 批量评分链路（独立演进）
- 不做规则过期/衰减（后续视数据量评估）

## Decisions

### 决策 1：正向规则生成采用「批量归纳为主 + 手动工具补充」

**选择**：方案 3（离线批量归纳脚本）+ 方案 1（MCP 手动增删工具）。

**备选与权衡**：

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 方案 1：仅手动工具 | 实现简单，零噪音 | 依赖用户/Agent 主动维护，覆盖率低 | ❌ 主路径，但作为补充 |
| 方案 2：approve 时自动提取 | 实时，无需额外步骤 | 每次 approve 都要 LLM 调用费 token；JD 文本质量参差噪音大；approve 高频时成本高 | ❌ |
| 方案 3：批量归纳 | 省 token（一次评多家）；LLM 质量高；可指纹缓存跳过 | 非实时，approve 后需手动触发归纳 | ✅ 主路径 |

**与三原则对齐**：Agent-First（归纳脚本由 Skill 触发，工具暴露给 Agent）；AI 可降级（无 Key 时脚本跳过，不阻塞）；Data Sovereignty（全本地 LLM 调用，数据不落地）。

### 决策 2：`rule_value` 与 `raw_feedback` 分离，实时路径不阻塞

**选择**：`handle_decision` 接受可选 `rule_value` 参数。调用方传则存结构化值；未传则 `rule_value` 留空，仅存 `raw_feedback`，由批量归纳脚本后续提炼。

**备选**：
- 内部对 `raw_feedback` 做无 LLM 关键词提取 → 质量有限，中文分词依赖外部库
- 强制调用方传 `rule_value` → 增加 MCP 调用负担，破坏现有契约

**对齐**：`evaluate_jd` 对空 `rule_value` 跳过匹配，不报错；批量归纳补齐后自动生效。实时路径保持低延迟。

### 决策 3：category 枚举在 `constants.py` 维护，不加 DB 约束

**选择**：`Memory.category` 保持 `String(50)`，在 `constants.py` 新增 `MEMORY_CATEGORIES` 常量列表（含 `prefer_tech` / `prefer_domain` / `prefer_company` / `salary_expected` / `culture_fit` / `exclude_tech` / `exclude_company` / `salary_too_low` / `general`）。

**理由**：与项目现有风格一致（`constants.py` 已维护行业/城市/优先级枚举）；避免迁移；向前兼容历史数据。

### 决策 4：批量归纳脚本复用 `ai_scorer.py` 架构

**选择**：新增 `scripts/induce_positive_rules.py`，复用 `ai_scorer.py` 的「裸 sqlite3 + 批量 LLM + profile 指纹缓存 + 失败重试」模式。

**理由**：评分引擎已验证此模式可行；独立进程不阻塞 Web；共享 `config.py` 路径配置；与 Skill 触发方式一致（`skills/` 下新增或扩展 Skill）。

### 决策 5：去重策略

**选择**：写入前查 `(category, rule_value)` 是否已存在，存在则跳过。归纳脚本与手动工具共用一个 `_upsert_memory_rule` 辅助函数。

## 表结构 diff

无 schema 迁移。`Memory` 表字段语义扩展：

```diff
 class Memory(db.Model):
     category = db.Column(db.String(50), nullable=False)
-    # exclude_tech, exclude_company, salary_too_low, general
+    # 正向: prefer_tech, prefer_domain, prefer_company, salary_expected, culture_fit
+    # 负向: exclude_tech, exclude_company, salary_too_low, general
     rule_value = db.Column(db.String(200))
-    # 结构化值 (如 Java, 外包)
+    # 结构化值 (如 ROS, 外包, 15000)；可为空，由批量归纳补齐
     raw_feedback = db.Column(db.Text)
-    # 人类原始拒绝评语
+    # 人类原始评语（approve/reject 均可）
```

新增 `polarity` 派生：`category LIKE 'prefer_%'` → positive，否则 negative。不落库，查询时计算。

## Risks / Trade-offs

- **[批量归纳 LLM 失败]** → 降级跳过，保留空 `rule_value`，下次重试（与 `ai_scorer` 一致）
- **[正向规则噪音]** → 手动修正工具 + 去重 + 批量归纳质量优于实时提取
- **[实时匹配在归纳前失效]** → `evaluate_jd` 对空 `rule_value` 跳过，不报错；过渡期负向匹配依赖已有非空规则
- **[历史脏数据（已污染的 rule_value）]** → 提供一次性清洗脚本：把误存在 `rule_value` 的长文本移到 `raw_feedback`（若 `raw_feedback` 为空），清空 `rule_value`
- **[approve 信号弱]** → approve 时无 JD 文本则无法提取特征；依赖 `applications` 关联的 company/JD 信息，若缺失则归纳跳过该条

## Migration Plan

1. 部署代码（无 schema 迁移）
2. 运行一次性清洗脚本修正历史脏数据
3. 触发批量归纳脚本填充正向规则
4. `evaluate_jd` 自动开始消费双向规则
5. 回滚：还原代码即可，数据无破坏性变更（`rule_value` 清空可由归纳重填）

## Open Questions

- 正向规则归纳的触发频率：手动 Skill 触发 vs 定时？倾向手动（与 `ai_scorer` 一致），待用户反馈再决定是否加定时。
