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

### 常用 MCP Tools 列表（36 个，覆盖 11 个数据域）

**👤 画像 & 偏好**
- `get_candidate_profile()`: 读取候选人 `data/profile.md` 简历画像。
- `update_candidate_profile(content)`: 更新候选人画像 Markdown 内容。
- `get_user_preferences()`: 获取偏好设置、负面记忆规则与拒绝反馈。
- `add_memory_rule(category, rule_value)`: 添加排除规则（如技术栈、公司）。
- `delete_memory_rule(memory_id, confirm)`: 删除记忆规则。

**🏢 公司**
- `search_companies(query)`: 按名称/行业模糊搜索公司。
- `get_company(company_id)`: 获取公司完整详情（含投递数、笔记数）。
- `create_company(...)`: 创建新公司并自动去重。
- `update_company(company_id, ...)`: 更新公司字段。
- `update_company_score(company_id, score, reason)`: 更新公司 AI 打分与评分理由。
- `delete_company(company_id, confirm)`: 删除公司（级联删除投递和笔记）。

**📮 投递**
- `create_application(...)`: 创建岗位投递记录，默认 `Pending Approval` 状态。
- `get_application(application_id)`: 获取投递详情（含公司名、简历名、面试反馈）。
- `list_applications(status, company_id, channel)`: 按条件筛选投递列表。
- `update_application_status(application_id, status)`: 更新投递状态。
- `get_pending_approvals()`: 获取待审批的推荐提案列表。
- `handle_decision(application_id, action, ...)`: 审批/拒绝/编辑待审批提案。
- `archive_application(application_id, archive)`: 归档/恢复投递记录。

**🎙️ 面试反馈**
- `create_interview_feedback(application_id, ...)`: 添加面试复盘记录。
- `list_interview_feedbacks(application_id)`: 查询某投递的面试反馈。

**📝 笔记**
- `create_note(company_id, title, content)`: 写笔记（可关联公司）。
- `list_notes(company_id)`: 查询公司笔记。
- `update_note(note_id, ...)`: 编辑笔记。
- `delete_note(note_id, confirm)`: 删除笔记。

**📅 时间线**
- `create_timeline_event(event_date, title, ...)`: 创建时间线节点。
- `list_timeline_events()`: 查询时间线事件。
- `toggle_timeline_event(event_id)`: 切换完成状态。

**📄 简历**
- `list_resumes()`: 查询简历版本列表。
- `get_default_resume()`: 获取当前默认简历。

**📊 统计**
- `get_statistics()`: 获取 Dashboard 核心指标（公司数、投递漏斗、Offer 数等）。

**🔍 评估**
- `evaluate_jd(jd_text, company_name, task_id)`: 评估 JD 文本，返回匹配分 + 亮点 + 风险提示。
- `batch_evaluate_jds(jds)`: 批量评估多个 JD，一次调用返回全部结果。

**🔄 轨迹 & 任务**
- `record_agent_trace(task_id, agent_name, ...)`: 记录或更新任务轨迹。
- `list_agent_tasks(status, limit)`: 查询任务列表。
- `get_agent_task(task_id)`: 查询任务详情 + 事件日志。
- `clear_agent_traces(confirm)`: 清空全部轨迹。

**🔔 系统**
- `notify_db_changed()`: 通知 UI 刷新（触发 SSE）。

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
| `skills/job-sourcing-and-scoring` | 自动化寻企、岗位挖掘、结合记忆 AI 打分 | `get_user_preferences`, `search_companies`, `get_company`, `create_company`, `update_company`, `update_company_score`, `evaluate_jd`, `batch_evaluate_jds`, `get_statistics` |
| `skills/application-tracker` | 岗位投递全生命周期、HITL 审核人机交互、Offer 跟踪 | `create_application`, `get_application`, `list_applications`, `update_application_status`, `get_pending_approvals`, `handle_decision`, `archive_application`, `create_interview_feedback`, `list_interview_feedbacks`, `get_user_preferences` |
| `skills/candidate-profile-and-resume` | 候选人简历解析、求职偏好与负面黑名单记忆 | `get_candidate_profile`, `update_candidate_profile`, `get_user_preferences`, `list_resumes`, `get_default_resume`, `add_memory_rule`, `delete_memory_rule` |
| `skills/tracker-ops` | 数据批量导入、去重、数据归档与系统运维 | `create_note`, `list_notes`, `update_note`, `delete_note`, `create_timeline_event`, `list_timeline_events`, `toggle_timeline_event`, `list_agent_tasks`, `get_agent_task`, `clear_agent_traces`, `notify_db_changed`, `get_statistics` |

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
[调用 mcp.create_application()] ──▶ 状态设为 'Pending Approval'，包含 match_score & agent_reason
       │
       ▼
[Web UI Decision Inbox (看板 /api/agent/decisions/pending)]
       │
  ┌────┴──────────────────────────┐
  ▼                               ▼
【批准 (Approve)】              【拒绝 (Reject)】
变更为 'Applied'               变更为 'Rejected'
记录 DecisionFeedback           记录 DecisionFeedback + Memory
       │                               │
       ▼                               ▼
[正常投递流程]              [反馈反哺到下次评估]
                                │
                                ▼
                      [evaluate_jd 查询 decision_feedbacks
                       与 memories，对相似模式扣分]
```

**闭环说明**：每次拒绝反馈通过 `DecisionFeedback` 和 `Memory` 表持久化。下次 Agent 调用 `evaluate_jd` 评估新岗位时，会自动查询历史拒绝记录，对匹配过去拒绝特征的岗位扣分并输出风险提示，实现 Agent 推荐偏好的持续校准。

---

## 5. FAQ 与常见问题

1. **Agent 是否需要一直挂着 MCP 服务器？**
   - 不需要。支持 MCP 的 Agent 客户端（如 OpenCode、VS Code）会在需要时根据 `.mcp.json` 自动启动 `mcp_server.py` 子进程。

2. **打分时如何避开我不喜欢的公司或技术栈？**
   - 当你在 Web UI 拒绝某项推荐时，拒接理由会被自动记入 `memories` 表。Skill 会在每次评估前先通过 `get_user_preferences()` 读取 `negative_rules` 并进行拦截。
