## ADDED Requirements

### Requirement: 数据库与核心画像防误删熔断保护 (Database & Asset Destruction Guard)
系统 SHALL 禁止在非测试环境（`TESTING=False`）下任意调用 `db.drop_all()` 或批量删除 `data/` 核心文件。若需执行危险重构或破坏性操作，必须提供显式环境变量确认（如 `ALLOW_DROP_DB=I_KNOW_WHAT_I_AM_DOING`），并在操作前强制触发一次外部安全区快照。

#### Scenario: 生产或日常运行环境下意外触发 drop_all
- **WHEN** 在默认开发/生产模式下执行包含 `db.drop_all()` 的脚本且未设置确认环境变量
- **THEN** 系统立即抛出 `RuntimeError("CRITICAL: drop_all is forbidden in non-test environment!")` 熔断拦截，阻止表结构与数据被抹除。

#### Scenario: 测试环境隔离运行
- **WHEN** 运行 pytest 自动化测试套件
- **THEN** 测试固件严格使用内存数据库（`:memory:`）或 pytest 提供的临时目录（`tmp_path`），严禁读写或覆盖 `data/tracker.db`。
