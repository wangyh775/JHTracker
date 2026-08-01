## Context

Agent 轨迹数据（`agent_tasks` + `agent_events`）无限增长，无任何清理机制。每条 `evaluate_jd` 调用自动写入一条轨迹，Dashboard 每 15 秒轮询展示最近 50 条，但旧数据从不被访问却持续占用数据库空间。

See proposal.md for motivation. Specs at `specs/traces-cleanup/spec.md`.

## Goals / Non-Goals

**Goals:**
- 自动清理超过保留天数的过期轨迹，每日最多一次
- 手动清空全部轨迹（带确认，不可恢复）
- 保留天数可通过环境变量配置（默认 30 天）
- 复用归档的「每日节流」模式，保持一致性

**Non-Goals:**
- 不提供 UI 级别的保留天数配置（仅环境变量，后续可加）
- 不清除 `DecisionFeedback` 或 `Memory` 表（这些是 HITL 核心数据，不属于轨迹）
- 不改变现有轨迹查询逻辑（仍然只查最近 50 条）

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| 清理时机 | 访问 `/traces` 页面时触发 | 同归档模式，不引入后台进程；用户主动访问轨迹页时清理最合理 |
| 节流方式 | `.traces_cleanup_last_run` 文件记录日期 | 复用 `archive.py` 的 `_should_run_today` / `_touch_last_run` 模式 |
| 清理策略 | 先删 events（WHERE created_at < cutoff），再删无 events 的 tasks | events 是数据主体，tasks 只是外壳；SQL 一次性完成 |
| 手动清空 | 新端点 `POST /api/agent/traces/clear` + 页面按钮 | 与现有 RESTful 风格一致；不可逆操作加确认弹窗 |
| 配置项 | `config.py: TRACES_RETENTION_DAYS`，环境变量 `JH_TRACES_RETENTION_DAYS` | 与 `ARCHIVE_STALE_DAYS` 命名一致 |

## Risks / Trade-offs

- [数据丢失] 自动清理可能误删用户想保留的轨迹。→ 默认 30 天足够长，且 `/traces` 页面只展示最近 50 条，旧数据本就不被访问
- [不可恢复] 手动清空不可撤销。→ 加确认弹窗 + 二次确认文案
- [SQLite 无并发] 清理时可能阻塞写操作。→ 数据量小（万级），耗时 < 100ms，不影响用户体验