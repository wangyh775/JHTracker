---
type: feat
title: 建立基于 OmniRoute 模式的工程质量门禁、指标棘轮与碎片化更新日志系统
author: agent
issue: ""
---

- 引入 `changelog.d/` 碎片化日志目录与自动化归档脚本 `scripts/compile_changelog.py`。
- 引入质量指标棘轮机制 `quality-baseline.json` 与 `scripts/check_ratchet.py`，锁死测试资产，严禁质量指标退步。
- 引入统一质量门禁调度器 `scripts/check_all.py`，集成日志边界、反断言弱化、版本号 SSOT 一致性、前后端测试与生产打包全量校验。
- 在 `AGENTS.md` 中强化工程物理硬性门禁规范（Hard Gate）。
