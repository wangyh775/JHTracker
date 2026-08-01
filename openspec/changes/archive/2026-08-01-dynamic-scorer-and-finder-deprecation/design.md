## Context

See `proposal.md`. `ai_scorer.py` 当前仅硬编码静态词库；`daily_new_company_finder.py` 为废弃的前代发现脚本。

## Goals / Non-Goals

**Goals:**
- 在 `ai_scorer.py` 中引入 `load_dynamic_negative_rules(conn)` 从 `memories` 表读取 `category LIKE 'exclude_%' OR category IN ('salary_too_low', 'general')` 规则
- 将动态负向规则与静态 `DEAL_BREAKERS` 合并，传入 Stage 1 预筛函数 `prefilter()`
- 在 `daily_new_company_finder.py` 顶部添加格式化的已废弃 Banner，并在脚本内部直接打印提示并 `sys.exit(0)`

**Non-Goals:**
- 不删除 `daily_new_company_finder.py` 文件本身（保留其文件与说明结构，仅做优雅拦截）
- 不改动 `memories` 数据库表结构

## Decisions

- **动态词库加载时机**：在 `ai_scorer.py` 的 `main()` 函数中，数据库连接建立后立刻查询 `memories` 库获取最新规则集合，并注入到 `score_batch()` 中。
- **匹配规则**：对从 `memories` 中提取的 `rule_value` 或 `content` 进行小写化处理，执行子串匹配。

## Risks / Trade-offs

- [记忆规则过宽导致误杀] → 用户可在页面编辑/删除错误的 Negative Memory 规则，引擎下一次评分即生效。