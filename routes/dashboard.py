"""看板路由。"""
from flask import Blueprint, render_template
from sqlalchemy import func
from extensions import db
from models import Company, Application, Timeline
from constants import STATUS_LIST
from sqlalchemy.orm import joinedload

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def dashboard():
    total = Company.query.count()
    applied = Application.query.filter(
        Application.status.in_(['已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer'])
    ).count()
    interviews = Application.query.filter(
        Application.status.in_(['一面', '二面', '终面'])
    ).count()
    offers = Application.query.filter_by(status='Offer').count()
    rejected = Application.query.filter_by(status='已拒').count()

    # funnel：单次 group_by 查询
    status_counts = db.session.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()
    funnel = {s: 0 for s in STATUS_LIST}
    for s, c in status_counts:
        funnel[s] = c

    # city distribution：过滤 NULL 和空串，按数量降序
    city_counts = db.session.query(
        func.coalesce(Company.city, '未知'), func.count(Company.id)
    ).filter(
        func.coalesce(Company.city, '') != ''
    ).group_by(Company.city).order_by(func.count(Company.id).desc()).all()

    # industry distribution
    ind_counts = db.session.query(
        func.coalesce(Company.industry, '未知'), func.count(Company.id)
    ).filter(
        func.coalesce(Company.industry, '') != ''
    ).group_by(Company.industry).order_by(func.count(Company.id).desc()).all()

    # priority breakdown
    pri_counts = db.session.query(
        func.coalesce(Company.priority, '无'), func.count(Company.id)
    ).group_by(Company.priority).all()

    # timeline upcoming
    upcoming = Timeline.query.filter(Timeline.done == False).order_by(Timeline.event_date).limit(5).all()

    # recent：用 joinedload 修 N+1
    recent = Application.query.options(
        joinedload(Application.company)
    ).order_by(Application.updated_at.desc()).limit(5).all()

    # 紧急截止：未来 7 天内 deadline
    from datetime import date, timedelta
    today = date.today()
    week_later = today + timedelta(days=7)
    urgent_deadlines = Application.query.options(
        joinedload(Application.company)
    ).filter(
        Application.deadline != None,
        Application.deadline >= today,
        Application.deadline <= week_later,
        ~Application.status.in_(['Offer', '已拒'])
    ).order_by(Application.deadline).all()

    # 面试复盘待写：status in (一面,二面,终面,Offer) 且无 feedbacks
    pending_feedbacks = Application.query.options(
        joinedload(Application.company)
    ).filter(
        Application.status.in_(['一面', '二面', '终面', 'Offer'])
    ).all()
    pending_feedbacks = [a for a in pending_feedbacks if a.feedbacks.count() == 0]

    max_funnel = max(funnel.values()) if funnel.values() else 1

    return render_template('dashboard.html',
                           total=total, applied=applied, interviews=interviews,
                           offers=offers, rejected=rejected,
                           funnel=funnel, max_funnel=max_funnel,
                           city_counts=city_counts, ind_counts=ind_counts,
                           pri_counts=pri_counts, upcoming=upcoming, recent=recent,
                           urgent_deadlines=urgent_deadlines,
                           pending_feedbacks=pending_feedbacks)
