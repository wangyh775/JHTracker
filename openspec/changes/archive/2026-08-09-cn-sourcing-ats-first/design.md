# Design: cn-sourcing-ats-first

## 架构决策：MCP 工具下沉 + Skill 编排的混合路径

### 决策背景

用户问"应该走什么技术路径，mcp+skill 吗"。核心权衡是：哪些逻辑下沉为 MCP 工具（代码实现、可单测、稳定），哪些保留在 Skill 编排（Markdown 指令、灵活、易改）。

### 分层原则

按**数据源稳定性**分层，而不是按"功能"分层：

| 数据源类型 | 稳定性 | 技术路径 | 理由 |
|---|---|---|---|
| 北森/Moka/牛客/应届生 ATS 公开接口 | 高（接口稳定多年） | **下沉为 MCP 工具** | 接口稳定，下沉后可单测、可缓存、可批量；锁死在代码里反而省心 |
| BOSS/智联/拉勾 CDP 爬虫 | 低（反爬常变） | **保留外部 MCP + skill 编排** | 反爬变化时只改 skill 指令，不动代码、不发版 |
| Firecrawl/Exa/Tavily 通用搜索 | 中 | **保留 skill 编排作兜底** | 灵活性优先，由 agent 现场决策 |

### 为什么不全部下沉

BOSS直聘的字体反爬、智联的 cookie 校验、拉勾的登录态，这些反爬机制每隔几个月就会变。如果下沉到 `services/sourcing/` 代码里，每次反爬变化都要改代码、跑测试、发版。保留在 skill 里，改几行 Markdown 指令即可。

### 为什么不全部 skill 编排

北森、Moka 这种公开接口，字段结构固定、无需鉴权、反爬弱。每次让 agent 现场决策"用哪个工具、怎么解析 JSON、怎么去重"，token 消耗大、结果不稳定。下沉为 `fetch_ats_jobs` MCP 工具后，agent 一句话就能拿到结构化数据。

## 组件设计

### 1. `services/sourcing/ats_fetcher.py`（新增）

封装 4 个国内 ATS 公开接口，对外暴露统一函数 `fetch_ats_jobs()`。

#### 接口适配器模式

```
ats_fetcher.py
├── _fetch_beisen(company_slug, keyword, city, page) → list[Job]
├── _fetch_moka(company_slug, keyword, city, page) → list[Job]
├── _fetch_nowcoder(keyword, city, page) → list[Job]
├── _fetch_yingjiesheng(keyword, city, page) → list[Job]
└── fetch_ats_jobs(provider, keyword, city, page) → list[Job]  # 统一入口
```

#### 标准化 Job 结构

```python
@dataclass
class AtsJob:
    title: str
    company: str
    location: str
    salary: Optional[str]
    apply_url: str
    form_type: str  # structured | open_question | attachment | one_click
    source_platform: str  # beisen | moka | nowcoder | yingjiesheng
    raw: dict  # 原始响应，用于调试
```

#### form_type 识别规则

通过 `apply_url` 域名匹配，不走 LLM：

```python
FORM_TYPE_RULES = [
    (r'beisen\.com|yingjiesheng\.com', 'structured'),
    (r'mokahr\.com', 'structured'),
    (r'nowcoder\.com', 'structured'),
    (r'workday\.com', 'attachment'),
    (r'greenhouse\.io|lever\.co', 'attachment'),
    (r'zhipin\.com', 'one_click'),
    # 默认: open_question（快消/咨询/银行校招）
]
```

#### 各 ATS 接口要点

**北森（Beisen）**：
- 域名特征：`*.beisen.com`、`yingjiesheng.com`（应届生求职网底层用北森）
- 接口：`https://m.beisen.com/Api/JobSearch/SearchV2`（POST）
- 鉴权：无需，但需要正确的 `AppId` header（可从任意北森招聘页抓取，公开值）
- 字段：`JobName`, `CompanyName`, `WorkPlaceName`, `SalaryStr`, `Url`

**Moka**：
- 域名特征：`app.mokahr.com`
- 接口：`https://app.mokahr.com/api/apply/spa/positions/search`（POST）
- 鉴权：无需，需要 `orgId`（从 URL `app.mokahr.com/apply/{orgId}` 提取）
- 字段：`title`, `department`, `workLocation`, `salaryMin/salaryMax`, `externalUrl`

**牛客网**：
- 域名特征：`nowcoder.com`
- 接口：`https://www.nowcoder.com/np/api/job/schooljobs/list`（GET）
- 鉴权：无需
- 字段：`title`, `companyName`, `city`, `salary`, `jumpUrl`

**应届生求职网**：
- 域名特征：`yingjiesheng.com`
- 接口：底层走北森，复用 `_fetch_beisen`，或直接抓列表页 HTML（结构稳定）
- 字段：从 HTML 解析（标题/公司/城市/网申链接）

### 2. MCP 工具 `fetch_ats_jobs`（新增，注册到 mcp_server.py）

```python
@mcp.tool()
def fetch_ats_jobs(
    provider: str,          # beisen | moka | nowcoder | yingjiesheng | all
    keyword: str,           # 岗位关键词
    city: Optional[str] = None,
    company_slug: Optional[str] = None,  # Moka/北森需要
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    从国内 ATS 平台直连获取岗位列表。
    provider=all 时并发查询所有平台并合并去重。
    返回 {jobs: [...], total, provider, form_type_hint}
    """
```

### 3. layered-retrieval-protocol spec 升级

#### 新 Layer 顺序

```
Layer 0: 国内 ATS 直连（JHTracker:fetch_ats_jobs）  ← 新增，最优先
  ├─ 校招场景: beisen + moka + nowcoder + yingjiesheng
  └─ 社招场景: moka + workday（外企）

Layer 1: 平台结构化爬虫（Firecrawl）              ← 原 Layer 1
  ├─ 国聘/猎聘列表页
  └─ 海投网/应届生校招聚合

Layer 2: 通用搜索兜底（Exa + Tavily）              ← 原 Layer 3/4 合并

Layer 3: CDP 高风险源（Playwright）                ← 原 Layer 2 降级
  ├─ BOSS直聘 CDP（明文薪资 API）
  └─ 智联内部接口

Layer 4: webfetch 终极兜底                         ← 原 Layer 5
```

#### 降级规则

- Layer 0 命中 ≥3 条结果 → 停止，不进入 Layer 1
- Layer 0 命中 <3 条 → 进入 Layer 1 补充
- Layer 1 命中 → 停止
- 依次类推，CDP 只在前 3 层全空时才触发

### 4. 平台路由二维化

`enterprise_preference × scenario` 二维路由表。`scenario` 从 profile.md 的新字段 `job_scenario` 读取（校招/社招/实习），缺失时从用户对话推断或询问。

### 5. form_type 传递链路

```
fetch_ats_jobs → 返回 form_type
     ↓
skill 调 create_application → 写入 application.form_type 字段
     ↓
application-executor prefill_dry_run → 读 form_type 选择填写策略
```

需要在 `applications` 表加 `form_type` 字段（migration）。

## 数据模型变更

### `applications` 表新增字段

```sql
ALTER TABLE applications ADD COLUMN form_type TEXT;  -- structured | open_question | attachment | one_click
ALTER TABLE applications ADD COLUMN source_platform TEXT;  -- beisen | moka | nowcoder | yingjiesheng | zhipin | ...
```

`source_platform` 用于追溯岗位来源，`form_type` 用于驱动 application-executor。

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| ATS 接口变更导致 fetch_ats_jobs 失败 | 每个适配器独立 try/except，单家失败不阻塞其他；skill 层有 Layer 1-4 兜底 |
| 北森 AppId 被封 | AppId 是公开值，可从任意北森页面抓取；缓存策略避免频繁请求 |
| form_type 误判 | 域名规则保守匹配，未命中默认 `open_question`（最安全，会走 awaiting_human） |
| Moka orgId 提取失败 | company_slug 参数必填时校验，缺失返回空列表而非报错 |

## 测试策略

- `tests/test_ats_fetcher.py`：mock 各 ATS 接口响应，验证字段映射与 form_type 识别
- `tests/test_sourcing_skill.py`：验证 Layer 0 降级逻辑、二维路由表
- 复用 `tests/conftest.py` 的 in-memory SQLite fixture
