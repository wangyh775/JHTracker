"""数据备份与恢复路由。"""
import os
import io
import json
import shutil
import zipfile
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from extensions import db
from models import Company, Application, Note, Timeline, InterviewFeedback, Resume
from config import Config

bp = Blueprint('backup', __name__)

BACKUP_VERSION = 1


@bp.route('/backup')
def backup_page():
    counts = {
        'companies': Company.query.count(),
        'applications': Application.query.count(),
        'notes': Note.query.count(),
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
    """导出为 zip 包：内含 data.json（所有表数据）+ resumes/ 目录下的简历文件。

    纯 JSON 导出无法跨机器恢复简历文件，故默认导出 zip。
    """
    data = {
        'version': BACKUP_VERSION,
        'exported_at': datetime.now().isoformat(),
        'companies': [_serialize(c, Company) for c in Company.query.all()],
        'applications': [_serialize(a, Application) for a in Application.query.all()],
        'notes': [_serialize(n, Note) for n in Note.query.all()],
        'timelines': [_serialize(t, Timeline) for t in Timeline.query.all()],
        'interview_feedbacks': [_serialize(f, InterviewFeedback) for f in InterviewFeedback.query.all()],
        'resumes': [_serialize(r, Resume) for r in Resume.query.all()],
    }
    filename = f'tracker_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    backup_dir = os.path.join(current_app.config['BASE_DIR'], 'data', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    filepath = os.path.join(backup_dir, filename)

    # 写 zip：data.json + resumes/ 目录下所有文件
    resume_dir_abs = os.path.join(current_app.config['BASE_DIR'], 'data', 'resumes')
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('data.json', json.dumps(data, ensure_ascii=False, indent=2, default=str))
        if os.path.isdir(resume_dir_abs):
            for fname in os.listdir(resume_dir_abs):
                fpath = os.path.join(resume_dir_abs, fname)
                if os.path.isfile(fpath):
                    zf.write(fpath, f'resumes/{fname}')
    return send_file(filepath, as_attachment=True, download_name=filename)


@bp.route('/backup/restore', methods=['POST'])
def backup_restore():
    """恢复数据：支持 zip（含 data.json + resumes/）或纯 json。

    zip 时会先把 resumes/ 目录下的文件还原到 data/resumes/，再恢复 DB。
    """
    file = request.files.get('backup_file')
    if not file or not file.filename:
        flash('未选择文件')
        return redirect(url_for('backup.backup_page'))

    mode = request.form.get('mode', 'skip')  # skip / overwrite
    filename = file.filename.lower()

    # 备份当前 db
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    bak_path = f"{db_path}.before_restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, bak_path)

    try:
        if filename.endswith('.zip'):
            # zip 包：先解压简历文件，再读 data.json
            file_bytes = file.read()
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                names = zf.namelist()
                # 还原 resumes/ 文件到 data/resumes/
                resume_dir_abs = os.path.join(current_app.config['BASE_DIR'], 'data', 'resumes')
                os.makedirs(resume_dir_abs, exist_ok=True)
                restored_files = 0
                for name in names:
                    # 只处理 resumes/ 前缀且是文件（跳过目录条目和 data.json）
                    if name.startswith('resumes/') and not name.endswith('/'):
                        # 防路径穿越：取 basename
                        base = os.path.basename(name)
                        if not base:
                            continue
                        target = os.path.join(resume_dir_abs, base)
                        with zf.open(name) as src, open(target, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        restored_files += 1
                # 读取 data.json
                try:
                    with zf.open('data.json') as f:
                        content = f.read().decode('utf-8')
                except KeyError:
                    flash('zip 包中未找到 data.json')
                    return redirect(url_for('backup.backup_page'))
            file_extra_msg = f'，已还原 {restored_files} 个简历文件'
        else:
            # 纯 JSON
            content = file.read().decode('utf-8')
            file_extra_msg = ''

        data = json.loads(content)
        if data.get('version') != BACKUP_VERSION:
            flash(f'版本不匹配：期望 {BACKUP_VERSION}，实际 {data.get("version")}')
            return redirect(url_for('backup.backup_page'))

        id_map = {'companies': {}, 'applications': {}}
        stats = {'companies': 0, 'applications': 0, 'notes': 0, 'timelines': 0,
                 'interview_feedbacks': 0, 'resumes': 0}

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
            old_app_id = a_data.pop('id', None)
            a = Application(**{k: v for k, v in a_data.items() if v is not None})
            db.session.add(a)
            db.session.flush()
            if old_app_id is not None:
                id_map['applications'][old_app_id] = a.id
            stats['applications'] += 1

        for n_data in data.get('notes', []):
            old_company_id = n_data.get('company_id')
            if old_company_id:
                n_data['company_id'] = id_map['companies'].get(old_company_id, old_company_id)
            n_data.pop('id', None)
            db.session.add(Note(**{k: v for k, v in n_data.items() if v is not None}))
            stats['notes'] += 1

        for t_data in data.get('timelines', []):
            t_data.pop('id', None)
            db.session.add(Timeline(**{k: v for k, v in t_data.items() if v is not None}))
            stats['timelines'] += 1

        for f_data in data.get('interview_feedbacks', []):
            old_app_id = f_data.get('application_id')
            f_data['application_id'] = id_map['applications'].get(old_app_id, old_app_id)
            f_data.pop('id', None)
            db.session.add(InterviewFeedback(**{k: v for k, v in f_data.items() if v is not None}))
            stats['interview_feedbacks'] += 1

        for r_data in data.get('resumes', []):
            existing_path = r_data.get('file_path')
            if existing_path and mode == 'skip' and Resume.query.filter_by(file_path=existing_path).first():
                continue
            r_data.pop('id', None)
            db.session.add(Resume(**{k: v for k, v in r_data.items() if v is not None}))
            stats['resumes'] += 1

        db.session.commit()
        flash(f'恢复完成：{stats["companies"]} 家公司、{stats["applications"]} 条投递、{stats["notes"]} 条笔记、{stats["timelines"]} 个时间线、{stats["interview_feedbacks"]} 条面试反馈、{stats["resumes"]} 个简历{file_extra_msg}。当前 db 已备份到 {os.path.basename(bak_path)}')
    except Exception as e:
        db.session.rollback()
        flash(f'恢复失败：{str(e)}。当前 db 未变更（备份在 {os.path.basename(bak_path)}）')
    return redirect(url_for('backup.backup_page'))
