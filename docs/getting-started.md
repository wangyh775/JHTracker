# 快速开始 / 入门指南

_JHTracker（Job Hunt Tracker）的 5 分钟极速上手指南：从环境准备、个人画像初始化，到 AI 智能体 (MCP) 对接与投递全流程管理。_

---

## 🚀 1. 环境准备与启动

### 前置要求
- Python ≥ 3.10
- 任意现代浏览器（Edge / Chrome / Safari / Firefox）

### 一键启动

- **Windows**：双击根目录 `start.bat`
- **macOS / Linux**：
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

### 手动安装与启动

```bash
git clone <repo-url>
cd career-tracker

# 1. 创建并激活虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 2. 安装基础依赖
pip install -r requirements.txt

# 3. 启动 Web 服务
python app.py
```

启动成功后，浏览器访问 `http://127.0.0.1:5000` 即可开启求职管理看板。

---

## 👤 2. 初始化求职画像 (`data/profile.md`)

求职画像是 AI 对公司做匹配度评分和智能检索的核心依据。

1. **自动生成（推荐）**：在 Web 界面「简历版本」上传 PDF/DOCX 简历，使用 **Profile Skill** 自动解析生成。
2. **手动创建**：复制示例文件模板：
   ```bash
   cp prompts/profile.example.md data/profile.md
   ```
   修改 `data/profile.md` 填入你的技术栈、目标岗位、目标城市与偏好。

---

## 🏢 3. 建立公司库

JHTracker 支持多种建立公司库的方式：

### 方式 A：智能体自动检索入库（最便捷）
对接入的 AI 智能体（Trae / Claude / Cursor / Hermes）直接说明需求：
> *"帮我寻找深圳和上海 5 家工业自动化领域的龙头企业"*

智能体会自动搜网、去重并写入数据库。

### 方式 B：Markdown 清单批量导入
1. 参考 `prompts/company_list_prompt.md` 提取 Markdown 清单。
2. 将表格文件放入 `career_data/` 目录。
3. 打开 Web 界面 `http://127.0.0.1:5000/import` 点击「执行导入」。

---

## 🤖 4. 对接 AI 智能体 (MCP 协议)

JHTracker 内置原生 **Model Context Protocol (MCP)** 服务，让智能体可以直接与你的本地求职记忆交互。

### 配置接入 (Hermes / Claude Desktop / Cursor)

在你的智能体 MCP 配置文件（如 `~/.hermes/mcp.json`）中添加：

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

配置完成后，Agent 即可自动调用：
- **读取画像与记忆**：`jhtracker://profile` 资源与 `get_user_preferences` 工具
- **检索公司**：`search_companies` 工具
- **自动建公司**：`create_company` 工具 (支持自动去重)
- **推送待投递**：`create_application` 工具 (生成待投递记录，支持匹配分、推荐理由与 Task ID)
- **回写评分**：`update_company_score` 工具

---

## 📊 5. 投递跟踪与 Agent 轨迹审查

- **投递跟踪**：在 `/applications` 页面记录投递状态（待投递 → 已投递 → 面试 → Offer），支持面试复盘与 Offer 对比。
- **Agent 轨迹**：访问 `http://127.0.0.1:5000/traces` 查看智能体在后台的操作事件、思考轨迹与实时推送。

---

## ⏰ 6. 定时任务推荐（配合 Hermes 使用）

部分脚本适合定时运行以保持数据新鲜，推荐使用 **Hermes** 的定时任务能力来触发：

| 脚本 | 用途 | 推荐频率 |
|---|---|---|
| `scripts/daily_new_company_finder.py` | 每日自动发现并入库新公司 | 每日一次 |
| `scripts/ai_scorer.py` | 为未评分的公司执行 AI 匹配评分 | 每日一次（或新公司入库后） |

在 Hermes 中配置定时任务，定时执行以下命令即可：

```bash
python scripts/daily_new_company_finder.py
python scripts/ai_scorer.py
```

> **提示**：确保在项目根目录和激活的虚拟环境中执行。AI 评分需要配置有效的 LLM API Key（见 `.env.example`）。

---

## 🔗 下一步阅读

- [系统架构文档](architecture.md) — 了解高并发 WAL 与 Blueprint 设计
- [数据库设计](database.md) — 查看 ORM 模型与表结构
- [API / MCP 参考](api.md) — 查看完整接口与 MCP 工具列表
