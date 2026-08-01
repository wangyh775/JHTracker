## MODIFIED Requirements

### Requirement: MCP server provides tools for database operations
The MCP server MUST provide executable tools for searching companies, adding position applications, and updating evaluation scores. Tool docstrings SHALL clearly declare agent capability boundaries: `update_application_status` SHALL state that agents are prohibited from setting `POST_APPLY_STATUS_LIST` statuses. `get_pending_approvals` SHALL state that only `Pending Approval` and `待审批` records are returned (excluding `待投递`). `search_companies` and `get_company` SHALL document their return fields, LIMIT, and sort order.

#### Scenario: Agent invokes company search tool
- **WHEN** an AI agent calls tool `search_companies` with query argument `"AI"`
- **THEN** the MCP server MUST query the SQLite database and return matching company records, limited to 20 results, sorted by score DESC

#### Scenario: Agent attempts to set post-apply status via update tool
- **WHEN** an AI agent calls `update_application_status` to set a status in `POST_APPLY_STATUS_LIST` on a record already in `POST_APPLY_STATUS_LIST`
- **THEN** the MCP server MUST reject the request and return an error message indicating that active records are reserved for human edit only

#### Scenario: Agent reads pending approvals
- **WHEN** an AI agent calls `get_pending_approvals`
- **THEN** the MCP server MUST return only records with status `Pending Approval` or `待审批`, excluding records with status `待投递`

## ADDED Requirements

### Requirement: To-Apply Count in Statistics
The `get_statistics` tool SHALL include a `to_apply_count` field counting applications with `status = '待投递'`.

#### Scenario: Statistics includes to-apply count
- **WHEN** an AI agent or dashboard calls `get_statistics`
- **THEN** the returned JSON SHALL include `to_apply_count` representing the number of applications in `待投递` status