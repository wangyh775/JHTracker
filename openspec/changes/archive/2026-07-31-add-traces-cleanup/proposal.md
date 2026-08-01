## Why

Agent 轨迹（`agent_tasks` + `agent_events`）无限累积，无任何清理机制。每次 `evaluate_jd` 调用自动写入一条轨迹，Dashboard 每 15 秒轮询，长期使用后数据库会无限膨胀，影响查询性能。

## What Changes

- 新增 `services/cleanup.py`：按保留天数（默认 30 天）清理过期轨迹，复用归档的每日节流模式
- 在 `routes/agent_api.py` 的 `/traces` 页面访问时触发自动清理检查
- 在 `/traces` 页面增加「清空全部轨迹」按钮（手动触发，不可恢复）
- 新增 `TRACES_RETENTION_DAYS` 配置项（环境变量 + 默认值）
- 更新 `docs/hitl-feedback-loop.md` 文档

## Capabilities

### New Capabilities
- `traces-cleanup`: 自动清理过期 Agent 轨迹 + 手动清空全部轨迹

### Modified Capabilities
<!-- No existing specs change behavior -->

## Impact

- `services/cleanup.py` — 新增，清理逻辑 + 每日节流
- `routes/agent_api.py` — `/traces` 路由增加触发清理 + 手动清空端点
- `templates/traces.html` — 增加「清空全部轨迹」按钮
- `config.py` — 新增 `TRACES_RETENTION_DAYS` 配置
- `docs/hitl-feedback-loop.md` — 补充清理机制说明
- `tests/test_cleanup.py` — 新增测试