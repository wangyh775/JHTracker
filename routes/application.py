"""投递记录路由。"""
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy.orm import joinedload
from extensions import db
from models import Application, Company, InterviewFeedback
from constants import STATUS_LIST, OFFER_STATUS_CHOICES, OFFER_STATUS_LABEL, OFFER_STATUS_BADGE
from utils import parse_date, try_int, validate_salary, validate_dates

bp = Blueprint('application', __name__)


def _safe_redirect(fallback_endpoint):
    """安全重定向：仅允许同源 referrer，否则回退到指定 endpoint。"""
    referrer = request.referrer
    if referrer:
        parsed = urlparse(referrer)
        # 仅允许同 host（本地工具通常为 localhost / 127.0.0.1）
        if parsed.host in ('localhost', '127.0.0.1', request.host):
            return redirect(referrer)
    return redirect(url_for(fallback_endpoint))


@bp.route('/applications')
def app_list():
    page = request.args.get('page', 1, type=int)
    st = request.args.get('status', '')
    ch = request.args.get('channel', '')
    query = Application.query.options(joinedload(Application.company))
    if st:
        query = query.filter_by(status=st)
    if ch:
        query = query.filter_by(channel=ch)
    apps = query.order_by(Application.updated_at.desc()).paginate(page=page, per_page=30)
    channels = db.session.query(
        Application.channel, db.func.count(Application.id)
    ).group_by(Application.channel).all()
    return render_template('applications.html', apps=apps, channels=channels,
                           status_list=STATUS_LIST)


@bp.route('/applications/add', methods=['POST'])
def app_add():
    try:
        salary_min = try_int(request.form.get('salary_min'))
        salary_max = try_int(request.form.get('salary_max'))
        validate_salary(salary_min, salary_max)
        apply_date = parse_date(request.form.get('apply_date', ''))
        deadline = parse_date(request.form.get('deadline', ''))
        validate_dates(apply_date, deadline)
        a = Application(
            company_id=request.form['company_id'],
            position=request.form.get('position', '').strip(),
            channel=request.form.get('channel', '').strip(),
            status=request.form.get('status', '待投递'),
            apply_date=apply_date,
            deadline=deadline,
            salary_min=salary_min,
            salary_max=salary_max,
            job_desc=request.form.get('job_desc', ''),
            url=request.form.get('url', '').strip(),
        )
        db.session.add(a)
        db.session.commit()
    except ValueError:
        pass
    return _safe_redirect('application.app_list')


@bp.route('/applications/<int:a_id>/status', methods=['POST'])
def app_status(a_id):
    a = Application.query.get_or_404(a_id)
    a.status = request.form['status']
    if 'feedback' in request.form:
        a.feedback = request.form['feedback']
    db.session.commit()
    return _safe_redirect('application.app_list')


@bp.route('/applications/<int:a_id>/offer_status', methods=['POST'])
def app_offer_status(a_id):
    a = Application.query.get_or_404(a_id)
    a.offer_status = request.form.get('offer_status', 'pending')
    db.session.commit()
    return _safe_redirect('application.compare')


@bp.route('/applications/<int:a_id>/delete', methods=['POST'])
def app_delete(a_id):
    a = Application.query.get_or_404(a_id)
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for('application.app_list'))


@bp.route('/applications/<int:a_id>/feedback/add', methods=['POST'])
def feedback_add(a_id):
    a = Application.query.get_or_404(a_id)
    f = InterviewFeedback(
        application_id=a.id,
        interviewer=request.form.get('interviewer', '').strip(),
        interview_date=parse_date(request.form.get('interview_date', '')),
        round=request.form.get('round', ''),
        difficulty=try_int(request.form.get('difficulty')),
        self_rating=try_int(request.form.get('self_rating')),
        questions=request.form.get('questions', ''),
        improvement=request.form.get('improvement', ''),
    )
    db.session.add(f)
    db.session.commit()
    return _safe_redirect('application.app_list')


@bp.route('/applications/<int:a_id>/feedback/<int:f_id>/delete', methods=['POST'])
def feedback_delete(a_id, f_id):
    f = InterviewFeedback.query.get_or_404(f_id)
    db.session.delete(f)
    db.session.commit()
    return _safe_redirect('application.app_list')


@bp.route('/compare')
def compare():
    offers = Application.query.options(joinedload(Application.company)).filter_by(
        status='Offer'
    ).order_by(Application.salary_max.desc().nullslast()).all()
    return render_template('compare.html', offers=offers,
                           offer_choices=OFFER_STATUS_CHOICES,
                           offer_labels=OFFER_STATUS_LABEL,
                           offer_badges=OFFER_STATUS_BADGE)
