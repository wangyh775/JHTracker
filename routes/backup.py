"""数据备份与恢复路由。"""
import os
import json
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from extensions import db
from models import Company, Application, Note, StudyMaterial, Timeline, InterviewFeedback, Resume
from config import Config

bp = Blueprint('backup', __name__)

BACKUP_VERSION = 1


@bp.route('/backup')
def backup_page():
    counts = {
        'companies': Company.query.count(),
        'applications': Application.query.count(),
        'notes': Note.query.count(),
        'study_materials': StudyMaterial.query.count(),
        'timelines': Timeline.query.count(),
        'interview_feedbacks': InterviewFeedback.query.count(),
        'resumes': Resume.query.count(),
    }
    return render_template('backup.html', counts=counts)


def _serialize(obj, model):
    """把 SQLAlchemy 对象序列化为 dict。"""
    result = {}
    for col in model.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        elif hasattr(val, 'isoformat') and not isinstance(val, str):
            val = val.isoformat()
        result[col.name] = val
    return result


@bp.route('/backup/export', methods=['POST'])
def backup_export():
    data = {
        'version': BACKUP_VERSION,
        'exported_at': datetime.now().isoformat(),
        'companies': [_serialize(c, Company) for c in Company.query.all()],
        'applications': [_serialize(a, Application) for a in Application.query.all()],
        'notes': [_serialize(n, Note) for n in Note.query.all()],
        'study_materials': [_serialize(s, StudyMaterial) for s in StudyMaterial.query.all()],
        'timelines': [_serialize(t, Timeline) for t in Timeline.query.all()],
        'interview_feedbacks': [_serialize(f, InterviewFeedback) for f in InterviewFeedback.query.all()],
        'resumes': [_serialize(r, Resume) for r in Resume.query.all()],
    }
    filename = f'tracker_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    backup_dir = os.path.join(current_app.config['BASE_DIR'], 'data', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    filepath = os.path.join(backup_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return send_file(filepath, as_attachment=True, download_name=filename)


@bp.route('/backup/restore', methods=['POST'])
def backup_restore():
    file = request.files.get('backup_file')
    if not file or not file.filename:
        flash('未选择文件')
        return redirect(url_for('backup.backup_page'))

    mode = request.form.get('mode', 'skip')  # skip / overwrite

    # 备份当前 db
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    bak_path = f"{db_path}.before_restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, bak_path)

    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        if data.get('version') != BACKUP_VERSION:
            flash(f'版本不匹配：期望 {BACKUP_VERSION}，实际 {data.get("version")}')
            return redirect(url_for('backup.backup_page'))

        id_map = {'companies': {}}
        stats = {'companies': 0, 'applications': 0, 'notes': 0, 'timelines': 0,
                 'study_materials': 0, 'interview_feedbacks': 0, 'resumes': 0}

        for c_data in data.get('companies', []):
            name = c_data.get('name')
            existing = Company.query.filter_by(name=name).first()
            if existing and mode == 'skip':
                id_map['companies'][c_data['id']] = existing.id
                continue
            old_id = c_data.pop('id', None)
            c = Company(**{k: v for k, v in c_data.items() if v is not None or k in ['name']})
            db.session.add(c)
            db.session.flush()
            id_map['companies'][old_id] = c.id
            stats['companies'] += 1

        for a_data in data.get('applications', []):
            old_company_id = a_data.get('company_id')
            a_data['company_id'] = id_map['companies'].get(old_company_id, old_company_id)
            a_data.pop('id', None)
            a = Application(**{k: v for k, v in a_data.items() if v is not None})
            db.session.add(a)
            stats['applications'] += 1

        for n_data in data.get('notes', []):
            old_company_id = n_data.get('company_id')
            if old_company_id:
                n_data['company_id'] = id_map['companies'].get(old_company_id, old_company_id)
            n_data.pop('id', None)
            db.session.add(Note(**{k: v for k, v in n_data.items() if v is not None}))

        for s_data in data.get('study_materials', []):
            s_data.pop('id', None)
            db.session.add(StudyMaterial(**{k: v for k, v in s_data.items() if v is not None}))

        for t_data in data.get('timelines', []):
            t_data.pop('id', None)
            db.session.add(Timeline(**{k: v for k, v in t_data.items() if v is not None}))

        db.session.commit()
        flash(f'恢复完成：{stats["companies"]} 家公司、{stats["applications"]} 条投递。当前 db 已备份到 {os.path.basename(bak_path)}')
    except Exception as e:
        db.session.rollback()
        flash(f'恢复失败：{str(e)}。当前 db 未变更（备份在 {os.path.basename(bak_path)}）')
    return redirect(url_for('backup.backup_page'))
