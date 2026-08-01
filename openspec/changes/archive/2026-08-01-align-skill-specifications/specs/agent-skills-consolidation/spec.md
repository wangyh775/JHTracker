## MODIFIED Requirements

### Requirement: FastMCP Tool and HITL Review Support in Skills
The consolidated skills SHALL explicitly define FastMCP tool mappings and support pushing jobs to `Pending Approval` (pre-apply staged) status for Human-in-the-Loop (HITL) approval. The `application-tracker` skill SHALL declare that agents are prohibited from modifying records in `POST_APPLY_STATUS_LIST` (已投递 and beyond). The `candidate-profile-and-resume` skill SHALL support reading and writing the `enterprise_preference` field in `data/profile.md`.

#### Scenario: Agent pushes candidate application via skill
- **WHEN** an AI agent discovers a job matching candidate profile score >= 75
- **THEN** it calls the MCP tool `create_application` setting initial status to `Pending Approval` (system forces this value) and including match metadata (`match_score`, `agent_reason`, `source_url`).

#### Scenario: Agent prohibited from mutating post-apply records
- **WHEN** an AI agent attempts to update an application whose status is in `POST_APPLY_STATUS_LIST` (已投递, 简历筛选, 笔试, 面试, Offer, 已拒)
- **THEN** the system SHALL reject the request and return an error indicating that active application records are reserved for human edit only.

#### Scenario: Agent reads enterprise preference from profile
- **WHEN** an AI agent begins a sourcing task and reads `data/profile.md`
- **THEN** it SHALL parse the `enterprise_preference` field (央国企/外企/民企/不限) and use it to route retrieval to the appropriate recruitment platforms.

#### Scenario: Agent updates enterprise preference from resume
- **WHEN** a candidate uploads a new resume and the parsing detects an enterprise type preference
- **THEN** the agent SHALL update the `enterprise_preference` field in `data/profile.md` to reflect the extracted preference.