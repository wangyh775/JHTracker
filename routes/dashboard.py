"""看板路由。"""
from flask import Blueprint, render_template, redirect, url_for, Response, json, request, jsonify
from sqlalchemy import func
from extensions import db
from models import Company, Application, Timeline
from constants import STATUS_LIST
from sqlalchemy.orm import joinedload
import time

bp = Blueprint('dashboard', __name__)

# 全局 DB 变动版本号
_db_version = 0

def notify_db_changed():
    global _db_version
    _db_version += 1


@bp.route('/api/notify', methods=['POST'])
def api_notify():
    """供外部 Agent 脚本在更新数据库后主动通知 UI 刷新。"""
    notify_db_changed()
    return jsonify({'status': 'ok', 'version': _db_version})


@bp.route('/api/stream')
def api_stream():
    """SSE 实时数据变动推送接口。"""
    def event_stream():
        last_version = _db_version
        while True:
            time.sleep(3)
            if _db_version != last_version:
                last_version = _db_version
                data = json.dumps({'type': 'db_updated', 'version': _db_version})
                yield f"data: {data}\n\n"
            else:
                yield "data: {\"type\": \"ping\"}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


def _top_n_with_other(counts, n):
    """将 [(label, count), ...] 压缩为前 n 项 + '其他' 汇总。
    若总条目数 <= n，原样返回。
    """
    if len(counts) <= n:
        return counts
    top = list(counts[:n])
    other_count = sum(c for _, c in counts[n:])
    top.append(('其他', other_count))
    return top


@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    total = Company.query.count()
    s_count = Company.query.filter_by(priority='S').count()
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

    # city distribution：过滤 NULL 和空串，按数量降序，仅保留前 5，其余归为"其他"
    city_all = db.session.query(
        func.coalesce(Company.city, '未知'), func.count(Company.id)
    ).filter(
        func.coalesce(Company.city, '') != ''
    ).group_by(Company.city).order_by(func.count(Company.id).desc()).all()
    city_counts = _top_n_with_other(city_all, 10)

    # industry distribution：同上
    ind_all = db.session.query(
        func.coalesce(Company.industry, '未知'), func.count(Company.id)
    ).filter(
        func.coalesce(Company.industry, '') != ''
    ).group_by(Company.industry).order_by(func.count(Company.id).desc()).all()
    ind_counts = _top_n_with_other(ind_all, 10)

    # priority breakdown
    pri_counts = db.session.query(
        func.coalesce(Company.priority, '无'), func.count(Company.id)
    ).group_by(Company.priority).all()

    # AI 匹配度 vs 参考最高薪资散点数据
    score_salary_query = Company.query.filter(
        Company.score != None, Company.score > 0
    ).limit(100).all()
    score_salary_data = [
        {
            'name': c.name,
            'x': c.score,
            'y': c.salary_max or c.salary_min or 0,
            'priority': c.priority or 'C'
        } for c in score_salary_query
    ]

    # timeline upcoming
    upcoming = Timeline.query.filter(Timeline.done == False).order_by(Timeline.event_date).limit(5).all()

    # recent：用 joinedload 修 N+1
    recent = Application.query.options(
        joinedload(Application.company)
    ).order_by(Application.updated_at.desc()).limit(5).all()

    # 紧急截止：未来 7 天内 deadline
    from datetime import date, datetime, timedelta
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

    # AI Daily Briefing 建议数据
    seven_days_ago = datetime.now() - timedelta(days=7)
    stale_unanswered = Application.query.options(joinedload(Application.company)).filter(
        Application.status.in_(['已投递', '简历筛选']),
        Application.updated_at < seven_days_ago,
        Application.is_archived.is_(False)
    ).limit(3).all()

    high_match_pending = Application.query.options(joinedload(Application.company)).filter(
        Application.status.in_(['Pending Approval', '待审批']),
        Application.match_score >= 80
    ).limit(3).all()

    ai_briefing = {
        'stale_unanswered': stale_unanswered,
        'high_match_pending': high_match_pending,
        'urgent_count': len(urgent_deadlines),
        'pending_feedback_count': len(pending_feedbacks)
    }

    max_funnel = max(funnel.values()) if funnel.values() else 1

    return render_template('dashboard.html',
                           total=total, applied=applied, interviews=interviews,
                           offers=offers, rejected=rejected, s_count=s_count,
                           funnel=funnel, max_funnel=max_funnel,
                           city_counts=city_counts, ind_counts=ind_counts,
                           pri_counts=pri_counts, upcoming=upcoming, recent=recent,
                           urgent_deadlines=urgent_deadlines,
                           pending_feedbacks=pending_feedbacks,
                           score_salary_data=score_salary_data,
                           ai_briefing=ai_briefing)
