## 1. Company Domain Tools

- [x] 1.1 Add `get_company(company_id)` — return all fields + application count + note count
- [x] 1.2 Add `update_company(company_id, ...)` — update editable fields, return updated company
- [x] 1.3 Add `delete_company(company_id, confirm=False)` — cascade delete, require confirm=True

## 2. Application Domain Tools

- [x] 2.1 Add `get_application(application_id)` — return application with company name, resume name, interview feedbacks
- [x] 2.2 Add `list_applications(status=None, company_id=None, channel=None)` — filter and return list
- [x] 2.3 Add `update_application_status(application_id, status)` — update status field
- [x] 2.4 Add `get_pending_approvals()` — return pending approval proposals
- [x] 2.5 Add `handle_decision(application_id, action, reason_category, raw_feedback)` — approve/reject/edit with DecisionFeedback + Memory
- [x] 2.6 Add `archive_application(application_id, archive=True)` — toggle is_archived

## 3. Interview Feedback Tools

- [x] 3.1 Add `create_interview_feedback(application_id, round, difficulty, ...)` — create feedback record
- [x] 3.2 Add `list_interview_feedbacks(application_id)` — return feedbacks for an application

## 4. Note Domain Tools

- [x] 4.1 Add `create_note(company_id, title, content, category)` — create note
- [x] 4.2 Add `list_notes(company_id)` — return notes for a company
- [x] 4.3 Add `update_note(note_id, title, content, category)` — update note fields
- [x] 4.4 Add `delete_note(note_id, confirm=False)` — delete note, require confirm=True

## 5. Timeline Domain Tools

- [x] 5.1 Add `create_timeline_event(event_date, title, description, event_type, end_date)` — create event
- [x] 5.2 Add `list_timeline_events()` — return upcoming events
- [x] 5.3 Add `toggle_timeline_event(event_id)` — toggle done status

## 6. Resume Domain Tools

- [x] 6.1 Add `list_resumes()` — return all resume versions
- [x] 6.2 Add `get_default_resume()` — return default resume ID and name

## 7. Memory Rule Tools

- [x] 7.1 Add `add_memory_rule(category, rule_value, raw_feedback)` — create exclusion rule
- [x] 7.2 Add `delete_memory_rule(memory_id, confirm=False)` — delete rule, require confirm=True

## 8. Statistics Tool

- [x] 8.1 Add `get_statistics()` — return dashboard-level aggregate counts

## 9. Trace & Task Tools

- [x] 9.1 Add `list_agent_tasks(status=None, limit=50)` — return task list with event counts
- [x] 9.2 Add `get_agent_task(task_id)` — return task detail with event trace log
- [x] 9.3 Add `clear_agent_traces(confirm=False)` — delete all traces, require confirm=True

## 10. Batch Evaluation Tool

- [x] 10.1 Add `batch_evaluate_jds(jds)` — accept array of JD objects, return array of evaluation results

## 11. System Notification Tool

- [x] 11.1 Add `notify_db_changed()` — increment DB version for SSE notification

## 12. Tests

- [x] 12.1 Create `tests/test_mcp_full.py` with tests for all 27 new tools using tmp_path + monkeypatch pattern

## 13. Skill & Doc Updates

- [x] 13.1 Update `skills/job-sourcing-and-scoring/SKILL.md` — add get_company, get_statistics to tool references
- [x] 13.2 Update `skills/application-tracker/SKILL.md` — add list_applications, get_application, update_application_status, handle_decision, archive_application, create_interview_feedback, list_interview_feedbacks
- [x] 13.3 Update `skills/candidate-profile-and-resume/SKILL.md` — add list_resumes, get_default_resume, add_memory_rule, delete_memory_rule
- [x] 13.4 Update `skills/tracker-ops/SKILL.md` — add create_note, list_notes, update_note, delete_note, create_timeline_event, list_timeline_events, toggle_timeline_event, list_agent_tasks, get_agent_task, clear_agent_traces, notify_db_changed
- [x] 13.5 Update `docs/SKILLS_AND_MCP_GUIDE.md` — update MCP tools list to 36 tools