"""关键路由的单元测试：覆盖 200 / 302 / 404 等关键响应。"""
from datetime import date
import pytest
from extensions import db
from models import Company, Application, Timeline


class TestPublicPages:
    def test_dashboard_ok(self, client):
        r = client.get('/')
        assert r.status_code == 200

    def test_companies_list_ok(self, client):
        r = client.get('/companies')
        assert r.status_code == 200

    def test_applications_list_ok(self, client):
        r = client.get('/applications')
        assert r.status_code == 200

    def test_notes_list_ok(self, client):
        r = client.get('/notes')
        assert r.status_code == 200

    def test_resumes_list_ok(self, client):
        r = client.get('/resumes')
        assert r.status_code == 200

    def test_timeline_ok(self, client):
        r = client.get('/timeline')
        assert r.status_code == 200

    def test_compare_ok(self, client):
        r = client.get('/compare')
        assert r.status_code == 200

    def test_import_ok(self, client):
        r = client.get('/import')
        assert r.status_code == 200

    def test_backup_ok(self, client):
        r = client.get('/backup')
        assert r.status_code == 200


class TestCompanyRoutes:
    def test_company_detail_404_for_missing(self, client):
        r = client.get('/companies/99999')
        assert r.status_code == 404

    def test_company_detail_ok(self, client, app):
        with app.app_context():
            c = Company(name='某测试公司', priority='A', city='深圳')
            db.session.add(c)
            db.session.commit()
            cid = c.id
        r = client.get(f'/companies/{cid}')
        assert r.status_code == 200

    def test_company_add_redirects(self, client):
        r = client.post('/companies/add', data={
            'name': '测试新增公司',
            'priority': 'B',
            'industry': '3D打印',
            'city': '深圳',
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_company_search_api_empty(self, client):
        r = client.get('/api/companies/search?q=')
        assert r.status_code == 200
        assert r.get_json() == []

    def test_company_search_api_returns_results(self, client, app):
        with app.app_context():
            db.session.add(Company(name='腾讯科技', priority='A'))
            db.session.add(Company(name='腾讯音乐', priority='B'))
            db.session.commit()
        r = client.get('/api/companies/search?q=腾讯')
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 2


class TestApplicationRoutes:
    def test_application_status_update(self, client, app):
        with app.app_context():
            c = Company(name='投递测试公司', priority='B')
            db.session.add(c)
            db.session.commit()
            a = Application(company_id=c.id, status='待投递')
            db.session.add(a)
            db.session.commit()
            aid = a.id
        r = client.post(f'/applications/{aid}/status', data={
            'status': '已投递',
            'feedback': '已投递简历',
        }, follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            assert db.session.get(Application, aid).status == '已投递'


class TestTimelineRoutes:
    def test_timeline_add(self, client):
        r = client.post('/timeline/add', data={
            'event_date': '2026-08-15',
            'event_type': 'milestone',
            'title': '秋招开启',
            'description': '秋招正式开始',
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_timeline_toggle(self, client, app):
        with app.app_context():
            t = Timeline(event_date=date(2026, 8, 20), title='测试节点')
            db.session.add(t)
            db.session.commit()
            tid = t.id
            assert t.done is False
        r = client.post(f'/timeline/{tid}/toggle', follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            assert db.session.get(Timeline, tid).done is True
