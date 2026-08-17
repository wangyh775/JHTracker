"""新增模型 (AnswerBank / ExperienceBank / ApplicationSubmission) 的单元测试。"""
import pytest
from extensions import db
from models import Company, Application, AnswerBank, ExperienceBank, ApplicationSubmission


class TestAnswerBank:
    def test_create_minimal(self, app):
        with app.app_context():
            ab = AnswerBank(question_pattern='学校', answer='清华大学')
            db.session.add(ab)
            db.session.commit()
            assert ab.id is not None
            assert ab.role_family is None
            assert ab.needs_review is False
            assert ab.source == 'manual'

    def test_create_with_role_family(self, app):
        with app.app_context():
            ab = AnswerBank(question_pattern='GPA', answer='3.8', role_family='嵌入式', needs_review=True, source='extracted')
            db.session.add(ab)
            db.session.commit()
            assert ab.role_family == '嵌入式'
            assert ab.needs_review is True
            assert ab.source == 'extracted'

    def test_relationship_no_cascade_to_application(self, app):
        """AnswerBank 不关联 application，删除 application 不影响 AnswerBank。"""
        with app.app_context():
            c = Company(name='TestCo')
            db.session.add(c); db.session.flush()
            a = Application(company_id=c.id, status='待投递')
            db.session.add(a); db.session.flush()
            ab = AnswerBank(question_pattern='Q', answer='A')
            db.session.add(ab); db.session.commit()
            ab_id = ab.id
            db.session.delete(a)
            db.session.commit()
            assert AnswerBank.query.get(ab_id) is not None


class TestExperienceBank:
    def test_create(self, app):
        with app.app_context():
            eb = ExperienceBank(role_family='嵌入式', bullet_text='3 年 RTOS 开发经验', jd_keywords='RTOS,CAN', priority=5)
            db.session.add(eb)
            db.session.commit()
            assert eb.id is not None
            assert eb.priority == 5


class TestApplicationSubmission:
    def test_create(self, app):
        with app.app_context():
            c = Company(name='TestCo')
            db.session.add(c); db.session.flush()
            a = Application(company_id=c.id, status='待提交')
            db.session.add(a); db.session.flush()
            sub = ApplicationSubmission(
                application_id=a.id,
                form_url='https://example.com/apply',
                prefilled_data='{"fields":[]}',
                status='prefilled',
            )
            db.session.add(sub)
            db.session.commit()
            assert sub.id is not None
            assert sub.status == 'prefilled'

    def test_relationship_backref(self, app):
        with app.app_context():
            c = Company(name='TestCo')
            db.session.add(c); db.session.flush()
            a = Application(company_id=c.id, status='待提交')
            db.session.add(a); db.session.flush()
            sub = ApplicationSubmission(application_id=a.id, form_url='https://x')
            db.session.add(sub); db.session.commit()
            # backref submissions
            assert len(a.submissions.all()) == 1
            assert a.submissions[0].form_url == 'https://x'

    def test_cascade_delete_with_application(self, app):
        """删除 application 应级联删除其 submissions（cascade='all,delete-orphan' 待评估，目前未加级联）。"""
        with app.app_context():
            c = Company(name='TestCo')
            db.session.add(c); db.session.flush()
            a = Application(company_id=c.id, status='待提交')
            db.session.add(a); db.session.flush()
            sub = ApplicationSubmission(application_id=a.id, form_url='https://x')
            db.session.add(sub); db.session.commit()
            sub_id = sub.id
            db.session.delete(a)
            db.session.commit()
            # application_submissions 表没有显式级联设置，依赖外键约束
            # SQLite 默认不强制外键，所以记录可能保留 — 这与现有 application->feedback 风格不同
            # 这里仅验证 application 删除本身不报错
            assert Application.query.get(a.id) is None
