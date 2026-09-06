# AI 智能体与 FastMCP 开放接入指南 (MCP Agent Guide) 🤖🔌

JHTracker 全面遵循 Anthropic 提出的 **Model Context Protocol (MCP)** 标准，内置了基于 FastMCP 的高性能本地服务（`backend/src/mcp_server.py`）。

通过 MCP 协议，外部现代 AI 智能体（如 Claude Desktop、OpenCode、Cursor、Cline 等）能够以结构化、高安全、带审计的方式协同求职者开展岗位全景检索、人在环路推荐打分、智能体协同直推、外网职位安全采入、关键词矩阵动态补齐与专岗 ATS 简历优化。

---

## 1. 智能体交互架构与数据流图

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 用户
    participant Agent as 🤖 AI 智能体 (Claude / OpenCode / Cursor)
    participant MCP as 🛡️ FastMCP Server (backend/src/mcp_server.py)
    participant PubDB as 🌐 公共岗位库 (data/public_jobs.db)
    participant PrivDB as 🔒 私有敏感库 (~/.JHTracker/user_data.db)

    User->>Agent: "帮我找找上海要求 Python 的岗位，按我的简历推荐最匹配的并做专岗润色"
    Agent->>MCP: 1. 调用 resume_get_profile()
    MCP->>PrivDB: 只读读取默认活跃简历的技能标签与摘要
    MCP-->>Agent: 返回技能清单: ["Python", "FastAPI", "Docker", "PostgreSQL"]

    Agent->>MCP: 2. 调用 job_search(query="Python", city="上海", limit=5)
    MCP->>PubDB: FTS5 全文索引检索
    MCP-->>Agent: 返回匹配的 5 个岗位列表

    Agent->>MCP: 3. 调用 job_recommend(limit=3)
    MCP->>PubDB: 结合用户画像与 HITL 偏好权重矩阵执行双路召回
    MCP-->>Agent: 返回契合度评分最高的前 3 个岗位及匹配理由

    Agent->>MCP: 4. 调用 job_get_detail(job_id="fangzhou_abc123")
    MCP->>PubDB: 获取完整 JD、任职要求及官网申请链接
    MCP-->>Agent: 返回完整岗位元数据

    Agent->>MCP: 5. 调用 job_agent_push(job_id="fangzhou_abc123", recommend_reason="技术栈契合且秋招提前批")
    MCP->>PrivDB: 录入未决智能体推送队列，前置检查同集团企业上限
    MCP-->>Agent: 推送成功，前台看板可见高亮推荐卡片

    Agent->>MCP: 6. 调用 resume_optimize(job_id="fangzhou_abc123", save_as_version=True)
    MCP->>PrivDB: 针对该 JD 进行 ATS 诊断，并保存为独立的 [AI定制优化] 新版本
    MCP-->>Agent: 返回 ATS 得分、STAR 改写建议与新生成的独立版本 ID

    Agent-->>User: 结构化输出推荐岗位详情、官网投递直达链接，并告知优化版简历已独立入库存证！
```

---

## 2. 智能体开放设计哲学与权限红线 (Security Boundary)

智能体是求职者的**参谋中枢与信息助手**，绝非主观决策的替代者。JHTracker 底层设立了严格的权限隔离与安全红线：

```mermaid
graph TD
    subgraph AllowedZone ["🟢 允许智能体调用的 10 大安全工具能力"]
        A1["岗位全景检索与详情下钻 (job_search / job_get_detail)"]
        A2["人在环路双路召回推荐 (job_recommend)"]
        A3["求职意向正负反馈自学习 (job_feedback)"]
        A4["智能体定向合规直推 (job_agent_push)"]
        A5["外部新岗位安全去重采入 (job_add_external)"]
        A6["定向爬虫增量同步触发 (job_sync_run)"]
        A7["只读简历画像与技能清单查询 (resume_get_profile)"]
        A8["独立版本 ATS 专岗定制优化 (resume_optimize)"]
        A9["简历关键词矩阵增量更新 (resume_update_keywords_matrix)"]
    end

    subgraph ForbiddenZone ["🔴 严苛禁止越权的红线操作"]
        F1["🚫 严禁推进/篡改投递看板阶段 (无 application_update_status 接口)"]
        F2["🚫 严禁覆写/覆盖用户原始简历 (原始主版本只读保护)"]
        F3["🚫 严禁删除或清空看板投递记录 (用户主权独占)"]
        F4["🚫 严禁注入未经校验的恶意字符 (SAFE_IDENTIFIER_PATTERN 防护)"]
    end
```

- **决策主权在人**：投递看板阶段流转（投递/笔试/面试/Offer）是高度严肃的人生决策，**智能体无权直接流转看板状态**。
- **智能体推送频控机制**：调用 `job_agent_push` 时严格受到安全门禁约束：
  - **已投递企业绝对排除**：若用户已向某公司投递过任何岗位，智能体严禁向该企业继续盲目推荐。
  - **未决上限阈值防护**：同一公司在看板与推荐队列中最多挂载 **3 个** 未决岗位，防范单一公司职位霸屏与投递资源挤兑。
- **基准简历只读保护**：用户的原始主简历具有只读属性，AI 优化结果仅作为带有 `version_type = "AI_OPTIMIZED"` 的独立版本持久化，绝不污染原始底本。
- **参数强校验**：所有标识符与文本均受到 `SAFE_IDENTIFIER_PATTERN = r"^[a-zA-Z0-9_\-一-龥]{1,128}$"` 正则安全约束，支持中文后缀并杜绝 SQL 注入与路径穿越。

---

## 3. 完整 FastMCP 10 大工具链规格参考 (Tools Pool)

| 编号 | 工具名称 | 输入参数 | 功能说明与约束 | 返回结果规范 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `job_search` | `query: str`<br>`city: Optional[str]`<br>`limit: int = 10` | 基于 FTS5 引擎全文模糊检索公共岗位库，自动过滤空值。 | 包含 `total` 命中数与 `jobs` 简要元数据列表。 |
| 2 | `job_recommend` | `resume_id: Optional[str]`<br>`limit: int = 5` | 基于用户简历技能余弦度与 HITL 特征权重计算契合度最高的岗位。 | 推荐列表（包含 `score` 匹配分值与 `match_reason` 解释）。 |
| 3 | `job_feedback` | `job_id: str`<br>`action: str`<br>`reason: Optional[str]` | 提交对岗位的感兴趣 (`ACCEPT`) 或跳过 (`REJECT`) 决策，驱动权重自学习与自动建单。 | 操作状态与反馈持久化确认结果。 |
| 4 | `job_agent_push` | `job_id: str`<br>`recommend_reason: str`<br>`match_score: float = 0.95`<br>`agent_name: str = "JobSourcingAgent"` | 智能体直接向用户界面推送高价值职位，内置已投递拦截与同公司上限限制。 | 包含 `push_id` 与推送确认状态字典。 |
| 5 | `job_get_detail` | `job_id: str` | 依据职位唯一 ID，提取完整职责、任职要求与官方网申直达链接。 | 完整职位字典对象（包含 `url`、`description` 等）。 |
| 6 | `job_add_external`| `company: str`<br>`title: str`<br>`url: str`<br>`location: Optional[str]`<br>`description: Optional[str]`<br>`requirements: Optional[str]`<br>`salary_range: Optional[str]`<br>`skills: Optional[List[str]]`<br>`job_type: str = "CAMPUS"` | 将外部招聘渠道、社交媒体发现的新岗位去重录入公共库（MD5 安全哈希）。 | 录入状态、生成哈希 ID 与是否为新增条目。 |
| 7 | `job_sync_run` | `spider_name: str = "qiuzhifangzhou"`<br>`limit: int = 50` | 触发运行指定的定向招聘网站爬虫（支持 `qiuzhifangzhou`, `wondercv`, `nowcoder`）。 | 爬虫采集统计数据与增量抓取报告。 |
| 8 | `resume_get_profile`| `resume_id: Optional[str] = None` | 只读提取指定简历或默认活跃简历的技能词云与摘要画像。 | 包含 `resume_id`、`title` 与 `skills` 标签列表。 |
| 9 | `resume_optimize` | `job_id: Optional[str] = None`<br>`resume_id: Optional[str] = None`<br>`save_as_version: bool = True` | 诊断简历与目标 JD 的差距，按 STAR 原则生成建议并可选独立存为新版本。 | 包含 `ats_score`、`suggestions`、优化内容与新生成的 `version_id`。 |
| 10 | `resume_update_keywords_matrix` | `resume_id: str`<br>`keywords_to_add: List[str]`<br>`category_tag: Optional[str] = None` | 增量更新简历的技能关键词矩阵并触发权重池扩展，支持行业专岗演进。 | 更新状态与合并后的完整 skills 列表。 |

---

## 4. 常见主流 AI 客户端接入配置

### 4.1 OpenCode 配置接入

在项目根目录或全局的 `opencode.json`（或 `~/.config/opencode/opencode.json`）中添加 MCP Server 配置：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "jhtracker": {
        "command": "python",
        "args": [
          "<PROJECT_ROOT>/backend/src/mcp_server.py"
        ],
        "env": {
          "PYTHONPATH": "<PROJECT_ROOT>/backend"
        }
      }
    }
  }
}
```

### 4.2 Claude Desktop 配置接入

编辑 Claude Desktop 配置文件：
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jhtracker": {
      "command": "python",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "<PROJECT_ROOT>/backend",
      "env": {
        "PYTHONPATH": "<PROJECT_ROOT>/backend"
      }
    }
  }
}
```

### 4.3 Cursor / Windsurf / Cline 配置接入

在 Cursor 设置页面的 `Features -> MCP Servers` 中点击 **Add New MCP Server**：
- **Name**: `JHTracker`
- **Type**: `command`
- **Command**: `python path/to/JHTracker/backend/src/mcp_server.py`

---

## 5. 典型应用场景实战范例

### 场景一：自然语言复合查岗与简历速配

**用户提问**：
> “请查看我的简历，找出库里最匹配的 3 个自动驾驶或者大模型岗位，给出投递链接和匹配理由。”

**智能体自动化调用链路**：
1. 智能体调用 `resume_get_profile()` 获取当前简历画像。
2. 智能体调用 `job_recommend(limit=3)` 计算并返回得分最高的 3 个岗位。
3. 智能体针对最高分岗位调用 `job_get_detail(job_id=...)` 提取其职责与官网投递入口。
4. 智能体向用户结构化呈现分析，并附上直达链接。

### 场景二：针对特定心仪岗位的专岗版本定制与矩阵同步

**用户提问**：
> “我对 ID 为 `fangzhou_550e8400` 的大厂核心平台岗非常感兴趣，请帮我做一份专岗定制简历，并把缺失的关键技能同步到技能库中！”

**智能体自动化调用链路**：
1. 智能体调用 `job_get_detail(job_id="fangzhou_550e8400")` 深入了解高频考点。
2. 智能体调用 `resume_optimize(job_id="fangzhou_550e8400", save_as_version=True)` 触发 ATS 评分与 STAR 强化。
3. 智能体调用 `resume_update_keywords_matrix(resume_id=..., keywords_to_add=["K8s Operators", "gRPC"])` 动态拓展技能图谱。
4. 后端服务自动在 `~/.JHTracker/user_data.db` 中创建带有 `AI_OPTIMIZED` 标签的新简历。
5. 智能体向用户汇报：“已生成针对该岗位的独立定制版本（ID: `res_ai_xxx`），重点量化了分布式缓存与高并发 QPS 指标；原简历保持安全无损，新技能矩阵已同步，可随时在 Web 端审阅预览！”

### 场景三：外部寻源智能体主动发现与受控直推

**寻源 Agent 自动化工作流**：
1. Agent 外部抓取到某独角兽新发出的高匹配校招岗位，调用 `job_add_external(...)` 录入公共库。
2. Agent 评估该职位与用户技术栈高度契合，准备推送前调用 `job_agent_push(job_id=...)`。
3. JHTracker 底层安全拦截层核验该企业不在用户“已投递黑名单”内，且未决直推数未超标（$\le 3$），成功存入推荐流。
4. 求职者打开 Web 页面即可看到醒目的“AI 直推卡片”并决定是否一键申报。
