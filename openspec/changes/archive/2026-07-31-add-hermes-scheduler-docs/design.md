## Context

See `proposal.md`. 项目目前有 `scripts/daily_new_company_finder.py` 等脚本适合定时运行，但文档中没有说明如何设置定时任务。用户需要知道推荐用 Hermes 的调度能力。

## Goals / Non-Goals

**Goals:**
- 在 `docs/getting-started.md` 中新增一段 Hermes 定时任务推荐说明
- 列出适合定时运行的脚本

**Non-Goals:**
- 不修改任何代码或脚本
- 不提供 Hermes 以外的调度方案说明

## Decisions

- **放在 `docs/getting-started.md`**：该文档是用户上手引导，适合在设置完 MCP 后告知下一步推荐操作
- **不单独建文档**：内容只有一段话，不值得单独开一页

## Risks / Trade-offs

- 无