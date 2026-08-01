## Purpose

Defines the layered retrieval protocol that governs how the AI Agent sources real company and job information from the web, ensuring authenticity, cross-platform verification, and user preference alignment.

## Requirements

### Requirement: Tool Chain Priority and Layering

The system SHALL define a strict priority-ordered tool chain for web retrieval, with fallback across layers.

#### Scenario: Agent follows tool priority for discovery
- **WHEN** an Agent begins sourcing companies or jobs
- **THEN** the system SHALL attempt tools in this order: Firecrawl scrape (with proxy=enhanced) → CDP network interception (Playwright/Firecrawl browser) → Exa web search → Tavily search → Agent built-in search (webfetch)

#### Scenario: Agent escalates to next layer on failure
- **WHEN** a tool at the current layer returns no results or fails to extract content
- **THEN** the Agent SHALL try the next layer in the priority chain

#### Scenario: All layers exhausted
- **WHEN** all tool layers have been attempted and no valid results are found
- **THEN** the Agent SHALL report the failure to the user and MUST NOT fabricate or hallucinate company names, URLs, or job descriptions

### Requirement: Platform Routing by Enterprise Preference

The system SHALL route retrieval to specific recruitment platforms based on the user's enterprise preference, sourced from either `data/profile.md` or runtime user input.

#### Scenario: Profile-based platform routing
- **WHEN** the user's `enterprise_preference` is set to `央国企`
- **THEN** the Agent SHALL prioritize 国聘 (iguopin.com), 国资委官网, and individual央企 career pages
- **WHEN** the user's `enterprise_preference` is set to `外企`
- **THEN** the Agent SHALL prioritize 猎聘 (liepin.cn), LinkedIn, and target foreign company career pages
- **WHEN** the user's `enterprise_preference` is set to `民企`
- **THEN** the Agent SHALL prioritize BOSS直聘 (zhipin.com), 拉勾 (lagou.com), and 智联招聘 (zhaopin.com)
- **WHEN** the user's `enterprise_preference` is set to `不限`
- **THEN** the Agent SHALL attempt BOSS直聘 first, then 国聘, then 猎聘, then 智联招聘, then company career pages

#### Scenario: Runtime preference override
- **WHEN** the user explicitly states a preference during a conversation (e.g., "帮我找外企岗位")
- **THEN** the Agent SHALL use the runtime preference for this session, overriding the profile value

### Requirement: Authenticity Verification Gate

The system SHALL implement a three-step verification gate that all discovered data must pass before being written to the database.

#### Scenario: URL accessibility check
- **WHEN** the Agent has extracted a candidate URL
- **THEN** the Agent SHALL verify the URL returns HTTP 200 and the page content is non-empty

#### Scenario: Content consistency check
- **WHEN** the Agent has extracted a company name and job description from a page
- **THEN** the Agent SHALL verify that the page title or visible header matches the expected company name
- **THEN** the Agent SHALL reject the result if the company name on the page does not match the search target

#### Scenario: Cross-source verification
- **WHEN** the Agent has candidate data from a single source
- **THEN** the Agent SHALL attempt to find the same company or job on at least one additional independent source
- **THEN** the Agent SHALL mark the data as `verified` when a second independent source confirms the listing
- **THEN** the Agent SHALL mark the data as `single_source` when no second source is found, and still allow writing with a provenance note

### Requirement: Source Provenance Trace

The system SHALL record the full retrieval provenance for every company and application created by the Agent.

#### Scenario: Provenance metadata recorded
- **WHEN** the Agent creates a company or application
- **THEN** the system SHALL record `source_url`, `source_platform`, `discovery_tool`, and `verification_status` in the associated trace log
- **THEN** the system SHALL include the timestamp of the retrieval and the tool chain used

### Requirement: Refusal Protocol for Insufficient Data

The Agent SHALL refuse to create records when it cannot verify authenticity, and SHALL communicate the reason to the user.

#### Scenario: Agent refuses to fabricate
- **WHEN** the Agent cannot find a real company or job matching the user's request after exhausting all layers
- **THEN** the Agent SHALL respond with a message explaining what was searched, which tools were used, and what was found (or not found)
- **THEN** the Agent SHALL NOT create any company or application record
- **THEN** the Agent SHALL suggest refined search terms or ask the user to provide specific company names

### Requirement: CDP Network Interception Layer

The system SHALL support Chrome DevTools Protocol (CDP) network interception as a dedicated retrieval layer for SPA-based recruitment platforms.

#### Scenario: Agent uses CDP to intercept API responses
- **WHEN** the Agent is targeting a platform that loads job data via XHR/fetch (e.g., BOSS直聘, 猎聘)
- **THEN** the Agent SHALL launch a headless browser session and intercept network requests to capture structured JSON responses
- **THEN** the Agent SHALL extract company names, positions, and URLs from the intercepted JSON payloads

### Requirement: Enterprise Preference Field in Profile

The system SHALL support an `enterprise_preference` field in `data/profile.md` that the Agent reads at startup.

#### Scenario: Profile field read by Agent
- **WHEN** the Agent begins a sourcing task
- **THEN** the Agent SHALL read the `enterprise_preference` field from `data/profile.md`
- **WHEN** the field is absent or empty
- **THEN** the Agent SHALL ask the user for their preference and write the answer to the profile for future sessions