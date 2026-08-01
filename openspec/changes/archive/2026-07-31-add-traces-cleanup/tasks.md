## 1. Config & Service

- [x] 1.1 Add `TRACES_RETENTION_DAYS` to `config.py` with env var `JH_TRACES_RETENTION_DAYS` (default 30)
- [x] 1.2 Create `services/cleanup.py` with `cleanup_expired_traces(days)` function: delete `agent_events` WHERE `created_at < cutoff`, then delete orphaned `agent_tasks` with no remaining events
- [x] 1.3 Add daily throttle to `services/cleanup.py` (`.traces_cleanup_last_run` file, same pattern as `archive.py`)

## 2. API Endpoint & Route Trigger

- [x] 2.1 In `routes/agent_api.py`, add `POST /api/agent/traces/clear` endpoint that deletes all `agent_events` and `agent_tasks`
- [x] 2.2 In `routes/agent_api.py`, update the `traces_view()` (`GET /traces`) to call `cleanup_expired_traces()` with throttle before rendering

## 3. Frontend

- [x] 3.1 Add "清空全部轨迹" button to `templates/traces.html` with confirmation dialog
- [x] 3.2 Wire the button to `POST /api/agent/traces/clear` via JavaScript fetch

## 4. Tests

- [x] 4.1 Create `tests/test_cleanup.py`: test auto cleanup deletes expired events, preserves recent events, deletes orphaned tasks
- [x] 4.2 Test manual clear endpoint deletes all traces
- [x] 4.3 Test throttle prevents duplicate runs

## 5. Documentation

- [x] 5.1 Update `docs/hitl-feedback-loop.md` "Trace Audit" section to mention cleanup mechanism and retention period