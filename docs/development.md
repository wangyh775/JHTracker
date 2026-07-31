# 开发指南

_JHTracker 的本地开发手册：环境搭建、运行测试、数据库迁移、代码规范与常见问题。_

---

## 🛠️ 环境搭建

### 前置要求

| 要求 | 版本 | 检查命令 |
|---|---|---|
| Python | ≥ 3.10 | `python --version` |
| pip | 任意现代版本 | `pip --version` |
| LibreOffice（可选） | 任意 | DOCX 简历转 PDF 预览需要，不装则 DOCX 预览不可用 |

### 安装

```bash
git clone <repo-url>
cd career-tracker
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt        # 核心依赖
pip install -r requirements-ai.txt     # 可选：AI 评分（anthropic / openai）
pip install pytest                     # 可选：跑测试
```

### 启动

```bash
# 开发模式（自动重载 + 调试）
set FLASK_DEBUG=1      # Windows
export FLASK_DEBUG=1   # macOS / Linux
python app.py
```

启动后访问 `http://127.0.0.1:5000`。

> 环境变量与默认值对照见根目录 [.env.example](../.env.example)。

---

## 🧪 测试

项目使用 **pytest**，测试位于 `tests/`：

| 文件 | 覆盖内容 |
|---|---|
| `test_utils.py` | 日期解析、薪资校验、Markdown 表格解析等工具函数 |
| `test_models.py` | ORM 模型与关系（含 AgentTask / AgentEvent） |
| `test_routes.py` | 各 blueprint 路由（页面渲染、表单提交、404、状态流转） |
| `test_agent_api.py` | Agent REST API (/api/v1/) 与 Agent Trace 轨迹端点 |
| `conftest.py` | 测试夹具：内存 SQLite、测试客户端 |

```bash
# 运行全部测试
python -m pytest tests/

# 运行单个文件
python -m pytest tests/test_agent_api.py -v

# 只看失败详情
python -m pytest tests/ -q
```

---

## 🔌 MCP Server 本地调试

测试 Model Context Protocol (MCP) 服务 `mcp_server.py`：

```bash
# 1. 验证工具注册
python -c "import mcp_server; print([t.name for t in mcp_server.mcp._tool_manager.list_tools()])"

# 2. 官方 Inspector 浏览器可视化调试
npx @modelcontextprotocol/inspector python mcp_server.py
```

**约定：**

- 测试使用独立的内存/临时数据库（见 `conftest.py`），不触碰 `data/tracker.db`
- 新增功能须补对应测试；路由测试用 Flask `test_client` + 302 跟随断言

---

## 🗃️ 数据库迁移

新增或修改字段的标准流程（Flask-Migrate / Alembic）：

```bash
# 1. 修改 models.py 中的模型定义

# 2. 生成迁移脚本（自动对比模型与库差异）
flask db migrate -m "描述，如：add xxx field to companies"

# 3. 应用迁移
flask db upgrade

# 4. 检查生成的脚本（migrations/versions/ 下），必要时手工调整
```

**注意事项：**

- `app.py` 启动时的 `db.create_all()` 只建表**不迁移**，已有库必须走 `flask db upgrade`
- 历史迁移见 [数据库设计文档](database.md#迁移管理)
- 迁移脚本是版本化的，随代码一起提交

---

## 📐 代码规范

- Python 遵循 **PEP 8**，函数/类带 docstring（中文）
- 提交信息格式：`<类型>: <描述>`，中文描述，类型取 `feat / fix / docs / refactor / chore / test`
- **新增功能尽量补单元测试**（`tests/` 目录）
- 提交前检查：`python -m pytest tests/`

### 新增页面的最小步骤

1. 在 `models.py` 加模型（如需持久化）
2. 在 `routes/` 新建 `<name>.py`，定义 `bp = Blueprint(...)`
3. 在 `routes/__init__.py` 导入并加入 `ALL_BLUEPRINTS`
4. 在 `templates/` 建模板，可参考现有页面结构（`base.html` 提供布局与侧边栏）
5. 补测试 + 迁移（如涉及字段变更）

---

## 🗺️ 开发工作流（新增功能示例）

```mermaid
flowchart LR
    accTitle: Feature Development Workflow
    accDescr: From model change to migration, route, template, test, and verification

    m[✏️ 改 models.py] --> mig[flask db migrate + upgrade]
    mig --> r[📦 新建 routes/<name>.py]
    r --> reg[🔗 注册到 ALL_BLUEPRINTS]
    reg --> t[🎨 模板 templates/]
    t --> test[🧪 pytest 补测试]
    test --> run[🚀 本地验证]
    run --> commit[💾 提交]

    classDef step fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    class m,mig,r,reg,t,test,run,commit step
```

---

## 🐛 常见问题排查

### 启动时报 `No module named 'flask'`

**原因**：未激活 venv 或依赖未安装。

**修复**：

```bash
venv\Scripts\activate        # Windows
# 或
source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### DOCX 简历无法预览

**原因**：LibreOffice 未安装或不在默认路径（`C:\Program Files\LibreOffice\program\soffice.exe` 等）。

**修复**：安装 LibreOffice 后重启；或直接上传 PDF 版本。探测逻辑见 `routes/resume.py:15`。

### 修改了 models.py 但数据库没变

**原因**：`db.create_all()` 不迁移已有表。

**修复**：执行 `flask db migrate -m "..."` + `flask db upgrade`。

### 自动归档把记录归档了，想要关掉

**修复**：投递列表页的「归档设置」面板，关闭「自动归档」并保存（写入 `data/settings.json`，默认值来自 `JH_ARCHIVE_AUTO` 环境变量）。

### 评分脚本显示「未配置 profile」

**原因**：`data/profile.md` 不存在。

**修复**：上传简历后用 Profile Skill 自动生成，或参考 `prompts/profile.example.md` 手动创建。

---

## 🔗 相关文档

- [系统架构](architecture.md) — 模块依赖与设计决策
- [数据库设计](database.md) — 字段与迁移历史
- [路由/API 参考](api.md) — 端点清单
- [AI 评分引擎](ai-scoring.md) — 评分脚本用法
- [贡献指南](../CONTRIBUTING.md) — PR 流程与 Bug 报告模板

---

_最后更新：2026-07-31 · 维护者：JHTracker 项目组_
