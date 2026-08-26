import pytest
import json
from models import Company, Application, Resume, AnswerBank, ApplicationSubmission

def _seed_data(db_session):
    company = Company(name='测试机器人公司', industry='机器人', city='上海')
    db_session.add(company)
    db_session.flush()

    resume = Resume(
        name='2026_张三_控制算法工程师.pdf',
        file_path='data/resumes/test_resume.pdf',
        file_type='pdf'
    )
    db_session.add(resume)
    db_session.flush()

    app_record = Application(
        company_id=company.id,
        position='具身控制算法工程师',
        status='待投递',
        url='https://careers.test-robot.com/job/101',
        source_url='https://careers.test-robot.com/job/101',
        match_score=92,
        resume_id=resume.id
    )
    db_session.add(app_record)
    db_session.commit()
    return app_record.id


def test_get_autofill_payload(client, db_session):
    """测试 GET /api/agent/applications/<id>/autofill-payload 接口。"""
    app_id = _seed_data(db_session)
    res = client.get(f'/api/agent/applications/{app_id}/autofill-payload')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'success'
    assert data['application']['company_name'] == '测试机器人公司'
    assert data['application']['position'] == '具身控制算法工程师'
    assert data['application']['default_track'] == 'track_1'
    assert 'candidate' in data
    assert 'tracks' in data
    assert 'open_questions' in data
    assert len(data['open_questions']) > 0


def test_match_application_by_url(client, db_session):
    """测试 POST /api/agent/applications/match-by-url 接口。"""
    app_id = _seed_data(db_session)
    res = client.post('/api/agent/applications/match-by-url', json={
        'url': 'https://careers.test-robot.com/job/101#section=apply'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'success'
    assert data['application_id'] == app_id


def test_sync_application_submitted(client, db_session):
    """测试 POST /api/agent/applications/<id>/sync-submitted 接口。"""
    app_id = _seed_data(db_session)
    res = client.post(f'/api/agent/applications/{app_id}/sync-submitted', json={
        'page_url': 'https://careers.test-robot.com/job/101',
        'track': '控制算法',
        'open_answers': [
            {
                'pattern': '谈谈最具挑战的项目经历',
                'answer': '在四足机器人控制项目中，我设计了基于MPC的动力学控制架构。'
            }
        ],
        'filled_fields': {'name': '求职者', 'degree': '硕士'}
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'success'
    assert data['status_text'] == '已投递'

    # 验证数据库状态更新
    app_item = Application.query.get(app_id)
    assert app_item.status == '已投递'
    assert app_item.apply_date is not None

    # 验证 AnswerBank 记录
    ab = AnswerBank.query.filter_by(question_pattern='谈谈最具挑战的项目经历').first()
    assert ab is not None
    assert '四足机器人' in ab.answer

    # 验证 ApplicationSubmission
    sub = ApplicationSubmission.query.filter_by(application_id=app_id).first()
    assert sub is not None
    assert sub.status == 'submitted'
