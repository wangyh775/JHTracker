"""Agent RESTful API & Trace Endpoints (/api/v1/)."""
import os
import json
from flask import Blueprint, jsonify, request, render_template
from extensions import db
from models import Company, Application, AgentTask, AgentEvent, Memory, DecisionFeedback
from config import DATA_DIR
from services.cleanup import run_auto_cleanup, clear_all_traces

bp = Blueprint('agent_api', __name__)
PROFILE_FILE = os.path.join(DATA_DIR, 'profile.md')


def _rest_upsert_memory_rule(category, rule_value, raw_feedback, application_id):
    """写入一条 memory 规则，按 (category, rule_value) 去重。rule_value 为空时不参与去重。"""
    if rule_value:
        existing = Memory.query.filter_by(category=category, rule_value=rule_value).first()
        if existing:
            return
    db.session.add(Memory(
        application_id=application_id,
        category=category,
        rule_value=rule_value,
        raw_feedback=raw_feedback
    ))


def _rest_upsert_positive_memories(application, explicit_rule_value, raw_feedback):
    """从 application + company 提取正向特征写入 prefer_* 记忆。"""
    rules = []
    if explicit_rule_value:
        rules.append(('prefer_tech', explicit_rule_value))
    else:
        if application.company and application.company.name:
            rules.append(('prefer_company', application.company.name))
        if application.company and application.company.industry:
            rules.append(('prefer_domain', application.company.industry))
    for cat, val in rules:
        _rest_upsert_memory_rule(cat, val, raw_feedback, application.id)


@bp.route('/traces', methods=['GET'])
def traces_view():
    from config import Config
    run_auto_cleanup(days=Config.TRACES_RETENTION_DAYS)
    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        tasks = AgentTask.query.order_by(AgentTask.id.desc()).limit(50).all()
        results = []
        for t in tasks:
            events = t.events.order_by(AgentEvent.id.asc()).all()
            results.append({
                'id': t.id,
                'task_id': t.task_id,
                'agent_name': t.agent_name,
                'status': t.status,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'events': [
                    {
                        'id': e.id,
                        'event_type': e.event_type,
                        'payload': json.loads(e.payload_json) if e.payload_json and e.payload_json.startswith(('{', '[')) else e.payload_json,
                        'created_at': e.created_at.isoformat() if e.created_at else None
                    }
                    for e in events
                ]
            })
        return jsonify({'status': 'success', 'count': len(results), 'tasks': results})
    tasks = AgentTask.query.order_by(AgentTask.id.desc()).limit(50).all()
    return render_template('traces.html', tasks=tasks)


@bp.route('/api/agent/traces/clear', methods=['POST'])
def clear_traces():
    """Delete all agent event and task records."""
    clear_all_traces()
    return jsonify({'status': 'success', 'message': 'All traces cleared'})
    tasks = AgentTask.query.order_by(AgentTask.id.desc()).limit(50).all()
    return render_template('traces.html', tasks=tasks)


@bp.route('/api/agent/tasks', methods=['GET'])
def get_agent_tasks():
    """API Endpoint to query Agent tasks list."""
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    query = AgentTask.query
    if status:
        query = query.filter(AgentTask.status == status)
    tasks = query.order_by(AgentTask.id.desc()).limit(limit).all()

    pending_approvals_count = Application.query.filter(
        Application.status.in_(['Pending Approval', '待审批', '待投递'])
    ).count()

    results = []
    for t in tasks:
        results.append({
            'id': t.id,
            'task_id': t.task_id,
            'agent_name': t.agent_name,
            'status': t.status,
            'event_count': t.events.count(),
            'created_at': t.created_at.isoformat() if t.created_at else None,
            'updated_at': t.updated_at.isoformat() if t.updated_at else None
        })
    return jsonify({
        'status': 'success',
        'count': len(results),
        'pending_approvals_count': pending_approvals_count,
        'tasks': results
    })


@bp.route('/api/agent/tasks/<task_id>', methods=['GET'])
def get_agent_task_detail(task_id):
    """API Endpoint to query specific Agent task and its execution event trace logs."""
    task = AgentTask.query.filter((AgentTask.task_id == task_id) | (AgentTask.id == task_id)).first()
    if not task:
        return jsonify({'status': 'error', 'message': 'Task not found'}), 404

    events = task.events.order_by(AgentEvent.id.asc()).all()
    event_list = []
    for e in events:
        payload = e.payload_json
        if payload and payload.startswith(('{', '[')):
            try:
                payload = json.loads(payload)
            except Exception:
                pass
        event_list.append({
            'id': e.id,
            'event_type': e.event_type,
            'payload': payload,
            'created_at': e.created_at.isoformat() if e.created_at else None
        })

    return jsonify({
        'status': 'success',
        'task': {
            'id': task.id,
            'task_id': task.task_id,
            'agent_name': task.agent_name,
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
            'events': event_list
        }
    })


@bp.route('/api/v1/companies', methods=['POST'])
def create_companies():
    data = request.get_json(silent=True) or {}
    items = data.get('companies', [])
    if isinstance(data, list):
        items = data
    elif not items and 'name' in data:
        items = [data]

    if not items:
        return jsonify({'status': 'error', 'message': 'No companies data provided'}), 400

    results = []
    for item in items:
        name = item.get('name', '').strip()
        if not name:
            continue
        company = Company.query.filter(Company.name.ilike(name)).first()
        if not company:
            company = Company(
                name=name,
                industry=item.get('industry'),
                city=item.get('city'),
                sub_city=item.get('sub_city'),
                job_type=item.get('job_type'),
                match_reason=item.get('match_reason'),
                priority=item.get('priority'),
                website=item.get('website'),
                source_list=item.get('source_list', 'Agent Auto-Sourcing'),
                salary_min=item.get('salary_min'),
                salary_max=item.get('salary_max'),
                scale=item.get('scale'),
                financing_stage=item.get('financing_stage'),
                tags=item.get('tags'),
                company_type=item.get('company_type'),
                score=item.get('score'),
                score_reason=item.get('score_reason')
            )
            db.session.add(company)
            db.session.flush()
            created = True
        else:
            created = False

        results.append({
            'id': company.id,
            'name': company.name,
            'created': created
        })

    db.session.commit()
    return jsonify({'status': 'success', 'count': len(results), 'companies': results})


@bp.route('/api/v1/applications', methods=['POST'])
def create_application():
    data = request.get_json(silent=True) or {}
    company_id = data.get('company_id')
    company_name = data.get('company_name')

    if not company_id and company_name:
        company = Company.query.filter(Company.name.ilike(company_name.strip())).first()
        if company:
            company_id = company.id
        else:
            return jsonify({'status': 'error', 'message': f"Company '{company_name}' not found"}), 404

    if not company_id:
        return jsonify({'status': 'error', 'message': 'company_id or valid company_name is required'}), 400

    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({'status': 'error', 'message': 'Company not found'}), 404

    application = Application(
        company_id=company_id,
        resume_id=data.get('resume_id'),
        position=data.get('position', '待定岗位'),
        channel=data.get('channel', 'Agent 自动推送'),
        status=data.get('status', '待投递'),
        job_desc=data.get('job_desc'),
        url=data.get('url'),
        salary_min=data.get('salary_min'),
        salary_max=data.get('salary_max'),
        match_score=data.get('match_score'),
        agent_reason=data.get('agent_reason'),
        agent_task_id=data.get('agent_task_id'),
        source_url=data.get('source_url')
    )
    db.session.add(application)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'application': {
            'id': application.id,
            'company_id': application.company_id,
            'company_name': company.name,
            'position': application.position,
            'status': application.status,
            'url': application.url,
            'match_score': application.match_score,
            'agent_reason': application.agent_reason,
            'agent_task_id': application.agent_task_id,
            'source_url': application.source_url
        }
    })


@bp.route('/api/v1/applications/<int:app_id>/review', methods=['POST'])
def review_application(app_id):
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({'status': 'error', 'message': 'Application not found'}), 404

    data = request.get_json(silent=True) or request.form
    action = data.get('action')

    if action not in ['approve', 'reject']:
        return jsonify({'status': 'error', 'message': "Action must be 'approve' or 'reject'"}), 400

    reason_category = data.get('category', data.get('reason_category', 'general'))
    raw_feedback = data.get('raw_feedback') or data.get('reason') or ''
    rule_value = data.get('rule_value') or ''

    if action == 'approve':
        application.status = 'to_apply'
        # 写正向记忆 + feedback
        feedback_entry = DecisionFeedback(
            application_id=application.id,
            action='approve',
            reason_category=reason_category,
            raw_feedback=raw_feedback
        )
        db.session.add(feedback_entry)
        db.session.flush()
        _rest_upsert_positive_memories(application, rule_value, raw_feedback)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'action': 'approved',
            'application': {
                'id': application.id,
                'status': application.status
            }
        })
    else:
        application.status = 'rejected'
        feedback_entry = DecisionFeedback(
            application_id=application.id,
            action='reject',
            reason_category=reason_category,
            raw_feedback=raw_feedback
        )
        db.session.add(feedback_entry)
        # 写负向记忆：rule_value 仅存结构化值（修复污染 bug）
        neg_category = reason_category if reason_category in (
            'exclude_tech', 'exclude_company', 'salary_too_low', 'general'
        ) else 'general'
        _rest_upsert_memory_rule(neg_category, rule_value, raw_feedback, application.id)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'action': 'rejected',
            'application': {
                'id': application.id,
                'status': application.status
            }
        })


@bp.route('/api/agent/decisions/pending', methods=['GET'])
def get_pending_decisions():
    """API Endpoint to list all staged proposals pending human approval."""
    pending_apps = Application.query.filter(
        Application.status.in_(['Pending Approval', '待审批', '待投递'])
    ).order_by(Application.id.desc()).all()

    results = []
    for app in pending_apps:
        results.append({
            'application_id': app.id,
            'company_id': app.company_id,
            'company_name': app.company.name if app.company else None,
            'position': app.position,
            'status': app.status,
            'match_score': app.match_score,
            'agent_reason': app.agent_reason,
            'agent_task_id': app.agent_task_id,
            'source_url': app.source_url,
            'url': app.url,
            'resume_id': app.resume_id,
            'resume_name': app.resume.name if app.resume else None,
            'created_at': app.created_at.isoformat() if app.created_at else None
        })

    return jsonify({'status': 'success', 'count': len(results), 'proposals': results})


@bp.route('/api/agent/decisions/pending-html', methods=['GET'])
def get_pending_decisions_html():
    """Returns rendered Jinja2 partial _decision_inbox.html for HTMX."""
    pending_apps = Application.query.filter(
        Application.status.in_(['Pending Approval', '待审批', '待投递'])
    ).order_by(Application.id.desc()).all()

    proposals = []
    for app in pending_apps:
        proposals.append({
            'application_id': app.id,
            'company_id': app.company_id,
            'company_name': app.company.name if app.company else None,
            'position': app.position,
            'status': app.status,
            'match_score': app.match_score,
            'agent_reason': app.agent_reason,
            'agent_task_id': app.agent_task_id,
            'source_url': app.source_url,
            'url': app.url,
            'resume_id': app.resume_id,
            'resume_name': app.resume.name if app.resume else None,
            'created_at': app.created_at.strftime('%Y-%m-%d %H:%M') if app.created_at else None
        })

    return render_template('_decision_inbox.html', proposals=proposals)


@bp.route('/api/agent/tasks-html', methods=['GET'])
def get_agent_tasks_html():
    """Returns rendered Jinja2 partial _agent_tasks.html for HTMX."""
    status = request.args.get('status')
    limit = request.args.get('limit', 10, type=int)
    query = AgentTask.query
    if status:
        query = query.filter(AgentTask.status == status)
    tasks = query.order_by(AgentTask.id.desc()).limit(limit).all()

    task_list = []
    for t in tasks:
        task_list.append({
            'id': t.id,
            'task_id': t.task_id,
            'agent_name': t.agent_name,
            'status': t.status,
            'event_count': t.events.count(),
            'created_at': t.created_at.strftime('%H:%M') if t.created_at else None
        })

    return render_template('_agent_tasks.html', tasks=task_list)


@bp.route('/api/agent/decisions/<int:application_id>', methods=['POST'])
def handle_decision_action(application_id):
    """API Endpoint for human user to approve, reject, or edit a staged application proposal."""
    app = db.session.get(Application, application_id)
    if not app:
        return jsonify({'status': 'error', 'message': 'Application proposal not found'}), 404

    data = request.get_json(silent=True) or request.form
    action = data.get('action')

    if action not in ['approve', 'reject', 'edit']:
        return jsonify({'status': 'error', 'message': "Action must be 'approve', 'reject', or 'edit'"}), 400

    reason_category = data.get('reason_category', 'general')
    raw_feedback = data.get('raw_feedback') or data.get('reason')

    if action == 'approve':
        app.status = 'Applied'  # or 已投递
        feedback_entry = DecisionFeedback(
            application_id=app.id,
            action='approve',
            reason_category=reason_category,
            raw_feedback=raw_feedback
        )
        db.session.add(feedback_entry)
        db.session.flush()
        # 写正向记忆：从关联 application/company 提取特征
        rule_value = data.get('rule_value') or ''
        _rest_upsert_positive_memories(app, rule_value, raw_feedback)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'action': 'approved',
            'application': {
                'id': app.id,
                'status': app.status,
                'position': app.position
            }
        })

    elif action == 'reject':
        app.status = 'Rejected'  # or 已拒
        feedback_entry = DecisionFeedback(
            application_id=app.id,
            action='reject',
            reason_category=reason_category,
            raw_feedback=raw_feedback
        )
        db.session.add(feedback_entry)

        # 写负向记忆：rule_value 仅存结构化值（修复污染 bug），未传则留空
        rule_value = data.get('rule_value') or ''
        neg_category = reason_category if reason_category in (
            'exclude_tech', 'exclude_company', 'salary_too_low', 'general'
        ) else 'general'
        _rest_upsert_memory_rule(neg_category, rule_value, raw_feedback, app.id)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'action': 'rejected',
            'application': {
                'id': app.id,
                'status': app.status
            }
        })

    elif action == 'edit':
        if 'position' in data:
            app.position = data['position']
        if 'resume_id' in data:
            app.resume_id = data['resume_id']
        if 'match_score' in data:
            app.match_score = data['match_score']
        if 'agent_reason' in data:
            app.agent_reason = data['agent_reason']

        feedback_entry = DecisionFeedback(
            application_id=app.id,
            action='edit',
            reason_category=reason_category,
            raw_feedback=raw_feedback
        )
        db.session.add(feedback_entry)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'action': 'edited',
            'application': {
                'id': app.id,
                'status': app.status,
                'position': app.position,
                'resume_id': app.resume_id
            }
        })


@bp.route('/api/v1/profile/preferences', methods=['GET'])
def get_user_preferences():
    content = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

    from constants import memory_polarity
    memories = Memory.query.order_by(Memory.id.desc()).all()
    positive_rules = []
    negative_rules = []
    recent_rejection_notes = []

    for m in memories:
        polarity = memory_polarity(m.category)
        if m.rule_value:
            entry = {'category': m.category, 'rule_value': m.rule_value}
            if polarity == 'positive':
                positive_rules.append(entry)
            else:
                negative_rules.append(entry)
        if m.raw_feedback:
            recent_rejection_notes.append(m.raw_feedback)

    return jsonify({
        'status': 'success',
        'profile': content,
        'positive_rules': positive_rules,
        'negative_rules': negative_rules,
        'recent_rejection_notes': recent_rejection_notes[:20]
    })


@bp.route('/api/v1/companies/search', methods=['GET'])
def search_companies():
    q = request.args.get('q', '').strip()
    query = Company.query
    if q:
        query = query.filter(
            (Company.name.ilike(f'%{q}%')) |
            (Company.match_reason.ilike(f'%{q}%')) |
            (Company.industry.ilike(f'%{q}%'))
        )
    companies = query.order_by(Company.score.desc().nullslast(), Company.id.desc()).limit(20).all()
    results = [
        {
            'id': c.id,
            'name': c.name,
            'city': c.city,
            'industry': c.industry,
            'priority': c.priority,
            'score': c.score,
            'score_reason': c.score_reason,
            'job_type': c.job_type
        }
        for c in companies
    ]
    return jsonify({'status': 'success', 'count': len(results), 'companies': results})


@bp.route('/api/v1/companies/<int:company_id>/score', methods=['POST'])
def update_company_score(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return jsonify({'status': 'error', 'message': 'Company not found'}), 404

    data = request.get_json(silent=True) or request.form
    score = data.get('score')
    reason = data.get('reason', '')

    if score is not None:
        try:
            company.score = int(score)
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid score format'}), 400

    if reason:
        company.score_reason = str(reason)

    db.session.commit()

    # Trigger SSE broadcast
    try:
        from routes.dashboard import trigger_event
        trigger_event('company_score_updated', f"Company '{company.name}' score updated to {company.score}")
    except Exception:
        pass

    return jsonify({
        'status': 'success',
        'company': {
            'id': company.id,
            'name': company.name,
            'score': company.score,
            'score_reason': company.score_reason
        }
    })


@bp.route('/api/v1/profile', methods=['GET'])
def get_profile():
    content = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    return jsonify({
        'status': 'success',
        'profile': content
    })


@bp.route('/api/v1/traces', methods=['POST'])
def record_trace():
    data = request.get_json(silent=True) or {}
    task_id = data.get('task_id')
    agent_name = data.get('agent_name', 'Agent')
    event_type = data.get('event_type', 'info')
    payload = data.get('payload', {})
    status = data.get('status', 'running')

    if not task_id:
        return jsonify({'status': 'error', 'message': 'task_id is required'}), 400

    task = AgentTask.query.filter_by(task_id=task_id).first()
    if not task:
        task = AgentTask(task_id=task_id, agent_name=agent_name, status=status)
        db.session.add(task)
        db.session.flush()
    else:
        task.status = status
        if agent_name:
            task.agent_name = agent_name

    payload_str = json.dumps(payload, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
    event = AgentEvent(task_id=task.id, event_type=event_type, payload_json=payload_str)
    db.session.add(event)
    db.session.commit()

    # SSE notification
    try:
        from routes.dashboard import trigger_event
        trigger_event('agent_trace', f"Agent '{agent_name}' trace logged for task '{task_id}'")
    except Exception:
        pass

    return jsonify({'status': 'success', 'task_id': task_id, 'event_id': event.id})


@bp.route('/api/v1/traces', methods=['GET'])
def list_traces():
    tasks = AgentTask.query.order_by(AgentTask.id.desc()).limit(50).all()
    results = []
    for t in tasks:
        events = t.events.order_by(AgentEvent.id.asc()).all()
        results.append({
            'id': t.id,
            'task_id': t.task_id,
            'agent_name': t.agent_name,
            'status': t.status,
            'created_at': t.created_at.isoformat() if t.created_at else None,
            'events': [
                {
                    'id': e.id,
                    'event_type': e.event_type,
                    'payload': json.loads(e.payload_json) if e.payload_json and e.payload_json.startswith(('{', '[')) else e.payload_json,
                    'created_at': e.created_at.isoformat() if e.created_at else None
                }
                for e in events
            ]
        })
    return jsonify({'status': 'success', 'count': len(results), 'tasks': results})

