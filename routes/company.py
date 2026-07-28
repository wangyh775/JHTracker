"""公司清单路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import case, or_
from extensions import db
from models import Company, Application, Note
from constants import INDUSTRIES, CITIES, COMPANY_TYPES
from utils import validate_salary, try_int

bp = Blueprint('company', __name__)


@bp.route('/companies')
def company_list():
    page = request.args.get('page', 1, type=int)
    ind = request.args.getlist('industry')
    ct = request.args.getlist('city')
    pr = request.args.getlist('priority')
    ctype = request.args.getlist('company_type')
    q = request.args.get('q', '')

    query = Company.query
    if ind:
        query = query.filter(Company.industry.in_(ind))
    if ct:
        query = query.filter(or_(*[Company.city.contains(c) for c in ct]))
    if pr:
        query = query.filter(Company.priority.in_(pr))
    if ctype:
        query = query.filter(Company.company_type.in_(ctype))
    if q:
        query = query.filter(Company.name.contains(q) | Company.match_reason.contains(q))

    # NULL priority 排最后; S > A > B > C (非字母序)
    priority_order = case(
        {'S': 0, 'A': 1, 'B': 2, 'C': 3},
        value=Company.priority,
        else_=4
    )
    query = query.order_by(priority_order, Company.name)
    companies = query.paginate(page=page, per_page=40)

    # 统计卡片数据
    total = Company.query.count()
    scored = Company.query.filter(Company.score.isnot(None)).count()
    high = Company.query.filter(Company.score >= 70).count()
    mid = Company.query.filter(Company.score >= 40, Company.score < 70).count()
    low = Company.query.filter(Company.score < 40).count()

    return render_template('companies.html', companies=companies,
                           industries=INDUSTRIES, cities=CITIES,
                           company_types=COMPANY_TYPES,
                           stats={'total': total, 'scored': scored,
                                  'high': high, 'mid': mid, 'low': low})


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
            scale=request.form.get('scale', '').strip(),
            financing_stage=request.form.get('financing_stage', '').strip(),
            tags=request.form.get('tags', '').strip(),
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
        c.scale = request.form.get('scale', c.scale or '').strip()
        c.financing_stage = request.form.get('financing_stage', c.financing_stage or '').strip()
        c.tags = request.form.get('tags', c.tags or '').strip()
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


@bp.route('/companies/score', methods=['POST'])
def company_score_all():
    """触发后台批量 AI 评分（异步）。"""
    from flask import flash, jsonify
    import subprocess
    import os

    from dotenv import load_dotenv
    load_dotenv()

    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'ai_scorer.py')
    try:
        # 后台异步执行
        subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        flash('✅ 评分已启动，请观察进度条等待完成', 'success')
    except Exception as e:
        flash(f'❌ 启动评分失败：{e}', 'danger')

    return redirect(url_for('company.company_list'))


@bp.route('/companies/<int:c_id>/score', methods=['POST'])
def company_score_one(c_id):
    """触发单公司 AI 重评分（异步）。

    复用 ai_scorer.py 的 --company-id 模式，1 家公司 1 次 LLM 调用。
    写入同一个 .score_progress.json，前端复用现有进度条。
    """
    from flask import jsonify
    import subprocess
    import os
    import json

    from dotenv import load_dotenv
    load_dotenv()

    # 校验公司存在
    c = Company.query.get_or_404(c_id)

    # 防重入：已有评分任务在跑
    progress_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', '.score_progress.json')
    try:
        with open(progress_file) as f:
            prog = json.load(f)
        if prog.get('status') == 'running':
            return jsonify({'ok': False, 'msg': '已有评分任务进行中，请等待完成'}), 409
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # 重置进度为 starting
    try:
        with open(progress_file, 'w') as f:
            json.dump({'current': 0, 'total': 1, 'name': c.name, 'score': 0, 'status': 'starting'}, f)
    except OSError:
        pass

    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'ai_scorer.py')
    try:
        subprocess.Popen(
            ['python', script_path, '--company-id', str(c_id)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'启动失败：{e}'}), 500

    return jsonify({'ok': True, 'msg': f'已触发「{c.name}」重评分', 'company_id': c_id})



@bp.route('/api/score-progress')
def api_score_progress():
    """返回评分进度 JSON。"""
    from flask import jsonify
    import json
    import os
    progress_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', '.score_progress.json')
    try:
        with open(progress_file) as f:
            data = json.load(f)
        return jsonify(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'current': 0, 'total': 0, 'name': '', 'score': 0, 'status': 'idle'})
