"""简历版本管理路由。"""
import os
import shutil
import subprocess
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from extensions import db
from models import Resume
from utils import safe_filename, humanize_size
from config import Config

bp = Blueprint('resume', __name__)


# ── LibreOffice 路径自动探测 ──
def _find_soffice():
    """在常见位置查找 LibreOffice 的 soffice.exe，返回完整路径或 None。"""
    candidates = [
        r'C:\Program Files\LibreOffice\program\soffice.exe',
        r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
    ]
    # 也检查 PATH
    path_in_env = shutil.which('soffice') or shutil.which('libreoffice')
    if path_in_env:
        candidates.insert(0, path_in_env)
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _docx_to_pdf(docx_path, output_dir):
    """用 LibreOffice headless 将 DOCX 转成 PDF，返回 PDF 路径或 None。"""
    soffice = _find_soffice()
    if not soffice:
        current_app.logger.warning('LibreOffice 未安装，跳过 DOCX→PDF 转换')
        return None
    try:
        result = subprocess.run(
            [soffice, '--headless', '--convert-to', 'pdf', '--outdir', output_dir, docx_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            current_app.logger.error(f'LibreOffice 转换失败: {result.stderr}')
            return None
        # 输出文件名 = 输入文件名去掉 .docx 加 .pdf
        base = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(output_dir, base + '.pdf')
        if os.path.isfile(pdf_path):
            return pdf_path
        return None
    except Exception as e:
        current_app.logger.error(f'LibreOffice 转换异常: {e}')
        return None


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
        # DOCX 自动转 PDF 做预览
        if ext == 'docx':
            new_abs = os.path.join(current_app.config['BASE_DIR'], r.file_path)
            out_dir = os.path.dirname(new_abs)
            pdf_abs = _docx_to_pdf(new_abs, out_dir)
            if pdf_abs:
                # 删除旧 pdf 文件
                if r.pdf_path:
                    old_pdf = os.path.join(current_app.config['BASE_DIR'], r.pdf_path)
                    try:
                        if os.path.exists(old_pdf):
                            os.remove(old_pdf)
                    except OSError:
                        pass
                r.pdf_path = os.path.relpath(pdf_abs, current_app.config['BASE_DIR']).replace('\\', '/')
        else:
            # 非 DOCX 文件，清除旧 pdf_path 引用
            if r.pdf_path:
                old_pdf = os.path.join(current_app.config['BASE_DIR'], r.pdf_path)
                try:
                    if os.path.exists(old_pdf):
                        os.remove(old_pdf)
                except OSError:
                    pass
                r.pdf_path = None
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
    # DOCX 自动转 PDF 做预览
    if ext == 'docx':
        new_abs = os.path.join(current_app.config['BASE_DIR'], r.file_path)
        out_dir = os.path.dirname(new_abs)
        pdf_abs = _docx_to_pdf(new_abs, out_dir)
        if pdf_abs:
            r.pdf_path = os.path.relpath(pdf_abs, current_app.config['BASE_DIR']).replace('\\', '/')
    db.session.add(r)
    db.session.commit()
    flash(f'上传成功：{r.name}')
    if ext == 'docx' and not r.pdf_path:
        flash('提示：LibreOffice 未安装或转换失败，DOCX 预览将不可用。请安装 LibreOffice 或上传 PDF 版本。', 'warning')
    return redirect(url_for('resume.resume_list'))


@bp.route('/resumes/<int:r_id>/preview')
def resume_preview(r_id):
    r = Resume.query.get_or_404(r_id)
    return render_template('resume_preview.html', resume=r)


@bp.route('/resumes/<int:r_id>/file')
def resume_file(r_id):
    """返回原文件，供下载或直接预览使用。"""
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.join(current_app.config['BASE_DIR'], r.file_path)
    return send_file(abs_path)


@bp.route('/resumes/<int:r_id>/pdf')
def resume_pdf_file(r_id):
    """返回用于预览的 PDF 文件（对 DOCX 而言是转换后的 PDF，对 PDF 而言是原文件）。"""
    r = Resume.query.get_or_404(r_id)
    if r.file_type == 'pdf':
        abs_path = os.path.join(current_app.config['BASE_DIR'], r.file_path)
    elif r.pdf_path:
        abs_path = os.path.join(current_app.config['BASE_DIR'], r.pdf_path)
    else:
        # 如果没有转换成功的 PDF，尝试实时转换一次
        docx_abs = os.path.join(current_app.config['BASE_DIR'], r.file_path)
        out_dir = os.path.dirname(docx_abs)
        pdf_abs = _docx_to_pdf(docx_abs, out_dir)
        if pdf_abs:
            r.pdf_path = os.path.relpath(pdf_abs, current_app.config['BASE_DIR']).replace('\\', '/')
            db.session.commit()
            abs_path = pdf_abs
        else:
            return "无法预览此文件类型，因为 PDF 转换失败", 404
    return send_file(abs_path, mimetype='application/pdf')


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
