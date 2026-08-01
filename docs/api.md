# 路由 / API 参考

_JHTracker 的全部 HTTP 端点，按 blueprint 组织。所有端点定义在 `routes/` 目录，注册入口为 `routes/__init__.py`。_

---

## 🧭 约定

- **Base URL**：`http://127.0.0.1:5000`
- **鉴权**：无。应用仅监听 `127.0.0.1`（见 `app.py:52`），不面向公网
- **写操作**：一律 `POST` 表单 + 302 重定向（PRG 模式）
- **错误处理**：表单校验失败（`ValueError`）静默回退并刷新页面；资源不存在返回 404 页面
- **JSON 接口**：Agent API 全部返回 JSON（`/api/` 前缀），常规页面路由返回 HTML

---

## 📄 页面与动作端点总览

| Blueprint | 前缀 | 端点数 | 说明 |
|---|---|---|---|
| dashboard | `/`, `/dashboard` | 5 | 看板（含 SSE `/api/stream` 与 `/api/notify`） |
| company | `/companies` | 5 | 公司库 + 搜索 JSON API |
| application | `/applications` | 11 | 投递跟踪、归档、面试反馈 |
| note | `/notes` | 3 | 笔记 CRUD |
| timeline | `/timeline` | 4 | 甘特图时间线 |
| import_data | `/import` | 4 | 公司清单导入/重同步、时间线初始化 |
| backup | `/backup` | 3 | 备份导出/恢复 |
| resume | `/resumes` | 8 | 简历版本管理 |
| profile | `/profile` | 2 | 候选人画像 |
| agent_api | `/api/v1`, `/api/agent`, `/traces` | 15 | Agent REST API (公司搜索/创建、评分更新、画像、Trace 追踪、HITL 决策审核、Agent 任务中心) |

---

## 🤖 Agent API 端点 (`routes/agent_api.py`)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/companies/search` | 按关键词 `q` 搜索公司，返回 JSON |
| POST | `/api/v1/companies` | 批量自动去重写入公司记录 |
| POST | `/api/v1/companies/<id>/score` | 更新公司 AI 评分与评分理由 |
| POST | `/api/v1/applications` | 自动创建 `Pending Approval` 状态的岗位申请记录 (支持 `match_score`, `agent_reason`, `agent_task_id`, `source_url`, `resume_id`) |
| POST | `/api/v1/applications/<id>/review` | 人在回路审核接口 (`action="approve"` 设为 `to_apply` / `"reject"` 设为 `rejected` 并生成 Memory) |
| GET | `/api/v1/profile` | 获取候选人画像与目标配置 JSON |
| GET | `/api/v1/profile/preferences` | 获取候选人画像、负向规则黑名单与历史拒绝反哺 Memory |
| POST | `/api/v1/traces` | 提交 Agent 任务执行轨迹 (`task_id`, `agent_name`, `event_type`, `payload`) |
| GET | `/api/v1/traces` | 获取 Agent 任务轨迹列表 JSON |
| GET | `/api/agent/tasks` | 查询 Agent 任务列表，含 `pending_approvals_count` 聚合 |
| GET | `/api/agent/tasks/<task_id>` | 查询单个 Agent 任务详情及完整事件 Trace 日志 |
| GET | `/api/agent/decisions/pending` | 列出所有待审批的岗位推荐提案（HITL 队列） |
| POST | `/api/agent/decisions/<id>` | 人类决策：`approve` → `Applied` / `reject` → `Rejected` + 写入 DecisionFeedback + Memory / `edit` → 更新字段 |
| GET | `/traces` | Agent 执行轨迹 UI 审计页面（HTML） |

### 🧑‍⚖️ HITL Decision Endpoints (`/api/agent/`)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/agent/decisions/pending` | 列出所有待审批的岗位推荐提案，含 `company_name`, `position`, `match_score`, `agent_reason`, `resume_name`, `source_url`, `created_at` |
| POST | `/api/agent/decisions/<id>` | 三动作决策：`approve`（状态 → `Applied`，记录 `DecisionFeedback`）/ `reject`（状态 → `Rejected`，写入 `DecisionFeedback` + `Memory`）/ `edit`（更新字段 + 记录 `DecisionFeedback`） |
| GET | `/api/agent/tasks` | 查询 Agent 任务列表，含 `pending_approvals_count` 聚合 |
| GET | `/api/agent/tasks/<task_id>` | 查询单个 Agent 任务详情及完整事件 Trace 日志 |

---

## 🔌 MCP Server (Model Context Protocol)

MCP 服务定义在 `mcp_server.py`，支持 stdio / JSON-RPC 传输。当前共 **36 个工具**，覆盖 11 个数据域。

### 暴露资源与工具

**Resource**
- `jhtracker://profile` — 返回候选人 Profile 文本

**👤 画像 & 偏好**
- `get_candidate_profile()` — 读取候选人画像
- `update_candidate_profile(content)` — 更新候选人画像
- `get_user_preferences()` — 获取偏好设置、负向规则、拒绝反馈
- `add_memory_rule(category, rule_value)` — 添加排除规则
- `delete_memory_rule(memory_id, confirm)` — 删除记忆规则

**🏢 公司**
- `search_companies(query)` — 模糊搜索公司
- `get_company(company_id)` — 获取公司完整详情（含投递数、笔记数）
- `create_company(...)` — 创建公司（自动去重）
- `update_company(company_id, ...)` — 更新公司字段
- `update_company_score(company_id, score, reason)` — 更新评分
- `delete_company(company_id, confirm)` — 删除公司（级联）

**📮 投递**
- `create_application(...)` — 创建投递（Pending Approval）
- `get_application(application_id)` — 获取投递详情
- `list_applications(status, company_id, channel)` — 筛选投递列表
- `update_application_status(application_id, status)` — 更新状态
- `get_pending_approvals()` — 获取待审批提案
- `handle_decision(application_id, action, ...)` — 审批/拒绝/编辑
- `archive_application(application_id, archive)` — 归档/恢复

**🎙️ 面试反馈**
- `create_interview_feedback(application_id, ...)` — 添加面试复盘
- `list_interview_feedbacks(application_id)` — 查询面试反馈

**📝 笔记**
- `create_note(company_id, title, content)` — 写笔记
- `list_notes(company_id)` — 查询笔记
- `update_note(note_id, ...)` — 编辑笔记
- `delete_note(note_id, confirm)` — 删除笔记

**📅 时间线**
- `create_timeline_event(event_date, title, ...)` — 创建时间线节点
- `list_timeline_events()` — 查询时间线
- `toggle_timeline_event(event_id)` — 切换完成状态

**📄 简历**
- `list_resumes()` — 查询简历版本列表
- `get_default_resume()` — 获取默认简历

**📊 统计**
- `get_statistics()` — 获取 Dashboard 核心指标

**🔍 评估**
- `evaluate_jd(jd_text, company_name, task_id)` — 评估 JD 文本
- `batch_evaluate_jds(jds)` — 批量评估多个 JD

**🔄 轨迹 & 任务**
- `record_agent_trace(task_id, agent_name, ...)` — 记录任务轨迹
- `list_agent_tasks(status, limit)` — 查询任务列表
- `get_agent_task(task_id)` — 查询任务详情 + 事件日志
- `clear_agent_traces(confirm)` — 清空全部轨迹

**🔔 系统**
- `notify_db_changed()` — 通知 UI 刷新（SSE）

### 客户端接入配置 (`mcp.json`)

在 Claude Desktop / Cursor / Hermes 的 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "jhtracker": {
      "command": "python",
      "args": [
        "D:\\DJTU\\HermesWorkspace\\career-tracker\\mcp_server.py"
      ]
    }
  }
}
```

### 可视化调试 (MCP Inspector)

运行以下命令可在浏览器中交互式测试工具：

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

---

## 🏠 看板 `routes/dashboard.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 看板主页：公司数/投递漏斗/城市与行业分布/优先级分布/紧急截止（7 天内）/待写复盘/最近动态/时间线提醒 |
| GET | `/dashboard` | 同上（别名） |

---

## 🏢 公司库 `routes/company.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/companies` | 公司列表。分页（40/页），支持多选筛选：`industry`、`city`、`priority`、`company_type`（均为可重复参数），关键词 `q` 匹配名称或匹配理由。排序：S > A > B > C，NULL 最后 |
| GET | `/companies/<int:c_id>` | 公司详情：基本信息 + 投递记录 + 笔记 |
| POST | `/companies/add` | 新增公司。字段见 `routes/company.py:70`；校验薪资范围 |
| POST | `/companies/<int:c_id>/edit` | 编辑公司 |
| POST | `/companies/<int:c_id>/delete` | 删除公司（级联删除投递/笔记） |
| GET | `/api/companies/search` | **JSON**：按名称模糊搜索，返回前 10 条 `{id, name, city, industry}` |

---

## 📮 投递跟踪 `routes/application.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/applications` | 投递列表。分页（30/页），筛选 `status`、`channel`；`view=active`（默认）/`view=archived`。访问时按设置**触发自动归档检查** |
| POST | `/applications/settings` | 保存归档设置：`archive_stale_days`、`archive_auto_enabled` |
| POST | `/applications/archive/run` | 手动执行归档 |
| POST | `/applications/<int:a_id>/archive` | 单条归档 |
| POST | `/applications/<int:a_id>/unarchive` | 恢复归档 |
| POST | `/applications/add` | 新增投递。校验薪资与日期顺序 |
| POST | `/applications/<int:a_id>/status` | 更新状态（可选更新 `feedback`） |
| POST | `/applications/<int:a_id>/offer_status` | 更新 Offer 决策（`pending/accepted/rejected`），跳回对比页 |
| POST | `/applications/<int:a_id>/delete` | 删除投递（级联删除面试反馈） |
| POST | `/applications/<int:a_id>/feedback/add` | 新增面试反馈 |
| POST | `/applications/<int:a_id>/feedback/<int:f_id>/delete` | 删除面试反馈 |
| GET | `/compare` | Offer 对比页：`status=Offer` 且未归档，按 `salary_max` 降序 |

> **安全重定向**：`_safe_redirect`（`routes/application.py:19`）只接受同源 referrer，防止开放重定向。

---

## 📝 笔记 `routes/note.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST | `/notes` | GET 列表（分页 30/页）；POST 新增 |
| POST | `/notes/<int:n_id>/edit` | 编辑笔记（可改关联公司） |
| POST | `/notes/<int:n_id>/delete` | 删除笔记 |

---

## 📅 时间线 `routes/timeline.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/timeline` | 甘特图视图，按日期排序 |
| POST | `/timeline/add` | 新增节点：`event_date`（必填）、`end_date`（可空，须不早于开始）、`title`、`description`、`event_type` |
| POST | `/timeline/<int:t_id>/edit` | 编辑节点 |
| POST | `/timeline/<int:t_id>/toggle` | 切换完成状态 |

---

## 📥 数据导入 `routes/import_data.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/import` | 导入页：展示已评分/待评分公司数 |
| POST | `/import/companies` | 从 `career_data/企业清单_{source}_*.md` 批量导入。`source` 参数仅允许字母数字（防路径遍历）。按公司名去重，行业优先取行内列，回退文件名推断 |
| POST | `/import/companies/resync` | 重新同步：从源 Markdown 更新已有公司的 `city/industry/job_type/match_reason`，清理误入库的表头行，防跨源覆盖 |
| POST | `/import/timeline` | 初始化秋招/春招关键节点（9 条预置，按标题去重） |

**Markdown 表格解析规则**（`utils.py:51`）：

- 公司名列精确匹配：`公司名称` / `公司` / `名称`（跳过统计表）
- 列名子串匹配：城市 `城市/地点`、岗位 `岗位/职位/方向`、理由 `匹配/理由`、行业 `细分行业/行业`

---

## 💾 备份与恢复 `routes/backup.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/backup` | 备份页：各表数据量统计 |
| POST | `/backup/export` | 导出 ZIP：`data.json`（6 张表全量，ISO 时间）+ `resumes/` 目录全部文件。文件名 `tracker_backup_YYYYMMDD_HHMMSS.zip`，存到 `data/backups/` |
| POST | `/backup/restore` | 恢复。支持 ZIP 或纯 JSON；`mode=skip`（默认，按名称跳过已存在公司）/`overwrite`。恢复前自动备份当前 DB 为 `*.before_restore.*`；还原简历文件时取 basename 防路径穿越；版本号不匹配拒绝恢复 |

**恢复时的 ID 重映射**：公司按名称匹配后重映射 `company_id`，投递重映射后关联面试反馈，保证外键一致性（`routes/backup.py:135`）。

---

## 📄 简历管理 `routes/resume.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/resumes` | 简历列表（按创建时间倒序）+ 默认简历 |
| POST | `/resumes/upload` | 上传。接受 `pdf/docx/doc`，≤20MB（`config.py:57`）。**`replace_id` 参数支持更新已有简历**（删旧文件、可选重新转 PDF）。首份自动设为默认。DOCX 用 LibreOffice headless 转 PDF 预览 |
| GET | `/resumes/<int:r_id>/preview` | 预览页 |
| GET | `/resumes/<int:r_id>/file` | 返回原始文件 |
| GET | `/resumes/<int:r_id>/pdf` | 返回预览 PDF：PDF 原样返回；DOCX 优先返回已转换 PDF，没有则实时转换一次 |
| GET | `/resumes/<int:r_id>/download` | 下载（带原文件名） |
| POST | `/resumes/<int:r_id>/edit` | 编辑名称/版本/备注 |
| POST | `/resumes/<int:r_id>/default` | 设为默认（取消其他默认） |
| POST | `/resumes/<int:r_id>/delete` | 删除（含物理文件） |

---

## 👤 候选人画像 `routes/profile.py`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/profile` | 查看画像（`data/profile.md` 不存在或为空时显示模板） |
| POST | `/profile/save` | 保存 Markdown 内容到 `data/profile.md` |

> AI 自动解析简历（Profile Skill）不走 Web 路由，由智能体调用 `skills/career-tracker-profile/SKILL.md` 完成，详见 [AI 评分文档](ai-scoring.md)。

---

## 🔗 相关文档

- [系统架构](architecture.md) — 请求生命周期与模块依赖
- [数据库设计](database.md) — 端点操作的数据表
- [AI 评分引擎](ai-scoring.md) — `scripts/ai_scorer.py` 命令行接口

---

_最后更新：2026-07-31 · 维护者：JHTracker 项目组_
