"""Unit tests for Agent API endpoints (/api/v1/)."""
import json
import pytest
from extensions import db
from models import Company, Application, Memory, AgentTask, AgentEvent


class TestAgentAPI:
    def test_search_companies(self, client, app):
        with app.app_context():
            c1 = Company(name='AI Tech Inc', industry='AI', priority='S')
            c2 = Company(name='Robotics Co', industry='Robotics', priority='A')
            db.session.add_all([c1, c2])
            db.session.commit()

        res = client.get('/api/v1/companies/search?q=AI')
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert data['count'] >= 1
        names = [item['name'] for item in data['companies']]
        assert 'AI Tech Inc' in names

    def test_update_company_score(self, client, app):
        with app.app_context():
            c = Company(name='Score Test Co', priority='B')
            db.session.add(c)
            db.session.commit()
            c_id = c.id

        res = client.post(
            f'/api/v1/companies/{c_id}/score',
            data=json.dumps({'score': 92, 'reason': 'Excellent alignment'}),
            content_type='application/json'
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert data['company']['score'] == 92
        assert data['company']['score_reason'] == 'Excellent alignment'

    def test_get_profile(self, client):
        res = client.get('/api/v1/profile')
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert 'profile' in data

    def test_record_and_list_traces(self, client):
        payload = {
            'task_id': 'task-001',
            'agent_name': 'TestAgent',
            'event_type': 'thought',
            'payload': {'action': 'searching companies'},
            'status': 'running'
        }
        res = client.post(
            '/api/v1/traces',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert data['task_id'] == 'task-001'

        res_list = client.get('/api/v1/traces')
        assert res_list.status_code == 200
        list_data = res_list.get_json()
        assert list_data['status'] == 'success'
        assert list_data['count'] >= 1

    def test_create_companies_batch_and_dedup(self, client, app):
        payload = {
            'companies': [
                {'name': 'Unique Co', 'industry': 'Automation', 'city': 'Shenzhen'},
                {'name': 'Unique Co', 'industry': 'Automation', 'city': 'Shenzhen'}
            ]
        }
        res = client.post(
            '/api/v1/companies',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert data['count'] == 2
        assert data['companies'][0]['created'] is True
        assert data['companies'][1]['created'] is False

    def test_create_pending_application(self, client, app):
        with app.app_context():
            c = Company(name='App Target Co')
            db.session.add(c)
            db.session.commit()
            c_id = c.id

        payload = {
            'company_id': c_id,
            'position': 'Embedded Engineer',
            'url': 'https://example.com/job/1',
            'match_score': 95,
            'agent_reason': 'High stack match',
            'agent_task_id': 'task-999',
            'source_url': 'https://example.com/job/1'
        }
        res = client.post(
            '/api/v1/applications',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert data['application']['company_id'] == c_id
        assert data['application']['status'] == '待投递'
        assert data['application']['match_score'] == 95
        assert data['application']['agent_reason'] == 'High stack match'

    def test_review_application_and_preferences(self, client, app):
        with app.app_context():
            c = Company(name='Review Co')
            db.session.add(c)
            db.session.commit()
            app_obj = Application(company_id=c.id, position='Algo Engineer', status='pending')
            db.session.add(app_obj)
            db.session.commit()
            app_id = app_obj.id

        # Test approve
        res_appr = client.post(
            f'/api/v1/applications/{app_id}/review',
            data=json.dumps({'action': 'approve'}),
            content_type='application/json'
        )
        assert res_appr.status_code == 200
        assert res_appr.get_json()['action'] == 'approved'

        # Test reject with memory
        res_rej = client.post(
            f'/api/v1/applications/{app_id}/review',
            data=json.dumps({
                'action': 'reject',
                'category': 'exclude_tech',
                'rule_value': 'Java',
                'raw_feedback': 'Not interested in legacy Java maintenance'
            }),
            content_type='application/json'
        )
        assert res_rej.status_code == 200
        assert res_rej.get_json()['action'] == 'rejected'

        # Test get_user_preferences
        res_pref = client.get('/api/v1/profile/preferences')
        assert res_pref.status_code == 200
        pref_data = res_pref.get_json()
        assert pref_data['status'] == 'success'
        assert any(r['rule_value'] == 'Java' for r in pref_data['negative_rules'])
        assert 'Not interested in legacy Java maintenance' in pref_data['recent_rejection_notes']

    def test_traces_html_page(self, client):
        res = client.get('/traces')
        assert res.status_code == 200
        assert 'Agent 执行轨迹' in res.get_data(as_text=True)
