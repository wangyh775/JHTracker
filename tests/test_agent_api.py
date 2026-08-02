"""Unit tests for Agent API endpoints (/api/v1/)."""
import json
import sqlite3
import pytest
from extensions import db
from models import Company, Application, Memory, AgentTask, AgentEvent, DecisionFeedback


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
        assert data['created'] is True
        assert data['application']['company_id'] == c_id
        assert data['application']['status'] == 'Pending Approval'
        assert data['application']['match_score'] == 95
        assert data['application']['agent_reason'] == 'High stack match'

    def test_create_application_deduplication(self, client, app):
        with app.app_context():
            c = Company(name='Dedup Target Co')
            db.session.add(c)
            db.session.commit()
            c_id = c.id

        payload = {
            'company_id': c_id,
            'position': '  Robotics Engineer ',
            'source_url': 'https://example.com/job/2'
        }
        # First creation -> created: True
        res1 = client.post('/api/v1/applications', data=json.dumps(payload), content_type='application/json')
        assert res1.status_code == 200
        data1 = res1.get_json()
        assert data1['status'] == 'success'
        assert data1['created'] is True
        app_id = data1['application']['id']

        # Duplicate creation with whitespace & case difference -> created: False, returns existing app_id
        payload_dup = {
            'company_id': c_id,
            'position': 'robotics engineer',
            'source_url': 'https://example.com/job/2?ref=dup'
        }
        res2 = client.post('/api/v1/applications', data=json.dumps(payload_dup), content_type='application/json')
        assert res2.status_code == 200
        data2 = res2.get_json()
        assert data2['status'] == 'success'
        assert data2['created'] is False
        assert data2['application']['id'] == app_id

    def test_review_application_and_preferences(self, client, app):
        with app.app_context():
            c = Company(name='Review Co', industry='Robotics')
            db.session.add(c)
            db.session.commit()
            app_obj = Application(company_id=c.id, position='Algo Engineer', status='pending')
            db.session.add(app_obj)
            db.session.commit()
            app_id = app_obj.id

        # Test approve — should write positive memories (prefer_company, prefer_domain)
        res_appr = client.post(
            f'/api/v1/applications/{app_id}/review',
            data=json.dumps({'action': 'approve'}),
            content_type='application/json'
        )
        assert res_appr.status_code == 200
        assert res_appr.get_json()['action'] == 'approved'

        # Test reject with memory — rule_value 仅存结构化值，raw_feedback 存原文
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

        # Test get_user_preferences — 验证 positive_rules 与 negative_rules 双向返回
        res_pref = client.get('/api/v1/profile/preferences')
        assert res_pref.status_code == 200
        pref_data = res_pref.get_json()
        assert pref_data['status'] == 'success'
        # 正向规则：approve 写入的 prefer_company / prefer_domain
        pos_rules = pref_data['positive_rules']
        assert any(r['rule_value'] == 'Review Co' for r in pos_rules)
        assert any(r['rule_value'] == 'Robotics' for r in pos_rules)
        # 负向规则：reject 写入的 exclude_tech
        assert any(r['rule_value'] == 'Java' for r in pref_data['negative_rules'])
        assert 'Not interested in legacy Java maintenance' in pref_data['recent_rejection_notes']

    def test_traces_html_page(self, client):
        res = client.get('/traces')
        assert res.status_code == 200
        assert 'Agent 执行轨迹' in res.get_data(as_text=True)

    def test_get_agent_tasks_and_detail_api(self, client, app):
        with app.app_context():
            task = AgentTask(task_id='test-task-100', agent_name='TesterAgent', status='running')
            db.session.add(task)
            db.session.commit()
            event = AgentEvent(task_id=task.id, event_type='step_1', payload_json=json.dumps({'msg': 'ok'}))
            db.session.add(event)
            db.session.commit()
            t_id = task.id

        res = client.get('/api/agent/tasks')
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert data['count'] >= 1

        res_detail = client.get(f'/api/agent/tasks/{t_id}')
        assert res_detail.status_code == 200
        detail_data = res_detail.get_json()
        assert detail_data['status'] == 'success'
        assert detail_data['task']['agent_name'] == 'TesterAgent'
        assert len(detail_data['task']['events']) == 1


class TestMCPToolsDirectly:
    def test_update_candidate_profile_mcp(self, tmp_path, monkeypatch):
        import mcp_server
        profile_file = tmp_path / "profile.md"
        monkeypatch.setattr(mcp_server, "PROFILE_PATH", str(profile_file))

        res_raw = mcp_server.update_candidate_profile("## Education\n- BS CS")
        res = json.loads(res_raw)
        assert res['status'] == 'success'
        assert profile_file.read_text(encoding='utf-8') == "## Education\n- BS CS"

    def test_agent_mutation_active_record_mcp_rejected(self, tmp_path, monkeypatch):
        import mcp_server
        db_file = tmp_path / "tracker.db"
        monkeypatch.setattr(mcp_server, "DB_PATH", str(db_file))

        # Setup schema
        conn = sqlite3.connect(str(db_file))
        conn.execute("""
            CREATE TABLE companies (id INTEGER PRIMARY KEY, name TEXT);
        """)
        conn.execute("""
            CREATE TABLE applications (id INTEGER PRIMARY KEY, company_id INTEGER, position TEXT, status TEXT, updated_at DATETIME);
        """)
        conn.execute("INSERT INTO companies (id, name) VALUES (1, 'Test Co')")
        conn.execute("INSERT INTO applications (id, company_id, position, status) VALUES (10, 1, 'Dev', '已投递')")
        conn.commit()
        conn.close()

        res_raw = mcp_server.update_application_status(10, 'Offer')
        res = json.loads(res_raw)
        assert res['status'] == 'error'
        assert 'POST_APPLY_STATUS_LIST' in res['message']

    def test_record_agent_trace_mcp(self, tmp_path, monkeypatch):
        import mcp_server
        db_file = tmp_path / "tracker.db"
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        conn.execute("""
            CREATE TABLE agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                agent_name TEXT,
                status TEXT DEFAULT 'running',
                created_at DATETIME
            );
        """)
        conn.execute("""
            CREATE TABLE agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT,
                created_at DATETIME
            );
        """)
        conn.commit()
        conn.close()

        def mock_get_db():
            c = sqlite3.connect(str(db_file))
            c.row_factory = sqlite3.Row
            return c

        monkeypatch.setattr(mcp_server, "get_db_connection", mock_get_db)

        res_raw = mcp_server.record_agent_trace(
            task_id="mcp-task-1",
            agent_name="MCPScorer",
            event_type="scoring",
            payload={"score": 88}
        )
        res = json.loads(res_raw)
        assert res['status'] == 'success'
        assert res['task_id'] == 'mcp-task-1'
        assert res['event_id'] > 0

    def test_evaluate_jd_mcp(self, tmp_path, monkeypatch):
        import mcp_server
        db_file = tmp_path / "tracker.db"
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        conn.execute("""
            CREATE TABLE agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                agent_name TEXT,
                status TEXT DEFAULT 'running',
                created_at DATETIME
            );
        """)
        conn.execute("""
            CREATE TABLE agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT,
                created_at DATETIME
            );
        """)
        conn.execute("""
            CREATE TABLE memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                rule_value TEXT,
                raw_feedback TEXT,
                created_at DATETIME
            );
        """)
        conn.execute("""
            CREATE TABLE decision_feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                action TEXT,
                reason_category TEXT,
                raw_feedback TEXT,
                created_at DATETIME
            );
        """)
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('exclude_tech', 'Java外包');")
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('prefer_tech', 'python');")
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('prefer_tech', 'c++');")
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('prefer_domain', '机器人');")
        conn.commit()
        conn.close()

        def mock_get_db():
            c = sqlite3.connect(str(db_file))
            c.row_factory = sqlite3.Row
            return c

        monkeypatch.setattr(mcp_server, "get_db_connection", mock_get_db)

        res_raw = mcp_server.evaluate_jd(
            jd_text="招聘机器人算法工程师，精通 Python, C++, ROS，负责算法开发",
            company_name="RoboCorp",
            task_id="eval-test-1"
        )
        res = json.loads(res_raw)
        assert res['status'] == 'success'
        # 正向规则命中（python/c++/机器人）应加分，基准 75 + 至少 2 条命中 = 83+
        assert res['result']['match_score'] >= 80
        assert 'python' in [m.lower() for m in res['result']['positive_matches']]
        assert '机器人' in res['result']['positive_matches']


class TestDecisionInboxAPI:
    def test_pending_decisions_and_actions(self, client, app):
        with app.app_context():
            c = Company(name='Decision Co', priority='A')
            db.session.add(c)
            db.session.commit()

            app1 = Application(company_id=c.id, position='Robotics Eng', status='Pending Approval', match_score=88, agent_reason='Great fit')
            app2 = Application(company_id=c.id, position='Web Dev', status='Pending Approval', match_score=50, agent_reason='Low fit')
            db.session.add_all([app1, app2])
            db.session.commit()
            id1, id2 = app1.id, app2.id

        res = client.get('/api/agent/decisions/pending')
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'
        assert data['count'] >= 2

        res_approve = client.post(f'/api/agent/decisions/{id1}', json={'action': 'approve'})
        assert res_approve.status_code == 200
        assert res_approve.get_json()['action'] == 'approved'

        res_reject = client.post(f'/api/agent/decisions/{id2}', json={
            'action': 'reject',
            'reason_category': 'tech_mismatch',
            'raw_feedback': 'Role is too web-focused'
        })
        assert res_reject.status_code == 200
        assert res_reject.get_json()['action'] == 'rejected'

        with app.app_context():
            a1 = db.session.get(Application, id1)
            a2 = db.session.get(Application, id2)
            assert a1.status == '待投递'
            assert a2.status == '已拒'
            fb = DecisionFeedback.query.filter_by(application_id=id2).first()
            assert fb is not None
            assert fb.action == 'reject'
            assert fb.reason_category == 'tech_mismatch'
            assert fb.raw_feedback == 'Role is too web-focused'

    def test_pending_decisions_html(self, client, app):
        with app.app_context():
            c = Company(name='HTML Decision Co', priority='A')
            db.session.add(c)
            db.session.commit()
            app1 = Application(company_id=c.id, position='HTML Eng', status='Pending Approval', match_score=90)
            db.session.add(app1)
            db.session.commit()

        res = client.get('/api/agent/decisions/pending-html')
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert 'HTML Decision Co' in html
        assert 'HTML Eng' in html

    def test_agent_tasks_html(self, client, app):
        with app.app_context():
            task = AgentTask(task_id='html-task-001', agent_name='HTMXAgent', status='running')
            db.session.add(task)
            db.session.commit()

        res = client.get('/api/agent/tasks-html')
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert 'HTMXAgent' in html
        assert 'html-task-001' in html


class TestTracesEdgeCases:
    """Traces 功能的边界场景测试。"""

    def test_trace_without_task_id_returns_400(self, client):
        res = client.post(
            '/api/v1/traces',
            data=json.dumps({'agent_name': 'NoTaskAgent', 'event_type': 'info'}),
            content_type='application/json'
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['status'] == 'error'

    def test_duplicate_task_id_appends_events_not_duplicate_tasks(self, client):
        payload = {
            'task_id': 'dup-task',
            'agent_name': 'DupAgent',
            'event_type': 'step_1',
            'payload': {'msg': 'first'},
            'status': 'running'
        }
        client.post('/api/v1/traces', data=json.dumps(payload), content_type='application/json')

        payload['event_type'] = 'step_2'
        payload['payload'] = {'msg': 'second'}
        client.post('/api/v1/traces', data=json.dumps(payload), content_type='application/json')

        res_list = client.get('/api/v1/traces')
        data = res_list.get_json()
        tasks_with_dup = [t for t in data['tasks'] if t['task_id'] == 'dup-task']
        assert len(tasks_with_dup) == 1
        assert len(tasks_with_dup[0]['events']) == 2
        assert tasks_with_dup[0]['events'][0]['payload']['msg'] == 'first'
        assert tasks_with_dup[0]['events'][1]['payload']['msg'] == 'second'

    def test_trace_with_large_payload_does_not_crash(self, client):
        large_payload = {'data': 'x' * 10000}
        res = client.post(
            '/api/v1/traces',
            data=json.dumps({'task_id': 'large-payload', 'agent_name': 'BigAgent', 'event_type': 'data', 'payload': large_payload}),
            content_type='application/json'
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'success'

    def test_traces_html_page_with_no_data_shows_empty_state(self, client):
        res = client.get('/traces')
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert '暂无 Agent 任务记录' in html

    def test_get_agent_tasks_empty_returns_zero(self, client):
        res = client.get('/api/agent/tasks')
        assert res.status_code == 200
        data = res.get_json()
        assert data['count'] == 0
        assert data['tasks'] == []

    def test_get_agent_task_detail_not_found_returns_404(self, client):
        res = client.get('/api/agent/tasks/nonexistent-task-id')
        assert res.status_code == 404
        data = res.get_json()
        assert data['status'] == 'error'

    def test_trace_status_updates_preserve_previous_events(self, client):
        payload = {
            'task_id': 'status-update-task',
            'agent_name': 'StatusAgent',
            'event_type': 'start',
            'payload': {'phase': 'begin'},
            'status': 'running'
        }
        client.post('/api/v1/traces', data=json.dumps(payload), content_type='application/json')

        payload['event_type'] = 'complete'
        payload['payload'] = {'phase': 'end'}
        payload['status'] = 'completed'
        client.post('/api/v1/traces', data=json.dumps(payload), content_type='application/json')

        res = client.get('/api/v1/traces')
        data = res.get_json()
        task = next(t for t in data['tasks'] if t['task_id'] == 'status-update-task')
        assert task['status'] == 'completed'
        assert len(task['events']) == 2


class TestBidirectionalMemoryRules:
    """双向记忆规则：正向 prefer_* / 负向 exclude_* 的写入、消费、去重、极性。"""

    def _setup_mcp_db(self, tmp_path, monkeypatch):
        """构造一个带 memories + decision_feedbacks + agent 表的临时 DB，并 monkeypatch mcp_server。"""
        import mcp_server
        import sqlite3
        db_file = tmp_path / "tracker.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("""CREATE TABLE agent_tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT UNIQUE NOT NULL, agent_name TEXT, status TEXT DEFAULT 'running', created_at DATETIME)""")
        conn.execute("""CREATE TABLE agent_events (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER NOT NULL, event_type TEXT NOT NULL, payload_json TEXT, created_at DATETIME)""")
        conn.execute("""CREATE TABLE memories (id INTEGER PRIMARY KEY AUTOINCREMENT, application_id INTEGER, category TEXT, rule_value TEXT, raw_feedback TEXT, created_at DATETIME)""")
        conn.execute("""CREATE TABLE decision_feedbacks (id INTEGER PRIMARY KEY AUTOINCREMENT, application_id INTEGER, action TEXT, reason_category TEXT, raw_feedback TEXT, created_at DATETIME)""")
        conn.execute("""CREATE TABLE applications (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, position TEXT, job_desc TEXT, status TEXT, created_at DATETIME, updated_at DATETIME)""")
        conn.execute("""CREATE TABLE companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, industry TEXT, city TEXT)""")
        conn.commit()
        conn.close()

        def mock_get_db():
            c = sqlite3.connect(str(db_file))
            c.row_factory = sqlite3.Row
            return c

        monkeypatch.setattr(mcp_server, "get_db_connection", mock_get_db)
        return mcp_server

    def test_evaluate_jd_no_rules_baseline(self, tmp_path, monkeypatch):
        """无任何规则时基准分 75，无 positive/negative matches。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        res = json.loads(mcp_server.evaluate_jd(
            jd_text="招聘嵌入式工程师，要求精通 STM32 和 FreeRTOS，负责算法开发",
            company_name="TestCo",
            task_id="eval-bi-1"
        ))
        assert res['status'] == 'success'
        assert res['result']['match_score'] == 75
        assert res['result']['positive_matches'] == []
        assert res['result']['negative_matches'] == []

    def test_evaluate_jd_negative_rule_deducts_score(self, tmp_path, monkeypatch):
        """负向规则命中应扣分。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        conn = mcp_server.get_db_connection()
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('exclude_tech', 'stm32')")
        conn.commit()
        conn.close()

        res = json.loads(mcp_server.evaluate_jd(
            jd_text="招聘嵌入式工程师，要求精通 STM32 和 FreeRTOS",
            company_name="TestCo",
            task_id="eval-neg-1"
        ))
        assert res['status'] == 'success'
        assert 'stm32' in [m.lower() for m in res['result']['negative_matches']]
        assert res['result']['match_score'] < 75
        assert any('stm32' in r.lower() for r in res['result']['risks'])

    def test_evaluate_jd_outsourcing_keyword_caps_score(self, tmp_path, monkeypatch):
        """外包/驻场关键词应封顶 30 分。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        res = json.loads(mcp_server.evaluate_jd(
            jd_text="招聘外包驻场开发工程师，精通 Java",
            company_name="OutsourceCo",
            task_id="eval-out-1"
        ))
        assert res['status'] == 'success'
        assert res['result']['match_score'] <= 30

    def test_add_memory_rule_polarity_positive_mapping(self, tmp_path, monkeypatch):
        """polarity='positive' + category='tech' → prefer_tech。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        res = json.loads(mcp_server.add_memory_rule(category='tech', rule_value='ROS', polarity='positive'))
        assert res['status'] == 'success'
        assert res['category'] == 'prefer_tech'
        assert res['polarity'] == 'positive'

    def test_add_memory_rule_polarity_negative_mapping(self, tmp_path, monkeypatch):
        """polarity='negative' + category='company' → exclude_company。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        res = json.loads(mcp_server.add_memory_rule(category='company', rule_value='BadCorp', polarity='negative'))
        assert res['status'] == 'success'
        assert res['category'] == 'exclude_company'
        assert res['polarity'] == 'negative'

    def test_add_memory_rule_backward_compat_no_polarity(self, tmp_path, monkeypatch):
        """未传 polarity 时直接使用 category（向后兼容）。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        res = json.loads(mcp_server.add_memory_rule(category='salary_too_low', rule_value='8000'))
        assert res['status'] == 'success'
        assert res['category'] == 'salary_too_low'

    def test_add_memory_rule_invalid_polarity_category(self, tmp_path, monkeypatch):
        """非法 polarity+category 组合应报错。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        res = json.loads(mcp_server.add_memory_rule(category='nonexistent', rule_value='x', polarity='positive'))
        assert res['status'] == 'error'

    def test_add_memory_rule_dedup(self, tmp_path, monkeypatch):
        """相同 (category, rule_value) 去重，不重复写入。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        r1 = json.loads(mcp_server.add_memory_rule(category='tech', rule_value='Python', polarity='positive'))
        assert r1['status'] == 'success'
        r2 = json.loads(mcp_server.add_memory_rule(category='tech', rule_value='Python', polarity='positive'))
        assert r2['status'] == 'success'
        assert r2['memory_id'] == r1['memory_id']

        conn = mcp_server.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM memories WHERE category='prefer_tech' AND rule_value='Python'")
        assert cursor.fetchone()['cnt'] == 1
        conn.close()

    def test_delete_memory_rule_requires_confirm(self, tmp_path, monkeypatch):
        """delete_memory_rule 无 confirm 应报错，有 confirm 删除成功。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        mcp_server.add_memory_rule(category='tech', rule_value='Go', polarity='positive')
        conn = mcp_server.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM memories WHERE rule_value='Go'")
        mem_id = cursor.fetchone()['id']
        conn.close()

        res = json.loads(mcp_server.delete_memory_rule(memory_id=mem_id, confirm=False))
        assert res['status'] == 'error'
        assert 'confirm' in res['message'].lower()

        res2 = json.loads(mcp_server.delete_memory_rule(memory_id=mem_id, confirm=True))
        assert res2['status'] == 'success'

    def test_get_user_preferences_splits_polarity(self, tmp_path, monkeypatch):
        """get_user_preferences 应按极性拆分 positive_rules / negative_rules。"""
        mcp_server = self._setup_mcp_db(tmp_path, monkeypatch)
        conn = mcp_server.get_db_connection()
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('prefer_tech', 'ROS')")
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('exclude_company', 'BadCo')")
        conn.execute("INSERT INTO memories (category, rule_value) VALUES ('salary_expected', '20000')")
        conn.commit()
        conn.close()

        res = json.loads(mcp_server.get_user_preferences())
        assert res['status'] == 'success'
        pos_cats = [r['category'] for r in res['positive_rules']]
        neg_cats = [r['category'] for r in res['negative_rules']]
        assert 'prefer_tech' in pos_cats
        assert 'salary_expected' in pos_cats
        assert 'exclude_company' in neg_cats
        assert 'prefer_tech' not in neg_cats


class TestInducePositiveRules:
    """批量归纳脚本测试：指纹缓存跳过、去重、解析过滤。"""

    def test_fingerprint_skip_when_unchanged(self, tmp_path, monkeypatch):
        """指纹未变时应跳过 LLM 归纳。"""
        import scripts.induce_positive_rules as induce

        monkeypatch.setattr(induce, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(induce, "FINGERPRINT_FILE", str(tmp_path / ".fp"))
        monkeypatch.setattr(induce, "DB_PATH", str(tmp_path / "tracker.db"))

        import sqlite3
        conn = sqlite3.connect(str(tmp_path / "tracker.db"))
        conn.execute("""CREATE TABLE applications (id INTEGER PRIMARY KEY, company_id INTEGER, position TEXT, job_desc TEXT, status TEXT, channel TEXT)""")
        conn.execute("""CREATE TABLE companies (id INTEGER PRIMARY KEY, name TEXT, industry TEXT, city TEXT)""")
        conn.execute("""CREATE TABLE memories (id INTEGER PRIMARY KEY, category TEXT, rule_value TEXT, raw_feedback TEXT, created_at DATETIME)""")
        conn.execute("INSERT INTO applications (id, company_id, position, status) VALUES (1, 1, 'Eng', 'Applied')")
        conn.execute("INSERT INTO companies (id, name, industry) VALUES (1, 'Co', 'Robotics')")
        conn.commit()
        conn.close()

        # 预先写入指纹（与当前 approve 列表 + 空 profile 一致）
        fp = induce.compute_fingerprint([1], "")
        induce.save_fingerprint(fp)

        # mock sys.argv 避免 argparse 吞掉 pytest 参数
        monkeypatch.setattr("sys.argv", ["induce_positive_rules.py"])
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            induce.main()
        output = buf.getvalue()
        assert "未变化" in output or "跳过" in output

    def test_dedup_does_not_duplicate(self, tmp_path, monkeypatch):
        """去重写入：相同 (category, rule_value) 不重复。"""
        import scripts.induce_positive_rules as induce
        import sqlite3

        monkeypatch.setattr(induce, "DB_PATH", str(tmp_path / "tracker.db"))
        conn = sqlite3.connect(str(tmp_path / "tracker.db"))
        conn.execute("""CREATE TABLE memories (id INTEGER PRIMARY KEY, category TEXT, rule_value TEXT, raw_feedback TEXT, created_at DATETIME)""")
        conn.commit()
        conn.close()

        # 第一次写入
        c1 = sqlite3.connect(str(tmp_path / "tracker.db"))
        assert induce._upsert_memory_rule(c1, 'prefer_tech', 'ROS') is True
        c1.commit()
        c1.close()

        # 第二次相同规则 → 去重
        c2 = sqlite3.connect(str(tmp_path / "tracker.db"))
        assert induce._upsert_memory_rule(c2, 'prefer_tech', 'ROS') is False
        cursor = c2.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM memories WHERE category='prefer_tech' AND rule_value='ROS'")
        assert cursor.fetchone()[0] == 1
        c2.close()

    def test_parse_rules_filters_invalid_category(self):
        """_parse_rules 应过滤掉非法 category。"""
        import scripts.induce_positive_rules as induce
        text = '[{"category": "prefer_tech", "rule_value": "ROS"}, {"category": "hacked", "rule_value": "evil"}]'
        rules = induce._parse_rules(text)
        assert len(rules) == 1
        assert rules[0] == ('prefer_tech', 'ROS')


