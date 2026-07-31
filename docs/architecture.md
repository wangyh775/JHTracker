# 系统架构

_JHTracker 的架构设计文档：技术栈、模块划分、请求生命周期与关键设计决策。_

---

## 🏗️ 架构总览

JHTracker 是一个**本地优先**的单体 Flask 应用：浏览器直接访问本机 5000 端口的 Flask 服务，所有数据落在本地 SQLite 数据库与文件系统，无任何云依赖。AI 能力（评分、简历解析、公司检索）以**可选**方式接入：核心业务不依赖 AI，未配置 API Key 时系统自动降级为关键词规则。

```mermaid
flowchart TB
    accTitle: Layered Architecture
    accDescr: Client to presentation to business services to data layer, with AI skills as external optional integration

    subgraph client ["🖥️ 客户端"]
        browser["浏览器<br/>Bootstrap 5 + Chart.js + 原生 JS"]
    end

    subgraph flask ["🌐 Flask 应用层"]
        factory["app.py<br/>create_app 工厂"]
        bp["routes/ ×9 blueprint<br/>页面渲染 + 表单处理"]
        ctx["context_processor<br/>全局模板变量"]
    end

    subgraph biz ["⚙️ 业务逻辑层"]
        services["services/<br/>settings.py / archive.py"]
        utils["utils.py<br/>日期/薪资/表格解析"]
    end

    subgraph data ["💾 数据层"]
        db[("SQLite<br/>data/tracker.db")]
        files["data/<br/>resumes/ backups/ profile.md settings.json"]
        career["career_data/<br/>企业清单_*.md"]
    end

    subgraph ai ["🤖 AI 能力（可选）"]
        scorer["scripts/ai_scorer.py<br/>两阶段评分引擎"]
        skills["skills/ ×8<br/>智能体 Skill 工作流"]
        llm["LLM API<br/>Anthropic / OpenAI 兼容"]
    end

    browser --> factory
    factory --> bp
    bp --> services
    bp --> utils
    bp --> db
    bp --> files
    services --> db
    utils --> career
    scorer --> db
    skills --> scorer
    scorer --> llm

    classDef app fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef biz fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef data fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    classDef ai fill:#fae8ff,stroke:#9333ea,stroke-width:2px,color:#581c87

    class factory,bp,ctx app
    class services,utils biz
    class db,files,career data
    class scorer,skills,llm ai
```

---

## 🧩 关键组件

| 组件 | 职责 | 技术 | 关键文件 |
|---|---|---|---|
| 应用工厂 | 初始化 Flask、注册 blueprint、注入全局模板变量 | Flask 3.0 | `app.py` |
| 配置中心 | 路径、密钥、分页、AI 参数，全部支持环境变量覆盖 | 标准库 | `config.py` |
| ORM 模型 | 8 张表的定义与关系 | SQLAlchemy 2.0 | `models.py` |
| 路由层 | HTTP 入口，页面渲染 + 表单处理 + Agent API | Flask Blueprint | `routes/` ×10 |
| MCP 服务 | Agent-Native 接口，暴露 MCP 资源与工具 | FastMCP / mcp SDK | `mcp_server.py` |
| 业务服务 | 归档节流、用户设置持久化 | 标准库 | `services/` |
| 工具函数 | 日期/薪资校验、Markdown 表格解析、安全文件名 | 标准库 | `utils.py` |
| 业务常量 | 状态机、行业/城市枚举、优先级规则 | 标准库 | `constants.py` |
| AI 评分引擎 | 关键词预筛 + LLM 批量评分，直连 SQLite | anthropic / openai | `scripts/ai_scorer.py` |
| 智能体 Skills | 公司检索、简历解析、评分、投递管理等 AI 工作流 | Markdown Skill | `skills/` ×8 |

---

## 🔄 请求生命周期

以「新增一条投递记录」为例，说明一次典型请求的处理链路：

```mermaid
sequenceDiagram
    accTitle: Add Application Request Lifecycle
    accDescr: Browser submits form to Flask route, which validates, persists to SQLite, and redirects back

    participant B as 🖥️ Browser
    participant R as 🌐 Flask Route<br/>app_add
    participant U as 🧰 utils
    participant D as 💾 SQLite

    B->>R: 📤 POST /applications/add<br/>表单字段
    R->>U: 校验薪资范围<br/>validate_salary
    R->>U: 解析日期<br/>parse_date + validate_dates
    U-->>R: ✅ 校验通过
    R->>D: 写入 Application 记录
    D-->>R: ✅ commit
    R-->>B: 🔀 302 重定向到投递列表
```

**要点：**

- 所有写操作都是**表单 POST + 服务端重定向**（PRG 模式），避免刷新重复提交
- 校验失败（`ValueError`）静默回退，不抛 500
- 重定向使用 `_safe_redirect`（`routes/application.py:19`）：仅允许同源 referrer，防开放重定向

---

## 🗂️ 模块职责与依赖关系

```mermaid
flowchart LR
    accTitle: Module Dependency Graph
    accDescr: App factory depends on routes, models and config; services depend on models; scripts access DB directly

    app["app.py"] --> routes["routes/"]
    app --> models["models.py"]
    app --> config["config.py"]
    routes --> models
    routes --> services["services/"]
    routes --> utils["utils.py"]
    routes --> constants["constants.py"]
    services --> models
    services --> config
    scripts["scripts/ai_scorer.py"] --> config
    scripts --> db[("🔗 直连 sqlite3")]
    skills["skills/"] -.-> scripts

    classDef core fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef leaf fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f

    class app,routes,models core
    class services,utils,constants,scripts,skills leaf
```

**依赖规则：**

- `routes/` 只做「收表单 → 调服务 → 渲染/重定向」，业务逻辑下沉到 `services/`
- `scripts/ai_scorer.py` 是独立进程，不走 Flask，直接 `sqlite3` 读写数据库，与 Web 应用通过 `config.py` 共享路径配置
- `constants.py` 与 `utils.py` 是纯函数模块，不依赖任何业务模块，可被任意层引用

---

## 📁 目录结构

```
career-tracker/
├── app.py                  # 应用工厂与启动入口
├── mcp_server.py           # MCP (Model Context Protocol) 服务入口
├── config.py               # 集中配置（环境变量可覆盖）
├── constants.py            # 业务常量与优先级/行业推断规则
├── extensions.py           # db / migrate 实例（独立于 app）
├── models.py               # 8 张表 ORM 定义（含 AgentTask / AgentEvent）
├── utils.py                # 工具函数
├── routes/                 # 10 个 blueprint
│   ├── dashboard.py        #   看板（漏斗/分布/紧急截止/SSE 推送）
│   ├── company.py          #   公司库
│   ├── application.py      #   投递跟踪 + 归档
│   ├── note.py             #   笔记
│   ├── timeline.py         #   甘特图时间线
│   ├── import_data.py      #   公司清单导入/重同步
│   ├── backup.py           #   备份导出/恢复
│   ├── resume.py           #   简历版本管理
│   ├── profile.py          #   候选人画像
│   └── agent_api.py        #   Agent API 端点 & Agent Trace 轨迹
├── services/               # 业务逻辑
│   ├── settings.py         #   用户设置（settings.json）
│   └── archive.py          #   投递归档（每日节流）
├── scripts/                # 命令行工具
│   ├── ai_scorer.py        #   AI 评分引擎
│   └── ...                 #   其他辅助脚本
├── skills/                 # 跨平台 AI 智能体 Skill ×8
├── templates/              # Jinja2 模板
├── static/                 # 前端资源（Bootstrap/Chart.js/KaTeX 本地化）
├── career_data/            # 公司清单 Markdown 数据源
├── data/                   # 运行时数据（gitignore）
│   ├── tracker.db          #   SQLite 数据库
│   ├── resumes/            #   简历文件
│   ├── backups/            #   备份 ZIP
│   ├── profile.md          #   候选人画像
│   └── settings.json       #   用户设置
├── migrations/             # Flask-Migrate 迁移脚本
└── tests/                  # pytest 测试
```

---

## 💡 关键设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| **100% 本地优先** | SQLite + 本地文件 | 数据不离开用户电脑；零部署成本 |
| **Blueprint 聚合** | `routes/__init__.py` 导出 `ALL_BLUEPRINTS` | 新增功能页只需加一个文件 + 一行注册 |
| **AI 可降级** | 未配置 Key 自动走关键词预筛 | AI 是增强而非必需，核心流程永不阻塞 |
| **评分直连 DB** | 脚本绕过 Flask 直接用 `sqlite3` | 评分是长任务，与 Web 进程解耦；共享 `config.py` 保证路径一致 |
| **表单 PRG 模式** | POST 后 302 重定向 | 防刷新重复提交；配合同源校验防开放重定向 |
| **设置存 JSON** | `data/settings.json` + 环境变量默认值 | 用户可改设置但无需动代码；`services/settings.py` 统一读写 |
| **归档节流** | `data/.archive_last_run` 每日一次 | 自动归档不打扰，规则见 `services/archive.py:80` |
| **前端零构建** | Bootstrap 5 + 原生 JS，vendor 本地化 | 双击 `start.bat` 即可用，无 npm 依赖 |

---

## 🔗 相关文档

- [数据库设计](database.md) — 表结构与关系
- [路由/API 参考](api.md) — 全部端点
- [AI 评分引擎](ai-scoring.md) — 评分流程与省 token 策略
- [开发指南](development.md) — 本地开发与测试

---

_最后更新：2026-07-31 · 维护者：JHTracker 项目组_
