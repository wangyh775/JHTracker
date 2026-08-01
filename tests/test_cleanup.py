"""Unit tests for Agent trace cleanup logic."""
import json
import os
from datetime import datetime, timedelta
from extensions import db
from models import AgentTask, AgentEvent


class TestCleanupService:
    def test_cleanup_expired_events(self, app, tmp_path):
        from services.cleanup import cleanup_expired_traces
        with app.app_context():
            task = AgentTask(task_id='expired-task', agent_name='Test', status='completed')
            db.session.add(task)
            db.session.flush()
            old = AgentEvent(task_id=task.id, event_type='old',
                             payload_json='{}', created_at=datetime.now() - timedelta(days=60))
            recent = AgentEvent(task_id=task.id, event_type='recent',
                                payload_json='{}', created_at=datetime.now())
            db.session.add_all([old, recent])
            db.session.commit()

            count = cleanup_expired_traces(days=30)

            assert count >= 1
            remaining = AgentEvent.query.all()
            assert len(remaining) == 1
            assert remaining[0].event_type == 'recent'

    def test_cleanup_orphaned_tasks(self, app):
        from services.cleanup import cleanup_expired_traces
        with app.app_context():
            task = AgentTask(task_id='orphan-task', agent_name='Test', status='completed',
                             created_at=datetime.now() - timedelta(days=60))
            db.session.add(task)
            db.session.commit()

            cleanup_expired_traces(days=30)

            remaining = AgentTask.query.filter_by(task_id='orphan-task').first()
            assert remaining is None

    def test_cleanup_preserves_recent_events(self, app):
        from services.cleanup import cleanup_expired_traces
        with app.app_context():
            task = AgentTask(task_id='recent-task', agent_name='Test', status='running')
            db.session.add(task)
            db.session.flush()
            ev = AgentEvent(task_id=task.id, event_type='recent', payload_json='{}',
                            created_at=datetime.now() - timedelta(days=5))
            db.session.add(ev)
            db.session.commit()

            cleanup_expired_traces(days=30)

            assert AgentEvent.query.count() == 1
            assert AgentTask.query.filter_by(task_id='recent-task').first() is not None

    def test_clear_all_traces(self, app):
        from services.cleanup import clear_all_traces
        with app.app_context():
            task = AgentTask(task_id='clear-task', agent_name='Test', status='completed')
            db.session.add(task)
            db.session.flush()
            db.session.add(AgentEvent(task_id=task.id, event_type='ev', payload_json='{}'))
            db.session.commit()

            clear_all_traces()

            assert AgentEvent.query.count() == 0
            assert AgentTask.query.count() == 0

    def test_throttle_prevents_duplicate_run(self, app, tmp_path):
        from services.cleanup import _should_run_today, _touch_last_run, LAST_RUN_FILE
        _touch_last_run()
        assert not _should_run_today()
        os.remove(LAST_RUN_FILE)
        assert _should_run_today()


class TestCleanupAPI:
    def test_clear_endpoint(self, client, app):
        with app.app_context():
            task = AgentTask(task_id='api-clear', agent_name='Test', status='completed')
            db.session.add(task)
            db.session.flush()
            db.session.add(AgentEvent(task_id=task.id, event_type='ev', payload_json='{}'))
            db.session.commit()

        res = client.post('/api/agent/traces/clear')
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'

        with app.app_context():
            assert AgentEvent.query.count() == 0
            assert AgentTask.query.count() == 0