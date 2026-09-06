# 开发者环境与架构指南 (Developer Guide) 🛠️💻

本文档面向 JHTracker 的二次开发者与开源贡献者，详细阐述系统的技术栈架构、代码目录组织、环境搭建、自动化测试流程与核心开发规范。

---

## 1. 技术栈全貌

JHTracker 采用前后端分离的现代化架构，兼顾轻量化部署与极佳的响应性能：

- **后端中枢**：
  - **语言/运行时**：Python 3.10+
  - **Web 框架**：FastAPI（基于 Starlette 与 Pydantic v2 提供强类型 API）
  - **智能体接入**：FastMCP（Anthropic Model Context Protocol Python SDK 实现）
  - **存储引擎**：SQLite 3（使用 `aiosqlite` 实现全异步 I/O，并利用 `FTS5` 模块支持高效分词全文搜索）
  - **网络与采集**：`httpx`（异步 HTTP 客户端）、`BeautifulSoup4`（HTML 解析提取）
- **前端中台**：
  - **语言/构建**：TypeScript 5.x + Vite 5.x
  - **核心框架**：React 18
  - **表格与数据流**：AG Grid React v36.1.0（支持左固定列、虚拟滚动与全定制 Cyber-Dark 主题）
  - **3D 视觉引擎**：Spline 3D Runtime（动态赛博粒子与 WebGL 降级）
  - **UI 与样式**：Tailwind CSS + Lucide React 图标体系

---

## 2. 工程目录结构说明

```
JHTracker/
├── backend/                       # Python 后端工程
│   ├── src/                       # 核心业务源码
│   │   ├── main.py                # FastAPI Web API 服务入口、路由与生命周期挂载
│   │   ├── mcp_server.py          # FastMCP 智能体工具暴露协议入口 (10大受控工具)
│   │   ├── models.py              # Pydantic 数据模型定义（JobItem, ResumeItem, ApplicationItem 等）
│   │   ├── db.py                  # 数据库连接池初始化、表迁移与会话管理
│   │   ├── security.py            # 安全防线（SQL 注入防护、安全标识符正则校验）
│   │   ├── repositories/          # 数据访问持久层
│   │   │   ├── job_repository.py  # 公共岗位库（public_jobs.db）检索与 FTS5 同步
│   │   │   └── user_repository.py # 私有用户库（~/.JHTracker/user_data.db）增删改查
│   │   └── services/              # 领域业务逻辑层
│   │       ├── recommendation_service.py # 人在环路 (HITL) 推荐、特征加权与双路召回算法
│   │       ├── resume_service.py         # 简历解析、ATS 评分与独立版本生成
│   │       ├── job_sync_service.py       # 统一爬虫调度与入库同步管理
│   │       └── spiders/                  # 招聘渠道定向爬虫适配器集合
│   │           ├── base_spider.py        # 爬虫抽象基类与清洗标准
│   │           └── qiuzhifangzhou_spider.py # 求职方舟定向数据采集适配器
│   ├── tests/                     # 自动化单元与集成测试套件 (43 项全绿)
│   │   ├── test_recommendations.py# 推荐算法与反馈闭环测试
│   │   ├── test_spider_qiuzhifangzhou.py # 爬虫解析与幂等性测试
│   │   ├── test_mcp_tools.py      # MCP 工具集权限与安全测试
│   │   ├── test_resume.py         # 简历 CRUD 与版本流转测试
│   │   ├── test_api.py            # FastAPI 接口全生命周期回归测试
│   │   └── test_kanban_archival.py# 看板卡片归档、删除与筛选测试
│   └── requirements.txt           # Python 依赖清单
├── frontend/                      # React 前端工程
│   ├── src/
│   │   ├── components/            # 核心业务组件
│   │   │   ├── JobBoard.tsx       # 全景岗位大厅（AG Grid 挂载与状态同步）
│   │   │   ├── PinnedJobTable.tsx # AG Grid 封装实现（左侧锁定列与自适应宽屏）
│   │   │   ├── FilterPillsBar.tsx # 城市与类别快捷胶囊过滤器
│   │   │   ├── SplineHeader.tsx   # 赛博 3D 动态顶栏与降级画布
│   │   │   ├── KanbanBoard.tsx    # 投递进展六大阶段流转看板
│   │   │   ├── RecommendationPanel.tsx # 人在环路智能推荐与权重监控面板
│   │   │   ├── ResumeWorkbench.tsx# 简历工作台（自动入库、版本树与只读保护）
│   │   │   └── ResumeImportModal.tsx # 本地文件上传与解析弹窗
│   │   ├── services/api.ts        # Axios 请求封装与统一错误拦截
│   │   ├── types.ts               # TypeScript 共享类型接口
│   │   ├── App.tsx                # 根应用与视图路由分发
│   │   └── main.tsx               # 前端 DOM 挂载入口
│   ├── package.json               # Node 依赖与构建脚本
│   └── vite.config.ts             # Vite 配置与反向代理设定
├── data/                          # 本地共享数据资产目录
│   └── public_jobs.db             # 公共岗位 SQLite 数据库 (24,000+ 岗位)
├── docs/                          # 官方技术文档中心
├── specs/                         # 需求规格说明、设计方案与任务看板
├── scripts/                       # 运维与启动脚本目录 (含 start.bat / start.ps1)
└── AGENTS.md                      # AI 协作开发规约与红线说明
```

---

## 3. 开发环境搭建与启动

### 3.1 Python 后端开发服务

建议使用虚拟环境进行隔离开发：

```bash
# 进入后端目录
cd backend

# 创建并激活虚拟环境 (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 启动 FastAPI 开发服务器 (支持代码热重载)
python src/main.py
```
> 服务器默认监听 `http://127.0.0.1:8000`。

### 3.2 React 前端开发服务

```bash
cd frontend

# 安装依赖
npm install

# 启动 Vite 开发服务器 (支持 HMR 热更新)
npm run dev
```
> 前端默认监听 `http://localhost:5173`，并通过 Vite 代理将 `/api` 请求自动转发至 `127.0.0.1:8000`。

---

## 4. 自动化测试与质量检验 (重要)

为保障系统稳定运行，**所有代码变更提交前必须通过全套自动化检验**。

```mermaid
graph LR
    Code["💻 代码修改"] --> PyTest["🧪 python -m pytest (全套 43 项后端单元测试)"]
    PyTest --> FrontendBuild["📦 npm run build (TypeScript 类型检查 + Vite 构建)"]
    FrontendBuild --> Pass["✅ 验证通过，可提交合并"]
```

### 4.1 后端测试验证

⚠️ **极其重要**：执行 pytest 时切勿直接敲 `pytest`（会导致 `src` 模块路径解析失败），**必须使用 Python 模块化启动模式**：

```bash
cd backend

# 运行全量测试套件
python -m pytest

# 运行特定模块测试（以推荐算法为例）
python -m pytest tests/test_recommendations.py -v

# 运行简历与 API 测试
python -m pytest tests/test_resume.py tests/test_api.py -v
```

### 4.2 前端类型检查与构建验证

前端统一通过 TypeScript 编译与 Vite 打包命令检验：

```bash
cd frontend

# 执行 TypeScript 类型校验与打包构建
npm run build
```
输出 `✓ built in xxx ms` 且无任何类型警告即为合规。

---

## 5. 核心架构贡献红线

1. **绝对禁止破坏双库物理隔离**：公共岗位代码决不能写入用户私有库，外部智能体决不能直接写入用户投递看板。
2. **安全标识符验证**：任何传入数据库检索的 `job_id` 或 `resume_id` 必须通过 `security.validate_identifier` 校验，防范注入攻击。
3. **幂等性优先**：新增爬虫或同步逻辑必须保证多次执行不产生重复职位或重复特征项。
