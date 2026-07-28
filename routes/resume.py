"""简历版本管理路由。"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from extensions import db
from models import Resume
from utils import safe_filename, humanize_size
from config import Config

bp = Blueprint('resume', __name__)


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_RESUME_EXT


@bp.route('/resumes')
def resume_list():
    resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    default_resume = Resume.query.filter_by(is_default=True).first()
    return render_template('resumes.html', resumes=resumes, default_resume=default_resume,
                           humanize_size=humanize_size)


@bp.route('/resumes/upload', methods=['POST'])
def resume_upload():
    file = request.files.get('file')
    if not file or not file.filename:
        flash('未选择文件')
        return redirect(url_for('resume.resume_list'))
    if not _allowed_file(file.filename):
        flash(f'不支持的文件类型，仅接受 {", ".join(Config.ALLOWED_RESUME_EXT)}')
        return redirect(url_for('resume.resume_list'))

    ext = file.filename.rsplit('.', 1)[1].lower()
    storage_name = safe_filename(file.filename, ext)
    storage_path = os.path.join(Config.UPLOAD_FOLDER, storage_name)
    file.save(storage_path)
    file_size = os.path.getsize(storage_path)

    # 支持更新现有简历：replace_id 指定要替换的简历 ID
    replace_id = request.form.get('replace_id', '').strip()
    if replace_id:
        from utils import try_int
        rid = try_int(replace_id)
        r = db.session.get(Resume, rid) if rid else None
        if r is None:
            # 校验失败，删除已保存的新文件以避免垃圾残留
            try:
                os.remove(storage_path)
            except OSError:
                pass
            flash('未找到要更新的简历')
            return redirect(url_for('resume.resume_list'))
        # 删除旧文件
        old_abs = os.path.join(current_app.config['BASE_DIR'], r.file_path)
        try:
            if os.path.exists(old_abs):
                os.remove(old_abs)
        except OSError as e:
            current_app.logger.warning(f'删除旧简历文件失败: {old_abs} - {e}')
        # 更新记录
        r.file_path = f'data/resumes/{storage_name}'
        r.file_type = ext
        r.file_size = file_size
        # 名称/版本/备注仅在表单提供了非空值时才覆盖
        new_name = request.form.get('name', '').strip()
        if new_name:
            r.name = new_name
        new_version = request.form.get('version', '').strip()
        if new_version:
            r.version = new_version
        new_note = request.form.get('note', '').strip()
        if new_note:
            r.note = new_note
        db.session.commit()
        flash(f'已更新简历文件：{r.name}')
        return redirect(url_for('resume.resume_list'))

    # 新建简历
    is_first = Resume.query.count() == 0

    r = Resume(
        name=request.form.get('name', file.filename).strip(),
        version=request.form.get('version', '').strip(),
        file_path=f'data/resumes/{storage_name}',
        file_type=ext,
        file_size=file_size,
        note=request.form.get('note', '').strip(),
        is_default=is_first,
    )
    db.session.add(r)
    db.session.commit()
    flash(f'上传成功：{r.name}')
    return redirect(url_for('resume.resume_list'))


@bp.route('/resumes/<int:r_id>/preview')
def resume_preview(r_id):
    r = Resume.query.get_or_404(r_id)
    return render_template('resume_preview.html', resume=r)


@bp.route('/resumes/<int:r_id>/file')
def resume_file(r_id):
    """返回原文件，供 iframe 或 fetch 使用。"""
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.join(current_app.config['BASE_DIR'], r.file_path)
    return send_file(abs_path)


@bp.route('/resumes/<int:r_id>/download')
def resume_download(r_id):
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.join(current_app.config['BASE_DIR'], r.file_path)
    return send_file(abs_path, as_attachment=True, download_name=f'{r.name}.{r.file_type}')


@bp.route('/resumes/<int:r_id>/edit', methods=['POST'])
def resume_edit(r_id):
    r = Resume.query.get_or_404(r_id)
    r.name = request.form.get('name', r.name).strip()
    r.version = request.form.get('version', r.version).strip()
    r.note = request.form.get('note', r.note).strip()
    db.session.commit()
    flash('已更新')
    return redirect(url_for('resume.resume_list'))


@bp.route('/resumes/<int:r_id>/default', methods=['POST'])
def resume_set_default(r_id):
    r = Resume.query.get_or_404(r_id)
    Resume.query.filter_by(is_default=True).update({'is_default': False})
    r.is_default = True
    db.session.commit()
    flash(f'已将「{r.name}」设为默认')
    return redirect(url_for('resume.resume_list'))


@bp.route('/resumes/<int:r_id>/delete', methods=['POST'])
def resume_delete(r_id):
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.join(current_app.config['BASE_DIR'], r.file_path)
    try:
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except OSError:
        pass
    db.session.delete(r)
    db.session.commit()
    flash('已删除')
    return redirect(url_for('resume.resume_list'))
