## Purpose

提供可复用的求职答案库（Answer Bank）和按岗位族路由的经历片段库（Experience Bank），供 Agent 预填网申表单时逐字段检索。敏感答案（身份/薪酬/签证等）不独立存储，优先从 `data/profile.md`（用户画像）直通；非敏感答案支持从过往提交自动沉淀、人工维护、按 `(question_pattern+role_family)` 去重。

借鉴 JobHuntBot `answer_bank.template.md` 与 `experience_bank.template.md`。

## ADDED Requirements

### Requirement: AnswerBank 存储与检索
系统 SHALL 持久化 `AnswerBank` 记录，字段：`id`、`question_pattern`、`answer`、`role_family`（可空=通用）、`needs_review`（默认 0）、`source`（manual / extracted）、`created_at`。

#### Scenario: 按问题模式查答案
- **WHEN** MCP 工具 `get_answer_bank(role_family, question)` 被调用
- **THEN** 系统 SHALL 先匹配 `role_family` 精确 + `question_pattern` 模糊（子串+正则），再回退到 `role_family=NULL` 的通用答案；命中 `needs_review=1` 的答案必须在返回值中标记。

### Requirement: AnswerBank 去重与变更
系统 SHALL 在 `upsert_answer_bank` 时按 `(question_pattern, role_family)` 做唯一约束 upsert。

#### Scenario: 人工更新答案
- **WHEN** 用户或 Agent 对同模式同岗位族重复插入答案
- **THEN** 系统 SHALL 更新已存在行并返回更新后的 ID，不产生重复行。

### Requirement: 敏感字段答案从 profile 直通
系统 SHALL 对命中 `SENSITIVE_FIELD_PATTERNS` 的问题，跳过 AnswerBank 查库，改为从 `data/profile.md` 解析后返回；若 profile 中缺失则标记 `missing=true`。

#### Scenario: 问期望薪资
- **WHEN** 检索 "expected salary" 或 "期望薪资" 类问题
- **THEN** 系统 SHALL 解析 `data/profile.md` 的 target_salary 字段；缺失时返回 `missing=true` 并触发人工询问（`awaiting_human`），绝不猜测。

### Requirement: ExperienceBank 按岗位族路由
系统 SHALL 持久化 `ExperienceBank` 记录，字段：`id`、`role_family`、`bullet_text`、`jd_keywords`、`priority`。

#### Scenario: 匹配岗位经历
- **WHEN** MCP 工具 `get_resume_for_role(role_family, jd_keywords)` 被调用
- **THEN** 系统 SHALL 返回该岗位族下 `jd_keywords` 与传入关键词交集最多、priority 最高的前 N 条经历片段，并给出推荐默认简历版本 ID。

### Requirement: 提交历史自动沉淀答案
系统 SHALL 在 `record_submission_result(success=true)` 时扫描本次 prefilled_data 字段，对 AnswerBank 未命中且非敏感的问答对，自动按 `source='extracted'` 写入，需人工确认后才参与下一次检索（`needs_review=1` 默认置 1）。
