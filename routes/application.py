"""投递记录路由。"""
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import joinedload
from datetime import datetime
from extensions import db
from models import Application, Company, InterviewFeedback
from constants import STATUS_LIST, OFFER_STATUS_CHOICES, OFFER_STATUS_LABEL, OFFER_STATUS_BADGE, POST_APPLY_STATUS_LIST, STAGED_STATUS_LIST
from utils import parse_date, try_int, validate_salary, validate_dates
from services.settings import load_settings, save_settings, is_archive_auto_enabled, get_archive_stale_days
from services.archive import (
    query_stale_applications, run_auto_archive,
    archive_applications, archive_one, unarchive_one,
)

bp = Blueprint('application', __name__)


def _safe_redirect(fallback_endpoint):
    """安全重定向：仅允许同源 referrer，否则回退到指定 endpoint。"""
    referrer = request.referrer
    if referrer:
        parsed = urlparse(referrer)
        if parsed.hostname in ('localhost', '127.0.0.1', request.host):
            return redirect(referrer)
    return redirect(url_for(fallback_endpoint))


def _maybe_auto_archive():
    """若启用自动归档，按节流规则执行。"""
    if is_archive_auto_enabled():
        run_auto_archive(get_archive_stale_days())


@bp.route('/to-apply')
def to_apply_list():
    page = request.args.get('page', 1, type=int)
    ch = request.args.get('channel', '')
    query = Application.query.options(joinedload(Application.company), joinedload(Application.resume)).filter(
        Application.is_archived.is_(False),
        Application.status == '待投递'
    )
    if ch:
        query = query.filter_by(channel=ch)
    apps = query.order_by(Application.updated_at.desc()).paginate(page=page, per_page=30)
    channels = db.session.query(
        Application.channel, db.func.count(Application.id)
    ).filter(Application.is_archived.is_(False), Application.status == '待投递').group_by(Application.channel).all()
    return render_template('to_apply.html', apps=apps, channels=channels)


@bp.route('/applications')
def app_list():
    _maybe_auto_archive()
    page = request.args.get('page', 1, type=int)
    st = request.args.get('status', '')
    ch = request.args.get('channel', '')
    view = request.args.get('view', 'active')
    query = Application.query.options(joinedload(Application.company), joinedload(Application.resume))
    if view == 'archived':
        query = query.filter_by(is_archived=True)
    else:
        query = query.filter(
            Application.is_archived.is_(False),
            ~Application.status.in_(STAGED_STATUS_LIST)
        )
    if st:
        query = query.filter_by(status=st)
    if ch:
        query = query.filter_by(channel=ch)
    apps = query.order_by(Application.updated_at.desc()).paginate(page=page, per_page=30)
    channels = db.session.query(
        Application.channel, db.func.count(Application.id)
    ).filter_by(is_archived=(view == 'archived')).group_by(Application.channel).all()
    settings = load_settings()
    stale_count = len(query_stale_applications(settings['archive_stale_days']))
    post_apply_statuses = ['已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer', '已拒']
    return render_template('applications.html', apps=apps, channels=channels,
                           status_list=post_apply_statuses, view=view,
                           archive_settings=settings, stale_count=stale_count)


@bp.route('/applications/settings', methods=['POST'])
def app_settings():
    days = try_int(request.form.get('archive_stale_days'), 15)
    auto = request.form.get('archive_auto_enabled') == '1'
    save_settings(archive_stale_days=max(1, days or 15), archive_auto_enabled=auto)
    flash('归档设置已保存')
    return redirect(url_for('application.app_list'))


@bp.route('/applications/archive/run', methods=['POST'])
def app_archive_run():
    days = get_archive_stale_days()
    count = archive_applications(query_stale_applications(days))
    flash(f'已归档 {count} 条投递记录')
    return redirect(url_for('application.app_list'))


@bp.route('/applications/<int:a_id>/archive', methods=['POST'])
def app_archive(a_id):
    if archive_one(a_id):
        flash('已归档')
    return _safe_redirect('application.app_list')


@bp.route('/applications/<int:a_id>/unarchive', methods=['POST'])
def app_unarchive(a_id):
    if unarchive_one(a_id):
        flash('已恢复')
    return redirect(url_for('application.app_list', view='archived'))


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
            resume_id=try_int(request.form.get('resume_id')),
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
    a.updated_at = datetime.now()
    db.session.commit()
    return _safe_redirect('application.app_list')


@bp.route('/applications/<int:a_id>/offer_status', methods=['POST'])
def app_offer_status(a_id):
    a = Application.query.get_or_404(a_id)
    a.offer_status = request.form.get('offer_status', 'pending')
    a.updated_at = datetime.now()
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
    a.updated_at = datetime.now()
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
        status='Offer', is_archived=False
    ).order_by(Application.salary_max.desc().nullslast()).all()
    return render_template('compare.html', offers=offers,
                           offer_choices=OFFER_STATUS_CHOICES,
                           offer_labels=OFFER_STATUS_LABEL,
                           offer_badges=OFFER_STATUS_BADGE)
