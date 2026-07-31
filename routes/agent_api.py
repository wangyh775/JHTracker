"""Agent RESTful API & Trace Endpoints (/api/v1/)."""
import os
import json
from flask import Blueprint, jsonify, request, render_template
from extensions import db
from models import Company, Application, AgentTask, AgentEvent, Memory
from config import DATA_DIR

bp = Blueprint('agent_api', __name__)
PROFILE_FILE = os.path.join(DATA_DIR, 'profile.md')


@bp.route('/traces', methods=['GET'])
def traces_view():
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
    return render_template('traces.html')


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

    if action == 'approve':
        application.status = 'to_apply'
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
        category = data.get('category', 'general')
        rule_value = data.get('rule_value')
        raw_feedback = data.get('raw_feedback')

        memory = Memory(
            application_id=application.id,
            category=category,
            rule_value=rule_value,
            raw_feedback=raw_feedback
        )
        db.session.add(memory)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'action': 'rejected',
            'application': {
                'id': application.id,
                'status': application.status
            },
            'memory_id': memory.id
        })


@bp.route('/api/v1/profile/preferences', methods=['GET'])
def get_user_preferences():
    content = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

    memories = Memory.query.order_by(Memory.id.desc()).all()
    negative_rules = []
    recent_rejection_notes = []

    for m in memories:
        if m.rule_value:
            negative_rules.append({
                'category': m.category,
                'rule_value': m.rule_value
            })
        if m.raw_feedback:
            recent_rejection_notes.append(m.raw_feedback)

    return jsonify({
        'status': 'success',
        'profile': content,
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

