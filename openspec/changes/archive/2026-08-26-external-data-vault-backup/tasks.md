## 1. 文档先行与规则固化 (Documentation & Guardrails)

- [x] 1.1 在 `docs/database.md` 中新增「外部安全区备份 (External Data Vault) 与灾难恢复」章节与架构图
- [x] 1.2 在 `AGENTS.md` 和 `CLAUDE.md` 中增加智能体操作铁律：严禁删除 `data/` 下核心画像与数据库文件，大版本重构前必须触发快照
- [x] 1.3 在 `docs/architecture.md` 中更新数据安全防御与生命周期章节

## 2. 外部安全区备份核心引擎实现 (Core Vault Service)

- [x] 2.1 创建 `services/backup_vault.py`，实现 `ExternalVaultService`，支持解析 `~/.career-tracker/backups/` 路径及环境变量覆盖
- [x] 2.2 实现 SQLite WAL 事务一致性在线快照方法 `create_db_snapshot()`，基于 `sqlite3.backup` API
- [x] 2.3 实现用户画像与核心资产全量封包方法 `create_full_bundle()`，打包 `tracker.db`、`profile.md`、`applicant_profile.json`、`resumes/` 和 `career_data/`
- [x] 2.4 实现快照与归档包的自动轮转淘汰机制 `rotate_backups()`（保留 30 天 / 最多 50 份）
- [x] 2.5 实现灾难检测与还原探测方法 `check_disaster_state()` 与 `restore_from_snapshot()`

## 3. 应用生命周期钩子与熔断保护集成 (App Lifecycle & Guard Integration)

- [x] 3.1 在 `app.py`（及相关初始化模块）中增加启动自检钩子：执行 2 小时节流的自动快照
- [x] 3.2 在启动流程中增加灾难探测：若 `tracker.db` 丢失但外部 Vault 存在备份，高亮打印预警与恢复指引
- [x] 3.3 在数据库模型或初始化逻辑中添加 `drop_all` 非测试环境防呆熔断拦截
- [x] 3.4 改造 `routes/backup.py`，支持查看外部 Vault 备份列表、一键触发全量封包及从外部快照还原

## 4. 自动化测试与验证 (Testing & Verification)

- [x] 4.1 编写 `tests/test_backup_vault.py`，测试外部路径解析、WAL 在线快照生成及画像打包完整性
- [x] 4.2 测试备份自动轮转与 2 小时启动节流逻辑
- [x] 4.3 测试灾难探测与还原恢复流程，验证恢复后表数据与画像的一致性
- [x] 4.4 运行全量 `pytest` 回归测试，确保所有既有功能与测试套件稳定通过
