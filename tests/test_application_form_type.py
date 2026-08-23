"""applications 表新增 form_type 与 source_platform 字段的测试。

验证字段写入与读取、create_application 默认值、get_application 返回新字段。
"""
import sqlite3
import json
import pytest

# mcp 包未安装时跳过 MCP server 相关测试（与现有 test_agent_api.py 一致）
try:
    import mcp  # noqa: F401
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class TestApplicationFormTypeField:
    def test_form_type_persisted_via_create_application(self, app, db_session):
        """create_application 写入 form_type，get_application 能读回。"""
        from models import Company, Application

        with app.app_context():
            c = Company(name='FormTypeCo', priority='A')
            db_session.add(c)
            db_session.commit()

            a = Application(
                company_id=c.id, position='嵌入式', status='待投递',
                form_type='structured', source_platform='beisen',
            )
            db_session.add(a)
            db_session.commit()
            aid = a.id

            # 重新查询验证持久化
            reloaded = db_session.get(Application, aid)
            assert reloaded.form_type == 'structured'
            assert reloaded.source_platform == 'beisen'

    def test_form_type_nullable(self, app, db_session):
        """旧数据未设置 form_type 时应为 None，兼容性。"""
        from models import Company, Application

        with app.app_context():
            c = Company(name='OldCo', priority='B')
            db_session.add(c)
            db_session.commit()

            a = Application(company_id=c.id, position='旧岗位', status='待投递')
            db_session.add(a)
            db_session.commit()

            reloaded = db_session.get(Application, a.id)
            assert reloaded.form_type is None
            assert reloaded.source_platform is None


class TestCreateApplicationMcpDefaults:
    @pytest.mark.skipif(not MCP_AVAILABLE, reason="mcp package not installed")
    def test_form_type_defaults_to_open_question_when_not_provided(self):
        """create_application 未传 form_type 时默认 open_question。

        通过直接调用 mcp_server.create_application 验证（mock DB）。
        """
        # 构造内存 DB + 表结构
        import tempfile, os
        db_file = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(db_file)
        conn.executescript('''
            CREATE TABLE companies (id INTEGER PRIMARY KEY, name TEXT, priority TEXT);
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY, company_id INTEGER, position TEXT, status TEXT,
                channel TEXT, job_desc TEXT, url TEXT, match_score INTEGER, agent_reason TEXT,
                agent_task_id TEXT, source_url TEXT, resume_id INTEGER,
                form_type TEXT, source_platform TEXT,
                is_archived INTEGER DEFAULT 0, created_at DATETIME, updated_at DATETIME
            );
            INSERT INTO companies (id, name, priority) VALUES (1, 'TestCo', 'A');
        ''')
        conn.commit()
        conn.close()

        # mock DB_PATH 指向临时 DB
        import mcp_server
        orig_db_path = mcp_server.DB_PATH
        mcp_server.DB_PATH = db_file
        try:
            result = json.loads(mcp_server.create_application(
                company_id=1,
                position='测试岗位',
                source_url='https://example.com/job/1',
            ))
            assert result['status'] == 'success'
            assert result['created'] is True
            assert result['application']['form_type'] == 'open_question'
            assert result['application']['source_platform'] is None
        finally:
            mcp_server.DB_PATH = orig_db_path
            os.unlink(db_file)

    @pytest.mark.skipif(not MCP_AVAILABLE, reason="mcp package not installed")
    def test_form_type_and_source_platform_persisted(self):
        """create_application 传入 form_type + source_platform 时正确持久化。"""
        import tempfile, os
        db_file = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(db_file)
        conn.executescript('''
            CREATE TABLE companies (id INTEGER PRIMARY KEY, name TEXT, priority TEXT);
            CREATE TABLE resumes (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE decision_feedbacks (id INTEGER PRIMARY KEY, application_id INTEGER);
            CREATE TABLE interview_feedbacks (id INTEGER PRIMARY KEY, application_id INTEGER);
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY, company_id INTEGER, position TEXT, status TEXT,
                channel TEXT, job_desc TEXT, url TEXT, match_score INTEGER, agent_reason TEXT,
                agent_task_id TEXT, source_url TEXT, resume_id INTEGER,
                form_type TEXT, source_platform TEXT,
                is_archived INTEGER DEFAULT 0, created_at DATETIME, updated_at DATETIME
            );
            INSERT INTO companies (id, name, priority) VALUES (1, 'TestCo', 'A');
        ''')
        conn.commit()
        conn.close()

        import mcp_server
        orig_db_path = mcp_server.DB_PATH
        mcp_server.DB_PATH = db_file
        try:
            result = json.loads(mcp_server.create_application(
                company_id=1,
                position='北森岗位',
                source_url='https://xyz.beisen.com/jobs/1',
                form_type='structured',
                source_platform='beisen',
            ))
            assert result['application']['form_type'] == 'structured'
            assert result['application']['source_platform'] == 'beisen'

            # get_application 能读回
            get_result = json.loads(mcp_server.get_application(application_id=result['application']['id']))
            assert get_result['application']['form_type'] == 'structured'
            assert get_result['application']['source_platform'] == 'beisen'
        finally:
            mcp_server.DB_PATH = orig_db_path
            os.unlink(db_file)
