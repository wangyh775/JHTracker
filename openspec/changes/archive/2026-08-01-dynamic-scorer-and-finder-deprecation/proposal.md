## Why

目前 `scripts/ai_scorer.py` 的 Stage 1 预筛关键词仅基于硬编码的静态词库（`DEAL_BREAKERS`），无法感知人类在 Decision Inbox 中通过 Reject 积累的个性化排除偏好（存储于数据库 `memories` 表）。此外，`scripts/daily_new_company_finder.py` 属于早期硬编码模版，与现有 Agent + MCP 真实网络检索流程冲突，需要优雅废弃。

## What Changes

- **`ai_scorer.py` 动态记忆预筛**：扩展 Stage 1 预筛逻辑，增加 `load_dynamic_negative_rules(conn)` 函数，自动从数据库 `memories` 表读取人类累积的负向规则（`exclude_*`, `salary_too_low`, `general` 等），合并静态 `DEAL_BREAKERS` 词库，实现 0 Token 开销的前置淘汰。
- **`daily_new_company_finder.py` 优雅废弃**：在脚本头部增加明显的 `DEPRECATED` 警告声明，在直接执行时打印引导提示并退出 (`sys.exit(0)`)，指引使用 Agent + Skill 执行真实搜寻。

## Capabilities

### New Capabilities
- `dynamic-prefiltering`: 支持评分引擎动态加载数据库 `memories` 中的人类排除记忆做零 Token 前置预筛
- `script-deprecation-notice`: 废弃脚本执行防御与标准操作指引

### Modified Capabilities

## Impact

- `scripts/ai_scorer.py` — 新增动态负向记忆加载逻辑并整合至 `prefilter`
- `scripts/daily_new_company_finder.py` — 增加废弃 Warning Banner 与 `sys.exit(0)` 阻断
- `specs/dynamic-prefiltering/spec.md` — 规范描述
- `specs/script-deprecation-notice/spec.md` — 规范描述