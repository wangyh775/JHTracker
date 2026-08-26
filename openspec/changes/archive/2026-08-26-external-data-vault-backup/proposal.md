## Why

在之前的系统架构升级和智能体自动化重构过程中，由于智能体清理工作区，导致存有求职投递全流程记录、面试复盘及负向偏好记忆的本地 SQLite 数据库（`data/tracker.db`）被误删除。
由于包含真实姓名、联系方式、投递记录、面试反馈等敏感隐私数据，`data/tracker.db` 及用户画像严禁通过 Git 进行远程仓库跟踪。而传统的内部备份（`data/backups/`）与数据同源，一旦智能体清空 `data/` 目录便会随之全军覆没。

为了彻底解决“既不泄露到远程，又防智能体误删”的数据安全与隐私冲突，必须建立工作区外的自动化数据备份与灾难恢复机制（External Data Vault），对数据库、用户画像及投递资产实施物理隔离保护。

## What Changes

- **工作区外部安全隔离备份存储 (External Vault Storage)**：将自动快照与备份包存储路径移至用户主目录 `~/.career-tracker/backups/`（跨平台兼容，Windows 下为 `C:\Users\<user>\.career-tracker\backups\`），彻底脱离 Git 工作区。
- **用户画像与核心资产全量封包 (Comprehensive Profile & Asset Bundling)**：备份范围不仅包含 `tracker.db`（SQLite 全量表数据），还完整涵盖 `data/profile.md`、`data/applicant_profile.json`、`data/.profile_hash`、`data/resumes/`（4-Track 简历实体）以及 `career_data/`。
- **WAL 事务一致性秒级快照引擎 (Online SQLite Snapshot Engine)**：利用 `sqlite3.backup` API 实现 WAL 模式下的在线安全备份，消除脏读与未刷盘风险。
- **生命周期钩子与自动轮转 (Lifecycle Hooks & Retention)**：
  - 应用启动时自检并执行轻量快照（内置 2 小时节流）。
  - 支持全量 Zip 归档（保留最近 30 天 / 最多 50 份，超额自动轮转）。
- **灾难检测与自愈机制 (Disaster Recovery Engine)**：启动时若检测到 `data/tracker.db` 或画像文件丢失，自动探测安全区最新快照并提供终端高亮预警与恢复指令/自愈能力。
- **智能体防呆规则与代码防护 (Agent Guardrails & Code Safety)**：在 `AGENTS.md` / `CLAUDE.md` 及代码层添加防呆熔断，严禁非测试环境下执行 `drop_all` 或删除 `data/` 核心文件。

## Capabilities

### New Capabilities
- `external-data-vault`: 提供工作区外物理隔离的自动化数据与用户画像备份、快照轮转、灾难恢复与防误删安全防护。

### Modified Capabilities
- `safety-guard-ats`: 增强安全守卫体系，将数据库与用户画像防误删、防直接 drop、测试环境隔离等规则纳入系统级安全防御规范。

## Impact

- **核心受影响文件/模块**：
  - `services/backup_vault.py` (新增：外部 Vault 管理器)
  - `routes/backup.py` (修改：集成外部 Vault 与恢复接口)
  - `app.py` (修改：启动时自检、自动快照与灾难探测钩子)
  - `AGENTS.md` / `CLAUDE.md` (修改：更新智能体防误删铁律)
  - `docs/database.md` / `docs/architecture.md` (修改：更新外部备份与灾难恢复架构说明)
- **依赖变更**：使用标准库 `sqlite3`、`shutil`、`pathlib`、`zipfile`，无新增外部重量级依赖。
- **向下兼容性**：完全兼容现有手动备份导入导出逻辑，无破坏性变更。
