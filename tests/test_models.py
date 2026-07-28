"""ORM 模型的关键路径单元测试。"""
from datetime import date, datetime
import pytest

from extensions import db
from models import Company, Application, Note, Resume, Timeline, InterviewFeedback


class TestCompany:
    def test_create_minimal(self, app):
        with app.app_context():
            c = Company(name='拓竹科技', priority='B')
            db.session.add(c)
            db.session.commit()
            assert c.id is not None
            assert c.created_at is not None
            assert c.priority == 'B'

    def test_name_unique(self, app):
        with app.app_context():
            db.session.add(Company(name='重复公司', priority='B'))
            db.session.commit()
            db.session.add(Company(name='重复公司', priority='A'))
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_cascade_delete_applications(self, app):
        with app.app_context():
            c = Company(name='某公司', priority='A')
            db.session.add(c)
            db.session.commit()
            db.session.add(Application(company_id=c.id, status='已投递'))
            db.session.commit()
            assert c.applications.count() == 1

            db.session.delete(c)
            db.session.commit()
            assert Application.query.count() == 0

    def test_cascade_delete_notes(self, app):
        with app.app_context():
            c = Company(name='某公司2', priority='A')
            db.session.add(c)
            db.session.commit()
            db.session.add(Note(company_id=c.id, title='背调', content='test'))
            db.session.commit()
            db.session.delete(c)
            db.session.commit()
            assert Note.query.count() == 0


class TestApplication:
    def test_default_status(self, app):
        with app.app_context():
            c = Company(name='某公司3', priority='B')
            db.session.add(c)
            db.session.commit()
            a = Application(company_id=c.id)
            db.session.add(a)
            db.session.commit()
            assert a.status == '待投递'
            assert a.offer_status is None

    def test_relationship(self, app):
        with app.app_context():
            c = Company(name='某公司4', priority='B')
            db.session.add(c)
            db.session.commit()
            a = Application(company_id=c.id, position='嵌入式工程师', status='一面')
            db.session.add(a)
            db.session.commit()
            assert a.company.name == '某公司4'
            assert c.applications.first().position == '嵌入式工程师'


class TestResume:
    def test_default_is_default_false(self, app):
        with app.app_context():
            r = Resume(name='主简历', file_path='data/resumes/x.pdf', file_type='pdf')
            db.session.add(r)
            db.session.commit()
            assert r.is_default is False
            assert r.file_type == 'pdf'


class TestTimeline:
    def test_default_done_false(self, app):
        with app.app_context():
            t = Timeline(event_date=date(2026, 8, 1), title='秋招开始')
            db.session.add(t)
            db.session.commit()
            assert t.done is False
            assert t.end_date is None


class TestInterviewFeedback:
    def test_cascade_with_application(self, app):
        with app.app_context():
            c = Company(name='某公司5', priority='B')
            db.session.add(c)
            db.session.commit()
            a = Application(company_id=c.id, status='一面')
            db.session.add(a)
            db.session.commit()
            f = InterviewFeedback(application_id=a.id, round='一面', difficulty=3)
            db.session.add(f)
            db.session.commit()
            assert a.feedbacks.count() == 1

            db.session.delete(a)
            db.session.commit()
            assert InterviewFeedback.query.count() == 0
