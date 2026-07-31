## 1. 常量与模型语义扩展

- [x] 1.1 在 `constants.py` 新增 `MEMORY_CATEGORIES` 常量列表（含正向 `prefer_tech` / `prefer_domain` / `prefer_company` / `salary_expected` / `culture_fit`，负向 `exclude_tech` / `exclude_company` / `salary_too_low` / `general`）和 `MEMORY_POSITIVE_PREFIX = 'prefer_'` 派生规则
- [x] 1.2 更新 `models.py` 中 `Memory` 表字段注释，反映 category 双向语义与 `rule_value` 可空语义（无 schema 迁移）

## 2. handle_decision 双向写入与 bug 修复

- [x] 2.1 `mcp_server.py` 的 `handle_decision` 新增可选参数 `rule_value: str = ""`，在 approve/reject 分支按极性写入 `Memory`（approve → `prefer_*`，reject → `exclude_*` / `general`） (depends on: 1.1)
- [x] 2.2 修复 reject 分支 `rule_value` 污染 bug：`rule_value` 仅存结构化值，`raw_feedback` 存原文；`rule_value` 未传时留空 (depends on: 2.1)
- [x] 2.3 approve 分支：从关联 application 的 company/JD 信息尝试提取简单结构化特征（如公司名、行业）写入 `rule_value`；无法提取时留空 (depends on: 2.1)
- [x] 2.4 同步修复 `routes/agent_api.py` 中 `handle_decision_action` 与 `review_application` 的相同单向 + 污染 bug，使其与 MCP `handle_decision` 行为一致 (depends on: 2.2)

## 3. evaluate_jd 消费双向规则

- [x] 3.1 `mcp_server.py` 的 `evaluate_jd` 移除硬编码 `keywords` 列表，改为查 `memories WHERE category LIKE 'prefer_%' AND rule_value != ''` 做正向加分 (depends on: 1.1)
- [x] 3.2 正向命中：每条 +N 分（上限 +20），写入 highlights；负向逻辑保持，且对空 `rule_value` 的记录跳过匹配 (depends on: 3.1)
- [x] 3.3 同步修改 `evaluate_jd` 在 `routes/agent_api.py` 或其他重复实现处的相同逻辑（若存在） (depends on: 3.1)

## 4. get_user_preferences 双向返回

- [x] 4.1 `get_user_preferences` 返回结构新增 `positive_rules` 字段，与现有 `negative_rules` 并列 (depends on: 1.1)

## 5. MCP 手动修正工具

- [x] 5.1 扩展 `add_memory_rule`：新增 `polarity` 参数（`positive` / `negative`），按极性映射 category 前缀；保持向后兼容 (depends on: 1.1)
- [x] 5.2 抽取公共 `_upsert_memory_rule(category, rule_value, raw_feedback)` 辅助函数，写入前按 `(category, rule_value)` 去重 (depends on: 5.1)
- [x] 5.3 `delete_memory_rule` 保持 `confirm=True` 校验逻辑不变，确认覆盖正向规则删除路径

## 6. 批量归纳脚本

- [x] 6.1 新增 `scripts/induce_positive_rules.py`，复用 `ai_scorer.py` 的「裸 sqlite3 + 批量 LLM + profile 指纹缓存」骨架 (depends on: 1.1)
- [x] 6.2 实现：查询历史 approve 的 applications（关联 company/JD），按 batch_size（默认 15）分批喂 LLM 提取 `prefer_*` 规则 (depends on: 6.1)
- [x] 6.3 实现 profile 指纹缓存（`data/.positive_induction_fingerprint`），无新 approve 时跳过 LLM (depends on: 6.1)
- [x] 6.4 写入用 `_upsert_memory_rule` 去重；无 API Key 时降级跳过并 log warning (depends on: 5.2, 6.2)
- [x] 6.5 支持 CLI 参数：`--force`（强制重归纳）、`--batch-size N`、`--dry-run`（仅预览不写库）

## 7. 历史数据清洗

- [x] 7.1 新增 `scripts/cleanup_memory_rule_value.py`：把误存在 `rule_value` 的长文本（长度 > 阈值，如 50 字符）移到 `raw_feedback`（若 `raw_feedback` 为空），清空 `rule_value` (depends on: 1.1)
- [x] 7.2 支持 `--dry-run` 预览待清洗条目，`--apply` 实际执行

## 8. 测试

- [x] 8.1 `tests/test_agent_api.py` 新增：approve 写正向 memory、reject 写结构化负向 memory、`rule_value` 不再被污染 (depends on: 2.2)
- [x] 8.2 新增 `evaluate_jd` 双向规则消费测试：正向命中加分、负向命中扣分、空规则不报错、无硬编码 fallback (depends on: 3.2)
- [x] 8.3 新增 `add_memory_rule` 极性参数与去重测试、`delete_memory_rule` 无 confirm 报错测试 (depends on: 5.1, 5.2)
- [x] 8.4 新增批量归纳脚本测试：指纹缓存跳过、去重、无 Key 降级（mock LLM） (depends on: 6.4)

## 9. 文档

- [x] 9.1 更新 `docs/hitl-feedback-loop.md`：闭环图改为双向，说明 approve/reject 均产生记忆、批量归纳流程、手动修正工具 (depends on: 2.2, 6.4, 5.1)
- [x] 9.2 更新 `README.md` 的 MCP 工具清单：`add_memory_rule` 增加 polarity 说明，新增 `induce_positive_rules` 脚本说明 (depends on: 5.1, 6.5)
