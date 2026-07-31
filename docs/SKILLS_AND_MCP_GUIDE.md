# JHTracker Skills & MCP Server 集成与使用指南

本指南详细介绍了如何为 **JHTracker (Career Tracker)** 配置 FastMCP 服务器 (`mcp_server.py`)、安装 Agent Skills 技能包，并结合 HITL (Human-in-the-Loop) 人机协同审核机制完成自动化求职管理。

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       AI Agent 平台 (OpenCode / Claude / Cursor / Trae) │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
┌───────────────────────┐                           ┌────────────────────┐
│ Agent Skills ( Prompt)│                           │ MCP Server         │
│ (skills/*)            │                           │ (mcp_server.py)    │
└───────────────────────┘                           └─────────┬──────────┘
                                                              │
                                                              ▼
                                                   ┌─────────────────────┐
                                                   │ SQLite Database     │
                                                   │ (data/tracker.db)   │
                                                   └─────────────────────┘
```

---

## 2. FastMCP 服务器配置 (`mcp_server.py`)

JHTracker 基于 FastMCP 提供了原生的 MCP 接口，供 AI Agent 实时读取候选人画像、搜索公司、创建岗位投递以及更新打分。

### 常用 MCP Tools 列表
- `get_candidate_profile()`: 读取候选人 `data/profile.md` 简历画像。
- `get_user_preferences()`: 获取偏好设置、负面记忆规则 (`negative_rules`) 与拒绝反馈。
- `search_companies(query)`: 按名称/行业模糊搜索目标公司。
- `create_company(...)`: 创建新公司并自动去重。
- `update_company_score(company_id, score, reason)`: 更新公司 AI 打分 (0-100) 与评分理由。
- `create_application(...)`: 创建岗位投递记录，支持挂载 `match_score`、`agent_reason` 并推送到 HITL 审核队列。

### 编辑器 / Agent MCP 配置文件 (`.mcp.json`)

在项目根目录或 Agent 客户端配置文件中接入 `mcp_server.py`：

```json
{
  "mcpServers": {
    "JHTracker": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "D:\\DJTU\\HermesWorkspace\\career-tracker"
    }
  }
}
```

---

## 3. 4 大核心 Skills 规范与安装

为了避免技能碎片化与智能体决策冲突，系统已将 Skills 整合为 4 个核心领域 Skill：

| Skill 目录 | 核心职责与场景 | 对应 MCP 工具 |
|---|---|---|
| `skills/job-sourcing-and-scoring` | 自动化寻企、岗位挖掘、结合记忆 AI 打分 | `get_user_preferences`, `search_companies`, `create_company`, `update_company_score` |
| `skills/application-tracker` | 岗位投递全生命周期、HITL 审核人机交互、Offer 跟踪 | `create_application`, `get_user_preferences` |
| `skills/candidate-profile-and-resume` | 候选人简历解析、求职偏好与负面黑名单记忆 | `get_candidate_profile`, `get_user_preferences` |
| `skills/tracker-ops` | 数据批量导入、去重、数据归档与系统运维 | Python 脚本与 SQL 运维 |

### Skill 安装/引入方法

#### OpenCode / Claude Code
项目根目录下的 `.opencode/skills/` 或本地环境 `skills/` 可直接识别。如需全局关联，可创建软链接或直接挂载目录。

#### Cursor / Trae / VS Code
在自定义 Prompt 或 Rules (如 `.cursorrules` / `.traerules`) 中添加引用：
```
Include skills definitions from skills/*/SKILL.md
```

---

## 4. 人机协同 (HITL) 推荐与审核全流程

```
[Agent 挖掘岗位]
       │
       ▼
[调用 mcp.create_application()] ──▶ 状态设为 '待投递' (Pending Review)，包含 match_score & agent_reason
       │
       ▼
[Web UI 审核队列 (/applications 或 /traces)]
       │
  ┌────┴──────────────────────────┐
  ▼                               ▼
【批准 (Approve)】              【拒绝 (Reject)】
变更为 'to_apply' (待投递)     变更为 'rejected'，反馈自动写入 'memories' 负面规则表
```

---

## 5. FAQ 与常见问题

1. **Agent 是否需要一直挂着 MCP 服务器？**
   - 不需要。支持 MCP 的 Agent 客户端（如 OpenCode、VS Code）会在需要时根据 `.mcp.json` 自动启动 `mcp_server.py` 子进程。

2. **打分时如何避开我不喜欢的公司或技术栈？**
   - 当你在 Web UI 拒绝某项推荐时，拒接理由会被自动记入 `memories` 表。Skill 会在每次评估前先通过 `get_user_preferences()` 读取 `negative_rules` 并进行拦截。
