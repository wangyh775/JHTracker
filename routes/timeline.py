"""时间线路由（甘特图）。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Timeline
from utils import parse_date

bp = Blueprint('timeline', __name__)


@bp.route('/timeline')
def timeline_view():
    items = Timeline.query.order_by(Timeline.event_date, Timeline.id).all()
    return render_template('timeline.html', items=items)


@bp.route('/timeline/add', methods=['POST'])
def timeline_add():
    try:
        event_date = parse_date(request.form['event_date'])
        end_date = parse_date(request.form.get('end_date', ''))
        if event_date is None:
            raise ValueError('开始日期不能为空')
        if end_date and end_date < event_date:
            raise ValueError('结束日期不能早于开始日期')
        t = Timeline(
            event_date=event_date,
            end_date=end_date,
            title=request.form['title'],
            description=request.form.get('description', ''),
            event_type=request.form.get('event_type', 'action'),
        )
        db.session.add(t)
        db.session.commit()
    except ValueError:
        pass
    return redirect(url_for('timeline.timeline_view'))


@bp.route('/timeline/<int:t_id>/edit', methods=['POST'])
def timeline_edit(t_id):
    t = Timeline.query.get_or_404(t_id)
    try:
        event_date = parse_date(request.form['event_date'])
        end_date = parse_date(request.form.get('end_date', ''))
        if event_date is None:
            raise ValueError('开始日期不能为空')
        if end_date and end_date < event_date:
            raise ValueError('结束日期不能早于开始日期')
        t.event_date = event_date
        t.end_date = end_date
        t.title = request.form['title']
        t.description = request.form.get('description', '')
        t.event_type = request.form.get('event_type', 'action')
        db.session.commit()
    except ValueError:
        pass
    return redirect(url_for('timeline.timeline_view'))


@bp.route('/timeline/<int:t_id>/toggle', methods=['POST'])
def timeline_toggle(t_id):
    t = Timeline.query.get_or_404(t_id)
    t.done = not t.done
    db.session.commit()
    return redirect(url_for('timeline.timeline_view'))
