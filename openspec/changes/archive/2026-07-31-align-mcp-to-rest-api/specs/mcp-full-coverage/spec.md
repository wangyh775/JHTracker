## Purpose

Extends the MCP Server tool set from 9 to 36 tools, covering all 11 data domains so that AI agents can fully manage the career tracking system through MCP protocol without falling back to REST API.

## ADDED Requirements

### Requirement: Company domain tools
The MCP server SHALL provide tools for full company CRUD and query.

#### Scenario: Agent gets company detail
- **WHEN** an Agent calls `get_company(company_id)` with a valid company ID
- **THEN** the system SHALL return all company fields plus application count and note count

#### Scenario: Agent updates company fields
- **WHEN** an Agent calls `update_company(company_id, name=..., industry=...)`
- **THEN** the system SHALL update the specified fields and return the updated company

#### Scenario: Agent deletes a company
- **WHEN** an Agent calls `delete_company(company_id)`
- **THEN** the system SHALL delete the company and cascade-delete associated applications and notes

### Requirement: Application domain tools
The MCP server SHALL provide tools for querying, updating, and managing applications.

#### Scenario: Agent gets application detail
- **WHEN** an Agent calls `get_application(application_id)`
- **THEN** the system SHALL return the application with company name, resume name, and interview feedbacks

#### Scenario: Agent lists applications by status
- **WHEN** an Agent calls `list_applications(status="已投递", company_id=5)`
- **THEN** the system SHALL return applications matching the filter criteria

#### Scenario: Agent updates application status
- **WHEN** an Agent calls `update_application_status(application_id, status="已投递")`
- **THEN** the system SHALL update the status and return the updated application

#### Scenario: Agent gets pending approvals
- **WHEN** an Agent calls `get_pending_approvals()`
- **THEN** the system SHALL return all applications in "Pending Approval" status

#### Scenario: Agent handles decision on pending proposal
- **WHEN** an Agent calls `handle_decision(application_id, action="approve")`
- **THEN** the system SHALL update status, record DecisionFeedback, and return result

#### Scenario: Agent archives an application
- **WHEN** an Agent calls `archive_application(application_id, archive=True)`
- **THEN** the system SHALL set is_archived accordingly

### Requirement: Interview feedback domain tools
The MCP server SHALL provide tools for managing interview feedback records.

#### Scenario: Agent creates interview feedback
- **WHEN** an Agent calls `create_interview_feedback(application_id, round="一面", difficulty=4)`
- **THEN** the system SHALL create the feedback record and return its ID

#### Scenario: Agent lists interview feedbacks
- **WHEN** an Agent calls `list_interview_feedbacks(application_id)`
- **THEN** the system SHALL return all feedbacks for that application

### Requirement: Note domain tools
The MCP server SHALL provide tools for managing notes.

#### Scenario: Agent creates a note
- **WHEN** an Agent calls `create_note(company_id, title="调研总结", content="...")`
- **THEN** the system SHALL create the note and return its ID

#### Scenario: Agent lists notes by company
- **WHEN** an Agent calls `list_notes(company_id)`
- **THEN** the system SHALL return all notes for that company

#### Scenario: Agent updates a note
- **WHEN** an Agent calls `update_note(note_id, title="新标题")`
- **THEN** the system SHALL update the note fields

#### Scenario: Agent deletes a note
- **WHEN** an Agent calls `delete_note(note_id)`
- **THEN** the system SHALL delete the note

### Requirement: Timeline domain tools
The MCP server SHALL provide tools for managing timeline events.

#### Scenario: Agent creates timeline event
- **WHEN** an Agent calls `create_timeline_event(event_date="2026-08-15", title="秋招开始")`
- **THEN** the system SHALL create the timeline event

#### Scenario: Agent lists timeline events
- **WHEN** an Agent calls `list_timeline_events()`
- **THEN** the system SHALL return upcoming timeline events

#### Scenario: Agent toggles timeline event
- **WHEN** an Agent calls `toggle_timeline_event(event_id)`
- **THEN** the system SHALL toggle the done status

### Requirement: Resume domain tools
The MCP server SHALL provide tools for querying resume versions.

#### Scenario: Agent lists resumes
- **WHEN** an Agent calls `list_resumes()`
- **THEN** the system SHALL return all resume versions

#### Scenario: Agent gets default resume
- **WHEN** an Agent calls `get_default_resume()`
- **THEN** the system SHALL return the current default resume ID and name

### Requirement: Memory rule domain tools
The MCP server SHALL provide tools for managing exclusion rules directly.

#### Scenario: Agent adds a memory rule
- **WHEN** an Agent calls `add_memory_rule(category="exclude_tech", rule_value="Java")`
- **THEN** the system SHALL create a Memory record and return its ID

#### Scenario: Agent deletes a memory rule
- **WHEN** an Agent calls `delete_memory_rule(memory_id)`
- **THEN** the system SHALL delete the memory record

### Requirement: Statistics domain tool
The MCP server SHALL provide a tool for getting dashboard-level statistics.

#### Scenario: Agent gets statistics
- **WHEN** an Agent calls `get_statistics()`
- **THEN** the system SHALL return company count, S-count, funnel counts, offer count, interview count, rejected count, urgent deadlines count, pending feedbacks count

### Requirement: Trace and task domain tools
The MCP server SHALL provide tools for managing agent tasks and traces.

#### Scenario: Agent lists tasks
- **WHEN** an Agent calls `list_agent_tasks()`
- **THEN** the system SHALL return recent agent tasks with event counts and pending approvals count

#### Scenario: Agent gets task detail
- **WHEN** an Agent calls `get_agent_task(task_id)`
- **THEN** the system SHALL return the task with full event trace log

#### Scenario: Agent clears all traces
- **WHEN** an Agent calls `clear_agent_traces()`
- **THEN** the system SHALL delete all agent_event and agent_task records

### Requirement: Batch evaluation tool
The MCP server SHALL provide a batch evaluation tool for efficiency.

#### Scenario: Agent evaluates multiple JDs at once
- **WHEN** an Agent calls `batch_evaluate_jds(jds=[{"jd_text": "...", "company_name": "A"}, {"jd_text": "...", "company_name": "B"}])`
- **THEN** the system SHALL evaluate each JD independently and return an array of results with individual scores and risks

### Requirement: System notification tool
The MCP server SHALL provide a tool to trigger UI refresh notifications.

#### Scenario: Agent notifies UI of changes
- **WHEN** an Agent calls `notify_db_changed()`
- **THEN** the system SHALL increment the DB version counter, triggering SSE updates on dashboard