# 数据库设计

_JHTracker 的数据模型：6 张表、字段说明、实体关系与迁移管理。定义见 `models.py`，迁移脚本位于 `migrations/versions/`。_

---

## 📋 表清单

| 表名 | ORM 模型 | 用途 | 关系 |
|---|---|---|---|
| `companies` | `Company` | 公司库（含 AI 评分） | 1:N applications / notes |
| `applications` | `Application` | 投递记录（状态机 + 归档） | N:1 company；1:N feedbacks |
| `notes` | `Note` | 笔记（可挂公司） | N:1 company（可空） |
| `timeline` | `Timeline` | 甘特图时间线节点 | 无外键 |
| `interview_feedbacks` | `InterviewFeedback` | 面试复盘 | N:1 application |
| `resumes` | `Resume` | 简历版本 | 无外键 |
| `agent_tasks` | `AgentTask` | Agent 任务日志与状态 | 1:N agent_events |
| `agent_events` | `AgentEvent` | Agent 推理与执行步骤事件 | N:1 agent_task |

---

## 🗺️ ER 图

```mermaid
erDiagram
    companies ||--o{ applications : "被投递"
    companies ||--o{ notes : "被记录"
    applications ||--o{ interview_feedbacks : "包含"
    agent_tasks ||--o{ agent_events : "包含"
    agent_tasks {
        int id PK
        string task_id UK "任务 UUID"
        string agent_name "Agent 名称"
        string status "running/completed/failed"
        datetime created_at
        datetime updated_at
    }
    agent_events {
        int id PK
        int task_id FK "关联 agent_tasks.id"
        string event_type "thought/tool_call/observation"
        text payload_json "JSON 结构体数据"
        datetime created_at
    }
    companies {
        int id PK
        string name UK "公司名，唯一"
        string industry "行业"
        string city "城市"
        string sub_city "子城市/区"
        string job_type "岗位方向"
        text match_reason "匹配理由"
        string priority "S/A/B/C"
        string website "官网"
        string source_list "来源清单"
        int salary_min "参考薪资下限 k/月"
        int salary_max "参考薪资上限 k/月"
        string scale "规模"
        string financing_stage "融资阶段"
        string tags "逗号分隔标签"
        string company_type "企业性质"
        int score "AI 匹配评分 0-100"
        string score_reason "AI 评分理由"
        datetime created_at
    }
    applications {
        int id PK
        int company_id FK
        string position "岗位名称"
        string channel "投递渠道"
        string status "状态机"
        date apply_date "投递日期"
        date deadline "截止日期"
        int salary_min "投递薪资下限"
        int salary_max "投递薪资上限"
        text job_desc "JD 描述"
        string url "投递链接"
        text feedback "备注反馈"
        string offer_status "pending/accepted/rejected"
        boolean is_archived "是否归档"
        datetime archived_at "归档时间"
        datetime created_at
        datetime updated_at "状态变更时间"
    }
    notes {
        int id PK
        int company_id FK "可空"
        string category "分类"
        string title "标题"
        text content "内容"
        datetime created_at
    }
    timeline {
        int id PK
        date event_date "开始日期"
        date end_date "结束日期，空=单日"
        string title "标题"
        text description "描述"
        string event_type "action/deadline/milestone"
        boolean done "是否完成"
        datetime created_at
    }
    interview_feedbacks {
        int id PK
        int application_id FK
        string interviewer "面试官"
        date interview_date "面试日期"
        string round "一面/二面/终面"
        int difficulty "难度 1-5"
        int self_rating "自评 1-5"
        text questions "问题记录"
        text improvement "改进点"
        datetime created_at
    }
    resumes {
        int id PK
        string name "简历名称"
        string version "版本号"
        string file_path "相对路径 data/resumes/"
        string file_type "pdf/docx"
        int file_size "字节数"
        text note "备注"
        boolean is_default "是否默认"
        string pdf_path "DOCX 转出的 PDF 预览路径"
        datetime created_at
    }
```

---

## 🏷️ 关键枚举与规则

### 投递状态机（`Application.status`）

```mermaid
stateDiagram-v2
    accTitle: Application Status State Machine
    accDescr: Applications flow from pending to submitted through screening, tests and interviews, ending in offer or rejected

    [*] --> 待投递
    待投递 --> 已投递
    已投递 --> 简历筛选
    简历筛选 --> 笔试
    笔试 --> 一面
    一面 --> 二面
    二面 --> 终面
    终面 --> Offer
    Offer --> [*]
    状态间可被拒绝: 已拒
    待投递 --> 已拒
    已投递 --> 已拒
    简历筛选 --> 已拒
    笔试 --> 已拒
    一面 --> 已拒
    二面 --> 已拒
    终面 --> 已拒
    已拒 --> [*]
```

> 注：状态流转是**自由编辑**（任意状态可互相切换），上图为典型流程。完整枚举见 `constants.py:3`。

### 其他枚举

| 字段 | 取值 | 定义位置 |
|---|---|---|
| `Company.priority` | `S` / `A` / `B` / `C` | `constants.py:24`（含按公司名关键词推断规则） |
| `Company.scale` | 少于50人 / 50-200人 / 200-1000人 / 1000-5000人 / 5000人以上 | `constants.py:53` |
| `Company.financing_stage` | 未融资 / 天使轮 / A轮 / B轮 / C轮 / D轮及以上 / 已上市 / 国企 / 外企 | `constants.py:54` |
| `Application.offer_status` | `pending` / `accepted` / `rejected` | `constants.py:38` |
| `Timeline.event_type` | `action` / `deadline` / `milestone` | 自由字符串，模板按类型着色 |

---

## 🔑 归档机制（`is_archived`）

投递记录支持**自动归档**：`updated_at` 超过 N 天（默认 15，可配）且不在保护名单内的活跃记录，会被标记为 `is_archived=True`。

**保护规则**（`services/archive.py:14`）：状态为 `Offer` 且 `offer_status ∈ {pending, accepted}` 的记录**永不自动归档**。

```mermaid
flowchart LR
    accTitle: Auto Archive Decision Flow
    accDescr: Active applications older than the stale threshold are archived unless they are pending or accepted offers

    start([🔄 每次访问投递列表]) --> enabled{自动归档开启?}
    enabled -- 否 --> done([结束])
    enabled -- 是 --> throttle{今日已跑过?<br/>.archive_last_run}
    throttle -- 是 --> done
    throttle -- 否 --> stale{updated_at < 今天-N天?}
    stale -- 否 --> done
    stale -- 是 --> offer{Offer 且 pending/accepted?}
    offer -- 是 --> done
    offer -- 否 --> archive[📦 标记 is_archived=True]
    archive --> done

    classDef dec fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef act fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    class enabled,throttle,stale,offer dec
    class archive act
```

---

## 🧬 迁移管理

项目使用 **Flask-Migrate**（Alembic）管理 schema 变更，历史迁移见 `migrations/versions/`：

| 迁移 | 内容 |
|---|---|
| `8f5f295b6215` | 初始：company salary / application offer 等基础字段 |
| `a1b2c3d4e5f6` | 投递记录新增归档字段 `is_archived` / `archived_at` |
| `3ccaa5ea3b4a` | 简历表新增 DOCX→PDF 预览路径 `pdf_path` |

**新增字段的标准流程**（详见 [development.md](development.md#数据库迁移)）：

```bash
flask db migrate -m "描述"
flask db upgrade
```

> ⚠️ 注意：`app.py` 启动时调用 `db.create_all()`，它**只建表、不迁移**。已有库变更 schema 必须走 `flask db upgrade`。

---

## 🔗 相关文档

- [系统架构](architecture.md) — 模块与数据流
- [路由/API 参考](api.md) — 操作这些表的端点
- [开发指南](development.md) — 迁移与测试流程

---

_最后更新：2026-07-31 · 维护者：JHTracker 项目组_
