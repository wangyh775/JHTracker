---
name: "job-sourcing-and-scoring"
description: "Fetches company/job info from the web, evaluates matching scores based on candidate profile and negative constraint rules (memories), and writes scores or recommendations back to JHTracker via MCP or REST API. Alias: company-finder, career-tracker-scorer."
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

This skill automates target company sourcing, job discovery, AI matching evaluation, and negative constraint memory filtering for JHTracker.

## Trigger Scenarios

Invoke when the user says any of:
- "帮我找XX行业的公司" / "搜索机器人公司" / "补充公司库" / "寻找符合偏好的岗位"
- "评估公司匹配度" / "给已有的公司打分" / "AI rating / score companies"
- "find companies in <industry>" / "score target companies"

## Workflow

### 0. Profile Ingestion & Platform Routing

1. Initialize a `task_id` (e.g. `sourcing-timestamp`) and call `JHTracker:record_agent_trace(task_id=task_id, agent_name="SourcingAgent", event_type="start", payload={"action": "init"})`.
2. Read `data/profile.md` and query `memories` table for negative rules.
3. **Read `enterprise_preference` from profile.md** (field: `enterprise_preference`). If absent or empty, ask the user: "你偏好央国企/外企/民企/不限？" and write the answer to profile.md.
4. **Route to target platforms** based on preference:

   | Preference | Primary Platform | Secondary | Fallback |
   |------------|-----------------|-----------|----------|
   | 央国企 | 国聘 (iguopin.com) | 国资委官网 | 央企官网招聘页 |
   | 外企 | 猎聘 (liepin.cn) | LinkedIn | 外企官网 Career 页 |
   | 民企 | BOSS直聘 (zhipin.com) | 拉勾 (lagou.com) | 智联招聘 (zhaopin.com) |
   | 不限 | BOSS直聘 | 国聘 | 猎聘 → 智联 → 官网 |

5. Log preference ingestion event via `JHTracker:record_agent_trace(task_id=task_id, event_type="preferences_loaded", payload={"enterprise_preference": "<value>", "target_platforms": [...]})`.

### 1. Layered Retrieval Protocol (检索-验证闭环)

**Authenticity Contract**: All company names, positions, URLs, and job descriptions MUST be sourced from real web search results. Fabrication or hallucination of data is STRICTLY PROHIBITED.

Execute the following layers in order. Stop at the first layer that returns results.

#### Layer 1: Firecrawl Scrape (Proxy Mode)
- Target: Primary/secondary platforms from Step 0 routing.
- Tool: `firecrawl-mcp-server_firecrawl_scrape` with `proxy=enhanced` or `proxy=stealth`.
- Action: Scrape job listing pages, extract company name, position, JD text, and source URL.
- Success criteria: Page content is non-empty, JS-rendered content is visible.

#### Layer 2: CDP Network Interception (Playwright)
- Target: SPA platforms where Firecrawl could not extract dynamic content (e.g., BOSS直聘 XHR-loaded listings).
- Tool: `Playwright_playwright_navigate` + `Playwright_playwright_evaluate` to intercept XHR/fetch responses.
- Action: Launch headless browser, navigate to search page, intercept network requests, extract structured JSON payloads containing position/company data.

#### Layer 3: Exa Web Search
- Target: General web discovery, company/career page search.
- Tool: `Exa_web_search_exa` with semantic queries (e.g., "company name 招聘 2026").
- Action: Search for company career pages, extract URLs and descriptions.

#### Layer 4: Tavily Search
- Target: Fallback when Exa returns no results.
- Tool: `tavily-mcp_tavily_search` + `tavily-mcp_tavily_extract`.
- Action: Web search for company/job information, extract page content.

#### Layer 5: Built-in Web Fetch
- Target: Ultimate fallback for any remaining candidate URLs.
- Tool: `webfetch`.
- Action: Simple HTTP fetch to verify URL accessibility and extract basic content.

#### Layer Failure Protocol
- If a layer returns no results → escalate to the next layer.
- **If ALL layers return no results**: DO NOT fabricate data. Report to the user:
  > "我在 [平台列表] 搜索了 [行业/关键词] 相关的岗位，但未找到真实匹配的结果。请提供更具体的关键词或目标公司名称，我可以重新搜索。"
  End the task. Do NOT create any company or application record.

### 2. Authenticity Verification Gate

Every candidate record MUST pass the following checks before being committed to the database.

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

### 3. Deduplication & Company Creation

1. Check existing database using `JHTracker:search_companies(query=name)`.
2. If not existing, call `JHTracker:create_company(...)` with:
   - `website`: Real company website URL (from verification).
   - `source_url`: Real job listing URL (from verification).
   - `industry`, `city`, `priority` based on verified data.
3. Log provenance in trace: `payload={"source_url": "...", "source_platform": "...", "discovery_tool": "...", "verification_status": "verified|single_source"}`.

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
2. Log completion trace via `JHTracker:record_agent_trace(task_id=task_id, status="completed", event_type="finish", payload={"created_applications": 1, "source_urls": [...]})`.
