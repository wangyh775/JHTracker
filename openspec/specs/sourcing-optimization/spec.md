## Purpose

优化岗位检索技能的数据提取与抓取策略，实现对 Raw JD 文本的瘦身与结构化清洗，支持读取 profile.md 中的招聘类型偏好（校招/社招/不限），增加 2027 届校招与发布时间（2026 年 7 月之后）的硬拦截校验，并构建面向国内主流招聘平台的 4 阶降级与反爬避让矩阵。

## Requirements

### Requirement: Recruitment Type Preference Ingestion

The candidate profile (`data/profile.md`) and candidate profile skill SHALL support a `recruitment_type` preference field (`校招`, `社招`, or `不限`). If this field is absent or empty when sourcing jobs, the host agent SHALL prompt the user ("你选择寻找校招、社招还是不限？") and write the selection to `data/profile.md`.

#### Scenario: Agent reads profile with recruitment_type set to campus hiring
- **WHEN** the agent reads `data/profile.md` containing `recruitment_type: 校招`
- **THEN** the agent configures job sourcing filters to target campus recruiting roles and strictly enforces the graduation batch gate

#### Scenario: Agent reads profile with missing recruitment_type
- **WHEN** `recruitment_type` is absent in `data/profile.md`
- **THEN** the agent prompts the user for their preference and updates `data/profile.md` with the response

### Requirement: Structured Data Extraction and Token Compression SOP

The `job-sourcing-and-scoring` Skill SOP SHALL require host agents to compress and structure raw job description (JD) web payloads before calling evaluation or proposal tools. Extracted fields MUST include core technical stack requirements, nice-to-have qualifications, normalized salary range (`salary_min`, `salary_max` in k/month), location, recruitment type (`recruitment_type`), graduation target year (`target_graduation_year`), and posting date (`job_posted_date`), while stripping away company promotional copy, perk descriptions, and peripheral UI noise.

#### Scenario: Agent processes a noisy raw JD page
- **WHEN** the agent retrieves a raw JD web page containing 3000+ tokens of mixed content
- **THEN** the agent extracts only structured fields (`must_have_skills`, `nice_to_have`, `salary_min`, `salary_max`, `location`, `recruitment_type`, `target_graduation_year`, `job_posted_date`) into a compressed payload of 200-400 tokens before invoking `evaluate_jd`

#### Scenario: Agent parses salary strings in various Chinese formats
- **WHEN** the agent encounters salary formats like "20-35K·16薪", "25k-40k", or "40-70万/年"
- **THEN** the agent normalizes them into monthly minimum/maximum values in k (e.g. `salary_min: 20`, `salary_max: 35`)

### Requirement: Graduation Batch and Job Freshness Filtering Gate

The `job-sourcing-and-scoring` Skill SOP SHALL enforce an absolute verification gate during JD processing:
1. When `recruitment_type` is `校招` (or default): jobs MUST target the 2027 graduating class (or 2026.09 - 2027.08 graduation window) AND MUST be posted on or after July 1, 2026.
2. Any posting targeting earlier graduating classes, mismatched recruitment types, or posted prior to July 1, 2026 SHALL be immediately rejected as expired or non-matching, without calling application proposal tools.

#### Scenario: Agent encounters a posting for the 2026 graduating class or posted in May 2026
- **WHEN** `recruitment_type` is `校招` AND (the extracted `target_graduation_year` is 2026 or earlier OR `job_posted_date` is before 2026-07-01)
- **THEN** the agent rejects the candidate posting, marks it as `expired_or_batch_mismatch`, and skips creating any company or application proposal

#### Scenario: Agent encounters a fresh 2027 campus hiring posting from August 2026
- **WHEN** `recruitment_type` is `校招` AND the extracted posting is for the 2027 campus recruiting drive AND posted after 2026-07-01
- **THEN** the agent passes the freshness gate and proceeds to matching evaluation

### Requirement: Multi-Tiered Anti-Scrape Fallback Matrix

The `job-sourcing-and-scoring` Skill SOP SHALL establish a platform-specific 4-stage fallback matrix for BOSS直聘, 猎聘, and 国聘/官网. Stage 1 MUST use XHR/API JSON interception where available; Stage 2 MUST use Firecrawl with stealth/enhanced proxy; Stage 3 MUST fallback to search engine cache/snapshots (Exa/Tavily); Stage 4 MUST gracefully output a verifiable URL for human interaction without fabricating data.

#### Scenario: Agent encounters a CAPTCHA or slider lock on BOSS直聘
- **WHEN** Stage 1 and Stage 2 retrieval fail due to verification or CAPTCHA challenges
- **THEN** the agent falls back to Stage 3 search engine snapshots or Stage 4 graceful output, reporting the exact job URL to the user without hallucinating job details