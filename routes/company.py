"""公司清单路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Company, Application, Note
from constants import INDUSTRIES, CITIES
from utils import validate_salary, try_int

bp = Blueprint('company', __name__)


@bp.route('/companies')
def company_list():
    page = request.args.get('page', 1, type=int)
    ind = request.args.get('industry', '')
    ct = request.args.get('city', '')
    pr = request.args.get('priority', '')
    q = request.args.get('q', '')

    query = Company.query
    if ind:
        query = query.filter_by(industry=ind)
    if ct:
        query = query.filter(Company.city.contains(ct))
    if pr:
        query = query.filter_by(priority=pr)
    if q:
        query = query.filter(Company.name.contains(q) | Company.match_reason.contains(q))

    # NULL priority 排最后
    query = query.order_by(Company.priority.is_(None), Company.priority, Company.name)
    companies = query.paginate(page=page, per_page=40)
    return render_template('companies.html', companies=companies,
                           industries=INDUSTRIES, cities=CITIES)


@bp.route('/companies/<int:c_id>')
def company_detail(c_id):
    c = Company.query.get_or_404(c_id)
    apps = c.applications.order_by(Application.updated_at.desc()).all()
    notes = c.notes.order_by(Note.created_at.desc()).all()
    return render_template('company_detail.html', company=c, apps=apps, notes=notes)


@bp.route('/companies/add', methods=['POST'])
def company_add():
    try:
        salary_min = try_int(request.form.get('salary_min'))
        salary_max = try_int(request.form.get('salary_max'))
        validate_salary(salary_min, salary_max)
        c = Company(
            name=request.form['name'].strip(),
            industry=request.form.get('industry', '').strip(),
            city=request.form.get('city', '').strip(),
            sub_city=request.form.get('sub_city', '').strip(),
            job_type=request.form.get('job_type', '').strip(),
            match_reason=request.form.get('match_reason', '').strip(),
            priority=request.form.get('priority', 'B'),
            website=request.form.get('website', '').strip(),
            source_list=request.form.get('source_list', '').strip(),
            salary_min=salary_min,
            salary_max=salary_max,
        )
        db.session.add(c)
        db.session.commit()
    except ValueError:
        pass
    return redirect(url_for('company.company_list'))


@bp.route('/companies/<int:c_id>/edit', methods=['POST'])
def company_edit(c_id):
    c = Company.query.get_or_404(c_id)
    try:
        salary_min = try_int(request.form.get('salary_min'))
        salary_max = try_int(request.form.get('salary_max'))
        validate_salary(salary_min, salary_max)
        c.name = request.form.get('name', c.name).strip()
        c.industry = request.form.get('industry', c.industry).strip()
        c.city = request.form.get('city', c.city).strip()
        c.sub_city = request.form.get('sub_city', c.sub_city).strip()
        c.job_type = request.form.get('job_type', c.job_type).strip()
        c.match_reason = request.form.get('match_reason', c.match_reason).strip()
        c.priority = request.form.get('priority', c.priority)
        c.website = request.form.get('website', c.website).strip()
        c.salary_min = salary_min
        c.salary_max = salary_max
        db.session.commit()
    except ValueError:
        pass
    return redirect(url_for('company.company_detail', c_id=c_id))


@bp.route('/companies/<int:c_id>/delete', methods=['POST'])
def company_delete(c_id):
    c = Company.query.get_or_404(c_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for('company.company_list'))


@bp.route('/api/companies/search')
def api_company_search():
    from flask import jsonify
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    cs = Company.query.filter(Company.name.contains(q)).limit(10).all()
    return jsonify([{'id': c.id, 'name': c.name, 'city': c.city, 'industry': c.industry} for c in cs])
