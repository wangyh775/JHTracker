## Purpose

升级 auto-sourcing spec：`create_application` 工具 SHALL 接收并持久化 `form_type` 与 `source_platform` 字段，供下游 application-executor 选择填写策略；`applications` 表 SHALL 新增对应列。

## Requirements

### Requirement: create_application 接收 form_type 与 source_platform

`create_application` MCP 工具 SHALL 接收 `form_type` 与 `source_platform` 参数，并写入 application 记录。

#### Scenario: create_application 携带 form_type
- **WHEN** Agent 调用 `create_application(form_type="structured", source_platform="beisen", ...)`
- **THEN** 系统 SHALL 将 `form_type` 与 `source_platform` 写入 application 记录
- **THEN** 系统 SHALL 返回包含这两个字段的 application 详情

#### Scenario: create_application 未传 form_type
- **WHEN** Agent 调用 `create_application(...)` 未提供 `form_type`
- **THEN** 系统 SHALL 写入默认值 `form_type = "open_question"`
- **THEN** 系统 SHALL 写入 `source_platform = None`

### Requirement: applications 表新增 form_type 与 source_platform 列

系统 SHALL 通过 Alembic migration 在 `applications` 表新增两列：

```sql
ALTER TABLE applications ADD COLUMN form_type TEXT;
ALTER TABLE applications ADD COLUMN source_platform TEXT;
```

#### Scenario: migration 幂等执行
- **WHEN** migration 已执行过
- **THEN** 重复执行 SHALL NOT 报错（使用 `if not exists` 检查）

#### Scenario: 旧数据兼容
- **WHEN** 已有 application 记录未设置 form_type
- **THEN** 系统 SHALL 视其 `form_type` 为 `None`，application-executor SHALL 按 `open_question` 处理

### Requirement: list_applications 与 get_application 返回新字段

`list_applications` 与 `get_application` SHALL 在返回结果中包含 `form_type` 与 `source_platform` 字段。

#### Scenario: get_application 返回 form_type
- **WHEN** Agent 调用 `get_application(application_id=100)`
- **THEN** 返回结果 SHALL 包含 `form_type` 与 `source_platform` 字段

### Requirement: source_url 校验保留

原 spec 中 `source_url` 必填的校验 SHALL 保持不变。`source_platform` 是对 `source_url` 的补充标注，不替代 `source_url`。

#### Scenario: source_url 仍必填
- **WHEN** Agent 调用 `create_application(...)` 未提供 `source_url`
- **THEN** 系统 SHALL 拒绝创建并返回错误，行为与原 spec 一致
