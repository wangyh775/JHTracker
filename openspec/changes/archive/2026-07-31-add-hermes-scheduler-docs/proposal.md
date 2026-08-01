## Why

项目现有 `scripts/daily_new_company_finder.py` 等脚本适合定时运行，但文档中没有说明如何设置定时任务，用户不知道推荐用 Hermes 的调度能力来配合。

## What Changes

- 在 `docs/getting-started.md` 中新增一段「推荐使用 Hermes 设置定时任务」的说明
- 提及哪些脚本适合定时运行（如 `daily_new_company_finder.py`）
- 指向 Hermes 的定时任务配置方式

## Capabilities

<!-- 纯文档变更，无 spec 行为变化 -->
`skip_specs: true`

## Impact

- `docs/getting-started.md` — 新增 Hermes 定时任务推荐说明