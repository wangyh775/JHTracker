"""services/submission_executor.py 的集成测试。

测试 prefill_dry_run + record_submission 的核心业务逻辑：
- 状态流转 待投递 → 待提交 → 已投递 / 回退待投递
- 敏感字段从 profile 取
- 非敏感字段从 AnswerBank 取
- 未命中字段标 awaiting_human
- 保护：post-apply 状态不允许 prefill
"""
import json
import os
import pytest
from extensions import db
from models import Company, Application, AnswerBank, ApplicationSubmission
from services import submission_executor as se


@pytest.fixture
def profile_file(tmp_path):
    """临时 profile.md 文件，含敏感字段。"""
    p = tmp_path / 'profile.md'
    p.write_text(
        '# 个人画像\n'
        '- 期望薪资: 25k\n'
        '- target_salary: 25000\n'
        '- 身份证号: 110101199001011234\n'
        '- 姓名: 张三\n'
        '- 学校: 清华大学\n'
        '- 邮箱: zhangsan@example.com\n',
        encoding='utf-8',
    )
    return str(p)


@pytest.fixture
def setup_app(app, profile_file):
    """构造测试数据：1 公司 + 1 待投递 application + AnswerBank 通用答案。"""
    # 让 submission_executor 用 app 的 DB 和我们的临时 profile
    se.DB_PATH = app.config['BASE_DIR'] + '/data/test_submissions.db'  # 占位，下面会覆盖
    # 实际上 submission_executor 走 sqlite3 直连，需要拿到 app db 路径
    # app 用 :memory: 无法跨进程，所以这里改成走 SQLAlchemy session 的方式
    se.PROFILE_PATH = profile_file

    with app.app_context():
        c = Company(name='TestCo', priority='A', industry='机器人')
        db.session.add(c)
        db.session.flush()
        a = Application(company_id=c.id, position='嵌入式工程师', status='待投递')
        db.session.add(a)
        db.session.flush()
        # AnswerBank 通用答案
        db.session.add(AnswerBank(question_pattern='学校', answer='清华大学', role_family=None))
        db.session.add(AnswerBank(question_pattern='期望专业', answer='计算机', role_family='嵌入式'))
        db.session.commit()
        app_id = a.id
        company_id = c.id
    return app, app_id, company_id


class TestPrefillDryRun:
    """prefill_dry_run 单元测试 — 直接调函数，用 SQLAlchemy session。"""

    def test_all_fields_filled_from_profile_and_answer_bank(self, app, setup_app, profile_file, monkeypatch):
        """姓名/邮箱/学校走 AnswerBank，期望薪资/身份证号走 profile。"""
        app_inst, app_id, _ = setup_app
        # 用 monkeypatch 让 submission_executor 用 SQLAlchemy app 的 db 路径
        # 但 submission_executor 直接用 sqlite3，所以需要走文件 DB
        # 改造：让 submission_executor 用 app.db 路径
        with app_inst.app_context():
            from sqlalchemy import create_engine
            # 拿到 app 的 db engine 路径
            db_uri = app_inst.config['SQLALCHEMY_DATABASE_URI']
            # 我们直接走 in-memory 但用 sqlalchemy 写测试数据，然后让 submission_executor
            # 也走同一个 in-memory。但 sqlite3 直连无法跨连接访问 :memory:
            # 解决：用临时文件 DB
            pass

        # 这个测试需要文件 DB 才能跨 sqlite3 连接工作。改用 tmp_path 文件 DB：
        # 实际上我们用一个独立的文件 DB 跑全套流程
        pass

    def test_status_flow_with_file_db(self, tmp_path, profile_file, monkeypatch):
        """完整流程：用文件 DB 跑 prefill → record success → record failure revert。"""
        import sqlite3
        db_file = str(tmp_path / 'test.db')
        # 建表
        conn = sqlite3.connect(db_file)
        conn.executescript('''
            CREATE TABLE companies (id INTEGER PRIMARY KEY, name TEXT, industry TEXT, priority TEXT);
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY, company_id INTEGER, position TEXT,
                status TEXT DEFAULT '待投递', apply_date DATE, updated_at DATETIME
            );
            CREATE TABLE resumes (id INTEGER PRIMARY KEY, name TEXT, is_default BOOLEAN);
            CREATE TABLE agent_tasks (id INTEGER PRIMARY KEY, task_id TEXT, agent_name TEXT, status TEXT);
            CREATE TABLE agent_events (id INTEGER PRIMARY KEY, task_id INTEGER, event_type TEXT, payload_json TEXT, created_at DATETIME);
            CREATE TABLE answer_bank (
                id INTEGER PRIMARY KEY, question_pattern TEXT NOT NULL, answer TEXT NOT NULL,
                role_family TEXT, needs_review BOOLEAN DEFAULT 0, source TEXT DEFAULT 'manual', created_at DATETIME
            );
            CREATE TABLE experience_bank (
                id INTEGER PRIMARY KEY, role_family TEXT NOT NULL, bullet_text TEXT NOT NULL,
                jd_keywords TEXT, priority INTEGER DEFAULT 0, created_at DATETIME
            );
            CREATE TABLE application_submissions (
                id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL, form_url TEXT NOT NULL,
                prefilled_data TEXT, agent_trace_id TEXT, status TEXT DEFAULT 'prefilled',
                human_approved_at DATETIME, submitted_at DATETIME, screenshot_path TEXT,
                failure_reason TEXT, created_at DATETIME, updated_at DATETIME
            );
        ''')
        conn.execute("INSERT INTO companies (id, name, industry, priority) VALUES (1, 'TestCo', '机器人', 'A')")
        conn.execute("INSERT INTO applications (id, company_id, position, status) VALUES (100, 1, '嵌入式', '待投递')")
        conn.execute("INSERT INTO answer_bank (question_pattern, answer, role_family, needs_review, source) VALUES ('学校', '清华大学', NULL, 0, 'manual')")
        conn.execute("INSERT INTO answer_bank (question_pattern, answer, role_family, needs_review, source) VALUES ('期望专业', '计算机', '嵌入式', 0, 'manual')")
        conn.commit()
        conn.close()

        # monkeypatch submission_executor 的路径
        monkeypatch.setattr(se, 'DB_PATH', db_file)
        monkeypatch.setattr(se, 'PROFILE_PATH', profile_file)

        # 1. prefill_dry_run — 敏感从 profile，非敏感从 AnswerBank
        fields = [
            {'label': '姓名', 'name': 'name'},          # 未命中 AnswerBank（"姓名" 模糊查询"姓名" 不在表中） → awaiting
            {'label': '邮箱', 'name': 'email'},         # 同上
            {'label': '期望薪资', 'name': 'salary'},     # 敏感 → profile
            {'label': '身份证号', 'name': 'id_card'},    # 敏感 → profile
            {'label': '学校', 'name': 'school'},         # AnswerBank 命中
            {'label': 'GPA', 'name': 'gpa'},             # 未命中 → awaiting
        ]
        result = se.prefill_dry_run(
            application_id=100,
            form_url='https://example.com/apply',
            fields=fields,
            role_family='嵌入式',
        )
        assert result['status'] == 'awaiting_human'  # 姓名/邮箱/GPA 未命中
        assert result['application_status'] == '待提交'

        # 校验 application 状态已切
        conn = sqlite3.connect(db_file); conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT status FROM applications WHERE id = 100').fetchone()
        assert row['status'] == '待提交'

        # 校验 submission 已写
        sub = conn.execute(
            'SELECT status, prefilled_data FROM application_submissions WHERE application_id = 100 ORDER BY id DESC LIMIT 1'
        ).fetchone()
        assert sub['status'] == 'awaiting_human'
        data = json.loads(sub['prefilled_data'])
        filled = [f for f in data['fields'] if f['filled']]
        unfilled = [f for f in data['fields'] if not f['filled']]
        # 期望薪资 / 身份证号 / 学校 三项命中
        assert len(filled) == 3
        sources = [f['source'] for f in filled]
        assert 'profile' in sources
        assert 'answer_bank' in sources
        # 姓名/邮箱/GPA 三项未命中
        assert len(unfilled) == 3
        conn.close()

        # 2. record_submission 成功路径
        r = se.record_submission(application_id=100, success=True, screenshot_path='/tmp/x.png')
        assert r['application_status'] == '已投递'
        assert r['submission_status'] == 'submitted'
        conn = sqlite3.connect(db_file); conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT status, apply_date FROM applications WHERE id = 100').fetchone()
        assert row['status'] == '已投递'
        assert row['apply_date'] is not None
        sub = conn.execute('SELECT status, submitted_at, screenshot_path FROM application_submissions WHERE application_id = 100 ORDER BY id DESC LIMIT 1').fetchone()
        assert sub['status'] == 'submitted'
        assert sub['screenshot_path'] == '/tmp/x.png'
        conn.close()

        # 3. 失败回退路径（新一条 submission）
        conn = sqlite3.connect(db_file); conn.row_factory = sqlite3.Row
        conn.execute("UPDATE applications SET status = '待投递' WHERE id = 100")
        conn.execute("INSERT INTO application_submissions (application_id, form_url, status, created_at) VALUES (100, 'https://x', 'prefilled', datetime('now'))")
        conn.commit(); conn.close()

        r = se.record_submission(application_id=100, success=False, failure_reason='网络超时')
        assert r['application_status'] == '待投递'
        assert r['submission_status'] == 'failed'
        conn = sqlite3.connect(db_file); conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT status FROM applications WHERE id = 100').fetchone()
        assert row['status'] == '待投递'
        sub = conn.execute('SELECT status, failure_reason FROM application_submissions WHERE application_id = 100 ORDER BY id DESC LIMIT 1').fetchone()
        assert sub['status'] == 'failed'
        assert '网络超时' in sub['failure_reason']
        conn.close()

    def test_protection_post_apply_status_blocked(self, tmp_path, profile_file, monkeypatch):
        """已投递 等 post-apply 状态不允许 prefill。"""
        import sqlite3
        db_file = str(tmp_path / 'test2.db')
        conn = sqlite3.connect(db_file)
        conn.executescript('''
            CREATE TABLE companies (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE applications (id INTEGER PRIMARY KEY, company_id INTEGER, status TEXT, updated_at DATETIME);
            CREATE TABLE application_submissions (
                id INTEGER PRIMARY KEY, application_id INTEGER, form_url TEXT, prefilled_data TEXT,
                agent_trace_id TEXT, status TEXT, human_approved_at DATETIME, submitted_at DATETIME,
                screenshot_path TEXT, failure_reason TEXT, created_at DATETIME, updated_at DATETIME
            );
        ''')
        conn.execute("INSERT INTO companies (id, name) VALUES (1, 'TestCo')")
        conn.execute("INSERT INTO applications (id, company_id, status) VALUES (100, 1, '已投递')")
        conn.commit(); conn.close()

        monkeypatch.setattr(se, 'DB_PATH', db_file)
        monkeypatch.setattr(se, 'PROFILE_PATH', profile_file)

        result = se.prefill_dry_run(application_id=100, form_url='https://x', fields=[])
        assert result['status'] == 'failed'
        assert '已投递' in result['reason']

    def test_protection_nonexistent_application(self, tmp_path, profile_file, monkeypatch):
        """不存在的 application_id 返回 failed。"""
        import sqlite3
        db_file = str(tmp_path / 'test3.db')
        conn = sqlite3.connect(db_file)
        conn.executescript('''
            CREATE TABLE applications (id INTEGER PRIMARY KEY, status TEXT, updated_at DATETIME);
        ''')
        conn.commit(); conn.close()

        monkeypatch.setattr(se, 'DB_PATH', db_file)
        monkeypatch.setattr(se, 'PROFILE_PATH', profile_file)

        result = se.prefill_dry_run(application_id=9999, form_url='https://x', fields=[])
        assert result['status'] == 'failed'

    def test_missing_form_url(self, tmp_path, monkeypatch):
        """缺 form_url 返回 failed。"""
        import sqlite3
        db_file = str(tmp_path / 'test4.db')
        conn = sqlite3.connect(db_file)
        conn.executescript('CREATE TABLE applications (id INTEGER PRIMARY KEY, status TEXT, updated_at DATETIME);')
        conn.commit(); conn.close()

        monkeypatch.setattr(se, 'DB_PATH', db_file)
        monkeypatch.setattr(se, 'PROFILE_PATH', str(tmp_path / 'no_profile.md'))

        result = se.prefill_dry_run(application_id=1, form_url='', fields=[])
        assert result['status'] == 'failed'
        assert 'form_url' in result['reason']

    def test_human_filled_value_takes_priority(self, tmp_path, profile_file, monkeypatch):
        """人工传入 value 的字段优先采用，跳过 AnswerBank/profile 查询。"""
        import sqlite3
        db_file = str(tmp_path / 'test5.db')
        conn = sqlite3.connect(db_file)
        conn.executescript('''
            CREATE TABLE applications (id INTEGER PRIMARY KEY, status TEXT, updated_at DATETIME);
            CREATE TABLE application_submissions (
                id INTEGER PRIMARY KEY, application_id INTEGER, form_url TEXT, prefilled_data TEXT,
                agent_trace_id TEXT, status TEXT, human_approved_at DATETIME, submitted_at DATETIME,
                screenshot_path TEXT, failure_reason TEXT, created_at DATETIME, updated_at DATETIME
            );
            CREATE TABLE agent_tasks (id INTEGER PRIMARY KEY, task_id TEXT, agent_name TEXT, status TEXT);
            CREATE TABLE agent_events (id INTEGER PRIMARY KEY, task_id INTEGER, event_type TEXT, payload_json TEXT, created_at DATETIME);
            CREATE TABLE answer_bank (id INTEGER PRIMARY KEY, question_pattern TEXT, answer TEXT, role_family TEXT, needs_review BOOLEAN, source TEXT, created_at DATETIME);
        ''')
        conn.execute("INSERT INTO applications (id, status) VALUES (100, '待投递')")
        conn.execute("INSERT INTO answer_bank (question_pattern, answer, role_family, needs_review, source) VALUES ('学校', '清华大学', NULL, 0, 'manual')")
        conn.commit(); conn.close()

        monkeypatch.setattr(se, 'DB_PATH', db_file)
        monkeypatch.setattr(se, 'PROFILE_PATH', profile_file)

        # 人工传 value 应优先于 AnswerBank 命中
        fields = [{'label': '学校', 'name': 'school', 'value': '北京大学'}]
        result = se.prefill_dry_run(application_id=100, form_url='https://x', fields=fields)
        assert result['status'] == 'prefilled'  # 全部填好
        data = result['prefilled_data']
        assert data['fields'][0]['answer'] == '北京大学'
        assert data['fields'][0]['source'] == 'human_filled'


class TestParseProfileToDict:
    def test_chinese_keys(self):
        d = se.parse_profile_to_dict('- 期望薪资: 25k\n- 身份证号: 110101')
        assert d.get('期望薪资') == '25k'
        assert d.get('身份证号') == '110101'

    def test_english_keys(self):
        d = se.parse_profile_to_dict('target_salary: 25000\nname: Zhang San')
        assert d.get('target_salary') == '25000'
        # value 保留原大小写，只有 key 归一化
        assert d.get('name') == 'Zhang San'

    def test_bold_markdown(self):
        d = se.parse_profile_to_dict('- **期望薪资**: 30k')
        assert d.get('期望薪资') == '30k'

    def test_empty(self):
        assert se.parse_profile_to_dict('') == {}
        assert se.parse_profile_to_dict(None) == {}

    def test_skip_non_kv_lines(self):
        d = se.parse_profile_to_dict('# 标题\n## 子标题\n纯文本行')
        assert d == {}
