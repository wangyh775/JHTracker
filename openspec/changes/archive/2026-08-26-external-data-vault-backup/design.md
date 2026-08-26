## Context

参见 `proposal.md`。当前系统的数据文件包括 SQLite 数据库（`data/tracker.db`）、用户画像（`data/profile.md`, `data/applicant_profile.json`, `data/.profile_hash`）、4-Track 简历文件（`data/resumes/*`）以及重点企业清单（`career_data/*`）。这些文件由于包含高度敏感的个人隐私，不能通过 Git 跟踪。现有的备份机制位于 `data/backups/`，与源数据共处于同一父目录下，极易在智能体执行重构或清理时被一并误删。

## Goals / Non-Goals

**Goals:**
- **物理隔离**：建立位于 Git 工作区之外的安全备份区（`~/.career-tracker/backups/`）。
- **事务安全**：使用 SQLite 底层 Backup API 确保 WAL 模式下的在线热备无损。
- **全量资产纳管**：将数据库表数据与用户画像、简历二进制文件一体化封包。
- **自动化与防膨胀**：实现应用启动无感快照、2 小时间隔节流以及最多 50 份/30 天自动轮转。
- **灾难探测与自愈指引**：启动检测丢失并提供明确恢复路径。
- **防呆熔断**：在代码入口与测试层阻止 `drop_all` 意外抹除生产数据。

**Non-Goals:**
- 不引入外部云存储（如 S3/OSS/网盘）上传逻辑，坚持 100% 本地化与隐私绝对安全。
- 不对 SQLite 数据库进行复杂的表级增量 Binlog 解析，统一采用轻量级 Page 级快照与 ZIP 归档。

## Decisions

### 决策 1: 外部存储路径规范
- **选择**：跨平台的 `Path.home() / ".career-tracker" / "backups"`（支持 `CAREER_TRACKER_BACKUP_DIR` 环境变量覆盖）。
- **理由**：
  1. `Path.home()` 在 Windows、macOS 和 Linux 上均有标准位置，且处于智能体当前项目目录之外。
  2. 即使智能体在项目根目录下执行 `git clean -fdx` 或删除 `data/`，均无法波及用户主目录。
- **替代方案**：
  - *系统临时目录 `temp/`*：会被操作系统定期清理，不可靠。
  - *同级外部目录 `../career-tracker-backups`*：对工作区目录命名有强假设，跨机器不通用。

### 决策 2: 备份引擎技术选型
- **选择**：`sqlite3.backup()` 在线备份 API + `zipfile` 归档。
- **理由**：
  1. SQLite 在 WAL 模式下存在 `-wal` 和 `-shm` 文件，简单文件拷贝在写操作并发时会导致快照损坏；`sqlite3.Connection.backup()` 能够保证原子一致性。
  2. 配合标准库 `zipfile` 打包静态 Markdown、JSON 与简历 PDF，零第三方依赖。
- **替代方案**：
  - *Shell 调用 `sqlite3 .dump`*：需要依赖外部系统命令环境，跨平台（特别是 Windows PowerShell/cmd）兼容性较差。
  - *文件级 `shutil.copy2`*：无法保证 WAL 写入中数据的一致性。

### 决策 3: 快照分级（微快照 vs 全量资产包）
- **选择**：
  1. **微快照 (Micro Snapshot)**：仅执行 `tracker.db` 在线备份 + `profile.md` 同步，用于每次应用启动时的日常轻量快照（毫秒级耗时）。
  2. **全量资产包 (Full Bundle Zip)**：包含 DB、全量画像套件、`data/resumes/` 和 `career_data/`，用于手动归档、每日冷备或重大升级前置触发。
- **理由**：兼顾启动性能与容灾完整性。

### 决策 4: 启动期自愈探测与预警交互
- **选择**：后端初始化自检，若 `tracker.db` 不存在，自动扫描外部 Vault：
  - 若找到历史快照：在终端与日志输出高亮警告，提示快照时间及包含的投递记录数，并提供一键恢复 CLI/API。
  - 若无快照：才执行全新空白数据库初始化。
- **理由**：防止智能体误删数据库后，后端静默创建了一个空库，导致用户误以为数据正常而写入新数据造成数据覆盖。

## Risks / Trade-offs

- **[Risk] 磁盘空间占用膨胀**
  - *Mitigation*: 实施严格的保留策略（Retention Policy），快照最多保留 50 份，超额自动按时间戳清理最旧文件；微快照体积通常仅数 MB。
- **[Risk] 外部目录读写权限问题**
  - *Mitigation*: 在初始化时进行 `try...except` 权限校验，若主目录不可写则降级记录 Warning 并支持通过环境变量重定向路径。
- **[Risk] 频繁重启导致快照堆积**
  - *Mitigation*: 引入 2 小时节流机制，短期内反复重启直接跳过自动快照。

## Migration Plan

1. 在 `services/backup_vault.py` 中实现 `ExternalVaultService` 单例。
2. 在 `app.py`（或工厂函数 `create_app`）启动流程中挂载 `init_vault()` 和 `startup_health_check()`。
3. 改造 `routes/backup.py`，将现有的 Web 备份与恢复接口对接至外部 Vault。
4. 更新 `AGENTS.md`、`CLAUDE.md` 及 `docs/database.md`，固化智能体安全防御规则。
