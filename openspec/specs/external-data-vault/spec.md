## Purpose

提供物理隔离在 Git 工作区外部的自动化数据与用户画像备份机制，实现 SQLite 数据库事务安全快照、全量画像与简历资产封包、自动轮转归档以及灾难自愈探测，确保用户隐私与数据防误删安全。

## Requirements

### Requirement: 工作区外存储隔离 (External Vault Path Isolation)
系统 SHALL 将自动快照和全量归档包存储在当前 Git 工作区外部的用户主目录安全区 `~/.career-tracker/backups/`（可通过环境变量 `CAREER_TRACKER_BACKUP_DIR` 覆盖）。系统禁止将未受 Git 忽略的备份直接写在当前项目根目录下的公开路径。

#### Scenario: 默认安全存储路径解析
- **WHEN** 系统初始化备份服务且未配置特殊环境变量
- **THEN** 备份路径解析为 `Path.home() / ".career-tracker" / "backups"`，并自动创建 `snapshots/` 与 `bundles/` 子目录。

#### Scenario: 环境变量自定义路径
- **WHEN** 设置环境变量 `CAREER_TRACKER_BACKUP_DIR=/custom/backup/dir`
- **THEN** 备份路径切换为该指定目录并校验写入权限。

---

### Requirement: SQLite WAL 事务一致性快照 (Online SQLite Snapshot)
系统 SHALL 使用底层 `sqlite3.backup` API 对 `data/tracker.db` 执行在线安全快照，确保在 WAL 模式下不丢事务、不产生脏读且不阻塞并发读写。

#### Scenario: 执行在线数据库快照
- **WHEN** 触发数据库微快照（如应用启动或数据变更钩子）
- **THEN** 系统通过 SQLite 连接级 backup 接口将数据原子同步至安全区 `snapshots/tracker_auto_<timestamp>.db`。

---

### Requirement: 全量资产画像封包归档 (Full Profile & Asset Bundling)
系统 SHALL 支持生成包含 `tracker.db`、`profile.md`、`applicant_profile.json`、`data/resumes/` 目录下全部简历实体、`data/.profile_hash` 以及 `career_data/` 的完整 ZIP 资产包。

#### Scenario: 创建全量资产备份包
- **WHEN** 用户或系统触发全量备份归档
- **THEN** 系统在安全区 `bundles/` 目录下生成 `bundle_<timestamp>.zip`，并在包内附带包含表行数、哈希指纹和生成时间的 `manifest.json`。

---

### Requirement: 启动自检与节流快照 (Startup Check & Throttled Snapshot)
系统在后端服务（Flask/FastAPI/MCP）启动时 SHALL 自动触发自检与快照。为避免高频重启产生大量冗余，若距离上次自动快照时间小于设定的节流阈值（默认 2 小时），系统 SHALL 跳过重复快照。

#### Scenario: 首次启动或超过节流时间启动
- **WHEN** 系统启动且距离上次自动快照已超过 2 小时（或为首次快照）
- **THEN** 系统自动在外部安全区创建一份新的快照，并更新时间戳记录。

#### Scenario: 短时间内频繁重启
- **WHEN** 系统在 10 分钟内再次重启
- **THEN** 系统自检识别到间隔小于 2 小时，跳过快照生成，不占用多余存储。

---

### Requirement: 自动轮转与防膨胀策略 (Retention Policy)
系统 SHALL 自动维护备份生命周期，防止磁盘空间无限制膨胀。默认策略为保留最近 30 天内快照，且快照总数不超过 50 份。超出阈值时 SHALL 自动按时间升序淘汰最旧的历史备份。

#### Scenario: 触发快照自动淘汰
- **WHEN** 安全区快照总数达到 51 份
- **THEN** 系统自动删除创建时间最早的 1 份快照，确保总量维持在 50 份以内。

---

### Requirement: 灾难检测与自愈探测 (Disaster Detection & Auto-Recovery Guidance)
当系统启动发现工作区内的 `data/tracker.db` 或用户画像文件缺失时，系统 SHALL 自动检索安全区中的最新备份，并在控制台/UI 发出高亮警告与恢复指引，或支持一键自愈。

#### Scenario: 数据库意外丢失时的自愈探测
- **WHEN** 应用启动时 `data/tracker.db` 不存在，但在外部安全区检索到有效的历史快照
- **THEN** 系统在日志/控制台打印紧急预警并列出可用快照元数据（时间、公司数、投递数），提供 CLI/API 恢复命令。
