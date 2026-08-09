"""网申预填审核路由：人审 + 提交回写。"""
import json
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models import Application, ApplicationSubmission, AnswerBank, Company, Resume
from constants import (
    SUBMISSION_STATUSES,
    SUBMISSION_STATUS_BADGE,
    SUBMISSION_STATUS_LABEL,
    STATUS_BADGE,
)
from utils import role_family_normalize

bp = Blueprint('submission', __name__)


@bp.route('/submissions')
def submission_list():
    """待提交预填审核列表。

    Agent 预填完成后，application.status 切换到 待提交。
    本页列出所有 待提交 状态的 application + 其最新 submission 记录。
    """
    apps = (
        Application.query
        .filter(Application.is_archived.is_(False), Application.status == '待提交')
        .order_by(Application.updated_at.desc())
        .all()
    )

    # 预取每条 application 对应的最新 submission（一条 SQL）
    submissions_map = {}
    submissions_data_map = {}  # 解析后的 prefilled_data dict
    if apps:
        app_ids = [a.id for a in apps]
        rows = (
            db.session.query(ApplicationSubmission)
            .filter(ApplicationSubmission.application_id.in_(app_ids))
            .order_by(ApplicationSubmission.application_id, ApplicationSubmission.id.desc())
            .all()
        )
        seen = set()
        for r in rows:
            if r.application_id in seen:
                continue
            seen.add(r.application_id)
            submissions_map[r.application_id] = r
            parsed = None
            if r.prefilled_data:
                try:
                    parsed = json.loads(r.prefilled_data)
                except (json.JSONDecodeError, TypeError):
                    parsed = None
            submissions_data_map[r.application_id] = parsed

    return render_template(
        'submissions.html',
        apps=apps,
        submissions_map=submissions_map,
        submissions_data_map=submissions_data_map,
        submission_status_badge=SUBMISSION_STATUS_BADGE,
        submission_status_label=SUBMISSION_STATUS_LABEL,
        status_badge=STATUS_BADGE,
    )


@bp.route('/submissions/<int:a_id>')
def submission_detail(a_id):
    """单条 application 的预填详情。"""
    app = Application.query.get_or_404(a_id)
    sub = (
        ApplicationSubmission.query
        .filter_by(application_id=a_id)
        .order_by(ApplicationSubmission.id.desc())
        .first()
    )
    prefilled_data = None
    if sub and sub.prefilled_data:
        try:
            prefilled_data = json.loads(sub.prefilled_data)
        except (json.JSONDecodeError, TypeError):
            prefilled_data = None
    return render_template(
        'submission_detail.html',
        app=app,
        sub=sub,
        prefilled_data=prefilled_data,
        submission_status_badge=SUBMISSION_STATUS_BADGE,
        submission_status_label=SUBMISSION_STATUS_LABEL,
    )


@bp.route('/submissions/<int:a_id>/submit', methods=['POST'])
def submission_submit(a_id):
    """人类在真实页面提交后，回写为已投递。

    必须人工点过真实页面的「提交」按钮后才能调用此接口。

    走 SQLAlchemy 直写，与 submission_executor.record_submission 的 raw-sqlite 路径
    保持业务等价（该 raw-sqlite 路径仅供 MCP / Agent 在 Flask 上下文外调用）。
    """
    app = Application.query.get_or_404(a_id)
    if app.status != '待提交':
        flash(f'当前状态 {app.status} 不允许此操作', 'danger')
        return redirect(url_for('submission.submission_detail', a_id=a_id))

    screenshot_path = request.form.get('screenshot_path', '').strip() or None
    now = datetime.now()

    app.status = '已投递'
    app.apply_date = date.today()
    app.updated_at = now

    sub = (
        ApplicationSubmission.query
        .filter_by(application_id=a_id)
        .order_by(ApplicationSubmission.id.desc())
        .first()
    )
    if sub:
        sub.status = 'submitted'
        sub.submitted_at = now
        sub.human_approved_at = now
        if screenshot_path:
            sub.screenshot_path = screenshot_path
        sub.updated_at = now

    db.session.commit()
    flash('已记录为已投递', 'success')
    return redirect(url_for('submission.submission_list'))


@bp.route('/submissions/<int:a_id>/fail', methods=['POST'])
def submission_fail(a_id):
    """人类在真实页面提交失败，回退到 待投递。"""
    app = Application.query.get_or_404(a_id)
    if app.status != '待提交':
        flash(f'当前状态 {app.status} 不允许此操作', 'danger')
        return redirect(url_for('submission.submission_detail', a_id=a_id))

    failure_reason = request.form.get('failure_reason', '').strip() or '人工标记失败'
    now = datetime.now()

    app.status = '待投递'
    app.updated_at = now

    sub = (
        ApplicationSubmission.query
        .filter_by(application_id=a_id)
        .order_by(ApplicationSubmission.id.desc())
        .first()
    )
    if sub:
        sub.status = 'failed'
        sub.failure_reason = failure_reason
        sub.updated_at = now

    db.session.commit()
    flash('已回退到 待投递', 'warning')
    return redirect(url_for('submission.submission_list'))


# ============================================================
# AnswerBank 管理（Phase 1 仅做只读列表）
# ============================================================
@bp.route('/answer-bank')
def answer_bank_list():
    """AnswerBank 管理列表：按 role_family 分组。"""
    role_family = request.args.get('role_family', '').strip()
    needs_review_filter = request.args.get('needs_review', '')

    q = AnswerBank.query
    if role_family:
        norm = role_family_normalize(role_family)
        q = q.filter_by(role_family=norm)
    if needs_review_filter == '1':
        q = q.filter_by(needs_review=True)
    elif needs_review_filter == '0':
        q = q.filter_by(needs_review=False)

    items = q.order_by(AnswerBank.role_family.asc().nulls_first(), AnswerBank.id.desc()).all()

    # 列出所有出现过的 role_family，用于筛选下拉
    role_families = [
        r[0] for r in
        db.session.query(AnswerBank.role_family)
        .distinct()
        .order_by(AnswerBank.role_family.asc().nulls_first())
        .all()
    ]

    return render_template(
        'answer_bank.html',
        items=items,
        role_families=role_families,
        current_role_family=role_family,
        current_needs_review=needs_review_filter,
    )


@bp.route('/answer-bank/<int:answer_id>/delete', methods=['POST'])
def answer_bank_delete(answer_id):
    """删除一条 AnswerBank 答案（必须勾选 confirm）。"""
    if request.form.get('confirm') != '1':
        flash('必须勾选「我确认删除」', 'danger')
        return redirect(url_for('submission.answer_bank_list'))

    item = AnswerBank.query.get_or_404(answer_id)
    db.session.delete(item)
    db.session.commit()
    flash('已删除该答案', 'success')
    return redirect(url_for('submission.answer_bank_list'))
