---
name: "job-sourcing-and-scoring"
description: "Fetches company/job info from the web via layered retrieval (ATS direct → Firecrawl → Exa/Tavily → CDP → webfetch), evaluates matching scores based on candidate profile and negative constraint rules (memories), and writes scores or recommendations back to JHTracker via MCP or REST API. Alias: company-finder, career-tracker-scorer."
allowed-tools:
  - JHTracker:get_user_preferences
  - JHTracker:search_companies
  - JHTracker:get_company
  - JHTracker:create_company
  - JHTracker:update_company
  - JHTracker:update_company_score
  - JHTracker:create_application
  - JHTracker:evaluate_jd
  - JHTracker:batch_evaluate_jds
  - JHTracker:get_statistics
  - JHTracker:record_agent_trace
  - JHTracker:fetch_ats_jobs
  - Exa_web_search_exa
  - Exa_web_fetch_exa
  - tavily-mcp_tavily_search
  - tavily-mcp_tavily_extract
  - firecrawl-mcp-server_firecrawl_scrape
  - firecrawl-mcp-server_firecrawl_search
  - Playwright_playwright_navigate
  - Playwright_playwright_evaluate
  - webfetch
---

# Job Sourcing and Scoring Skill

This skill automates target company sourcing, job discovery, AI matching evaluation, and negative constraint memory filtering for JHTracker. Optimized for China domestic recruitment ecosystem (校招/社招 × 央国企/外企/民企).

## Trigger Scenarios

Invoke when the user says any of:
- "帮我找XX行业的公司" / "搜索机器人公司" / "补充公司库" / "寻找符合偏好的岗位"
- "评估公司匹配度" / "给已有的公司打分" / "AI rating / score companies"
- "find companies in <industry>" / "score target companies"

## Workflow

### 0. Profile Ingestion & Two-Dimensional Platform Routing

1. Initialize a `task_id` (e.g. `sourcing-timestamp`) and call `JHTracker:record_agent_trace(task_id=task_id, agent_name="SourcingAgent", event_type="start", payload={"action": "init"})`.
2. Read `data/profile.md` and query `memories` table for negative rules.
3. **Read two routing dimensions from profile.md**:
   - `enterprise_preference` ∈ {央国企, 外企, 民企, 不限} — if absent, ask user and write to profile.
   - `recruitment_type` ∈ {校招, 社招, 不限} — if absent, ask user "校招、社招还是不限？" and write to profile (defaults to `校招`).
4. **Route to target platforms** based on `enterprise_preference × recruitment_type`:

   | | 校招（网申） | 社招 |
   |---|---|---|
   | **央国企** | Layer 0: beisen + 国聘 / Layer 1: 国聘校招专区 | Layer 1: 国聘 / 猎聘 |
   | **外企** | Layer 0: moka / Layer 1: Workday/Greenhouse 官网 | Layer 1: 猎聘 / LinkedIn |
   | **民企大厂** | Layer 0: moka + beisen 并发 / Layer 1: 官网校招页 | Layer 1: BOSS/拉勾/智联 |
   | **民企创业** | Layer 0: moka + nowcoder / Layer 1: 牛客校招 | Layer 1: BOSS/拉勾 |
   | **不限** | Layer 0: all 并发 / Layer 1: 海投网+应届生 | Layer 1: BOSS → 国聘 → 猎聘 → 智联 |

5. Log preference ingestion event via `JHTracker:record_agent_trace(task_id=task_id, event_type="preferences_loaded", payload={"enterprise_preference": "<value>", "recruitment_type": "<value>", "target_platforms": [...]})`.

### 1. Platform-Specific 4-Stage Fallback Protocol (检索-验证闭环与反爬避让)

**Authenticity Contract**: All company names, positions, URLs, and job descriptions MUST be sourced from real web search results. Fabrication or hallucination of data is STRICTLY PROHIBITED.

Execute the following layers in order. **Layer 0 is mandatory for 校招 scenario** — do NOT skip to Layer 1 without attempting Layer 0 first.

#### Layer 0: 国内 ATS 直连（JHTracker:fetch_ats_jobs）— 校招最优先

- **Target**: 国内 ATS 平台公开 JSON 接口（北森/Moka/牛客/应届生），字段结构化、无需鉴权、反爬弱。
- **Tool**: `JHTracker:fetch_ats_jobs`.
- **Action**: 按 Step 0 路由表选择 provider，调用 `fetch_ats_jobs(provider=<...>, keyword=<...>, city=<...>, company_slug=<...>)`。
- **provider 选择规则**:
  - 校招 + 央国企 → `provider="beisen"`
  - 校招 + 外企/民企大厂 → `provider="moka"`（或 `provider="all"` 并发）
  - 校招 + 民企创业 → `provider="nowcoder"` 或 `provider="all"`
  - 社招场景 → **跳过 Layer 0**（ATS 直连对社招覆盖低），直接进 Layer 1
- **降级规则**:
  - Layer 0 返回 ≥3 条去重结果 → **停止检索**，进入 Step 2 验证门
  - Layer 0 返回 <3 条 → 进入 Layer 1 补充
  - Layer 0 返回 0 条 → 进入 Layer 1
- **form_type 透传**: fetch_ats_jobs 返回的每个岗位带 `form_type` 字段（structured/open_question/attachment/one_click），在 Step 5 调 `create_application` 时必须传入，供 application-executor 选择填写策略。

#### Layer 1: Firecrawl Scrape (Proxy Mode)

- **Target**: 国聘/猎聘/海投网/应届生列表页，或目标公司官网招聘页。
- **Tool**: `firecrawl-mcp-server_firecrawl_scrape` with `proxy=enhanced` or `proxy=stealth`.
- **Action**: Scrape job listing pages, extract company name, position, JD text, and source URL.
- **Success criteria**: Page content is non-empty, JS-rendered content is visible.
- **form_type 识别**: 从 `apply_url` 域名匹配 form_type 规则（beisen/mokahr/nowcoder → structured；workday/greenhouse/lever → attachment；zhipin → one_click；其他 → open_question）。

#### Layer 2: Exa + Tavily 通用搜索兜底

- **Target**: 通用 web 搜索，发现公司 Career 页与岗位描述。
- **Tool**: `Exa_web_search_exa`（语义搜索，优先）→ `tavily-mcp_tavily_search` + `tavily-mcp_tavily_extract`（兜底）。
- **Action**: 用语义查询（如 "company name 招聘 2026 校招"）搜索，提取 URL 与描述。

#### Layer 3: CDP Network Interception (Playwright) — 高风险兜底

- **Target**: BOSS直聘/智联招聘等 SPA 平台，前 3 层全空时才触发。
- **Tool**: `Playwright_playwright_navigate` + `Playwright_playwright_evaluate` to intercept XHR/fetch responses.
- **Action**: Launch headless browser, navigate to search page, intercept network requests:
  - BOSS直聘: 调内部 API `/wapi/zpgeek/search/joblist.json`，提取明文 `salaryDesc`（绕过字体反爬）
  - 智联: 调 `fe-api.zhaopin.com/c/i/search/positions`，需带正确 cookie/header
- **触发条件**: **仅当 Layer 0/1/2 全部无结果，或结果薪资字段全部为空时**才启动 CDP。避免高风险源被频繁调用。

#### Layer 4: Built-in Web Fetch — 终极兜底

- **Target**: 任何剩余候选 URL 的可达性验证。
- **Tool**: `webfetch`.
- **Action**: Simple HTTP fetch to verify URL accessibility and extract basic content.

#### Layer Failure Protocol
- If a layer returns no results → escalate to the next layer.
- **If ALL layers return no results**: DO NOT fabricate data. Report to the user:
  > "我在 [平台列表] 搜索了 [行业/关键词] 相关的岗位，但未找到真实匹配的结果。请提供更具体的关键词或目标公司名称，我可以重新搜索。"
  End the task. Do NOT create any company or application record.

### 2. Authenticity Verification Gate

Every candidate record MUST pass the following checks before being committed to the database. Layer 0 results are NOT exempt.

#### Step 2a: URL Accessibility Check
- Verify the source URL returns HTTP 200.
- Verify page content is non-empty and contains meaningful text.

#### Step 2b: Content Consistency Check
- Verify the page title or visible header matches the expected company name.
- Reject if the company name on the page does not match the search target.

#### Step 2c: Cross-Source Verification
- Attempt to find the same company/job on at least one additional independent source.
- If a second independent source confirms → mark as `verified`.
- If no second source found → mark as `single_source` (still allowed, with provenance note).
- **Layer 0 豁免**: 若 Layer 0 返回的 `source_platform` 为已知 ATS（beisen/moka/nowcoder/yingjiesheng），视为可信源，可标记 `verified` 无需交叉验证。

#### Step 2d: JD Structured Data Extraction & Token Compression SOP

Before calling evaluation tools or saving JDs, host agents MUST compress and structure the raw webpage content (typically 3000+ tokens) into a compact JSON payload (200-400 tokens), stripping away company promotional copy, perk lists, and peripheral UI text.

**Extracted JSON Fields**:
```json
{
  "must_have_skills": ["STM32H7", "C++", "MPC算法"],
  "nice_to_have": ["3D打印", "Klipper"],
  "salary_min": 20,
  "salary_max": 35,
  "location": "深圳",
  "recruitment_type": "校招",
  "target_graduation_year": 2027,
  "job_posted_date": "2026-07-15"
}
```

**Salary Normalization Table**:

| Raw Salary String | Normalized `salary_min` (k/mo) | Normalized `salary_max` (k/mo) | Notes |
|-------------------|--------------------------------|--------------------------------|-------|
| `"20-35K·16薪"` | `20` | `35` | Standard monthly range |
| `"25k-40k"` | `25` | `40` | Lowercase k handling |
| `"40-70万/年"` | `33` | `58` | Converted (divide by 12, round) |
| `"150-250元/天"` | `3` | `5` | Internship daily rate (22 days) |

#### Step 2e: Graduation Batch & Job Freshness Hard Gate

Host agents MUST check the extracted `recruitment_type`, `target_graduation_year`, and `job_posted_date` against candidate profile rules BEFORE calling `evaluate_jd`:

1. **Recruitment Type Rule**:
   - If `recruitment_type` in `data/profile.md` is `校招` (default): Candidate MUST be a 2027 graduate. The posting MUST target the **2027 graduating class** (or graduation window 2026.09 - 2027.08).
   - If `recruitment_type` is `社招`: Skip graduation year gate, but verify required experience matches candidate status.
2. **Job Freshness Rule**:
   - Job posting date (`job_posted_date`) MUST be **on or after 2026-07-01**.
   - Any job posted prior to 2026-07-01 (e.g. old 2025/2026 spring postings) MUST be immediately rejected as EXPIRED.

**Keyword Inspection Checklist**:

| Field | Passing Keywords (`ALLOW`) | Blocking Keywords (`REJECT`) |
|-------|----------------------------|------------------------------|
| **Graduation Batch** (when `recruitment_type: 校招`) | `2027届`, `2027年毕业`, `2027校招`, `2027应届` | `2026届`, `2025届`, `社招`, `3年以上经验`, `往届生` |
| **Posting Date** | Posted on/after `2026-07-01`, `2027秋招` | Posted before `2026-07-01`, `2025年`, `2026春招` |

**Rejection Protocol**:
If a job fails Step 2e, DO NOT call `evaluate_jd` or `create_application`. Log rejection in trace:
`payload={"skipped": true, "reason": "expired_or_batch_mismatch", "posting_date": "...", "target_batch": "..."}`.

### 3. Deduplication & Company Creation

1. Check existing database using `JHTracker:search_companies(query=name)`.
2. If not existing, call `JHTracker:create_company(...)` with:
   - `website`: Real company website URL (from verification).
   - `source_url`: Real job listing URL (from verification).
   - `industry`, `city`, `priority` based on verified data.
3. Log provenance in trace: `payload={"source_url": "...", "source_platform": "...", "discovery_tool": "...", "verification_status": "verified|single_source"}`.

### 3a. Application Deduplication Check (全量查重与跳过)

**IMPORTANT: Before calling `create_application`, you MUST pass this deduplication gate.**

**去重核心规则**：
1. **多岗位允许**：同一个公司可以录入多个不同的岗位（例如：公司 A + 嵌入式软件开发工程师、公司 A + 控制算法工程师 均可正常录入）。
2. **同公司同岗位唯一性（绝对去重）**：严禁出现同一个公司、同一个岗位的重复记录（无论该岗位处于 `已投递`、`待投递`、`Pending Approval`、`流程中` 还是已归档状态）。

**查重执行步骤**：
1. 若搜寻到某岗位，首先通过 `JHTracker:search_companies(query=name)` 获取目标公司的 `company_id`。
2. 检索并核对该公司在库内已有的全部岗位记录。若发现库中已经存在相同（或标准化后完全一致）的岗位名称：
   - **立即跳过（SKIP）** 该岗位，严禁调用 `JHTracker:create_application`。
   - 在 trace 中记录跳过事件：`payload={"skipped": true, "reason": "duplicate_position", "company": "<name>", "position": "<position>"}`。
3. 若库中无该公司的同名岗位（即使已有其他不同岗位），则判定为新岗位，继续进入 Step 4（AI 匹配度评估）及 Step 5（推送待审批）。

### 4. AI Matching Evaluation (0 - 100)

Score companies/jobs based on alignment with candidate skills, city, salary expectations, and negative rules:
- **0 - 59**: Violates negative rules or poor tech stack fit.
- **60 - 79**: Moderate match, keep in company DB.
- **80 - 100**: High match, candidate should consider applying.

Update company score using `JHTracker:update_company_score(company_id, score, reason)`.

### 5. Push High Match Jobs to HITL Queue & Complete Trace

For jobs/companies with score ≥ 75:
1. Call `JHTracker:create_application(...)` with:
   - `status` = `'Pending Approval'` (system forces this value).
   - `source_url` = verifiable real job listing URL (required).
   - `match_score`, `agent_reason`, `agent_task_id=task_id`.
   - `form_type` = from Layer 0 return value, or identified in Layer 1-4 by apply_url domain rules. **Must pass this field** so application-executor knows how to prefill.
   - `source_platform` = from Layer 0 return value (beisen/moka/nowcoder/yingjiesheng), or identified in Layer 1-4 (zhipin/lagou/zhaopin/iguopin/liepin/official).
2. Log completion trace via `JHTracker:record_agent_trace(task_id=task_id, status="completed", event_type="finish", payload={"created_applications": 1, "source_urls": [...], "form_types": [...], "source_platforms": [...]})`.

## form_type 识别规则速查

供 Layer 1-4 手动识别 form_type 时使用（Layer 0 自动返回，无需手动识别）：

| form_type | 域名特征 | 网申填写策略（application-executor 消费） |
|---|---|---|
| `structured` | beisen.com, yingjiesheng.com, mokahr.com, nowcoder.com | AnswerBank 直接取值 |
| `attachment` | workday.com, greenhouse.io, lever.co | 跳过表单，走简历生成 |
| `one_click` | zhipin.com | 不需要 prefill |
| `open_question` | 未命中规则的默认值 | AnswerBank + LLM 生成（最保守，走 awaiting_human） |
