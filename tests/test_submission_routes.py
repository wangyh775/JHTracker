"""网申预填路由 + AnswerBank 路由的集成测试。"""
import json
import pytest
from extensions import db
from models import Company, Application, AnswerBank, ApplicationSubmission


@pytest.fixture
def setup_submission_data(app):
    """构造测试数据：1 公司 + 1 待提交 application + 1 已预填 submission。"""
    with app.app_context():
        c = Company(name='TestCo', priority='A', industry='机器人')
        db.session.add(c)
        db.session.flush()
        a = Application(company_id=c.id, position='嵌入式工程师', status='待提交')
        db.session.add(a)
        db.session.flush()
        sub = ApplicationSubmission(
            application_id=a.id,
            form_url='https://example.com/apply',
            prefilled_data=json.dumps({
                'fields': [
                    {'selector': {'label': '姓名', 'name': 'name'}, 'classified_as': 'benign',
                     'answer': '张三', 'source': 'answer_bank', 'filled': True},
                    {'selector': {'label': '期望薪资', 'name': 'salary'}, 'classified_as': 'compensation',
                     'answer': '25k', 'source': 'profile', 'filled': True},
                    {'selector': {'label': 'GPA', 'name': 'gpa'}, 'classified_as': 'benign',
                     'answer': None, 'source': 'missing', 'filled': False},
                ],
                'awaiting_human_items': ['非敏感字段「GPA」AnswerBank 未命中，请补填'],
            }, ensure_ascii=False),
            status='awaiting_human',
        )
        db.session.add(sub)

        # AnswerBank 数据
        db.session.add(AnswerBank(question_pattern='学校', answer='清华大学', role_family=None, source='manual'))
        db.session.add(AnswerBank(question_pattern='GPA', answer='3.8', role_family='嵌入式', source='manual', needs_review=True))

        db.session.commit()
        return a.id, sub.id


class TestSubmissionRoutes:
    def test_submissions_list_ok(self, client):
        r = client.get('/submissions')
        assert r.status_code == 200

    def test_submissions_list_shows_pending(self, client, setup_submission_data):
        app_id, _ = setup_submission_data
        r = client.get('/submissions')
        assert r.status_code == 200
        # 页面应含公司名 TestCo
        assert b'TestCo' in r.data
        # 应含「待提交」徽章
        assert '待提交'.encode() in r.data

    def test_submission_detail_ok(self, client, setup_submission_data):
        app_id, _ = setup_submission_data
        r = client.get(f'/submissions/{app_id}')
        assert r.status_code == 200
        # 应展示预填字段表
        assert '姓名'.encode() in r.data
        assert '期望薪资'.encode() in r.data
        assert 'GPA'.encode() in r.data

    def test_submission_detail_404_for_missing(self, client):
        r = client.get('/submissions/99999')
        assert r.status_code == 404

    def test_submission_submit_marks_applied(self, client, app, setup_submission_data):
        """提交后 application 状态切到 已投递。"""
        app_id, _ = setup_submission_data
        r = client.post(f'/submissions/{app_id}/submit', follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            a = Application.query.get(app_id)
            assert a.status == '已投递'
            sub = ApplicationSubmission.query.filter_by(application_id=app_id).order_by(ApplicationSubmission.id.desc()).first()
            assert sub.status == 'submitted'

    def test_submission_fail_reverts(self, client, app, setup_submission_data):
        """失败回退到 待投递。"""
        app_id, _ = setup_submission_data
        r = client.post(f'/submissions/{app_id}/fail', data={'failure_reason': 'CAPTCHA 拦截'}, follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            a = Application.query.get(app_id)
            assert a.status == '待投递'
            sub = ApplicationSubmission.query.filter_by(application_id=app_id).order_by(ApplicationSubmission.id.desc()).first()
            assert sub.status == 'failed'
            assert 'CAPTCHA 拦截' in sub.failure_reason

    def test_submit_blocked_for_wrong_status(self, client, app, setup_submission_data):
        """非 待提交 状态不允许 submit。"""
        app_id, _ = setup_submission_data
        with app.app_context():
            a = Application.query.get(app_id)
            a.status = '已投递'
            db.session.commit()
        r = client.post(f'/submissions/{app_id}/submit', follow_redirects=False)
        assert r.status_code == 302  # 重定向到 detail 页带 flash 错误


class TestAnswerBankRoutes:
    def test_answer_bank_list_ok(self, client):
        r = client.get('/answer-bank')
        assert r.status_code == 200

    def test_answer_bank_list_shows_items(self, client, setup_submission_data):
        r = client.get('/answer-bank')
        assert r.status_code == 200
        assert '清华大学'.encode() in r.data
        assert '3.8'.encode() in r.data

    def test_answer_bank_filter_by_role_family(self, client, setup_submission_data):
        r = client.get('/answer-bank?role_family=嵌入式')
        assert r.status_code == 200
        assert '3.8'.encode() in r.data
        # 通用答案不应该出现（按 role_family 精确匹配）
        assert '清华大学'.encode() not in r.data

    def test_answer_bank_delete_requires_confirm(self, client, setup_submission_data):
        r = client.post('/answer-bank/1/delete', data={}, follow_redirects=False)
        assert r.status_code == 302  # 重定向带错误 flash

    def test_answer_bank_delete_with_confirm(self, client, app, setup_submission_data):
        # 取一条 answer id
        with app.app_context():
            ab = AnswerBank.query.first()
            ab_id = ab.id
        r = client.post(f'/answer-bank/{ab_id}/delete', data={'confirm': '1'}, follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            assert AnswerBank.query.get(ab_id) is None

    def test_answer_bank_delete_404_for_missing(self, client):
        r = client.post('/answer-bank/99999/delete', data={'confirm': '1'}, follow_redirects=False)
        assert r.status_code == 404
